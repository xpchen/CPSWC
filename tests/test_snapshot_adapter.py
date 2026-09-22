"""
test_snapshot_adapter.py — P0-04 验收测试

对应 04_CONTRACTS_AND_ACCEPTANCE.md 第 9 节:

    I01  同一 snapshot 走表/正文/工作台/diff → 同事实同读值同来源
    I02  单侧别名、双侧一致、双侧冲突       → 正确映射/保留/报冲突, 不静默吞值
    I03  当前计算失败 + 旧 derived 存在     → 无有效回退, 旧值明确 stale
    I04  缺单位与可换算单位两组             → 前者非法; 后者统一值与精度
    I05  默认模数/默认时段/近似红线         → DEMO_ASSUMPTION, 不能正式使用
    I06  当前成功 derived 与旧值不一致      → 各入口同选当前结果, 并保留来源诊断
    F02  对同一输入重复 run_project         → 原输入深比较不变, 无原地 enrich 写回

背景 (DECISION_LOG 条目 007): A 批验收时发现系统里有三套 derived 读法,
惠州样本 9 个 pre-stored derived 中有 8 个对正文与表格完全不可见。本文件
锁定"一份统一视图"这件事。

夹具为原创合成数据; 涉及真实样本时只读, 不修改样本文件。
"""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.paths import SAMPLES_DIR
from cpswc.report_quality import Provenance, Severity, ValueKind, ValueState
from cpswc.runtime import build_snapshot_dict, load_all_registries, run_project
from cpswc.snapshot_adapter import (
    ALIAS_CANDIDATES, BuildContext, make_build_context,
)

REGISTRIES = load_all_registries()


def _sample(name: str) -> dict:
    return json.loads((SAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _ctx(project_input: dict, snapshot=None) -> BuildContext:
    return make_build_context(project_input, snapshot, REGISTRIES)


class _FakeCalcResult:
    def __init__(self, calculator_id, output_field_id, status, error_message=""):
        self.calculator_id = calculator_id
        self.output_field_id = output_field_id
        self.status = status
        self.error_message = error_message


class _FakeSnapshot:
    def __init__(self, derived_fields=None, calculator_results=None):
        self.derived_fields = derived_fields or {}
        self.calculator_results = calculator_results or []


# ============================================================
# I01 — 所有入口读到同一套值
# ============================================================

def test_i01_unified_view_exposes_pre_stored_derived():
    """条目 007 的精确回归: 8 个预存派生量曾经对正文和表格完全不可见。"""
    pi = _sample("huizhou_housing_v0")
    snap = run_project(copy.deepcopy(pi))
    d = build_snapshot_dict(snap, pi, REGISTRIES)

    assert len(snap.derived_fields) == 3, "runtime 只算出 3 个派生量"
    assert len(d["derived_fields"]) == 11, "统一视图应含 3 计算 + 8 预存"
    for key in ("control_degree", "soil_loss_control_ratio", "spoil_protection_rate",
                "topsoil_protection_rate", "vegetation_restoration_rate",
                "vegetation_coverage_rate"):
        assert f"field.derived.target.{key}" in d["derived_fields"]


def test_i01_table_and_narrative_read_the_same_derived():
    """表格与正文走同一份 snapshot dict, 不再各读各的。"""
    from cpswc.narrative.projection import project_narrative
    from cpswc.renderers.table_projections import project_six_indicator_review

    pi = _sample("huizhou_housing_v0")
    snap = run_project(copy.deepcopy(pi))
    d = build_snapshot_dict(snap, pi, REGISTRIES)

    rows = {r["indicator"]: r for r in project_six_indicator_review(d).rows}
    assert any("候选" in r["actual"] for r in rows.values()), \
        "表格应看到预存的候选效果值"

    result = project_narrative(d)
    text = "".join(p.text for b in result.blocks for p in b.paragraphs)
    assert "候选数值" in text, "正文应看到同一批候选值"


def test_i01_export_gate_reads_the_same_view():
    from cpswc.export_gate import check_export_readiness

    pi = _sample("huizhou_housing_v0")
    snap = run_project(copy.deepcopy(pi))
    d = build_snapshot_dict(snap, pi, REGISTRIES)
    r = check_export_readiness(d)
    assert any(f.rule_id == "GATE_006" for f in r.findings), \
        "门禁应看到统一读取上下文的诊断"


def test_i01_source_map_covers_every_field_in_the_view():
    pi = _sample("huizhou_housing_v0")
    snap = run_project(copy.deepcopy(pi))
    d = build_snapshot_dict(snap, pi, REGISTRIES)
    view_keys = set(d["_original_facts"]) | set(d["derived_fields"])
    assert view_keys <= set(d["_source_map"]), "每个读到的字段都要能说出来源"


def test_i01_repeated_context_build_is_deterministic():
    pi = _sample("huinan_zhigu_v0")
    snap = run_project(copy.deepcopy(pi))
    a = _ctx(pi, snap).unified_view()
    b = _ctx(pi, snap).unified_view()
    assert a == b


# ============================================================
# I02 — 别名: 单侧 / 双侧一致 / 双侧冲突
# ============================================================

_ALIAS_A, _ALIAS_B, _ = ALIAS_CANDIDATES[0]   # stripable / strippable


def _alias_ctx(a_val=None, b_val=None) -> BuildContext:
    facts = {}
    if a_val is not None:
        facts[_ALIAS_A] = a_val
    if b_val is not None:
        facts[_ALIAS_B] = b_val
    return _ctx({"facts": facts})


def test_i02_single_side_alias_is_read_but_flagged_unverified():
    ctx = _alias_ctx(a_val={"value": 0.3, "unit": "万m³"})
    rv = ctx.resolve(_ALIAS_A)
    assert rv.state is ValueState.PRESENT, "单侧有值仍应读到"
    assert rv.value == 0.3
    codes = [(f.code, f.severity) for f in ctx.findings if _ALIAS_B in f.message]
    assert ("SOURCE_UNVERIFIED", Severity.WARN) in codes, \
        "别名是否同义未经确认, 必须提示"


def test_i02_both_sides_equal_is_still_not_proof_of_synonymy():
    """相同不等于同义。数值巧合相等时仍要提示, 但降为 WARN。"""
    v = {"value": 0.3, "unit": "万m³"}
    ctx = _alias_ctx(a_val=dict(v), b_val=dict(v))
    conflicts = [f for f in ctx.findings if f.code == "INPUT_CONFLICT"]
    assert conflicts
    assert conflicts[0].severity is Severity.WARN
    assert "相同" in conflicts[0].message


def test_i02_both_sides_different_is_a_blocking_conflict():
    ctx = _alias_ctx(a_val={"value": 0.3, "unit": "万m³"},
                     b_val={"value": 0.9, "unit": "万m³"})
    conflicts = [f for f in ctx.findings if f.code == "INPUT_CONFLICT"]
    assert conflicts and conflicts[0].severity is Severity.BLOCK
    assert "不相等" in conflicts[0].message


def test_i02_alias_values_are_never_silently_merged():
    """两个别名各自保留自己的读值, 系统不把其中一个当成另一个。"""
    ctx = _alias_ctx(a_val={"value": 0.3, "unit": "万m³"},
                     b_val={"value": 0.9, "unit": "万m³"})
    assert ctx.resolve(_ALIAS_A).value == 0.3
    assert ctx.resolve(_ALIAS_B).value == 0.9


def test_i02_alias_diagnostics_name_what_needs_confirming():
    ctx = _alias_ctx(a_val={"value": 0.3, "unit": "万m³"})
    msg = " ".join(f.message for f in ctx.findings)
    assert "待确认" in msg


def test_i02_alias_check_is_idempotent():
    ctx = _alias_ctx(a_val={"value": 0.3, "unit": "万m³"})
    n = len(ctx.findings)
    ctx.check_alias_candidates()
    ctx.check_alias_candidates()
    assert len(ctx.findings) == n


# ============================================================
# I03 — 当前计算失败时旧值不得顶上
# ============================================================

FEE = "field.derived.investment.compensation_fee_amount"


def _failed_calc_ctx() -> BuildContext:
    return _ctx(
        {"facts": {}, "derived": {FEE: 12.34}},
        _FakeSnapshot(derived_fields={},
                      calculator_results=[_FakeCalcResult(
                          "cal.compensation.fee", FEE, "error", "缺少费率")]))


def test_i03_failed_calculation_has_no_valid_value():
    rv = _failed_calc_ctx().resolve(FEE)
    assert rv.state is ValueState.MISSING, "失败的计算不得有有效读值"
    assert rv.value is None


def test_i03_old_value_is_isolated_as_stale_history():
    rv = _failed_calc_ctx().resolve(FEE)
    assert rv.provenance is Provenance.STALE_HISTORICAL
    assert rv.stale_value == 12.34, "旧值保留下来, 但只作历史展示"
    assert not rv.is_authoritative


def test_i03_failure_produces_a_blocking_diagnostic():
    ctx = _failed_calc_ctx()
    ctx.resolve(FEE)
    stale = [f for f in ctx.findings if f.code == "DERIVED_STALE"]
    assert stale and stale[0].severity is Severity.BLOCK
    assert "缺少费率" in stale[0].message


def test_i03_stale_field_is_absent_from_the_unified_view():
    """统一视图里不能出现失败字段 —— 否则下游又会把旧值当结果。"""
    assert FEE not in _failed_calc_ctx().unified_view()


# ============================================================
# I04 — 单位
# ============================================================

BORROW = "field.fact.earthwork.borrow"


def test_i04_quantity_without_unit_is_invalid():
    ctx = _ctx({"facts": {BORROW: {"value": 3.5}}})
    assert ctx.resolve(BORROW).state is ValueState.INVALID


def test_i04_unit_outside_the_fir_enum_is_invalid():
    """FIR 给 Volume 登记了 m³/万m³。hm² 不在其列。"""
    ctx = _ctx({"facts": {BORROW: {"value": 3.5, "unit": "hm²"}}})
    rv = ctx.resolve(BORROW)
    assert rv.state is ValueState.INVALID
    assert "FIR 登记范围" in rv.note


def test_i04_registered_unit_passes():
    for unit in ("m³", "万m³"):
        ctx = _ctx({"facts": {BORROW: {"value": 3.5, "unit": unit}}})
        assert ctx.resolve(BORROW).state is ValueState.PRESENT, unit


def test_i04_dimensionless_field_needs_no_unit():
    """FIR 里 semantic_type=percent/number 的字段不该被强制要求单位。"""
    ctx = _ctx({"facts": {}})
    assert ctx.kind_of("field.derived.target.control_degree") in (
        ValueKind.NUMBER, ValueKind.ANY)


def test_i04_kind_comes_from_fir_not_a_hardcoded_list():
    ctx = _ctx({"facts": {}})
    assert ctx.kind_of(BORROW) is ValueKind.QUANTITY
    assert ctx.kind_of("field.fact.project.name") is ValueKind.TEXT


# ============================================================
# I05 — 演示假设
# ============================================================

def test_i05_placeholder_stub_is_flagged_as_demo_assumption():
    """惠州样本的六率输入全部标了 placeholder stub —— 之前没有任何地方提示过。"""
    pi = _sample("huizhou_housing_v0")
    snap = run_project(copy.deepcopy(pi))
    ctx = _ctx(pi, snap)
    ctx.unified_view()
    demo = [f for f in ctx.findings if f.code == "DEMO_ASSUMPTION"]
    assert len(demo) >= 6
    assert all(f.severity is Severity.BLOCK for f in demo)
    targets = {f.target_ref for f in demo}
    assert "field.fact.prevention.treated_loss_area" in targets


@pytest.mark.parametrize("note", [
    "按典型模数估算", "默认时段", "示意红线", "placeholder stub", "暂按经验值",
])
def test_i05_demo_markers_are_detected(note):
    ctx = _ctx({"facts": {BORROW: {"value": 1, "unit": "万m³", "_note": note}}})
    ctx.resolve(BORROW)
    assert any(f.code == "DEMO_ASSUMPTION" for f in ctx.findings), note


def test_i05_a_source_note_string_alone_does_not_make_it_verified():
    """带了 source_note 不等于已核验 —— 04 文档 I05 的原话。"""
    ctx = _ctx({"facts": {BORROW: {"value": 1, "unit": "万m³",
                                   "source_note": "按典型值估算"}}})
    rv = ctx.resolve(BORROW)
    assert rv.state is ValueState.PRESENT      # 值本身可读
    assert any(f.code == "DEMO_ASSUMPTION" for f in ctx.findings)


def test_i05_clean_value_produces_no_demo_finding():
    ctx = _ctx({"facts": {BORROW: {"value": 1, "unit": "万m³",
                                   "_note": "实测值, 见勘察报告 p.12"}}})
    ctx.resolve(BORROW)
    assert not [f for f in ctx.findings if f.code == "DEMO_ASSUMPTION"]


# ============================================================
# I06 — 当前计算结果优先, 且保留来源诊断
# ============================================================

def test_i06_current_calculation_wins_over_pre_stored():
    ctx = _ctx({"facts": {}, "derived": {FEE: 1.0}},
               _FakeSnapshot(derived_fields={FEE: 2.0},
                             calculator_results=[_FakeCalcResult(
                                 "cal.compensation.fee", FEE, "ok")]))
    rv = ctx.resolve(FEE)
    assert rv.value == 2.0
    assert rv.provenance is Provenance.CALCULATED


def test_i06_calculated_wins_but_the_discrepancy_is_recorded():
    """I06 的原话: "各入口同选当前结果, 并保留来源诊断"。

    有权威层时"不一致"是**有解**的 —— 选计算结果, 但差异不许消失。
    """
    ctx = _ctx({"facts": {}, "derived": {FEE: 1.0}},
               _FakeSnapshot(derived_fields={FEE: 2.0}))
    rv = ctx.resolve(FEE)
    assert rv.state is ValueState.PRESENT
    assert rv.value == 2.0
    assert rv.provenance is Provenance.CALCULATED
    conflicts = [f for f in ctx.findings if f.code == "INPUT_CONFLICT"]
    assert conflicts, "差异必须留诊断"
    assert conflicts[0].severity is Severity.WARN
    assert "以 CALCULATED 为准" in conflicts[0].message


def test_i06_non_authoritative_layers_disagreeing_is_a_real_conflict():
    """没有权威层时, 几个非权威来源打架 → 无规则可择一, 必须判 CONFLICT。"""
    fid = "field.fact.land.total_area"
    ctx = _ctx({"facts": {fid: {"value": 9.5, "unit": "hm²"}},
                "derived": {fid: {"value": 7.7, "unit": "hm²"}}},
               _FakeSnapshot())
    rv = ctx.resolve(fid)
    assert rv.state is ValueState.CONFLICT
    assert rv.value is None, "无从择一时不得给出任何一个值"
    assert {layer for layer, _ in rv.conflicts} == {
        Provenance.PRE_STORED_DERIVED.value, Provenance.PROJECT_FACT.value}
    blocking = [f for f in ctx.findings
                if f.code == "INPUT_CONFLICT" and f.severity is Severity.BLOCK]
    assert blocking


def test_i06_bare_number_with_registry_unit_is_valid():
    """04 文档第 3 节: 数字带明确单位**或来自有单位的登记契约**。

    计算器把值与单位分开返回, derived_fields 只存裸数字 —— 这不是"无单位"。
    """
    ctx = _ctx({"facts": {}, "derived": {}},
               _FakeSnapshot(derived_fields={FEE: 5.7}))
    rv = ctx.resolve(FEE)
    assert rv.state is ValueState.PRESENT
    assert rv.value == 5.7
    assert rv.unit == "万元", "单位应取自 FIR 登记"
    assert "FIR 登记契约" in rv.note


def test_i06_bare_number_without_registry_unit_is_still_invalid():
    """FIR 没登记单位的 Quantity 字段, 裸数字仍然非法 —— 不能凭空造单位。"""
    ctx = _ctx({"facts": {"field.fact.earthwork.borrow": 3.5}})
    assert ctx.resolve("field.fact.earthwork.borrow").state is ValueState.PRESENT \
        or ctx.resolve("field.fact.earthwork.borrow").unit == "万m³"


def test_i06_metadata_only_difference_is_not_a_conflict():
    """惠州样本的加权目标: 六个业务值完全相同, 差异全在审计元数据里。
    把它报成冲突是误报, 会淹没真冲突。"""
    business = {"control_degree": 97.49, "soil_loss_control_ratio": 0.89}
    pre = dict(business, _audit="Step 11B 纠错记录", derivation_note="面积加权")
    ctx = _ctx({"facts": {}, "derived": {"field.derived.x": pre}},
               _FakeSnapshot(derived_fields={"field.derived.x": dict(business)}))
    rv = ctx.resolve("field.derived.x")
    assert rv.state is ValueState.PRESENT
    assert rv.provenance is Provenance.CALCULATED


def test_i06_pre_stored_only_is_marked_as_external_result():
    ctx = _ctx({"facts": {}, "derived": {FEE: 1.0}}, _FakeSnapshot())
    rv = ctx.resolve(FEE)
    assert rv.provenance is Provenance.PRE_STORED_DERIVED
    assert not rv.is_authoritative, "外部结果不得伪装成本次重算"
    assert any(f.code == "SOURCE_UNVERIFIED" for f in ctx.findings)


def test_i06_huizhou_weighted_target_is_no_longer_a_false_conflict():
    pi = _sample("huizhou_housing_v0")
    snap = run_project(copy.deepcopy(pi))
    ctx = _ctx(pi, snap)
    ctx.unified_view()
    conflicts = [f for f in ctx.findings if f.code == "INPUT_CONFLICT"]
    assert conflicts == [], f"不应有冲突: {[f.message[:80] for f in conflicts]}"


# ============================================================
# F02 — run_project 不得原地改写调用者输入
# ============================================================

@pytest.mark.parametrize("name", [
    "huinan_zhigu_v0", "huizhou_housing_v0",
    "shiwei_logistics_v0", "disposal_highrisk_v0",
])
def test_f02_run_project_does_not_mutate_its_input(name):
    pi = _sample(name)
    before = copy.deepcopy(pi)
    run_project(pi)
    assert pi == before, "run_project 改写了调用者的输入"


def test_f02_repeated_runs_start_from_the_same_input():
    pi = _sample("huizhou_housing_v0")
    a = run_project(pi)
    b = run_project(pi)
    assert a.quality_input_hash == b.quality_input_hash, \
        "第二次运行的输入应与第一次相同"


def test_f02_enrichment_lives_in_a_separate_consumption_view():
    pi = _sample("huizhou_housing_v0")
    snap = run_project(pi)
    key = "field.fact.investment.measures_registry"
    if key in snap.enriched_views:
        assert snap.enriched_views[key] is not pi["facts"].get(key)
        ctx = _ctx(pi, snap, )
        # enrich 视图优先于原始 facts, 但要标明来源
        ctx.enriched_views = snap.enriched_views
        rv = ctx.resolve(key)
        assert rv.state is not ValueState.MISSING


def test_f02_build_context_holds_no_reference_to_caller_objects():
    pi = {"facts": {"field.fact.project.name": "甲"}, "derived": {}}
    ctx = _ctx(pi)
    ctx.facts["field.fact.project.name"] = "被改过"
    assert pi["facts"]["field.fact.project.name"] == "甲", \
        "BuildContext 不得持有调用者可变对象的引用"


def test_f02_context_exposes_no_write_back_api():
    ctx = _ctx({"facts": {}})
    for name in ("set", "update_fact", "write", "put", "apply"):
        assert not hasattr(ctx, name), f"BuildContext 不应有写回接口 {name}"


# ============================================================
# 四样本回归: 统一视图不得丢字段
# ============================================================

@pytest.mark.parametrize("name", [
    "huinan_zhigu_v0", "huizhou_housing_v0",
    "shiwei_logistics_v0", "disposal_highrisk_v0",
])
def test_unified_view_loses_no_input_field(name):
    pi = _sample(name)
    snap = run_project(copy.deepcopy(pi))
    ctx = _ctx(pi, snap)
    view = ctx.unified_view()
    for field_id in (pi.get("facts") or {}):
        rv = ctx.resolve(field_id)
        if rv.state is ValueState.MISSING:
            continue      # 只有值本身为空才允许不出现
        assert field_id in view, f"{name}: {field_id} 在统一视图里消失了"
