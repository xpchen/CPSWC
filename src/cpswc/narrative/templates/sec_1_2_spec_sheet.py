"""
sec_1_2_spec_sheet — 1.2 水土保持工程特性表 narrative template

最简 pilot: 仅输出一句引导语, 实际特性表由 table_projections 自动嵌入。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)

TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_1_2.spec_sheet.v1",
    section_id="sec.overview.spec_sheet_end",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=["rule.template_2026.section_1"],
    supported_variants=["default"],
    input_fields=[
        "field.fact.project.name",
    ],
)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    name = facts.get("field.fact.project.name", "本项目")

    p = NarrativeParagraph(
        text=f"{name}工程特性表汇总了项目基本信息、占地情况、土石方平衡及水土保持相关参数，详见下表。",
        evidence_refs=["field.fact.project.name"],
        source_rule_refs=["rule.template_2026.section_1"],
    )

    return NarrativeBlock(
        section_id="sec.overview.spec_sheet_end",
        title="水土保持工程特性表",
        render_status=RenderStatus.FULL,
        paragraphs=[p],
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )
