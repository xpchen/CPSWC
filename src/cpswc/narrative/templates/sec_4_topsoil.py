"""
sec_4_topsoil — 第4章 表土资源保护与利用 narrative template

两个子节:
  sec.topsoil.stripping  — 4.1 表土剥离
  sec.topsoil.balance    — 4.2 表土平衡

消费 facts:
  topsoil.excavation / fill / stripable_area / stripable_volume
  earthwork.excavation / fill
  land.total_area
消费 obligations:
  ob.topsoil.balance_required
  ob.topsoil.reuse_evidence
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


TEMPLATE_SPEC_STRIPPING = NarrativeTemplateSpec(
    template_id="nt.sec_4_1.topsoil_stripping.v1",
    section_id="sec.topsoil.stripping",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_4",
        "standard.gb_50433_2018.section_4",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.topsoil.stripable_area",
        "field.fact.topsoil.stripable_volume",
        "field.fact.land.total_area",
    ],
)

TEMPLATE_SPEC_BALANCE = NarrativeTemplateSpec(
    template_id="nt.sec_4_2.topsoil_balance.v1",
    section_id="sec.topsoil.balance",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_4",
        "standard.gb_50433_2018.section_4",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.topsoil.excavation",
        "field.fact.topsoil.fill",
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


# ── sec.topsoil.stripping (4.1 表土剥离) ────────────────────

def render_stripping(facts: dict, derived: dict, triggered: set[str],
                     **kwargs) -> NarrativeBlock:
    """渲染 4.1 表土剥离"""
    total_area = _v(facts, "field.fact.land.total_area")
    strip_area = _v(facts, "field.fact.topsoil.stripable_area")
    strip_vol = _v(facts, "field.fact.topsoil.stripable_volume")

    total_n = _num(facts, "field.fact.land.total_area")
    strip_n = _num(facts, "field.fact.topsoil.stripable_area")
    strip_pct = f"{strip_n / total_n * 100:.0f}" if total_n > 0 else "—"

    p1 = NarrativeParagraph(
        text=(
            f"项目总占地面积{total_area}，"
            f"经现场踏勘，可剥离表土区域面积{strip_area}，"
            f"占总占地面积的{strip_pct}%。"
            f"按平均剥离厚度估算，可剥离表土量为{strip_vol}。"
        ),
        evidence_refs=[
            "field.fact.land.total_area",
            "field.fact.topsoil.stripable_area",
            "field.fact.topsoil.stripable_volume",
        ],
        source_rule_refs=[
            "rule.template_2026.section_4",
            "standard.gb_50433_2018.section_4",
        ],
    )

    p2 = NarrativeParagraph(
        text=(
            "表土剥离应在场地平整前进行，"
            "剥离的表土集中堆放于临时堆土区，"
            "采用防尘网覆盖并设置临时排水沟，"
            "防止水土流失。"
        ),
        evidence_refs=[
            "field.fact.topsoil.stripable_volume",
        ],
        source_rule_refs=[
            "standard.gb_50433_2018.section_4",
        ],
    )

    return NarrativeBlock(
        section_id="sec.topsoil.stripping",
        title="表土剥离",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2],
        variant_id="default",
        template_id=TEMPLATE_SPEC_STRIPPING.template_id,
        template_version=TEMPLATE_SPEC_STRIPPING.template_version,
        normative_basis=TEMPLATE_SPEC_STRIPPING.normative_basis,
    )


# ── sec.topsoil.balance (4.2 表土平衡) ──────────────────────

def render_balance(facts: dict, derived: dict, triggered: set[str],
                   **kwargs) -> NarrativeBlock:
    """渲染 4.2 表土平衡"""
    strip_vol = _v(facts, "field.fact.topsoil.stripable_volume")
    ts_exc = _v(facts, "field.fact.topsoil.excavation")
    ts_fill = _v(facts, "field.fact.topsoil.fill")

    strip_n = _num(facts, "field.fact.topsoil.stripable_volume")
    exc_n = _num(facts, "field.fact.topsoil.excavation")
    fill_n = _num(facts, "field.fact.topsoil.fill")
    surplus = exc_n - fill_n

    p1 = NarrativeParagraph(
        text=(
            f"可剥离表土量{strip_vol}，"
            f"表土挖方{ts_exc}，回覆利用量{ts_fill}。"
        ),
        evidence_refs=[
            "field.fact.topsoil.stripable_volume",
            "field.fact.topsoil.excavation",
            "field.fact.topsoil.fill",
        ],
        source_rule_refs=[
            "rule.template_2026.section_4",
        ],
    )

    paragraphs = [p1]

    # 平衡结论
    if surplus > 0:
        conclusion = (
            f"表土挖方大于回覆量，剩余 {surplus:.2f} 万m³ "
            f"用于项目区绿化覆土或外运至其他绿化项目利用。"
        )
    elif surplus < 0:
        conclusion = (
            f"表土回覆量大于剥离量，不足部分 {abs(surplus):.2f} 万m³ "
            f"由外购种植土补充。"
        )
    else:
        conclusion = "表土挖填平衡，全部用于项目区绿化覆土。"

    p2_parts = [conclusion]

    if "ob.topsoil.reuse_evidence" in triggered:
        p2_parts.append("剥离表土全部在项目区内回覆利用，不外运。")

    p2 = NarrativeParagraph(
        text="".join(p2_parts),
        evidence_refs=[
            "field.fact.topsoil.excavation",
            "field.fact.topsoil.fill",
            "ob.topsoil.reuse_evidence",
        ],
        source_rule_refs=[
            "standard.gb_50433_2018.section_4",
        ],
    )
    paragraphs.append(p2)

    return NarrativeBlock(
        section_id="sec.topsoil.balance",
        title="表土平衡",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_BALANCE.template_id,
        template_version=TEMPLATE_SPEC_BALANCE.template_version,
        normative_basis=TEMPLATE_SPEC_BALANCE.normative_basis,
    )
