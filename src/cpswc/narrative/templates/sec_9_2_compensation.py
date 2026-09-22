"""
sec_9_2_compensation — 9.2 水土保持补偿费 narrative template

消费 cal.compensation.fee 输出, 解释征收依据、计算逻辑、金额结论。
单 variant (default): 所有项目都有补偿费。

B 批 P0-04 改造 (任务 B-T5):
  补偿费金额直接进投资表, 错值影响面大。原实现用 `_v(..., default="—")` 与
  `f"{fee} 万元" if fee is not None else "—"`, 费率或面积缺失时整段照样成句,
  读者看不出这笔钱是算出来的还是没算。现在缺任何一项计征要素都走缺口段。
"""
from __future__ import annotations

from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence

SECTION_ID = "sec.investment_estimation.compensation_fee"

TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_9_2.compensation.v2",
    section_id=SECTION_ID,
    template_version="v2",
    template_author="cpswc_p0_04",
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


def render(facts: dict, derived: dict, triggered: set[str],
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence(SECTION_ID, facts, derived, ledger=ledger,
                         context=context)

    province = ev.text("field.fact.location.province_list")
    rate = ev.raw("field.fact.regulatory.compensation_fee_rate")
    perm = ev.quantity("field.fact.land.permanent_area")
    temp = ev.quantity("field.fact.land.temporary_area")
    fee = ev.raw("field.derived.investment.compensation_fee_amount")

    paragraphs: list[NarrativeParagraph] = []

    # 段 1: 征收依据与费率
    if ev.all_present(province, rate):
        paragraphs.append(NarrativeParagraph(
            text=(f"根据水利部令第 53 号及{province.display()}水土保持补偿费"
                  f"征收标准（粤发改价格〔2021〕231 号），本项目属一般性生产建设"
                  f"项目，适用费率为{rate.display()}，一次性计征。"),
            evidence_refs=["field.fact.regulatory.compensation_fee_rate",
                           "field.fact.location.province_list"],
            source_rule_refs=["rule.ministry_order_53",
                              "rule.guangdong.fa_gai_2021_231"],
            assertion_class=AssertionClass.NORMATIVE_REQUIREMENT,
            paragraph_id="narr.investment_estimation.compensation_fee.basis",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            province, rate,
            lead="补偿费征收依据不完整，无法确定适用费率",
            source_rule_refs=["rule.ministry_order_53"],
            paragraph_id="narr.investment_estimation.compensation_fee.basis",
        ))

    # 段 2: 计征范围与金额 —— 面积或金额缺任一项都不给结论
    if ev.all_present(perm, temp, fee):
        paragraphs.append(NarrativeParagraph(
            text=(f"计征范围为永久占地{perm.display()}与临时占地{temp.display()}"
                  f"之和（广东口径含临时占地），经 cal.compensation.fee 计算，"
                  f"本项目应缴水土保持补偿费为{fee.display()}万元。"
                  f"详见水土保持补偿费计费表。"),
            evidence_refs=["field.fact.land.permanent_area",
                           "field.fact.land.temporary_area",
                           "field.derived.investment.compensation_fee_amount",
                           "cal.compensation.fee",
                           "art.table.compensation_fee_detail"],
            source_rule_refs=["rule.guangdong.fa_gai_2021_231",
                              "rule.template_2026.section_9"],
            assertion_class=AssertionClass.ARITHMETIC,
            paragraph_id="narr.investment_estimation.compensation_fee.amount",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            perm, temp, fee,
            lead="补偿费计征要素不完整，本轮无有效补偿费金额",
            source_rule_refs=["rule.guangdong.fa_gai_2021_231"],
            extra_refs=["cal.compensation.fee"],
            paragraph_id="narr.investment_estimation.compensation_fee.amount",
        ))

    return NarrativeBlock(
        section_id=SECTION_ID,
        title="水土保持补偿费",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
        quality_findings=ev.findings,
    )
