"""
narrative/evidence.py — CPSWC P0-03 模板取值与断言准入辅助

任务来源: docs/report_production_plan/03_P0_TASKS.md P0-03
接口依据: 04_CONTRACTS_AND_ACCEPTANCE.md 第 1、5 节

模板过去用 `_v(facts, key, default="—")` 取值: 缺失、0、非法值全被压成一个短横线,
于是空输入也能拼出"平衡合理、来源可靠"的完整段落。本模块把这条路堵死:

  1. 取值一律经 ResolvedValue, 缺失就是缺失, **不显示成像数据的"—"**, 不转 0。
  2. 每次缺失/非法都登记一条稳定诊断码的 QualityFinding, 能定位到 field id。
  3. 本项目"合理/可行/符合"类判断走 judgment(), 没有当前有效复核记录就
     降级为"待复核"说明 —— 不是把结论藏进脚注, 是根本不作这个结论。

本模块不做的事:
  - 不给文本"可信度打分", 不调用任何模型。
  - 不替工程师下技术结论, 不创造复核记录。
"""

from __future__ import annotations

from typing import Any, Iterable

from cpswc.narrative.contract import AssertionClass, NarrativeParagraph
from cpswc.report_quality import (
    QualityFinding, ResolvedValue, ReviewLedger, Severity, Stage,
    ValueKind, ValueState, resolve_value,
)

# 缺失值在正文里的统一写法。不用"—": 短横线看起来像一个已填写的数据。
MISSING_MARK = "（缺）"

# 本节存在这些 BLOCK 级诊断时, **任何**肯定结论都不得输出 —— 即使有复核记录。
#
# 为什么需要这条: 复核记录是必要条件, 不是通行证。A 批验收复现过一个反例 ——
# "目标 95 / 效果 80 / 另五项效果缺失" 的输入配上一条匹配当前输入的复核记录,
# 正文里同时出现"该指标未达到目标值"和"各项防治目标可以实现"。
# 章节级的一次确认不能自动授权该节所有肯定判断。
_DATA_BLOCKER_CODES: frozenset[str] = frozenset({
    "VALUE_MISSING", "VALUE_INVALID", "INPUT_CONFLICT",
    "CONDITION_UNKNOWN", "CONDITION_ERROR",
    "DERIVED_STALE", "TARGET_EFFECT_CONFLATED", "CONTENT_INCOMPLETE",
    "REVIEW_STALE", "REVIEW_INCOMPLETE",
})


class SectionEvidence:
    """
    一个 section 渲染期间的取值账本。

    用法:
        ev = SectionEvidence("sec.evaluation.earthwork_balance", facts, derived)
        exc = ev.quantity("field.fact.earthwork.excavation")
        if ev.all_present(exc, fill):
            ...复述...
        else:
            paragraphs.append(ev.gap_paragraph(...))
    """

    def __init__(self, section_id: str, facts: dict | None = None,
                 derived: dict | None = None, *,
                 ledger: ReviewLedger | None = None,
                 severity: Severity = Severity.BLOCK,
                 context: Any = None) -> None:
        self.section_id = section_id
        self.facts = facts or {}
        self.derived = derived or {}
        self.ledger = ledger or ReviewLedger()
        self.default_severity = severity
        self.findings: list[QualityFinding] = []
        self._seen: dict[str, ResolvedValue] = {}

        # P0-04: 有 BuildContext 时一律走它 —— 模板因此免费拿到来源、冲突、
        # 失效派生量、演示假设和 FIR 单位校验, 不用每个模板自己判一遍。
        # 没有 context 时退回 facts/derived 两个 dict (A 批的老路径), 便于
        # 单元测试直接喂夹具。
        self.context = context

    # ---------- 取值 ----------

    def _read(self, field_id: str, kind: ValueKind,
              severity: Severity | None = None) -> ResolvedValue:
        if field_id in self._seen:
            return self._seen[field_id]
        if self.context is not None:
            rv = self.context.resolve(field_id, kind)
        elif field_id in self.derived:
            rv = resolve_value(field_id, self.derived[field_id], kind=kind, present=True)
        elif field_id in self.facts:
            rv = resolve_value(field_id, self.facts[field_id], kind=kind, present=True)
        else:
            rv = resolve_value(field_id, None, kind=kind, present=False)
        if rv.state is not ValueState.PRESENT:
            f = rv.to_finding(severity=severity or self.default_severity,
                              stage=Stage.RENDER)
            if f is not None:
                f.target_ref = f.target_ref or field_id
                self.findings.append(f)
        self._seen[field_id] = rv
        return rv

    def quantity(self, field_id: str, severity: Severity | None = None) -> ResolvedValue:
        """读一个带单位的量。无单位或未登记单位判 INVALID。"""
        return self._read(field_id, ValueKind.QUANTITY, severity)

    def number(self, field_id: str, severity: Severity | None = None) -> ResolvedValue:
        """读一个无量纲数 (如土壤流失控制比)。"""
        return self._read(field_id, ValueKind.NUMBER, severity)

    def text(self, field_id: str, severity: Severity | None = None) -> ResolvedValue:
        return self._read(field_id, ValueKind.TEXT, severity)

    def items(self, field_id: str, severity: Severity | None = None) -> ResolvedValue:
        """读一个列表。空列表是 PRESENT + is_empty_container, 不等于"已核查无涉及"。"""
        return self._read(field_id, ValueKind.LIST, severity)

    def raw(self, field_id: str, severity: Severity | None = None) -> ResolvedValue:
        return self._read(field_id, ValueKind.ANY, severity)

    # ---------- 判定 ----------

    @staticmethod
    def all_present(*values: ResolvedValue) -> bool:
        return all(v.state is ValueState.PRESENT for v in values)

    @staticmethod
    def missing_refs(*values: ResolvedValue) -> list[str]:
        return [v.field_id for v in values if v.state is not ValueState.PRESENT]

    def add_finding(self, code: str, message: str, *,
                    severity: Severity | None = None,
                    target_ref: str = "",
                    missing_input_refs: Iterable[str] = (),
                    remediation: str = "",
                    stage: Stage = Stage.RENDER) -> QualityFinding:
        f = QualityFinding(
            code=code,
            severity=severity or self.default_severity,
            message=message,
            target_ref=target_ref or self.section_id,
            missing_input_refs=list(missing_input_refs),
            remediation=remediation,
            stage=stage,
        )
        self.findings.append(f)
        return f

    # ---------- 段落构造 ----------

    def gap_paragraph(self, *values: ResolvedValue,
                      lead: str = "本节所需资料尚不完整",
                      paragraph_id: str | None = None,
                      source_rule_refs: Iterable[str] = (),
                      extra_refs: Iterable[str] = ()) -> NarrativeParagraph:
        """
        如实说明缺口的段落。它替代过去"数值缺失但结论照给"的写法。

        缺口段落**不是**占位符: 它列出具体缺哪些登记字段, 供编制人定位补资料。
        """
        missing = [v.field_id for v in values if v.state is ValueState.MISSING]
        invalid = [v.field_id for v in values if v.state is ValueState.INVALID]
        conflict = [v.field_id for v in values if v.state is ValueState.CONFLICT]

        parts = [lead + "："]
        if missing:
            parts.append(f"缺少 {len(missing)} 项必需输入（{'、'.join(missing)}）；")
        if invalid:
            parts.append(f"{len(invalid)} 项输入非法或单位未登记（{'、'.join(invalid)}）；")
        if conflict:
            parts.append(f"{len(conflict)} 项输入存在来源冲突（{'、'.join(conflict)}）；")
        parts.append("本节在上述资料补齐并经复核前不作结论。")

        return NarrativeParagraph(
            text="".join(parts),
            evidence_refs=list(dict.fromkeys(
                [v.field_id for v in values] + list(extra_refs))) or [self.section_id],
            source_rule_refs=list(source_rule_refs),
            assertion_class=AssertionClass.GAP_STATEMENT,
            unresolved_placeholders=missing + invalid + conflict,
            paragraph_id=paragraph_id,
        )

    def blocking_findings(self, target_ref: str) -> list[QualityFinding]:
        """
        列出会阻断本次肯定结论的已有诊断。

        两类算数:
          1. **数据类** BLOCK 诊断 —— 缺值、非法值、来源冲突、适用性未知、
             目标/效果混淆、复核失效或不完整。这类问题出现在本节任何位置,
             都说明这一节的事实基础还没站稳, 结论无从谈起。
          2. 指向**同一 target** 的断言类诊断 —— 同一个判断自己已经被判缺支持。
             指向别的 target 的断言类诊断不算 (同一节里的两个子判断互相独立,
             例如敏感区的"重点防治区核查"与"12 类逐项排查")。
        """
        out = []
        for f in self.findings:
            if f.severity is not Severity.BLOCK:
                continue
            if f.code in _DATA_BLOCKER_CODES:
                out.append(f)
            elif f.target_ref == target_ref:
                out.append(f)
        return out

    def judgment(self, text: str, *,
                 target_ref: str = "",
                 pending_text: str,
                 evidence_refs: Iterable[str] = (),
                 source_rule_refs: Iterable[str] = (),
                 paragraph_id: str | None = None,
                 remediation: str = "",
                 preconditions: Iterable[tuple[bool, str]] = ()) -> NarrativeParagraph:
        """
        本项目合理性/可行性/符合性判断的唯一出口。

        输出 text 需要**同时**满足三个条件, 缺一不可:

          1. 有当前有效的复核记录 (CONFIRMED + 绑定当前输入指纹 + 记录完整);
          2. 本节没有未解决的数据类 BLOCK 诊断 (见 blocking_findings);
          3. 调用方声明的领域前提全部成立 (preconditions)。

        任一不满足 → 输出 pending_text, 标 GAP_STATEMENT, 并登记诊断。

        第 2、3 条是 A 批验收后加的。复核记录是**必要条件, 不是通行证**:
        它证明"有人对这版输入下过结论", 不能替代数据完整性、适用性、数值
        有效性和比较结果的检查。技术正确性仍由专业复核承担, 软件不代签。

        参数:
          preconditions: (是否成立, 说明) 的序列。说明会进入待复核文字与诊断,
                         因此要写成读者能据以补救的话。
        """
        ref = target_ref or self.section_id
        unmet = [why for ok, why in preconditions if not ok]
        blockers = self.blocking_findings(ref)
        has_review = self.ledger.supports_judgment(ref)

        if has_review and not unmet and not blockers:
            _, rec = self.ledger.review_state(ref)
            return NarrativeParagraph(
                text=text,
                evidence_refs=list(evidence_refs) or [ref],
                source_rule_refs=list(source_rule_refs),
                assertion_class=AssertionClass.PROJECT_JUDGMENT,
                review_refs=[rec.review_id] if rec else [],
                paragraph_id=paragraph_id,
            )

        # 走到这里说明结论不成立。把"为什么不成立"说清楚, 而不是笼统待复核。
        reasons: list[str] = []
        if not has_review:
            review_finding = self.ledger.stale_finding(ref)
            if review_finding is not None:
                self.findings.append(review_finding)
                reasons.append("已有复核记录不适用于当前输入或记录不完整")
            else:
                self.add_finding(
                    "ASSERTION_UNSUPPORTED",
                    f"{ref}: 无绑定当前输入的专业复核记录, 不作本项目合规/合理性判断",
                    severity=Severity.BLOCK,
                    target_ref=ref,
                    remediation=remediation or "由水土保持工程师复核后录入复核记录",
                    stage=Stage.EVALUATION,
                )
                reasons.append("尚无绑定当前输入的专业复核记录")
        if unmet:
            self.add_finding(
                "ASSERTION_UNSUPPORTED",
                f"{ref}: 肯定结论的前提未满足 —— {'; '.join(unmet)}",
                severity=Severity.BLOCK,
                target_ref=ref,
                remediation=remediation or "补齐上述前提后重新判定",
                stage=Stage.EVALUATION,
            )
            reasons.extend(unmet)
        if blockers:
            codes = sorted({f.code for f in blockers})
            reasons.append(
                f"本节尚有 {len(blockers)} 项未解决的阻断性问题（{'、'.join(codes)}）")
            if has_review and not unmet:
                # 有复核记录却仍被数据问题挡住: 单独留痕, 否则会被误读成"没人复核"
                self.add_finding(
                    "ASSERTION_UNSUPPORTED",
                    f"{ref}: 已有当前输入的复核记录, 但本节仍有 {len(blockers)} 项"
                    f"未解决的阻断性问题（{'、'.join(codes)}）, 肯定结论不成立",
                    severity=Severity.BLOCK,
                    target_ref=ref,
                    remediation="先解决上述问题, 再就本节结论重新复核",
                    stage=Stage.EVALUATION,
                )

        suffix = ("（未成立的原因：" + "；".join(reasons) + "）") if reasons else ""
        return NarrativeParagraph(
            text=pending_text + suffix,
            evidence_refs=list(evidence_refs) or [ref],
            source_rule_refs=list(source_rule_refs),
            assertion_class=AssertionClass.GAP_STATEMENT,
            paragraph_id=paragraph_id,
        )


def make_ledger(snapshot: dict | None) -> ReviewLedger:
    """从 snapshot dict 构造复核账本 (实现在 report_quality, 这里保留别名)。"""
    from cpswc.report_quality import ledger_from_snapshot
    return ledger_from_snapshot(snapshot)


__all__ = ["SectionEvidence", "make_ledger", "MISSING_MARK"]
