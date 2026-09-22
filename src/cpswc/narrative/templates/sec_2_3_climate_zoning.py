"""
sec_2_3_climate_zoning — 2.x 气候与自然概况 / 水土保持区划 narrative templates

两个子节:
  sec.project_overview.climate          — 气候与自然概况
  sec.project_overview.water_soil_zoning — 水土保持区划

消费 facts: natural.* (climate_type, landform_type, soil_erosion_*, water_soil_zoning, original_erosion_modulus, allowable_loss)
消费 facts: location.* (province, prefecture)
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)


# ── sec.project_overview.climate ─────────────────────────────

SPEC_CLIMATE = NarrativeTemplateSpec(
    template_id="nt.sec_2_x.climate.v1",
    section_id="sec.project_overview.climate",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=["rule.template_2026.section_2"],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.climate_type",
        "field.fact.natural.landform_type",
        "field.fact.natural.soil_erosion_type",
        "field.fact.natural.soil_erosion_intensity",
        "field.fact.natural.original_erosion_modulus",
        "field.fact.natural.allowable_loss",
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
    ],
)


def render_climate(facts: dict, derived: dict, triggered: set[str],
                   ledger=None, context=None, **kwargs) -> NarrativeBlock:
    from cpswc.narrative.evidence import SectionEvidence

    ev = SectionEvidence("sec.project_overview.climate", facts, derived,
                         ledger=ledger, context=context)
    province = ev.text("field.fact.location.province_list")
    prefecture = ev.text("field.fact.location.prefecture_list")
    climate = ev.text("field.fact.natural.climate_type")
    landform = ev.text("field.fact.natural.landform_type")
    erosion_type = ev.text("field.fact.natural.soil_erosion_type")
    intensity = ev.text("field.fact.natural.soil_erosion_intensity")
    modulus = ev.quantity("field.fact.natural.original_erosion_modulus")
    allowable = ev.quantity("field.fact.natural.allowable_loss")

    values = [province, prefecture, climate, landform,
              erosion_type, intensity, modulus, allowable]
    if not ev.all_present(*values):
        p1 = ev.gap_paragraph(
            *values,
            lead="项目区自然概况资料不完整",
            source_rule_refs=["rule.template_2026.section_2"],
            paragraph_id="narr.project_overview.climate.overview")
    else:
        p1 = NarrativeParagraph(
        assertion_class=AssertionClass.FACT_RESTATEMENT,
        paragraph_id="narr.project_overview.climate.overview",
        text=(
            f"项目区位于{province.display()}{prefecture.display()}，"
            f"属{climate.display()}，地貌类型为{landform.display()}。"
            f"区域土壤侵蚀类型以{erosion_type.display()}为主，"
            f"现状土壤侵蚀强度为{intensity.display()}，"
            f"原生侵蚀模数{modulus.display()}，"
            f"容许土壤流失量{allowable.display()}。"
        ),
        evidence_refs=[
            "field.fact.location.province_list",
            "field.fact.location.prefecture_list",
            "field.fact.natural.climate_type",
            "field.fact.natural.landform_type",
            "field.fact.natural.soil_erosion_type",
            "field.fact.natural.soil_erosion_intensity",
            "field.fact.natural.original_erosion_modulus",
            "field.fact.natural.allowable_loss",
        ],
        source_rule_refs=["rule.template_2026.section_2"],
    )

    return NarrativeBlock(
        section_id="sec.project_overview.climate",
        title="气候与自然概况",
        render_status=RenderStatus.FULL,
        paragraphs=[p1],
        variant_id="default",
        template_id=SPEC_CLIMATE.template_id,
        template_version=SPEC_CLIMATE.template_version,
        normative_basis=SPEC_CLIMATE.normative_basis,
        quality_findings=ev.findings,
    )


# ── sec.project_overview.water_soil_zoning ───────────────────

SPEC_ZONING = NarrativeTemplateSpec(
    template_id="nt.sec_2_x.water_soil_zoning.v1",
    section_id="sec.project_overview.water_soil_zoning",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_2",
        "standard.gb_50433_2018.section_2",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.water_soil_zoning",
        "field.fact.natural.key_prevention_treatment_areas",
    ],
)


def render_zoning(facts: dict, derived: dict, triggered: set[str],
                  ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """水土保持区划。

    P0-03: 原实现用 `isinstance(key_areas, list) and key_areas` 判断,
    于是字段**没填**和填了空清单都会输出"项目区不涉及国家级水土流失重点
    预防区或重点治理区"。这与 sec_2_5 的缺陷同源 (04 文档第 5 节:
    空 list / 字典查不到 不构成"已核查不涉及"的充分支持)。
    """
    from cpswc.narrative.evidence import SectionEvidence
    from cpswc.report_quality import Severity, Stage

    SEC = "sec.project_overview.water_soil_zoning"
    ev = SectionEvidence(SEC, facts, derived, ledger=ledger, context=context)

    zoning = ev.text("field.fact.natural.water_soil_zoning")
    key_areas = ev.items("field.fact.natural.key_prevention_treatment_areas")

    paragraphs = []
    if zoning.is_present:
        paragraphs.append(NarrativeParagraph(
            text=f"根据全国水土保持区划，项目区属{zoning.display()}。",
            evidence_refs=["field.fact.natural.water_soil_zoning"],
            source_rule_refs=["rule.template_2026.section_2",
                              "standard.gb_50433_2018.section_2"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.project_overview.water_soil_zoning.zoning",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            zoning,
            lead="未提供全国水土保持区划归属",
            source_rule_refs=["rule.template_2026.section_2"],
            paragraph_id="narr.project_overview.water_soil_zoning.zoning",
        ))

    if not key_areas.is_present:
        paragraphs.append(ev.gap_paragraph(
            key_areas,
            lead="未提供国家级水土流失重点预防区、重点治理区的排查结果",
            source_rule_refs=["rule.template_2026.section_2"],
            paragraph_id="narr.project_overview.water_soil_zoning.key_areas",
        ))
    elif key_areas.value:
        paragraphs.append(NarrativeParagraph(
            text=(f"项目区涉及国家级水土流失重点预防区或重点治理区："
                  f"{'、'.join(str(a) for a in key_areas.value)}。"),
            evidence_refs=["field.fact.natural.key_prevention_treatment_areas"],
            source_rule_refs=["rule.template_2026.section_2"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.project_overview.water_soil_zoning.key_areas",
        ))
    else:
        para = ev.judgment(
            "经核查，项目区不涉及国家级水土流失重点预防区或重点治理区。",
            target_ref=f"{SEC}.key_areas",
            pending_text=("本项目填报的国家级水土流失重点预防区、重点治理区清单为空。"
                          "是否确实不涉及，须核对相应区划文件并留下核查记录；"
                          "核查记录形成前，本节不作“不涉及”的结论。"),
            evidence_refs=["field.fact.natural.key_prevention_treatment_areas"],
            source_rule_refs=["rule.template_2026.section_2"],
            paragraph_id="narr.project_overview.water_soil_zoning.key_areas",
            remediation="核对国家级水土流失重点防治区划文件并记录核查结论",
        )
        if para.assertion_class is not AssertionClass.PROJECT_JUDGMENT:
            ev.add_finding(
                "SOURCE_UNVERIFIED",
                f"{SEC}: 空清单不构成“不涉及国家级重点防治区”的证据",
                severity=Severity.BLOCK, target_ref=SEC,
                remediation="核对区划文件并记录核查结论", stage=Stage.INPUT)
        paragraphs.append(para)

    return NarrativeBlock(
        section_id="sec.project_overview.water_soil_zoning",
        title="水土保持区划",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=SPEC_ZONING.template_id,
        template_version=SPEC_ZONING.template_version,
        normative_basis=SPEC_ZONING.normative_basis,
        quality_findings=ev.findings,
    )
