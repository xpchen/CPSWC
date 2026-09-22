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

P0-03 变更 (03 文档 P0-03 第 8 条: 汇总结论不能绕过下游缺口):
  综合说明是全册的第一页, 也是最容易"替下游把话说满"的地方。原实现:
    - 用 `_v(..., default="—")` 把缺失写成短横线, 段落照样成句;
    - `measures_total` 用 `cat_data.get("total", 0.0)` 缺项当 0 累加, 于是
      投资合计永远算得出来, 即使措施汇总根本没提供;
    - 末段用**目标值**写"方案实施后…各项指标均满足相应防治标准要求"。

  现在: 缺失如实标注; 投资合计只在措施汇总可读时计算; 末段只复述目标值,
  达标与否由效益分析按效果计算判定 (验收 N04)。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity


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


SECTION_ID = "sec.overview"


def render(facts: dict, derived: dict, triggered: set[str],
           snapshot: dict | None = None, ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """渲染 综合说明 — 报告首页摘要"""
    ev = SectionEvidence(SECTION_ID, facts, derived, ledger=ledger, context=context)
    paragraphs: list[NarrativeParagraph] = []

    # ── 段 1: 项目概况 ──
    name = ev.text("field.fact.project.name")
    nature = ev.text("field.fact.project.nature")
    province = ev.text("field.fact.location.province_list")
    prefecture = ev.text("field.fact.location.prefecture_list")
    total_inv = ev.quantity("field.fact.investment.total_investment")
    civil_inv = ev.quantity("field.fact.investment.civil_investment")
    start = ev.text("field.fact.schedule.start_time")
    end = ev.text("field.fact.schedule.end_time")
    total_area = ev.quantity("field.fact.land.total_area")
    perm_area = ev.quantity("field.fact.land.permanent_area")
    temp_area = ev.quantity("field.fact.land.temporary_area")

    g1 = [name, nature, province, prefecture, total_inv, civil_inv,
          start, end, total_area, perm_area, temp_area]
    if ev.all_present(*g1):
        paragraphs.append(NarrativeParagraph(
            text=(f"{name.display()}为{nature.display()}项目，"
                  f"位于{province.display()}{prefecture.display()}。"
                  f"项目总投资{total_inv.display()}，其中土建投资{civil_inv.display()}。"
                  f"施工期{start.display()}至{end.display()}。"
                  f"总占地面积{total_area.display()}，"
                  f"其中永久占地{perm_area.display()}，临时占地{temp_area.display()}。"),
            evidence_refs=[v.field_id for v in g1],
            source_rule_refs=["rule.template_2026.section_1"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.overview.project_basic",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            *g1,
            lead="项目基本情况资料不完整，综合说明无法给出完整概述",
            source_rule_refs=["rule.template_2026.section_1"],
            paragraph_id="narr.overview.project_basic",
        ))

    # ── 段 2: 土石方 + 表土 + 流失预测 ──
    zoning = ev.text("field.fact.natural.water_soil_zoning")
    exc = ev.quantity("field.fact.earthwork.excavation")
    fill = ev.quantity("field.fact.earthwork.fill")
    spoil = ev.quantity("field.fact.earthwork.spoil")
    topsoil = ev.quantity("field.fact.topsoil.stripable_volume")
    new_loss = ev.quantity("field.fact.prediction.new_loss")
    reducible = ev.quantity("field.fact.prediction.reducible_loss")

    g2 = [zoning, exc, fill, spoil, topsoil, new_loss, reducible]
    if ev.all_present(*g2):
        paragraphs.append(NarrativeParagraph(
            text=(f"项目区属{zoning.display()}。"
                  f"挖方总量{exc.display()}，填方总量{fill.display()}，"
                  f"弃方{spoil.display()}。可剥离表土{topsoil.display()}。"
                  f"施工期预测新增水土流失量{new_loss.display()}，"
                  f"其中可治理量{reducible.display()}。"),
            evidence_refs=[v.field_id for v in g2],
            source_rule_refs=["rule.template_2026.section_1",
                              "standard.gb_50433_2018.section_1"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.overview.quantities",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            *g2,
            lead="土石方、表土与流失预测数据不完整",
            source_rule_refs=["rule.template_2026.section_1"],
            paragraph_id="narr.overview.quantities",
        ))

    # ── 段 3: 投资估算 ──
    # 措施汇总缺项不再当 0 累加: 分项缺失会让合计看起来"算出来了"但偏小。
    summary = ev.raw("field.fact.investment.measures_summary")
    comp_fee = ev.raw("field.derived.investment.compensation_fee_amount")
    measures_total, missing_cats = _sum_measures(summary)

    if measures_total is not None and comp_fee.is_present:
        grand = measures_total + float(comp_fee.value)
        text = (f"水土保持措施投资合计 {measures_total:.2f} 万元，"
                f"水土保持补偿费 {float(comp_fee.value):.2f} 万元，"
                f"水土保持总投资 {grand:.2f} 万元。")
        if missing_cats:
            text += (f"其中{len(missing_cats)}个分项未提供合计金额"
                     f"（{'、'.join(missing_cats)}），上述合计尚不完整。")
            ev.add_finding(
                "VALUE_MISSING",
                f"{SECTION_ID}: 措施投资有 {len(missing_cats)} 个分项缺合计金额",
                severity=Severity.BLOCK,
                target_ref="field.fact.investment.measures_summary",
                remediation="补齐各分项合计金额后重算",
            )
        paragraphs.append(NarrativeParagraph(
            text=text,
            evidence_refs=["field.fact.investment.measures_summary",
                           "field.derived.investment.compensation_fee_amount"],
            source_rule_refs=["rule.template_2026.section_1"],
            assertion_class=AssertionClass.ARITHMETIC,
            paragraph_id="narr.overview.investment",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            summary, comp_fee,
            lead="水土保持投资估算尚不完整，无法给出总投资",
            source_rule_refs=["rule.template_2026.section_1"],
            paragraph_id="narr.overview.investment",
        ))

    # ── 段 4: 防治目标 ──
    # 只复述目标值。达标结论属效益分析, 且须有独立的效果计算 (验收 N04)。
    weighted = ev.raw("field.derived.target.weighted_comprehensive_target",
                      severity=Severity.WARN)
    if weighted.is_present and isinstance(weighted.value, dict):
        w = weighted.value
        items = []
        for key, label, unit in (
            ("control_degree", "水土流失治理度", "%"),
            ("soil_loss_control_ratio", "土壤流失控制比", ""),
            ("spoil_protection_rate", "渣土防护率", "%"),
            ("vegetation_restoration_rate", "林草植被恢复率", "%"),
        ):
            if w.get(key) is not None:
                items.append(f"{label}{w[key]}{unit}")
        if items:
            paragraphs.append(NarrativeParagraph(
                text=(f"本项目设计水平年防治指标目标值为：{'、'.join(items)}。"
                      f"上述为目标要求，实施后实际可达到的效果见防治效益分析章节。"),
                evidence_refs=["field.derived.target.weighted_comprehensive_target"],
                source_rule_refs=["standard.gb_50433_2018.section_1"],
                assertion_class=AssertionClass.TARGET_VALUE,
                paragraph_id="narr.overview.targets",
            ))

    # ── 段 5: 未决事项 ── 综合说明不替下游把话说满
    unknown_obs = list((snapshot or {}).get("unknown_obligations") or [])
    if unknown_obs:
        paragraphs.append(NarrativeParagraph(
            text=(f"另有{len(unknown_obs)}项水土保持义务因输入资料不足，"
                  f"本轮无法判定是否适用，相应内容尚未定稿。"),
            evidence_refs=sorted(unknown_obs)[:10],
            source_rule_refs=["rule.template_2026.section_1"],
            assertion_class=AssertionClass.GAP_STATEMENT,
            paragraph_id="narr.overview.open_items",
        ))

    return NarrativeBlock(
        section_id=SECTION_ID,
        title="综合说明",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
        quality_findings=ev.findings,
    )


def _sum_measures(summary) -> tuple[float | None, list[str]]:
    """
    累加措施投资分项。

    返回 (合计, 缺合计金额的分项名)。summary 不可读时返回 (None, [])——
    **不返回 0.0**: 0 会被下游当成"合计为零"而不是"没有数据"。
    """
    if not summary.is_present or not isinstance(summary.value, dict):
        return None, []
    total = 0.0
    missing: list[str] = []
    for cat, data in summary.value.items():
        if isinstance(data, dict) and isinstance(data.get("total"), (int, float)):
            total += float(data["total"])
        else:
            missing.append(str(cat))
    return total, missing
