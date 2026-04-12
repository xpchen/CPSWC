"""
sec_7_3_design_horizon — 7.x 设计水平年 narrative template

消费 facts: schedule.end_time / design_horizon_year
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_7_x.design_horizon.v1",
    section_id="sec.soil_loss_prevention.design_horizon",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_7",
        "standard.gb_t_50434_2018",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.schedule.end_time",
        "field.fact.schedule.design_horizon_year",
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
    end = _v(facts, "field.fact.schedule.end_time")
    horizon = _v(facts, "field.fact.schedule.design_horizon_year")

    p1 = NarrativeParagraph(
        text=(
            f"本项目计划竣工时间为{end}，"
            f"按照 GB/T 50434-2018 规定，"
            f"生产建设项目水土保持方案设计水平年一般为工程完工后的第一个完整自然年。"
            f"本项目设计水平年确定为{horizon}年。"
        ),
        evidence_refs=[
            "field.fact.schedule.end_time",
            "field.fact.schedule.design_horizon_year",
        ],
        source_rule_refs=[
            "rule.template_2026.section_7",
            "standard.gb_t_50434_2018",
        ],
    )

    return NarrativeBlock(
        section_id="sec.soil_loss_prevention.design_horizon",
        title="设计水平年",
        render_status=RenderStatus.FULL,
        paragraphs=[p1],
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
    )
