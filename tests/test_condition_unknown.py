"""
test_condition_unknown.py — P0-02 验收测试

对应 04_CONTRACTS_AND_ACCEPTANCE.md 第 9 节:

    U01  借方 trigger 依赖缺失        → UNKNOWN, 不进入 not_triggered
    U02  输入明确 0 / False           → 可确定 False, 仍保留来源状态
    U03  DSL 解析/求值异常            → ERROR finding, 非 False
    U04  UNKNOWN 经 NOT / AND / OR    → 满足三值逻辑, 不伪判不涉及
    U05  级联链调换 registry 顺序     → 相同求值结果
    U06  缺依赖 / 循环                → UNKNOWN 及诊断, 不默认 False
    U07  无红线冲突但未做常规评价     → 常规选址内容保留为待核验

夹具是原创合成 obligation 定义, 不修改 registries/ 下的任何生效文件。
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.condition_engine import (
    EvaluationStatus, evaluate_all, evaluate_obligation, extract_field_refs,
    transform_dsl, validate_transformed_expr,
)

BORROW = "field.fact.earthwork.borrow"
BORROW_TYPE = "field.fact.earthwork.borrow_source_type"


def _ob(when: str, mode: str = "conditional") -> dict:
    return {"trigger": {"mode": mode, "when": when}}


def _driven(refs: list[str]) -> dict:
    return {"trigger": {"mode": "driven_by_obligation", "driven_by_refs": refs}}


# ============================================================
# U01 — 依赖缺失 → UNKNOWN, 不进 not_triggered
# ============================================================

def test_u01_missing_borrow_is_unknown_not_untriggered():
    reg = {"ob.borrow_site.land_use_approval":
           _ob(f'{BORROW}.value > 0 AND {BORROW_TYPE} == "自设取土场"')}
    r = evaluate_all(reg, {})
    assert "ob.borrow_site.land_use_approval" in r.unknown
    assert "ob.borrow_site.land_use_approval" not in r.not_triggered
    assert "ob.borrow_site.land_use_approval" not in r.triggered


def test_u01_unknown_result_names_the_missing_fields():
    d = evaluate_obligation("ob.x", _ob(f"{BORROW}.value > 0"), {})
    assert d.triggered is None
    assert d.evaluation_status is EvaluationStatus.UNKNOWN_MISSING_INPUT
    assert BORROW in d.missing_field_refs
    assert d.diagnostic_code == "CONDITION_UNKNOWN"


def test_u01_applicability_map_reports_unknown():
    reg = {"ob.a": _ob(f"{BORROW}.value > 0"), "ob.b": _ob("always", "always")}
    m = evaluate_all(reg, {}).applicability_map()
    assert m["ob.a"] == "UNKNOWN"
    assert m["ob.b"] == "APPLICABLE"


def test_u01_always_survives_unrelated_missing_fields():
    """无关字段缺失不得把 always 义务一起冲掉。"""
    reg = {"ob.always": _ob("always", "always"),
           "ob.cond": _ob(f"{BORROW}.value > 0")}
    r = evaluate_all(reg, {})
    assert "ob.always" in r.triggered
    assert "ob.cond" in r.unknown


# ============================================================
# U02 — 明确 0 / False 是可确定的结果
# ============================================================

def test_u02_explicit_zero_evaluates_to_false():
    d = evaluate_obligation("ob.x", _ob(f"{BORROW}.value > 0"),
                            {BORROW: {"value": 0, "unit": "万m³"}})
    assert d.triggered is False
    assert d.evaluation_status is EvaluationStatus.EVALUATED


def test_u02_zero_and_missing_produce_different_verdicts():
    """PROBE-4 复现的缺陷: 两种输入曾经产生同一个结论。"""
    reg = {"ob.x": _ob(f"{BORROW}.value > 0")}
    missing = evaluate_all(reg, {})
    zero = evaluate_all(reg, {BORROW: {"value": 0, "unit": "万m³"}})
    assert "ob.x" in missing.unknown
    assert "ob.x" in zero.not_triggered


def test_u02_explicit_false_bool_is_determinate():
    d = evaluate_obligation(
        "ob.x", _ob("field.fact.disposal_site.failure_analysis_required == true"),
        {"field.fact.disposal_site.failure_analysis_required": False})
    assert d.triggered is False


def test_u02_empty_list_makes_has_any_false_but_missing_key_unknown():
    reg = {"ob.x": _ob("has_any(field.fact.natural.other_sensitive_areas)")}
    provided = evaluate_all(reg, {"field.fact.natural.other_sensitive_areas": []})
    absent = evaluate_all(reg, {})
    assert "ob.x" in provided.not_triggered, "提供了空清单 = 可确定的 False"
    assert "ob.x" in absent.unknown, "字段没提供 = 未知"


def test_u02_determinate_result_still_records_touched_missing_deps():
    """A OR B 中 A 已为真时结果确定, 但 B 的缺失照实记录供质量层提示。"""
    d = evaluate_obligation(
        "ob.x", _ob(f"{BORROW}.value > 0 OR field.fact.earthwork.spoil.value > 0"),
        {BORROW: {"value": 5, "unit": "万m³"}})
    assert d.triggered is True
    assert "field.fact.earthwork.spoil" in d.missing_field_refs


# ============================================================
# U03 — DSL 异常 → ERROR, 绝不回落 False
# ============================================================

def test_u03_syntax_error_is_error_not_false():
    d = evaluate_obligation("ob.x", _ob(f"{BORROW}.value > "), {})
    assert d.triggered is None
    assert d.is_error
    assert d.diagnostic_code == "CONDITION_ERROR"


def test_u03_error_does_not_land_in_not_triggered():
    reg = {"ob.x": _ob(f"{BORROW}.value > ")}
    r = evaluate_all(reg, {})
    assert "ob.x" in r.unknown
    assert "ob.x" not in r.not_triggered


def test_u03_out_of_grammar_operator_is_rejected():
    """`>>` 在 Python 里是右移, 会悄悄算出真值。闭集校验必须拦下它。"""
    d = evaluate_obligation("ob.x", _ob(f"{BORROW}.value >> 0"),
                            {BORROW: {"value": 5, "unit": "万m³"}})
    assert d.triggered is None
    assert d.evaluation_status is EvaluationStatus.ERROR_DSL
    assert "BinOp" in d.diagnostic_message


def test_u03_no_arbitrary_python_execution():
    d = evaluate_obligation("ob.x", _ob('__import__("os").system("true")'), {})
    assert d.triggered is None
    assert d.evaluation_status is EvaluationStatus.ERROR_DSL


def test_u03_nan_dependency_is_unknown_not_false():
    d = evaluate_obligation("ob.x", _ob(f"{BORROW}.value > 0"),
                            {BORROW: {"value": float("nan"), "unit": "万m³"}})
    assert d.triggered is None
    assert d.evaluation_status is EvaluationStatus.UNKNOWN_INVALID_INPUT


# ============================================================
# U04 — 三值逻辑 (04 文档第 4 节)
# ============================================================

KNOWN_TRUE = {"field.a": {"value": 5, "unit": "万m³"}}
KNOWN_FALSE = {"field.a": {"value": 0, "unit": "万m³"}}


@pytest.mark.parametrize("when,unified,expected", [
    # TRUE OR UNKNOWN = TRUE
    ("field.a.value > 0 OR field.b.value > 0", KNOWN_TRUE, True),
    # FALSE OR UNKNOWN = UNKNOWN
    ("field.a.value > 0 OR field.b.value > 0", KNOWN_FALSE, None),
    # TRUE AND UNKNOWN = UNKNOWN
    ("field.a.value > 0 AND field.b.value > 0", KNOWN_TRUE, None),
    # FALSE AND UNKNOWN = FALSE
    ("field.a.value > 0 AND field.b.value > 0", KNOWN_FALSE, False),
    # NOT UNKNOWN = UNKNOWN
    ("NOT field.b.value > 0", {}, None),
    # NOT FALSE = TRUE
    ("NOT field.a.value > 0", KNOWN_FALSE, True),
])
def test_u04_three_valued_logic(when, unified, expected):
    d = evaluate_obligation("ob.x", _ob(when), unified)
    assert d.triggered is expected, f"{when} on {unified} → {d.triggered}"


def test_u04_true_or_unknown_keeps_required_artifacts():
    """回归护栏: 曾经"整条表达式判未知"会把确定触发的义务降级成未知,
    结果是本该要求的制品消失了。三值逻辑必须保住这个 True。"""
    d = evaluate_obligation(
        "ob.disposal_site.site_selection",
        _ob("field.fact.earthwork.spoil.value > 0 "
            "OR count(field.fact.construction.temp_topsoil_site) > 0"),
        {"field.fact.earthwork.spoil": {"value": 3.5, "unit": "万m³"}})
    assert d.triggered is True


# ============================================================
# U05 — 级联结果与 registry 书写顺序无关
# ============================================================

def _cascade_registry():
    return {
        "ob.root": _ob("field.a.value > 0"),
        "ob.mid": _driven(["ob.root"]),
        "ob.leaf": _driven(["ob.mid"]),
    }


def test_u05_cascade_order_independent():
    reg = _cascade_registry()
    reversed_reg = dict(reversed(list(reg.items())))
    unified = {"field.a": {"value": 5, "unit": "万m³"}}

    a = evaluate_all(reg, unified)
    b = evaluate_all(reversed_reg, unified)
    assert a.triggered == b.triggered
    assert a.not_triggered == b.not_triggered
    assert a.unknown == b.unknown
    assert a.triggered == {"ob.root", "ob.mid", "ob.leaf"}


def test_u05_cascade_order_independent_when_root_unknown():
    reg = _cascade_registry()
    reversed_reg = dict(reversed(list(reg.items())))
    a = evaluate_all(reg, {})
    b = evaluate_all(reversed_reg, {})
    assert a.unknown == b.unknown == {"ob.root", "ob.mid", "ob.leaf"}
    assert a.not_triggered == b.not_triggered == set()


def test_u05_cascade_false_propagates_definitively():
    reg = _cascade_registry()
    r = evaluate_all(reg, {"field.a": {"value": 0, "unit": "万m³"}})
    assert r.not_triggered == {"ob.root", "ob.mid", "ob.leaf"}
    assert r.unknown == set()


# ============================================================
# U06 — 缺依赖 / 循环
# ============================================================

def test_u06_dangling_driven_by_ref_is_unknown_with_diagnostic():
    reg = {"ob.x": _driven(["ob.does_not_exist"])}
    r = evaluate_all(reg, {})
    assert "ob.x" in r.unknown
    d = r.obligation_details[0]
    assert d.evaluation_status is EvaluationStatus.UNKNOWN_DANGLING_REF
    assert "ob.does_not_exist" in d.diagnostic_message


def test_u06_cycle_is_unknown_not_false():
    reg = {"ob.a": _driven(["ob.b"]), "ob.b": _driven(["ob.a"])}
    r = evaluate_all(reg, {})
    assert r.unknown == {"ob.a", "ob.b"}
    assert r.not_triggered == set()
    assert all(d.evaluation_status is EvaluationStatus.UNKNOWN_CYCLE
               for d in r.obligation_details)


def test_u06_driven_by_without_refs_is_unknown():
    reg = {"ob.x": {"trigger": {"mode": "driven_by_obligation"}}}
    r = evaluate_all(reg, {})
    assert "ob.x" in r.unknown
    assert "未声明 driven_by_refs" in r.obligation_details[0].diagnostic_message


def test_u06_unknown_dependency_does_not_become_false():
    reg = {"ob.root": _ob("field.a.value > 0"), "ob.child": _driven(["ob.root"])}
    r = evaluate_all(reg, {})
    assert "ob.child" in r.unknown
    assert "ob.child" not in r.not_triggered


# ============================================================
# U07 — 常规章节不再被专题义务一票否决
# ============================================================

def test_u07_routine_sections_are_not_gated_by_redline_conflict():
    """敏感区说明与选址选线评价是常规内容, 不是不可避让专题的附属品。"""
    from cpswc.narrative.projection import (
        _SECTION_CONDITIONALS, _SECTION_SPECIAL_TOPICS,
    )
    assert _SECTION_CONDITIONALS["sec.project_overview.sensitive_areas"] is None
    assert _SECTION_CONDITIONALS["sec.evaluation.site_selection"] is None
    # 专题本身仍登记在案, 只是不再控制整节适用性
    assert (_SECTION_SPECIAL_TOPICS["sec.evaluation.site_selection"]
            == "ob.unavoidability.redline_conflict")


def test_u07_routine_sections_render_when_no_redline_conflict():
    from cpswc.narrative.projection import project_narrative
    from cpswc.report_quality import Applicability

    result = project_narrative({"_original_facts": {}, "derived_fields": {},
                                "triggered_obligations": [],
                                "unknown_obligations": []})
    by_id = {b.section_id: b for b in result.blocks}
    for sid in ("sec.project_overview.sensitive_areas",
                "sec.evaluation.site_selection"):
        assert by_id[sid].render_status.value != "not_applicable", \
            f"{sid} 不得因为没有红线冲突就变成不涉及"
        assert by_id[sid].applicability is not Applicability.NOT_APPLICABLE


def test_u07_unknown_applicability_section_is_skeleton_not_na():
    from cpswc.narrative.projection import project_narrative
    from cpswc.report_quality import Applicability

    result = project_narrative({
        "_original_facts": {}, "derived_fields": {},
        "triggered_obligations": [],
        "unknown_obligations": ["ob.disposal_site.site_selection"],
    })
    by_id = {b.section_id: b for b in result.blocks}
    blk = by_id["sec.disposal_site"]
    assert blk.applicability is Applicability.UNKNOWN
    assert blk.render_status.value == "skeleton"
    assert blk.render_status.value != "not_applicable"
    assert any(f.code == "CONDITION_UNKNOWN" for f in blk.quality_findings)
    assert result.unknown_applicability_count >= 1


def test_u07_not_applicable_block_says_the_verdict_is_unconfirmed():
    """可确定不触发 ≠ 已专业核查确认不涉及。"""
    from cpswc.narrative.projection import project_narrative

    result = project_narrative({
        "_original_facts": {}, "derived_fields": {},
        "triggered_obligations": [], "unknown_obligations": [],
    })
    na = [b for b in result.blocks if b.render_status.value == "not_applicable"]
    assert na, "应至少有一个可确定不适用的章节"
    assert all("未经专业核查确认" in "".join(b.block_warnings) for b in na)


# ============================================================
# DSL 依赖解析本身
# ============================================================

def test_extract_field_refs_matches_evaluation_paths():
    """依赖清单必须与实际求值路径一致: any() 里的成员属性名不是字段。"""
    refs = extract_field_refs(
        'any(field.fact.natural.other_sensitive_areas.area_type in ["生态保护红线"])'
        ' AND field.fact.earthwork.borrow.value > 0')
    assert refs == ["field.fact.natural.other_sensitive_areas",
                    "field.fact.earthwork.borrow"]


def test_transform_result_passes_closed_set_validation():
    """全部生效 registry 里的 when 表达式都必须落在闭集内。"""
    import yaml
    from cpswc.paths import REGISTRIES_DIR

    for name in ("ObligationSet_v0.yaml", "AssuranceRegistry_v0.yaml"):
        doc = yaml.safe_load((REGISTRIES_DIR / name).read_text(encoding="utf-8"))
        section = doc.get("obligations") or doc.get("assurances") or {}
        for oid, odef in section.items():
            when = ((odef or {}).get("trigger") or {}).get("when")
            if not when or str(when).strip().lower() == "always":
                continue
            validate_transformed_expr(transform_dsl(str(when)))


def test_no_registry_obligation_falls_into_dsl_error():
    """生效 registry 的任何一条义务都不应因为 DSL 问题变成 ERROR。"""
    import yaml
    from cpswc.paths import REGISTRIES_DIR

    doc = yaml.safe_load(
        (REGISTRIES_DIR / "ObligationSet_v0.yaml").read_text(encoding="utf-8"))
    reg = doc.get("obligations") or {}
    r = evaluate_all(reg, {})
    errored = [d.obligation_id for d in r.obligation_details if d.is_error]
    assert errored == []
