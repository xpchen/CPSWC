"""
test_table_projections.py — P0.5-2 最小单测

验证:
  1. 格式化规则 (_format_value)
  2. 合计行存在性
  3. 空值 → "—"
  4. render_policy 正确设置
  5. section_id 绑定到 _CHAPTER_TREE
  6. 缺数据时 SKIP / PLACEHOLDER / NOT_APPLICABLE 行为
"""
import json
import sys
from pathlib import Path

# 确保 src/ 在 path 上 (运行时不需要, 但 pytest 发现测试文件时可能需要)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.renderers.table_protocol import (
    TableRenderPolicy, _format_value,
)
from cpswc.renderers.table_projections import (
    TABLE_PROJECTIONS,
    project_total_land_occupation,
    project_earthwork_balance,
    project_land_occupation_by_county,
    project_topsoil_balance,
    project_responsibility_range,
    project_spoil_summary,
)


# ============================================================
# Test _format_value
# ============================================================

def test_format_value_int():
    assert _format_value(3.7, "int") == "3"
    assert _format_value(0, "int") == "0"

def test_format_value_2f():
    assert _format_value(8.2, "2f") == "8.20"
    assert _format_value(0, "2f") == "0.00"

def test_format_value_1f():
    assert _format_value(74.7368, "1f") == "74.7"

def test_format_value_none():
    assert _format_value(None, "2f") == "—"
    assert _format_value(None, "str") == "—"

def test_format_value_str():
    assert _format_value("hello", "str") == "hello"
    assert _format_value("", "str") == "—"


# ============================================================
# Load samples for projection tests
# ============================================================

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"

def _load_snapshot(sample_name: str) -> dict:
    """Load sample + run through runtime to get snapshot-like dict"""
    sample_path = SAMPLES_DIR / sample_name
    with sample_path.open() as f:
        project_input = json.load(f)
    # Build a minimal snapshot dict (without running full runtime)
    return {
        "_original_facts": project_input.get("facts") or {},
        "derived_fields": project_input.get("derived") or {},
        "triggered_obligations": (project_input.get("sample_meta") or {}).get(
            "designed_to_trigger_obligations") or [],
    }


HZ = _load_snapshot("huizhou_housing_v0.json")
DISP = _load_snapshot("disposal_highrisk_v0.json")


# ============================================================
# Test: total_land_occupation
# ============================================================

def test_total_land_huizhou():
    td = project_total_land_occupation(HZ)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert len(td.rows) >= 1  # M1: now from county_breakdown, multiple rows
    assert td.total_row is not None
    assert td.total_row["permanent"] == 8.2
    assert td.total_row["temporary"] == 1.3

def test_total_land_disposal():
    td = project_total_land_occupation(DISP)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert td.total_row["permanent"] == 38.0


# ============================================================
# Test: earthwork_balance
# ============================================================

def test_earthwork_huizhou():
    td = project_earthwork_balance(HZ)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert td.rows[0]["excavation"] == 8.5
    assert td.rows[0]["spoil"] == 3.5
    assert td.rows[0]["component"] == "项目合计"
    assert td.total_row is not None


# ============================================================
# Test: land_occupation_by_county
# ============================================================

def test_county_land_huizhou():
    td = project_land_occupation_by_county(HZ)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert len(td.rows) >= 1
    assert td.total_row is not None

def test_county_land_disposal_skip():
    td = project_land_occupation_by_county(DISP)
    # Disposal sample has no county_breakdown → SKIP
    assert td.render_policy == TableRenderPolicy.SKIP_RENDER


# ============================================================
# Test: topsoil_balance
# ============================================================

def test_topsoil_huizhou():
    td = project_topsoil_balance(HZ)
    # Huizhou has topsoil data
    assert td.render_policy in (
        TableRenderPolicy.RENDER_WITH_VALUES,
        TableRenderPolicy.RENDER_WITH_PLACEHOLDER,
    )

def test_topsoil_disposal_placeholder():
    td = project_topsoil_balance(DISP)
    # Disposal has no topsoil data → placeholder or all None
    assert td.rows[0]["excavation"] is None or td.render_policy in (
        TableRenderPolicy.RENDER_WITH_PLACEHOLDER,
        TableRenderPolicy.RENDER_WITH_VALUES,
    )


# ============================================================
# Test: responsibility_range
# ============================================================

def test_resp_range_huizhou():
    td = project_responsibility_range(HZ)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert td.total_row["ratio"] == 100.0

