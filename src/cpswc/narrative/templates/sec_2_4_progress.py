"""
sec_2_4_progress — 2.x 施工进度 narrative template

消费 facts: schedule.start_time / end_time / design_horizon_year
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_2_x.progress.v1",
    section_id="sec.project_overview.progress",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=["rule.template_2026.section_2"],
    supported_variants=["default"],
    input_fields=[
        "field.fact.schedule.start_time",
        "field.fact.schedule.end_time",
        "field.fact.schedule.design_horizon_year",
    ],
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        unit = v.get("unit", "")
        return f"{v['value']} {unit}".strip()
    return str(v)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    start = _v(facts, "field.fact.schedule.start_time")
    end = _v(facts, "field.fact.schedule.end_time")
    horizon = _v(facts, "field.fact.schedule.design_horizon_year")

    p1 = NarrativeParagraph(
        text=(
            f"本项目计划于{start}开工，{end}竣工。"
            f"水土保持方案设计水平年为{horizon}年。"
        ),
        evidence_refs=[
            "field.fact.schedule.start_time",
            "field.fact.schedule.end_time",
            "field.fact.schedule.design_horizon_year",
        ],
        source_rule_refs=["rule.template_2026.section_2"],
    )

    return NarrativeBlock(
        section_id="sec.project_overview.progress",
        title="施工进度",
        render_status=RenderStatus.FULL,
        paragraphs=[p1],
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
    )
