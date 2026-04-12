"""
sec_8_1_monitoring_scope — 8.1 监测范围与时段

2026 模板要求:
  明确水土保持监测范围和时段，施工准备期应进行本底值监测。

消费 facts: schedule.*, land.total_area, land.permanent_area, land.temporary_area
推导: schedule_phases → 三阶段时段
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)
from cpswc.narrative.templates.schedule_phases import derive_phases, format_phases_text


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_8_1.monitoring_scope.v1",
    section_id="sec.monitoring.scope_and_period",
    template_version="v1",
    template_author="cpswc_v1",
    normative_basis=[
        "rule.template_2026.section_8",
        "standard.gb_50433_2018",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.schedule.start_time",
        "field.fact.schedule.end_time",
        "field.fact.schedule.design_horizon_year",
        "field.fact.land.total_area",
    ],
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        return f"{v['value']} {v.get('unit', '')}".strip()
    return str(v)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    total_area = _v(facts, "field.fact.land.total_area")
    phases = derive_phases(facts)

    # Scope paragraph
    p1 = NarrativeParagraph(
        text=(
            f"水土保持监测范围为项目水土流失防治责任范围，面积{total_area}。"
            f"监测范围覆盖全部永久占地和临时占地区域。"
        ),
        evidence_refs=[
            "field.fact.land.total_area",
        ],
        source_rule_refs=["rule.template_2026.section_8"],
    )

    # Time periods
    if phases:
        phase_text = format_phases_text(phases)
        period_detail = f"监测时段划分为{phase_text}。"

        # Baseline monitoring requirement
        prep = next((p for p in phases if p.phase_id == "prep"), None)
        if prep:
            period_detail += (
                f"其中施工准备期（{prep.start}至{prep.end}）"
                f"应进行本底值监测，掌握项目区水土流失背景值。"
            )
    else:
        start = _v(facts, "field.fact.schedule.start_time")
        end = _v(facts, "field.fact.schedule.end_time")
        period_detail = (
            f"监测时段自{start}至项目水土保持设施验收完成。"
            f"施工准备期应进行本底值监测，掌握项目区水土流失背景值。"
        )

    p2 = NarrativeParagraph(
        text=period_detail,
        evidence_refs=[
            "field.fact.schedule.start_time",
            "field.fact.schedule.end_time",
            "field.fact.schedule.design_horizon_year",
        ],
        source_rule_refs=[
            "rule.template_2026.section_8",
            "rule.t2026.monitoring_baseline",
        ],
    )

    return NarrativeBlock(
        section_id="sec.monitoring.scope_and_period",
        title="监测范围与时段",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2],
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
    )
