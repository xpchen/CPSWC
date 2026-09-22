"""
sec_5_disposal — 5.1 弃渣来源与流向 + 5.2 弃渣场选址论证 narrative templates

最关键的 pilot section: 有 variant 分支, 两个样本产出不同正文。

Variants (静态注册):
  - no_site:    本项目不设永久弃渣场, 弃渣全部综合利用, 涉及临时堆土场
  - multi_site: 本项目设有多处弃渣场, 逐场论证级别/选址/拦挡
  - single_site: 本项目设有一处弃渣场 (未来扩展, 本轮不实现)

variant 选择逻辑:
  - derived 里 field.derived.disposal_site.level_assessment 非空且 len > 0 → multi_site
  - 明确提供了空清单 → no_site
  - 该字段整个缺失 → **未知**, 不渲染 no_site (P0-03)

P0-03 变更:
  原 no_site 分支无条件断言"弃渣全部通过综合利用消纳，不设置永久弃渣场"。
  但 no_site 是"derived 里没有弃渣场级别评定结果"推出来的 —— 资料没填和
  确实没有弃渣场, 在原实现里是同一个分支。现在:
    - 字段整个缺失 → SKELETON + Applicability.UNKNOWN + CONDITION_UNKNOWN 诊断
    - 明确空清单   → 复述弃方/综合利用数值, "不设永久弃渣场"改为待复核判断
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Applicability, Severity, Stage


TEMPLATE_SPEC_5_1 = NarrativeTemplateSpec(
    template_id="nt.sec_5_1.disposal_flow.v2",
    section_id="sec.disposal_site.source_and_flow",
    template_version="v2",
    template_author="cpswc_v0.6",
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
        "field.fact.disposal.external_receivers",
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


_LEVEL_FIELD_DERIVED = "field.derived.disposal_site.level_assessment"
_LEVEL_FIELD_FACT = "field.fact.disposal_site.level_assessment"


def _select_variant(facts: dict, derived: dict) -> str:
    """选择 variant (静态注册集合: no_site / multi_site / single_site)"""
    level_list = derived.get(_LEVEL_FIELD_DERIVED)
    if isinstance(level_list, list) and len(level_list) > 0:
        if len(level_list) == 1:
            return "single_site"  # 未来可扩展
        return "multi_site"
    return "no_site"


def _disposal_input_is_unknown(facts: dict, derived: dict) -> bool:
    """弃渣场级别评定结果是"没提供"还是"明确为空"?

    两个键都不存在 = 资料没给, 不能据此断言项目不设弃渣场。
    存在但是空列表 = 提供了空清单, 可以复述, 但仍需确认。
    """
    return (_LEVEL_FIELD_DERIVED not in derived
            and _LEVEL_FIELD_FACT not in facts
            and _LEVEL_FIELD_DERIVED not in facts)


def _unknown_block(section_id: str, title: str, spec: NarrativeTemplateSpec,
                   ev: SectionEvidence) -> NarrativeBlock:
    f = ev.add_finding(
        "CONDITION_UNKNOWN",
        f"{section_id}: 未提供弃渣场级别评定结果, 无法判断项目是否设置弃渣场",
        severity=Severity.BLOCK,
        target_ref=section_id,
        missing_input_refs=[_LEVEL_FIELD_FACT, _LEVEL_FIELD_DERIVED],
        remediation="补充弃渣场清单与级别评定结果; 确无弃渣场时提供空清单并说明核查依据",
        stage=Stage.INPUT,
    )
    return NarrativeBlock(
        section_id=section_id,
        title=title,
        render_status=RenderStatus.SKELETON,
        applicability=Applicability.UNKNOWN,
        block_warnings=["未提供弃渣场级别评定结果, 本节不作'不设弃渣场'结论"],
        quality_findings=[f],
        normative_basis=spec.normative_basis,
    )


# ============================================================
# 5.1 弃渣来源与流向
# ============================================================

def _render_5_1_no_site(facts: dict, derived: dict,
                        ledger=None, context=None) -> NarrativeBlock:
    ev = SectionEvidence("sec.disposal_site.source_and_flow", facts, derived,
                         ledger=ledger, context=context)
    spoil_v = ev.quantity("field.fact.earthwork.spoil")
    reuse_v = ev.quantity("field.fact.earthwork.comprehensive_reuse")
    temp_sites = facts.get("field.fact.construction.temp_topsoil_site") or []
    temp_count = len(temp_sites)
    receivers = facts.get("field.fact.disposal.external_receivers") or []

    if ev.all_present(spoil_v, reuse_v):
        paragraphs = [NarrativeParagraph(
            text=f"本项目弃渣总量为{spoil_v.display()}，其中综合利用{reuse_v.display()}。",
            evidence_refs=[
                "field.fact.earthwork.spoil",
                "field.fact.earthwork.comprehensive_reuse",
            ],
            source_rule_refs=["rule.template_2026.section_5_1"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.disposal_site.source_and_flow.volumes",
        )]
    else:
        paragraphs = [ev.gap_paragraph(
            spoil_v, reuse_v,
            lead="弃渣来源与流向缺少基础数据",
            source_rule_refs=["rule.template_2026.section_5_1"],
            paragraph_id="narr.disposal_site.source_and_flow.volumes",
        )]

    # "不设永久弃渣场"是一个论证结论, 不是 variant 分支的副产品。
    paragraphs.append(ev.judgment(
        "弃渣全部通过综合利用消纳，本项目不设置永久弃渣场。",
        target_ref="sec.disposal_site.source_and_flow",
        pending_text=(
            "弃渣场级别评定结果为空清单。是否确实不需设置永久弃渣场，"
            "须结合弃渣去向、综合利用去处落实情况与现场核查结论确认；"
            "确认记录形成前，本节不作“不设弃渣场”的结论。"),
        evidence_refs=["field.fact.earthwork.spoil",
                       "field.fact.earthwork.comprehensive_reuse",
                       _LEVEL_FIELD_DERIVED],
        source_rule_refs=["rule.template_2026.section_5_1"],
        paragraph_id="narr.disposal_site.source_and_flow.no_site_conclusion",
        remediation="核实弃渣去向后录入绑定当前输入的复核记录",
    ))

    # G-06: 弃方外运接收方逐条实名 + 接收方水保方案状态 + 附件挂钩
    for r in receivers:
        if not isinstance(r, dict):
            continue
        name = r.get("receiver_project_name", "—")
        loc = r.get("receiver_location", "")
        vol = r.get("volume_received") or {}
        if isinstance(vol, dict):
            vol_str = f"{vol.get('value', '?')} {vol.get('unit', '万m³')}".strip()
        else:
            vol_str = str(vol)
        dist = r.get("distance_km")
        dist_str = f"，运距约 {dist} km" if dist not in (None, "") else ""
        route = r.get("transport_route") or ""
        route_str = f"，经{route}运输" if route else ""
        timing = r.get("timing_window") or ""
        timing_str = f"，弃置时间窗：{timing}" if timing else ""

        status = r.get("receiver_swc_status", "未编")
        approval_id = r.get("receiver_swc_approval_id") or ""
        attach = r.get("receiver_swc_approval_attachment") or ""
        ownership = r.get("ownership_relation_statement") or ""

        if status == "已批复":
            parts_ok = []
            if approval_id:
                parts_ok.append(f"批复文号{approval_id}")
            if attach:
                parts_ok.append(f"详见{attach}")
            tail = f"（{'，'.join(parts_ok)}）" if parts_ok else ""
            status_clause = f"接收方水土保持方案已取得批复{tail}"
        elif status == "在编":
            status_clause = "接收方水土保持方案目前正在编制中"
        else:
            status_clause = "⚠️ 接收方水土保持方案尚未编制（审查将退回，须先取得批复或在编证明）"

        ownership_clause = f"双方权属关系详见{ownership}" if ownership else ""

        loc_clause = f"（{loc}）" if loc else ""
        paragraphs.append(NarrativeParagraph(
            text=(
                f"弃方 {vol_str} 全部运至 “{name}” {loc_clause}回填利用"
                f"{dist_str}{route_str}{timing_str}。"
                f"{status_clause}。"
                f"运至接收场地后，水土保持防治责任由接收方承担。"
                f"{ownership_clause}"
            ).strip(),
            evidence_refs=[
                "field.fact.disposal.external_receivers",
                "field.fact.earthwork.spoil",
                "field.fact.earthwork.comprehensive_reuse",
            ],
            source_rule_refs=[
                "rule.template_2026.section_5_1",
                "rule.template_2026.section_4_4_4",
            ],
        ))

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
        quality_findings=ev.findings,
    )


def _render_5_1_multi_site(facts: dict, derived: dict,
                           ledger=None, context=None) -> NarrativeBlock:
    ev = SectionEvidence("sec.disposal_site.source_and_flow", facts, derived,
                         ledger=ledger, context=context)
    spoil_rv = ev.quantity("field.fact.earthwork.spoil")
    reuse_rv = ev.quantity("field.fact.earthwork.comprehensive_reuse")
    spoil = spoil_rv.display() if spoil_rv.is_present else "（缺）"
    reuse = reuse_rv.display() if reuse_rv.is_present else "（缺）"
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
        quality_findings=ev.findings,
    )


# ============================================================
# 5.2 弃渣场选址论证
# ============================================================

def _render_5_2_no_site(facts: dict, derived: dict,
                        ledger=None, context=None) -> NarrativeBlock:
    ev = SectionEvidence("sec.disposal_site.site_selection", facts, derived,
                         ledger=ledger, context=context)
    return NarrativeBlock(
        section_id="sec.disposal_site.site_selection",
        title="弃渣场（或临时堆土场）选址与堆置论证",
        render_status=RenderStatus.FULL,
        paragraphs=[ev.judgment(
            "本项目不设置永久弃渣场，弃渣全部通过综合利用消纳，"
            "因此不涉及弃渣场选址论证和 GB 51018 弃渣场级别评定。"
            "临时堆土场的安排已在 5.1 节说明。",
            target_ref="sec.disposal_site.site_selection",
            pending_text=(
                "弃渣场级别评定结果为空清单，本节暂无可论证的弃渣场。"
                "是否确实无需进行弃渣场选址论证与 GB 51018 级别评定，"
                "须经核查确认后方可成立；确认记录形成前不作该结论。"
                "临时堆土场的安排见 5.1 节。"),
            evidence_refs=[
                "field.fact.earthwork.spoil",
                "field.fact.earthwork.comprehensive_reuse",
                _LEVEL_FIELD_DERIVED,
            ],
            source_rule_refs=[
                "rule.template_2026.section_5_2",
                "rule.gb_51018_2014.section_5_7_1",
            ],
            paragraph_id="narr.disposal_site.site_selection.no_site",
            remediation="核查弃渣去向后录入绑定当前输入的复核记录",
        )],
        variant_id="no_site",
        template_id=TEMPLATE_SPEC_5_2.template_id,
        template_version=TEMPLATE_SPEC_5_2.template_version,
        normative_basis=TEMPLATE_SPEC_5_2.normative_basis,
        quality_findings=ev.findings,
    )


def _render_5_2_multi_site(facts: dict, derived: dict,
                           ledger=None, context=None) -> NarrativeBlock:
    ev = SectionEvidence("sec.disposal_site.site_selection", facts, derived,
                         ledger=ledger, context=context)
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
        quality_findings=ev.findings,
    )


# ============================================================
# Public API
# ============================================================

def render_5_1(facts: dict, derived: dict, triggered: set[str],
               ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """渲染 5.1 弃渣来源与流向"""
    variant = _select_variant(facts, derived)
    if variant == "no_site":
        if _disposal_input_is_unknown(facts, derived):
            ev = SectionEvidence("sec.disposal_site.source_and_flow", facts,
                                 derived, ledger=ledger, context=context)
            return _unknown_block("sec.disposal_site.source_and_flow",
                                  "弃渣来源与流向", TEMPLATE_SPEC_5_1, ev)
        return _render_5_1_no_site(facts, derived, ledger=ledger, context=context)
    return _render_5_1_multi_site(facts, derived, ledger=ledger, context=context)


def render_5_2(facts: dict, derived: dict, triggered: set[str],
               ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """渲染 5.2 弃渣场选址论证"""
    variant = _select_variant(facts, derived)
    if variant == "no_site":
        if _disposal_input_is_unknown(facts, derived):
            ev = SectionEvidence("sec.disposal_site.site_selection", facts,
                                 derived, ledger=ledger, context=context)
            return _unknown_block("sec.disposal_site.site_selection",
                                  "弃渣场（或临时堆土场）选址与堆置论证",
                                  TEMPLATE_SPEC_5_2, ev)
        return _render_5_2_no_site(facts, derived, ledger=ledger, context=context)
    return _render_5_2_multi_site(facts, derived, ledger=ledger, context=context)
