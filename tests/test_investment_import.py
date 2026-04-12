"""
test_investment_import.py — Step 19 CSV/YAML 投资导入校验单测

验证:
  1. CSV happy path: 9 条正确记录 → ok, 0 errors
  2. 金额计算: quantity × unit_price / 10000, 四舍五入到 0.01
  3. 缺必填列 → error
  4. 重复 measure_id → error
  5. 非法 fee_category → error
  6. quantity ≤ 0 → error
  7. 缺 source_attribution → 默认方案新增 + warning
  8. inject_import_result → snapshot 包含 registry + summary
  9. inject 拒绝 errors > 0 的 ImportResult
  10. YAML mock 通过 load_import_file 也能正常导入
  11. 汇总金额回算一致
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.investment_loader import (
    load_csv, load_import_file, inject_import_result, ImportResult,
)


FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
CSV_PATH = FIXTURE_DIR / "investment_huizhou_f1.csv"
YAML_PATH = FIXTURE_DIR / "investment_mock_huizhou.yaml"


# ============================================================
# Happy path
# ============================================================

def test_csv_happy_path():
    r = load_csv(CSV_PATH)
    assert r.ok, f"Expected ok, got errors: {r.errors}"
    assert len(r.records) == 9
    assert r.source_type == "csv"


def test_csv_amount_calculation():
    r = load_csv(CSV_PATH)
    eng01 = next(rec for rec in r.records if rec["measure_id"] == "eng_01")
    # 120 × 150 / 10000 = 1.80
    assert eng01["amount_wan"] == 1.80


def test_csv_amount_rounding():
    """eng_03: 60 × 85 / 10000 = 0.51"""
    r = load_csv(CSV_PATH)
    eng03 = next(rec for rec in r.records if rec["measure_id"] == "eng_03")
    assert eng03["amount_wan"] == 0.51


def test_csv_summary_aggregation():
    r = load_csv(CSV_PATH)
    snap = inject_import_result({"_original_facts": {}}, r)
    summary = snap["_original_facts"]["field.fact.investment.measures_summary"]

    assert "工程措施" in summary
    assert summary["工程措施"]["total"] == 3.64  # 1.80 + 1.33 + 0.51
    assert summary["工程措施"]["new"] == 3.64
    assert summary["工程措施"]["existing"] == 0.0

    assert summary["植物措施"]["new"] == 0.52  # 0.16 + 0.36
    assert summary["植物措施"]["existing"] == 0.50
    assert summary["植物措施"]["total"] == 1.02

    assert summary["临时措施"]["new"] == 0.84  # 0.52 + 0.32
    assert summary["临时措施"]["existing"] == 0.50
    assert summary["临时措施"]["total"] == 1.34


# ============================================================
# Validation errors
# ============================================================

def _write_csv(lines: list[str]) -> Path:
    """Helper: write CSV lines to temp file, return path."""
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    tf.write("\n".join(lines))
    tf.close()
    return Path(tf.name)


def test_missing_required_column():
    p = _write_csv([
        "measure_id,measure_name,fee_category,prevention_zone,unit,quantity",
        "eng_01,排水沟,工程措施,主体工程区,m,100",
    ])
    r = load_csv(p)
    assert not r.ok
    assert any("缺少必填列" in e for e in r.errors)


def test_duplicate_measure_id():
    p = _write_csv([
        "measure_id,measure_name,fee_category,prevention_zone,unit,quantity,unit_price",
        "eng_01,排水沟A,工程措施,主体工程区,m,100,150",
        "eng_01,排水沟B,工程措施,临时堆土区,m,50,120",
    ])
    r = load_csv(p)
    assert not r.ok
    assert any("重复" in e for e in r.errors)


def test_invalid_fee_category():
    p = _write_csv([
        "measure_id,measure_name,fee_category,prevention_zone,unit,quantity,unit_price",
        "eng_01,排水沟,独立费用,主体工程区,m,100,150",
    ])
    r = load_csv(p)
    assert not r.ok
    assert any("fee_category" in e for e in r.errors)


def test_invalid_measure_id_format():
    p = _write_csv([
        "measure_id,measure_name,fee_category,prevention_zone,unit,quantity,unit_price",
        "ENG-01,排水沟,工程措施,主体工程区,m,100,150",
    ])
    r = load_csv(p)
    assert not r.ok
    assert any("不合法" in e for e in r.errors)


def test_quantity_zero():
    p = _write_csv([
        "measure_id,measure_name,fee_category,prevention_zone,unit,quantity,unit_price",
        "eng_01,排水沟,工程措施,主体工程区,m,0,150",
    ])
    r = load_csv(p)
    assert not r.ok
    assert any("quantity" in e for e in r.errors)


def test_quantity_not_a_number():
    p = _write_csv([
        "measure_id,measure_name,fee_category,prevention_zone,unit,quantity,unit_price",
        "eng_01,排水沟,工程措施,主体工程区,m,abc,150",
    ])
    r = load_csv(p)
    assert not r.ok
    assert any("不是数字" in e for e in r.errors)


def test_negative_unit_price():
    p = _write_csv([
        "measure_id,measure_name,fee_category,prevention_zone,unit,quantity,unit_price",
        "eng_01,排水沟,工程措施,主体工程区,m,100,-50",
    ])
    r = load_csv(p)
    assert not r.ok
    assert any("unit_price" in e for e in r.errors)


# ============================================================
# Warnings
# ============================================================

def test_missing_source_attribution_defaults_to_new():
    p = _write_csv([
        "measure_id,measure_name,fee_category,prevention_zone,unit,quantity,unit_price",
        "eng_01,排水沟,工程措施,主体工程区,m,100,150",
    ])
    r = load_csv(p)
    assert r.ok
    assert r.records[0]["source_attribution"] == "方案新增"
    assert len(r.warnings) >= 1
    assert any("方案新增" in w for w in r.warnings)


def test_unknown_columns_warned():
    p = _write_csv([
        "measure_id,measure_name,fee_category,prevention_zone,unit,quantity,unit_price,extra_col",
        "eng_01,排水沟,工程措施,主体工程区,m,100,150,whatever",
    ])
    r = load_csv(p)
    assert r.ok
    assert any("未知列" in w for w in r.warnings)


# ============================================================
# Inject safety
# ============================================================

def test_inject_refuses_errors():
    bad = ImportResult(errors=["something wrong"])
    try:
        inject_import_result({}, bad)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_inject_marks_overlay_active():
    r = load_csv(CSV_PATH)
    snap = inject_import_result({"_original_facts": {}}, r)
    assert snap["_investment_overlay_active"] is True
    assert "investment_huizhou_f1.csv" in snap["_investment_overlay_source"]


# ============================================================
# YAML mock compatibility
# ============================================================

def test_yaml_mock_via_load_import_file():
    r = load_import_file(YAML_PATH)
    assert r.ok, f"YAML import errors: {r.errors}"
    assert len(r.records) == 7
    assert r.source_type == "yaml_mock"


def test_csv_via_load_import_file():
    r = load_import_file(CSV_PATH)
    assert r.ok
    assert len(r.records) == 9
    assert r.source_type == "csv"


def test_unsupported_format():
    r = load_import_file(Path("/tmp/foo.xlsx"))
    assert not r.ok
    assert any("不支持" in e for e in r.errors)


# ============================================================
# Amount consistency: sum(records) == summary totals
# ============================================================

def test_amount_consistency():
    """records 逐条 amount_wan 之和 == summary 按 category 汇总"""
    r = load_csv(CSV_PATH)
    snap = inject_import_result({"_original_facts": {}}, r)
    summary = snap["_original_facts"]["field.fact.investment.measures_summary"]

    for cat, vals in summary.items():
        new_sum = round(sum(
            rec["amount_wan"] for rec in r.records
            if rec["fee_category"] == cat and rec["source_attribution"] != "主体已列"
        ), 2)
        existing_sum = round(sum(
            rec["amount_wan"] for rec in r.records
            if rec["fee_category"] == cat and rec["source_attribution"] == "主体已列"
        ), 2)
        assert vals["new"] == new_sum, f"{cat} new: {vals['new']} != {new_sum}"
        assert vals["existing"] == existing_sum, f"{cat} existing: {vals['existing']} != {existing_sum}"
        assert vals["total"] == round(new_sum + existing_sum, 2)
