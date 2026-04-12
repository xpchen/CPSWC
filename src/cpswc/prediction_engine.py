"""
prediction_engine.py — 水土流失预测核心引擎 (Step 31B)

Contract:
  - 预测单元通过 derive_prediction_units(facts) 派生, 不绑死任何单一 fact 字段
  - Phases 复用 schedule_phases.derive_phases()
  - 背景模数: field.fact.natural.original_erosion_modulus
  - 扰动模数: 内建标准矩阵为默认 + 项目级可选覆盖 (全局/分区)
  - 公式: background_loss_t = area_hm2/100 * M_bg * months/12
          disturbed_loss_t  = area_hm2/100 * M_dist * months/12
          new_loss_t = disturbed_loss_t - background_loss_t
  - 所有默认模数带来源标签 (modulus_source)

红线:
  1. 预测粒度: 分区 × 时段, 不追分措施/分月
  2. 所有默认模数必须带来源标签
  3. 恢复期模数也走矩阵, 不硬编码常量
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================
# 1. Prediction Unit 派生
# ============================================================

@dataclass
class PredictionUnit:
    """最小预测单元: 一个防治分区."""
    zone_id: str          # 唯一标识 (e.g. "pu_1")
    zone_type: str        # 分区类型 (e.g. "主体工程区")
    area_hm2: float       # 面积 (hm²)
    nature: str = ""      # "永久" / "临时"


def derive_prediction_units(facts: dict) -> list[PredictionUnit]:
    """
    从现有 facts 派生预测单元。

    当前 v1-alpha: 从 county_breakdown 提取工程分区作为派生输入。
    未来: 可从显式 prevention_zones / disturbance_zones facts 派生。

    不将 county_breakdown 视为预测单元的长期语义根。
    """
    units: list[PredictionUnit] = []

    breakdown = facts.get("field.fact.land.county_breakdown")
    if isinstance(breakdown, list) and breakdown:
        for i, zone in enumerate(breakdown):
            zone_type = zone.get("type", f"分区{i+1}")
            area_raw = zone.get("area")
            if isinstance(area_raw, dict):
                area = float(area_raw.get("value", 0))
            elif isinstance(area_raw, (int, float)):
                area = float(area_raw)
            else:
                area = 0.0
            nature = zone.get("nature", "")
            units.append(PredictionUnit(
                zone_id=f"pu_{i+1}",
                zone_type=zone_type,
                area_hm2=area,
                nature=nature,
            ))
    else:
        # Fallback: single unit from total area
        total = facts.get("field.fact.land.total_area")
        if isinstance(total, dict):
            area = float(total.get("value", 0))
        elif isinstance(total, (int, float)):
            area = float(total)
        else:
            area = 0.0
        units.append(PredictionUnit(
            zone_id="pu_1",
            zone_type="项目区",
            area_hm2=area,
        ))

    return units


# ============================================================
# 2. 标准扰动侵蚀模数矩阵
# ============================================================
# 来源: 类比工程经验值 + GB 50433-2018 附录参考
# key = zone type keyword
# value = (construction_modulus, recovery_modulus)  单位: t/(km²·a)

_DISTURBED_MODULUS_MATRIX: list[tuple[str, float, float, str]] = [
    # (zone_keyword, construction_modulus, recovery_modulus, source_note)
    ("主体",    5000, 800,  "类比: 城建项目主体工程区施工期典型值"),
    ("建筑",    5000, 800,  "类比: 建筑物区施工期典型值"),
    ("道路",    4500, 700,  "类比: 道路工程施工期典型值"),
    ("广场",    3500, 500,  "类比: 硬化广场施工期典型值"),
    ("绿化",    2000, 500,  "类比: 绿化区施工期典型值"),
    ("景观",    2000, 500,  "类比: 景观绿化区施工期典型值"),
    ("临时堆土", 8000, 1200, "类比: 临时堆土区裸露扰动典型值"),
    ("施工生产", 4000, 800,  "类比: 施工生产生活区典型值"),
    ("弃渣",   10000, 1500, "类比: 弃渣场高扰动典型值"),
    ("取土",    8000, 1200, "类比: 取土场典型值"),
]

_DEFAULT_DISTURBED = (5000, 800, "类比: 一般扰动区默认值")


def _match_disturbed_modulus(zone_type: str) -> tuple[float, float, str]:
    """Match zone type to (construction_modulus, recovery_modulus, source_note)."""
    for keyword, m_c, m_r, note in _DISTURBED_MODULUS_MATRIX:
        if keyword in zone_type:
            return m_c, m_r, note
    return _DEFAULT_DISTURBED


# ============================================================
# 3. 模数解析 (默认矩阵 + 项目覆盖)
# ============================================================

@dataclass
class ModulusInfo:
    """扰动模数信息, 含来源追溯."""
    construction: float        # t/(km²·a)
    recovery: float            # t/(km²·a)
    source: str                # "default_matrix" | "project_override"
    source_note: str = ""      # 具体来源说明


def resolve_disturbed_modulus(
    zone_type: str,
    zone_id: str,
    facts: dict,
) -> ModulusInfo:
    """
    解析扰动模数, 优先级:
      1. 分区级覆盖 (prediction.zone_modulus_overrides)
      2. 全项目覆盖 (prediction.disturbed_modulus_override)
      3. 标准矩阵默认值
    """
    # Check zone-level override
    zone_overrides = facts.get("field.fact.prediction.zone_modulus_overrides")
    if isinstance(zone_overrides, list):
        for ov in zone_overrides:
            if isinstance(ov, dict) and ov.get("zone_id") == zone_id:
                return ModulusInfo(
                    construction=float(ov.get("construction", 0)),
                    recovery=float(ov.get("recovery", 0)),
                    source="project_override",
                    source_note=f"分区覆盖: {zone_id}",
                )

    # Check project-level override
    proj_override = facts.get("field.fact.prediction.disturbed_modulus_override")
    if isinstance(proj_override, dict):
        m_c = proj_override.get("construction")
        m_r = proj_override.get("recovery")
        if m_c is not None and m_r is not None:
            return ModulusInfo(
                construction=float(m_c),
                recovery=float(m_r),
                source="project_override",
                source_note="全项目统一覆盖",
            )

    # Default matrix
    m_c, m_r, note = _match_disturbed_modulus(zone_type)
    return ModulusInfo(
        construction=m_c,
        recovery=m_r,
        source="default_matrix",
        source_note=note,
    )


# ============================================================
# 4. 预测计算核心
# ============================================================

@dataclass
class ZonePrediction:
    """单分区单时段预测结果."""
    zone_id: str
    zone_type: str
    area_hm2: float
    period: str                    # "施工期" / "自然恢复期"
    months: int
    background_modulus: float      # t/(km²·a)
    disturbed_modulus: float       # t/(km²·a)
    background_loss_t: float       # 背景流失量 (t)
    disturbed_loss_t: float        # 扰动后流失量 (t)
    new_loss_t: float              # 新增流失量 (t)
    modulus_source: str            # "default_matrix" | "project_override"
    modulus_source_note: str = ""


@dataclass
class PredictionResult:
    """完整预测结果."""
    zone_results: list[ZonePrediction] = field(default_factory=list)
    total_loss_t: float = 0.0          # 总流失量 (t)
    total_new_loss_t: float = 0.0      # 新增流失量 (t)
    total_background_loss_t: float = 0.0
    total_area_hm2: float = 0.0
    background_modulus: float = 0.0    # 原地貌模数
    summary_by_period: dict = field(default_factory=dict)


def _get_val(facts: dict, key: str) -> float:
    v = facts.get(key)
    if isinstance(v, dict) and "value" in v:
        return float(v["value"])
    if isinstance(v, (int, float)):
        return float(v)
    return 0.0


def compute_prediction(facts: dict) -> PredictionResult:
    """
    核心预测计算。

    分区 × 时段, 输出可审计的预测结果。
    """
    from cpswc.narrative.templates.schedule_phases import derive_phases

    # 1. Derive prediction units
    units = derive_prediction_units(facts)

    # 2. Derive phases and compute durations
    phases = derive_phases(facts)

    def _month_diff(s: str, e: str) -> int:
        """Compute months between YYYY-MM strings."""
        try:
            sp = s.split("-")
            ep = e.split("-")
            return (int(ep[0]) - int(sp[0])) * 12 + (int(ep[1]) - int(sp[1]))
        except (ValueError, IndexError):
            return 0

    # For prediction, prep + construction = "施工期", recovery = "自然恢复期"
    construction_months = 0
    recovery_months = 0
    for p in phases:
        dur = _month_diff(p.start, p.end)
        if p.phase_id in ("prep", "construction"):
            construction_months += dur
        elif p.phase_id == "recovery":
            recovery_months += dur

    # Fallback if no phases derived
    if construction_months == 0 and recovery_months == 0:
        construction_months = 12
        recovery_months = 6

    # 3. Background modulus
    bg_modulus = _get_val(facts, "field.fact.natural.original_erosion_modulus")
    if bg_modulus == 0:
        # Check if it's stored as raw number without dict wrapper
        raw = facts.get("field.fact.natural.original_erosion_modulus")
        if isinstance(raw, (int, float)):
            bg_modulus = float(raw)

    # 4. Compute per-zone per-period
    results: list[ZonePrediction] = []
    total_area = sum(u.area_hm2 for u in units)

    for unit in units:
        modulus_info = resolve_disturbed_modulus(unit.zone_type, unit.zone_id, facts)

        # Construction period
        if construction_months > 0:
            area_km2 = unit.area_hm2 / 100.0
            bg_loss = area_km2 * bg_modulus * construction_months / 12.0
            dist_loss = area_km2 * modulus_info.construction * construction_months / 12.0
            new_loss = dist_loss - bg_loss

            results.append(ZonePrediction(
                zone_id=unit.zone_id,
                zone_type=unit.zone_type,
                area_hm2=unit.area_hm2,
                period="施工期",
                months=construction_months,
                background_modulus=bg_modulus,
                disturbed_modulus=modulus_info.construction,
                background_loss_t=round(bg_loss, 2),
                disturbed_loss_t=round(dist_loss, 2),
                new_loss_t=round(new_loss, 2),
                modulus_source=modulus_info.source,
                modulus_source_note=modulus_info.source_note,
            ))

        # Recovery period (only for zones that have recovery relevance)
        if recovery_months > 0:
            area_km2 = unit.area_hm2 / 100.0
            bg_loss = area_km2 * bg_modulus * recovery_months / 12.0
            dist_loss = area_km2 * modulus_info.recovery * recovery_months / 12.0
            new_loss = dist_loss - bg_loss

            results.append(ZonePrediction(
                zone_id=unit.zone_id,
                zone_type=unit.zone_type,
                area_hm2=unit.area_hm2,
                period="自然恢复期",
                months=recovery_months,
                background_modulus=bg_modulus,
                disturbed_modulus=modulus_info.recovery,
                background_loss_t=round(bg_loss, 2),
                disturbed_loss_t=round(dist_loss, 2),
                new_loss_t=round(new_loss, 2),
                modulus_source=modulus_info.source,
                modulus_source_note=modulus_info.source_note,
            ))

    # 5. Aggregate
    total_loss = sum(r.disturbed_loss_t for r in results)
    total_new = sum(r.new_loss_t for r in results)
    total_bg = sum(r.background_loss_t for r in results)

    # Summary by period
    summary: dict[str, dict[str, float]] = {}
    for r in results:
        if r.period not in summary:
            summary[r.period] = {
                "area_hm2": 0, "disturbed_loss_t": 0,
                "background_loss_t": 0, "new_loss_t": 0,
            }
        s = summary[r.period]
        s["area_hm2"] += r.area_hm2
        s["disturbed_loss_t"] += r.disturbed_loss_t
        s["background_loss_t"] += r.background_loss_t
        s["new_loss_t"] += r.new_loss_t

    return PredictionResult(
        zone_results=results,
        total_loss_t=round(total_loss, 2),
        total_new_loss_t=round(total_new, 2),
        total_background_loss_t=round(total_bg, 2),
        total_area_hm2=total_area,
        background_modulus=bg_modulus,
        summary_by_period=summary,
    )


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="CPSWC 水土流失预测引擎 (Step 31B)")
    parser.add_argument("sample_json", help="项目 facts JSON 文件")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    with open(args.sample_json, encoding="utf-8") as f:
        data = json.load(f)
    facts = data.get("facts", data)

    result = compute_prediction(facts)

    if args.json:
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), ensure_ascii=False, indent=2))
    else:
        print(f"预测总面积: {result.total_area_hm2} hm²")
        print(f"背景侵蚀模数: {result.background_modulus} t/(km²·a)")
        print(f"总流失量: {result.total_loss_t} t")
        print(f"新增流失量: {result.total_new_loss_t} t")
        print(f"背景流失量: {result.total_background_loss_t} t")
        print()
        print(f"{'分区':<16} {'时段':<10} {'面积hm²':>8} {'扰动模数':>8} "
              f"{'流失量t':>8} {'新增t':>8} {'来源'}")
        print("-" * 90)
        for r in result.zone_results:
            print(f"{r.zone_type:<16} {r.period:<10} {r.area_hm2:>8.2f} "
                  f"{r.disturbed_modulus:>8.0f} {r.disturbed_loss_t:>8.2f} "
                  f"{r.new_loss_t:>8.2f} {r.modulus_source}")


if __name__ == "__main__":
    main()
