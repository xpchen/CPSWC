"""
sec_9_2_compensation — 9.2 水土保持补偿费 narrative template

消费 cal.compensation.fee 输出, 解释征收依据、计算逻辑、金额结论。
单 variant (default): 所有项目都有补偿费。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)

TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_9_2.compensation.v1",
    section_id="sec.investment_estimation.compensation_fee",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.guangdong.fa_gai_2021_231",
        "rule.ministry_order_53",
        "rule.template_2026.section_9",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.derived.investment.compensation_fee_amount",
        "field.fact.regulatory.compensation_fee_rate",
        "field.fact.land.permanent_area",
        "field.fact.land.temporary_area",
        "field.fact.location.province_list",
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
    province = _v(facts, "field.fact.location.province_list")
    perm = _v(facts, "field.fact.land.permanent_area")
    temp = _v(facts, "field.fact.land.temporary_area")
    rate = _v(facts, "field.fact.regulatory.compensation_fee_rate")
    fee = derived.get("field.derived.investment.compensation_fee_amount")
    fee_str = f"{fee} 万元" if fee is not None else "—"

    paragraphs = [
        NarrativeParagraph(
            text=(
                f"根据水利部令第 53 号及{province}水土保持补偿费征收标准"
                f"（粤发改价格〔2021〕231 号），"
                f"本项目属一般性生产建设项目，适用费率为{rate}，一次性计征。"
            ),
            evidence_refs=[
                "field.fact.regulatory.compensation_fee_rate",
                "field.fact.location.province_list",
            ],
            source_rule_refs=[
                "rule.ministry_order_53",
                "rule.guangdong.fa_gai_2021_231",
            ],
        ),
        NarrativeParagraph(
            text=(
                f"计征范围为永久占地{perm}与临时占地{temp}之和"
                f"（广东口径含临时占地），"
                f"经 cal.compensation.fee 计算，"
                f"本项目应缴水土保持补偿费为{fee_str}。"
                f"详见补偿费计算表。"
            ),
            evidence_refs=[
                "field.fact.land.permanent_area",
                "field.fact.land.temporary_area",
                "field.derived.investment.compensation_fee_amount",
                "cal.compensation.fee",
                "art.table.investment.compensation_fee",
            ],
            source_rule_refs=[
                "rule.guangdong.fa_gai_2021_231",
                "rule.template_2026.section_9",
            ],
        ),
    ]

    return NarrativeBlock(
        section_id="sec.investment_estimation.compensation_fee",
        title="水土保持补偿费",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )
