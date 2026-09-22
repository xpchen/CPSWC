"""
test_template_input_classes.py — B 批模板改造的统一验收夹具

对应 implementation/B_BATCH_TEMPLATE_TASKS.md 第 1 节"统一验收项", 覆盖
四类输入 × 全部已注册 render section:

    T-a  相关字段全缺          → 不得用"—"冒充数据; 不得出现无复核支持的项目判断
    T-b  明确填 0 / 空清单     → 不得升级为业务结论 (不涉及 / 无需 / 不设置)
    T-c  非法值 (NaN / inf / 坏单位) → 不得崩溃, 非法数字不得出现在正文
    T-d  别名两侧冲突          → 不静默择一

为什么做成通用夹具而不是逐模板写:
  这四类输入的要求对每个模板都一样, 逐个手写既漏又不一致。参数化到全部
  已注册 section 上, 新增模板会自动纳入; 漏改一个模板就会红。

**这份夹具不能代替 B_BATCH_TEMPLATE_TASKS.md 的 T-e**: 逐句确认断言类型
是否分类正确, 必须人工做 —— 机器分不出"看起来像陈述事实、实际是专业判断"
的句子。T-e 的人工复核状态见交付记录。

夹具值全部由 FieldIdentityRegistry 的 semantic_type 合成, 不取自任何真实项目。
"""
import math
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.narrative.contract import AssertionClass, validate_block
from cpswc.narrative.projection import _PILOT_TEMPLATES
from cpswc.paths import REGISTRIES_DIR
from cpswc.report_quality import Severity
from cpswc.snapshot_adapter import ALIAS_CANDIDATES, BuildContext

_FIR = yaml.safe_load(
    (REGISTRIES_DIR / "FieldIdentityRegistry_v0.yaml").read_text(encoding="utf-8"))
_FIELDS: dict = _FIR.get("fields") or {}

SECTIONS = sorted(_PILOT_TEMPLATES)

# 业务结论措辞。这些话必须有核查/复核支持, 不能由"填了 0"或"空清单"推出来。
_UNSUPPORTED_CONCLUSIONS = (
    "不涉及", "无需", "不设置", "无可剥离表土", "基本平衡",
    "全部用于", "经现场踏勘", "经核查，项目区不",
)


def _synthesize(mode: str) -> tuple[dict, dict]:
    """
    按 FIR 登记的 semantic_type 合成一整套输入。

    mode:
      "zero"    每个字段给类型正确的"明确零值" (0 / False / 空串 / 空清单)
      "invalid" 每个字段给非法值 (NaN / inf / 未登记单位 / 坏数字串)
    """
    facts: dict = {}
    derived: dict = {}
    for field_id, fdef in _FIELDS.items():
        if not isinstance(fdef, dict) or fdef.get("placeholder") is True:
            continue
        st = fdef.get("semantic_type") or ""
        unit = fdef.get("unit")
        if mode == "zero":
            if st in ("string", "text", "enum", "year", "year_month", "geo_ref"):
                value = "0"
            elif st == "bool":
                value = False
            elif st in ("number", "percent"):
                value = 0
            elif st.startswith("list_of") or st.endswith("List"):
                value = []
            elif st.endswith("Dict") or st == "record":
                value = {}
            else:
                value = {"value": 0, "unit": unit} if unit else 0
        else:  # invalid
            if st in ("string", "text", "enum", "year", "year_month", "geo_ref"):
                value = "   "                       # 空白串 → MISSING
            elif st == "bool":
                value = "not-a-bool"
            elif st in ("number", "percent"):
                value = float("nan")
            elif st.startswith("list_of") or st.endswith("List"):
                value = [{}]
            elif st.endswith("Dict") or st == "record":
                value = {"__bad__": float("inf")}
            else:
                value = {"value": float("nan"), "unit": unit or "未登记单位"}
        (derived if field_id.startswith("field.derived.") else facts)[field_id] = value
    return facts, derived


_ZERO_FACTS, _ZERO_DERIVED = _synthesize("zero")
_BAD_FACTS, _BAD_DERIVED = _synthesize("invalid")


def _render(section_id: str, facts: dict, derived: dict,
            triggered=None, context=None):
    fn = _PILOT_TEMPLATES[section_id]
    return fn(facts=facts, derived=derived, triggered=set(triggered or ()),
              snapshot={}, ledger=None, unknown=set(), context=context)


def _text(block) -> str:
    return "".join(p.text for p in (block.paragraphs or []))


def _unsupported_judgments(block) -> list:
    return [p for p in (block.paragraphs or [])
            if p.assertion_class is AssertionClass.PROJECT_JUDGMENT
            and not p.review_refs]


# ============================================================
# T-a — 相关字段全缺
# ============================================================

def _strip_prose_dashes(text: str) -> str:
    """去掉作为标点的中文破折号"——", 只留可能冒充数据的单个"—"。

    `sec_7_8` 里的"先拦后弃——在弃渣作业前…"是正常行文, 不是占位符。
    """
    return text.replace("——", "")


@pytest.mark.parametrize("section_id", SECTIONS)
def test_ta_missing_inputs_never_render_a_dash_as_data(section_id):
    """缺失不得显示成"—": 短横线看起来像一个已填写的值。"""
    block = _render(section_id, {}, {})
    assert "—" not in _strip_prose_dashes(_text(block)), \
        f"{section_id} 用短横线冒充数据"


@pytest.mark.parametrize("section_id", SECTIONS)
def test_ta_missing_inputs_produce_no_unsupported_judgment(section_id):
    block = _render(section_id, {}, {})
    assert _unsupported_judgments(block) == [], \
        f"{section_id} 在空输入下输出了无复核支持的项目判断"
    assert validate_block(block) == []


@pytest.mark.parametrize("section_id", SECTIONS)
def test_ta_every_paragraph_declares_an_assertion_class(section_id):
    """每段都必须显式声明断言类型 —— 这是 T-e 人工复核的前提。"""
    block = _render(section_id, {}, {})
    for p in (block.paragraphs or []):
        assert isinstance(p.assertion_class, AssertionClass)


@pytest.mark.parametrize("section_id", SECTIONS)
def test_ta_gaps_name_the_missing_field_ids(section_id):
    """报缺口就要说清缺哪个登记字段, 不能只说"资料不全"。"""
    block = _render(section_id, {}, {})
    missing = {r for f in (block.quality_findings or [])
               for r in f.missing_input_refs}
    gap_paras = [p for p in (block.paragraphs or [])
                 if p.assertion_class is AssertionClass.GAP_STATEMENT]
    if gap_paras and any(f.code == "VALUE_MISSING"
                         for f in (block.quality_findings or [])):
        assert missing, f"{section_id} 报了缺失却没说缺哪个字段"


# ============================================================
# T-b — 明确填 0 / 空清单
# ============================================================

@pytest.mark.parametrize("section_id", SECTIONS)
def test_tb_explicit_zero_does_not_crash(section_id):
    block = _render(section_id, dict(_ZERO_FACTS), dict(_ZERO_DERIVED))
    assert validate_block(block) == []


@pytest.mark.parametrize("section_id", SECTIONS)
def test_tb_explicit_zero_does_not_become_a_business_conclusion(section_id):
    """填了 0 只说明填了 0。"不涉及 / 无需 / 不设置"是核查结论, 需要支持。"""
    block = _render(section_id, dict(_ZERO_FACTS), dict(_ZERO_DERIVED))
    text = _text(block)
    for phrase in _UNSUPPORTED_CONCLUSIONS:
        if phrase not in text:
            continue
        # 出现在"待核查/不作结论"这类说明里是允许的
        assert ("待" in text or "核查记录" in text or "复核" in text
                or "填报" in text or "未" in text), \
            f"{section_id} 由明确零值直接推出业务结论: {phrase}"


@pytest.mark.parametrize("section_id", SECTIONS)
def test_tb_explicit_zero_produces_no_unsupported_judgment(section_id):
    block = _render(section_id, dict(_ZERO_FACTS), dict(_ZERO_DERIVED))
    assert _unsupported_judgments(block) == []


# ============================================================
# T-c — 非法值
# ============================================================

@pytest.mark.parametrize("section_id", SECTIONS)
def test_tc_invalid_inputs_do_not_crash(section_id):
    block = _render(section_id, dict(_BAD_FACTS), dict(_BAD_DERIVED))
    assert validate_block(block) == []


@pytest.mark.parametrize("section_id", SECTIONS)
def test_tc_invalid_numbers_never_reach_the_text(section_id):
    """NaN / inf 不得出现在正文里 —— 读者会把它当成一个数。"""
    text = _text(_render(section_id, dict(_BAD_FACTS), dict(_BAD_DERIVED)))
    for token in ("nan", "NaN", "inf", "Infinity"):
        assert token not in text, f"{section_id} 正文里出现了 {token}"


@pytest.mark.parametrize("section_id", SECTIONS)
def test_tc_invalid_inputs_produce_no_unsupported_judgment(section_id):
    block = _render(section_id, dict(_BAD_FACTS), dict(_BAD_DERIVED))
    assert _unsupported_judgments(block) == []


# ============================================================
# T-d — 别名两侧冲突
# ============================================================

@pytest.mark.parametrize("section_id", SECTIONS)
def test_td_alias_conflict_does_not_crash_templates(section_id):
    a, b, _ = ALIAS_CANDIDATES[0]
    facts = {a: {"value": 0.3, "unit": "万m³"},
             b: {"value": 0.9, "unit": "万m³"}}
    ctx = BuildContext({"facts": facts})
    ctx.check_alias_candidates()
    block = _render(section_id, facts, {}, context=ctx)
    assert validate_block(block) == []


@pytest.mark.parametrize("alias_pair", ALIAS_CANDIDATES,
                         ids=[a.rsplit(".", 1)[-1] for a, _, _ in ALIAS_CANDIDATES])
def test_td_every_registered_alias_pair_is_checked(alias_pair):
    """每一对别名候选都要真的被检查到, 不能只是列在常量里。"""
    a, b, _ = alias_pair
    ctx = BuildContext({"facts": {a: "甲", b: "乙"}})
    findings = ctx.check_alias_candidates()
    assert any(f.code == "INPUT_CONFLICT" and f.severity is Severity.BLOCK
               for f in findings), f"{a} / {b} 未被检查"


# ============================================================
# 结构性约束: 全部 section 都已迁移
# ============================================================

def test_every_registered_template_uses_the_shared_reader():
    """漏改一个模板就会红 —— 防止两套取值方式并存。"""
    import inspect
    unmigrated = []
    for section_id, fn in _PILOT_TEMPLATES.items():
        src = inspect.getsource(sys.modules[fn.__module__])
        if "SectionEvidence" not in src:
            unmigrated.append((fn.__module__.rsplit(".", 1)[-1], section_id))
    assert unmigrated == [], f"未迁移到统一读取的模板: {unmigrated}"


def test_no_template_keeps_a_legacy_reader():
    """旧的 `_v(facts, ...)` / `_num(facts, ...)` 必须彻底移除。"""
    import inspect
    import re
    offenders = []
    seen = set()
    for fn in _PILOT_TEMPLATES.values():
        mod = fn.__module__
        if mod in seen:
            continue
        seen.add(mod)
        src = inspect.getsource(sys.modules[mod])
        # 只看代码, 不看文档字符串里的历史说明
        code = re.sub(r'"""(?:.|\n)*?"""', "", src)
        if re.search(r"(?<!def )_v\(facts|(?<!def )_num\(facts", code):
            offenders.append(mod.rsplit(".", 1)[-1])
    assert offenders == [], f"仍在使用旧取值函数: {offenders}"


def test_templates_accept_the_build_context_parameter():
    import inspect
    missing = []
    for section_id, fn in _PILOT_TEMPLATES.items():
        sig = inspect.signature(fn)
        if "context" not in sig.parameters and not any(
                p.kind is inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values()):
            missing.append(section_id)
    assert missing == []
