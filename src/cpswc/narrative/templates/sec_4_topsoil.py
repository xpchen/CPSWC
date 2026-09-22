"""
sec_4_topsoil — 第4章 表土资源保护与利用 narrative template

两个子节:
  sec.topsoil.stripping  — 4.1 表土剥离
  sec.topsoil.balance    — 4.2 表土平衡

消费 facts:
  topsoil.excavation / fill / stripable_area / stripable_volume
  earthwork.excavation / fill
  land.total_area
消费 obligations:
  ob.topsoil.balance_required
  ob.topsoil.reuse_evidence

P0-03 变更 (docs/report_production_plan/03_P0_TASKS.md):
  原实现用 `_num(..., default=0.0)` 取值, 于是表土数据**没填**会走进
  "经现场踏勘，项目用地范围内无可剥离表土" 分支 —— 这是把缺资料写成了
  一次现场踏勘结论, 属于 04 文档第 5 节明令禁止的"已核查不涉及"。

  现在:
    - 缺失 → 缺口段, 明确说是资料缺失, 不提现场踏勘。
    - 明确填 0 → 复述"填报可剥离表土量为 0", 并说明该结论需现场核查支持。
    - "全部用于项目区绿化覆土""全部在项目区内回覆利用，不外运"这类去向断言
      需要方案安排与证据支持, 改走 judgment()。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity


TEMPLATE_SPEC_STRIPPING = NarrativeTemplateSpec(
    template_id="nt.sec_4_1.topsoil_stripping.v1",
    section_id="sec.topsoil.stripping",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_4",
        "standard.gb_50433_2018.section_4",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.topsoil.stripable_area",
        "field.fact.topsoil.stripable_volume",
        "field.fact.land.total_area",
    ],
)

TEMPLATE_SPEC_BALANCE = NarrativeTemplateSpec(
    template_id="nt.sec_4_2.topsoil_balance.v1",
    section_id="sec.topsoil.balance",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_4",
        "standard.gb_50433_2018.section_4",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.topsoil.excavation",
        "field.fact.topsoil.fill",
        "field.fact.topsoil.stripable_volume",
    ],
)


# ── sec.topsoil.stripping (4.1 表土剥离) ────────────────────

SEC_STRIP = "sec.topsoil.stripping"
SEC_BALANCE = "sec.topsoil.balance"


def render_stripping(facts: dict, derived: dict, triggered: set[str],
                     ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """渲染 4.1 表土剥离"""
    ev = SectionEvidence(SEC_STRIP, facts, derived, ledger=ledger, context=context)

    total_area = ev.quantity("field.fact.land.total_area")
    strip_area = ev.quantity("field.fact.topsoil.stripable_area")
    strip_vol = ev.quantity("field.fact.topsoil.stripable_volume")

    paragraphs: list[NarrativeParagraph] = []

    if not ev.all_present(strip_area, strip_vol):
        # 资料缺失。**不能**写成"经现场踏勘无可剥离表土"。
        paragraphs.append(ev.gap_paragraph(
            total_area, strip_area, strip_vol,
            lead="表土剥离数据不完整，无法说明剥离范围与剥离量",
            source_rule_refs=["rule.template_2026.section_4",
                              "standard.gb_50433_2018.section_4"],
            paragraph_id="narr.topsoil.stripping.quantities",
        ))
        return NarrativeBlock(
            section_id=SEC_STRIP,
            title="表土剥离",
            render_status=RenderStatus.FULL,
            paragraphs=paragraphs,
            variant_id="default",
            template_id=TEMPLATE_SPEC_STRIPPING.template_id,
            template_version=TEMPLATE_SPEC_STRIPPING.template_version,
            normative_basis=TEMPLATE_SPEC_STRIPPING.normative_basis,
            quality_findings=ev.findings,
        )

    if not strip_area.value and not strip_vol.value:
        # 明确填 0: 可以复述填报值, 但"无可剥离表土"是核查结论, 需要支持。
        area_clause = (f"项目总占地面积{total_area.display()}。"
                       if total_area.is_present else "")
        paragraphs.append(NarrativeParagraph(
            text=(f"{area_clause}本项目填报的可剥离表土面积与表土量均为 0。"),
            evidence_refs=["field.fact.land.total_area",
                           "field.fact.topsoil.stripable_area",
                           "field.fact.topsoil.stripable_volume"],
            source_rule_refs=["rule.template_2026.section_4"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.topsoil.stripping.quantities",
        ))
        paragraphs.append(ev.judgment(
            "经现场踏勘，项目用地范围内无可剥离表土，本方案不涉及表土剥离。",
            target_ref=SEC_STRIP,
            pending_text=(
                "填报值为 0 只说明未填报可剥离表土。项目区是否确实无可剥离表土，"
                "须有土壤调查或现场踏勘记录支持；相应核查记录形成前，"
                "本节不作“无可剥离表土”的结论。"),
            evidence_refs=["field.fact.topsoil.stripable_area",
                           "field.fact.topsoil.stripable_volume"],
            source_rule_refs=["standard.gb_50433_2018.section_4"],
            paragraph_id="narr.topsoil.stripping.no_topsoil",
            remediation="补充表土调查点位、厚度与质量记录后录入核查结论",
        ))
    else:
        if total_area.is_present and total_area.value:
            pct = f"，占总占地面积的{strip_area.value / total_area.value * 100:.0f}%"
        else:
            pct = ""
        paragraphs.append(NarrativeParagraph(
            text=(f"项目总占地面积{total_area.display() if total_area.is_present else '（缺）'}，"
                  f"可剥离表土区域面积{strip_area.display()}{pct}。"
                  f"可剥离表土量为{strip_vol.display()}。"),
            evidence_refs=["field.fact.land.total_area",
                           "field.fact.topsoil.stripable_area",
                           "field.fact.topsoil.stripable_volume"],
            source_rule_refs=["rule.template_2026.section_4",
                              "standard.gb_50433_2018.section_4"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.topsoil.stripping.quantities",
        ))
        paragraphs.append(NarrativeParagraph(
            text=("表土剥离应在场地平整前进行，剥离的表土集中堆放于临时堆土区，"
                  "采取覆盖与临时排水措施，防止堆存期间产生水土流失。"),
            evidence_refs=["field.fact.topsoil.stripable_volume"],
            source_rule_refs=["standard.gb_50433_2018.section_4"],
            assertion_class=AssertionClass.NORMATIVE_REQUIREMENT,
            paragraph_id="narr.topsoil.stripping.requirements",
        ))

    return NarrativeBlock(
        section_id=SEC_STRIP,
        title="表土剥离",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_STRIPPING.template_id,
        template_version=TEMPLATE_SPEC_STRIPPING.template_version,
        normative_basis=TEMPLATE_SPEC_STRIPPING.normative_basis,
        quality_findings=ev.findings,
    )


# ── sec.topsoil.balance (4.2 表土平衡) ──────────────────────

def render_balance(facts: dict, derived: dict, triggered: set[str],
                   ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """渲染 4.2 表土平衡"""
    ev = SectionEvidence(SEC_BALANCE, facts, derived, ledger=ledger, context=context)

    strip_vol = ev.quantity("field.fact.topsoil.stripable_volume")
    ts_exc = ev.quantity("field.fact.topsoil.excavation")
    ts_fill = ev.quantity("field.fact.topsoil.fill")

    paragraphs: list[NarrativeParagraph] = []
    values = [strip_vol, ts_exc, ts_fill]

    if not ev.all_present(*values):
        paragraphs.append(ev.gap_paragraph(
            *values,
            lead="表土平衡数据不完整，无法计算表土挖填差额",
            source_rule_refs=["rule.template_2026.section_4"],
            paragraph_id="narr.topsoil.balance.quantities",
        ))
        return NarrativeBlock(
            section_id=SEC_BALANCE,
            title="表土平衡",
            render_status=RenderStatus.FULL,
            paragraphs=paragraphs,
            variant_id="default",
            template_id=TEMPLATE_SPEC_BALANCE.template_id,
            template_version=TEMPLATE_SPEC_BALANCE.template_version,
            normative_basis=TEMPLATE_SPEC_BALANCE.normative_basis,
            quality_findings=ev.findings,
        )

    paragraphs.append(NarrativeParagraph(
        text=(f"可剥离表土量{strip_vol.display()}，"
              f"表土挖方{ts_exc.display()}，回覆利用量{ts_fill.display()}。"),
        evidence_refs=[v.field_id for v in values],
        source_rule_refs=["rule.template_2026.section_4"],
        assertion_class=AssertionClass.FACT_RESTATEMENT,
        paragraph_id="narr.topsoil.balance.quantities",
    ))

    surplus = ts_exc.value - ts_fill.value
    unit = ts_exc.unit or ts_fill.unit
    if surplus > 0:
        arithmetic = (f"表土挖方大于回覆量，差额为 {surplus:.2f} {unit}，"
                      f"该部分表土的去向需在方案中明确。")
    elif surplus < 0:
        arithmetic = (f"回覆需求大于表土挖方，缺口为 {abs(surplus):.2f} {unit}，"
                      f"不足部分的来源需在方案中明确。")
    else:
        arithmetic = "表土挖方与回覆量相等，差额为 0。"
    paragraphs.append(NarrativeParagraph(
        text=arithmetic,
        evidence_refs=["field.fact.topsoil.excavation",
                       "field.fact.topsoil.fill"],
        source_rule_refs=["rule.template_2026.section_4"],
        assertion_class=AssertionClass.ARITHMETIC,
        paragraph_id="narr.topsoil.balance.difference",
    ))

    if "ob.topsoil.reuse_evidence" in triggered:
        paragraphs.append(NarrativeParagraph(
            text=("本项目已触发表土利用证明义务，须提供剥离表土的去向证明材料。"),
            evidence_refs=["ob.topsoil.reuse_evidence"],
            source_rule_refs=["standard.gb_50433_2018.section_4"],
            assertion_class=AssertionClass.NORMATIVE_REQUIREMENT,
            paragraph_id="narr.topsoil.balance.reuse_obligation",
        ))

    # 去向结论: "全部用于绿化覆土""不外运"都是方案安排 + 落实证据的问题
    paragraphs.append(ev.judgment(
        "剥离表土全部在项目区内回覆利用于绿化覆土，不外运，表土平衡方案可行。",
        target_ref=SEC_BALANCE,
        pending_text=(
            "剥离表土的最终去向（场内回覆、外运利用或外购补充）及其落实情况，"
            "须由水土保持工程师结合绿化设计与去向证明材料复核确认；"
            "复核记录形成前，本节不作表土去向与平衡可行性结论。"),
        evidence_refs=["field.fact.topsoil.excavation",
                       "field.fact.topsoil.fill", SEC_BALANCE],
        source_rule_refs=["standard.gb_50433_2018.section_4"],
        paragraph_id="narr.topsoil.balance.conclusion",
        remediation="核对绿化覆土需求与表土去向证明后录入复核记录",
    ))

    return NarrativeBlock(
        section_id=SEC_BALANCE,
        title="表土平衡",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_BALANCE.template_id,
        template_version=TEMPLATE_SPEC_BALANCE.template_version,
        normative_basis=TEMPLATE_SPEC_BALANCE.normative_basis,
        quality_findings=ev.findings,
    )
