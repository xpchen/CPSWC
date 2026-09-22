#!/usr/bin/env python3
"""
narrative_projection.py — CPSWC v0.5 Narrative Projection Engine

Step 14-0: 把 RuntimeSnapshot 投影成 list[NarrativeBlock]。

逻辑:
  1. 对 pilot sections (1.1 / 5.1 / 5.2) 调用对应 template → 产出 full blocks
  2. 对其余 sections → 产出 skeleton blocks (保持骨架)
  3. 对 not_applicable sections → 产出 not_applicable blocks
  4. 返回 NarrativeProjectionResult, 含 blocks + 校验结果

使用方式:
  from cpswc.narrative.projection import project_narrative
  result = project_narrative(runtime_snapshot_dict)
  for block in result.blocks:
      print(block.section_id, block.render_status)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure specs/ is on path

from cpswc.narrative.contract import (
    AssertionClass, ContentRole, NarrativeBlock, NarrativeParagraph,
    NarrativeProjectionResult, RenderStatus,
)
from cpswc.report_quality import (
    Applicability, QualityFinding, Severity, Stage,
)
from cpswc.narrative.templates.sec_1_1_basic_info import render as render_sec_1_1
from cpswc.narrative.templates.sec_5_disposal import render_5_1, render_5_2
from cpswc.narrative.templates.sec_7_2_targets import render as render_sec_7_2
from cpswc.narrative.templates.sec_9_2_compensation import render as render_sec_9_2
from cpswc.narrative.templates.sec_2_1_2_land_earthwork import render_2_1, render_2_2
from cpswc.narrative.templates.sec_11_conclusion import render as render_sec_11
from cpswc.narrative.templates.sec_3_evaluation import (
    render_evaluation as render_sec_3,
    render_earthwork_balance as render_sec_3_2,
)
from cpswc.narrative.templates.sec_4_topsoil import (
    render_stripping as render_sec_4_1,
    render_balance as render_sec_4_2,
)
from cpswc.narrative.templates.sec_9_1_investment_summary import render as render_sec_9_1
from cpswc.narrative.templates.sec_0_overview import render as render_sec_0
from cpswc.narrative.templates.sec_2_3_climate_zoning import (
    render_climate as render_sec_2_climate,
    render_zoning as render_sec_2_zoning,
)
from cpswc.narrative.templates.sec_2_4_progress import render as render_sec_2_progress
from cpswc.narrative.templates.sec_2_5_sensitive_areas import render as render_sec_2_sensitive
from cpswc.narrative.templates.sec_3_1_site_selection import render as render_sec_3_1
from cpswc.narrative.templates.sec_6_soil_loss import (
    render_current_state as render_sec_6_1,
    render_prediction as render_sec_6_2,
)
from cpswc.narrative.templates.sec_7_3_design_horizon import render as render_sec_7_horizon
from cpswc.narrative.templates.sec_1_2_spec_sheet import render as render_sec_1_2
from cpswc.narrative.templates.sec_7_1_responsibility_range import (
    render as render_sec_7_1,
    render_by_county as render_sec_7_1_1,
)
from cpswc.narrative.templates.sec_7_5_benefit_analysis import render as render_sec_7_5
from cpswc.narrative.templates.sec_7_8_construction_schedule import render as render_sec_7_8
from cpswc.narrative.templates.sec_8_1_monitoring_scope import render as render_sec_8_1
from cpswc.narrative.templates.sec_8_3_monitoring_points import render as render_sec_8_3
from cpswc.narrative.templates.sec_8_2_monitoring_content import render as render_sec_8_2
from cpswc.narrative.templates.sec_10_management import render as render_sec_10


# ============================================================
# Template registry
# ============================================================
# key = section_id, value = render function
_PILOT_TEMPLATES: dict[str, Any] = {
    # Step 14-0 pilot
    "sec.overview": render_sec_0,
    "sec.overview.project_basic": render_sec_1_1,
    "sec.overview.spec_sheet_end": render_sec_1_2,
    "sec.disposal_site.source_and_flow": render_5_1,
    "sec.disposal_site.site_selection": render_5_2,
    # Step 14-1 batch
    "sec.soil_loss_prevention.targets": render_sec_7_2,
    "sec.investment_estimation.compensation_fee": render_sec_9_2,
    "sec.project_overview.land_occupation": render_2_1,
    "sec.project_overview.earthwork_balance": render_2_2,
    "sec.conclusion": render_sec_11,
    # Step 21 P1 batch
    "sec.evaluation": render_sec_3,
    "sec.evaluation.earthwork_balance": render_sec_3_2,
    "sec.topsoil.stripping": render_sec_4_1,
    "sec.topsoil.balance": render_sec_4_2,
    "sec.investment.summary": render_sec_9_1,
    # Step 22 batch 1+2
    "sec.project_overview.climate": render_sec_2_climate,
    "sec.project_overview.water_soil_zoning": render_sec_2_zoning,
    "sec.project_overview.progress": render_sec_2_progress,
    "sec.project_overview.sensitive_areas": render_sec_2_sensitive,
    "sec.evaluation.site_selection": render_sec_3_1,
    "sec.soil_loss_analysis.current_state": render_sec_6_1,
    "sec.soil_loss_analysis.prediction_result": render_sec_6_2,
    "sec.soil_loss_prevention.responsibility_range": render_sec_7_1,
    "sec.soil_loss_prevention.responsibility_range_by_county": render_sec_7_1_1,
    "sec.soil_loss_prevention.design_horizon": render_sec_7_horizon,
    "sec.soil_loss_prevention.benefit_analysis": render_sec_7_5,
    # v1 Facts Package 1
    "sec.soil_loss_prevention.construction_schedule": render_sec_7_8,
    "sec.monitoring.scope_and_period": render_sec_8_1,
    "sec.monitoring.contents_methods_frequency": render_sec_8_2,
    "sec.monitoring.point_layout": render_sec_8_3,
    "sec.management": render_sec_10,
}

# Parent chapter headers: section_id → 1-sentence intro text
# 轻处理: 不单独写模板, 在 projection 循环中生成 FULL block
_PARENT_INTROS: dict[str, str] = {
    "sec.project_overview":
        "本章介绍项目区自然概况、占地面积、土石方平衡及施工进度等基本情况。",
    "sec.topsoil":
        "本章论述项目表土资源的剥离、保存和回覆利用方案。",
    "sec.disposal_site":
        "本章论述项目弃渣和临时堆土的来源、去向及堆置方案。",
    "sec.soil_loss_analysis":
        "本章分析项目区水土流失现状，预测施工期新增水土流失量。",
    "sec.soil_loss_prevention":
        "本章论述水土流失防治责任范围、防治目标、措施布局及效益分析。",
    "sec.investment":
        "本章汇总水土保持工程投资估算，包括措施费、补偿费及分项明细。",
    "sec.monitoring":
        "本章论述项目水土保持监测的范围、时段、内容、方法、频次及点位布设。",
}


# ============================================================
# Section tree (reuse from document_renderer but simplified here)
# ============================================================
# 只需要 section_id 列表来知道哪些 section 存在
# conditional 映射也需要, 用于判断 not_applicable
_SECTION_CONDITIONALS: dict[str, str | None] = {
    "sec.overview": None,
    "sec.overview.project_basic": None,
    "sec.overview.spec_sheet_end": None,
    "sec.project_overview": None,
    "sec.project_overview.land_occupation": None,
    "sec.project_overview.earthwork_balance": None,
    "sec.project_overview.progress": None,
    # P0-02 D04: 敏感区说明是**常规内容**, 每个项目都要逐项排查并如实记录结果。
    # 过去挂在 ob.unavoidability.redline_conflict 上, 等于"没有红线冲突就当没这一节",
    # 把"未触发专题论证"误读成"不必说明敏感区"。专题论证仍由该义务驱动, 见
    # _SECTION_SPECIAL_TOPICS。
    "sec.project_overview.sensitive_areas": None,
    "sec.project_overview.climate": None,
    "sec.project_overview.water_soil_zoning": None,
    "sec.evaluation": None,
    # 同上: 选址选线水土保持评价是常规评价内容, 不是不可避让专题。
    "sec.evaluation.site_selection": None,
    "sec.evaluation.earthwork_balance": None,
    "sec.topsoil": None,
    "sec.topsoil.stripping": None,
    "sec.topsoil.balance": None,
    "sec.disposal_site": "ob.disposal_site.site_selection",
    "sec.disposal_site.source_and_flow": "ob.disposal_site.site_selection",
    "sec.disposal_site.site_selection": "ob.disposal_site.site_selection",
    "sec.soil_loss_analysis": None,
    "sec.soil_loss_analysis.current_state": None,
    "sec.soil_loss_analysis.prediction_result": None,
    "sec.soil_loss_prevention": None,
    "sec.soil_loss_prevention.responsibility_range": None,
    "sec.soil_loss_prevention.responsibility_range_by_county":
        "ob.sensitive_overlay.multi_admin_breakdown",
    "sec.soil_loss_prevention.targets": None,
    "sec.soil_loss_prevention.design_horizon": None,
    "sec.soil_loss_prevention.benefit_analysis": None,
    "sec.soil_loss_prevention.construction_schedule": None,
    "sec.monitoring": None,
    "sec.monitoring.scope_and_period": None,
    "sec.monitoring.contents_methods_frequency": None,
    "sec.monitoring.point_layout": None,
    "sec.investment": None,
    "sec.investment.summary": None,
    "sec.investment_estimation.compensation_fee": None,
    "sec.management": None,
    "sec.conclusion": None,
}

# 专题内容与义务的对应关系。这些**不是**整节的适用性开关, 而是节内需要
# 额外展开的专题。P0-02 只做解耦与登记; 专题本身的投影属后续阶段。
_SECTION_SPECIAL_TOPICS: dict[str, str] = {
    "sec.project_overview.sensitive_areas": "ob.unavoidability.redline_conflict",
    "sec.evaluation.site_selection": "ob.unavoidability.redline_conflict",
}


# Section titles (for skeleton blocks)
_SECTION_TITLES: dict[str, str] = {
    "sec.overview": "综合说明",
    "sec.overview.project_basic": "项目基本情况",
    "sec.overview.spec_sheet_end": "水土保持工程特性表",
    "sec.project_overview": "项目概况",
    "sec.project_overview.land_occupation": "占地面积",
    "sec.project_overview.earthwork_balance": "土石方平衡",
    "sec.project_overview.progress": "施工进度",
    "sec.project_overview.sensitive_areas": "敏感区域",
    "sec.project_overview.climate": "气候与自然概况",
    "sec.project_overview.water_soil_zoning": "水土保持区划",
    "sec.evaluation": "项目水土保持评价",
    "sec.evaluation.site_selection": "选址选线水土保持评价",
    "sec.evaluation.earthwork_balance": "土石方平衡评价",
    "sec.topsoil": "表土资源保护与利用",
    "sec.topsoil.stripping": "表土剥离",
    "sec.topsoil.balance": "表土平衡",
    "sec.disposal_site": "弃渣与临时堆土场处置",
    "sec.disposal_site.source_and_flow": "弃渣来源与流向",
    "sec.disposal_site.site_selection": "弃渣场（或临时堆土场）选址与堆置论证",
    "sec.soil_loss_analysis": "水土流失分析与预测",
    "sec.soil_loss_analysis.current_state": "水土流失现状",
    "sec.soil_loss_analysis.prediction_result": "水土流失预测",
    "sec.soil_loss_prevention": "水土流失防治",
    "sec.soil_loss_prevention.responsibility_range": "防治责任范围",
    "sec.soil_loss_prevention.responsibility_range_by_county": "分县级行政区防治责任范围",
    "sec.soil_loss_prevention.targets": "防治目标",
    "sec.soil_loss_prevention.design_horizon": "设计水平年",
    "sec.soil_loss_prevention.benefit_analysis": "效益分析",
    "sec.soil_loss_prevention.construction_schedule": "施工组织与进度安排",
    "sec.monitoring": "水土保持监测",
    "sec.monitoring.scope_and_period": "监测范围与时段",
    "sec.monitoring.contents_methods_frequency": "监测内容、方法与频次",
    "sec.monitoring.point_layout": "监测点布设",
    "sec.investment": "水土保持投资及效益分析",
    "sec.investment.summary": "投资估算汇总",
    "sec.investment_estimation.compensation_fee": "水土保持补偿费",
    "sec.management": "水土保持管理",
    "sec.conclusion": "结论",
}


# ============================================================
# Core projection
# ============================================================

def project_narrative(snapshot: dict) -> NarrativeProjectionResult:
    """
    把 RuntimeSnapshot 投影成 list[NarrativeBlock]。

    适用性三分 (P0-02):
      条件义务已触发 / 无条件      → 调模板
      条件义务**可确定地**未触发   → not_applicable
      条件义务未知                 → **skeleton + UNKNOWN**, 绝不写成"本项目不涉及"

    最后一条是本函数存在的主要理由。过去 `conditional_ob not in triggered` 把
    "未触发"和"不知道"合成一件事, 于是资料没给的章节会以"不涉及"的面貌消失。
    """
    facts = snapshot.get("_original_facts") or {}
    derived = snapshot.get("derived_fields") or {}
    triggered = set(snapshot.get("triggered_obligations") or [])
    unknown_obs = set(snapshot.get("unknown_obligations") or [])

    from cpswc.narrative.evidence import make_ledger
    ledger = make_ledger(snapshot)

    # P0-04: 若调用方给了 BuildContext 就直接用; 否则由统一视图重建一个,
    # 保证模板读到的和表格、门禁读到的是同一份 (验收 I01)。
    context = snapshot.get("_build_context")
    if context is None:
        from cpswc.snapshot_adapter import BuildContext
        context = BuildContext({"facts": facts, "derived": derived})

    blocks: list[NarrativeBlock] = []
    full_count = 0
    skeleton_count = 0
    na_count = 0
    unknown_count = 0
    warnings: list[str] = []
    findings: list[QualityFinding] = []

    for sec_id in _SECTION_CONDITIONALS:
        title = _SECTION_TITLES.get(sec_id, sec_id)
        conditional_ob = _SECTION_CONDITIONALS[sec_id]

        # 三分适用性
        if not conditional_ob:
            applicability = Applicability.APPLICABLE
        elif conditional_ob in triggered:
            applicability = Applicability.APPLICABLE
        elif conditional_ob in unknown_obs:
            applicability = Applicability.UNKNOWN
        else:
            applicability = Applicability.NOT_APPLICABLE

        if applicability is Applicability.UNKNOWN:
            f = QualityFinding(
                code="CONDITION_UNKNOWN",
                severity=Severity.BLOCK,
                message=(f"{sec_id}: 适用性取决于 {conditional_ob}, 该义务无法确定; "
                         f"本节既不能按适用渲染, 也不得写成不涉及"),
                target_ref=sec_id,
                remediation=f"补齐 {conditional_ob} 触发条件依赖的输入后重跑",
                stage=Stage.EVALUATION,
            )
            findings.append(f)
            blocks.append(NarrativeBlock(
                section_id=sec_id,
                title=title,
                render_status=RenderStatus.SKELETON,
                applicability=Applicability.UNKNOWN,
                block_warnings=[f"适用性未知: 依赖义务 {conditional_ob} 无法确定"],
                quality_findings=[f],
            ))
            skeleton_count += 1
            unknown_count += 1
            continue

        # 专题内容登记 (不控制整节适用性)
        topic_ob = _SECTION_SPECIAL_TOPICS.get(sec_id)
        topic_findings: list[QualityFinding] = []
        if topic_ob and topic_ob in unknown_obs:
            topic_findings.append(QualityFinding(
                code="CONDITION_UNKNOWN",
                severity=Severity.WARN,
                message=(f"{sec_id}: 是否需要 {topic_ob} 专题论证无法确定; "
                         f"本节常规内容照常编制, 专题部分待定"),
                target_ref=sec_id,
                remediation=f"补齐 {topic_ob} 触发条件依赖的输入",
                stage=Stage.EVALUATION,
            ))

        if sec_id in _PILOT_TEMPLATES and applicability is Applicability.APPLICABLE:
            try:
                block = _PILOT_TEMPLATES[sec_id](
                    facts=facts, derived=derived, triggered=triggered,
                    snapshot=snapshot, ledger=ledger, unknown=unknown_obs,
                    context=context)
                if block.applicability is None:
                    block.applicability = applicability
                block.quality_findings = list(block.quality_findings) + topic_findings
                findings.extend(block.quality_findings)
                blocks.append(block)
                if block.render_status == RenderStatus.FULL:
                    full_count += 1
                elif block.render_status == RenderStatus.SKELETON:
                    skeleton_count += 1
                else:
                    na_count += 1
            except Exception as e:
                warnings.append(f"Template error for {sec_id}: {e}")
                f = QualityFinding(
                    code="RENDER_FAILED",
                    severity=Severity.BLOCK,
                    message=f"{sec_id}: 模板渲染失败 — {e}",
                    target_ref=sec_id,
                    remediation="修复模板或补齐其依赖输入",
                    stage=Stage.RENDER,
                )
                findings.append(f)
                blocks.append(NarrativeBlock(
                    section_id=sec_id,
                    title=title,
                    render_status=RenderStatus.SKELETON,
                    applicability=applicability,
                    block_warnings=[f"Template error: {e}"],
                    quality_findings=[f],
                ))
                skeleton_count += 1
        elif applicability is Applicability.NOT_APPLICABLE:
            # 可确定地不适用。注意: 这只表示触发条件不成立, **不表示**已经
            # 专业核查确认"本项目完全不涉及" —— 证据状态由质量层另行判定。
            blocks.append(NarrativeBlock(
                section_id=sec_id,
                title=title,
                render_status=RenderStatus.NOT_APPLICABLE,
                applicability=Applicability.NOT_APPLICABLE,
                block_warnings=[
                    f"依据 {conditional_ob} 未触发判定不适用; 该判定未经专业核查确认"],
            ))
            na_count += 1
        elif sec_id in _PARENT_INTROS:
            # 父章节标题引言: 一句话导语, 不是一份成果。
            # content_role=PARENT_INTRO 让质量层把它排除在内容完成度之外 (验收 Q01)。
            child_refs = [
                sid for sid in _SECTION_CONDITIONALS
                if sid.startswith(sec_id + ".") and sid != sec_id
            ]
            blocks.append(NarrativeBlock(
                section_id=sec_id,
                title=title,
                render_status=RenderStatus.FULL,
                content_role=ContentRole.PARENT_INTRO,
                applicability=applicability,
                paragraphs=[NarrativeParagraph(
                    text=_PARENT_INTROS[sec_id],
                    evidence_refs=child_refs or [sec_id],
                    source_rule_refs=["rule.template_2026"],
                    assertion_class=AssertionClass.NORMATIVE_REQUIREMENT,
                    paragraph_id=f"narr.{sec_id.removeprefix('sec.')}.intro",
                )],
                variant_id="default",
                template_id="nt.parent_intro.v1",
                template_version="v1",
                normative_basis=["rule.template_2026"],
                quality_findings=topic_findings,
            ))
            findings.extend(topic_findings)
            full_count += 1
        else:
            blocks.append(NarrativeBlock(
                section_id=sec_id,
                title=title,
                render_status=RenderStatus.SKELETON,
                applicability=applicability,
                quality_findings=topic_findings,
            ))
            findings.extend(topic_findings)
            skeleton_count += 1

    result = NarrativeProjectionResult(
        blocks=blocks,
        full_count=full_count,
        skeleton_count=skeleton_count,
        not_applicable_count=na_count,
        unknown_applicability_count=unknown_count,
        quality_findings=findings,
        projection_warnings=warnings,
    )
    result.validate_all()
    return result


# ============================================================
# CLI (debug)
# ============================================================
if __name__ == "__main__":
    import json
    from pathlib import Path as P

    from cpswc.paths import SAMPLES_DIR  # type: ignore
    sample_path = P(sys.argv[1]) if len(sys.argv) >= 2 else (
        SAMPLES_DIR / "huizhou_housing_v0.json"
    )

    # We need to run the runtime first to get a snapshot with _original_facts
    from cpswc.runtime import run_project, build_snapshot_dict  # type: ignore
    with sample_path.open() as f:
        project_input = json.load(f)

    snapshot = run_project(project_input)
    snapshot_dict = build_snapshot_dict(snapshot, project_input)

    result = project_narrative(snapshot_dict)

    print(f"Blocks: {len(result.blocks)} "
          f"(full={result.full_count} skeleton={result.skeleton_count} "
          f"na={result.not_applicable_count})")
    print()

    for b in result.blocks:
        status_icon = {"full": "█", "skeleton": "░", "not_applicable": "○"}
        icon = status_icon.get(b.render_status.value, "?")
        print(f"  {icon} {b.section_id} [{b.render_status.value}]"
              f"{' variant=' + b.variant_id if b.variant_id else ''}")
        if b.render_status == RenderStatus.FULL:
            for p in b.paragraphs:
                print(f"      \"{p.text[:80]}...\"")
                print(f"      evidence: {p.evidence_refs[:3]}...")

    if result.validation_errors:
        print(f"\nValidation errors ({len(result.validation_errors)}):")
        for e in result.validation_errors:
            print(f"  ✗ {e}")
    else:
        print(f"\nValidation: ALL BLOCKS PASS")
