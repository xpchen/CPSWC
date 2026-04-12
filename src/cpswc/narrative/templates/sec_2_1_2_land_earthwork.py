"""
sec_2_1_2_land_earthwork — 2.1 占地面积 + 2.2 土石方平衡 narrative templates

facts 密集章节。关键纪律: 像报告语言, 不能变成字段串烧。
单 variant (default)。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)

TEMPLATE_SPEC_2_1 = NarrativeTemplateSpec(
    template_id="nt.sec_2_1.land_occupation.v1",
    section_id="sec.project_overview.land_occupation",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=["rule.template_2026.section_2_1"],
    supported_variants=["default"],
    input_fields=[
        "field.fact.land.total_area",
        "field.fact.land.permanent_area",
        "field.fact.land.temporary_area",
    ],
)

TEMPLATE_SPEC_2_2 = NarrativeTemplateSpec(
    template_id="nt.sec_2_2.earthwork_balance.v1",
    section_id="sec.project_overview.earthwork_balance",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=["rule.template_2026.section_2_2"],
    supported_variants=["default"],
    input_fields=[
        "field.fact.earthwork.excavation",
        "field.fact.earthwork.fill",
        "field.fact.earthwork.spoil",
        "field.fact.earthwork.borrow",
        "field.fact.earthwork.comprehensive_reuse",
        "field.fact.earthwork.self_reuse",
    ],
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        unit = v.get("unit", "")
        return f"{v['value']} {unit}".strip()
    return str(v)


def render_2_1(facts: dict, derived: dict, triggered: set[str],
               **kwargs) -> NarrativeBlock:
    total = _v(facts, "field.fact.land.total_area")
    perm = _v(facts, "field.fact.land.permanent_area")
    temp = _v(facts, "field.fact.land.temporary_area")

    return NarrativeBlock(
        section_id="sec.project_overview.land_occupation",
        title="占地面积",
        render_status=RenderStatus.FULL,
        paragraphs=[NarrativeParagraph(
            text=(
                f"本项目总占地面积为{total}，"
                f"其中永久占地{perm}，临时占地{temp}。"
                f"永久占地包括建筑物基底、道路及永久性附属设施占地；"
                f"临时占地包括施工生产生活区、施工道路、"
                f"临时堆土场及其他施工临时用地。"
            ),
            evidence_refs=[
                "field.fact.land.total_area",
                "field.fact.land.permanent_area",
                "field.fact.land.temporary_area",
            ],
            source_rule_refs=["rule.template_2026.section_2_1"],
        )],
        variant_id="default",
        template_id=TEMPLATE_SPEC_2_1.template_id,
        template_version=TEMPLATE_SPEC_2_1.template_version,
        normative_basis=TEMPLATE_SPEC_2_1.normative_basis,
    )


def render_2_2(facts: dict, derived: dict, triggered: set[str],
               **kwargs) -> NarrativeBlock:
    exc = _v(facts, "field.fact.earthwork.excavation")
    fill = _v(facts, "field.fact.earthwork.fill")
    spoil = _v(facts, "field.fact.earthwork.spoil")
    borrow = _v(facts, "field.fact.earthwork.borrow")
    reuse = _v(facts, "field.fact.earthwork.comprehensive_reuse")
    self_reuse = _v(facts, "field.fact.earthwork.self_reuse")

    paragraphs = [
        NarrativeParagraph(
            text=(
                f"本项目挖方总量{exc}（不含表土），填方总量{fill}。"
                f"项目自身利用挖方{self_reuse}用于场地回填及地基处理。"
            ),
            evidence_refs=[
                "field.fact.earthwork.excavation",
                "field.fact.earthwork.fill",
                "field.fact.earthwork.self_reuse",
            ],
            source_rule_refs=["rule.template_2026.section_2_2"],
        ),
    ]

    # 借方 / 弃方 / 综合利用说明
    borrow_val = facts.get("field.fact.earthwork.borrow")
    borrow_num = borrow_val.get("value", 0) if isinstance(borrow_val, dict) else 0
    spoil_val = facts.get("field.fact.earthwork.spoil")
    spoil_num = spoil_val.get("value", 0) if isinstance(spoil_val, dict) else 0
    reuse_val = facts.get("field.fact.earthwork.comprehensive_reuse")
    reuse_num = reuse_val.get("value", 0) if isinstance(reuse_val, dict) else 0

    balance_parts = []
    if borrow_num > 0:
        balance_parts.append(f"需外购借方{borrow}")
    if spoil_num > 0:
        if reuse_num > 0:
            balance_parts.append(
                f"产生弃渣{spoil}，其中综合利用{reuse}")
        else:
            balance_parts.append(f"产生弃渣{spoil}")
    if not balance_parts:
        balance_parts.append("土石方基本平衡")

    paragraphs.append(NarrativeParagraph(
        text="；".join(balance_parts) + "。",
        evidence_refs=[
            "field.fact.earthwork.spoil",
            "field.fact.earthwork.borrow",
            "field.fact.earthwork.comprehensive_reuse",
        ],
        source_rule_refs=["rule.template_2026.section_2_2"],
    ))

    return NarrativeBlock(
        section_id="sec.project_overview.earthwork_balance",
        title="土石方平衡",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_2_2.template_id,
        template_version=TEMPLATE_SPEC_2_2.template_version,
        normative_basis=TEMPLATE_SPEC_2_2.normative_basis,
    )
