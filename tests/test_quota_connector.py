"""
test_quota_connector.py — F2 Price Layer Connector 单测

验证:
  1. load_mapping: YAML 加载正确条数和字段 + 校准元数据
  2. lookup_consumption: 有映射→返回 QuotaConsumption; 无映射→None
  3. calculate_unit_price: 人工/机械/材料费计算正确
  4. enrich_measures: 批量标注 price_source (分级) + quota_unit_price
  5. 无 DB 文件时安全降级
  6. 校准分级: calibrated→白名单, needs_section→risk, manual_review→review
"""
import sys
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.quota_connector import (
    load_mapping,
    load_material_prices,
    lookup_consumption,
    calculate_unit_price,
    enrich_measures,
    MappingEntry,
    ConsumptionItem,
    QuotaConsumption,
    RegionalRates,
    DEFAULT_MAPPING_PATH,
    DEFAULT_MATERIAL_PRICES_PATH,
    DB_PATH,
    CALIBRATION_CALIBRATED,
    CALIBRATION_NEEDS_SECTION,
    CALIBRATION_MANUAL_REVIEW,
    CALIBRATION_NOT_APPLICABLE,
    PS_QUOTA_CALIBRATED,
    PS_QUOTA_RAW,
    PS_QUOTA_RISK,
    PS_QUOTA_REVIEW,
    PS_NO_MAPPING,
    PS_NO_DB,
)

MAPPING_PATH = DEFAULT_MAPPING_PATH


# ============================================================
# Helpers
# ============================================================

def _make_test_db() -> tuple[Path, sqlite3.Connection]:
    """创建临时 SQLite 并插入少量测试数据."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    path = Path(tmp.name)
    conn = sqlite3.connect(str(path))
    conn.executescript("""
        CREATE TABLE quota_details (
            quota_code TEXT, detail_code TEXT,
            spec_name TEXT, spec_value TEXT, spec_unit TEXT,
            type_name TEXT, jx_id TEXT
        );
        CREATE TABLE machine_details (
            jx_id TEXT, spec_id TEXT, spec_value TEXT
        );
        -- 模拟定额 TEST01/T001: 人工 + 1 材料 + 1 机械
        INSERT INTO quota_details VALUES
            ('TEST01','T001','项目','测试子项','','',''),
            ('TEST01','T001','人工','10.0','工时','人工',''),
            ('TEST01','T001','块石','5.0','m³','材料',''),
            ('TEST01','T001','搅拌机','2.0','台时','机械','JX001');
        INSERT INTO machine_details VALUES ('JX001','sub_total','80.0');
    """)
    conn.commit()
    return path, conn


# ============================================================
# Tests: load_mapping
# ============================================================

def test_load_mapping_count():
    """YAML 包含 9 条映射."""
    mapping = load_mapping()
    assert len(mapping) == 9


def test_load_mapping_fields():
    """eng_02 字段正确 (含校准元数据)."""
    mapping = load_mapping()
    e = mapping["eng_02"]
    assert e.measure_name == "M7.5浆砌石挡土墙"
    assert e.quota_code == "0309"
    assert e.detail_code == "03031"
    assert e.unit_convert == 0.01
    assert e.calibration_status == CALIBRATION_CALIBRATED
    assert e.whitelist is True
    assert e.requires_section_params is False


def test_load_mapping_no_quota():
    """temp_02 无定额映射."""
    mapping = load_mapping()
    e = mapping["temp_02"]
    assert e.quota_code is None
    assert e.detail_code is None
    assert e.calibration_status == CALIBRATION_NOT_APPLICABLE
    assert e.whitelist is False


# ============================================================
# Tests: load_material_prices
# ============================================================

def test_load_material_prices_count():
    """YAML 包含 5 种材料."""
    prices = load_material_prices()
    assert len(prices) == 5


def test_load_material_prices_values():
    """材料价格值正确."""
    prices = load_material_prices()
    assert prices["块（片）石"] == 85.0
    assert prices["砂浆"] == 350.0
    assert prices["草皮"] == 8.0
    assert prices["水"] == 5.0


def test_load_material_prices_missing_file():
    """不存在的文件 → 空 dict."""
    prices = load_material_prices("/tmp/nonexistent_mat_12345.yaml")
    assert prices == {}


# ============================================================
# Tests: calibration (continued)
# ============================================================

def test_load_mapping_calibration_distribution():
    """校准状态分布: 3 calibrated, 3 needs_section, 1 manual_review, 2 not_applicable."""
    mapping = load_mapping()
    statuses = [e.calibration_status for e in mapping.values()]
    assert statuses.count(CALIBRATION_CALIBRATED) == 3
    assert statuses.count(CALIBRATION_NEEDS_SECTION) == 3
    assert statuses.count(CALIBRATION_MANUAL_REVIEW) == 1
    assert statuses.count(CALIBRATION_NOT_APPLICABLE) == 2


def test_load_mapping_whitelist_count():
    """白名单仅 3 条 (eng_02, plant_02, plant_03)."""
    mapping = load_mapping()
    wl = [mid for mid, e in mapping.items() if e.whitelist]
    assert sorted(wl) == ["eng_02", "plant_02", "plant_03"]


def test_load_mapping_needs_section():
    """needs_section 的 3 条都有 section_formula."""
    mapping = load_mapping()
    for mid in ["eng_01", "eng_03", "temp_01"]:
        e = mapping[mid]
        assert e.calibration_status == CALIBRATION_NEEDS_SECTION
        assert e.requires_section_params is True
        assert len(e.section_formula) > 0


# ============================================================
# Tests: lookup_consumption
# ============================================================

def test_lookup_no_mapping():
    """无 quota_code 的 entry → None."""
    entry = MappingEntry(
        measure_id="x", measure_name="x", measure_unit="m",
        quota_code=None, detail_code=None,
        quota_title="", quota_unit="", unit_convert=1.0,
    )
    path, conn = _make_test_db()
    result = lookup_consumption(conn, entry)
    assert result is None
    conn.close()
    path.unlink()


def test_lookup_found():
    """有效映射 → 返回 QuotaConsumption."""
    entry = MappingEntry(
        measure_id="t1", measure_name="test", measure_unit="m³",
        quota_code="TEST01", detail_code="T001",
        quota_title="测试", quota_unit="100m³", unit_convert=0.01,
    )
    path, conn = _make_test_db()
    cons = lookup_consumption(conn, entry)
    assert cons is not None
    assert cons.spec_label == "测试子项"
    assert len(cons.items) == 3  # 人工 + 材料 + 机械
    assert cons.machine_rates.get("JX001") == 80.0
    conn.close()
    path.unlink()


def test_lookup_labor_hours():
    """人工工时属性."""
    entry = MappingEntry(
        measure_id="t1", measure_name="test", measure_unit="m³",
        quota_code="TEST01", detail_code="T001",
        quota_title="测试", quota_unit="100m³", unit_convert=0.01,
    )
    path, conn = _make_test_db()
    cons = lookup_consumption(conn, entry)
    assert cons.labor_hours == 10.0
    assert cons.labor_hours_per_unit == 10.0 * 0.01  # 0.1
    conn.close()
    path.unlink()


# ============================================================
# Tests: calculate_unit_price
# ============================================================

def test_calculate_labor_only():
    """人工费 = hours_per_unit × rate."""
    cons = QuotaConsumption(
        quota_code="X", detail_code="X1", quota_title="",
        spec_label="", quota_unit="100m³", unit_convert=0.01,
        items=[ConsumptionItem("人工", 10.0, "工时", "人工", "")],
    )
    rates = RegionalRates(labor_rate=30.0)
    result = calculate_unit_price(cons, rates)
    assert result["labor_cost"] == round(10.0 * 0.01 * 30.0, 2)  # 3.0
    assert result["machine_cost"] == 0.0
    assert result["material_cost"] == 0.0
    assert result["unit_price"] == 3.0


def test_calculate_with_material():
    """材料费 = qty_per_unit × material_price."""
    cons = QuotaConsumption(
        quota_code="X", detail_code="X1", quota_title="",
        spec_label="", quota_unit="100m³", unit_convert=0.01,
        items=[
            ConsumptionItem("人工", 10.0, "工时", "人工", ""),
            ConsumptionItem("块石", 5.0, "m³", "材料", ""),
        ],
    )
    rates = RegionalRates(labor_rate=25.0)
    mat_prices = {"块石": 120.0}
    result = calculate_unit_price(cons, rates, mat_prices)
    expected_labor = 10.0 * 0.01 * 25.0  # 2.5
    expected_mat = 5.0 * 0.01 * 120.0    # 6.0
    assert result["labor_cost"] == expected_labor
    assert result["material_cost"] == expected_mat
    assert result["unit_price"] == expected_labor + expected_mat


def test_calculate_with_machine():
    """机械费 = qty_per_unit × machine_rate."""
    cons = QuotaConsumption(
        quota_code="X", detail_code="X1", quota_title="",
        spec_label="", quota_unit="100m³", unit_convert=0.01,
        items=[
            ConsumptionItem("人工", 10.0, "工时", "人工", ""),
            ConsumptionItem("搅拌机", 2.0, "台时", "机械", "JX001"),
        ],
        machine_rates={"JX001": 80.0},
    )
    rates = RegionalRates(labor_rate=25.0)
    result = calculate_unit_price(cons, rates)
    expected_labor = 10.0 * 0.01 * 25.0   # 2.5
    expected_mach = 2.0 * 0.01 * 80.0     # 1.6
    assert result["labor_cost"] == expected_labor
    assert result["machine_cost"] == expected_mach
    assert result["unit_price"] == expected_labor + expected_mach


def test_breakdown_count():
    """breakdown 条目数 = items 数."""
    cons = QuotaConsumption(
        quota_code="X", detail_code="X1", quota_title="",
        spec_label="", quota_unit="100m³", unit_convert=0.01,
        items=[
            ConsumptionItem("人工", 10.0, "工时", "人工", ""),
            ConsumptionItem("块石", 5.0, "m³", "材料", ""),
            ConsumptionItem("搅拌机", 2.0, "台时", "机械", "JX001"),
        ],
        machine_rates={"JX001": 80.0},
    )
    rates = RegionalRates()
    result = calculate_unit_price(cons, rates)
    assert len(result["breakdown"]) == 3


def test_calculate_misc_material_pct():
    """百分比材料费 = direct_cost × pct / 100."""
    cons = QuotaConsumption(
        quota_code="X", detail_code="X1", quota_title="",
        spec_label="", quota_unit="100m³", unit_convert=0.01,
        items=[
            ConsumptionItem("人工", 10.0, "工时", "人工", ""),
            ConsumptionItem("块石", 5.0, "m³", "材料", ""),
            ConsumptionItem("其他材料费", 0.5, "%", "材料", ""),
        ],
    )
    rates = RegionalRates(labor_rate=25.0)
    mat_prices = {"块石": 100.0}
    result = calculate_unit_price(cons, rates, mat_prices)
    labor = 10.0 * 0.01 * 25.0   # 2.5
    mat_entity = 5.0 * 0.01 * 100.0  # 5.0
    direct = labor + mat_entity   # 7.5
    misc = direct * 0.5 * 0.01 / 100.0  # 0.000375
    assert result["misc_material_cost"] == round(misc, 2)
    assert result["material_cost"] == round(mat_entity + misc, 2)


def test_calculate_composite_with_all_components():
    """综合单价 = 人工 + 实体材料 + 百分比材料 + 机械."""
    cons = QuotaConsumption(
        quota_code="X", detail_code="X1", quota_title="",
        spec_label="", quota_unit="100m³", unit_convert=0.01,
        items=[
            ConsumptionItem("人工", 10.0, "工时", "人工", ""),
            ConsumptionItem("块石", 5.0, "m³", "材料", ""),
            ConsumptionItem("搅拌机", 2.0, "台时", "机械", "JX001"),
            ConsumptionItem("其他材料费", 0.5, "%", "材料", ""),
        ],
        machine_rates={"JX001": 80.0},
    )
    rates = RegionalRates(labor_rate=25.0)
    mat_prices = {"块石": 100.0}
    result = calculate_unit_price(cons, rates, mat_prices)
    assert result["labor_cost"] > 0
    assert result["material_cost"] > 0
    assert result["machine_cost"] > 0
    assert result["misc_material_cost"] >= 0
    assert result["unit_price"] == round(
        result["labor_cost"] + result["material_cost"] + result["machine_cost"], 2
    )


# ============================================================
# Tests: enrich_measures
# ============================================================

def test_enrich_with_test_db():
    """enrich 使用临时 DB → 正确标注 price_source."""
    path, conn = _make_test_db()
    conn.close()

    measures = [
        {"measure_id": "t1", "measure_name": "test", "unit_price": 100},
        {"measure_id": "t2", "measure_name": "no_map", "unit_price": 50},
    ]
    mapping = {
        "t1": MappingEntry(
            measure_id="t1", measure_name="test", measure_unit="m³",
            quota_code="TEST01", detail_code="T001",
            quota_title="测试", quota_unit="100m³", unit_convert=0.01,
            calibration_status=CALIBRATION_CALIBRATED, whitelist=True,
        ),
    }
    enriched = enrich_measures(measures, mapping=mapping, db_path=path)

    assert enriched[0]["price_source"] == PS_QUOTA_CALIBRATED
    assert enriched[0]["quota_unit_price"] > 0
    assert enriched[0]["whitelist"] is True
    assert "quota_breakdown" in enriched[0]
    assert enriched[1]["price_source"] == PS_NO_MAPPING
    assert enriched[1]["whitelist"] is False
    path.unlink()


def test_enrich_no_db():
    """DB 不存在 → 全部标 no_db."""
    measures = [{"measure_id": "x"}]
    enriched = enrich_measures(measures, db_path="/tmp/nonexistent_12345.db")
    assert enriched[0]["price_source"] == "no_db"


def test_enrich_preserves_original_price():
    """enrich 不覆盖原始 unit_price."""
    path, conn = _make_test_db()
    conn.close()

    measures = [{"measure_id": "t1", "unit_price": 999.0}]
    mapping = {
        "t1": MappingEntry(
            measure_id="t1", measure_name="test", measure_unit="m³",
            quota_code="TEST01", detail_code="T001",
            quota_title="测试", quota_unit="100m³", unit_convert=0.01,
            calibration_status=CALIBRATION_CALIBRATED, whitelist=True,
        ),
    }
    enriched = enrich_measures(measures, mapping=mapping, db_path=path)
    assert enriched[0]["unit_price"] == 999.0  # 原始价格不变
    assert enriched[0]["quota_unit_price"] != 999.0  # 定额价格另存
    path.unlink()


def test_enrich_grading_needs_section():
    """needs_section → price_source = unit_convert_risk."""
    path, conn = _make_test_db()
    conn.close()

    measures = [{"measure_id": "t1"}]
    mapping = {
        "t1": MappingEntry(
            measure_id="t1", measure_name="test", measure_unit="m",
            quota_code="TEST01", detail_code="T001",
            quota_title="测试", quota_unit="100m³", unit_convert=0.01,
            calibration_status=CALIBRATION_NEEDS_SECTION,
            requires_section_params=True, whitelist=False,
        ),
    }
    enriched = enrich_measures(measures, mapping=mapping, db_path=path)
    assert enriched[0]["price_source"] == PS_QUOTA_RISK
    assert enriched[0]["calibration_status"] == CALIBRATION_NEEDS_SECTION
    path.unlink()


def test_enrich_grading_manual_review():
    """manual_review → price_source = manual_review_required."""
    path, conn = _make_test_db()
    conn.close()

    measures = [{"measure_id": "t1"}]
    mapping = {
        "t1": MappingEntry(
            measure_id="t1", measure_name="test", measure_unit="hm²",
            quota_code="TEST01", detail_code="T001",
            quota_title="测试", quota_unit="100m²", unit_convert=100.0,
            calibration_status=CALIBRATION_MANUAL_REVIEW, whitelist=False,
        ),
    }
    enriched = enrich_measures(measures, mapping=mapping, db_path=path)
    assert enriched[0]["price_source"] == PS_QUOTA_REVIEW
    assert enriched[0]["whitelist"] is False
    path.unlink()


# ============================================================
# Tests: real DB (skip if not available)
# ============================================================

def test_real_db_enrich():
    """用真实 DB 测试 enrich (如果 DB 存在)."""
    if not DB_PATH.exists():
        return  # skip

    from cpswc.investment_loader import load_csv
    result = load_csv(str(Path(__file__).resolve().parent.parent / "fixtures" / "investment_huizhou_f1.csv"))
    measures = [dict(r) for r in result.records]
    enriched = enrich_measures(measures)

    # 按分级统计
    sources = [m["price_source"] for m in enriched]
    assert sources.count(PS_QUOTA_CALIBRATED) == 3   # eng_02, plant_02, plant_03
    assert sources.count(PS_QUOTA_RISK) == 3         # eng_01, eng_03, temp_01
    assert sources.count(PS_QUOTA_REVIEW) == 1       # plant_01
    assert sources.count(PS_NO_MAPPING) == 2         # temp_02, temp_03

    # 白名单仅 3 条
    wl = [m for m in enriched if m.get("whitelist")]
    assert len(wl) == 3

    # 有定额价格的都 > 0
    for m in enriched:
        if m["price_source"] not in (PS_NO_MAPPING, PS_NO_DB):
            assert m["quota_unit_price"] > 0
            assert m["quota_ref"] is not None

    # 白名单 3 条现在应该有非零材料费 (material_prices 自动加载)
    for m in wl:
        assert m["quota_material"] > 0, f'{m["measure_id"]} should have material cost'
        assert "quota_misc_material" in m


def test_real_db_composite_prices():
    """白名单综合单价合理性检查."""
    if not DB_PATH.exists():
        return  # skip

    from cpswc.investment_loader import load_csv
    result = load_csv(str(Path(__file__).resolve().parent.parent / "fixtures" / "investment_huizhou_f1.csv"))
    measures = [dict(r) for r in result.records]
    enriched = enrich_measures(measures)

    by_id = {m["measure_id"]: m for m in enriched}

    # eng_02: 综合单价应 > 人工费 (加了材料)
    eng02 = by_id["eng_02"]
    assert eng02["quota_unit_price"] > eng02["quota_labor"]
    assert eng02["quota_material"] > 100  # 块石+砂浆应超 100 元/m³

    # plant_02: 苗木费应占主体
    p02 = by_id["plant_02"]
    assert p02["quota_material"] > p02["quota_labor"]

    # plant_03: 单价应在合理范围 (15-50 元/m²)
    p03 = by_id["plant_03"]
    assert 15 < p03["quota_unit_price"] < 50
