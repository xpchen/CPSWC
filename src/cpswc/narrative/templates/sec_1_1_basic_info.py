"""
sec_1_1_basic_info — 1.1 项目基本情况 narrative template

最简单的 pilot section: 纯 facts 投影, 无条件分支, 单 variant。
用于验证 facts → NarrativeParagraph → NarrativeBlock 的完整链路。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence


TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_1_1.basic_info.v1",
    section_id="sec.overview.project_basic",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_1_1",  # 2026 模板 1.1 节要求列出基本信息
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.project.name",
        "field.fact.project.code",
        "field.fact.project.industry_category",
        "field.fact.project.nature",
        "field.fact.investment.total_investment",
        "field.fact.investment.civil_investment",
        "field.fact.schedule.start_time",
        "field.fact.schedule.end_time",
        "field.fact.land.total_area",
        "field.fact.land.permanent_area",
        "field.fact.land.temporary_area",
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
    ],
)


def render(facts: dict, derived: dict, triggered: set[str],
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """渲染 1.1 项目基本情况"""
    SEC = "sec.overview.project_basic"
    ev = SectionEvidence(SEC, facts, derived, ledger=ledger, context=context)

    name = ev.text("field.fact.project.name")
    code = ev.text("field.fact.project.code")
    industry = ev.text("field.fact.project.industry_category")
    nature = ev.text("field.fact.project.nature")
    total_inv = ev.quantity("field.fact.investment.total_investment")
    civil_inv = ev.quantity("field.fact.investment.civil_investment")
    start = ev.text("field.fact.schedule.start_time")
    end = ev.text("field.fact.schedule.end_time")
    total_area = ev.quantity("field.fact.land.total_area")
    perm_area = ev.quantity("field.fact.land.permanent_area")
    temp_area = ev.quantity("field.fact.land.temporary_area")
    province = ev.text("field.fact.location.province_list")
    prefecture = ev.text("field.fact.location.prefecture_list")

    g1 = [name, nature, industry, province, prefecture, total_inv, civil_inv]
    if ev.all_present(*g1):
        p1 = NarrativeParagraph(
            text=(
                f"{name.display()}"
                f"{'（项目代码：' + code.display() + '）' if code.is_present else ''}"
                f"为{nature.display()}项目，"
                f"属{industry.display()}类行业，"
                f"位于{province.display()}{prefecture.display()}。"
                f"项目总投资{total_inv.display()}，"
                f"其中土建投资{civil_inv.display()}。"
            ),
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.overview.project_basic.identity",
        evidence_refs=[
            "field.fact.project.name",
            "field.fact.project.code",
            "field.fact.project.industry_category",
            "field.fact.project.nature",
            "field.fact.investment.total_investment",
            "field.fact.investment.civil_investment",
            "field.fact.location.province_list",
            "field.fact.location.prefecture_list",
        ],
        source_rule_refs=["rule.template_2026.section_1_1"],
        )
    else:
        p1 = ev.gap_paragraph(
            *g1, lead="项目基本信息不完整",
            source_rule_refs=["rule.template_2026.section_1_1"],
            paragraph_id="narr.overview.project_basic.identity")

    g2 = [start, end, total_area, perm_area, temp_area]
    if ev.all_present(*g2):
        p2 = NarrativeParagraph(
            text=(
                f"施工期为{start.display()}至{end.display()}。"
                f"项目总占地面积{total_area.display()}，"
                f"其中永久占地{perm_area.display()}，"
                f"临时占地{temp_area.display()}。"
            ),
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.overview.project_basic.schedule_and_land",
        evidence_refs=[
            "field.fact.schedule.start_time",
            "field.fact.schedule.end_time",
            "field.fact.land.total_area",
            "field.fact.land.permanent_area",
            "field.fact.land.temporary_area",
        ],
        source_rule_refs=["rule.template_2026.section_1_1"],
        )
    else:
        p2 = ev.gap_paragraph(
            *g2, lead="施工期与占地数据不完整",
            source_rule_refs=["rule.template_2026.section_1_1"],
            paragraph_id="narr.overview.project_basic.schedule_and_land")

    return NarrativeBlock(
        section_id="sec.overview.project_basic",
        title="项目基本情况",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2],
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )
