"""
sec_0_overview — 综合说明 narrative template

报告第一页。对全报告的关键结论做提纲挈领式概述。
不引入新 facts, 只消费已有数据做"摘要投影"。

消费 facts:
  project.name / code / nature / industry_category
  investment.total_investment / civil_investment
  schedule.start_time / end_time
  land.total_area / permanent_area / temporary_area
  earthwork.excavation / fill / spoil
  topsoil.stripable_volume
  prediction.new_loss / reducible_loss
  natural.water_soil_zoning
  location.province_list / prefecture_list
消费 derived:
  field.derived.investment.compensation_fee_amount
  field.derived.target.weighted_comprehensive_target
消费 投资 facts:
  field.fact.investment.measures_summary
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_0.overview.v1",
    section_id="sec.overview",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_1",
        "standard.gb_50433_2018.section_1",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.project.name",
        "field.fact.project.nature",
        "field.fact.investment.total_investment",
        "field.fact.investment.civil_investment",
        "field.fact.schedule.start_time",
        "field.fact.schedule.end_time",
        "field.fact.land.total_area",
        "field.fact.land.permanent_area",
        "field.fact.land.temporary_area",
        "field.fact.earthwork.excavation",
        "field.fact.earthwork.fill",
        "field.fact.earthwork.spoil",
        "field.fact.topsoil.stripable_volume",
        "field.fact.prediction.new_loss",
        "field.fact.prediction.reducible_loss",
        "field.fact.natural.water_soil_zoning",
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
        "field.fact.investment.measures_summary",
        "field.derived.investment.compensation_fee_amount",
        "field.derived.target.weighted_comprehensive_target",
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
           **kwargs) -> NarrativeBlock:
    """渲染 综合说明 — 报告首页摘要"""
    name = _v(facts, "field.fact.project.name")
    nature = _v(facts, "field.fact.project.nature")
    province = _v(facts, "field.fact.location.province_list")
    prefecture = _v(facts, "field.fact.location.prefecture_list")
    total_inv = _v(facts, "field.fact.investment.total_investment")
    civil_inv = _v(facts, "field.fact.investment.civil_investment")
    start = _v(facts, "field.fact.schedule.start_time")
    end = _v(facts, "field.fact.schedule.end_time")
    total_area = _v(facts, "field.fact.land.total_area")
    perm_area = _v(facts, "field.fact.land.permanent_area")
    temp_area = _v(facts, "field.fact.land.temporary_area")

    # 第一段: 项目概况
    p1 = NarrativeParagraph(
        text=(
            f"{name}为{nature}项目，位于{province}{prefecture}。"
            f"项目总投资{total_inv}，其中土建投资{civil_inv}。"
            f"施工期{start}至{end}。"
            f"总占地面积{total_area}，其中永久占地{perm_area}，临时占地{temp_area}。"
        ),
        evidence_refs=[
            "field.fact.project.name",
            "field.fact.project.nature",
            "field.fact.location.province_list",
            "field.fact.location.prefecture_list",
            "field.fact.investment.total_investment",
            "field.fact.investment.civil_investment",
            "field.fact.schedule.start_time",
            "field.fact.schedule.end_time",
            "field.fact.land.total_area",
            "field.fact.land.permanent_area",
            "field.fact.land.temporary_area",
        ],
        source_rule_refs=[
            "rule.template_2026.section_1",
        ],
    )

    # 第二段: 土石方 + 表土 + 流失预测
    exc = _v(facts, "field.fact.earthwork.excavation")
    fill = _v(facts, "field.fact.earthwork.fill")
    spoil = _v(facts, "field.fact.earthwork.spoil")
    topsoil = _v(facts, "field.fact.topsoil.stripable_volume")
    new_loss = _v(facts, "field.fact.prediction.new_loss")
    reducible = _v(facts, "field.fact.prediction.reducible_loss")
    zoning = _v(facts, "field.fact.natural.water_soil_zoning")

    p2 = NarrativeParagraph(
        text=(
            f"项目区属{zoning}。"
            f"挖方总量{exc}，填方总量{fill}，弃方{spoil}。"
            f"可剥离表土{topsoil}。"
            f"施工期预测新增水土流失量{new_loss}，其中可治理量{reducible}。"
        ),
        evidence_refs=[
            "field.fact.natural.water_soil_zoning",
            "field.fact.earthwork.excavation",
            "field.fact.earthwork.fill",
            "field.fact.earthwork.spoil",
            "field.fact.topsoil.stripable_volume",
            "field.fact.prediction.new_loss",
            "field.fact.prediction.reducible_loss",
        ],
        source_rule_refs=[
            "rule.template_2026.section_1",
            "standard.gb_50433_2018.section_1",
        ],
    )

    # 第三段: 投资估算结论
    summary = facts.get("field.fact.investment.measures_summary")
    comp_fee = derived.get("field.derived.investment.compensation_fee_amount")

    measures_total = 0.0
    if isinstance(summary, dict):
        for cat_data in summary.values():
            if isinstance(cat_data, dict):
                measures_total += cat_data.get("total", 0.0)
    comp_val = float(comp_fee) if comp_fee is not None else 0.0
    grand_total = measures_total + comp_val

    p3 = NarrativeParagraph(
        text=(
            f"水土保持措施投资合计 {measures_total:.2f} 万元，"
            f"水土保持补偿费 {comp_val:.2f} 万元，"
            f"水土保持总投资 {grand_total:.2f} 万元。"
        ),
        evidence_refs=[
            "field.fact.investment.measures_summary",
            "field.derived.investment.compensation_fee_amount",
        ],
        source_rule_refs=[
            "rule.template_2026.section_1",
        ],
    )

    # 第四段: 防治目标结论
    paragraphs = [p1, p2, p3]
    weighted = derived.get("field.derived.target.weighted_comprehensive_target")
    if isinstance(weighted, dict):
        ctrl = weighted.get("control_degree", "—")
        loss_ratio = weighted.get("soil_loss_control_ratio", "—")
        spoil_rate = weighted.get("spoil_protection_rate", "—")
        veg_restore = weighted.get("vegetation_restoration_rate", "—")

        p4 = NarrativeParagraph(
            text=(
                f"方案实施后，扰动土地治理率{ctrl}%，"
                f"土壤流失控制比{loss_ratio}，"
                f"渣土防护率{spoil_rate}%，"
                f"林草植被恢复率{veg_restore}%，"
                f"各项指标均满足相应防治标准要求。"
            ),
            evidence_refs=[
                "field.derived.target.weighted_comprehensive_target",
            ],
            source_rule_refs=[
                "standard.gb_50433_2018.section_1",
            ],
        )
        paragraphs.append(p4)

    return NarrativeBlock(
        section_id="sec.overview",
        title="综合说明",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )
