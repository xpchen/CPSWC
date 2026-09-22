"""
sec_7_1_responsibility_range — 7.1 水土流失防治责任范围 narrative template

纯 facts 投影: 防治责任范围 = 永久占地 + 临时占地 + 其他管辖区域。
引用 GB 50433-2018 第 4.4.1 条。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity

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


def render(facts: dict, derived: dict, triggered: set[str],
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    SEC = "sec.soil_loss_prevention.responsibility_range"
    ev = SectionEvidence(SEC, facts, derived, ledger=ledger, context=context)

    total_area = ev.quantity("field.fact.land.total_area")
    perm = ev.quantity("field.fact.land.permanent_area")
    temp = ev.quantity("field.fact.land.temporary_area")

    paragraphs = []

    # 规范要求本身与项目数据无关, 照常陈述
    paragraphs.append(NarrativeParagraph(
        text=("根据《生产建设项目水土保持技术标准》（GB 50433-2018）第 4.4.1 条，"
              "生产建设项目水土流失防治责任范围应包括项目永久征地、临时占地"
              "（含租赁土地）以及其他使用与管辖区域。"),
        evidence_refs=["field.fact.land.total_area"],
        source_rule_refs=["rule.gb_50433_2018.section_4_4_1",
                          "rule.template_2026.section_7"],
        assertion_class=AssertionClass.NORMATIVE_REQUIREMENT,
        paragraph_id="narr.soil_loss_prevention.responsibility_range.basis",
    ))

    # 项目数据段: 临时占地"没填"与"填了 0"不是一回事 ——
    # 原实现 `_num(..., default=0.0)` 会把没填写成"无临时占地"。
    if ev.all_present(total_area, perm, temp):
        temp_clause = (f"临时占地{temp.display()}" if temp.value
                       else "填报临时占地面积为 0")
        paragraphs.append(NarrativeParagraph(
            text=(f"本项目总占地面积{total_area.display()}，"
                  f"其中永久占地{perm.display()}，{temp_clause}，"
                  f"水土流失防治责任范围为{total_area.display()}。"),
            evidence_refs=[v.field_id for v in (total_area, perm, temp)],
            source_rule_refs=["rule.gb_50433_2018.section_4_4_1"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.soil_loss_prevention.responsibility_range.areas",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            total_area, perm, temp,
            lead="占地数据不完整，无法界定防治责任范围",
            source_rule_refs=["rule.gb_50433_2018.section_4_4_1"],
            paragraph_id="narr.soil_loss_prevention.responsibility_range.areas",
        ))

    # 分区段
    bd = ev.items("field.fact.land.county_breakdown", severity=Severity.WARN)
    if bd.is_present and bd.value:
        zone_descs = []
        incomplete = 0
        for rec in bd.value:
            if not isinstance(rec, dict):
                incomplete += 1
                continue
            comp = rec.get("type") or "（分区类型未填）"
            area = rec.get("area")
            if isinstance(area, dict) and area.get("value") is not None:
                area_str = f"{area['value']} {area.get('unit', '')}".strip()
            else:
                area_str = "面积未填"
                incomplete += 1
            zone_descs.append(f"{comp}（{area_str}）")
        text = (f"防治责任范围内共划分{len(bd.value)}个防治分区: "
                f"{'、'.join(zone_descs)}。详见防治责任范围及分区表。")
        if incomplete:
            text += f"其中{incomplete}项分区信息不完整，需补齐后重新统计。"
            ev.add_finding(
                "VALUE_MISSING",
                f"{SEC}: {incomplete} 个防治分区缺类型或面积",
                severity=Severity.BLOCK,
                target_ref="field.fact.land.county_breakdown",
                missing_input_refs=["field.fact.land.county_breakdown"],
                remediation="补齐各分区的类型与面积")
        paragraphs.append(NarrativeParagraph(
            text=text,
            evidence_refs=["field.fact.land.county_breakdown",
                           "art.table.responsibility_range_by_admin_division"],
            source_rule_refs=["rule.template_2026.section_7"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.soil_loss_prevention.responsibility_range.zones",
        ))

    return NarrativeBlock(
        section_id="sec.soil_loss_prevention.responsibility_range",
        title="水土流失防治责任范围",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
        quality_findings=ev.findings,
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
                     ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """7.1.1 分县级行政区防治责任范围"""
    SEC_BY_COUNTY = "sec.soil_loss_prevention.responsibility_range_by_county"
    ev = SectionEvidence(SEC_BY_COUNTY, facts, derived, ledger=ledger,
                         context=context)
    county = ev.raw("field.fact.location.county_list")
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

    if county.is_present:
        p1_text = (f"本项目涉及{county.display()}等行政区域。根据审查要点要求，"
                   f"跨行政区项目应按县级行政区分别列出防治责任范围面积。")
        paragraphs.append(NarrativeParagraph(
            text=p1_text,
            evidence_refs=["field.fact.location.county_list"],
            source_rule_refs=["rule.2023_177.review_dimension_county_breakdown"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.soil_loss_prevention.responsibility_range_by_county.scope",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            county,
            lead="未提供行政区清单，无法按县级行政区分列防治责任范围",
            source_rule_refs=["rule.2023_177.review_dimension_county_breakdown"],
            paragraph_id="narr.soil_loss_prevention.responsibility_range_by_county.scope",
        ))

    if isinstance(breakdown, list) and breakdown:
        # 尝试按 county 分组
        by_county: dict[str, float] = {}
        missing_area = 0
        for rec in breakdown:
            if not isinstance(rec, dict):
                missing_area += 1
                continue
            cty = rec.get("county") or rec.get("zone_id") or "（行政区未填）"
            area = rec.get("area")
            # 面积缺失不按 0 累加 —— 否则某个区会显示成 0.00 hm²
            if isinstance(area, dict) and isinstance(area.get("value"), (int, float)):
                by_county[cty] = by_county.get(cty, 0.0) + float(area["value"])
            elif isinstance(area, (int, float)):
                by_county[cty] = by_county.get(cty, 0.0) + float(area)
            else:
                missing_area += 1

        if by_county:
            parts = [f"{c}：{a:.2f} hm²" for c, a in by_county.items()]
            text = (f"各行政区防治责任范围面积分别为：{'；'.join(parts)}。"
                    f"详见分县级行政区防治责任范围统计表。")
            if missing_area:
                text += f"另有{missing_area}条记录缺面积，未计入上述统计。"
                ev.add_finding(
                    "VALUE_MISSING",
                    f"{SEC_BY_COUNTY}: {missing_area} 条分区记录缺面积, 未计入分县统计",
                    severity=Severity.BLOCK,
                    target_ref="field.fact.land.county_breakdown",
                    missing_input_refs=["field.fact.land.county_breakdown"],
                    remediation="补齐各分区面积后重新统计")
            paragraphs.append(NarrativeParagraph(
                text=text,
                evidence_refs=["field.fact.land.county_breakdown",
                               "art.table.responsibility_range_by_admin_division"],
                source_rule_refs=["rule.template_2026.section_7"],
                assertion_class=AssertionClass.ARITHMETIC,
                paragraph_id="narr.soil_loss_prevention.responsibility_range_by_county.areas",
            ))

    return NarrativeBlock(
        section_id="sec.soil_loss_prevention.responsibility_range_by_county",
        title="分县级行政区防治责任范围",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_BY_COUNTY.template_id,
        template_version=TEMPLATE_SPEC_BY_COUNTY.template_version,
        normative_basis=TEMPLATE_SPEC_BY_COUNTY.normative_basis,
        quality_findings=ev.findings,
    )
