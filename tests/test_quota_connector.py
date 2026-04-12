"""
test_quota_connector.py — F2 Price Layer Connector 单测

验证:
  1. load_mapping: YAML 加载正确条数和字段
  2. lookup_consumption: 有映射→返回 QuotaConsumption; 无映射→None
  3. calculate_unit_price: 人工/机械/材料费计算正确
  4. enrich_measures: 批量标注 price_source + quota_unit_price
  5. 无 DB 文件时安全降级
"""
import sys
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.quota_connector import (
    load_mapping,
    lookup_consumption,
    calculate_unit_price,
    enrich_measures,
    MappingEntry,
    ConsumptionItem,
    QuotaConsumption,
    RegionalRates,
    DEFAULT_MAPPING_PATH,
    DB_PATH,
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
    """eng_02 字段正确."""
    mapping = load_mapping()
    e = mapping["eng_02"]
    assert e.measure_name == "M7.5浆砌石挡土墙"
    assert e.quota_code == "0309"
    assert e.detail_code == "03031"
    assert e.unit_convert == 0.01


def test_load_mapping_no_quota():
    """temp_02 无定额映射."""
    mapping = load_mapping()
    e = mapping["temp_02"]
    assert e.quota_code is None
    assert e.detail_code is None


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
        ),
    }
    enriched = enrich_measures(measures, mapping=mapping, db_path=path)

    assert enriched[0]["price_source"] == "quota_db"
    assert enriched[0]["quota_unit_price"] > 0
    assert "quota_breakdown" in enriched[0]
    assert enriched[1]["price_source"] == "no_mapping"
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
        ),
    }
    enriched = enrich_measures(measures, mapping=mapping, db_path=path)
    assert enriched[0]["unit_price"] == 999.0  # 原始价格不变
    assert enriched[0]["quota_unit_price"] != 999.0  # 定额价格另存
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

    # 7 条有映射, 2 条无映射
    quota_db_count = sum(1 for m in enriched if m.get("price_source") == "quota_db")
    no_mapping_count = sum(1 for m in enriched if m.get("price_source") == "no_mapping")
    assert quota_db_count == 7
    assert no_mapping_count == 2

    # 有定额价格的都 > 0
    for m in enriched:
        if m.get("price_source") == "quota_db":
            assert m["quota_unit_price"] > 0
            assert m["quota_ref"] is not None
