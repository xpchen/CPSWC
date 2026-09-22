"""
test_a_batch_review_regressions.py — A 批验收意见的四项反例回归

来源: 2026-09-20 项目负责人对 A 批的独立验收。验收方在既有 217 条测试之外
补构造反例, 发现四个漏洞。本文件逐条锁定, 防止回归。

    R-1  复核记录只校验 hash, 不校验完整性 → 空壳记录可输出专业肯定结论
    R-2  复核记录可以盖过已知的不达标 / 数据缺失
    R-3  非法数值与"清单成员缺关键属性"仍被判成"不触发"
    R-4  三值逻辑遇非法输入时抛异常退出, 丢掉另一分支已确定的 True

另附"有复核记录 × 数据有问题"的组合矩阵 —— 验收意见特别要求覆盖这一组。

夹具全部为原创合成数据。其中的 EvidenceRecord / ReviewRecord 是为测试构造的
技术结构, **不代表任何真实工程师的专业确认**, 也不声称验证了签名真实性。
"""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.condition_engine import (
    EvaluationStatus, evaluate_all, evaluate_obligation,
)
from cpswc.narrative.contract import AssertionClass
from cpswc.narrative.evidence import SectionEvidence
from cpswc.narrative.templates.sec_7_5_benefit_analysis import (
    render as render_benefit,
)
from cpswc.paths import REGISTRIES_DIR
from cpswc.report_quality import (
    EvidenceRecord, QualityInputs, ReviewLedger, ReviewRecord, ReviewState,
    Severity, compute_quality_input_hash,
)

SEC = "sec.soil_loss_prevention.benefit_analysis"


def _ob(when: str) -> dict:
    return {"trigger": {"mode": "conditional", "when": when}}


def _inputs(review_kwargs: dict, *, evidence: list | None = None) -> QualityInputs:
    return QualityInputs(
        evidence_records=evidence or [],
        review_records=[ReviewRecord(**review_kwargs)])


def _complete_inputs(target: str, input_hash: str) -> QualityInputs:
    """一条完整成形的复核记录 + 它引用的证据记录。"""
    return _inputs(
        dict(review_id="rev.full", target_refs=[target], input_hash=input_hash,
             verdict="CONFIRMED", reviewer_ref="fixture.synthetic.reviewer",
             reviewed_at="2026-09-20", evidence_refs=["ev.full"]),
        evidence=[EvidenceRecord(evidence_id="ev.full", target_refs=[target],
                                 locator="fixture.synthetic 合成夹具")])


# ============================================================
# R-1 — 复核记录必须成形, 才谈得上是一次专业确认
# ============================================================

_H = compute_quality_input_hash({"field.fact.project.name": "甲"}, {})


@pytest.mark.parametrize("label,kwargs,evidence", [
    ("全空壳", dict(), []),
    ("只有审核人", dict(reviewer_ref="X"), []),
    ("有人有时间无证据", dict(reviewer_ref="X", reviewed_at="2026-09-20"), []),
    ("证据引用悬空",
     dict(reviewer_ref="X", reviewed_at="2026-09-20", evidence_refs=["ev.nope"]), []),
    ("所引证据已被否决",
     dict(reviewer_ref="X", reviewed_at="2026-09-20", evidence_refs=["ev.1"]),
     [EvidenceRecord(evidence_id="ev.1", locator="p.1",
                     verification_status="REJECTED")]),
])
def test_r1_incomplete_review_never_reaches_confirmed(label, kwargs, evidence):
    """只要对上 input_hash 就升级为 CONFIRMED —— 这是验收复现的漏洞。"""
    qi = _inputs(dict(review_id="r", target_refs=["sec.x"], input_hash=_H,
                      verdict="CONFIRMED", **kwargs), evidence=evidence)
    ledger = ReviewLedger(qi, _H)
    state, _ = ledger.review_state("sec.x")
    assert state is not ReviewState.CONFIRMED, f"{label} 不应成为专业确认"
    assert ledger.supports_judgment("sec.x") is False


@pytest.mark.parametrize("label,kwargs,evidence", [
    ("全空壳", dict(), []),
    ("证据引用悬空",
     dict(reviewer_ref="X", reviewed_at="2026-09-20", evidence_refs=["ev.nope"]), []),
])
def test_r1_incomplete_review_produces_a_locatable_finding(label, kwargs, evidence):
    qi = _inputs(dict(review_id="r", target_refs=["sec.x"], input_hash=_H,
                      verdict="CONFIRMED", **kwargs), evidence=evidence)
    f = ReviewLedger(qi, _H).stale_finding("sec.x")
    assert f is not None and f.code == "REVIEW_INCOMPLETE"
    assert f.severity is Severity.BLOCK
    assert f.target_ref == "sec.x"
    assert f.remediation, "必须告诉使用者补什么才算成形"


def test_r1_complete_review_still_works():
    """收紧不能把正常路径也堵死。"""
    ledger = ReviewLedger(_complete_inputs("sec.x", _H), _H)
    assert ledger.review_state("sec.x")[0] is ReviewState.CONFIRMED
    assert ledger.supports_judgment("sec.x") is True
    assert ledger.stale_finding("sec.x") is None


def test_r1_rejected_verdict_does_not_require_completeness():
    """否决方向保守: 驳回一个结论不需要额外证据。"""
    qi = _inputs(dict(review_id="r", target_refs=["sec.x"], input_hash=_H,
                      verdict="REJECTED"))
    ledger = ReviewLedger(qi, _H)
    assert ledger.review_state("sec.x")[0] is ReviewState.REJECTED
    assert ledger.supports_judgment("sec.x") is False


def test_r1_completeness_gaps_are_enumerated():
    rec = ReviewRecord(review_id="r", target_refs=["sec.x"], verdict="CONFIRMED")
    gaps = rec.completeness_gaps({})
    assert any("reviewer_ref" in g for g in gaps)
    assert any("reviewed_at" in g for g in gaps)
    assert any("evidence_refs" in g for g in gaps)
    assert any("input_hash" in g for g in gaps)


# ============================================================
# R-2 — 复核记录是必要条件, 不是通行证
# ============================================================

_WT = {"control_degree": 95, "soil_loss_control_ratio": 1.0,
       "spoil_protection_rate": 95, "topsoil_protection_rate": 92,
       "vegetation_restoration_rate": 97, "vegetation_coverage_rate": 22}


def _benefit_with_review(derived: dict):
    h = compute_quality_input_hash({}, derived)
    return render_benefit({}, derived, set(),
                          ledger=ReviewLedger(_complete_inputs(SEC, h), h))


def test_r2_review_cannot_override_a_known_shortfall():
    """验收复现的原始反例: 目标 95 / 效果 80 / 另五项缺失 + 一条匹配的复核记录。

    旧行为: 同一节同时出现"该指标未达到目标值"和"各项防治目标可以实现"。
    """
    derived = {
        "field.derived.target.weighted_comprehensive_target": dict(_WT),
        "field.derived.target.control_degree": {
            "value": 95, "unit": "%", "actual_derived": 80},
    }
    block = _benefit_with_review(derived)
    text = "".join(p.text for p in block.paragraphs)
    assert "各项防治目标可以实现" not in text
    assert not [p for p in block.paragraphs
                if p.assertion_class is AssertionClass.PROJECT_JUDGMENT]


def test_r2_blocked_conclusion_explains_why():
    """不是笼统"待复核", 要说清是哪几条前提没站住。"""
    derived = {
        "field.derived.target.weighted_comprehensive_target": dict(_WT),
        "field.derived.target.control_degree": {
            "value": 95, "unit": "%", "actual_derived": 80},
    }
    block = _benefit_with_review(derived)
    conclusion = block.paragraphs[-1].text
    assert "未成立的原因" in conclusion
    assert "尚无效果计算结果" in conclusion


