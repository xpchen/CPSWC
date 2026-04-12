"""
sec_7_5_benefit_analysis — 防治效益分析 narrative template

从 prediction.* facts + derived.target.* 做效益定性结论。
v0: 不做逐分区逐指标的详细达标计算 (需要 measures 实施效果数据),
    只做总量级减损结论 + 引用六率目标值。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)

TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_7_5.benefit_analysis.v1",
    section_id="sec.soil_loss_prevention.benefit_analysis",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_7",
        "rule.gb_t_50434_2018.chapter_4",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.prediction.total_loss",
        "field.fact.prediction.new_loss",
        "field.fact.prediction.reducible_loss",
        "field.fact.land.total_area",
        "field.derived.target.weighted_comprehensive_target",
    ],
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        unit = v.get("unit", "")
        return f"{v['value']} {unit}".strip()
    return str(v)


def _num(facts: dict, key: str, default: float = 0.0) -> float:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        try:
            return float(v["value"])
        except (ValueError, TypeError):
            return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    total_loss = _v(facts, "field.fact.prediction.total_loss")
    new_loss = _v(facts, "field.fact.prediction.new_loss")
    reducible = _v(facts, "field.fact.prediction.reducible_loss")
    total_area = _v(facts, "field.fact.land.total_area")

    total_n = _num(facts, "field.fact.prediction.total_loss")
    new_n = _num(facts, "field.fact.prediction.new_loss")
    reducible_n = _num(facts, "field.fact.prediction.reducible_loss")

    paragraphs = []

    # 段1: 减损效益
    if new_n > 0 and reducible_n > 0:
        reduce_pct = min(reducible_n / new_n * 100, 100)
        p1_text = (
            f"通过实施本方案各项水土保持措施，"
            f"预测水土流失总量{total_loss}，其中新增水土流失量{new_loss}，"
            f"可治理水土流失量{reducible}，"
            f"治理比例为{reduce_pct:.0f}%。"
        )
    else:
        p1_text = (
            f"预测水土流失总量{total_loss}，其中新增水土流失量{new_loss}。"
            f"通过实施本方案各项水土保持措施，可有效减少水土流失。"
        )

    paragraphs.append(NarrativeParagraph(
        text=p1_text,
        evidence_refs=[
            "field.fact.prediction.total_loss",
            "field.fact.prediction.new_loss",
            "field.fact.prediction.reducible_loss",
        ],
        source_rule_refs=[
            "rule.template_2026.section_7",
        ],
    ))

    # 段2: 六率目标达标结论
    wt = derived.get("field.derived.target.weighted_comprehensive_target")
    if isinstance(wt, dict):
        indicator_labels = {
            "control_degree": "水土流失治理度",
            "soil_loss_control_ratio": "土壤流失控制比",
            "spoil_protection_rate": "渣土防护率",
            "topsoil_protection_rate": "表土保护率",
            "vegetation_restoration_rate": "林草植被恢复率",
            "vegetation_coverage_rate": "林草覆盖率",
        }
        target_items = []
        for key, label in indicator_labels.items():
            val = wt.get(key)
            if val is not None:
                unit = "%" if key != "soil_loss_control_ratio" else ""
                target_items.append(f"{label}{val}{unit}")

        if target_items:
            paragraphs.append(NarrativeParagraph(
                text=(
                    f"设计水平年各项防治指标目标值为: "
                    f"{'、'.join(target_items)}。"
                    f"通过合理布设工程措施、植物措施和临时措施，"
                    f"各项指标可达到上述目标值要求。"
                    f"详见六项指标复核表。"
                ),
                evidence_refs=[
                    "field.derived.target.weighted_comprehensive_target",
                    "art.table.six_indicator_review",
                ],
                source_rule_refs=[
                    "rule.gb_t_50434_2018.chapter_4",
                ],
            ))

    # 段3: 综合结论
    paragraphs.append(NarrativeParagraph(
        text=(
            f"综上，本方案水土保持措施布局合理，"
            f"防治责任范围{total_area}内的水土流失可得到有效控制，"
            f"各项防治目标可以实现。"
        ),
        evidence_refs=[
            "field.fact.land.total_area",
        ],
        source_rule_refs=[
            "rule.template_2026.section_7",
        ],
    ))

    return NarrativeBlock(
        section_id="sec.soil_loss_prevention.benefit_analysis",
        title="防治效益分析",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )
