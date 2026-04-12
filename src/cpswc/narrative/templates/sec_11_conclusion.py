"""
sec_11_conclusion — 第 11 章 结论 narrative template

全局收束段: 汇总项目基本合规状态、关键义务、必要制品、关键指标。
高低风险样本应有明显差异但结构一致。
单 variant (default)。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)

TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_11.conclusion.v1",
    section_id="sec.conclusion",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=["rule.template_2026.section_11"],
    supported_variants=["default"],
    input_fields=[
        "field.fact.project.name",
        "field.fact.project.industry_category",
        "field.fact.prevention.control_standard_level",
        "field.derived.investment.compensation_fee_amount",
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


def render(facts: dict, derived: dict, triggered: set[str],
           snapshot: dict | None = None, **kwargs) -> NarrativeBlock:
    name = _v(facts, "field.fact.project.name")
    level = _v(facts, "field.fact.prevention.control_standard_level")
    fee = derived.get("field.derived.investment.compensation_fee_amount")
    fee_str = f"{fee} 万元" if fee is not None else "—"

    triggered_count = len(triggered)
    # Count required artifacts from snapshot if available
    art_count = len((snapshot or {}).get("required_artifacts") or [])
    assurance_count = len((snapshot or {}).get("required_assurances") or [])

    paragraphs = [
        NarrativeParagraph(
            text=(
                f"综上所述，{name}的水土保持方案编制依据充分，"
                + (f"防治标准等级为{level}，" if level and level != "—" else "")
                + f"各项防治指标目标值符合 GB/T 50434-2018 的要求。"
            ),
            evidence_refs=[
                "field.fact.project.name",
                "field.fact.prevention.control_standard_level",
            ],
            source_rule_refs=[
                "rule.gb_t_50434_2018.chapter_4",
                "rule.template_2026.section_11",
            ],
        ),
        NarrativeParagraph(
            text=(
                f"本方案共触发{triggered_count}项水土保持义务，"
                f"需编制{art_count}项制品（附表、附图、附件等），"
                f"需满足{assurance_count}项保障要求。"
                f"水土保持补偿费为{fee_str}。"
            ),
            evidence_refs=[
                "field.derived.investment.compensation_fee_amount",
                "cal.compensation.fee",
            ],
            source_rule_refs=[
                "rule.template_2026.section_11",
            ],
        ),
    ]

    # 高风险差异: 弃渣场级别
    disposal_levels = derived.get("field.derived.disposal_site.level_assessment")
    if isinstance(disposal_levels, list) and len(disposal_levels) > 0:
        levels_desc = []
        for site in disposal_levels:
            sid = site.get("site_id", "?")
            lv = site.get("level", "?")
            levels_desc.append(f"{sid}({lv})")
        high_risk_obs = [ob for ob in triggered
                         if ob in ("ob.disposal_site.geology_report",
                                   "ob.disposal_site.stability_monitoring",
                                   "ob.disposal_site.video_surveillance")]
        paragraphs.append(NarrativeParagraph(
            text=(
                f"本项目设有{len(disposal_levels)}处弃渣场，"
                f"级别评定结果为: {'、'.join(levels_desc)}。"
                + (f"其中触发了{len(high_risk_obs)}项高风险弃渣场义务"
                   f"（{'、'.join(high_risk_obs)}）。"
                   if high_risk_obs else
                   "各弃渣场级别未触发高风险义务。")
            ),
            evidence_refs=[
                "field.derived.disposal_site.level_assessment",
                "cal.disposal_site.level_assessment",
            ] + high_risk_obs,
            source_rule_refs=[
                "rule.gb_51018_2014.section_5_7_1",
            ],
        ))

    paragraphs.append(NarrativeParagraph(
        text=(
            "本方案各项内容符合现行法律法规和技术标准要求，"
            "水土保持措施布局合理，投资估算依据充分。"
            "建议按本方案实施，确保水土保持目标的实现。"
        ),
        evidence_refs=[],
        source_rule_refs=["rule.template_2026.section_11"],
    ))

    return NarrativeBlock(
        section_id="sec.conclusion",
        title="结论",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )
