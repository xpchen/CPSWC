"""
test_intake_contract.py — F-0 契约补强验收测试

对应 FRONTEND_WIRING_PLAN.md v1.1 第 4 节 F-0：

    F-0.1  BuildContext.project_fields() —— 唯一的字段状态序列化出口
    F-0.2  ExportGate 停止二次合并 derived（已复现的活 bug）
    F-0.3  canonical findings 分层 + intake_issues 投影

这三项全部是**后端契约**工作，不含前端代码。它们决定后面每一步是"搬运"
还是"重新推断"——没有它们，payload 生成器就得自己推断值状态，等于把
P0-04 刚消灭的多套口径复制一份到生成器里。
"""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.export_gate import check_export_readiness
from cpswc.intake_issues import (
    CATEGORY_BY_CODE, build_intake_issues, canonical_findings, resolve_impact,
    summarize_intake,
)
from cpswc.narrative.projection import project_narrative
from cpswc.paths import SAMPLES_DIR
from cpswc.report_quality import Provenance, ValueState
from cpswc.runtime import build_snapshot_dict, load_all_registries, run_project
from cpswc.snapshot_adapter import BuildContext, make_build_context

REGISTRIES = load_all_registries()
FIR_FIELDS = (REGISTRIES.get("fields") or {}).get("fields") or {}
FEE = "field.derived.investment.compensation_fee_amount"


def _sample(name: str = "huizhou_housing_v0") -> dict:
    return json.loads((SAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


class _FakeCalc:
    def __init__(self, cid, out, status, msg=""):
        self.calculator_id, self.output_field_id = cid, out
        self.status, self.error_message = status, msg


class _FakeSnapshot:
    def __init__(self, derived_fields=None, calculator_results=None):
        self.derived_fields = derived_fields or {}
        self.calculator_results = calculator_results or []


# ============================================================
# F-0.1 project_fields()
# ============================================================

def test_f01_missing_fields_are_visible():
    """`unified_view()` 为了"旧值不顶上"跳过 MISSING —— 但那样"缺什么"
    在界面上就看不见了。project_fields() 必须把缺失字段列出来。"""
    pi = _sample()
    ctx = make_build_context(pi, run_project(copy.deepcopy(pi)), REGISTRIES)
    fields = ctx.project_fields()
    missing = [f for f in fields if f["state"] == "MISSING"]
    assert missing, "缺失字段必须出现在 project_fields() 里"
    assert len(fields) > len(ctx.unified_view())


def test_f01_field_universe_is_fir_union_consumed():
    """字段全集 = FIR 登记字段 ∪ 本次实际消费字段。"""
    pi = _sample()
    ctx = make_build_context(pi, run_project(copy.deepcopy(pi)), REGISTRIES)
    ids = {f["field_id"] for f in ctx.project_fields()}
    registered = {k for k, v in FIR_FIELDS.items()
                  if isinstance(v, dict) and v.get("placeholder") is not True}
    assert registered <= ids, "FIR 登记字段必须全部出现"
    for consumed in (pi.get("facts") or {}):
        assert consumed in ids, f"实际消费的 {consumed} 未出现"


def test_f01_each_item_carries_the_full_resolved_state():
    ctx = make_build_context(_sample(), None, REGISTRIES)
    for f in ctx.project_fields():
        for key in ("field_id", "state", "value", "unit", "provenance",
                    "stale_value", "conflicts", "note", "canonical_name"):
            assert key in f, f"{f.get('field_id')} 缺 {key}"


def test_f01_value_is_none_unless_present():
    """调用方不得绕过 state 直接用 value。非 PRESENT 一律 None。"""
    ctx = make_build_context(_sample(), None, REGISTRIES)
    for f in ctx.project_fields():
        if f["state"] != "PRESENT":
            assert f["value"] is None, f


def test_f01_stale_history_is_exposed_but_not_as_a_value():
    """计算失败: 旧值作为历史展示给出, 但 state 仍是 MISSING、value 为 None。"""
    ctx = make_build_context(
        {"facts": {}, "derived": {FEE: 12.34}},
        _FakeSnapshot(calculator_results=[
            _FakeCalc("cal.compensation.fee", FEE, "error", "缺费率")]),
        REGISTRIES)
    item = next(f for f in ctx.project_fields() if f["field_id"] == FEE)
    assert item["state"] == ValueState.MISSING.value
    assert item["value"] is None
    assert item["provenance"] == Provenance.STALE_HISTORICAL.value
    assert item["stale_value"] == 12.34


def test_f01_conflicts_are_serialized():
    fid = "field.fact.land.total_area"
    ctx = make_build_context(
        {"facts": {fid: {"value": 9.5, "unit": "hm²"}},
         "derived": {fid: {"value": 7.7, "unit": "hm²"}}},
        _FakeSnapshot(), REGISTRIES)
    item = next(f for f in ctx.project_fields() if f["field_id"] == fid)
    assert item["state"] == ValueState.CONFLICT.value
    assert len(item["conflicts"]) == 2
    assert {layer for layer, _ in item["conflicts"]} == {
        Provenance.PRE_STORED_DERIVED.value, Provenance.PROJECT_FACT.value}


def test_f01_is_deterministic_and_sorted():
    ctx = make_build_context(_sample(), None, REGISTRIES)
    a, b = ctx.project_fields(), ctx.project_fields()
    assert a == b
    assert [f["field_id"] for f in a] == sorted(f["field_id"] for f in a)


def test_f01_callers_never_need_to_re_derive_state():
    """契约纪律: project_fields() 的每一项都自带状态, 调用方无需再解析原值。"""
    ctx = make_build_context(_sample(), None, REGISTRIES)
    for f in ctx.project_fields():
        assert f["state"] in {s.value for s in ValueState}
        assert f["provenance"] in {p.value for p in Provenance}


# ============================================================
# F-0.2 ExportGate 不再二次合并
# ============================================================

def test_f02_gate_does_not_resurrect_isolated_stale_values():
    """已复现的活 bug 的回归测试。

    某 CRITICAL 字段本次计算失败 → BuildContext 判 MISSING/STALE_HISTORICAL
    并把它挡在统一视图外。门禁若重新合并 `_pre_stored_derived`, GATE_001 会
    认为该字段"有值"而放行 —— 历史值被当成当前值通过了门禁。
    """
    snap = {
        "_original_facts": {}, "derived_fields": {},
        "_pre_stored_derived": {FEE: 99.9},      # 只供对照, 不得参与合并
        "required_assurances": [], "unknown_obligations": [],
        "obligation_details": [], "_build_findings": [],
    }
    result = check_export_readiness(snap)
    assert any(f.target_ref == FEE for f in result.blocks), \
        "门禁复活了被隔离的历史值"


def test_f02_gate_reads_only_the_unified_view():
    """往 `_pre_stored_derived` 里塞任何东西都不应改变门禁结论。"""
    base = {
        "_original_facts": {"field.fact.project.name": "甲"},
        "derived_fields": {}, "required_assurances": [],
        "unknown_obligations": [], "obligation_details": [],
        "_build_findings": [],
    }
    a = check_export_readiness(dict(base, _pre_stored_derived={}))
    b = check_export_readiness(dict(base, _pre_stored_derived={
        FEE: 1.0, "field.fact.land.total_area": {"value": 9.9, "unit": "hm²"}}))
    assert {(f.rule_id, f.target_ref) for f in a.findings} == \
           {(f.rule_id, f.target_ref) for f in b.findings}


def test_f02_real_sample_gate_still_works():
    pi = _sample()
    d = build_snapshot_dict(run_project(copy.deepcopy(pi)), pi, REGISTRIES)
    r = check_export_readiness(d)
    assert r.verdict in ("PASS", "WARN", "BLOCK")
    assert any(f.rule_id == "GATE_006" for f in r.findings)


# ============================================================
# F-0.3 canonical findings
# ============================================================

def _pipeline(name: str = "huizhou_housing_v0"):
    pi = _sample(name)
    d = build_snapshot_dict(run_project(copy.deepcopy(pi)), pi, REGISTRIES)
    nar = project_narrative(d)
    return d, nar


def test_f03_findings_are_layered_not_merged():
    d, nar = _pipeline()
    cf = canonical_findings(build=d["_build_findings"],
                            narrative=nar.quality_findings)
    for layer in ("build", "narrative", "quality", "gate"):
        assert layer in cf, "四个来源必须分层保留"
    assert isinstance(cf["build"], list) and isinstance(cf["narrative"], list)


def test_f03_dedup_mechanism():
    """机制本身: 同一 (code, target_ref, message) 跨层只计一次。

    用合成重复, 不依赖样本数据碰巧有没有重复。
    """
    same = {"code": "VALUE_MISSING", "severity": "BLOCK",
            "message": "field.x: MISSING", "target_ref": "field.x"}
    other = {"code": "VALUE_MISSING", "severity": "WARN",
             "message": "field.y: MISSING", "target_ref": "field.y"}
    cf = canonical_findings(build=[same], narrative=[dict(same)],
                            quality=[dict(same)], gate=[other])
    assert cf["raw_count"] == 4
    assert cf["distinct_count"] == 2, "同一件事被三层报到, 只应计一次"
    assert cf["counts_by_severity"] == {"BLOCK": 1, "WARN": 1, "INFO": 0}
    # 分层仍然原样保留, 界面可分别显示
    assert len(cf["build"]) == len(cf["narrative"]) == len(cf["quality"]) == 1


def test_f03_dedup_matters_on_the_real_pipeline():
    """真实四层管线上, 放大是显著的 —— 这就是不能直接拼接的理由。"""
    from cpswc.report_quality import (
        evaluate_report_quality, load_content_requirements,
    )

    d, nar = _pipeline()
    gate = check_export_readiness(d)
    quality = evaluate_report_quality(
        context=d, narrative=nar,
        content_requirements=load_content_requirements(),
        current_input_hash=d["generation_input_hash"])
    cf = canonical_findings(build=d["_build_findings"],
                            narrative=nar.quality_findings,
                            quality=quality.findings, gate=gate.findings)
    assert cf["distinct_count"] < cf["raw_count"],         f"四层管线上应出现重复, 实测 {cf['raw_count']} → {cf['distinct_count']}"
    total = sum(cf["counts_by_severity"].values())
    assert total == cf["distinct_count"]


def test_f03_gate_findings_are_normalized():
    """GateFinding 用 rule_id/action, 要归一到 code/severity。"""
    d, _ = _pipeline()
    gate = check_export_readiness(d)
    cf = canonical_findings(gate=gate.findings)
    assert cf["gate"]
    for f in cf["gate"]:
        assert f["code"].startswith("GATE_")
        assert f["severity"] in ("BLOCK", "WARN", "INFO")


# ============================================================
# F-0.3 intake_issues
# ============================================================

def test_intake_only_collects_things_to_ask_the_client_for():
    """模板渲染失败、功能未实现不是"向甲方收资"的事, 不进清单。"""
    assert "RENDER_FAILED" not in CATEGORY_BY_CODE
    assert "CONTENT_INCOMPLETE" not in CATEGORY_BY_CODE
    assert "ASSERTION_UNSUPPORTED" not in CATEGORY_BY_CODE
    assert CATEGORY_BY_CODE["VALUE_MISSING"] == "MISSING"
    assert CATEGORY_BY_CODE["DEMO_ASSUMPTION"] == "ASSUMPTION"


def test_intake_is_not_a_stage_input_filter():
    """评审指出的关键点: 有 VALUE_MISSING 是在 RENDER 阶段发现的,
    按 stage=INPUT 过滤会把它们全漏掉。"""
    d, nar = _pipeline("disposal_highrisk_v0")
    issues = build_intake_issues(
        {"build": d["_build_findings"], "narrative": nar.quality_findings},
        FIR_FIELDS)
    from_narrative = [i for i in issues if i["origin"] == "narrative"]
    assert from_narrative, "RENDER 阶段发现的缺失必须进清单"
    input_stage_only = [f for f in d["_build_findings"]
                        if f.get("stage") == "INPUT"]
    assert len(issues) > len(input_stage_only)


def test_intake_categories_distinguish_kinds_of_problem():
    """DEMO_ASSUMPTION / CONFLICT / UNVERIFIED 不是简单的"缺资料"。"""
    d, nar = _pipeline()
    issues = build_intake_issues(
        {"build": d["_build_findings"], "narrative": nar.quality_findings},
        FIR_FIELDS)
    cats = {i["category"] for i in issues}
    assert "ASSUMPTION" in cats, "惠州样本的 placeholder stub 应被识别为假设"
    assert cats <= {"MISSING", "INVALID", "CONFLICT", "ASSUMPTION",
                    "UNVERIFIED_SOURCE"}


def test_intake_deduplicates_across_origins():
    d, nar = _pipeline()
    issues = build_intake_issues(
        {"build": d["_build_findings"], "narrative": nar.quality_findings},
        FIR_FIELDS)
    keys = [(i["category"], tuple(i["field_refs"]), i["message"]) for i in issues]
    assert len(keys) == len(set(keys))
    multi = [i for i in issues if len(i["origins"]) > 1]
    for i in multi:
        assert i["origins"] == sorted(set(i["origins"]), key=i["origins"].index)


def test_intake_impact_comes_from_the_registry():
    """影响范围按 FIR 的 projection_target_refs 解析, 不由界面猜。"""
    impact = resolve_impact(["field.fact.earthwork.borrow"], FIR_FIELDS)
    assert impact["impact_known"] is True
    assert "sec.evaluation.earthwork_balance" in impact["affected_section_refs"]
    assert impact["affected_projection_refs"]


def test_intake_unknown_impact_is_declared_not_fabricated():
    impact = resolve_impact(["field.fact.not.registered.anywhere"], FIR_FIELDS)
    assert impact["impact_known"] is False
    assert impact["affected_section_refs"] == []
    assert impact["affected_artifact_refs"] == []


def test_intake_flags_issues_whose_impact_is_unknown():
    d, nar = _pipeline()
    issues = build_intake_issues(
        {"build": d["_build_findings"], "narrative": nar.quality_findings},
        FIR_FIELDS)
    unknown = [i for i in issues if not i["impact_known"]]
    for i in unknown:
        assert i["affected_section_refs"] == []
    assert summarize_intake(issues)["impact_unknown_count"] == len(unknown)


def test_intake_blocking_issues_come_first():
    d, nar = _pipeline()
    issues = build_intake_issues(
        {"build": d["_build_findings"], "narrative": nar.quality_findings},
        FIR_FIELDS)
    order = {"BLOCK": 0, "WARN": 1, "INFO": 2}
    seq = [order[i["severity"]] for i in issues]
    assert seq == sorted(seq), "收资的人要先看阻断项"


def test_intake_carries_field_names_for_display():
    d, nar = _pipeline()
    issues = build_intake_issues(
        {"build": d["_build_findings"], "narrative": nar.quality_findings},
        FIR_FIELDS)
    named = [i for i in issues if i["field_refs"]]
    assert named
    for i in named:
        assert len(i["field_names"]) == len(i["field_refs"])


def test_intake_summary_gives_subcounts_not_a_score():
    d, nar = _pipeline()
    issues = build_intake_issues(
        {"build": d["_build_findings"], "narrative": nar.quality_findings},
        FIR_FIELDS)
    s = summarize_intake(issues)
    assert set(s) == {"total", "by_category", "by_severity",
                      "impact_unknown_count"}
    assert "score" not in s and "percent" not in s


@pytest.mark.parametrize("name", [
    "huinan_zhigu_v0", "huizhou_housing_v0",
    "shiwei_logistics_v0", "disposal_highrisk_v0",
])
def test_intake_works_on_all_four_samples(name):
    d, nar = _pipeline(name)
    issues = build_intake_issues(
        {"build": d["_build_findings"], "narrative": nar.quality_findings},
        FIR_FIELDS)
    assert issues, f"{name} 应能列出收资项"
    for i in issues:
        assert i["remediation"] or i["message"], "每条都要能告诉人怎么办"
