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
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        unit = v.get("unit", "")
        return f"{v['value']} {unit}".strip()
    if isinstance(v, list):
        return "、".join(str(x) for x in v) if v else default
    return str(v)


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
                   **kwargs) -> NarrativeBlock:
    province = _v(facts, "field.fact.location.province_list")
    prefecture = _v(facts, "field.fact.location.prefecture_list")
    climate = _v(facts, "field.fact.natural.climate_type")
    landform = _v(facts, "field.fact.natural.landform_type")
    erosion_type = _v(facts, "field.fact.natural.soil_erosion_type")
    intensity = _v(facts, "field.fact.natural.soil_erosion_intensity")
    modulus = _v(facts, "field.fact.natural.original_erosion_modulus")
    allowable = _v(facts, "field.fact.natural.allowable_loss")

    p1 = NarrativeParagraph(
        text=(
            f"项目区位于{province}{prefecture}，属{climate}，地貌类型为{landform}。"
            f"区域土壤侵蚀类型以{erosion_type}为主，"
            f"现状土壤侵蚀强度为{intensity}，"
            f"原生侵蚀模数{modulus}，容许土壤流失量{allowable}。"
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
                  **kwargs) -> NarrativeBlock:
    zoning = _v(facts, "field.fact.natural.water_soil_zoning")
    key_areas = facts.get("field.fact.natural.key_prevention_treatment_areas")

    text_parts = [f"根据全国水土保持区划，项目区属{zoning}。"]

    if isinstance(key_areas, list) and key_areas:
        text_parts.append(
            f"项目区涉及国家级水土流失重点预防区或重点治理区："
            f"{'、'.join(str(a) for a in key_areas)}。"
        )
    else:
        text_parts.append(
            "项目区不涉及国家级水土流失重点预防区或重点治理区。"
        )

    p1 = NarrativeParagraph(
        text="".join(text_parts),
        evidence_refs=[
            "field.fact.natural.water_soil_zoning",
            "field.fact.natural.key_prevention_treatment_areas",
        ],
        source_rule_refs=[
            "rule.template_2026.section_2",
            "standard.gb_50433_2018.section_2",
        ],
    )

    return NarrativeBlock(
        section_id="sec.project_overview.water_soil_zoning",
        title="水土保持区划",
        render_status=RenderStatus.FULL,
        paragraphs=[p1],
        variant_id="default",
        template_id=SPEC_ZONING.template_id,
        template_version=SPEC_ZONING.template_version,
        normative_basis=SPEC_ZONING.normative_basis,
    )
