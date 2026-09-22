"""
sec_7_3_design_horizon — 7.x 设计水平年 narrative template

消费 facts: schedule.end_time / design_horizon_year
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence


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


def render(facts: dict, derived: dict, triggered: set[str],
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    SEC = "sec.soil_loss_prevention.design_horizon"
    ev = SectionEvidence(SEC, facts, derived, ledger=ledger, context=context)
    end = ev.text("field.fact.schedule.end_time")
    horizon = ev.text("field.fact.schedule.design_horizon_year")

    if not ev.all_present(end, horizon):
        p1 = ev.gap_paragraph(
            end, horizon,
            lead="竣工时间或设计水平年缺失，无法确定设计水平年",
            source_rule_refs=["standard.gb_t_50434_2018"],
            paragraph_id="narr.soil_loss_prevention.design_horizon.value")
    else:
        p1 = NarrativeParagraph(
        text=(
            f"本项目计划竣工时间为{end.display()}，"
            f"按照 GB/T 50434-2018 规定，"
            f"生产建设项目水土保持方案设计水平年一般为工程完工后的第一个完整自然年。"
            f"本项目设计水平年确定为{horizon.display()}年。"
        ),
        assertion_class=AssertionClass.FACT_RESTATEMENT,
        paragraph_id="narr.soil_loss_prevention.design_horizon.value",
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
        quality_findings=ev.findings,
    )
