"""
quota_connector.py — F2 Price Layer Connector

将 CSV 措施条目通过定额映射自动查询工料机消耗量,
并结合地区单价计算措施单价。

数据流:
  CSV measure_id → mapping YAML → quota DB → 工料机消耗 → 单价

核心函数:
  load_mapping(path) → dict[measure_id, MappingEntry]
  lookup_consumption(db, mapping_entry) → QuotaConsumption
  calculate_unit_price(consumption, regional_rates) → float
  enrich_measures(measures, mapping, db, rates) → list[dict]
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from cpswc.paths import PROJECT_ROOT


# ============================================================
# Data classes
# ============================================================

@dataclass
class MappingEntry:
    """一条措施→定额映射."""
    measure_id: str
    measure_name: str
    measure_unit: str
    quota_code: str | None       # None = 无定额映射
    detail_code: str | None
    quota_title: str
    quota_unit: str
    unit_convert: float          # 定额单位→措施单位的换算系数
    notes: str = ""


@dataclass
class ConsumptionItem:
    """一条工料机消耗记录."""
    spec_name: str       # 如 "人工", "块（片）石", "搅拌机 0.4m³"
    spec_value: float    # 消耗量 (定额单位下)
    spec_unit: str       # 如 "工时", "m³", "台时"
    type_name: str       # 人工 / 材料 / 机械 / 其他
    jx_id: str           # 机械关联 ID


@dataclass
class QuotaConsumption:
    """一条定额子项的完整工料机消耗."""
    quota_code: str
    detail_code: str
    quota_title: str
    spec_label: str              # 子项规格 (如 "挡土墙", "土类级别Ⅰ-Ⅱ")
    quota_unit: str
    unit_convert: float
    items: list[ConsumptionItem] = field(default_factory=list)
    machine_rates: dict[str, float] = field(default_factory=dict)  # jx_id → 台班费小计

    @property
    def labor_hours(self) -> float:
        """每定额单位的人工工时."""
        for it in self.items:
            if it.type_name == "人工" and it.spec_name == "人工":
                return it.spec_value
        return 0.0

    @property
    def labor_hours_per_unit(self) -> float:
        """每措施单位的人工工时."""
        return self.labor_hours * self.unit_convert

    def material_cost_per_unit(self, material_prices: dict[str, float]) -> float:
        """
        每措施单位的材料费。
        material_prices: {spec_name: 元/单位} 或 {jx_id: 元/单位}
        """
        total = 0.0
        for it in self.items:
            if it.type_name != "材料":
                continue
            if "%" in it.spec_unit:
                continue  # 百分比项 (零星材料费) 后续按比例计
            price = material_prices.get(it.spec_name) or material_prices.get(it.jx_id, 0.0)
            total += it.spec_value * price
        return total * self.unit_convert

    def machine_cost_per_unit(self) -> float:
        """每措施单位的机械费 (从 machine_details 查台班费)."""
        total = 0.0
        for it in self.items:
            if it.type_name != "机械":
                continue
            rate = self.machine_rates.get(it.jx_id, 0.0)
            total += it.spec_value * rate
        return total * self.unit_convert


# ============================================================
# 加载映射
# ============================================================

DEFAULT_MAPPING_PATH = PROJECT_ROOT / "registries" / "quota_measure_mapping_v0.yaml"


def load_mapping(path: str | Path = DEFAULT_MAPPING_PATH) -> dict[str, MappingEntry]:
    """加载措施→定额映射 YAML, 返回 {measure_id: MappingEntry}."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    result: dict[str, MappingEntry] = {}
    for mid, m in (data.get("mappings") or {}).items():
        result[mid] = MappingEntry(
            measure_id=mid,
            measure_name=m.get("measure_name", ""),
            measure_unit=m.get("measure_unit", ""),
            quota_code=m.get("quota_code"),
            detail_code=m.get("detail_code"),
            quota_title=m.get("quota_title", ""),
            quota_unit=m.get("quota_unit", ""),
            unit_convert=float(m.get("unit_convert", 1.0)),
            notes=m.get("notes", ""),
        )
    return result


# ============================================================
# 查询消耗量
# ============================================================

def lookup_consumption(
    db: sqlite3.Connection,
    entry: MappingEntry,
) -> QuotaConsumption | None:
    """
    从 SQLite 查询指定定额子项的工料机消耗量。
    返回 None 如果无映射或查不到数据。
    """
    if not entry.quota_code or not entry.detail_code:
        return None

    # 查子项规格标签
    spec_label = ""
    row = db.execute(
        "SELECT spec_value FROM quota_details "
        "WHERE quota_code=? AND detail_code=? AND spec_name='项目' LIMIT 1",
        (entry.quota_code, entry.detail_code),
    ).fetchone()
    if row:
        spec_label = row[0]

    # 查全部工料机消耗
    rows = db.execute(
        "SELECT spec_name, spec_value, spec_unit, type_name, jx_id "
        "FROM quota_details "
        "WHERE quota_code=? AND detail_code=? AND spec_name != '项目' "
        "ORDER BY type_name, spec_name",
        (entry.quota_code, entry.detail_code),
    ).fetchall()

    if not rows:
        return None

    items = []
    jx_ids = set()
    for sn, sv, su, tn, jid in rows:
        try:
            val = float(sv)
        except (ValueError, TypeError):
            continue  # 跳过非数值项 (如范围 "0.1-1.8")
        items.append(ConsumptionItem(
            spec_name=sn, spec_value=val, spec_unit=su,
            type_name=tn or "", jx_id=jid or "",
        ))
        if tn == "机械" and jid:
            jx_ids.add(jid)

    # 查机械台班费
    machine_rates: dict[str, float] = {}
    for jid in jx_ids:
        rate_row = db.execute(
            "SELECT spec_value FROM machine_details "
            "WHERE jx_id=? AND spec_id='sub_total' LIMIT 1",
            (jid,),
        ).fetchone()
        if rate_row:
            try:
                machine_rates[jid] = float(rate_row[0])
            except (ValueError, TypeError):
                pass

    return QuotaConsumption(
        quota_code=entry.quota_code,
        detail_code=entry.detail_code,
        quota_title=entry.quota_title,
        spec_label=spec_label,
        quota_unit=entry.quota_unit,
        unit_convert=entry.unit_convert,
        items=items,
        machine_rates=machine_rates,
    )


# ============================================================
# 计算单价
# ============================================================

@dataclass
class RegionalRates:
    """地区费率参数."""
    labor_rate: float = 25.0     # 元/工时 (广东 2024 参考)
    misc_material_base: float = 0.0  # 零星材料费基数 (通常为直接费的百分比)


def calculate_unit_price(
    consumption: QuotaConsumption,
    rates: RegionalRates,
    material_prices: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    从消耗量 + 地区单价计算措施单价。

    返回:
      {
        labor_cost: 人工费 (元/措施单位),
        material_cost: 材料费 (元/措施单位),
        machine_cost: 机械费 (元/措施单位),
        unit_price: 合计单价 (元/措施单位),
        breakdown: [{name, quantity, unit, unit_price, subtotal, type}],
        source: "quota_db",
      }
    """
    material_prices = material_prices or {}

    # 人工费
    labor_cost = consumption.labor_hours_per_unit * rates.labor_rate

    # 机械费
    machine_cost = consumption.machine_cost_per_unit()

    # 材料费 (有价格的材料)
    material_cost = consumption.material_cost_per_unit(material_prices)

    # 明细
    breakdown = []
    for it in consumption.items:
        qty_per_unit = it.spec_value * consumption.unit_convert
        if it.type_name == "人工":
            up = rates.labor_rate
            st = qty_per_unit * up
        elif it.type_name == "机械":
            up = consumption.machine_rates.get(it.jx_id, 0.0)
            st = qty_per_unit * up
        elif it.type_name == "材料" and "%" not in it.spec_unit:
            up = material_prices.get(it.spec_name) or material_prices.get(it.jx_id, 0.0)
            st = qty_per_unit * up
        else:
            up = 0.0
            st = 0.0

        breakdown.append({
            "name": it.spec_name,
            "quantity": round(qty_per_unit, 4),
            "unit": it.spec_unit,
            "unit_price": round(up, 2),
            "subtotal": round(st, 2),
            "type": it.type_name,
        })

    unit_price = labor_cost + material_cost + machine_cost

    return {
        "labor_cost": round(labor_cost, 2),
        "material_cost": round(material_cost, 2),
        "machine_cost": round(machine_cost, 2),
        "unit_price": round(unit_price, 2),
        "breakdown": breakdown,
        "source": "quota_db",
        "quota_ref": f"{consumption.quota_code}/{consumption.detail_code} {consumption.spec_label}",
    }


# ============================================================
# 批量 enrich: 为 CSV 措施补充定额信息
# ============================================================

DB_PATH = PROJECT_ROOT / "data" / "quota_2025" / "quota_2025.db"


def enrich_measures(
    measures: list[dict],
    mapping: dict[str, MappingEntry] | None = None,
    db_path: str | Path = DB_PATH,
    rates: RegionalRates | None = None,
    material_prices: dict[str, float] | None = None,
) -> list[dict]:
    """
    为 CSV 导入的措施列表补充定额消耗量和自动计算单价。

    每条措施 dict 新增字段:
      - quota_ref: 定额引用 (code/detail_code)
      - quota_consumption: 工料机消耗明细
      - quota_unit_price: 定额计算单价 (元)
      - price_source: "quota_db" | "manual" | "no_mapping"

    注意: 不覆盖已有的 unit_price, 而是并列提供 quota_unit_price 供对比。
    """
    if mapping is None:
        mapping = load_mapping()
    if rates is None:
        rates = RegionalRates()

    db_path = Path(db_path)
    if not db_path.exists():
        for m in measures:
            m["price_source"] = "no_db"
        return measures

    conn = sqlite3.connect(str(db_path))

    for m in measures:
        mid = m.get("measure_id", "")
        entry = mapping.get(mid)

        if not entry or not entry.quota_code:
            m["price_source"] = "no_mapping"
            m["quota_ref"] = None
            continue

        consumption = lookup_consumption(conn, entry)
        if not consumption:
            m["price_source"] = "no_mapping"
            m["quota_ref"] = None
            continue

        price_result = calculate_unit_price(consumption, rates, material_prices)

        m["quota_ref"] = price_result["quota_ref"]
        m["quota_unit_price"] = price_result["unit_price"]
        m["quota_labor"] = price_result["labor_cost"]
        m["quota_machine"] = price_result["machine_cost"]
        m["quota_material"] = price_result["material_cost"]
        m["quota_breakdown"] = price_result["breakdown"]
        m["price_source"] = "quota_db"

    conn.close()
    return measures
