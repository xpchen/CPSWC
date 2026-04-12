"""
sec_5_disposal — 5.1 弃渣来源与流向 + 5.2 弃渣场选址论证 narrative templates

最关键的 pilot section: 有 variant 分支, 两个样本产出不同正文。

Variants (静态注册):
  - no_site:    本项目不设永久弃渣场, 弃渣全部综合利用, 涉及临时堆土场
  - multi_site: 本项目设有多处弃渣场, 逐场论证级别/选址/拦挡
  - single_site: 本项目设有一处弃渣场 (未来扩展, 本轮不实现)

variant 选择逻辑:
  - derived 里 field.derived.disposal_site.level_assessment 非空且 len > 0 → multi_site
  - 否则 → no_site
"""
from __future__ import annotations
from narrative_contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


TEMPLATE_SPEC_5_1 = NarrativeTemplateSpec(
    template_id="nt.sec_5_1.disposal_flow.v1",
    section_id="sec.disposal_site.source_and_flow",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_5_1",
        "rule.gb_51018_2014.section_5_7_1",
    ],
    supported_variants=["no_site", "multi_site", "single_site"],
    input_fields=[
        "field.fact.earthwork.spoil",
        "field.fact.earthwork.comprehensive_reuse",
        "field.fact.disposal_site.level_assessment",
        "field.derived.disposal_site.level_assessment",
        "field.fact.construction.temp_topsoil_site",
    ],
)

