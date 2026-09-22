"""
sec_1_2_spec_sheet — 1.2 水土保持工程特性表 narrative template

最简 pilot: 仅输出一句引导语, 实际特性表由 table_projections 自动嵌入。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence

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
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence("sec.overview.spec_sheet_end", facts, derived,
                         ledger=ledger, context=context)
    # 原实现 `facts.get(key, "本项目")`: 项目名没填就悄悄替换成"本项目",
    # 读者看不出这里缺了一个已登记字段。
    name = ev.text("field.fact.project.name")
    subject = name.display() if name.is_present else "本项目"

    p = NarrativeParagraph(
        text=(f"{subject}工程特性表汇总了项目基本信息、占地情况、土石方平衡"
              f"及水土保持相关参数，详见下表。"),
        evidence_refs=["field.fact.project.name", "art.table.spec_sheet"],
        source_rule_refs=["rule.template_2026.section_1"],
        assertion_class=AssertionClass.NORMATIVE_REQUIREMENT,
        paragraph_id="narr.overview.spec_sheet_end.intro",
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
        quality_findings=ev.findings,
    )
