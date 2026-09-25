"""
sec_11_conclusion — 结论 narrative template

全局收束段: 汇总项目基本情况、关键义务、必要制品、关键指标。
单 variant (default)。

P0-03 变更 (docs/report_production_plan/03_P0_TASKS.md):
  本模板原来无条件输出"编制依据充分""符合现行法律法规和技术标准要求"
  "措施布局合理""投资估算依据充分"。空输入也照样输出 —— 实测见
  implementation/P0_BASELINE.md PROBE-1。

  现在:
    - 事实复述只在值可读时给出, 读不到就说缺哪一项 (不写"—")。
    - 合规/合理性判断改走 SectionEvidence.judgment(): 没有绑定当前输入的
      专业复核记录, 就输出"待复核"说明并登记 ASSERTION_UNSUPPORTED。
    - 义务触发数、制品数只是**统计**, 不再被表述为"已满足/已编制"。

  2026-09-25 (DECISION_LOG 条目 017): 上面登记的疑点已结清。
  P0-05 核实结果: **2026 模板没有第 11 章**, 主体章止于第 10 章"水土保持管理";
  结论是综合说明的末节 **1.9**。条款引用由 section_11 改为
  `rule.template_2026.section_1_9`; 旧 ID 在 RuleRegistry 里标 RETIRED_ID 留档,
  用于解释旧快照与按"第 11 章"定位结论的历史审查意见。

  SECTION_ID 仍是 `sec.conclusion`, **不改名** (硬约束见
  ReportContentRequirements_v1.yaml)。本文件名 sec_11_conclusion.py 同样保留,
  它只是文件名, 不是 stable id。
"""
from __future__ import annotations

from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity, Stage, ValueState

SECTION_ID = "sec.conclusion"

TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_11.conclusion.v2",
    section_id=SECTION_ID,
    template_version="v2",
    template_author="cpswc_p0_03",
    normative_basis=["rule.template_2026.section_1_9"],
    supported_variants=["default"],
    input_fields=[
        "field.fact.project.name",
        "field.fact.project.industry_category",
        "field.fact.prevention.control_standard_level",
        "field.derived.investment.compensation_fee_amount",
        "field.derived.disposal_site.level_assessment",
    ],
)


def render(facts: dict, derived: dict, triggered: set[str],
           snapshot: dict | None = None, ledger=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence(SECTION_ID, facts, derived, ledger=ledger, context=context)

    name = ev.text("field.fact.project.name")
    level = ev.text("field.fact.prevention.control_standard_level")
    fee = ev.raw("field.derived.investment.compensation_fee_amount")

    paragraphs: list[NarrativeParagraph] = []

    # ── 段 1: 项目标识与防治标准等级 — 只复述, 不评价 ──
    if name.is_present:
        head = f"本方案编制对象为{name.display()}。"
        if level.is_present:
            head += f"水土流失防治标准等级为{level.display()}。"
        else:
            head += "防治标准等级尚未确定。"
        paragraphs.append(NarrativeParagraph(
            text=head,
            evidence_refs=["field.fact.project.name",
                           "field.fact.prevention.control_standard_level"],
            source_rule_refs=["rule.template_2026.section_1_9"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.conclusion.identity",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            name, level,
            lead="本节无法给出结论对象",
            source_rule_refs=["rule.template_2026.section_1_9"],
            paragraph_id="narr.conclusion.identity",
        ))

    # ── 段 2: 义务与制品统计 — 是统计口径, 不是完成度 ──
    art_count = len((snapshot or {}).get("required_artifacts") or [])
    assurance_count = len((snapshot or {}).get("required_assurances") or [])
    unknown_obs = list((snapshot or {}).get("unknown_obligations") or [])

    stat = (f"按现行规则集判定，本项目触发水土保持义务{len(triggered)}项，"
            f"据此需编制制品{art_count}项、需满足保障要求{assurance_count}项。"
            f"以上为规则触发的“要求数量”，不代表相应内容已经完成或已经提供。")
    if unknown_obs:
        stat += (f"另有{len(unknown_obs)}项义务因输入不足无法判定是否适用"
                 f"（{'、'.join(sorted(unknown_obs)[:5])}"
                 f"{' 等' if len(unknown_obs) > 5 else ''}），"
                 f"这些义务既未被认定适用，也不得按不涉及处理。")
        ev.add_finding(
            "CONDITION_UNKNOWN",
            f"{SECTION_ID}: {len(unknown_obs)} 项义务适用性未知, 结论不完整",
            severity=Severity.BLOCK,
            target_ref=SECTION_ID,
            remediation="补齐这些义务触发条件依赖的输入后重跑",
            stage=Stage.EVALUATION,
        )
    paragraphs.append(NarrativeParagraph(
        text=stat,
        evidence_refs=sorted(triggered)[:10] or [SECTION_ID],
        source_rule_refs=["rule.template_2026.section_1_9"],
        assertion_class=AssertionClass.FACT_RESTATEMENT,
        paragraph_id="narr.conclusion.obligation_stats",
    ))

    # ── 段 3: 补偿费 — 有值才写 ──
    if fee.is_present:
        paragraphs.append(NarrativeParagraph(
            text=f"水土保持补偿费计算结果为{fee.display()}万元。",
            evidence_refs=["field.derived.investment.compensation_fee_amount",
                           "cal.compensation.fee"],
            source_rule_refs=["rule.template_2026.section_1_9"],
            assertion_class=AssertionClass.ARITHMETIC,
            paragraph_id="narr.conclusion.compensation",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            fee,
            lead="水土保持补偿费尚无有效计算结果",
            source_rule_refs=["rule.template_2026.section_1_9"],
            extra_refs=["cal.compensation.fee"],
            paragraph_id="narr.conclusion.compensation",
        ))

    # ── 段 4: 弃渣场级别 — 有评定结果才写 ──
    # 没有弃渣场评定结果不一定是缺陷 (项目可能确实没有弃渣场), 降为 WARN
    disposal = ev.items("field.derived.disposal_site.level_assessment",
                        severity=Severity.WARN)
    if disposal.is_present and not disposal.is_empty_container:
        levels_desc = []
        for site in disposal.value:
            if not isinstance(site, dict):
                continue
            levels_desc.append(f"{site.get('site_id', '?')}({site.get('level', '级别未评定')})")
        high_risk_obs = sorted(ob for ob in triggered
                               if ob in ("ob.disposal_site.geology_report",
                                         "ob.disposal_site.stability_monitoring",
                                         "ob.disposal_site.video_surveillance"))
        text = (f"本项目设弃渣场{len(levels_desc)}处，级别评定结果为："
                f"{'、'.join(levels_desc)}。")
        if high_risk_obs:
            text += (f"据此触发高风险弃渣场义务{len(high_risk_obs)}项"
                     f"（{'、'.join(high_risk_obs)}），相应成果需另行编制。")
        else:
            text += "按现有评定结果未触发高风险弃渣场专项义务。"
        paragraphs.append(NarrativeParagraph(
            text=text,
            evidence_refs=["field.derived.disposal_site.level_assessment",
                           "cal.disposal_site.level_assessment"] + high_risk_obs,
            source_rule_refs=["rule.gb_51018_2014.section_5_7_1"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.conclusion.disposal_level",
        ))

    # ── 段 5: 综合结论 — 必须有当前有效的专业复核记录才敢下 ──
    paragraphs.append(ev.judgment(
        "综上，本方案各项内容符合现行法律法规和技术标准要求，"
        "水土保持措施布局合理，投资估算依据充分，建议按本方案实施。",
        target_ref=SECTION_ID,
        pending_text=(
            # 措辞刻意避开"合理/充分"等肯定短语: 这些词即使出现在疑问句里,
            # 也会被正文抽查和关键词检索误判为已下结论。
            "本方案是否符合现行法律法规和技术标准要求、措施布局是否得当、"
            "投资估算依据是否成立，须由水土保持工程师在全册资料齐备后复核确认；"
            "复核记录形成前，本节不作上述结论。"),
        evidence_refs=[SECTION_ID],
        source_rule_refs=["rule.template_2026.section_1_9"],
        paragraph_id="narr.conclusion.overall",
        remediation="全册校审后录入绑定当前输入的复核记录",
    ))

    return NarrativeBlock(
        section_id=SECTION_ID,
        title="结论",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
        quality_findings=ev.findings,
    )
