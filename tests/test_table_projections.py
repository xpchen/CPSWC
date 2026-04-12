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
    assert len(td.rows) == 1
    assert td.rows[0]["permanent"] == 8.2
    assert td.rows[0]["temporary"] == 1.3
    assert td.rows[0]["total"] == 9.5
    assert td.total_row is not None

def test_total_land_disposal():
    td = project_total_land_occupation(DISP)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert td.rows[0]["permanent"] == 38.0


# ============================================================
# Test: earthwork_balance
# ============================================================

def test_earthwork_huizhou():
    td = project_earthwork_balance(HZ)
    assert td.render_policy == TableRenderPolicy.RENDER_WITH_VALUES
    assert td.rows[0]["excavation"] == 8.5
    assert td.rows[0]["spoil"] == 3.5
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
    assert td.rows[0]["stripable_area"] is None or td.render_policy in (
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
    from cpswc.renderers.document import _CHAPTER_TREE

    # Collect all section_ids from chapter tree
    def collect_ids(nodes):
        ids = set()
        for node in nodes:
            ids.add(node.get("stable_id", ""))
            ids.update(collect_ids(node.get("children") or []))
        return ids

    tree_ids = collect_ids(_CHAPTER_TREE)

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
