"""
sec_2_5_sensitive_areas — 2.x 敏感区域 narrative template

Conditional: ob.unavoidability.redline_conflict
消费 facts: natural.other_sensitive_areas / key_prevention_treatment_areas
           location.province_list / prefecture_list

措辞原则:
  - 严格复述 facts 中的 spatial_relation 和 approval_status
  - 不夸大影响范围, 不自行推断审批结论
  - 如果 facts 说"未实质占用", 就写"未实质占用"
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_2_x.sensitive_areas.v1",
    section_id="sec.project_overview.sensitive_areas",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_2",
        "standard.gb_50433_2018.section_2",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.other_sensitive_areas",
        "field.fact.natural.key_prevention_treatment_areas",
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
    ],
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        return f"{v['value']} {v.get('unit', '')}".strip()
    if isinstance(v, list):
        return "、".join(str(x) for x in v) if v else default
    return str(v)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    sensitive = facts.get("field.fact.natural.other_sensitive_areas")
    key_areas = facts.get("field.fact.natural.key_prevention_treatment_areas")

    paragraphs = []

    # 重点预防/治理区
    if isinstance(key_areas, list) and key_areas:
        p_key = NarrativeParagraph(
            text=(
                f"项目区涉及国家级水土流失重点预防区或重点治理区："
                f"{'、'.join(str(a) for a in key_areas)}。"
            ),
            evidence_refs=["field.fact.natural.key_prevention_treatment_areas"],
            source_rule_refs=["rule.template_2026.section_2"],
        )
        paragraphs.append(p_key)

    # 敏感区 (逐条复述 facts, 不自行推断)
    if isinstance(sensitive, list) and sensitive:
        for area in sensitive:
            area_type = area.get("area_type", "敏感区域")
            name = area.get("name", "—")
            spatial = area.get("spatial_relation", "—")
            approval = area.get("approval_status", "—")

            p = NarrativeParagraph(
                text=(
                    f"经核查，项目区涉及{area_type}：{name}。"
                    f"空间关系为：{spatial}。"
                    f"审批状态：{approval}。"
                ),
                evidence_refs=["field.fact.natural.other_sensitive_areas"],
                source_rule_refs=[
                    "rule.template_2026.section_2",
                    "standard.gb_50433_2018.section_2",
                ],
            )
            paragraphs.append(p)
    else:
        p_none = NarrativeParagraph(
            text="经核查，项目区不涉及生态保护红线、自然保护区等敏感区域。",
            evidence_refs=["field.fact.natural.other_sensitive_areas"],
            source_rule_refs=["rule.template_2026.section_2"],
        )
        paragraphs.append(p_none)

    return NarrativeBlock(
        section_id="sec.project_overview.sensitive_areas",
        title="敏感区域",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
    )
