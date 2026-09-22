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

P0-03 变更 (docs/report_production_plan/03_P0_TASKS.md):
  原实现对空输入也输出"项目无需外借土石方""可剥离表土—，全部用于后期绿化覆土"
  "土石方平衡合理，弃方有明确去向，借方有可靠来源" —— 实测见
  implementation/P0_BASELINE.md PROBE-1b。三处问题:

    1. `_num(facts, key, default=0.0)` 把缺失当 0, 于是"借方数据没填"被写成
       "无需外借土石方"。现在缺失走缺口段, 明确填 0 才复述为无借方。
    2. 表土去向("全部用于后期绿化覆土")是一个方案安排, 不是 stripable_volume
       这个数字能推出来的, 已删除。
    3. 平衡合理性/去向可靠性是专业判断, 改走 judgment()。

  另: 章总评里"各项指标均满足方案编制要求"用的是**目标值** —— 目标不能证明
  达标 (验收 N04), 该句已删除, 目标值只作为目标复述。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity


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
        "field.derived.target.weighted_comprehensive_target",
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


# ── sec.evaluation (章总评) ──────────────────────────────────

def render_evaluation(facts: dict, derived: dict, triggered: set[str],
                      ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """渲染 第3章 项目水土保持评价 — 总评段落"""
    ev = SectionEvidence("sec.evaluation", facts, derived, ledger=ledger, context=context)

    province = ev.text("field.fact.location.province_list")
    prefecture = ev.text("field.fact.location.prefecture_list")
    zoning = ev.text("field.fact.natural.water_soil_zoning")
    erosion_type = ev.text("field.fact.natural.soil_erosion_type")
    erosion_intensity = ev.text("field.fact.natural.soil_erosion_intensity")
    total_area = ev.quantity("field.fact.land.total_area")
    new_loss = ev.quantity("field.fact.prediction.new_loss")
    reducible = ev.quantity("field.fact.prediction.reducible_loss")

    paragraphs: list[NarrativeParagraph] = []

    located = [province, prefecture, zoning, erosion_type, erosion_intensity]
    if ev.all_present(*located):
        paragraphs.append(NarrativeParagraph(
            text=(f"项目位于{province.display()}{prefecture.display()}，"
                  f"属{zoning.display()}，以{erosion_type.display()}为主，"
                  f"现状土壤侵蚀强度为{erosion_intensity.display()}。"),
            evidence_refs=[v.field_id for v in located],
            source_rule_refs=["rule.template_2026.section_3",
                              "standard.gb_50433_2018.section_3"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.evaluation.setting",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            *located,
            lead="项目区自然概况资料不完整，无法给出评价背景",
            source_rule_refs=["rule.template_2026.section_3"],
            paragraph_id="narr.evaluation.setting",
        ))

    quantities = [total_area, new_loss, reducible]
    if ev.all_present(*quantities):
        paragraphs.append(NarrativeParagraph(
            text=(f"项目总占地{total_area.display()}，"
                  f"施工期新增水土流失量{new_loss.display()}，"
                  f"其中可治理量{reducible.display()}。"),
            evidence_refs=[v.field_id for v in quantities],
            source_rule_refs=["rule.template_2026.section_3"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.evaluation.quantities",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            *quantities,
            lead="占地与流失预测数据不完整",
            source_rule_refs=["rule.template_2026.section_3"],
            paragraph_id="narr.evaluation.quantities",
        ))

    # 防治指标: 只复述**目标值**。目标不是效果, 不能据此说"均满足要求"。
    weighted = ev.raw("field.derived.target.weighted_comprehensive_target",
                      severity=Severity.WARN)
    if weighted.is_present and isinstance(weighted.value, dict):
        ctrl = weighted.value.get("control_degree")
        veg = weighted.value.get("vegetation_restoration_rate")
        if ctrl is not None and veg is not None:
            paragraphs.append(NarrativeParagraph(
                text=(f"本项目防治标准对应的目标值为：水土流失治理度{ctrl}%、"
                      f"林草植被恢复率{veg}%。上述为“目标值”，"
                      f"设计水平年实际可达到的效果需由独立的效果计算得出，"
                      f"详见防治效益分析与六项指标复核表。"),
                evidence_refs=["field.derived.target.weighted_comprehensive_target"],
                source_rule_refs=["standard.gb_50433_2018.section_3"],
                assertion_class=AssertionClass.TARGET_VALUE,
                paragraph_id="narr.evaluation.targets",
            ))

    return NarrativeBlock(
        section_id="sec.evaluation",
        title="项目水土保持评价",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_EVAL.template_id,
        template_version=TEMPLATE_SPEC_EVAL.template_version,
        normative_basis=TEMPLATE_SPEC_EVAL.normative_basis,
        quality_findings=ev.findings,
    )


# ── sec.evaluation.earthwork_balance (3.2 土石方平衡评价) ────

def render_earthwork_balance(facts: dict, derived: dict, triggered: set[str],
                             ledger=None, context=None, **kwargs) -> NarrativeBlock:
    """渲染 3.2 土石方平衡评价"""
    SEC = "sec.evaluation.earthwork_balance"
    ev = SectionEvidence(SEC, facts, derived, ledger=ledger, context=context)

    exc = ev.quantity("field.fact.earthwork.excavation")
    fill = ev.quantity("field.fact.earthwork.fill")
    reuse = ev.quantity("field.fact.earthwork.self_reuse")
    comp_reuse = ev.quantity("field.fact.earthwork.comprehensive_reuse")
    spoil = ev.quantity("field.fact.earthwork.spoil")
    borrow = ev.quantity("field.fact.earthwork.borrow")
    borrow_type = ev.text("field.fact.earthwork.borrow_source_type",
                          severity=Severity.WARN)
    topsoil_vol = ev.quantity("field.fact.topsoil.stripable_volume")

    paragraphs: list[NarrativeParagraph] = []

    # ── 段 1: 挖填利用复述 ──
    core = [exc, fill, reuse, comp_reuse, spoil]
    if ev.all_present(*core):
        # 利用率只在挖方 > 0 时有定义; 挖方为 0 时不做除法, 也不写"—%"
        if exc.value:
            reuse_pct = f"{reuse.value / exc.value * 100:.0f}%"
            pct_clause = f"（占挖方总量的{reuse_pct}）"
        else:
            pct_clause = "（挖方总量为 0，利用率不适用）"
        paragraphs.append(NarrativeParagraph(
            text=(f"本项目挖方总量{exc.display()}，填方总量{fill.display()}，"
                  f"场内自行利用{reuse.display()}{pct_clause}，"
                  f"综合利用{comp_reuse.display()}，弃方{spoil.display()}。"),
            evidence_refs=[v.field_id for v in core],
            source_rule_refs=["rule.template_2026.section_3"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.evaluation.earthwork_balance.volumes",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            *core,
            lead="土石方平衡缺少基础数据，无法作平衡评价",
            source_rule_refs=["rule.template_2026.section_3"],
            paragraph_id="narr.evaluation.earthwork_balance.volumes",
        ))

    # ── 段 2: 借方 ──
    # 关键区分: 借方**没填**≠借方为 0。前者不能写成"无需外借土石方"。
    if not borrow.is_present:
        paragraphs.append(ev.gap_paragraph(
            borrow,
            lead="借方数据缺失，无法判断本项目是否需要外借土石方",
            source_rule_refs=["rule.template_2026.section_3"],
            paragraph_id="narr.evaluation.earthwork_balance.borrow",
        ))
    elif borrow.value:
        src = (f"，来源为{borrow_type.display()}" if borrow_type.is_present
               else "，借方来源尚未填写")
        paragraphs.append(NarrativeParagraph(
            text=f"本项目借方{borrow.display()}{src}。",
            evidence_refs=["field.fact.earthwork.borrow",
                           "field.fact.earthwork.borrow_source_type"],
            source_rule_refs=["rule.template_2026.section_3"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.evaluation.earthwork_balance.borrow",
        ))
    else:
        paragraphs.append(NarrativeParagraph(
            text="本项目填报借方量为 0，即不从项目区外借取土石方。",
            evidence_refs=["field.fact.earthwork.borrow"],
            source_rule_refs=["rule.template_2026.section_3"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.evaluation.earthwork_balance.borrow",
        ))

    # ── 段 3: 表土 ──
    # 只复述可剥离量。表土去向是方案安排, 不能由这个数字推出"全部用于绿化覆土"。
    if topsoil_vol.is_present:
        paragraphs.append(NarrativeParagraph(
            text=(f"可剥离表土{topsoil_vol.display()}，"
                  f"其保存与回覆利用安排见表土资源保护与利用章节。"),
            evidence_refs=["field.fact.topsoil.stripable_volume",
                           "sec.topsoil.balance"],
            source_rule_refs=["rule.template_2026.section_3"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.evaluation.earthwork_balance.topsoil",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            topsoil_vol,
            lead="可剥离表土量缺失",
            source_rule_refs=["rule.template_2026.section_3"],
            paragraph_id="narr.evaluation.earthwork_balance.topsoil",
        ))

    if "ob.evaluation.dual_source_earthwork_justification" in triggered:
        paragraphs.append(NarrativeParagraph(
            text=("本项目同时存在借方与弃方，已触发多来源土石方论证义务，"
                  "须分别说明各来源的弃方去向与借方来源。"),
            evidence_refs=["ob.evaluation.dual_source_earthwork_justification"],
            source_rule_refs=["standard.gb_50433_2018.section_3"],
            assertion_class=AssertionClass.NORMATIVE_REQUIREMENT,
            paragraph_id="narr.evaluation.earthwork_balance.dual_source",
        ))

    # ── 段 4: 平衡评价结论 ──
    paragraphs.append(ev.judgment(
        "综上，本项目土石方平衡合理，弃方有明确去向，借方有可靠来源，"
        "表土剥离利用方案可行。详见土石方平衡表。",
        target_ref=SEC,
        pending_text=(
            "土石方平衡是否合理、弃方去向与借方来源是否落实、表土剥离利用方案"
            "是否可行，须由水土保持工程师对照土石方平衡表与现场资料复核确认；"
            "复核记录形成前，本节不作上述结论。"),
        evidence_refs=["art.table.earthwork_balance", SEC],
        source_rule_refs=["standard.gb_50433_2018.section_3"],
        paragraph_id="narr.evaluation.earthwork_balance.conclusion",
        remediation="核对土石方平衡表与弃借方落实材料后录入复核记录",
    ))

    return NarrativeBlock(
        section_id=SEC,
        title="土石方平衡评价",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_EARTHWORK.template_id,
        template_version=TEMPLATE_SPEC_EARTHWORK.template_version,
        normative_basis=TEMPLATE_SPEC_EARTHWORK.normative_basis,
        quality_findings=ev.findings,
    )
