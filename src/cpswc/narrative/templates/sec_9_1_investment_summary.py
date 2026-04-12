"""
sec_9_1_investment_summary — 9.1 投资估算汇总 narrative template

消费 facts:
  field.fact.investment.measures_summary  — {费类: {new, existing, total}}
  field.fact.investment.measures_registry — list of measure records
  field.derived.investment.compensation_fee_amount
消费 derived:
  field.derived.investment.compensation_fee_amount
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_9_1.investment_summary.v1",
    section_id="sec.investment.summary",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_9",
        "standard.gb_50433_2018.section_9",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.investment.measures_summary",
        "field.fact.investment.measures_registry",
        "field.derived.investment.compensation_fee_amount",
    ],
)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    """渲染 9.1 投资估算汇总"""

    summary = facts.get("field.fact.investment.measures_summary")
    registry = facts.get("field.fact.investment.measures_registry")
    comp_fee = derived.get("field.derived.investment.compensation_fee_amount")

    # 计算各类费用
    eng_total = 0.0
    plant_total = 0.0
    temp_total = 0.0
    if isinstance(summary, dict):
        eng_total = (summary.get("工程措施") or {}).get("total", 0.0)
        plant_total = (summary.get("植物措施") or {}).get("total", 0.0)
        temp_total = (summary.get("临时措施") or {}).get("total", 0.0)

    measures_total = eng_total + plant_total + temp_total
    comp_fee_val = float(comp_fee) if comp_fee is not None else 0.0
    grand_total = measures_total + comp_fee_val

    measure_count = len(registry) if isinstance(registry, list) else 0

    if measure_count > 0:
        scope_text = (
            f"本项目水土保持投资估算包括工程措施费、植物措施费、"
            f"临时措施费及水土保持补偿费四部分，"
            f"共涉及{measure_count}项防治措施。"
        )
    else:
        scope_text = (
            f"本项目水土保持投资估算包括工程措施费、植物措施费、"
            f"临时措施费及水土保持补偿费四部分。"
        )

    p1 = NarrativeParagraph(
        text=scope_text,
        evidence_refs=[
            "field.fact.investment.measures_registry",
        ],
        source_rule_refs=[
            "rule.template_2026.section_9",
        ],
    )

    p2 = NarrativeParagraph(
        text=(
            f"其中，工程措施费 {eng_total:.2f} 万元，"
            f"植物措施费 {plant_total:.2f} 万元，"
            f"临时措施费 {temp_total:.2f} 万元，"
            f"三类措施合计 {measures_total:.2f} 万元。"
            f"水土保持补偿费 {comp_fee_val:.2f} 万元。"
        ),
        evidence_refs=[
            "field.fact.investment.measures_summary",
            "field.derived.investment.compensation_fee_amount",
        ],
        source_rule_refs=[
            "rule.template_2026.section_9",
            "standard.gb_50433_2018.section_9",
        ],
    )

    p3 = NarrativeParagraph(
        text=(
            f"本项目水土保持总投资估算为 {grand_total:.2f} 万元。"
            f"详见水土保持投资估算总表及分项估算表。"
        ),
        evidence_refs=[
            "field.fact.investment.measures_summary",
            "field.derived.investment.compensation_fee_amount",
            "art.table.investment.total_summary",
            "art.table.investment.split_summary",
        ],
        source_rule_refs=[
            "rule.template_2026.section_9",
        ],
    )

    return NarrativeBlock(
        section_id="sec.investment.summary",
        title="投资估算汇总",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2, p3],
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )
