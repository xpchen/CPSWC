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
    template_id="nt.sec_6_2.prediction_result.v2",
    section_id="sec.soil_loss_analysis.prediction_result",
    template_version="v2",
    template_author="cpswc_v1",
    normative_basis=[
        "rule.template_2026.section_6",
        "standard.gb_50433_2018.section_6",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.original_erosion_modulus",
        "field.fact.land.county_breakdown",
        "field.fact.land.total_area",
        "field.fact.schedule.start_time",
        "field.fact.schedule.end_time",
    ],
)


def render_prediction(facts: dict, derived: dict, triggered: set[str],
                      **kwargs) -> NarrativeBlock:
    from cpswc.prediction_engine import compute_prediction

    result = compute_prediction(facts)
    bg_modulus = _v(facts, "field.fact.natural.original_erosion_modulus")
    total_area = _v(facts, "field.fact.land.total_area")

    paragraphs = []

    # P1: Method and scope
    unit_count = len(set(r.zone_id for r in result.zone_results))
    paragraphs.append(NarrativeParagraph(
        text=(
            f"本项目采用类比法进行水土流失预测。"
            f"预测范围为项目防治责任范围（{total_area}），"
            f"共划分{unit_count}个预测单元。"
            f"原地貌土壤侵蚀模数{bg_modulus}。"
        ),
        evidence_refs=[
            "field.fact.natural.original_erosion_modulus",
            "field.fact.land.total_area",
            "field.fact.land.county_breakdown",
        ],
        source_rule_refs=["rule.template_2026.section_6"],
    ))

    # P2: Results summary
    summary_c = result.summary_by_period.get("施工期", {})
    summary_r = result.summary_by_period.get("自然恢复期", {})

    parts = []
    parts.append(
        f"预测结果表明：项目建设期及自然恢复期水土流失总量为 "
        f"{result.total_loss_t:.2f} t，其中新增水土流失量 "
        f"{result.total_new_loss_t:.2f} t。"
    )
    if summary_c:
        parts.append(
            f"施工期新增流失量 {summary_c.get('new_loss_t', 0):.2f} t，"
        )
    if summary_r:
        parts.append(
            f"自然恢复期新增流失量 {summary_r.get('new_loss_t', 0):.2f} t。"
        )

    paragraphs.append(NarrativeParagraph(
        text="".join(parts),
        evidence_refs=[
            "art.table.prediction.result",
            "art.table.prediction.summary",
        ],
        source_rule_refs=["rule.template_2026.section_6"],
    ))

    # P3: Key findings
    # Find the zone with highest new loss
    if result.zone_results:
        max_zone = max(
            (r for r in result.zone_results if r.period == "施工期"),
            key=lambda r: r.new_loss_t,
            default=None,
        )
        if max_zone and max_zone.new_loss_t > 0:
            paragraphs.append(NarrativeParagraph(
                text=(
                    f"施工期水土流失主要发生在{max_zone.zone_type}，"
                    f"新增流失量 {max_zone.new_loss_t:.2f} t，"
                    f"是水土流失防治的重点区域。"
                    f"详见水土流失预测成果表和预测汇总表。"
                ),
                evidence_refs=["art.table.prediction.result"],
                source_rule_refs=["rule.template_2026.section_6"],
            ))

    return NarrativeBlock(
        section_id="sec.soil_loss_analysis.prediction_result",
        title="水土流失预测",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=SPEC_PREDICTION.template_id,
        template_version=SPEC_PREDICTION.template_version,
        normative_basis=SPEC_PREDICTION.normative_basis,
    )
