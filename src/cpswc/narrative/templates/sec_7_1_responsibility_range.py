"""
sec_7_1_responsibility_range — 7.1 水土流失防治责任范围 narrative template

纯 facts 投影: 防治责任范围 = 永久占地 + 临时占地 + 其他管辖区域。
引用 GB 50433-2018 第 4.4.1 条。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)

TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_7_1.responsibility_range.v1",
    section_id="sec.soil_loss_prevention.responsibility_range",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.gb_50433_2018.section_4_4_1",
        "rule.template_2026.section_7",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.land.total_area",
        "field.fact.land.permanent_area",
        "field.fact.land.temporary_area",
        "field.fact.land.county_breakdown",
    ],
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        unit = v.get("unit", "")
        return f"{v['value']} {unit}".strip()
    if isinstance(v, list):
        return "、".join(str(x) for x in v)
    return str(v)


def _num(facts: dict, key: str, default: float = 0.0) -> float:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        try:
            return float(v["value"])
        except (ValueError, TypeError):
            return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    total_area = _v(facts, "field.fact.land.total_area")
    perm = _v(facts, "field.fact.land.permanent_area")
    temp = _v(facts, "field.fact.land.temporary_area")
    temp_n = _num(facts, "field.fact.land.temporary_area")

    paragraphs = []

    # 主段: 法规依据 + 范围界定
    temp_clause = f"临时占地{temp}" if temp_n > 0 else "无临时占地"
    p1 = NarrativeParagraph(
        text=(
            f"根据《生产建设项目水土保持技术标准》（GB 50433-2018）第 4.4.1 条，"
            f"生产建设项目水土流失防治责任范围应包括项目永久征地、临时占地"
            f"（含租赁土地）以及其他使用与管辖区域。"
            f"本项目总占地面积{total_area}，其中永久占地{perm}，{temp_clause}，"
            f"水土流失防治责任范围为{total_area}。"
        ),
        evidence_refs=[
            "field.fact.land.total_area",
            "field.fact.land.permanent_area",
            "field.fact.land.temporary_area",
        ],
        source_rule_refs=[
            "rule.gb_50433_2018.section_4_4_1",
            "rule.template_2026.section_7",
        ],
    )
    paragraphs.append(p1)

    # 分区段: 如有 county_breakdown, 列出防治分区
    breakdown = facts.get("field.fact.land.county_breakdown")
    if isinstance(breakdown, list) and breakdown:
        zone_descs = []
        for rec in breakdown:
            comp = rec.get("type", "—")
            area = rec.get("area", {})
            area_str = (f"{area.get('value', '—')} {area.get('unit', '')}"
                        if isinstance(area, dict) else str(area))
            zone_descs.append(f"{comp}（{area_str.strip()}）")

        p2 = NarrativeParagraph(
            text=(
                f"防治责任范围内共划分{len(breakdown)}个防治分区: "
                f"{'、'.join(zone_descs)}。"
                f"详见防治责任范围及分区表。"
            ),
            evidence_refs=[
                "field.fact.land.county_breakdown",
                "art.table.responsibility_range_by_admin_division",
            ],
            source_rule_refs=[
                "rule.template_2026.section_7",
            ],
        )
        paragraphs.append(p2)

    return NarrativeBlock(
        section_id="sec.soil_loss_prevention.responsibility_range",
        title="水土流失防治责任范围",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )


# ============================================================
# 7.1.1 分县级行政区防治责任范围 (Step 42 补完)
# ============================================================
TEMPLATE_SPEC_BY_COUNTY = NarrativeTemplateSpec(
    template_id="nt.sec_7_1_1.responsibility_range_by_county.v1",
    section_id="sec.soil_loss_prevention.responsibility_range_by_county",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_7",
        "rule.2023_177.review_dimension_county_breakdown",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.land.county_breakdown",
        "field.fact.location.county_list",
    ],
)


def render_by_county(facts: dict, derived: dict, triggered: set[str],
                     **kwargs) -> NarrativeBlock:
    """7.1.1 分县级行政区防治责任范围"""
    county_list = _v(facts, "field.fact.location.county_list")
    breakdown = facts.get("field.fact.land.county_breakdown")

    # 跨行政区才有实际内容
    is_multi_admin = "ob.sensitive_overlay.multi_admin_breakdown" in triggered

    if not is_multi_admin:
        return NarrativeBlock(
            section_id="sec.soil_loss_prevention.responsibility_range_by_county",
            title="分县级行政区防治责任范围",
            render_status=RenderStatus.NOT_APPLICABLE,
            paragraphs=[],
            variant_id="default",
            template_id=TEMPLATE_SPEC_BY_COUNTY.template_id,
            template_version=TEMPLATE_SPEC_BY_COUNTY.template_version,
            normative_basis=TEMPLATE_SPEC_BY_COUNTY.normative_basis,
        )

    paragraphs = []

    p1_text = f"本项目涉及{county_list}等行政区域。根据审查要点要求，跨行政区项目应按县级行政区分别列出防治责任范围面积。"
    paragraphs.append(NarrativeParagraph(
        text=p1_text,
        evidence_refs=["field.fact.location.county_list"],
        source_rule_refs=["rule.2023_177.review_dimension_county_breakdown"],
    ))

    if isinstance(breakdown, list) and breakdown:
        # 尝试按 county 分组
        by_county: dict[str, float] = {}
        for rec in breakdown:
            county = rec.get("county") or rec.get("zone_id", "未知")
            area = rec.get("area", {})
            a = float(area.get("value", 0)) if isinstance(area, dict) else float(area or 0)
            by_county[county] = by_county.get(county, 0) + a

        if by_county:
            parts = [f"{c}：{a:.2f} hm²" for c, a in by_county.items()]
            p2 = NarrativeParagraph(
                text=f"各行政区防治责任范围面积分别为：{'；'.join(parts)}。详见分县级行政区防治责任范围统计表。",
                evidence_refs=["field.fact.land.county_breakdown",
                               "art.table.responsibility_range_by_admin_division"],
                source_rule_refs=["rule.template_2026.section_7"],
            )
            paragraphs.append(p2)

    return NarrativeBlock(
        section_id="sec.soil_loss_prevention.responsibility_range_by_county",
        title="分县级行政区防治责任范围",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_BY_COUNTY.template_id,
        template_version=TEMPLATE_SPEC_BY_COUNTY.template_version,
        normative_basis=TEMPLATE_SPEC_BY_COUNTY.normative_basis,
    )
