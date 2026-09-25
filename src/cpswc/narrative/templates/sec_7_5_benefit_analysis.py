"""
sec_7_5_benefit_analysis — 防治效益分析 narrative template

P0-03 变更 (docs/report_production_plan/03_P0_TASKS.md, 验收 N04/N05/N06):

  原实现在**只有目标值、没有任何效果计算**的情况下输出
  "各项指标可达到上述目标值要求""各项防治目标可以实现" ——
  实测见 implementation/P0_BASELINE.md PROBE-2。这是目标与效果的混淆:
  目标值是 GB/T 50434-2018 按防治标准等级查表得到的**要求**,
  它不能证明本项目能达到它自己。

  现在:
    - 目标值只作为目标复述 (AssertionClass.TARGET_VALUE)。
    - 设计效果需要独立的效果计算结果; v0 没有可信的效果管线, 因此一律
      标"待计算", 并登记 TARGET_EFFECT_CONFLATED / VALUE_MISSING 诊断。
    - 不再用 `reducible / new * 100` 称"治理比例": 两者的口径 (是否含现状
      流失、是否同期、分母是否为应治理面积) 未经确认, 这个比值不是
      "水土流失治理度"。改为如实给出两个量与其算术比值, 并写明口径未确认。
    - `min(..., 100)` 封顶已删除: 封顶会把口径错误藏起来 (03 文档 P0-03 第 7 条)。

  本模板**不**新建六率算法, 也不为通过正向测试临时造效果字段。

  2026-09-25 (DECISION_LOG 条目 017): 条款引用由 section_7 改为
  `rule.template_2026.section_9_2` —— 效益分析在 2026 模板属第 9 章的 9.2,
  不在第 7 章 (跨章迁移, 见 ReportContentRequirements_v1.yaml
  stable_id_migrations)。stable_id `sec.soil_loss_prevention.benefit_analysis`
  与本文件名均**不改**。

A 批验收后的追加修正:
  - 验收复现出"复核记录盖过已知不达标"的反例: 只要有一条匹配当前输入的复核
    记录, 正文就会在"某指标未达标、另五项无结果"的同时输出"各项防治目标可以
    实现"。现在总述的前提由 `judgment(preconditions=...)` 显式约束:
    六项效果齐全且来源已确认、且无一项低于目标, 才谈得上下结论。
  - `actual_derived` 与 `value` 一律降级为**候选效果输入**。字段名和 derivation
    文字都不证明语义 (见 DECISION_LOG 条目 005), 候选值照实保留并标注来源,
    但不进入达标比较; 只有该字段证据状态达到 READY 才参与比较。
"""
from __future__ import annotations

from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import EvidenceState, Severity, Stage

SECTION_ID = "sec.soil_loss_prevention.benefit_analysis"

TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_7_5.benefit_analysis.v2",
    section_id=SECTION_ID,
    template_version="v2",
    template_author="cpswc_p0_03",
    normative_basis=[
        "rule.template_2026.section_9_2",
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

# 六项指标的展示标签与单位。soil_loss_control_ratio 是无量纲比值, 不带 %。
INDICATOR_LABELS: tuple[tuple[str, str, str], ...] = (
    ("control_degree", "水土流失治理度", "%"),
    ("soil_loss_control_ratio", "土壤流失控制比", ""),
    ("spoil_protection_rate", "渣土防护率", "%"),
    ("topsoil_protection_rate", "表土保护率", "%"),
    ("vegetation_restoration_rate", "林草植被恢复率", "%"),
    ("vegetation_coverage_rate", "林草覆盖率", "%"),
)


def render(facts: dict, derived: dict, triggered: set[str],
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence(SECTION_ID, facts, derived, ledger=ledger, context=context)

    total_loss = ev.quantity("field.fact.prediction.total_loss")
    new_loss = ev.quantity("field.fact.prediction.new_loss")
    reducible = ev.quantity("field.fact.prediction.reducible_loss")
    total_area = ev.quantity("field.fact.land.total_area")

    paragraphs: list[NarrativeParagraph] = []

    # ── 段 1: 流失量复述 ──
    losses = [total_loss, new_loss, reducible]
    if ev.all_present(*losses):
        text = (f"预测水土流失总量{total_loss.display()}，"
                f"其中新增水土流失量{new_loss.display()}，"
                f"经采取本方案措施后可减少的流失量{reducible.display()}。")
        # 只给算术比值, 并写明它不是"水土流失治理度"
        if new_loss.value:
            ratio = reducible.value / new_loss.value * 100
            text += (f"可减少量与新增量之比为 {ratio:.1f}%。"
                     f"该比值仅为上述两个填报量的算术比，"
                     f"两者的统计口径（时段、是否含现状流失、是否同一范围）尚未确认，"
                     f"不得作为“水土流失治理度”指标值使用。")
            ev.add_finding(
                "TARGET_EFFECT_CONFLATED",
                f"{SECTION_ID}: reducible/new 比值口径未确认, 不等于水土流失治理度",
                severity=Severity.WARN,
                target_ref=SECTION_ID,
                remediation="确认两个量的包含关系与时段后, 由专项计算给出治理度",
                stage=Stage.EVALUATION,
            )
        paragraphs.append(NarrativeParagraph(
            text=text,
            evidence_refs=[v.field_id for v in losses],
            source_rule_refs=["rule.template_2026.section_9_2"],
            assertion_class=AssertionClass.ARITHMETIC,
            paragraph_id="narr.soil_loss_prevention.benefit_analysis.losses",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            *losses,
            lead="效益分析缺少流失预测数据",
            source_rule_refs=["rule.template_2026.section_9_2"],
            paragraph_id="narr.soil_loss_prevention.benefit_analysis.losses",
        ))

    # ── 段 2: 目标值 ──
    # 这里**只有目标**。目标来自 GB/T 50434-2018 按等级查表, 是要求不是成绩。
    wt = ev.raw("field.derived.target.weighted_comprehensive_target",
                severity=Severity.WARN)
    target_items: list[str] = []
    if wt.is_present and isinstance(wt.value, dict):
        for key, label, unit in INDICATOR_LABELS:
            val = wt.value.get(key)
            if val is not None:
                target_items.append(f"{label}{val}{unit}")

    if target_items:
        paragraphs.append(NarrativeParagraph(
            text=(f"按本项目防治标准等级，设计水平年各项防治指标的目标值为："
                  f"{'、'.join(target_items)}。以上为依据 GB/T 50434-2018 "
                  f"查表得到的目标要求。"),
            evidence_refs=["field.derived.target.weighted_comprehensive_target",
                           "cal.target.weighted_comprehensive"],
            source_rule_refs=["rule.gb_t_50434_2018.chapter_4"],
            assertion_class=AssertionClass.TARGET_VALUE,
            paragraph_id="narr.soil_loss_prevention.benefit_analysis.targets",
        ))

    # ── 段 3: 效果候选值 ──
    # v0 没有独立的效果计算管线。既有 derived 里的数只能当候选, 不能当成绩。
    candidates = _effect_candidates(derived, ev.ledger)
    confirmed = {k: c for k, c in candidates.items() if c["confirmed"]}
    unconfirmed = {k: c for k, c in candidates.items() if not c["confirmed"]}
    no_effect = [label for key, label, _ in INDICATOR_LABELS
                 if key not in candidates]

    shortfalls: list[str] = []
    if confirmed:
        lines = []
        for key, label, unit in INDICATOR_LABELS:
            c = confirmed.get(key)
            if c is None:
                continue
            lines.append(f"{label}{c['value']}{unit}")
            tgt = (wt.value or {}).get(key) if wt.is_present and isinstance(wt.value, dict) else None
            if tgt is not None:
                try:
                    if float(c["value"]) < float(tgt):
                        shortfalls.append(
                            f"{label}（效果 {c['value']}{unit} 低于目标 {tgt}{unit}）")
                except (TypeError, ValueError):
                    pass
        text = f"已确认来源的设计效果结果为：{'、'.join(lines)}。"
        if shortfalls:
            text += (f"其中{len(shortfalls)}项未达到目标值："
                     f"{'；'.join(shortfalls)}。未达标指标须调整措施布局后重新计算。")
            ev.add_finding(
                "ASSERTION_UNSUPPORTED",
                f"{SECTION_ID}: {len(shortfalls)} 项指标效果低于目标值, 不得表述为全部达标",
                severity=Severity.BLOCK, target_ref=SECTION_ID,
                remediation="调整措施布局并重新计算效果, 或说明不达标的处理方案",
                stage=Stage.EVALUATION)
        paragraphs.append(NarrativeParagraph(
            text=text,
            evidence_refs=[f"field.derived.target.{k}" for k in confirmed],
            source_rule_refs=["rule.gb_t_50434_2018.chapter_4"],
            assertion_class=AssertionClass.DESIGN_EFFECT,
            paragraph_id="narr.soil_loss_prevention.benefit_analysis.effects",
        ))

    if unconfirmed:
        items = []
        for key, label, unit in INDICATOR_LABELS:
            c = unconfirmed.get(key)
            if c is None:
                continue
            items.append(f"{label}{c['value']}{unit}（源自 {c['source']}）")
            ev.add_finding(
                "TARGET_EFFECT_CONFLATED",
                f"field.derived.target.{key}: 存在候选效果值但语义未确认 "
                f"(同一结构的 value 在不同指标上分别承载目标与效果), 不进入达标比较",
                severity=Severity.BLOCK,
                target_ref=f"field.derived.target.{key}",
                remediation="由水保工程师确认该值是目标、设计预测效果还是监测实测值, "
                            "并登记计算依据、时段、单位与输入绑定后录入证据记录",
                stage=Stage.INPUT)
        paragraphs.append(NarrativeParagraph(
            text=(f"既有数据中另有{len(items)}项指标的候选数值："
                  f"{'、'.join(items)}。这些数值的语义（目标值 / 设计预测效果 / "
                  f"监测实测值）、时段、口径与计算依据尚未确认，"
                  f"本轮**不**将其作为效果值参与达标判定，仅在此保留原值与来源。"),
            evidence_refs=[f"field.derived.target.{k}" for k in unconfirmed],
            source_rule_refs=["rule.gb_t_50434_2018.chapter_4"],
            assertion_class=AssertionClass.GAP_STATEMENT,
            paragraph_id="narr.soil_loss_prevention.benefit_analysis.candidates",
        ))

    if no_effect:
        ev.add_finding(
            "VALUE_MISSING",
            f"{SECTION_ID}: {len(no_effect)} 项指标无任何效果计算结果, 无法作达标判定",
            severity=Severity.BLOCK, target_ref=SECTION_ID,
            missing_input_refs=[f"field.derived.target.{k}"
                                for k, _, _ in INDICATOR_LABELS
                                if k not in candidates],
            remediation="由独立的效果计算给出设计水平年结果",
            stage=Stage.EVALUATION)
        paragraphs.append(NarrativeParagraph(
            text=(f"另有{len(no_effect)}项指标尚无任何效果计算结果"
                  f"（{'、'.join(no_effect)}）。"
                  f"目标值不能替代效果计算，六项指标复核表中相应效果列为“待计算”，"
                  f"不得按达标处理。"),
            evidence_refs=["art.table.six_indicator_review", SECTION_ID],
            source_rule_refs=["rule.gb_t_50434_2018.chapter_4"],
            assertion_class=AssertionClass.GAP_STATEMENT,
            paragraph_id="narr.soil_loss_prevention.benefit_analysis.missing_effects",
        ))

    # ── 段 4: 综合结论 ──
    # 复核记录是必要条件, 不是通行证: 下面三条前提任一不成立, 结论都不输出。
    paragraphs.append(ev.judgment(
        f"综上，本方案水土保持措施布局合理，防治责任范围"
        f"{total_area.display() if total_area.is_present else ''}"
        f"内的水土流失可得到有效控制，各项防治目标可以实现。",
        target_ref=SECTION_ID,
        pending_text=(
            "措施布局是否得当、防治责任范围内水土流失能否得到有效控制、"
            "各项防治目标能否实现，须在六项指标效果计算完成、来源确认并经"
            "水土保持工程师复核后方可判定；本节暂不作上述结论。"),
        preconditions=[
            (not no_effect,
             f"{len(no_effect)} 项指标尚无效果计算结果" if no_effect else ""),
            (not unconfirmed,
             f"{len(unconfirmed)} 项指标的候选效果值语义未确认" if unconfirmed else ""),
            (not shortfalls,
             f"{len(shortfalls)} 项指标效果低于目标值" if shortfalls else ""),
        ],
        evidence_refs=["field.fact.land.total_area", SECTION_ID],
        source_rule_refs=["rule.template_2026.section_9_2"],
        paragraph_id="narr.soil_loss_prevention.benefit_analysis.conclusion",
        remediation="完成效果计算、确认来源并复核后录入绑定当前输入的复核记录",
    ))

    return NarrativeBlock(
        section_id=SECTION_ID,
        title="防治效益分析",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
        quality_findings=ev.findings,
    )


def _effect_candidates(derived: dict, ledger) -> dict:
    """
    读取六项指标的效果**候选**值。

    返回 {key: {"value":…, "source": "actual_derived"|"value", "confirmed": bool}}。

    语义边界 (A 批验收意见):
      `field.derived.target.<k>` 这个结构里, `value` 在不同指标上分别承载
      **目标**与**效果** (control_degree 的 value 是目标, spoil_protection_rate
      的 value 看着是效果), `actual_derived` 也只是候选效果输入 ——
      **名称和 derivation 文字都不证明可信**。

    因此本函数只负责"取出候选值并说明它从哪个键来", 判断可信与否交给证据状态:
    该字段有可解析、未被否决的证据记录 (EvidenceState.READY) 才算已确认。
    """
    out: dict = {}
    for key, _, _ in INDICATOR_LABELS:
        field_id = f"field.derived.target.{key}"
        raw = derived.get(field_id)
        if not isinstance(raw, dict):
            continue
        if raw.get("actual_derived") is not None:
            value, source = raw["actual_derived"], "actual_derived"
        elif raw.get("value") is not None:
            value, source = raw["value"], "value"
        else:
            continue
        out[key] = {
            "value": value,
            "source": source,
            "confirmed": ledger.evidence_state(field_id) is EvidenceState.READY,
        }
    return out
