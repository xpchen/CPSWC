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
    template_id="nt.sec_6_2.prediction_result.v3",
    section_id="sec.soil_loss_analysis.prediction_result",
    template_version="v3",
    template_author="cpswc_v0.6",
    normative_basis=[
        "rule.template_2026.section_6",
        "standard.gb_50433_2018.section_6",
        "registry.analog_project_v0",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.original_erosion_modulus",
        "field.fact.land.county_breakdown",
        "field.fact.land.total_area",
        "field.fact.schedule.start_time",
        "field.fact.schedule.end_time",
        "field.fact.prediction.analog_project_ref",
    ],
)


def _load_analog_project(analog_id: str) -> dict | None:
    """从 AnalogProjectRegistry_v0 取出指定 id 的类比工程档案; 找不到返回 None."""
    if not analog_id:
        return None
    import yaml
    from pathlib import Path
    reg_path = Path(__file__).resolve().parents[3].parent / "registries" / "AnalogProjectRegistry_v0.yaml"
    if not reg_path.exists():
        return None
    with reg_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for ap in data.get("analog_projects") or []:
        if isinstance(ap, dict) and ap.get("id") == analog_id:
            return ap
    return None


def render_prediction(facts: dict, derived: dict, triggered: set[str],
                      **kwargs) -> NarrativeBlock:
    from cpswc.prediction_engine import compute_prediction

    result = compute_prediction(facts)
    bg_modulus = _v(facts, "field.fact.natural.original_erosion_modulus")
    total_area = _v(facts, "field.fact.land.total_area")

    paragraphs = []

    # P1: Method and scope (含类比工程实名)
    unit_count = len(set(r.zone_id for r in result.zone_results))
    analog_ref = facts.get("field.fact.prediction.analog_project_ref")
    analog = _load_analog_project(analog_ref) if isinstance(analog_ref, str) else None

    if analog:
        analog_name = analog.get("name", analog_ref)
        analog_loc = analog.get("location", "—")
        analog_src = analog.get("citation_source", "—")
        method_clause = (
            f"本项目采用类比分析法进行水土流失预测，"
            f"经筛选确定"
            f"“{analog_name}”（{analog_loc}）"
            f"为类比工程，数据来源：{analog_src}。"
        )
        method_evidence = [
            "field.fact.natural.original_erosion_modulus",
            "field.fact.land.total_area",
            "field.fact.land.county_breakdown",
            "field.fact.prediction.analog_project_ref",
            "registry.analog_project_v0",
        ]
    else:
        method_clause = (
            f"本项目采用类比法进行水土流失预测（类比工程未实名引用，"
            f"待审查前补全 AnalogProjectRegistry 绑定）。"
        )
        method_evidence = [
            "field.fact.natural.original_erosion_modulus",
            "field.fact.land.total_area",
            "field.fact.land.county_breakdown",
        ]

    paragraphs.append(NarrativeParagraph(
        text=(
            f"{method_clause}"
            f"预测范围为项目防治责任范围（{total_area}），"
            f"共划分{unit_count}个预测单元。"
            f"原地貌土壤侵蚀模数{bg_modulus}。"
        ),
        evidence_refs=method_evidence,
        source_rule_refs=["rule.template_2026.section_6"],
    ))

    # P1b: 类比工程 6 维度可比性论证段 (仅在绑定时生成)
    if analog:
        b = analog.get("comparability_baseline") or {}
        comp_parts = []
        if b.get("geographic"):
            comp_parts.append(f"地理位置同属{b['geographic']}")
        if b.get("climate_zone"):
            rain = b.get("annual_rainfall_mm")
            rain_clause = f"多年平均降雨量约 {rain}mm" if rain else ""
            comp_parts.append(f"气候同为{b['climate_zone']}{('，' + rain_clause) if rain_clause else ''}")
        if b.get("soil_type"):
            comp_parts.append(f"土壤同以{b['soil_type']}为主")
        if b.get("vegetation_desc"):
            comp_parts.append(f"植被均为{b['vegetation_desc']}")
        if b.get("terrain_type"):
            comp_parts.append(f"地形地貌相近（类比工程为{b['terrain_type']}）")
        if b.get("soil_conservation_status"):
            comp_parts.append(f"水土保持现状{b['soil_conservation_status']}")
        if comp_parts:
            paragraphs.append(NarrativeParagraph(
                text=(
                    "类比工程与本项目可比性分析："
                    + "；".join(comp_parts)
                    + "。两项目基本相同，具有较强可比性，"
                    "其各扰动地表分区年均土壤侵蚀模数实测值可用于本项目预测取值。"
                ),
                evidence_refs=[
                    "field.fact.prediction.analog_project_ref",
                    "registry.analog_project_v0",
                    "art.table.prediction.analog_comparison",
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
