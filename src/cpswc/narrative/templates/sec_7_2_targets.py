"""
sec_7_2_targets — 7.2 防治目标 narrative template

消费 cal.target.weighted_comprehensive 的输出, 把六率目标值解释为正文。
两个 variant:
  - single_level:  单一等级, 直接引用目标值
  - multi_level:   多等级加权, 引用加权综合结果 + 解释加权逻辑
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)

TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_7_2.targets.v1",
    section_id="sec.soil_loss_prevention.targets",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.gb_t_50434_2018.chapter_4",
        "rule.template_2026.section_7_2",
    ],
    supported_variants=["single_level", "multi_level"],
    input_fields=[
        "field.fact.prevention.control_standard_level",
        "field.fact.prevention.control_standard_level_breakdown",
        "field.fact.natural.water_soil_zoning",
        "field.derived.target.weighted_comprehensive_target",
    ],
)

_INDICATOR_LABELS = {
    "control_degree": "水土流失治理度",
    "soil_loss_control_ratio": "土壤流失控制比",
    "spoil_protection_rate": "渣土防护率",
    "topsoil_protection_rate": "表土保护率",
    "vegetation_restoration_rate": "林草植被恢复率",
    "vegetation_coverage_rate": "林草覆盖率",
}

_INDICATOR_UNITS = {
    "control_degree": "%",
    "soil_loss_control_ratio": "",
    "spoil_protection_rate": "%",
    "topsoil_protection_rate": "%",
    "vegetation_restoration_rate": "%",
    "vegetation_coverage_rate": "%",
}


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        unit = v.get("unit", "")
        return f"{v['value']} {unit}".strip()
    if isinstance(v, list):
        return str(len(v))
    return str(v)


def _select_variant(facts: dict, derived: dict) -> str:
    breakdown = facts.get("field.fact.prevention.control_standard_level_breakdown")
    if isinstance(breakdown, list) and len(breakdown) >= 2:
        return "multi_level"
    return "single_level"


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    variant = _select_variant(facts, derived)
    level = _v(facts, "field.fact.prevention.control_standard_level")
    zoning = _v(facts, "field.fact.natural.water_soil_zoning")
    wt = derived.get("field.derived.target.weighted_comprehensive_target")

    paragraphs = []

    if variant == "single_level":
        paragraphs.append(NarrativeParagraph(
            text=(
                f"本项目位于{zoning}，防治标准等级为{level}。"
                f"根据 GB/T 50434-2018 第 4 章，"
                f"按{zoning}{level}标准确定六项防治指标目标值如下。"
            ),
            evidence_refs=[
                "field.fact.prevention.control_standard_level",
                "field.fact.natural.water_soil_zoning",
            ],
            source_rule_refs=[
                "rule.gb_t_50434_2018.chapter_4",
                "rule.template_2026.section_7_2",
            ],
        ))
    else:
        # multi_level
        breakdown = facts.get("field.fact.prevention.control_standard_level_breakdown") or []
        zone_descs = []
        for z in breakdown:
            zid = z.get("zone_id", "?")
            zname = z.get("zone_name", zid)
            zlevel = z.get("standard_level", "?")
            area = z.get("area", {})
            area_str = f"{area.get('value', '?')} {area.get('unit', '')}" if isinstance(area, dict) else str(area)
            zone_descs.append(f"{zname}({zid}) {area_str} 执行{zlevel}标准")

        paragraphs.append(NarrativeParagraph(
            text=(
                f"本项目位于{zoning}，涉及两个及以上防治标准等级。"
                f"防治分区及对应等级如下: {'；'.join(zone_descs)}。"
                f"根据 GB/T 50434-2018 第 4 章及 2026 模板 7.3.2 节要求，"
                f"需按面积加权计算综合防治指标目标值。"
            ),
            evidence_refs=[
                "field.fact.prevention.control_standard_level",
                "field.fact.prevention.control_standard_level_breakdown",
                "field.fact.natural.water_soil_zoning",
            ],
            source_rule_refs=[
                "rule.gb_t_50434_2018.chapter_4",
                "rule.template_2026.section_7_3_2",
            ],
        ))

    # 目标值表述 (从 derived weighted target 取数)
    if isinstance(wt, dict):
        lines = []
        for key, label in _INDICATOR_LABELS.items():
            val = wt.get(key, "—")
            unit = _INDICATOR_UNITS.get(key, "")
            lines.append(f"{label}: {val}{unit}")

        method = "面积加权计算" if variant == "multi_level" else f"{level}标准查表"
        paragraphs.append(NarrativeParagraph(
            text=(
                f"经{method}，本项目水土流失防治六项指标目标值为: "
                + "；".join(lines) + "。"
            ),
            evidence_refs=[
                "field.derived.target.weighted_comprehensive_target",
                "cal.target.weighted_comprehensive",
            ],
            source_rule_refs=[
                "rule.gb_t_50434_2018.table_4_0_2_5",
            ],
        ))

        if variant == "multi_level":
            paragraphs.append(NarrativeParagraph(
                text=(
                    "上述目标值由 cal.target.weighted_comprehensive 计算器产出，"
                    "依据 GB/T 50434-2018 表 4.0.2-5 南方红壤区目标值，"
                    "按各防治分区面积权重加权得出。详见附表 AT-02。"
                ),
                evidence_refs=[
                    "cal.target.weighted_comprehensive",
                    "art.table.weighted_target_calculation",
                ],
                source_rule_refs=[
                    "rule.gb_t_50434_2018.table_4_0_2_5",
                ],
            ))

    return NarrativeBlock(
        section_id="sec.soil_loss_prevention.targets",
        title="防治目标",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id=variant,
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )
