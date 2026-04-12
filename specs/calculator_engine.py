#!/usr/bin/env python3
"""
calculator_engine.py — CPSWC v0 极简 calculator 执行器

设计哲学 (Step 11A 共识):
  - 本模块只支持 CalculatorRegistry_v0.yaml 中当前登记的 1 条 calculator
  - 不建通用 DSL, 不做公式抽象, 不做 override resolver
  - 实现直接硬编码在 _eval_compensation_fee() 函数里
  - 下一颗 calculator 激活时再决定是否泛化
  - 对外仅暴露一个 evaluate() 函数, 被 sample_validator.py 调用

严格边界:
  1. 不读 RegionOverridePrototype (决议 9: v0 不消费 override)
  2. 不做单位通用换算 (硬编码 hm² → m²)
  3. 不做任意公式求值 (禁止 eval / exec)
  4. 错误分支必须显式 raise, 不允许静默 fallback
  5. 所有输入必须是 FieldIdentityRegistry 中登记的 field id

退出码: 本模块不是主程序, 不定义退出码; 异常通过 CalculatorError 抛出。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: 缺少 PyYAML — 请先 pip install pyyaml", file=sys.stderr)
    sys.exit(2)


SPECS_DIR = Path(__file__).resolve().parent


# ==================================================================
# 异常
# ==================================================================
class CalculatorError(Exception):
    """calculator 执行失败; 含 calculator_id 和具体 error_branch 信息"""
    def __init__(self, calculator_id: str, branch: str, message: str):
        self.calculator_id = calculator_id
        self.branch = branch
        self.message = message
        super().__init__(f"[{calculator_id}] {branch}: {message}")


# ==================================================================
# 结果对象
# ==================================================================
@dataclass
class CalcResult:
    calculator_id: str
    output_field_id: str
    value: float
    unit: str
    # 中间量, 便于 validator 做双向 cross-check
    intermediate: dict
    # 使用的输入快照
    inputs_snapshot: dict


# ==================================================================
# Field 取值辅助 (沿用 sample_validator.py 的约定)
# ==================================================================
def _get_field_value(path: str, sample: dict) -> Any:
    """
    从 sample.facts 按 field id 取值。
    处理 Quantity {value, unit} 结构 → 返回 value。
    regulatory 类字段若 sample 未覆盖, 回退到 FieldIdentityRegistry 的
    validation.default 值。
    """
    facts = sample.get("facts") or {}
    v = facts.get(path)
    if v is None:
        return None
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    if isinstance(v, (int, float)):
        return v
    return v


def _get_regulatory_default(field_id: str, fir: dict) -> Any:
    """
    从 FieldIdentityRegistry 读取 field 的 validation.default,
    用于 v0 单一广东包下 regulatory 参数的静态取值。
    """
    fields = fir.get("fields") or {}
    fdef = fields.get(field_id) or {}
    validation = fdef.get("validation") or {}
    return validation.get("default")


# ==================================================================
# calculator 实现 (硬编码, 不抽象)
# ==================================================================
def _eval_compensation_fee(calc_def: dict, sample: dict, fir: dict) -> CalcResult:
    """
    cal.compensation.fee 硬编码实现。

    公式:
      chargeable_area_m2 = (permanent_area_hm2 + temporary_area_hm2) * 10000
      amount_yuan        = chargeable_area_m2 * rate_yuan_per_m2
      amount_wan         = amount_yuan / 10000

    错误分支 (与 CalculatorRegistry_v0.yaml 的 error_branches 对齐):
      - permanent/temporary < 0 → raise
      - rate <= 0 → raise
      - rate < 0.1 → raise (十倍偏差保险丝)
    """
    calc_id = "cal.compensation.fee"

    # 读取输入 (fact fields)
    permanent_hm2 = _get_field_value("field.fact.land.permanent_area", sample)
    temporary_hm2 = _get_field_value("field.fact.land.temporary_area", sample)

    # 读取 regulatory 参数: sample 若无, 回退到 FIR validation.default
    rate = _get_field_value("field.fact.regulatory.compensation_fee_rate", sample)
    if rate is None:
        rate = _get_regulatory_default("field.fact.regulatory.compensation_fee_rate", fir)

    # 必填检查
    if permanent_hm2 is None:
        raise CalculatorError(calc_id, "missing_input",
                              "field.fact.land.permanent_area 未提供")
    if temporary_hm2 is None:
        raise CalculatorError(calc_id, "missing_input",
                              "field.fact.land.temporary_area 未提供")
    if rate is None:
        raise CalculatorError(calc_id, "missing_input",
                              "field.fact.regulatory.compensation_fee_rate 未提供, "
                              "且 FieldIdentityRegistry 无 validation.default")

    # 错误分支: 负面积
    if permanent_hm2 < 0 or temporary_hm2 < 0:
        raise CalculatorError(calc_id, "negative_area",
                              f"占地面积不能为负数: "
                              f"permanent={permanent_hm2} temporary={temporary_hm2}")

    # 错误分支: 非正费率
    if rate <= 0:
        raise CalculatorError(calc_id, "nonpositive_rate",
                              f"补偿费率必须为正数: rate={rate}")

    # 错误分支: 十倍偏差保险丝
    if rate < 0.1:
        raise CalculatorError(calc_id, "rate_too_low_suspected_historical_bias",
                              f"费率 {rate} 低于 0.1 元/m², 疑似命中历史样稿偏差 "
                              f"(如 0.06 元/m² 对应 2022 年前旧标准); "
                              f"v0 只接受广东新标准 0.6 元/m², 拒绝静默继承错误")

    # 公式计算
    chargeable_area_m2 = (permanent_hm2 + temporary_hm2) * 10000.0
    amount_yuan = chargeable_area_m2 * rate
    amount_wan = round(amount_yuan / 10000.0, 4)

    return CalcResult(
        calculator_id=calc_id,
        output_field_id="field.derived.investment.compensation_fee_amount",
        value=amount_wan,
        unit="万元",
        intermediate={
            "permanent_area_hm2": permanent_hm2,
            "temporary_area_hm2": temporary_hm2,
            "total_area_hm2": permanent_hm2 + temporary_hm2,
            "chargeable_area_m2": chargeable_area_m2,
            "rate_yuan_per_m2": rate,
            "amount_yuan": amount_yuan,
            "amount_wan": amount_wan,
        },
        inputs_snapshot={
            "field.fact.land.permanent_area": {"value": permanent_hm2, "unit": "hm²"},
            "field.fact.land.temporary_area": {"value": temporary_hm2, "unit": "hm²"},
            "field.fact.regulatory.compensation_fee_rate": {"value": rate, "unit": "元/m²"},
        },
    )


# ==================================================================
# calculator 实现: cal.target.weighted_comprehensive (Step 11B 硬编码)
# ==================================================================
# 6 项指标的名字, 对应 record 输出 key
_SIX_INDICATORS = (
    "control_degree",               # 水土流失治理度 (%)
    "soil_loss_control_ratio",      # 土壤流失控制比 (无量纲)
    "spoil_protection_rate",        # 渣土防护率 (%)
    "topsoil_protection_rate",      # 表土保护率 (%)
    "vegetation_restoration_rate",  # 林草植被恢复率 (%)
    "vegetation_coverage_rate",     # 林草覆盖率 (%)
)

# water_soil_zoning → reference_data key 的映射
# v0 只登记南方红壤区一张表, 其他 7 区在 v1+ 补齐
_ZONING_TO_TABLE_KEY = {
    "南方红壤区": "gbt50434_table_4_0_2_5",
    # v1+:
    # "东北黑土区": "gbt50434_table_4_0_2_1",
    # "北方风沙区": "gbt50434_table_4_0_2_2",
    # "北方土石山区": "gbt50434_table_4_0_2_3",
    # "西北黄土高原区": "gbt50434_table_4_0_2_4",
    # "西南紫色土区": "gbt50434_table_4_0_2_6",
    # "西南岩溶区": "gbt50434_table_4_0_2_7",
    # "青藏高原区": "gbt50434_table_4_0_2_8",
}

_VALID_LEVELS = ("一级", "二级", "三级")


def _get_area_value(area_field: Any) -> float:
    """从 area 字段提取 hm² 数值"""
    if isinstance(area_field, dict):
        return float(area_field.get("value", 0))
    if isinstance(area_field, (int, float)):
        return float(area_field)
    return 0.0


def _eval_weighted_comprehensive_target(calc_def: dict, sample: dict,
                                        fir: dict) -> CalcResult:
    """
    cal.target.weighted_comprehensive 硬编码实现。

    逻辑:
      1. 从 sample 读 water_soil_zoning, 查 reference_data 里的目标表
      2. 读 control_standard_level_breakdown (list of zones with area + level)
      3. 若只有 1 个等级 → 单等级兜底, 直接取表值
      4. 若多等级 → 按 area 权重对六项指标逐项加权
      5. 返回 record 型输出

    错误分支:
      - breakdown 为空 / 非 list → raise
      - water_soil_zoning 未登记 → raise (v0 只认南方红壤区)
      - zone.standard_level 非法 → raise
      - total_area <= 0 → raise
    """
    calc_id = "cal.target.weighted_comprehensive"

    # Step 1: 读 water_soil_zoning
    zoning = _get_field_value("field.fact.natural.water_soil_zoning", sample)
    if not zoning:
        raise CalculatorError(calc_id, "missing_input",
                              "field.fact.natural.water_soil_zoning 未提供")
    if zoning not in _ZONING_TO_TABLE_KEY:
        raise CalculatorError(calc_id, "zoning_not_registered",
                              f"water_soil_zoning '{zoning}' 未登记 reference_data 表; "
                              f"v0 仅支持南方红壤区, 其他 7 区在 v1+ 补齐。")

    # Step 2: 取 reference_data 对应的表
    ref_data = (calc_def.get("reference_data") or {}).get(_ZONING_TO_TABLE_KEY[zoning])
    if not ref_data:
        raise CalculatorError(calc_id, "reference_data_missing",
                              f"calculator reference_data 中未找到 "
                              f"{_ZONING_TO_TABLE_KEY[zoning]} 表")
    table = ref_data.get("水平年_values") or {}
    if not table:
        raise CalculatorError(calc_id, "reference_data_incomplete",
                              "reference_data.水平年_values 为空")

    # Step 3: 读 breakdown (list)
    breakdown = _get_field_value(
        "field.fact.prevention.control_standard_level_breakdown", sample)
    if breakdown is None or not isinstance(breakdown, list) or len(breakdown) == 0:
        raise CalculatorError(calc_id, "breakdown_empty",
                              "control_standard_level_breakdown 为空或非 list, "
                              "多等级加权必须提供 breakdown")

    # Step 4: 单等级兜底
    if len(breakdown) == 1:
        zone = breakdown[0]
        level = zone.get("standard_level")
        if level not in _VALID_LEVELS:
            raise CalculatorError(calc_id, "invalid_level",
                                  f"zone.standard_level='{level}' 非法")
        level_targets = table.get(level)
        if not level_targets:
            raise CalculatorError(calc_id, "level_not_in_table",
                                  f"标准 {level} 未在 reference_data 表中登记")
        result_record = dict(level_targets)  # 浅拷贝
        total_area = _get_area_value(zone.get("area"))
        return CalcResult(
            calculator_id=calc_id,
            output_field_id="field.derived.target.weighted_comprehensive_target",
            value=result_record,  # type: ignore[arg-type]
            unit="record",
            intermediate={
                "branch": "single_level_fallback",
                "level": level,
                "zoning": zoning,
                "total_area_hm2": total_area,
                "level_target_values": level_targets,
            },
            inputs_snapshot={
                "field.fact.natural.water_soil_zoning": zoning,
                "field.fact.prevention.control_standard_level_breakdown": breakdown,
            },
        )

    # Step 5: 多等级加权
    # 计算总面积
    total_area = 0.0
    for zone in breakdown:
        total_area += _get_area_value(zone.get("area"))
    if total_area <= 0:
        raise CalculatorError(calc_id, "total_area_nonpositive",
                              f"总责任范围面积 {total_area} 必须为正数")

    # 权重
    weights: list[tuple[str, float, str]] = []  # (zone_id, weight, level)
    for zone in breakdown:
        zid = zone.get("zone_id", "<unnamed>")
        level = zone.get("standard_level")
        if level not in _VALID_LEVELS:
            raise CalculatorError(calc_id, "invalid_level",
                                  f"zone {zid} standard_level='{level}' 非法")
        if level not in table:
            raise CalculatorError(calc_id, "level_not_in_table",
                                  f"zone {zid} 的标准 {level} 未在 reference_data 中登记")
        area = _get_area_value(zone.get("area"))
        w = area / total_area
        weights.append((zid, w, level))

    # 对每项指标加权
    result_record: dict[str, float] = {ind: 0.0 for ind in _SIX_INDICATORS}
    for zid, w, level in weights:
        level_targets = table[level]
        for ind in _SIX_INDICATORS:
            base = level_targets.get(ind)
            if base is None:
                raise CalculatorError(calc_id, "indicator_missing_in_table",
                                      f"指标 {ind} 在 {level} 行中缺失")
            result_record[ind] += w * float(base)

    # 四舍五入到 2 位小数 (工程精度)
    for ind in _SIX_INDICATORS:
        result_record[ind] = round(result_record[ind], 2)

    return CalcResult(
        calculator_id=calc_id,
        output_field_id="field.derived.target.weighted_comprehensive_target",
        value=result_record,  # type: ignore[arg-type]
        unit="record",
        intermediate={
            "branch": "multi_level_weighted",
            "zoning": zoning,
            "total_area_hm2": total_area,
            "weights": [{"zone_id": zid, "weight": round(w, 6), "level": lv}
                        for zid, w, lv in weights],
            "six_indicator_names": list(_SIX_INDICATORS),
        },
        inputs_snapshot={
            "field.fact.natural.water_soil_zoning": zoning,
            "field.fact.prevention.control_standard_level_breakdown": breakdown,
            "field.fact.prevention.control_standard_level":
                _get_field_value("field.fact.prevention.control_standard_level", sample),
        },
    )


# ==================================================================
# calculator 实现: cal.disposal_site.level_assessment (Step 11C 硬编码)
# ==================================================================
# GB 51018 表 5.7.1 三维判定 + "就高不就低"规则
# 约定: 1 级 = 最严重, 5 级 = 最轻
# 就高不就低 = 三路取最小数字

# 级别数字的大小比较 (1 级最严重 → 数字最小)
# Python 原生 str 比较 "1级" < "2级" 恰好成立, 但为了语义清晰, 用整数中间变量
_LEVEL_TO_INT = {"1级": 1, "2级": 2, "3级": 3, "4级": 4, "5级": 5}
_INT_TO_LEVEL = {v: k for k, v in _LEVEL_TO_INT.items()}
_VALID_HARM_CLASSES = ("严重", "较严重", "不严重", "较轻", "无危害")


def _level_by_volume(volume: float, thresholds: list) -> str:
    """根据堆渣量查 GB 51018 表 5.7.1 维度 1"""
    for row in thresholds:
        lo = float(row["min"])
        hi = float(row["max"])
        lvl = row["level"]
        # 区间是 [min, max): 每档 volume ∈ [min, max)
        # 但 1 级是 [1000, 2000] 闭区间 (GB 原文 2000 ≥ V ≥ 1000)
        # 其余档是 [lo, hi) 左闭右开
        if lvl == "1级":
            if lo <= volume <= hi:
                return lvl
        else:
            if lo <= volume < hi:
                return lvl
    # 超过 2000 视为 1 级 (极端情况)
    if volume > 2000.0:
        return "1级"
    # 负数或异常
    return "5级"  # 默认最轻


def _level_by_height(height: float, thresholds: list) -> str:
    """根据最大堆渣高度查 GB 51018 表 5.7.1 维度 2"""
    for row in thresholds:
        lo = float(row["min"])
        hi = float(row["max"])
        lvl = row["level"]
        if lvl == "1级":
            if lo <= height <= hi:
                return lvl
        elif lvl == "2级":
            # 2 级是 [100, 150] 闭区间 (150 ≥ H ≥ 100)
            if lo <= height <= hi:
                return lvl
        elif lvl == "3级":
            # 3 级是 [60, 100] 闭区间 (100 ≥ H ≥ 60)
            if lo <= height <= hi:
                return lvl
        else:
            if lo <= height < hi:
                return lvl
    if height > 200.0:
        return "1级"
    return "5级"


def _level_by_harm(harm_class: str, harm_map: dict) -> str:
    """根据下游危害程度查 GB 51018 表 5.7.1 维度 3 (enum→level)"""
    return harm_map.get(harm_class, "5级")


def _eval_disposal_site_level_assessment(calc_def: dict, sample: dict,
                                         fir: dict) -> CalcResult:
    """
    cal.disposal_site.level_assessment 硬编码实现。

    读取 field.fact.disposal_site.level_assessment (list of sites),
    对每个 site 按 GB 51018 表 5.7.1 三维判定 "就高不就低" 计算 level,
    返回 list_of_records 型 derived field 值。
    """
    calc_id = "cal.disposal_site.level_assessment"

    sites = _get_field_value("field.fact.disposal_site.level_assessment", sample)
    if sites is None:
        raise CalculatorError(calc_id, "missing_input",
                              "field.fact.disposal_site.level_assessment 未提供")
    if not isinstance(sites, list):
        raise CalculatorError(calc_id, "invalid_input",
                              "field.fact.disposal_site.level_assessment 必须是 list")

    # 空 list 是合法的 (项目无弃渣场)
    if len(sites) == 0:
        return CalcResult(
            calculator_id=calc_id,
            output_field_id="field.derived.disposal_site.level_assessment",
            value=[],  # type: ignore[arg-type]
            unit="list_of_records",
            intermediate={"branch": "empty_input", "sites_count": 0},
            inputs_snapshot={
                "field.fact.disposal_site.level_assessment": [],
            },
        )

    # 读 reference_data
    ref = (calc_def.get("reference_data") or {}).get("gb_51018_table_5_7_1")
    if not ref:
        raise CalculatorError(calc_id, "reference_data_missing",
                              "reference_data.gb_51018_table_5_7_1 未登记")
    volume_thresholds = ref.get("volume_thresholds") or []
    height_thresholds = ref.get("height_thresholds") or []
    harm_map = ref.get("harm_to_level") or {}

    result_sites: list[dict] = []

    for idx, site in enumerate(sites):
        if not isinstance(site, dict):
            raise CalculatorError(calc_id, "invalid_site_record",
                                  f"site[{idx}] 不是 dict")

        site_id = site.get("site_id", f"<site_{idx}>")
        site_name = site.get("site_name", "")

        # 取 volume
        vol_field = site.get("volume")
        if vol_field is None:
            raise CalculatorError(calc_id, "missing_input",
                                  f"site {site_id} 缺少 volume")
        volume = _get_area_value(vol_field)  # 复用 hm²/万m³ 取值

        # 取 max_height
        h_field = site.get("max_height")
        if h_field is None:
            raise CalculatorError(calc_id, "missing_input",
                                  f"site {site_id} 缺少 max_height")
        max_height = _get_area_value(h_field)

        # 取 downstream_harm_class
        harm_class = site.get("downstream_harm_class")
        if harm_class not in _VALID_HARM_CLASSES:
            raise CalculatorError(calc_id, "invalid_harm_class",
                                  f"site {site_id} downstream_harm_class "
                                  f"'{harm_class}' 不在 GB 51018 注 3 定义的 "
                                  f"5 个枚举之一: {_VALID_HARM_CLASSES}")

        # 错误分支: 负值
        if volume < 0 or max_height < 0:
            raise CalculatorError(calc_id, "negative_input",
                                  f"site {site_id} volume 或 max_height 为负数")
        # 错误分支: 双零
        if volume == 0 and max_height == 0:
            raise CalculatorError(calc_id, "zero_dimensions",
                                  f"site {site_id} volume 和 max_height 同时为 0, "
                                  f"此情形应不登记该场")

        # 三路查表
        l_vol = _level_by_volume(volume, volume_thresholds)
        l_ht = _level_by_height(max_height, height_thresholds)
        l_harm = _level_by_harm(harm_class, harm_map)

        # "就高不就低" = 取级别最高 = 取数字最小
        candidates = [
            (_LEVEL_TO_INT[l_vol], l_vol, "volume"),
            (_LEVEL_TO_INT[l_ht], l_ht, "height"),
            (_LEVEL_TO_INT[l_harm], l_harm, "harm"),
        ]
        candidates.sort(key=lambda x: x[0])  # 数字最小 = 级别最高
        winning_int, winning_level, governing = candidates[0]

        result_sites.append({
            "site_id": site_id,
            "site_name": site_name,
            "level": winning_level,
            "level_by_volume": l_vol,
            "level_by_height": l_ht,
            "level_by_harm": l_harm,
            "governing_dimension": governing,
        })

    return CalcResult(
        calculator_id=calc_id,
        output_field_id="field.derived.disposal_site.level_assessment",
        value=result_sites,  # type: ignore[arg-type]
        unit="list_of_records",
        intermediate={
            "branch": "multi_site_judgment",
            "sites_count": len(sites),
            "governing_dimensions_summary": [
                {"site_id": r["site_id"], "level": r["level"],
                 "governed_by": r["governing_dimension"]}
                for r in result_sites
            ],
        },
        inputs_snapshot={
            "field.fact.disposal_site.level_assessment":
                [{"site_id": s.get("site_id"),
                  "volume": _get_area_value(s.get("volume")),
                  "max_height": _get_area_value(s.get("max_height")),
                  "downstream_harm_class": s.get("downstream_harm_class")}
                 for s in sites]
        },
    )


# ==================================================================
# 注册表 (硬编码, 本轮 3 条)
# ==================================================================
_IMPLEMENTATIONS = {
    "cal.compensation.fee": _eval_compensation_fee,
    "cal.target.weighted_comprehensive": _eval_weighted_comprehensive_target,  # Step 11B
    "cal.disposal_site.level_assessment": _eval_disposal_site_level_assessment,  # Step 11C
}


# ==================================================================
# Registry 加载
# ==================================================================
def load_calculator_registry() -> dict:
    """读取 CalculatorRegistry_v0.yaml 并返回 dict"""
    path = SPECS_DIR / "CalculatorRegistry_v0.yaml"
    if not path.exists():
        raise CalculatorError("_loader", "missing_registry",
                              f"CalculatorRegistry_v0.yaml 未找到: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_field_identity_registry() -> dict:
    """读取 FieldIdentityRegistry_v0.yaml 并返回 dict"""
    path = SPECS_DIR / "FieldIdentityRegistry_v0.yaml"
    if not path.exists():
        raise CalculatorError("_loader", "missing_fir",
                              f"FieldIdentityRegistry_v0.yaml 未找到: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# ==================================================================
# 对外接口
# ==================================================================
def evaluate(calculator_id: str, sample: dict,
             registry: dict | None = None,
             fir: dict | None = None) -> CalcResult:
    """
    执行一条 calculator。

    参数:
      calculator_id: 必须在 CalculatorRegistry_v0.yaml 中登记
      sample: CPSWC sample JSON (dict)
      registry: 可选, 若不传则自动加载 CalculatorRegistry_v0.yaml
      fir: 可选, 若不传则自动加载 FieldIdentityRegistry_v0.yaml

    返回:
      CalcResult 对象
    """
    if registry is None:
        registry = load_calculator_registry()
    if fir is None:
        fir = load_field_identity_registry()

    calcs = registry.get("calculators") or {}
    if calculator_id not in calcs:
        raise CalculatorError(calculator_id, "not_registered",
                              f"calculator {calculator_id} 未在 "
                              f"CalculatorRegistry_v0.yaml 中登记")

    impl = _IMPLEMENTATIONS.get(calculator_id)
    if impl is None:
        raise CalculatorError(calculator_id, "no_implementation",
                              f"calculator {calculator_id} 已登记但无 Python 实现 "
                              f"(硬编码在 calculator_engine.py 中)")

    calc_def = calcs[calculator_id]
    return impl(calc_def, sample, fir)


# ==================================================================
# CLI (用于独立验证)
# ==================================================================
def _cli() -> int:
    """独立运行: 对默认惠州样本执行全部 live calculator"""
    import json as _json

    sample_path = SPECS_DIR / "CPSWC_SAMPLE_Huizhou_Housing_v0.json"
    with sample_path.open(encoding="utf-8") as f:
        sample = _json.load(f)

    registry = load_calculator_registry()
    fir = load_field_identity_registry()

    overall_ok = True
    for calc_id, calc_def in (registry.get("calculators") or {}).items():
        if (calc_def or {}).get("status") != "live":
            continue
        print("=" * 72)
        print(f"Calculator: {calc_id}")
        try:
            result = evaluate(calc_id, sample, registry=registry, fir=fir)
        except CalculatorError as e:
            print(f"FAIL: {e}", file=sys.stderr)
            overall_ok = False
            continue

        print(f"Output: {result.output_field_id}")
        if isinstance(result.value, dict):
            print(f"Value (record):")
            for k, v in result.value.items():
                print(f"  {k}: {v}")
        else:
            print(f"Value:  {result.value} {result.unit}")
        print()
        print("Intermediate steps:")
        for k, v in result.intermediate.items():
            print(f"  {k}: {v}")
        print()
        print("Inputs snapshot:")
        for k, v in result.inputs_snapshot.items():
            print(f"  {k}: {v}")
    print("=" * 72)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(_cli())
