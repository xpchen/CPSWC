"""
sec_2_5_sensitive_areas — 2.x 敏感区域 narrative template

强制按 SensitiveAreaTypeRegistry_v0 的 12 类 canonical 清单"逐项排查":
  - 命中项 (来自 facts.natural.other_sensitive_areas) 逐条详述
  - 未命中项汇总为单句 "经核查, 项目区不涉及 A、B、C... 等水土保持敏感区"
  - 重点预防/治理区 (key_prevention_treatment_areas) 单独成段

消费 facts: natural.other_sensitive_areas / key_prevention_treatment_areas
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


# SensitiveAreaTypeRegistry_v0 canonical 12 类 (display_name 顺序与 registry 一致)
# 与 registries/SensitiveAreaTypeRegistry_v0.yaml 保持镜像; 任一处变更需同步.
SENSITIVE_AREA_CANONICAL: tuple[str, ...] = (
    "流域管理范围",
    "河湖管理范围",
    "饮用水水源保护区",
    "水功能一级区（保护区与保留区）",
    "自然保护区",
    "世界文化和自然遗产地",
    "风景名胜区",
    "地质公园",
    "森林公园",
    "重要湿地",
    "生态保护红线",
    "永久基本农田",
)


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_2_x.sensitive_areas.v2",
    section_id="sec.project_overview.sensitive_areas",
    template_version="v2",
    template_author="cpswc_v0.6",
    normative_basis=[
        "rule.template_2026.section_2",
        "standard.gb_50433_2018.section_2",
        "registry.sensitive_area_type_v0",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.other_sensitive_areas",
        "field.fact.natural.key_prevention_treatment_areas",
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
    ],
)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    sensitive = facts.get("field.fact.natural.other_sensitive_areas") or []
    key_areas = facts.get("field.fact.natural.key_prevention_treatment_areas") or []

    paragraphs: list[NarrativeParagraph] = []

    # ---------- 段 1: 水土流失重点预防区/治理区 ----------
    if isinstance(key_areas, list) and key_areas:
        paragraphs.append(NarrativeParagraph(
            text=(
                f"项目区涉及水土流失重点预防区或重点治理区："
                f"{'、'.join(str(a) for a in key_areas)}。"
            ),
            evidence_refs=["field.fact.natural.key_prevention_treatment_areas"],
            source_rule_refs=["rule.template_2026.section_2"],
        ))
    else:
        paragraphs.append(NarrativeParagraph(
            text=(
                "经核查，项目区不属于国家级、省级及市级划定的"
                "水土流失重点预防区和重点治理区。"
            ),
            evidence_refs=["field.fact.natural.key_prevention_treatment_areas"],
            source_rule_refs=["rule.template_2026.section_2"],
        ))

    # ---------- 段 2..N: 命中的 12 类敏感区, 逐条详述 ----------
    hit_types: set[str] = set()
    if isinstance(sensitive, list):
        for area in sensitive:
            if not isinstance(area, dict):
                continue
            area_type = area.get("area_type", "敏感区域")
            hit_types.add(area_type)
            name = area.get("name", "—")
            spatial = area.get("spatial_relation", "—")
            approval = area.get("approval_status", "—")
            paragraphs.append(NarrativeParagraph(
                text=(
                    f"经核查，项目区涉及{area_type}：{name}。"
                    f"空间关系为：{spatial}。"
                    f"审批状态：{approval}。"
                ),
                evidence_refs=["field.fact.natural.other_sensitive_areas"],
                source_rule_refs=[
                    "rule.template_2026.section_2",
                    "standard.gb_50433_2018.section_2",
                    "registry.sensitive_area_type_v0",
                ],
            ))

    # ---------- 段末: 未命中类型逐项排查汇总 ----------
    not_hit = [t for t in SENSITIVE_AREA_CANONICAL if t not in hit_types]
    if not_hit:
        if hit_types:
            lead = "除上述涉及项外，项目区不涉及"
        else:
            lead = "经逐项排查，项目区不涉及"
        paragraphs.append(NarrativeParagraph(
            text=f"{lead}{'、'.join(not_hit)}等水土保持敏感区。",
            evidence_refs=["field.fact.natural.other_sensitive_areas"],
            source_rule_refs=[
                "rule.template_2026.section_2",
                "standard.gb_50433_2018.section_2",
                "registry.sensitive_area_type_v0",
            ],
        ))

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
