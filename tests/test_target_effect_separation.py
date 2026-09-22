"""
test_target_effect_separation.py — P0-03 验收测试 (目标/效果分离部分)

对应 04_CONTRACTS_AND_ACCEPTANCE.md 第 9 节:

    N04  仅有加权目标        → 表文只显示目标, 效果待计算, 不达标
    N05  效果低于目标        → 该指标不达标; 总述不得"各项均达标"
    N06  部分效果缺失/分母 0 → 未决或有依据 N/A, 不强行 100%

背景 (implementation/P0_BASELINE.md PROBE-2 与 D03):
  现有样本里 `field.derived.target.control_degree.value` 存的是**目标值**
  (如"南方红壤区一级标准 = 98"), 效果值放在同结构的 `actual_derived` 里,
  且没有计算方法、输入绑定或复核记录。旧表格实现把 `value` 当实现值,
  于是目标和自己比较, 六行全部"达标"。

  本文件锁定: 目标只能当目标; 没有效果结果就是"待计算"; 效果不低于目标时
  也只到"待复核"——机器检查不能替专业判断下达标结论。

  本文件**不**新增任何效果计算器, 夹具里的效果值是原创合成数据,
  不代表真实专业设计成果。

A 批验收后的收紧 (不是放松):
  验收意见指出 `actual_derived` 也只是**候选**效果输入, 名称本身不证明可信。
  因此候选值一律不进入达标比较, 只有该字段有可解析、未被否决的证据记录
  (EvidenceState.READY) 时才比较。

  这让 N05 "效果低于目标 → 未达标" 的前置条件变严了: 测试必须先构造一条
  完整的证据记录, 才谈得上比较。断言本身没有放松 —— 未达标仍必须被判出来,
  而且多了一层"来源未确认时连比较都不做"的保护。
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.narrative.contract import AssertionClass
from cpswc.report_quality import (
    EvidenceRecord, QualityInputs, ReviewLedger, compute_quality_input_hash,
)
from cpswc.narrative.templates.sec_7_5_benefit_analysis import (
    INDICATOR_LABELS, render as render_benefit,
)
from cpswc.renderers.table_projections import project_six_indicator_review

WEIGHTED_TARGET = {
    "control_degree": 95,
    "soil_loss_control_ratio": 1.0,
    "spoil_protection_rate": 95,
    "topsoil_protection_rate": 92,
    "vegetation_restoration_rate": 97,
    "vegetation_coverage_rate": 22,
}

TARGET_ONLY = {"field.derived.target.weighted_comprehensive_target": WEIGHTED_TARGET}


def _text(block) -> str:
    return "".join(p.text for p in block.paragraphs)


def _classes(block) -> set:
    return {p.assertion_class for p in block.paragraphs}


def _confirmed_evidence(*indicator_keys: str) -> dict:
    """为指定指标构造**已核验**的证据记录 (合成夹具, 无真实出处)。"""
    return {"evidence_records": [
        {"evidence_id": f"ev.{k}",
         "target_refs": [f"field.derived.target.{k}"],
         "source_kind": "calculation",
         "locator": "fixture.synthetic 合成夹具",
         "content_sha256": "0" * 64,
         "verification_status": "VERIFIED",
         "verified_by": "fixture.synthetic.reviewer",
         "verified_at": "2026-09-20"}
        for k in indicator_keys]}


def _rows(derived: dict, confirmed: tuple[str, ...] = ()) -> dict:
    snapshot = {"derived_fields": derived, "_original_facts": {}}
    if confirmed:
        snapshot["quality_inputs"] = _confirmed_evidence(*confirmed)
    td = project_six_indicator_review(snapshot)
    return {r["indicator"]: r for r in td.rows}


def _ledger(derived: dict, confirmed: tuple[str, ...] = ()) -> ReviewLedger:
    from cpswc.report_quality import ledger_from_snapshot
    snapshot = {"derived_fields": derived, "_original_facts": {}}
    if confirmed:
        snapshot["quality_inputs"] = _confirmed_evidence(*confirmed)
    return ledger_from_snapshot(snapshot)


# ============================================================
# N04 — 只有目标值
# ============================================================

def test_n04_targets_only_effects_are_pending():
    rows = _rows(TARGET_ONLY)
    for label, row in rows.items():
        assert row["target"] != "—", f"{label} 目标值应显示"
        assert row["actual"] == "待计算", f"{label} 无效果结果时不得填实现值"
        assert row["result"] == "待计算"


def test_n04_no_row_is_marked_compliant_from_targets_alone():
    rows = _rows(TARGET_ONLY)
    assert all(r["result"] != "达标" for r in rows.values())


def test_n04_target_is_never_copied_into_the_effect_column():
    """旧实现的精确回归: actual 曾经取 field.derived.target.<k>.value,
    而那个 value 正是目标值本身 —— 目标和自己比, 无条件达标。

    现在这个 value 只能作为**候选**出现, 明确标注来源, 且不参与比较。"""
    derived = dict(TARGET_ONLY)
    derived["field.derived.target.control_degree"] = {
        "value": 95, "unit": "%", "target_by_standard": "一级 = 95"}
    row = _rows(derived)["水土流失治理度 (%)"]
    assert "候选·待确认" in row["actual"], "value 不得被当成已确认的效果"
    assert "源自 value" in row["actual"], "必须说明候选值从哪个键来"
    assert row["result"] == "待确认效果来源"
    assert row["result"] != "达标"


def test_n04_candidate_value_is_preserved_not_discarded():
    """保守处理不等于丢数据: 原值与来源必须保留下来 (A 批验收建议)。"""
    row = _rows(_with_effect("control_degree", 80))["水土流失治理度 (%)"]
    assert "80" in row["actual"]
    assert "候选" in row["actual"]


def test_n04_narrative_marks_targets_as_targets():
    block = render_benefit({}, TARGET_ONLY, set())
    assert AssertionClass.TARGET_VALUE in _classes(block)
    assert AssertionClass.DESIGN_EFFECT not in _classes(block)
    text = _text(block)
    assert "以上为依据 GB/T 50434-2018 查表得到的目标要求" in text


def test_n04_narrative_refuses_the_attainment_claim():
    """PROBE-2 的精确回归。"""
    block = render_benefit({}, TARGET_ONLY, set())
    text = _text(block)
    assert "可达到上述目标值要求" not in text
    assert "各项防治目标可以实现" not in text
    assert "目标值不能替代效果计算" in text
    assert any(f.code == "VALUE_MISSING" for f in block.quality_findings)


def test_n04_no_project_judgment_without_review_record():
    block = render_benefit({}, TARGET_ONLY, set())
    assert not [p for p in block.paragraphs
                if p.assertion_class is AssertionClass.PROJECT_JUDGMENT]
    assert any(f.code == "ASSERTION_UNSUPPORTED" for f in block.quality_findings)


# ============================================================
# N05 — 效果低于目标
# ============================================================

def _with_effect(key: str, effect) -> dict:
    d = dict(TARGET_ONLY)
    d[f"field.derived.target.{key}"] = {
        "value": WEIGHTED_TARGET[key], "unit": "%", "actual_derived": effect}
    return d


def test_n05_confirmed_effect_below_target_is_marked_not_compliant():
    """来源已确认后, 低于目标必须判未达标。"""
    derived = _with_effect("control_degree", 80)
    row = _rows(derived, confirmed=("control_degree",))["水土流失治理度 (%)"]
    assert row["result"] == "未达标"
    assert row["actual"] == "80", "已确认的效果不再带候选标注"


def test_n05_unconfirmed_candidate_does_not_enter_comparison():
    """来源未确认时连比较都不做 —— 否则可能把一个目标值判成"未达标"。"""
    row = _rows(_with_effect("control_degree", 80))["水土流失治理度 (%)"]
    assert row["result"] == "待确认效果来源"
    assert row["result"] not in ("未达标", "达标", "待复核")


def test_n05_narrative_names_the_shortfall():
    derived = _with_effect("control_degree", 80)
    block = render_benefit({}, derived, set(),
                           ledger=_ledger(derived, confirmed=("control_degree",)))
    text = _text(block)
    assert "未达到目标值" in text
    assert "水土流失治理度" in text
    assert "各项防治目标可以实现" not in text
    assert any(f.code == "ASSERTION_UNSUPPORTED" for f in block.quality_findings)


def test_n05_summary_must_not_say_all_indicators_pass():
    block = render_benefit({}, _with_effect("control_degree", 80), set())
    text = _text(block)
    for phrase in ("各项指标均达到", "各项指标均满足", "全部达标"):
        assert phrase not in text


def test_n05_effect_at_or_above_target_is_only_pending_review():
    """即使来源已确认、效果不低于目标, 也只到"待复核" ——
    机器检查不能替专业判断下达标结论。"""
    derived = _with_effect("control_degree", 99)
    row = _rows(derived, confirmed=("control_degree",))["水土流失治理度 (%)"]
    assert row["result"] == "待复核"
    assert row["result"] != "达标"


def test_n05_no_row_ever_says_compliant_under_any_fixture():
    """穷举本文件用到的各种输入, "达标"这两个字都不得出现在判定列。"""
    fixtures = [
        ({}, ()), (TARGET_ONLY, ()),
        (_with_effect("control_degree", 80), ()),
        (_with_effect("control_degree", 80), ("control_degree",)),
        (_with_effect("control_degree", 99), ("control_degree",)),
    ]
    for derived, confirmed in fixtures:
        for row in _rows(derived, confirmed).values():
            assert row["result"] != "达标"


# ============================================================
# N06 — 部分效果缺失 / 分母为 0
# ============================================================

def test_n06_partial_effects_leave_the_rest_pending():
    rows = _rows(_with_effect("control_degree", 99))
    pending = [k for k, r in rows.items() if r["actual"] == "待计算"]
    assert len(pending) == len(INDICATOR_LABELS) - 1


def test_n06_narrative_counts_the_indicators_without_effects():
    block = render_benefit({}, _with_effect("control_degree", 99), set())
    text = _text(block)
    assert "另有5项指标尚无任何效果计算结果" in text
    assert "不得按达标处理" in text


def test_n06_narrative_reports_unconfirmed_candidates_separately():
    """候选值单独成段: 保留原值与来源, 并说明为何不参与判定。"""
    block = render_benefit({}, _with_effect("control_degree", 80), set())
    text = _text(block)
    assert "候选数值" in text
    assert "源自 actual_derived" in text
    assert "不**将其作为效果值参与达标判定" in text or "参与达标判定" in text
    assert any(f.code == "TARGET_EFFECT_CONFLATED" for f in block.quality_findings)


def test_n06_zero_denominator_is_not_forced_to_100_percent():
    """new_loss 为 0 时不做除法, 也不强行给出 100%。"""
    facts = {
        "field.fact.prediction.total_loss": {"value": 0, "unit": "t"},
        "field.fact.prediction.new_loss": {"value": 0, "unit": "t"},
        "field.fact.prediction.reducible_loss": {"value": 0, "unit": "t"},
    }
    block = render_benefit(facts, TARGET_ONLY, set())
    text = _text(block)
    assert "100%" not in text
    assert "可减少量与新增量之比" not in text


def test_n06_confirmed_effect_without_target_is_flagged():
    derived = {"field.derived.target.control_degree": {
        "value": 95, "unit": "%", "actual_derived": 99}}
    row = _rows(derived, confirmed=("control_degree",))["水土流失治理度 (%)"]
    assert row["result"] == "目标值缺失"


def test_n06_no_rows_disappear_when_data_is_missing():
    """缺数据不能让指标行消失 —— 消失等于从分母里删掉。"""
    assert len(_rows({})) == len(INDICATOR_LABELS)


# ============================================================
# 口径问题不得被算术掩盖
# ============================================================

def test_reducible_over_new_is_not_called_control_degree():
    """旧实现把 reducible/new 称作"治理比例"并 min(...,100) 封顶。
    封顶会把口径错误藏起来; 现在如实给比值并声明口径未确认。"""
    facts = {
        "field.fact.prediction.total_loss": {"value": 100, "unit": "t"},
        "field.fact.prediction.new_loss": {"value": 50, "unit": "t"},
        "field.fact.prediction.reducible_loss": {"value": 60, "unit": "t"},
    }
    block = render_benefit(facts, {}, set())
    text = _text(block)
    assert "120.0%" in text, "超过 100% 的比值必须如实显示, 不得封顶"
    assert "统计口径" in text
    assert "不得作为“水土流失治理度”指标值使用" in text
    assert any(f.code == "TARGET_EFFECT_CONFLATED" for f in block.quality_findings)


def test_footnote_documents_the_effect_source_rule():
    from cpswc.renderers.table_projections import SPEC_SIX_INDICATOR
    fn = SPEC_SIX_INDICATOR.footnote
    assert "actual_derived" in fn
    assert "候选效果输入" in fn
    assert "不进入达标比较" in fn
    assert "均不出现“达标”" in fn
