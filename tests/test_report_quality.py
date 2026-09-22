"""
test_report_quality.py — P0-01 验收测试

对应 docs/report_production_plan/04_CONTRACTS_AND_ACCEPTANCE.md 第 9 节:

    S01  缺键/None/空白              → MISSING, 不转换为 0
    S02  数值 0 / 布尔 False         → PRESENT, 按类型正确判断
    S03  空 list 且无调查记录        → 不生成"经核查不涉及"
    S04  NaN/inf/错误单位/Quantity 空值 → INVALID 或 MISSING, 禁止参与有效计算
    S05  legacy snapshot 无 quality  → 可读, UNASSESSED/UNVERIFIED, 非已审
    Q01  父引言 FULL、叶子缺失       → 内容完成度不增加, 缺口仍在
    Q02  不存在完整要求清单          → coverage=unknown, 不显示 100%

测试夹具全部是原创合成数据, 不来自任何真实项目, 也不声称代表专业成果。
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.narrative.contract import (
    ContentRole, NarrativeBlock, NarrativeParagraph, RenderStatus,
)
from cpswc.report_quality import (
    Applicability, ContentRequirement, ContentRequirementSet, ContentState,
    EvidenceRecord, EvidenceState, QualityFinding, QualityInputs, ReviewLedger,
    ReviewRecord, ReviewState, Severity, ValueKind, ValueState,
    compute_quality_input_hash, evaluate_report_quality, resolve_from,
    resolve_value,
)


# ============================================================
# S01 — 缺键 / None / 空白字符串 → MISSING, 绝不转 0
# ============================================================

def test_s01_missing_key_is_missing_not_zero():
    rv = resolve_from({}, "field.fact.earthwork.borrow", kind=ValueKind.QUANTITY)
    assert rv.state is ValueState.MISSING
    assert rv.value is None, "缺键绝不能被填成 0"
    assert not rv.is_usable_number


def test_s01_none_value_is_missing():
    rv = resolve_from({"field.x": None}, "field.x")
    assert rv.state is ValueState.MISSING
    assert "None" in rv.note


def test_s01_blank_string_is_missing():
    for blank in ("", "   ", "\t\n"):
        rv = resolve_from({"field.x": blank}, "field.x", kind=ValueKind.TEXT)
        assert rv.state is ValueState.MISSING, f"{blank!r} 应判 MISSING"


def test_s01_quantity_with_null_value_is_missing():
    """04 文档: {"value": null, "unit": "万m³"} 仍是 MISSING。"""
    rv = resolve_from({"field.x": {"value": None, "unit": "万m³"}}, "field.x",
                      kind=ValueKind.QUANTITY)
    assert rv.state is ValueState.MISSING


def test_s01_missing_display_is_not_a_dash():
    """缺失不能显示成"—": 短横线看起来像一个已填写的数据。"""
    rv = resolve_from({}, "field.x")
    assert rv.display() == "（缺）"
    assert "—" not in rv.display()


def test_s01_missing_produces_finding_with_stable_code():
    rv = resolve_from({}, "field.fact.land.total_area", kind=ValueKind.QUANTITY)
    f = rv.to_finding()
    assert f is not None
    assert f.code == "VALUE_MISSING"
    assert f.target_ref == "field.fact.land.total_area"
    assert "field.fact.land.total_area" in f.missing_input_refs


# ============================================================
# S02 — 数值 0 / 布尔 False 是有效值
# ============================================================

def test_s02_zero_is_present():
    rv = resolve_from({"field.x": {"value": 0, "unit": "万m³"}}, "field.x",
                      kind=ValueKind.QUANTITY)
    assert rv.state is ValueState.PRESENT
    assert rv.value == 0
    assert rv.is_usable_number
    assert rv.to_finding() is None


def test_s02_bare_zero_number_is_present():
    rv = resolve_from({"field.x": 0}, "field.x", kind=ValueKind.NUMBER)
    assert rv.state is ValueState.PRESENT
    assert rv.value == 0


def test_s02_false_is_present_and_not_a_number():
    rv = resolve_from({"field.x": False}, "field.x", kind=ValueKind.BOOL)
    assert rv.state is ValueState.PRESENT
    assert rv.value is False
    assert not rv.is_usable_number, "bool 不得当数值使用"


def test_s02_zero_and_missing_are_distinguishable():
    """这条是 P0 的核心: 填了 0 和没填, 必须能分开。"""
    zero = resolve_from({"field.x": {"value": 0, "unit": "万m³"}}, "field.x")
    absent = resolve_from({}, "field.x")
    assert zero.state is not absent.state
    assert zero.value == 0 and absent.value is None


# ============================================================
# S03 — 空 list 是"提供了空容器", 不是"已核查不涉及"
# ============================================================

def test_s03_empty_list_is_present_but_flagged_as_empty_container():
    rv = resolve_from({"field.x": []}, "field.x", kind=ValueKind.LIST)
    assert rv.state is ValueState.PRESENT
    assert rv.is_empty_container
    assert "不能独自证明" in rv.note


def test_s03_empty_list_does_not_support_judgment():
    """空清单不构成"已核查不涉及"的证据 —— 没有复核记录就不支持判断。"""
    ledger = ReviewLedger(QualityInputs(is_legacy=True), "hash_abc")
    assert ledger.supports_judgment("sec.project_overview.sensitive_areas") is False


def test_s03_empty_list_vs_missing_list():
    provided = resolve_from({"field.x": []}, "field.x", kind=ValueKind.LIST)
    absent = resolve_from({}, "field.x", kind=ValueKind.LIST)
    assert provided.state is ValueState.PRESENT
    assert absent.state is ValueState.MISSING


# ============================================================
# S04 — NaN / inf / 非法单位 / 非法数字串
# ============================================================

@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_s04_nan_inf_are_invalid(bad):
    rv = resolve_from({"field.x": {"value": bad, "unit": "万m³"}}, "field.x",
                      kind=ValueKind.QUANTITY)
    assert rv.state is ValueState.INVALID
    assert not rv.is_usable_number, "NaN/inf 禁止参与有效计算"


def test_s04_bare_nan_is_invalid():
    rv = resolve_from({"field.x": float("nan")}, "field.x", kind=ValueKind.NUMBER)
    assert rv.state is ValueState.INVALID


def test_s04_non_numeric_string_in_quantity_is_invalid():
    rv = resolve_from({"field.x": {"value": "约三万", "unit": "万m³"}}, "field.x",
                      kind=ValueKind.QUANTITY)
    assert rv.state is ValueState.INVALID


def test_s04_quantity_without_unit_is_invalid():
    rv = resolve_from({"field.x": {"value": 3.5}}, "field.x",
                      kind=ValueKind.QUANTITY)
    assert rv.state is ValueState.INVALID
    assert "缺单位" in rv.note


def test_s04_unregistered_unit_is_invalid():
    rv = resolve_from({"field.x": {"value": 3.5, "unit": "立方"}}, "field.x",
                      kind=ValueKind.QUANTITY)
    assert rv.state is ValueState.INVALID
    assert "未登记单位" in rv.note


def test_s04_dimensionless_number_needs_no_unit():
    """土壤流失控制比是无量纲比值, 不能因为"没单位"就判非法。"""
    rv = resolve_from({"field.x": 1.2}, "field.x", kind=ValueKind.NUMBER)
    assert rv.state is ValueState.PRESENT


def test_s04_display_symbol_is_not_a_business_value():
    """"/" 是显示符号, 不是业务值, 不得参与运算。"""
    rv = resolve_from({"field.x": "/"}, "field.x")
    assert rv.state is ValueState.NOT_APPLICABLE
    assert not rv.is_usable_number


# ============================================================
# S05 — legacy 输入不自动获得"已审核"
# ============================================================

def test_s05_legacy_without_quality_inputs_is_unassessed():
    qi = QualityInputs.from_raw(None)
    assert qi.is_legacy
    assert qi.evidence_records == []
    assert qi.review_records == []

    ledger = ReviewLedger(qi, "hash_abc")
    assert ledger.evidence_state("sec.conclusion") is EvidenceState.UNASSESSED
    assert ledger.review_state("sec.conclusion")[0] is ReviewState.NOT_REVIEWED
    assert ledger.supports_judgment("sec.conclusion") is False


def test_s05_adapter_never_fabricates_a_reviewer():
    """系统不得自行填写人名。"""
    qi = QualityInputs.from_raw({})
    assert all(not r.verified_by for r in qi.evidence_records)
    assert all(not r.reviewer_ref for r in qi.review_records)


def test_s05_self_declared_verified_without_locator_is_not_verified():
    """自称 VERIFIED 但没有原始证据定位/版本对应, 不算已核验。"""
    rec = EvidenceRecord(evidence_id="e1", verification_status="VERIFIED",
                         verified_by="张三", verified_at="2026-09-20")
    assert rec.is_verified is False, "缺 content_sha256 与 locator 不应算已核验"

    rec2 = EvidenceRecord(evidence_id="e2", verification_status="VERIFIED",
                          verified_by="张三", verified_at="2026-09-20",
                          locator="设计说明书 p.42 表 4-1")
    assert rec2.is_verified is True


def test_s05_render_status_full_does_not_imply_review_confirmed():
    """旧 RenderStatus.FULL 不能映射成 ReviewState.CONFIRMED。"""
    block = NarrativeBlock(section_id="sec.conclusion", title="结论",
                           render_status=RenderStatus.FULL,
                           paragraphs=[NarrativeParagraph(
                               text="x", evidence_refs=["field.x"])],
                           variant_id="default", template_id="t")
    summary = evaluate_report_quality(context={}, narrative=[block])
    sq = summary.sections[0]
    assert sq.render_status == "full"
    assert sq.review_state is ReviewState.NOT_REVIEWED
    assert sq.content_state is ContentState.DRAFTED
    assert sq.content_state is not ContentState.COMPLETE


# ============================================================
# Q01 — 父标题引言不计成果
# ============================================================

def _parent_intro_block():
    return NarrativeBlock(
        section_id="sec.topsoil", title="表土资源保护与利用",
        render_status=RenderStatus.FULL,
        content_role=ContentRole.PARENT_INTRO,
        paragraphs=[NarrativeParagraph(text="本章论述表土的剥离、保存和回覆利用方案。",
                                       evidence_refs=["sec.topsoil.stripping"])],
        variant_id="default", template_id="nt.parent_intro.v1")


def _missing_leaf_block():
    return NarrativeBlock(
        section_id="sec.topsoil.stripping", title="表土剥离",
        render_status=RenderStatus.SKELETON)


def test_q01_parent_intro_does_not_count_as_completed_content():
    reqs = ContentRequirementSet(
        source_ref="fixture.synthetic.content_requirements",
        verified=False,
        requirements=[
            ContentRequirement("req.topsoil", "sec.topsoil", "表土章", is_leaf=False),
            ContentRequirement("req.topsoil.stripping", "sec.topsoil.stripping",
                               "表土剥离"),
        ])
    summary = evaluate_report_quality(
        context={}, narrative=[_parent_intro_block(), _missing_leaf_block()],
        content_requirements=reqs)

    assert summary.parent_intro_block_count == 1
    assert summary.applicable_leaf_count == 1, "父章节不进叶子分母"
    assert summary.complete_leaf_count == 0, "叶子缺失时完成数不得增加"
    assert summary.content_coverage == 0.0
    # 缺口仍在
    assert any(f.code == "CONTENT_INCOMPLETE" for f in summary.findings)


def test_q01_parent_intro_section_quality_is_marked():
    summary = evaluate_report_quality(context={},
                                      narrative=[_parent_intro_block()])
    sq = next(s for s in summary.sections if s.section_id == "sec.topsoil")
    assert sq.is_parent_intro is True
    assert sq.content_state is not ContentState.COMPLETE


def test_q01_rendered_block_count_is_labelled_as_render_only():
    summary = evaluate_report_quality(context={},
                                      narrative=[_parent_intro_block()])
    assert summary.rendered_block_count == 1
    d = summary.to_dict()
    assert "不代表专业完成" in d["render_layer"]["note"]


# ============================================================
# Q02 — 没有内容规范清单时, 不许显示 100%
# ============================================================

def test_q02_no_requirements_means_coverage_unknown():
    summary = evaluate_report_quality(context={}, narrative=[_parent_intro_block(),
                                                             _missing_leaf_block()])
    assert summary.coverage_state == "unknown"
    assert summary.content_coverage is None
    assert "未知" in summary.coverage_display()
    assert "100%" not in summary.coverage_display()
    assert summary.unassessed_requirement_count > 0


def test_q02_empty_requirement_set_also_unknown():
    reqs = ContentRequirementSet(requirements=[])
    summary = evaluate_report_quality(context={}, narrative=[_missing_leaf_block()],
                                      content_requirements=reqs)
    assert summary.coverage_state == "unknown"
    assert summary.content_coverage is None


def test_q02_summary_always_reports_subcounts():
    """汇总必须保留分项数量, 不只给总分。"""
    summary = evaluate_report_quality(context={}, narrative=[_missing_leaf_block()])
    counts = summary.to_dict()["counts"]
    for key in ("unresolved_critical_count", "unknown_applicability_count",
                "missing_artifact_count", "unreviewed_requirement_count",
                "unassessed_requirement_count", "render_error_count"):
        assert key in counts


def test_q02_is_submittable_never_set_by_quality_layer():
    """is_submittable 只能来自正式门禁 (P0-08), 质量层永远返回 None。"""
    summary = evaluate_report_quality(context={}, narrative=[_parent_intro_block()])
    assert summary.is_submittable is None


def test_q02_unimplemented_requirement_stays_in_denominator():
    """模板没实现的必需内容仍进分母, 不能从分母里删掉 (验收 R02 的 A 批部分)。"""
    reqs = ContentRequirementSet(requirements=[
        ContentRequirement("req.x", "sec.x", "尚未实现的必需内容", implemented=False),
    ])
    summary = evaluate_report_quality(context={}, narrative=[], content_requirements=reqs)
    assert summary.applicable_leaf_count == 1
    assert summary.unimplemented_leaf_count == 1
    assert summary.complete_leaf_count == 0


# ============================================================
# 诊断码与输入指纹的基本约束
# ============================================================

def test_unregistered_finding_code_is_rejected():
    """诊断码必须静态登记, 不允许运行时拼接。"""
    with pytest.raises(ValueError):
        QualityFinding(code="I_JUST_MADE_THIS_UP", severity=Severity.WARN,
                       message="x")


def test_quality_input_hash_is_stable_and_order_independent():
    a = compute_quality_input_hash({"b": 1, "a": 2}, {"z": 3})
    b = compute_quality_input_hash({"a": 2, "b": 1}, {"z": 3})
    assert a == b


def test_quality_input_hash_changes_when_any_consumed_value_changes():
    a = compute_quality_input_hash({"field.fact.project.name": "甲项目"}, {})
    b = compute_quality_input_hash({"field.fact.project.name": "乙项目"}, {})
    assert a != b


def test_quality_input_hash_rejects_nan_into_a_stable_marker():
    """NaN 不进语义 hash, 但也不能让 hash 计算崩掉。"""
    h = compute_quality_input_hash({"x": float("nan")}, {})
    assert isinstance(h, str) and len(h) == 64