def test_r2_review_present_but_blocked_is_recorded_distinctly():
    """有复核记录却仍被数据问题挡住, 必须留痕 —— 否则会被误读成"没人复核"。"""
    derived = {
        "field.derived.target.weighted_comprehensive_target": dict(_WT),
        "field.derived.target.control_degree": {
            "value": 95, "unit": "%", "actual_derived": 80},
    }
    block = _benefit_with_review(derived)
    msgs = [f.message for f in block.quality_findings
            if f.code == "ASSERTION_UNSUPPORTED"]
    assert msgs, "应有断言未获支持的诊断"
    assert any("前提未满足" in m for m in msgs)


def test_r2_section_level_review_does_not_authorize_everything():
    """章节级确认不能自动授权该节所有肯定判断。"""
    ev = SectionEvidence("sec.x", {}, {})
    ev.quantity("field.fact.missing.one")      # 制造一条 BLOCK 数据诊断
    h = compute_quality_input_hash({}, {})
    ev.ledger = ReviewLedger(_complete_inputs("sec.x", h), h)
    p = ev.judgment("本节结论成立。", target_ref="sec.x",
                    pending_text="本节暂不作结论。")
    assert p.assertion_class is AssertionClass.GAP_STATEMENT
    assert "阻断性问题" in p.text


def test_r2_judgment_passes_when_data_is_clean():
    """有复核记录且数据干净时仍应放行 —— 收紧不等于全盘堵死。"""
    ev = SectionEvidence("sec.x", {"field.fact.ok": 1}, {})
    ev.raw("field.fact.ok")
    h = compute_quality_input_hash({}, {})
    ev.ledger = ReviewLedger(_complete_inputs("sec.x", h), h)
    p = ev.judgment("本节结论成立。", target_ref="sec.x",
                    pending_text="本节暂不作结论。")
    assert p.assertion_class is AssertionClass.PROJECT_JUDGMENT
    assert p.review_refs == ["rev.full"]


def test_r2_unmet_precondition_alone_blocks_the_judgment():
    ev = SectionEvidence("sec.x", {}, {})
    h = compute_quality_input_hash({}, {})
    ev.ledger = ReviewLedger(_complete_inputs("sec.x", h), h)
    p = ev.judgment("本节结论成立。", target_ref="sec.x",
                    pending_text="本节暂不作结论。",
                    preconditions=[(False, "六项指标效果尚未齐全")])
    assert p.assertion_class is AssertionClass.GAP_STATEMENT
    assert "六项指标效果尚未齐全" in p.text


def test_r2_warn_level_findings_do_not_block():
    """只有 BLOCK 级问题阻断结论; WARN 不应把正常路径堵死。"""
    ev = SectionEvidence("sec.x", {}, {})
    ev.quantity("field.fact.optional", severity=Severity.WARN)
    h = compute_quality_input_hash({}, {})
    ev.ledger = ReviewLedger(_complete_inputs("sec.x", h), h)
    p = ev.judgment("本节结论成立。", target_ref="sec.x",
                    pending_text="本节暂不作结论。")
    assert p.assertion_class is AssertionClass.PROJECT_JUDGMENT


def test_r2_sibling_judgment_failure_does_not_block_another_target():
    """同一节里两个独立子判断互不牵连 (如敏感区的重点防治区核查 vs 12 类排查)。"""
    ev = SectionEvidence("sec.x", {}, {})
    h = compute_quality_input_hash({}, {})
    ev.ledger = ReviewLedger(_complete_inputs("sec.x.b", h), h)
    a = ev.judgment("A 成立。", target_ref="sec.x.a", pending_text="A 待定。")
    assert a.assertion_class is AssertionClass.GAP_STATEMENT   # A 无复核记录
    b = ev.judgment("B 成立。", target_ref="sec.x.b", pending_text="B 待定。")
    assert b.assertion_class is AssertionClass.PROJECT_JUDGMENT, \
        "A 的失败不应牵连 B"


# ============================================================
# R-3 — 非法数值与成员属性缺失
# ============================================================

@pytest.mark.parametrize("raw", ["NaN", "nan", "-Infinity", "inf", "Infinity"])
def test_r3_non_finite_string_is_unknown_not_false(raw):
    """float("NaN") / float("inf") 都会成功。不查有限性的话:
    NaN > 0 静默判 False, inf > 0 更会**伪造出一个触发**。"""
    d = evaluate_obligation("ob.x", _ob("field.a.value > 0"),
                            {"field.a": {"value": raw, "unit": "万m³"}})
    assert d.triggered is None
    assert d.evaluation_status is EvaluationStatus.UNKNOWN_INVALID_INPUT


def test_r3_non_finite_never_fabricates_a_trigger():
    d = evaluate_obligation("ob.x", _ob("field.a.value > 0"),
                            {"field.a": {"value": "inf", "unit": "万m³"}})
    assert d.triggered is not True


def test_r3_list_member_missing_attribute_is_unknown():
    """提供了清单但成员缺关键属性 ≠ 明确没有涉及。"""
    d = evaluate_obligation(
        "ob.x", _ob('any(field.a.b.flag in [true])'),
        {"field.a.b": [{}]})
    assert d.triggered is None
    assert "缺少属性" in (d.diagnostic_message or "")


def test_r3_real_registry_obligation_with_bare_member():
    """用实际登记的义务复现: 临时堆土场清单 [{}] 缺 outside_permanent_land。"""
    reg = yaml.safe_load(
        (REGISTRIES_DIR / "ObligationSet_v0.yaml").read_text(encoding="utf-8"))
    ob_id = "ob.disposal_site.land_use_approval"
    d = evaluate_obligation(ob_id, reg["obligations"][ob_id],
                            {"field.fact.construction.temp_topsoil_site": [{}]})
    assert d.triggered is None, "缺成员属性不得判成不触发"


def test_r3_member_attribute_present_still_evaluates():
    reg = yaml.safe_load(
        (REGISTRIES_DIR / "ObligationSet_v0.yaml").read_text(encoding="utf-8"))
    ob_id = "ob.disposal_site.land_use_approval"
    ob_def = reg["obligations"][ob_id]
    hit = evaluate_obligation(ob_id, ob_def, {
        "field.fact.construction.temp_topsoil_site": [{"outside_permanent_land": True}]})
    miss = evaluate_obligation(ob_id, ob_def, {
        "field.fact.construction.temp_topsoil_site": [{"outside_permanent_land": False}]})
    empty = evaluate_obligation(ob_id, ob_def, {
        "field.fact.construction.temp_topsoil_site": []})
    assert hit.triggered is True
    assert miss.triggered is False
    assert empty.triggered is False, "明确提供空清单是可确定的 False"


def test_r3_any_in_member_level_three_valued():
    """成员级也走三值: 有一个成员确定命中 → True, 哪怕另一个成员缺属性。"""
    d = evaluate_obligation(
        "ob.x", _ob('any(field.a.b.flag in [true])'),
        {"field.a.b": [{}, {"flag": True}]})
    assert d.triggered is True


def test_r3_count_distinct_with_missing_member_attribute_is_unknown():
    d = evaluate_obligation(
        "ob.x", _ob("count(distinct(field.a.b.level)) >= 2"),
        {"field.a.b": [{"level": "1级"}, {}]})
    assert d.triggered is None


# ============================================================
# R-4 — 非法输入只让本分支未知, 不掀掉整条表达式
# ============================================================

def test_r4_type_error_branch_does_not_lose_a_determined_true():
    """验收复现: 左侧已为 True, 右侧类型错 → 旧实现整条返回 UNKNOWN。"""
    d = evaluate_obligation(
        "ob.x", _ob("field.a.value > 0 OR field.b.value > 0"),
        {"field.a": {"value": 1, "unit": "万m³"}, "field.b": []})
    assert d.triggered is True
    assert d.evaluation_status is EvaluationStatus.EVALUATED


def test_r4_branch_error_is_still_reported():
    """结果不受影响, 不等于问题可以消失。"""
    d = evaluate_obligation(
        "ob.x", _ob("field.a.value > 0 OR field.b.value > 0"),
        {"field.a": {"value": 1, "unit": "万m³"}, "field.b": []})
    assert d.diagnostic_code == "CONDITION_UNKNOWN"
    assert "分支输入错误" in d.diagnostic_message
    assert "field.b" in d.diagnostic_message


@pytest.mark.parametrize("left,op,expected", [
    (1, "OR", True),     # TRUE  OR  UNKNOWN = TRUE
    (0, "OR", None),     # FALSE OR  UNKNOWN = UNKNOWN
    (1, "AND", None),    # TRUE  AND UNKNOWN = UNKNOWN
    (0, "AND", False),   # FALSE AND UNKNOWN = FALSE
])
def test_r4_three_valued_logic_holds_for_invalid_branches(left, op, expected):
    """非法输入分支必须和"缺失"分支一样参与三值组合。"""
    d = evaluate_obligation(
        "ob.x", _ob(f"field.a.value > 0 {op} field.b.value > 0"),
        {"field.a": {"value": left, "unit": "万m³"}, "field.b": []})
    assert d.triggered is expected


def test_r4_grammar_error_is_still_an_error_not_unknown():
    """输入错误降级为分支未知, 但 DSL 语法错误仍独立报 ERROR。"""
    d = evaluate_obligation("ob.x", _ob("field.a.value >> 0"),
                            {"field.a": {"value": 1, "unit": "万m³"}})
    assert d.evaluation_status is EvaluationStatus.ERROR_DSL
    assert d.diagnostic_code == "CONDITION_ERROR"


def test_r4_invalid_branch_never_lands_in_not_triggered():
    reg = {"ob.x": _ob("field.a.value > 0 OR field.b.value > 0")}
    r = evaluate_all(reg, {"field.a": {"value": 0, "unit": "万m³"},
                           "field.b": []})
    assert "ob.x" in r.unknown
    assert "ob.x" not in r.not_triggered


# ============================================================
# 组合矩阵: 有复核记录 × 数据有问题
# ============================================================

_SCENARIOS = [
    ("数据齐全且已确认来源", True, True, False),
    ("效果全缺", False, False, False),
    ("效果候选未确认来源", False, True, False),
    ("已确认但低于目标", False, True, True),
]


@pytest.mark.parametrize("label,expect_judgment,has_candidate,below_target",
                         _SCENARIOS, ids=[s[0] for s in _SCENARIOS])
def test_review_plus_data_combination_matrix(label, expect_judgment,
                                             has_candidate, below_target):
    """有复核记录的前提下, 数据的四种状态分别该得到什么结论。"""
    derived = {"field.derived.target.weighted_comprehensive_target": dict(_WT)}
    confirmed_keys = []
    if has_candidate:
        effect = 80 if below_target else 99
        for key in _WT:
            derived[f"field.derived.target.{key}"] = {
                "value": _WT[key], "unit": "%", "actual_derived": effect}
        if label != "效果候选未确认来源":
            confirmed_keys = list(_WT)

    h = compute_quality_input_hash({}, derived)
    qi = _complete_inputs(SEC, h)
    for key in confirmed_keys:
        field_id = f"field.derived.target.{key}"
        qi.evidence_records.append(EvidenceRecord(
            evidence_id=f"ev.{key}", target_refs=[field_id],
            source_kind="calculation", locator="fixture.synthetic 合成夹具",
            content_sha256="0" * 64, verification_status="VERIFIED",
            verified_by="fixture.synthetic.reviewer", verified_at="2026-09-20"))

    block = render_benefit(
        {"field.fact.prediction.total_loss": {"value": 10, "unit": "t"},
         "field.fact.prediction.new_loss": {"value": 5, "unit": "t"},
         "field.fact.prediction.reducible_loss": {"value": 3, "unit": "t"},
         "field.fact.land.total_area": {"value": 9.5, "unit": "hm²"}},
        derived, set(), ledger=ReviewLedger(qi, h))

    judgments = [p for p in block.paragraphs
                 if p.assertion_class is AssertionClass.PROJECT_JUDGMENT]
    assert bool(judgments) is expect_judgment, f"{label}: 结论输出与预期不符"
    if not expect_judgment:
        text = "".join(p.text for p in block.paragraphs)
        assert "各项防治目标可以实现" not in text