TEMPLATE_SPEC_5_2 = NarrativeTemplateSpec(
    template_id="nt.sec_5_2.disposal_siting.v1",
    section_id="sec.disposal_site.site_selection",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_5_2",
        "rule.gb_51018_2014.section_5_7_1",
        "rule.gb_51018_2014.table_5_7_1_notes",
    ],
    supported_variants=["no_site", "multi_site", "single_site"],
    input_fields=[
        "field.fact.disposal_site.level_assessment",
        "field.derived.disposal_site.level_assessment",
        "field.fact.earthwork.spoil",
        "field.fact.earthwork.comprehensive_reuse",
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
        return str(len(v))
    return str(v)


def _select_variant(facts: dict, derived: dict) -> str:
    """选择 variant (静态注册集合: no_site / multi_site / single_site)"""
    level_list = derived.get("field.derived.disposal_site.level_assessment")
    if isinstance(level_list, list) and len(level_list) > 0:
        if len(level_list) == 1:
            return "single_site"  # 未来可扩展
        return "multi_site"
    return "no_site"


# ============================================================
# 5.1 弃渣来源与流向
# ============================================================

def _render_5_1_no_site(facts: dict, derived: dict) -> NarrativeBlock:
    spoil = _v(facts, "field.fact.earthwork.spoil")
    reuse = _v(facts, "field.fact.earthwork.comprehensive_reuse")
    temp_sites = facts.get("field.fact.construction.temp_topsoil_site") or []
    temp_count = len(temp_sites)

    paragraphs = [
        NarrativeParagraph(
            text=(
                f"本项目弃渣总量为{spoil}，其中综合利用{reuse}。"
                f"弃渣全部通过综合利用消纳，不设置永久弃渣场。"
            ),
            evidence_refs=[
                "field.fact.earthwork.spoil",
                "field.fact.earthwork.comprehensive_reuse",
            ],
            source_rule_refs=["rule.template_2026.section_5_1"],
        ),
    ]

    if temp_count > 0:
        site_names = "、".join(
            s.get("name_or_id", s.get("site_id", "?"))
            for s in temp_sites
        )
        paragraphs.append(NarrativeParagraph(
            text=(
                f"项目施工期间设有{temp_count}处临时堆土场/中转场（{site_names}），"
                f"用于表土或渣土临时堆存与周转，施工完毕后恢复原状。"
                f"临时堆土场不属于 GB 51018 弃渣场分级范畴。"
            ),
            evidence_refs=["field.fact.construction.temp_topsoil_site"],
            source_rule_refs=[
                "rule.template_2026.section_5_1",
                "rule.gb_51018_2014.section_5_7_1",
            ],
        ))

    return NarrativeBlock(
        section_id="sec.disposal_site.source_and_flow",
        title="弃渣来源与流向",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="no_site",
        template_id=TEMPLATE_SPEC_5_1.template_id,
        template_version=TEMPLATE_SPEC_5_1.template_version,
        normative_basis=TEMPLATE_SPEC_5_1.normative_basis,
    )


def _render_5_1_multi_site(facts: dict, derived: dict) -> NarrativeBlock:
    spoil = _v(facts, "field.fact.earthwork.spoil")
    reuse = _v(facts, "field.fact.earthwork.comprehensive_reuse")
    sites_raw = facts.get("field.fact.disposal_site.level_assessment") or []
    sites_derived = derived.get("field.derived.disposal_site.level_assessment") or []
    n = len(sites_raw)

    paragraphs = [
        NarrativeParagraph(
            text=(
                f"本项目弃渣总量为{spoil}，综合利用{reuse}。"
                f"项目设有{n}处弃渣场，需分场论证选址合理性与级别评定。"
            ),
            evidence_refs=[
                "field.fact.earthwork.spoil",
                "field.fact.earthwork.comprehensive_reuse",
                "field.fact.disposal_site.level_assessment",
            ],
            source_rule_refs=["rule.template_2026.section_5_1"],
        ),
    ]

    # 逐场摘要
    for sr, sd in zip(sites_raw, sites_derived):
        sid = sr.get("site_id", "?")
        sname = sr.get("site_name", sid)
        vol = sr.get("volume", {})
        vol_str = f"{vol.get('value', '?')} {vol.get('unit', '')}" if isinstance(vol, dict) else str(vol)
        ht = sr.get("max_height", {})
        ht_str = f"{ht.get('value', '?')} {ht.get('unit', '')}" if isinstance(ht, dict) else str(ht)
        harm = sr.get("downstream_harm_class", "?")
        level = sd.get("level", "?")
        governing = sd.get("governing_dimension", "?")

        paragraphs.append(NarrativeParagraph(
            text=(
                f"{sname}({sid}): 堆渣量{vol_str}, 最大堆渣高度{ht_str}, "
                f"下游危害程度为 {harm}。"
                f"经 GB 51018 表 5.7.1 三维判定 (就高不就低), "
                f"弃渣场级别为{level} (决定维度: {governing})。"
            ),
            evidence_refs=[
                "field.fact.disposal_site.level_assessment",
                "field.derived.disposal_site.level_assessment",
                f"cal.disposal_site.level_assessment",
            ],
            source_rule_refs=[
                "rule.gb_51018_2014.section_5_7_1",
                "rule.gb_51018_2014.table_5_7_1_notes",
            ],
        ))

    return NarrativeBlock(
        section_id="sec.disposal_site.source_and_flow",
        title="弃渣来源与流向",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="multi_site",
        template_id=TEMPLATE_SPEC_5_1.template_id,
        template_version=TEMPLATE_SPEC_5_1.template_version,
        normative_basis=TEMPLATE_SPEC_5_1.normative_basis,
    )


# ============================================================
# 5.2 弃渣场选址论证
# ============================================================

def _render_5_2_no_site(facts: dict, derived: dict) -> NarrativeBlock:
    return NarrativeBlock(
        section_id="sec.disposal_site.site_selection",
        title="弃渣场（或临时堆土场）选址与堆置论证",
        render_status=RenderStatus.FULL,
        paragraphs=[NarrativeParagraph(
            text=(
                "本项目不设置永久弃渣场，弃渣全部通过综合利用消纳。"
                "因此不涉及弃渣场选址论证和 GB 51018 弃渣场级别评定。"
                "临时堆土场的安排已在 5.1 节说明。"
            ),
            evidence_refs=[
                "field.fact.earthwork.spoil",
                "field.fact.earthwork.comprehensive_reuse",
            ],
            source_rule_refs=[
                "rule.template_2026.section_5_2",
                "rule.gb_51018_2014.section_5_7_1",
            ],
        )],
        variant_id="no_site",
        template_id=TEMPLATE_SPEC_5_2.template_id,
        template_version=TEMPLATE_SPEC_5_2.template_version,
        normative_basis=TEMPLATE_SPEC_5_2.normative_basis,
    )


def _render_5_2_multi_site(facts: dict, derived: dict) -> NarrativeBlock:
    sites_derived = derived.get("field.derived.disposal_site.level_assessment") or []

    paragraphs = [
        NarrativeParagraph(
            text=(
                "根据 GB 51018-2014 第 5.7.1 条，弃渣场级别按堆渣量、最大堆渣高度、"
                "渣场失事对主体工程或环境造成的危害程度三个维度确定，"
                "三者不一致时就高不就低。各弃渣场选址论证与级别评定结果如下。"
            ),
            evidence_refs=["field.derived.disposal_site.level_assessment"],
            source_rule_refs=[
                "rule.gb_51018_2014.section_5_7_1",
                "rule.gb_51018_2014.table_5_7_1_notes",
            ],
        ),
    ]

    # 高风险义务提示
    levels_int = []
    for sd in sites_derived:
        lv = sd.get("level", "5级")
        num = int(lv.replace("级", ""))
        levels_int.append(num)

    min_level = min(levels_int) if levels_int else 5

    obligation_notes = []
    if min_level <= 3:
        obligation_notes.append("稳定监测（ob.disposal_site.stability_monitoring）")
        obligation_notes.append("全过程视频监控（ob.disposal_site.video_surveillance）")
    if min_level <= 2:
        obligation_notes.append("地质勘察报告（ob.disposal_site.geology_report）")

    if obligation_notes:
        paragraphs.append(NarrativeParagraph(
            text=(
                f"项目弃渣场最严重级别为{min_level}级，根据 2026 模板要求，"
                f"本项目需满足以下高风险义务：{'；'.join(obligation_notes)}。"
            ),
            evidence_refs=[
                "field.derived.disposal_site.level_assessment",
                "ob.disposal_site.stability_monitoring",
                "ob.disposal_site.video_surveillance",
                "ob.disposal_site.geology_report",
            ],
            source_rule_refs=[
                "rule.template_2026.section_5_2",
            ],
        ))

    return NarrativeBlock(
        section_id="sec.disposal_site.site_selection",
        title="弃渣场（或临时堆土场）选址与堆置论证",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="multi_site",
        template_id=TEMPLATE_SPEC_5_2.template_id,
        template_version=TEMPLATE_SPEC_5_2.template_version,
        normative_basis=TEMPLATE_SPEC_5_2.normative_basis,
    )


# ============================================================
# Public API
# ============================================================

def render_5_1(facts: dict, derived: dict, triggered: set[str],
               **kwargs) -> NarrativeBlock:
    """渲染 5.1 弃渣来源与流向"""
    variant = _select_variant(facts, derived)
    if variant == "no_site":
        return _render_5_1_no_site(facts, derived)
    return _render_5_1_multi_site(facts, derived)


def render_5_2(facts: dict, derived: dict, triggered: set[str],
               **kwargs) -> NarrativeBlock:
    """渲染 5.2 弃渣场选址论证"""
    variant = _select_variant(facts, derived)
    if variant == "no_site":
        return _render_5_2_no_site(facts, derived)
    return _render_5_2_multi_site(facts, derived)
