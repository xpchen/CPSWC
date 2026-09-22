"""
sec_2_4_progress — 2.x 施工进度 narrative template

消费 facts: schedule.start_time / end_time / design_horizon_year
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence


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


def render(facts: dict, derived: dict, triggered: set[str],
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    SEC = "sec.project_overview.progress"
    ev = SectionEvidence(SEC, facts, derived, ledger=ledger, context=context)
    start = ev.text("field.fact.schedule.start_time")
    end = ev.text("field.fact.schedule.end_time")
    horizon = ev.text("field.fact.schedule.design_horizon_year")

    if not ev.all_present(start, end, horizon):
        p1 = ev.gap_paragraph(
            start, end, horizon,
            lead="施工进度信息不完整",
            source_rule_refs=["rule.template_2026.section_2"],
            paragraph_id="narr.project_overview.progress.schedule")
    else:
        p1 = NarrativeParagraph(
        text=(
            f"本项目计划于{start.display()}开工，{end.display()}竣工。"
            f"水土保持方案设计水平年为{horizon.display()}年。"
        ),
        assertion_class=AssertionClass.FACT_RESTATEMENT,
        paragraph_id="narr.project_overview.progress.schedule",
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
        quality_findings=ev.findings,
    )
