"""
sec_9_1_investment_summary — 9.1 投资估算汇总 narrative template

消费 facts:
  field.fact.investment.measures_summary  — {费类: {new, existing, total}}
  field.fact.investment.measures_registry — list of measure records
  field.derived.investment.compensation_fee_amount
消费 derived:
  field.derived.investment.compensation_fee_amount

B 批 P0-04 改造 (任务 B-T6):
  原实现用 `(summary.get("工程措施") or {}).get("total", 0.0)` 逐类取值 ——
  分项缺失当 0 累加, 于是"合计"永远算得出来, 而且看不出少了哪一类。
  与 sec_0_overview 的同类问题同源。现在缺分项就如实说缺哪一类, 不参与累加。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity


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
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """渲染 9.1 投资估算汇总"""
    SEC = "sec.investment.summary"
    ev = SectionEvidence(SEC, facts, derived, ledger=ledger, context=context)

    summary = ev.raw("field.fact.investment.measures_summary")
    registry = ev.items("field.fact.investment.measures_registry",
                        severity=Severity.WARN)
    comp_fee = ev.raw("field.derived.investment.compensation_fee_amount")

    _CATEGORIES = ("工程措施", "植物措施", "临时措施")
    totals: dict[str, float] = {}
    missing_categories: list[str] = []
    if summary.is_present and isinstance(summary.value, dict):
        for cat in _CATEGORIES:
            entry = summary.value.get(cat)
            amount = entry.get("total") if isinstance(entry, dict) else None
            if isinstance(amount, (int, float)) and not isinstance(amount, bool):
                totals[cat] = float(amount)
            else:
                missing_categories.append(cat)
    else:
        missing_categories = list(_CATEGORIES)

    measure_count = len(registry.value) if (
        registry.is_present and isinstance(registry.value, list)) else None

    paragraphs: list[NarrativeParagraph] = []

    # 段 1: 估算范围
    scope = ("本项目水土保持投资估算包括工程措施费、植物措施费、"
             "临时措施费及水土保持补偿费四部分。")
    if measure_count:
        scope += f"共涉及{measure_count}项防治措施。"
    elif measure_count == 0:
        scope += "措施清单为空，尚未录入任何防治措施。"
    else:
        scope += "措施清单未提供。"
    paragraphs.append(NarrativeParagraph(
        text=scope,
        evidence_refs=["field.fact.investment.measures_registry"],
        source_rule_refs=["rule.template_2026.section_9"],
        assertion_class=AssertionClass.FACT_RESTATEMENT,
        paragraph_id="narr.investment.summary.scope",
    ))

    # 段 2: 分项金额 —— 缺分项不按 0 累加
    if missing_categories:
        ev.add_finding(
            "VALUE_MISSING",
            f"{SEC}: {len(missing_categories)} 类措施投资缺合计金额"
            f"（{'、'.join(missing_categories)}）, 不得按 0 计入合计",
            severity=Severity.BLOCK,
            target_ref="field.fact.investment.measures_summary",
            missing_input_refs=["field.fact.investment.measures_summary"],
            remediation="补齐各类措施的合计金额后重算",
        )
        listed = "；".join(f"{c} {totals[c]:.2f} 万元" for c in _CATEGORIES
                          if c in totals)
        paragraphs.append(NarrativeParagraph(
            text=(f"已提供金额的措施类别："
                  f"{listed if listed else '无'}。"
                  f"尚缺{len(missing_categories)}类措施的合计金额"
                  f"（{'、'.join(missing_categories)}），"
                  f"因此本轮不给出措施投资合计与水土保持总投资。"),
            evidence_refs=["field.fact.investment.measures_summary"],
            source_rule_refs=["rule.template_2026.section_9"],
            assertion_class=AssertionClass.GAP_STATEMENT,
            paragraph_id="narr.investment.summary.breakdown",
        ))
    else:
        measures_total = sum(totals.values())
        paragraphs.append(NarrativeParagraph(
            text=("其中，"
                  + "，".join(f"{c}费 {totals[c]:.2f} 万元" for c in _CATEGORIES)
                  + f"，三类措施合计 {measures_total:.2f} 万元。"),
            evidence_refs=["field.fact.investment.measures_summary"],
            source_rule_refs=["rule.template_2026.section_9",
                              "standard.gb_50433_2018.section_9"],
            assertion_class=AssertionClass.ARITHMETIC,
            paragraph_id="narr.investment.summary.breakdown",
        ))

        # 段 3: 总投资 —— 补偿费缺失时同样不给总数
        if comp_fee.is_present:
            grand = measures_total + float(comp_fee.value)
            paragraphs.append(NarrativeParagraph(
                text=(f"水土保持补偿费 {float(comp_fee.value):.2f} 万元，"
                      f"本项目水土保持总投资估算为 {grand:.2f} 万元。"
                      f"详见水土保持投资估算总表及分项估算表。"),
                evidence_refs=["field.fact.investment.measures_summary",
                               "field.derived.investment.compensation_fee_amount",
                               "art.table.investment.total_summary",
                               "art.table.investment.split_summary"],
                source_rule_refs=["rule.template_2026.section_9"],
                assertion_class=AssertionClass.ARITHMETIC,
                paragraph_id="narr.investment.summary.grand_total",
            ))
        else:
            paragraphs.append(ev.gap_paragraph(
                comp_fee,
                lead="水土保持补偿费无有效结果，无法给出水土保持总投资",
                source_rule_refs=["rule.template_2026.section_9"],
                extra_refs=["cal.compensation.fee"],
                paragraph_id="narr.investment.summary.grand_total",
            ))

    return NarrativeBlock(
        section_id=SEC,
        title="投资估算汇总",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
        quality_findings=ev.findings,
    )
