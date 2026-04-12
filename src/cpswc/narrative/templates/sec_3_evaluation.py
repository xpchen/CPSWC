"""
sec_3_evaluation — 第3章 项目水土保持评价 narrative template

两个子节:
  sec.evaluation              — 章标题 (总评段落)
  sec.evaluation.site_selection — 3.1 选址选线评价 (conditional: redline_conflict)
  sec.evaluation.earthwork_balance — 3.2 土石方平衡评价

消费 facts:
  earthwork.* (挖/填/利用/弃/借方)
  land.* (总面积/永久/临时)
  natural.* (侵蚀类型/强度/区划)
  prediction.* (新增/可减少)
  topsoil.stripable_volume
  location.*
消费 obligations:
  ob.evaluation.dual_source_earthwork_justification
  ob.unavoidability.redline_conflict
消费 derived:
  field.derived.target.weighted_comprehensive_target
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


TEMPLATE_SPEC_EVAL = NarrativeTemplateSpec(
    template_id="nt.sec_3.evaluation.v1",
    section_id="sec.evaluation",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_3",
        "standard.gb_50433_2018.section_3",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.earthwork.excavation",
        "field.fact.earthwork.fill",
        "field.fact.earthwork.self_reuse",
        "field.fact.earthwork.comprehensive_reuse",
        "field.fact.earthwork.spoil",
        "field.fact.earthwork.borrow",
        "field.fact.earthwork.borrow_source_type",
        "field.fact.land.total_area",
        "field.fact.natural.soil_erosion_type",
        "field.fact.natural.soil_erosion_intensity",
        "field.fact.natural.water_soil_zoning",
        "field.fact.prediction.new_loss",
        "field.fact.prediction.reducible_loss",
        "field.fact.topsoil.stripable_volume",
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
    ],
)

TEMPLATE_SPEC_EARTHWORK = NarrativeTemplateSpec(
    template_id="nt.sec_3_2.earthwork_balance_eval.v1",
    section_id="sec.evaluation.earthwork_balance",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_3",
        "standard.gb_50433_2018.section_3",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.earthwork.excavation",
        "field.fact.earthwork.fill",
        "field.fact.earthwork.self_reuse",
        "field.fact.earthwork.comprehensive_reuse",
        "field.fact.earthwork.spoil",
        "field.fact.earthwork.borrow",
        "field.fact.earthwork.borrow_source_type",
        "field.fact.topsoil.stripable_volume",
    ],
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        unit = v.get("unit", "")
        return f"{v['value']} {unit}".strip()
    if isinstance(v, list):
        return "、".join(str(x) for x in v)
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


# ── sec.evaluation (章总评) ──────────────────────────────────

def render_evaluation(facts: dict, derived: dict, triggered: set[str],
                      **kwargs) -> NarrativeBlock:
    """渲染 第3章 项目水土保持评价 — 总评段落"""
    province = _v(facts, "field.fact.location.province_list")
    prefecture = _v(facts, "field.fact.location.prefecture_list")
    zoning = _v(facts, "field.fact.natural.water_soil_zoning")
    erosion_type = _v(facts, "field.fact.natural.soil_erosion_type")
    erosion_intensity = _v(facts, "field.fact.natural.soil_erosion_intensity")
    total_area = _v(facts, "field.fact.land.total_area")
    new_loss = _v(facts, "field.fact.prediction.new_loss")
    reducible = _v(facts, "field.fact.prediction.reducible_loss")

    p1 = NarrativeParagraph(
        text=(
            f"项目位于{province}{prefecture}，属{zoning}，"
            f"以{erosion_type}为主，现状土壤侵蚀强度为{erosion_intensity}。"
            f"项目总占地{total_area}，施工期新增水土流失量{new_loss}，"
            f"其中可治理量{reducible}。"
        ),
        evidence_refs=[
            "field.fact.location.province_list",
            "field.fact.location.prefecture_list",
            "field.fact.natural.water_soil_zoning",
            "field.fact.natural.soil_erosion_type",
            "field.fact.natural.soil_erosion_intensity",
            "field.fact.land.total_area",
            "field.fact.prediction.new_loss",
            "field.fact.prediction.reducible_loss",
        ],
        source_rule_refs=[
            "rule.template_2026.section_3",
            "standard.gb_50433_2018.section_3",
        ],
    )

    paragraphs = [p1]

    # 如果有 weighted target，添加防治目标评价结论
    weighted = derived.get("field.derived.target.weighted_comprehensive_target")
    if isinstance(weighted, dict):
        ctrl = weighted.get("control_degree", "—")
        veg = weighted.get("vegetation_restoration_rate", "—")
        p2 = NarrativeParagraph(
            text=(
                f"经计算，项目水土流失防治措施可使扰动土地治理率达到{ctrl}%、"
                f"林草植被恢复率达到{veg}%，"
                f"各项指标均满足方案编制要求。"
            ),
            evidence_refs=[
                "field.derived.target.weighted_comprehensive_target",
            ],
            source_rule_refs=[
                "standard.gb_50433_2018.section_3",
            ],
        )
        paragraphs.append(p2)

    return NarrativeBlock(
        section_id="sec.evaluation",
        title="项目水土保持评价",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_EVAL.template_id,
        template_version=TEMPLATE_SPEC_EVAL.template_version,
        normative_basis=TEMPLATE_SPEC_EVAL.normative_basis,
    )


# ── sec.evaluation.earthwork_balance (3.2 土石方平衡评价) ────

def render_earthwork_balance(facts: dict, derived: dict, triggered: set[str],
                             **kwargs) -> NarrativeBlock:
    """渲染 3.2 土石方平衡评价"""
    exc = _v(facts, "field.fact.earthwork.excavation")
    fill = _v(facts, "field.fact.earthwork.fill")
    reuse = _v(facts, "field.fact.earthwork.self_reuse")
    comp_reuse = _v(facts, "field.fact.earthwork.comprehensive_reuse")
    spoil = _v(facts, "field.fact.earthwork.spoil")
    borrow = _v(facts, "field.fact.earthwork.borrow")
    borrow_type = _v(facts, "field.fact.earthwork.borrow_source_type")
    topsoil_vol = _v(facts, "field.fact.topsoil.stripable_volume")

    exc_n = _num(facts, "field.fact.earthwork.excavation")
    fill_n = _num(facts, "field.fact.earthwork.fill")
    reuse_n = _num(facts, "field.fact.earthwork.self_reuse")

    # 利用率
    reuse_pct = f"{reuse_n / exc_n * 100:.0f}" if exc_n > 0 else "—"

    p1 = NarrativeParagraph(
        text=(
            f"本项目挖方总量{exc}，填方总量{fill}，"
            f"场内自行利用{reuse}（利用率{reuse_pct}%），"
            f"综合利用{comp_reuse}，弃方{spoil}。"
        ),
        evidence_refs=[
            "field.fact.earthwork.excavation",
            "field.fact.earthwork.fill",
            "field.fact.earthwork.self_reuse",
            "field.fact.earthwork.comprehensive_reuse",
            "field.fact.earthwork.spoil",
        ],
        source_rule_refs=[
            "rule.template_2026.section_3",
        ],
    )

    # 借方评价
    p2_parts = []
    borrow_n = _num(facts, "field.fact.earthwork.borrow")
    if borrow_n > 0:
        p2_parts.append(
            f"项目需借方{borrow}，来源为{borrow_type}。"
        )
    else:
        p2_parts.append("项目无需外借土石方。")

    # 表土评价
    p2_parts.append(
        f"可剥离表土{topsoil_vol}，全部用于后期绿化覆土。"
    )

    # 如果触发了 dual_source 义务
    if "ob.evaluation.dual_source_earthwork_justification" in triggered:
        p2_parts.append(
            "本项目涉及多来源土石方，已分别说明各来源的弃方去向和借方来源。"
        )

    p2 = NarrativeParagraph(
        text="".join(p2_parts),
        evidence_refs=[
            "field.fact.earthwork.borrow",
            "field.fact.earthwork.borrow_source_type",
            "field.fact.topsoil.stripable_volume",
            "ob.evaluation.dual_source_earthwork_justification",
        ],
        source_rule_refs=[
            "rule.template_2026.section_3",
            "standard.gb_50433_2018.section_3",
        ],
    )

    p3 = NarrativeParagraph(
        text=(
            "综上，本项目土石方平衡合理，"
            "弃方有明确去向，借方有可靠来源，"
            "表土剥离利用方案可行。详见土石方平衡表。"
        ),
        evidence_refs=[
            "art.table.earthwork_balance",
        ],
        source_rule_refs=[
            "standard.gb_50433_2018.section_3",
        ],
    )

    return NarrativeBlock(
        section_id="sec.evaluation.earthwork_balance",
        title="土石方平衡评价",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2, p3],
        variant_id="default",
        template_id=TEMPLATE_SPEC_EARTHWORK.template_id,
        template_version=TEMPLATE_SPEC_EARTHWORK.template_version,
        normative_basis=TEMPLATE_SPEC_EARTHWORK.normative_basis,
    )
