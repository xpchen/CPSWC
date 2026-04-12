"""
sec_3_1_site_selection — 3.1 选址选线水土保持评价 narrative template

Conditional: ob.unavoidability.redline_conflict
消费 facts: natural.other_sensitive_areas
           location.province_list / prefecture_list

措辞原则:
  - 严格复述 facts 中的 spatial_relation 和 approval_status
  - 评价结论只做"是否符合选址要求"的判断
  - 不替代审批部门做审批结论
  - 如果 approval_status 显示"待确认", 则如实表述为"待审批确认"
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_3_1.site_selection.v1",
    section_id="sec.evaluation.site_selection",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_3",
        "standard.gb_50433_2018.section_3",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.other_sensitive_areas",
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
    ],
)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    sensitive = facts.get("field.fact.natural.other_sensitive_areas")
    province = facts.get("field.fact.location.province_list")
    if isinstance(province, list):
        province = "、".join(province)
    else:
        province = str(province) if province else "—"

    paragraphs = []

    if isinstance(sensitive, list) and sensitive:
        for area in sensitive:
            area_type = area.get("area_type", "敏感区域")
            name = area.get("name", "—")
            spatial = area.get("spatial_relation", "—")
            approval = area.get("approval_status", "—")

            p = NarrativeParagraph(
                text=(
                    f"本项目涉及{area_type}（{name}），{spatial}。"
                    f"目前{approval}。"
                ),
                evidence_refs=["field.fact.natural.other_sensitive_areas"],
                source_rule_refs=[
                    "rule.template_2026.section_3",
                    "standard.gb_50433_2018.section_3",
                ],
            )
            paragraphs.append(p)

        # 评价结论: 基于 facts 做合规性判断, 不替代审批
        conclusion = NarrativeParagraph(
            text=(
                "从水土保持角度分析，项目选址已对涉及的敏感区域进行了核查，"
                "相关不可避让论证程序已启动或完成。"
                "在落实本方案提出的水土保持措施后，"
                "项目选址基本符合水土保持相关法律法规要求。"
            ),
            evidence_refs=[
                "field.fact.natural.other_sensitive_areas",
                "ob.unavoidability.redline_conflict",
            ],
            source_rule_refs=[
                "standard.gb_50433_2018.section_3",
            ],
        )
        paragraphs.append(conclusion)
    else:
        p = NarrativeParagraph(
            text=(
                "本项目不涉及生态保护红线、自然保护区等敏感区域，"
                "选址符合水土保持相关法律法规要求。"
            ),
            evidence_refs=["field.fact.natural.other_sensitive_areas"],
            source_rule_refs=["standard.gb_50433_2018.section_3"],
        )
        paragraphs.append(p)

    return NarrativeBlock(
        section_id="sec.evaluation.site_selection",
        title="选址选线水土保持评价",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
    )
