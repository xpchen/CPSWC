"""
sec_6_soil_loss — 第6章 水土流失分析与预测 narrative templates

两个子节:
  sec.soil_loss_analysis.current_state    — 6.1 水土流失现状
  sec.soil_loss_analysis.prediction_result — 6.2 水土流失预测

消费 facts:
  natural.soil_erosion_type / intensity / original_erosion_modulus / allowable_loss
  prediction.total_loss / new_loss / reducible_loss
  land.total_area
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


# ── sec.soil_loss_analysis.current_state ─────────────────────

SPEC_CURRENT = NarrativeTemplateSpec(
    template_id="nt.sec_6_1.current_state.v1",
    section_id="sec.soil_loss_analysis.current_state",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_6",
        "standard.gb_50433_2018.section_6",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.soil_erosion_type",
        "field.fact.natural.soil_erosion_intensity",
        "field.fact.natural.original_erosion_modulus",
        "field.fact.natural.allowable_loss",
        "field.fact.land.total_area",
    ],
)


def render_current_state(facts: dict, derived: dict, triggered: set[str],
                         **kwargs) -> NarrativeBlock:
    erosion_type = _v(facts, "field.fact.natural.soil_erosion_type")
    intensity = _v(facts, "field.fact.natural.soil_erosion_intensity")
    modulus = _v(facts, "field.fact.natural.original_erosion_modulus")
    allowable = _v(facts, "field.fact.natural.allowable_loss")
    total_area = _v(facts, "field.fact.land.total_area")

    p1 = NarrativeParagraph(
        text=(
            f"项目区现状土壤侵蚀类型以{erosion_type}为主，"
            f"侵蚀强度等级为{intensity}。"
            f"原生土壤侵蚀模数{modulus}，"
            f"容许土壤流失量{allowable}。"
            f"项目总占地{total_area}。"
        ),
        evidence_refs=[
            "field.fact.natural.soil_erosion_type",
            "field.fact.natural.soil_erosion_intensity",
            "field.fact.natural.original_erosion_modulus",
            "field.fact.natural.allowable_loss",
            "field.fact.land.total_area",
        ],
        source_rule_refs=[
            "rule.template_2026.section_6",
            "standard.gb_50433_2018.section_6",
        ],
    )

    return NarrativeBlock(
        section_id="sec.soil_loss_analysis.current_state",
        title="水土流失现状",
        render_status=RenderStatus.FULL,
        paragraphs=[p1],
        variant_id="default",
        template_id=SPEC_CURRENT.template_id,
        template_version=SPEC_CURRENT.template_version,
        normative_basis=SPEC_CURRENT.normative_basis,
    )


# ── sec.soil_loss_analysis.prediction_result ─────────────────

SPEC_PREDICTION = NarrativeTemplateSpec(
    template_id="nt.sec_6_2.prediction_result.v1",
    section_id="sec.soil_loss_analysis.prediction_result",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_6",
        "standard.gb_50433_2018.section_6",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.prediction.total_loss",
        "field.fact.prediction.new_loss",
        "field.fact.prediction.reducible_loss",
    ],
)


def render_prediction(facts: dict, derived: dict, triggered: set[str],
                      **kwargs) -> NarrativeBlock:
    total = _v(facts, "field.fact.prediction.total_loss")
    new_loss = _v(facts, "field.fact.prediction.new_loss")
    reducible = _v(facts, "field.fact.prediction.reducible_loss")

    p1 = NarrativeParagraph(
        text=(
            f"根据类比法预测，项目建设期及自然恢复期水土流失总量为{total}，"
            f"其中新增水土流失量{new_loss}。"
        ),
        evidence_refs=[
            "field.fact.prediction.total_loss",
            "field.fact.prediction.new_loss",
        ],
        source_rule_refs=[
            "rule.template_2026.section_6",
        ],
    )

    p2 = NarrativeParagraph(
        text=(
            f"通过采取工程措施、植物措施和临时措施，"
            f"可治理水土流失量{reducible}，"
            f"防治效果明显。详见水土流失预测成果表。"
        ),
        evidence_refs=[
            "field.fact.prediction.reducible_loss",
            "art.table.soil_loss_prediction",
        ],
        source_rule_refs=[
            "standard.gb_50433_2018.section_6",
        ],
    )

    return NarrativeBlock(
        section_id="sec.soil_loss_analysis.prediction_result",
        title="水土流失预测",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2],
        variant_id="default",
        template_id=SPEC_PREDICTION.template_id,
        template_version=SPEC_PREDICTION.template_version,
        normative_basis=SPEC_PREDICTION.normative_basis,
    )
