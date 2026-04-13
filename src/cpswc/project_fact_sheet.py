"""
project_fact_sheet.py — CPSWC v0 ProjectFactSheet

宪法收口: 对应 ARCHITECTURE_DECISIONS.md 宪法必做项 #1。
把 facts flat dict 投影为正式的、带类型的 ProjectFactSheet_v0 契约对象,
作为所有下游消费者 (特性表 / workbench / document / narrative) 的统一数据源。

设计原则:
  - 单一来源: 从 facts + derived_fields 投影, 不反向引用 sample / registry
  - 字段对齐: 覆盖 FieldIdentityRegistry_v0 中所有 proj.spec_sheet.* 投影目标
  - Quantity 解包: {value, unit} 结构自动解为 (value, unit) 元组
  - 缺失容忍: 所有字段 Optional, None = 事实未提供
  - v0 不做校验 (那是 validator 的事)

消费者迁移路径 (渐进):
  v0.current: 本模块提供 build() 函数, 返回 ProjectFactSheet dataclass
              table_projections.project_spec_sheet 可选择性迁移
  v0.next:    workbench / document 改为从 ProjectFactSheet 取值
  v1:         narrative 模板全部改为从 ProjectFactSheet 投影
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================
# Quantity helper
# ============================================================

def _extract(facts: dict, key: str) -> Any:
    """从 facts 取值, 处理 Quantity {value, unit} → value"""
    v = facts.get(key)
    if v is None:
        return None
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def _extract_str(facts: dict, key: str) -> str | None:
    """取字符串值。list 类型用顿号拼接。"""
    v = _extract(facts, key)
    if v is None:
        return None
    if isinstance(v, list):
        return "、".join(str(x) for x in v) if v else None
    return str(v)


def _extract_float(facts: dict, key: str) -> float | None:
    """取数值"""
    v = _extract(facts, key)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _extract_list(facts: dict, key: str) -> list | None:
    """取 list 值"""
    v = facts.get(key)
    if isinstance(v, list):
        return v
    return None


# ============================================================
# ProjectFactSheet_v0
# ============================================================

@dataclass
class ProjectFactSheet:
    """
    v0 项目事实清单 — 对齐 FieldIdentityRegistry_v0 的 proj.spec_sheet.* 投影。

    所有字段 Optional: None 表示事实未提供。
    字段分组对齐特性表三部分 + 水保相关 + derived。
    """

    # ── 一、项目基本情况 ──
    project_name: str | None = None           # field.fact.project.name
    project_code: str | None = None           # field.fact.project.code
    builder: str | None = None                # field.fact.project.builder
    compiler: str | None = None               # field.fact.project.compiler
    industry_category: str | None = None      # field.fact.project.industry_category
    construction_nature: str | None = None    # field.fact.project.nature

    # 位置
    province_list: str | None = None          # field.fact.location.province_list
    prefecture_list: str | None = None        # field.fact.location.prefecture_list
    county_list: str | None = None            # field.fact.location.county_list
    river_basin_agency: str | None = None     # field.fact.location.river_basin_agency

    # 投资
    total_investment: float | None = None     # field.fact.investment.total_investment (万元)
    civil_investment: float | None = None     # field.fact.investment.civil_investment (万元)

    # 工期
    start_time: str | None = None             # field.fact.schedule.start_time
    end_time: str | None = None               # field.fact.schedule.end_time
    design_horizon_year: str | None = None    # field.fact.schedule.design_horizon_year

    # 占地 (hm²)
    total_land_area: float | None = None      # field.fact.land.total_area
    permanent_land_area: float | None = None  # field.fact.land.permanent_area
    temporary_land_area: float | None = None  # field.fact.land.temporary_area

    # 分县占地明细
    county_breakdown: list | None = None      # field.fact.land.county_breakdown

    # ── 二、土石方平衡 (万 m³) ──
    earthwork_excavation: float | None = None       # field.fact.earthwork.excavation
    earthwork_fill: float | None = None             # field.fact.earthwork.fill
    earthwork_borrow: float | None = None           # field.fact.earthwork.borrow
    earthwork_spoil: float | None = None            # field.fact.earthwork.spoil
    earthwork_self_reuse: float | None = None       # field.fact.earthwork.self_reuse
    earthwork_comprehensive_reuse: float | None = None  # field.fact.earthwork.comprehensive_reuse

    # 表土 (万 m³)
    topsoil_excavation: float | None = None   # field.fact.topsoil.strippable_volume (剥离)
    topsoil_fill: float | None = None         # field.fact.topsoil.backfill_volume (回覆)

    # ── 三、水土保持相关 ──
    landform_type: str | None = None          # field.fact.natural.landform_type
    soil_erosion_type: str | None = None      # field.fact.natural.soil_erosion_type
    soil_erosion_intensity: str | None = None  # field.fact.natural.soil_erosion_intensity
    allowable_loss: float | None = None       # field.fact.natural.allowable_loss
    water_soil_zoning: str | None = None      # field.fact.natural.water_soil_zoning
    key_prevention_treatment_areas: str | None = None  # field.fact.natural.key_prevention_treatment_areas

    # 防治
    control_standard_level: str | None = None         # field.fact.prevention.control_standard_level
    responsibility_range_area: float | None = None    # field.fact.prevention.responsibility_range_area

    # 预测
    predicted_total_loss: float | None = None  # field.fact.prediction.predicted_total_loss
    new_loss: float | None = None              # field.fact.prediction.new_loss
    reducible_loss: float | None = None        # field.fact.prediction.reducible_loss

    # 比率 (derived)
    excavation_utilization_ratio: float | None = None   # field.derived.earthwork.excavation_utilization_ratio
    comprehensive_reuse_ratio: float | None = None      # field.derived.earthwork.comprehensive_reuse_ratio

    # 六率目标值 (derived, record)
    weighted_target: dict | None = None  # field.derived.target.weighted_comprehensive_target

    # 补偿费 (derived)
    compensation_fee_amount: float | None = None  # field.derived.investment.compensation_fee_amount (万元)

    # 补偿费率标准
    compensation_fee_rate: float | None = None  # field.fact.regulatory.compensation_fee_rate (元/m²)

    # 编制/建设单位 (如果不同于 builder/compiler)
    compile_unit: str | None = None       # field.fact.project.compile_unit
    construction_unit: str | None = None  # field.fact.project.construction_unit


# ============================================================
# 投影函数
# ============================================================

# facts field id → ProjectFactSheet attribute 映射表
_FACT_MAPPING: list[tuple[str, str, str]] = [
    # (fact_field_id, attr_name, type: "str" | "float" | "list")
    ("field.fact.project.name", "project_name", "str"),
    ("field.fact.project.code", "project_code", "str"),
    ("field.fact.project.builder", "builder", "str"),
    ("field.fact.project.compiler", "compiler", "str"),
    ("field.fact.project.industry_category", "industry_category", "str"),
    ("field.fact.project.nature", "construction_nature", "str"),
    ("field.fact.location.province_list", "province_list", "str"),
    ("field.fact.location.prefecture_list", "prefecture_list", "str"),
    ("field.fact.location.county_list", "county_list", "str"),
    ("field.fact.location.river_basin_agency", "river_basin_agency", "str"),
    ("field.fact.investment.total_investment", "total_investment", "float"),
    ("field.fact.investment.civil_investment", "civil_investment", "float"),
    ("field.fact.schedule.start_time", "start_time", "str"),
    ("field.fact.schedule.end_time", "end_time", "str"),
    ("field.fact.schedule.design_horizon_year", "design_horizon_year", "str"),
    ("field.fact.land.total_area", "total_land_area", "float"),
    ("field.fact.land.permanent_area", "permanent_land_area", "float"),
    ("field.fact.land.temporary_area", "temporary_land_area", "float"),
    ("field.fact.land.county_breakdown", "county_breakdown", "list"),
    ("field.fact.earthwork.excavation", "earthwork_excavation", "float"),
    ("field.fact.earthwork.fill", "earthwork_fill", "float"),
    ("field.fact.earthwork.borrow", "earthwork_borrow", "float"),
    ("field.fact.earthwork.spoil", "earthwork_spoil", "float"),
    ("field.fact.earthwork.self_reuse", "earthwork_self_reuse", "float"),
    ("field.fact.earthwork.comprehensive_reuse", "earthwork_comprehensive_reuse", "float"),
    ("field.fact.topsoil.strippable_volume", "topsoil_excavation", "float"),
    ("field.fact.topsoil.backfill_volume", "topsoil_fill", "float"),
    ("field.fact.natural.landform_type", "landform_type", "str"),
    ("field.fact.natural.soil_erosion_type", "soil_erosion_type", "str"),
    ("field.fact.natural.soil_erosion_intensity", "soil_erosion_intensity", "str"),
    ("field.fact.natural.allowable_loss", "allowable_loss", "float"),
    ("field.fact.natural.water_soil_zoning", "water_soil_zoning", "str"),
    ("field.fact.natural.key_prevention_treatment_areas", "key_prevention_treatment_areas", "str"),
    ("field.fact.prevention.control_standard_level", "control_standard_level", "str"),
    ("field.fact.prevention.responsibility_range_area", "responsibility_range_area", "float"),
    ("field.fact.prediction.predicted_total_loss", "predicted_total_loss", "float"),
    ("field.fact.prediction.new_loss", "new_loss", "float"),
    ("field.fact.prediction.reducible_loss", "reducible_loss", "float"),
    ("field.fact.regulatory.compensation_fee_rate", "compensation_fee_rate", "float"),
    ("field.fact.project.compile_unit", "compile_unit", "str"),
    ("field.fact.project.construction_unit", "construction_unit", "str"),
]

# derived field id → attr 映射
_DERIVED_MAPPING: list[tuple[str, str]] = [
    ("field.derived.earthwork.excavation_utilization_ratio", "excavation_utilization_ratio"),
    ("field.derived.earthwork.comprehensive_reuse_ratio", "comprehensive_reuse_ratio"),
    ("field.derived.target.weighted_comprehensive_target", "weighted_target"),
    ("field.derived.investment.compensation_fee_amount", "compensation_fee_amount"),
]


def build(facts: dict, derived_fields: dict | None = None) -> ProjectFactSheet:
    """
    从 facts + derived_fields 投影出 ProjectFactSheet。

    参数:
      facts: flat dict (field.fact.* → value), 通常是 project_input["facts"]
      derived_fields: flat dict (field.derived.* → value), 通常是 RuntimeSnapshot.derived_fields

    返回:
      ProjectFactSheet 实例
    """
    derived = derived_fields or {}
    kwargs: dict[str, Any] = {}

    extractors = {"str": _extract_str, "float": _extract_float, "list": _extract_list}
    for fact_id, attr, typ in _FACT_MAPPING:
        extractor = extractors[typ]
        kwargs[attr] = extractor(facts, fact_id)

    for derived_id, attr in _DERIVED_MAPPING:
        v = derived.get(derived_id)
        # derived 也可能是 Quantity {value, unit} (pre-stored in sample)
        if isinstance(v, dict) and "value" in v and attr != "weighted_target":
            v = v["value"]
        kwargs[attr] = v

    return ProjectFactSheet(**kwargs)


def build_from_snapshot(snapshot_dict: dict) -> ProjectFactSheet:
    """
    从 RuntimeSnapshot 的 dict 形式构建 ProjectFactSheet。
    (snapshot_dict 需包含 _original_facts 和 derived_fields 键)
    """
    facts = snapshot_dict.get("_original_facts") or {}
    derived = snapshot_dict.get("derived_fields") or {}
    return build(facts, derived)