def test_resp_range_disposal_skip():
    td = project_responsibility_range(DISP)
    # Disposal has no county_breakdown
    assert td.render_policy == TableRenderPolicy.SKIP_RENDER


# ============================================================
# Test: spoil_summary
# ============================================================

def test_spoil_huizhou():
    td = project_spoil_summary(HZ)
    # Huizhou has temp_topsoil_site but no disposal → still has rows (TS01/TS02)
    assert len(td.rows) >= 2
    assert td.rows[0]["level"] == "不适用"

def test_spoil_disposal():
    td = project_spoil_summary(DISP)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert len(td.rows) == 2  # D1 + D2
    levels = {r["site_id"]: r["level"] for r in td.rows}
    assert levels["D1"] == "1级"
    assert levels["D2"] == "4级"


# ============================================================
# Test: section_id alignment (P0.5-3)
# ============================================================

def test_section_id_all_registered():
    """Every spec.section_id must exist in _CHAPTER_TREE"""
    from cpswc.renderers import table_projections as tp
    from cpswc.renderers.document import _get_chapter_tree

    # Collect all section_ids from chapter tree
    def collect_ids(nodes):
        ids = set()
        for node in nodes:
            ids.add(node.get("stable_id", ""))
            ids.update(collect_ids(node.get("children") or []))
        return ids

    tree_ids = collect_ids(_get_chapter_tree())

    for attr_name in dir(tp):
        if attr_name.startswith("SPEC_"):
            spec = getattr(tp, attr_name)
            if hasattr(spec, "section_id") and spec.section_id:
                assert spec.section_id in tree_ids, (
                    f"{attr_name}.section_id = '{spec.section_id}' "
                    f"not found in _CHAPTER_TREE"
                )


# ============================================================
# Test: TABLE_PROJECTIONS registry completeness
# ============================================================

def test_registry_matches_specs():
    """Every SPEC_* has a corresponding entry in TABLE_PROJECTIONS"""
    from cpswc.renderers import table_projections as tp
    for attr_name in dir(tp):
        if attr_name.startswith("SPEC_"):
            spec = getattr(tp, attr_name)
            assert spec.table_id in TABLE_PROJECTIONS, (
                f"{attr_name}.table_id = '{spec.table_id}' "
                f"not in TABLE_PROJECTIONS registry"
            )



# ============================================================
# Test: six_indicator_review (N2)
# ============================================================

def test_six_indicator_huizhou():
    from cpswc.renderers.table_projections import project_six_indicator_review
    td = project_six_indicator_review(HZ)
    assert td.render_policy in (
        TableRenderPolicy.RENDER_WITH_VALUES,
        TableRenderPolicy.RENDER_WITH_PLACEHOLDER,
    )
    assert len(td.rows) == 6  # 6 indicators
    # First indicator should have target value
    assert td.rows[0]["indicator"] == "水土流失治理度 (%)"

def test_six_indicator_disposal():
    from cpswc.renderers.table_projections import project_six_indicator_review
    td = project_six_indicator_review(DISP)
    assert len(td.rows) == 6
    # Disposal: target may be "—" if derived not pre-populated in test snapshot
    # (full runtime populates it; test uses raw sample without runtime)
    assert td.rows[0]["target"] in ("98", "—")

# ============================================================
# Step 52-B: PreventionSystem §8.1 四张 LIVE 表
# ============================================================

from cpswc.renderers.table_projections import (
    project_prevention_zones_summary,
    project_measures_overall_layout,
    project_measures_layout_by_zone,
    project_measures_classification,
)

HUINAN = _load_snapshot("huinan_zhigu_v0.json")
SHIWEI = _load_snapshot("shiwei_logistics_v0.json")


def test_prevention_zones_summary_huizhou():
    td = project_prevention_zones_summary(HZ)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert len(td.rows) == 4
    # 面积守恒 (契约 §4.3 PREVENTION_ZONE_001): 合计不超 responsibility_range
    assert td.total_row is not None
    assert td.total_row["area_ha"] <= 9.5
    # 永久 + 临时 = 总面积 (huizhou 自洽: 8.2 + 1.3 = 9.5)
    assert td.total_row["area_permanent_ha"] == 8.2
    assert td.total_row["area_temporary_ha"] == 1.3


def test_prevention_zones_summary_disposal_spoil():
    """disposal 样本必含 spoil_disposal 分区 (Step 52-0 激活)"""
    td = project_prevention_zones_summary(DISP)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert len(td.rows) >= 3
    zone_types = [r["zone_type"] for r in td.rows]
    assert "弃渣场区" in zone_types, f"disposal 样本必含弃渣场区, got: {zone_types}"


