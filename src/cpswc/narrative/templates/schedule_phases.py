"""
schedule_phases — 施工阶段推导工具

从 schedule.start_time / end_time / design_horizon_year 推导三阶段:
  - 施工准备期
  - 施工期
  - 自然恢复期

规则:
  - 准备期占总工期前 10-15%, 最少 1 个月, 最多 2 个月
  - 施工期 = 准备期结束 ~ end_time
  - 恢复期 = end_time ~ design_horizon_year 年底

如果 intake 提供了 schedule.phases, 以用户输入为准。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Phase:
    phase_id: str
    name: str
    start: str  # YYYY-MM
    end: str    # YYYY-MM


def _parse_ym(s: str) -> tuple[int, int]:
    """Parse 'YYYY-MM' → (year, month)."""
    parts = str(s).split("-")
    return int(parts[0]), int(parts[1])


def _fmt_ym(y: int, m: int) -> str:
    return f"{y}-{m:02d}"


def _add_months(y: int, m: int, n: int) -> tuple[int, int]:
    m += n
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    return y, m


def _month_diff(y1: int, m1: int, y2: int, m2: int) -> int:
    return (y2 - y1) * 12 + (m2 - m1)


def derive_phases(facts: dict) -> list[Phase]:
    """
    Derive construction phases from facts.

    Uses schedule.phases if provided by user; otherwise derives from
    start_time / end_time / design_horizon_year.
    """
    # Check if user provided explicit phases
    user_phases = facts.get("field.fact.schedule.phases")
    if isinstance(user_phases, list) and user_phases:
        return [
            Phase(
                phase_id=p.get("phase_id", f"phase_{i}"),
                name=p.get("name", f"阶段{i+1}"),
                start=p.get("start", ""),
                end=p.get("end", ""),
            )
            for i, p in enumerate(user_phases)
        ]

    # Auto-derive
    start_raw = facts.get("field.fact.schedule.start_time", "")
    end_raw = facts.get("field.fact.schedule.end_time", "")
    horizon = facts.get("field.fact.schedule.design_horizon_year")

    if not start_raw or not end_raw:
        return []

    try:
        sy, sm = _parse_ym(start_raw)
        ey, em = _parse_ym(end_raw)
    except (ValueError, IndexError):
        return []

    # Prep duration: 10-15% of total, min 1 month, max 2 months
    total_months = _month_diff(sy, sm, ey, em)
    if total_months <= 0:
        return []

    prep_months = max(1, min(2, round(total_months * 0.12)))
    prep_end_y, prep_end_m = _add_months(sy, sm, prep_months)

    phases = [
        Phase("prep", "施工准备期", _fmt_ym(sy, sm), _fmt_ym(prep_end_y, prep_end_m)),
        Phase("construction", "施工期", _fmt_ym(prep_end_y, prep_end_m), _fmt_ym(ey, em)),
    ]

    # Recovery period
    if horizon and isinstance(horizon, int) and horizon > ey:
        phases.append(Phase(
            "recovery", "自然恢复期",
            _fmt_ym(ey, em), f"{horizon}-12",
        ))
    elif horizon and isinstance(horizon, int):
        # horizon year same as end year — recovery to year end
        phases.append(Phase(
            "recovery", "自然恢复期",
            _fmt_ym(ey, em), f"{horizon}-12",
        ))

    return phases


def format_phases_text(phases: list[Phase]) -> str:
    """Format phases as human-readable enumeration."""
    parts = []
    for p in phases:
        parts.append(f"{p.name}（{p.start}至{p.end}）")
    return "、".join(parts)
