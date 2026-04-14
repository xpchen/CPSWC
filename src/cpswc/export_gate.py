"""
export_gate.py — CPSWC v0 Export Gate

宪法必做项 #15: ProtectedBoundaryPolicy_v0 + 导出 gate

宪法公式:
  ExportGate = g(ObligationSet, AssuranceState, SubmissionLifecycle)

本模块职责:
  1. 加载 ProtectedBoundaryPolicy_v0.yaml
  2. 检查 CRITICAL fields 是否有值
  3. 检查 required assurances 状态
  4. 检查 SubmissionLifecycle.freeze_state
  5. 返回 PASS / BLOCK / WARN + 原因列表

完成判定:
  - 有独立 policy config ✓ (governance/ProtectedBoundaryPolicy_v0.yaml)
  - export gate 真正读取 ObligationSet + AssuranceState + SubmissionLifecycle ✓
  - 导出前能 PASS / BLOCK / WARN ✓
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from cpswc.paths import GOVERNANCE_DIR, REGISTRIES_DIR


# ============================================================
# Result types
# ============================================================

@dataclass
class GateFinding:
    """单条 gate 检查结果"""
    rule_id: str
    action: str          # "BLOCK" | "WARN" | "INFO"
    message: str
    target_ref: str = ""  # 具体 field_id / ob_id / as_id


@dataclass
class ExportGateResult:
    """Export gate 检查完整结果"""
    verdict: str          # "PASS" | "BLOCK" | "WARN"
    findings: list[GateFinding] = field(default_factory=list)

    @property
    def blocks(self) -> list[GateFinding]:
        return [f for f in self.findings if f.action == "BLOCK"]

    @property
    def warnings(self) -> list[GateFinding]:
        return [f for f in self.findings if f.action == "WARN"]

    @property
    def summary(self) -> str:
        return (f"ExportGate: {self.verdict} "
                f"({len(self.blocks)} block, {len(self.warnings)} warn)")


# ============================================================
# Policy loader
# ============================================================

def _load_policy() -> dict:
    """加载 ProtectedBoundaryPolicy_v0.yaml"""
    path = GOVERNANCE_DIR / "ProtectedBoundaryPolicy_v0.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_fir() -> dict:
    """加载 FieldIdentityRegistry_v0.yaml"""
    path = REGISTRIES_DIR / "FieldIdentityRegistry_v0.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================
# Gate checks
# ============================================================

def _check_critical_fields(
    unified: dict, fir: dict, findings: list[GateFinding]
) -> None:
    """GATE_001: 所有 CRITICAL 字段必须有值"""
    fields = fir.get("fields") or {}
    for field_id, fdef in fields.items():
        if not isinstance(fdef, dict):
            continue
        if fdef.get("protection_level") != "CRITICAL":
            continue
        # placeholder 字段不检查 (它们可能是 v1 预留)
        if fdef.get("placeholder") is True:
            continue

        value = unified.get(field_id)
        if value is None:
            findings.append(GateFinding(
                rule_id="GATE_001",
                action="BLOCK",
                message=f"CRITICAL 字段 {field_id} 缺失",
                target_ref=field_id,
            ))


def _check_assurances(
    required_assurances: list[str],
    assurance_state: dict,
    policy: dict,
    findings: list[GateFinding],
) -> None:
    """GATE_003: required assurances 检查"""
    enforcement = policy.get("assurance_enforcement") or {}

    for as_id in required_assurances:
        provided = assurance_state.get(as_id, False)
        if provided:
            continue

        # 查 policy 里的 gate 行为
        as_policy = enforcement.get(as_id) or {}
        gate_action = as_policy.get("gate", "WARN")

        # v0: assurance 录入机制未实现, 降级为 WARN
        effective_action = "WARN"  # v0 hardcode

        findings.append(GateFinding(
            rule_id="GATE_003",
            action=effective_action,
            message=f"Assurance {as_id} 未提供 (v0: WARN)",
            target_ref=as_id,
        ))


def _check_lifecycle(
    lifecycle: dict | None,
    findings: list[GateFinding],
) -> None:
    """GATE_004: lifecycle freeze check"""
    if lifecycle is None:
        return

    freeze_state = "unfrozen"
    if isinstance(lifecycle, dict):
        freeze_state = lifecycle.get("freeze_state", "unfrozen")
    elif hasattr(lifecycle, "freeze_state"):
        freeze_state = lifecycle.freeze_state

    if freeze_state != "frozen":
        findings.append(GateFinding(
            rule_id="GATE_004",
            action="WARN",
            message=f"SubmissionLifecycle.freeze_state={freeze_state}, 建议冻结后再导出",
        ))


# ============================================================
# Public API
# ============================================================

def check_export_readiness(
    snapshot: dict,
    *,
    assurance_state: dict | None = None,
) -> ExportGateResult:
    """
    检查 snapshot 是否满足导出条件。

    参数:
      snapshot: RuntimeSnapshot 的 dict 形式 (含 _original_facts 等)
      assurance_state: {as_id: bool} 映射 (v0 默认全 False)

    返回:
      ExportGateResult (verdict = PASS / BLOCK / WARN)
    """
    policy = _load_policy()
    fir = _load_fir()

    facts = snapshot.get("_original_facts") or {}
    derived = snapshot.get("derived_fields") or {}
    # pre-stored derived from sample (runtime Step 4 也合并这一层)
    pre_derived = snapshot.get("_pre_stored_derived") or {}
    # unified: facts + pre_derived + runtime derived (与 runtime Step 4 口径一致)
    unified: dict = {}
    unified.update(facts)
    unified.update(pre_derived)
    unified.update(derived)

    required_assurances = snapshot.get("required_assurances") or []
    lifecycle = snapshot.get("submission_lifecycle")
    assurance_state = assurance_state or {}

    findings: list[GateFinding] = []

    # GATE_001: CRITICAL fields (检查 facts + derived 合并后的 unified)
    _check_critical_fields(unified, fir, findings)

    # GATE_003: Assurances
    _check_assurances(required_assurances, assurance_state, policy, findings)

    # GATE_004: Lifecycle
    _check_lifecycle(lifecycle, findings)

    # Determine verdict
    has_block = any(f.action == "BLOCK" for f in findings)
    has_warn = any(f.action == "WARN" for f in findings)

    if has_block:
        verdict = "BLOCK"
    elif has_warn:
        verdict = "WARN"
    else:
        verdict = "PASS"

    return ExportGateResult(verdict=verdict, findings=findings)