def test_prevention_zones_summary_disposal_sot_boundary():
    """SoT 边界: spoil_disposal 行不得含 disposal_site 专业字段
    (volume / max_height / downstream_harm_class / level)"""
    td = project_prevention_zones_summary(DISP)
    for r in td.rows:
        if r["zone_type"] == "弃渣场区":
            # zones 表的列只有 area_*, 不应有专业事实字段
            assert "volume" not in r
            assert "max_height" not in r
            assert "downstream_harm_class" not in r
            assert "level" not in r


def test_measures_overall_layout_excludes_monitoring():
    """监测措施必须被排除 (契约 §5.4 measure_type 不含 monitoring)"""
    td = project_measures_overall_layout(HZ)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    measure_types = {r["measure_type"] for r in td.rows if r["measure_type"]}
    # 应只含工程/植物/临时
    assert measure_types.issubset({"工程措施", "植物措施", "临时措施"}), (
        f"overall_layout 不应含监测措施, got types: {measure_types}")


def test_measures_overall_layout_source_attr_mapping():
    td = project_measures_overall_layout(HZ)
    source_attrs = {r["source_attr"] for r in td.rows}
    # 英文 enum 必须映射为中文
    assert source_attrs.issubset({"主体已列", "方案新增"})
    # 样本 huizhou 应同时含两种来源
    assert "主体已列" in source_attrs
    assert "方案新增" in source_attrs


def test_measures_layout_by_zone_cross_zone_primary():
    """跨区措施按 primary_zone_ref 归一次, 不重复列在其他分区 (契约 §5.5)"""
    td = project_measures_layout_by_zone(DISP)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    # disposal 样本有跨区措施 (eng_01 浆砌石排水沟 zone_refs=[d1, d2], primary=d1)
    # 应只在 primary_zone (d1) 行列出一次
    measure_names = [r["measure_name"] for r in td.rows]
    assert measure_names.count("浆砌石排水沟") == 1


def test_measures_classification_verdict_mapping():
    td = project_measures_classification(HZ)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert len(td.rows) == 2  # huizhou 有 2 条 classification
    verdicts = {r["verdict"] for r in td.rows}
    # 必须映射为中文
    assert verdicts.issubset({"纳入", "不纳入", "部分纳入"})


def test_measures_classification_resulting_measure_resolution():
    """classification.resulting_measure_refs 必须解析到 measure_name"""
    td = project_measures_classification(HZ)
    for r in td.rows:
        # resulting 应是 measure_name, 不是 measure_id
        assert r["resulting"] != "—"
        assert not r["resulting"].startswith("measure."), (
            f"resulting 应是 measure_name, got raw id: {r['resulting']}")


def test_prevention_tables_all_samples_non_empty():
    """Acceptance: 4 张表在 4 个样本上都 non-empty."""
    for snap_name, snap in [("huizhou", HZ), ("disposal", DISP),
                             ("huinan", HUINAN), ("shiwei", SHIWEI)]:
        for fn, label in [
            (project_prevention_zones_summary,    "zones"),
            (project_measures_overall_layout,     "overall"),
            (project_measures_layout_by_zone,     "by_zone"),
            (project_measures_classification,     "classification"),
        ]:
            td = fn(snap)
            assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES, (
                f"{snap_name}.{label}: got {td.render_policy}")
            assert len(td.rows) > 0, f"{snap_name}.{label}: empty rows"


def test_prevention_tables_section_id_bindings():
    """Spec section_id 必须对应 DisplayNumberingPolicy 中的真实 section."""
    from cpswc.renderers.table_projections import (
        SPEC_PREVENTION_ZONES_SUMMARY,
        SPEC_MEASURES_OVERALL_LAYOUT,
        SPEC_MEASURES_LAYOUT_BY_ZONE,
        SPEC_MEASURES_CLASSIFICATION,
    )
    assert SPEC_PREVENTION_ZONES_SUMMARY.section_id == "sec.prevention.zones"
    assert SPEC_MEASURES_OVERALL_LAYOUT.section_id   == "sec.prevention.overall_layout"
    assert SPEC_MEASURES_LAYOUT_BY_ZONE.section_id   == "sec.prevention.zone_measures"
    assert SPEC_MEASURES_CLASSIFICATION.section_id   == "sec.evaluation.measures_classification"


# ============================================================
# Run all tests
# ============================================================

if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            print(f"  [PASS] {test_fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test_fn.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)

