"""
report_quality.py — CPSWC P0-01 报告质量旁路契约

任务来源: docs/report_production_plan/03_P0_TASKS.md P0-01
接口依据: docs/report_production_plan/04_CONTRACTS_AND_ACCEPTANCE.md 第 1、2 节
批准记录: implementation/DECISION_LOG.md 条目 002 (RFC-RP-001 v1.0, A 批)

本模块解决一件事: **`RenderStatus.FULL` 只代表"有连续可读文字", 不代表专业完成。**
它在渲染状态之外, 独立记录五类互不替代的状态:

    ValueState    值能不能读到          (PRESENT 不代表来源已核验)
    Applicability 内容/义务适不适用      (NOT_APPLICABLE 必须能说明判定依据)
    ContentState  适用内容写完了没有    (COMPLETE 不代表技术正确)
    EvidenceState 证据够不够            (READY 不代表专业复核通过)
    ReviewState   人工复核了没有        (CONFIRMED 绑定具体输入 hash)

边界 (硬约束, 不得放宽):
  - 本模块是**校验器**, 不是第五套项目事实真源。只存引用、状态和诊断,
    不复制可编辑的项目数值, 不提供任何写回 facts 的接口。
  - 本模块不证明任何自然语言命题为真。程序 PASS 只表示特定机器检查通过。
  - 本模块不自行创建 EvidenceRecord / ReviewRecord, 不填写任何人名。
    legacy 数据没有质量输入时一律 UNASSESSED / UNVERIFIED, 不自动升级。
  - `is_submittable` 只能由正式导出门禁 (P0-08) 写入。本模块永远返回 None。
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field as dc_field
from enum import Enum
from typing import Any, Iterable, Sequence

SCHEMA_VERSION = "report_quality_v0a"

# A 批临时输入指纹 schema。见 DECISION_LOG 条目 004:
# 它不是 fact_snapshot_hash, 也不是 generation_input_hash,
# P0-06 实施后由 generation_input_hash 取代, 届时本标识标 legacy。
QUALITY_INPUT_HASH_SCHEMA_VERSION = "quality_input_v0a"


# ============================================================
# 1. 五类状态 (04 文档第 1 节)
# ============================================================

class ValueState(str, Enum):
    PRESENT = "PRESENT"                # 值可读取 — 不代表来源已核验
    MISSING = "MISSING"                # 缺键 / None / 空白 / Quantity 空值
    INVALID = "INVALID"                # NaN / inf / 非法数字 / 未登记单位
    CONFLICT = "CONFLICT"              # 多来源不一致, 未确认取哪个
    NOT_APPLICABLE = "NOT_APPLICABLE"  # 本项目不适用 — 需理由与证据


class Applicability(str, Enum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class ContentState(str, Enum):
    UNASSESSED = "UNASSESSED"   # 未做内容审查 — 默认值
    MISSING = "MISSING"         # 适用但没有内容
    DRAFTED = "DRAFTED"         # 有文字, 未对照内容规范
    INCOMPLETE = "INCOMPLETE"   # 对照规范后确认有缺项
    COMPLETE = "COMPLETE"       # 规范叶子要求齐全 — 不代表技术正确


class EvidenceState(str, Enum):
    UNASSESSED = "UNASSESSED"
    MISSING = "MISSING"
    UNVERIFIED = "UNVERIFIED"   # 有来源记录但未核验
    READY = "READY"
    INVALID = "INVALID"


class ReviewState(str, Enum):
    NOT_REVIEWED = "NOT_REVIEWED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    STALE = "STALE"             # 曾确认, 但绑定的输入已变化


class Severity(str, Enum):
    BLOCK = "BLOCK"
    WARN = "WARN"
    INFO = "INFO"


class Stage(str, Enum):
    INPUT = "INPUT"
    EVALUATION = "EVALUATION"
    RENDER = "RENDER"
    POSTFLIGHT = "POSTFLIGHT"


# ============================================================
# 2. 稳定诊断码 (04 文档第 2 节)
# ============================================================
# 诊断码是**检查标识**, 不是法规条款 id。不得注册进 rule.* 命名空间。

STABLE_FINDING_CODES: frozenset[str] = frozenset({
    "VALUE_MISSING",
    "VALUE_INVALID",
    "INPUT_CONFLICT",
    "CONDITION_UNKNOWN",
    "CONDITION_ERROR",
    "SOURCE_UNVERIFIED",
    "ASSERTION_UNSUPPORTED",
    "TARGET_EFFECT_CONFLATED",
    "DERIVED_STALE",
    "DEMO_ASSUMPTION",
    "PROFILE_UNSUPPORTED",
    "CONTENT_INCOMPLETE",
    "ARTIFACT_MISSING",
    "RENDER_FAILED",
    "REVIEW_STALE",
    "FORMAL_CAPABILITY_INCOMPLETE",
    # 04 文档建议码之外的新增项。理由: A 批验收发现"只校验 hash 不校验记录完整性"
    # 会让空壳记录 (无审核人/时间/证据引用) 直接升级为专业确认。
    # 该情形既不是 REVIEW_STALE (记录没过期), 也不是 SOURCE_UNVERIFIED (不是来源问题),
    # 需要独立可定位的码。新增已记入 DECISION_LOG 条目 006。
    "REVIEW_INCOMPLETE",
})


@dataclass
class QualityFinding:
    """单条质量诊断。只存引用与状态, 不复制项目数值。"""
    code: str
    severity: Severity
    message: str
    target_ref: str = ""
    missing_input_refs: list[str] = dc_field(default_factory=list)
    evidence_refs: list[str] = dc_field(default_factory=list)
    remediation: str = ""
    stage: Stage = Stage.RENDER

    def __post_init__(self) -> None:
        if self.code not in STABLE_FINDING_CODES:
            raise ValueError(
                f"未登记的诊断码 {self.code!r}。"
                f"新增诊断码必须先加入 STABLE_FINDING_CODES, 不允许运行时拼接。"
            )
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity)
        if isinstance(self.stage, str):
            self.stage = Stage(self.stage)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "target_ref": self.target_ref,
            "missing_input_refs": list(self.missing_input_refs),
            "evidence_refs": list(self.evidence_refs),
            "remediation": self.remediation,
            "stage": self.stage.value,
        }


# ============================================================
# 3. 值状态解析 (验收 S01—S04)
# ============================================================

class ValueKind(str, Enum):
    """调用方声明它期望读到什么。单位要求由 kind 决定, 不做全局猜测。"""
    QUANTITY = "QUANTITY"   # {value, unit} — 必须有已登记单位
    NUMBER = "NUMBER"       # 无量纲数 (如土壤流失控制比)
    TEXT = "TEXT"
    LIST = "LIST"
    BOOL = "BOOL"
    ANY = "ANY"


# 已登记单位。样本中实际出现的单位 + 常见工程单位。
# 未登记单位不静默通过 —— 报 VALUE_INVALID, 由人决定是补登记还是改数据。
KNOWN_UNITS: frozenset[str] = frozenset({
    "hm²", "m²", "km²", "亩",
    "m³", "万m³",
    "元", "万元", "元/m²", "元/m³", "元/t",
    "m", "km", "cm",
    "t", "万t", "kg", "t/(km²·a)", "t/(hm²·a)",
    "%", "‰",
    "座", "项", "株", "个", "处", "台", "套", "根", "块",
    "a", "年", "月", "d", "h",
})

# 显示符号, 不是业务值。出现在输入里只说明"制表时写了不适用",
# 不能当数值参与运算 (04 文档第 1 节)。
_DISPLAY_NA_TOKENS: frozenset[str] = frozenset({"/", "／", "—", "-", "N/A", "n/a"})


class Provenance(str, Enum):
    """这个值是从哪一层读到的。P0-04 用它区分三套 derived 口径。"""
    UNKNOWN = "UNKNOWN"
    PROJECT_FACT = "PROJECT_FACT"                  # 项目填报事实
    CALCULATED = "CALCULATED"                      # 本次计算成功的派生量 (权威)
    PRE_STORED_DERIVED = "PRE_STORED_DERIVED"      # 样本/输入里预存的派生量 (外部结果)
    ENRICHED_VIEW = "ENRICHED_VIEW"                # 运行时 enrich 出来的消费视图
    STALE_HISTORICAL = "STALE_HISTORICAL"          # 当前计算失败, 只能作历史展示


@dataclass
class ResolvedValue:
    """一次读值的结果。state 与 value 分离, 调用方不得绕过 state 直接用 value。"""
    field_id: str
    state: ValueState
    value: Any = None
    unit: str = ""
    raw: Any = None
    note: str = ""
    is_empty_container: bool = False

    # ---- P0-04 来源信息 ----
    provenance: Provenance = Provenance.UNKNOWN
    """值取自哪一层。CALCULATED 是权威读值; PRE_STORED_DERIVED 是外部结果, 不伪装成重算"""

    stale_value: Any = None
    """当前计算失败时, 旧 pre-stored 值放这里**只作历史展示**, 不得当作有效值"""

    conflicts: list[tuple[str, Any]] = dc_field(default_factory=list)
    """(来源标识, 值) 列表。多来源不一致时非空, state 为 CONFLICT"""

    @property
    def is_present(self) -> bool:
        return self.state is ValueState.PRESENT

    @property
    def is_usable_number(self) -> bool:
        return self.state is ValueState.PRESENT and isinstance(self.value, (int, float)) \
            and not isinstance(self.value, bool)

    def display(self, missing: str = "（缺）") -> str:
        """给正文用的显示串。缺失**不显示为 0**, 也不伪装成"—"这种像数据的符号。"""
        if self.state is ValueState.MISSING:
            return missing
        if self.state is ValueState.INVALID:
            return "（数据非法）"
        if self.state is ValueState.CONFLICT:
            return "（来源冲突）"
        if self.state is ValueState.NOT_APPLICABLE:
            return "（不适用）"
        if isinstance(self.value, list):
            return "、".join(str(x) for x in self.value)
        if self.unit:
            return f"{self.value} {self.unit}".strip()
        return str(self.value)

    @property
    def is_authoritative(self) -> bool:
        """是不是本次计算得出的权威读值。外部结果 / 历史值都不是。"""
        return self.provenance in (Provenance.CALCULATED, Provenance.PROJECT_FACT)

    def to_finding(self, *, severity: Severity = Severity.BLOCK,
                   stage: Stage = Stage.RENDER,
                   remediation: str = "") -> QualityFinding | None:
        """把非 PRESENT 的状态转成诊断。PRESENT 返回 None。"""
        if self.state is ValueState.PRESENT:
            return None
        if self.state is ValueState.CONFLICT:
            sources = "、".join(f"{src}={val!r}" for src, val in self.conflicts)
            return QualityFinding(
                code="INPUT_CONFLICT",
                severity=severity,
                message=f"{self.field_id}: 多来源取值不一致 ({sources})",
                target_ref=self.field_id,
                remediation=remediation or "确认各来源语义后指定权威来源, 不得静默择一",
                stage=stage,
            )
        code = {
            ValueState.MISSING: "VALUE_MISSING",
            ValueState.INVALID: "VALUE_INVALID",
            ValueState.CONFLICT: "INPUT_CONFLICT",
            ValueState.NOT_APPLICABLE: "VALUE_MISSING",
        }[self.state]
        msg = f"{self.field_id}: {self.state.value}"
        if self.note:
            msg = f"{msg} — {self.note}"
        return QualityFinding(
            code=code,
            severity=severity,
            message=msg,
            target_ref=self.field_id,
            missing_input_refs=[self.field_id] if self.state is ValueState.MISSING else [],
            remediation=remediation or f"补充或核实 {self.field_id}",
            stage=stage,
        )


def _is_bad_number(x: Any) -> bool:
    return isinstance(x, float) and (math.isnan(x) or math.isinf(x))


def resolve_value(field_id: str, raw: Any, *,
                  kind: ValueKind = ValueKind.ANY,
                  present: bool = True) -> ResolvedValue:
    """
    按 04 文档第 1 节的边界规则判定单个值的 ValueState。

    参数:
      raw:     原始读值
      kind:    调用方期望的类型。决定是否强制单位。
      present: 键是否真的存在 (区分"缺键"与"键存在但值为 None")。
               两者都判 MISSING, 但 note 不同, 便于定位。

    关键规则 (不得放宽):
      - 缺键 / None / 空白字符串  → MISSING, **不转 0**
      - 数值 0 / 布尔 False       → PRESENT
      - 空 list                   → PRESENT + is_empty_container
                                    (容器已提供 ≠ 已完整调查且无涉及)
      - {"value": None}           → MISSING
      - NaN / inf / 非法数字串    → INVALID
      - QUANTITY 缺单位/未登记单位 → INVALID
      - "/" 等显示符号            → NOT_APPLICABLE (需理由与证据)
    """
    if not present:
        return ResolvedValue(field_id, ValueState.MISSING, raw=raw, note="键不存在")

    if raw is None:
        return ResolvedValue(field_id, ValueState.MISSING, raw=raw, note="值为 None")

    # 显示符号
    if isinstance(raw, str) and raw.strip() in _DISPLAY_NA_TOKENS:
        return ResolvedValue(
            field_id, ValueState.NOT_APPLICABLE, raw=raw,
            note=f"输入为显示符号 {raw.strip()!r}, 不是业务值; 判定不适用须另有理由与证据")

    if isinstance(raw, str) and not raw.strip():
        return ResolvedValue(field_id, ValueState.MISSING, raw=raw, note="空白字符串")

    # Quantity {value, unit}
    if isinstance(raw, dict) and "value" in raw:
        inner = raw.get("value")
        unit = raw.get("unit", "")
        if inner is None:
            return ResolvedValue(field_id, ValueState.MISSING, unit=unit or "", raw=raw,
                                 note="Quantity 的 value 为 None")
        if isinstance(inner, str):
            if not inner.strip():
                return ResolvedValue(field_id, ValueState.MISSING, unit=unit or "", raw=raw,
                                     note="Quantity 的 value 为空白")
            try:
                inner = float(inner)
            except ValueError:
                return ResolvedValue(field_id, ValueState.INVALID, unit=unit or "", raw=raw,
                                     note=f"value 不是合法数字: {raw.get('value')!r}")
        if _is_bad_number(inner):
            return ResolvedValue(field_id, ValueState.INVALID, unit=unit or "", raw=raw,
                                 note="value 为 NaN 或 inf, 禁止参与计算")
        if kind is ValueKind.QUANTITY:
            if not isinstance(unit, str) or not unit.strip():
                return ResolvedValue(field_id, ValueState.INVALID, raw=raw,
                                     note="按 QUANTITY 读取但缺单位; 无单位的数不得直接比较")
            if unit not in KNOWN_UNITS:
                return ResolvedValue(field_id, ValueState.INVALID, unit=unit, raw=raw,
                                     note=f"未登记单位 {unit!r}; 需先登记单位再使用")
        return ResolvedValue(field_id, ValueState.PRESENT, value=inner,
                             unit=unit if isinstance(unit, str) else "", raw=raw)

    # 裸 bool 先于数值判断 (bool 是 int 的子类)
    if isinstance(raw, bool):
        return ResolvedValue(field_id, ValueState.PRESENT, value=raw, raw=raw)

    if isinstance(raw, (int, float)):
        if _is_bad_number(raw):
            return ResolvedValue(field_id, ValueState.INVALID, raw=raw,
                                 note="NaN 或 inf, 禁止参与计算")
        if kind is ValueKind.QUANTITY:
            return ResolvedValue(field_id, ValueState.INVALID, raw=raw,
                                 note="按 QUANTITY 读取但输入是裸数字, 无单位")
        return ResolvedValue(field_id, ValueState.PRESENT, value=raw, raw=raw)

    if isinstance(raw, (list, tuple)):
        return ResolvedValue(field_id, ValueState.PRESENT, value=list(raw), raw=raw,
                             is_empty_container=(len(raw) == 0),
                             note="空容器: 已提供列表, 但不能独自证明已完整调查且无涉及"
                                  if len(raw) == 0 else "")

    if isinstance(raw, dict):
        return ResolvedValue(field_id, ValueState.PRESENT, value=raw, raw=raw,
                             is_empty_container=(len(raw) == 0))

    return ResolvedValue(field_id, ValueState.PRESENT, value=raw, raw=raw)


def resolve_from(source: dict, field_id: str, *,
                 kind: ValueKind = ValueKind.ANY) -> ResolvedValue:
    """从一个 flat dict 中读值并判定状态。区分缺键与 None。"""
    return resolve_value(field_id, source.get(field_id),
                         kind=kind, present=(field_id in source))


# ============================================================
# 4. 质量输入 sidecar (04 文档第 2 节)
# ============================================================
# 这些是**只读输入**: 由受控人工流程产生, 本模块只解析和校验, 从不创建。

@dataclass
class EvidenceRecord:
    evidence_id: str
    target_refs: list[str] = dc_field(default_factory=list)
    source_kind: str = ""              # project_document / structured_input / calculation / normative_source
    source_document_ref: str = ""
    locator: str = ""                  # 页/表/图/字段位置 — 不编造页码
    content_sha256: str = ""
    source_version: str = ""
    verification_status: str = "UNVERIFIED"   # UNVERIFIED / VERIFIED / REJECTED
    verified_by: str = ""              # 真实确认记录; 系统不得自行填写人名
    verified_at: str = ""

    @property
    def is_verified(self) -> bool:
        """自称 VERIFIED 但没有原始证据定位/版本对应的, 不算已核验 (04 文档第 2 节)。"""
        if self.verification_status != "VERIFIED":
            return False
        if not self.verified_by or not self.verified_at:
            return False
        if not self.content_sha256 and not self.locator:
            return False
        return True


@dataclass
class ReviewRecord:
    review_id: str
    target_refs: list[str] = dc_field(default_factory=list)
    input_hash: str = ""
    verdict: str = "NEEDS_REVIEW"      # CONFIRMED / REJECTED / NEEDS_REVIEW
    reviewer_ref: str = ""
    evidence_refs: list[str] = dc_field(default_factory=list)
    reviewed_at: str = ""

    def completeness_gaps(self, known_evidence: dict | None = None) -> list[str]:
        """
        列出这条记录缺什么, 才谈得上是一次**专业确认**。

        只校验记录本身是否成形, **不**声称验证了签名真实性或身份 ——
        那需要受控的人工流程, 软件不代签 (04 文档第 2 节)。

        缺任何一项, CONFIRMED 都不得生效:
          审核人引用 / 复核时间 / 证据引用 / 证据引用可解析 / 输入指纹
        """
        gaps: list[str] = []
        if not (self.reviewer_ref or "").strip():
            gaps.append("缺审核人引用 reviewer_ref")
        if not (self.reviewed_at or "").strip():
            gaps.append("缺复核时间 reviewed_at")
        if not self.evidence_refs:
            gaps.append("缺证据引用 evidence_refs")
        elif known_evidence is not None:
            dangling = [r for r in self.evidence_refs if r not in known_evidence]
            if dangling:
                gaps.append(f"证据引用无法解析: {'、'.join(dangling)}")
            rejected = [r for r in self.evidence_refs
                        if r in known_evidence
                        and known_evidence[r].verification_status == "REJECTED"]
            if rejected:
                gaps.append(f"所引证据已被否决: {'、'.join(rejected)}")
        if not (self.input_hash or "").strip():
            gaps.append("缺输入指纹 input_hash, 无法判断结论对应哪一版输入")
        return gaps


@dataclass
class AssuranceRecord:
    assurance_id: str                  # 复用 as.*
    state: str = "REQUIRED"            # REQUIRED / PROVIDED — 沿用既有两态
    evidence_refs: list[str] = dc_field(default_factory=list)
    input_hash: str = ""
    confirmed_by: str = ""
    confirmed_at: str = ""


@dataclass
class QualityInputs:
    schema_version: str = SCHEMA_VERSION
    evidence_records: list[EvidenceRecord] = dc_field(default_factory=list)
    review_records: list[ReviewRecord] = dc_field(default_factory=list)
    assurance_records: list[AssuranceRecord] = dc_field(default_factory=list)
    is_legacy: bool = False            # True = 输入里没有 quality_inputs 节

    @classmethod
    def from_raw(cls, raw: Any) -> "QualityInputs":
        """
        legacy 适配: 输入没有 quality_inputs 时返回空集合并标 is_legacy。

        **不创造记录**, 不补 verified_by, 不把旧数据升级为已审核 (验收 S05)。
        """
        if not isinstance(raw, dict) or not raw:
            return cls(is_legacy=True)

        def _mk(cls_, items, id_key):
            out = []
            for it in (items or []):
                if not isinstance(it, dict):
                    continue
                kwargs = {k: v for k, v in it.items()
                          if k in cls_.__dataclass_fields__}
                if not kwargs.get(id_key):
                    continue
                out.append(cls_(**kwargs))
            return out

        return cls(
            schema_version=raw.get("schema_version") or SCHEMA_VERSION,
            evidence_records=_mk(EvidenceRecord, raw.get("evidence_records"), "evidence_id"),
            review_records=_mk(ReviewRecord, raw.get("review_records"), "review_id"),
            assurance_records=_mk(AssuranceRecord, raw.get("assurance_records"), "assurance_id"),
            is_legacy=False,
        )


# ============================================================
# 5. 输入指纹 (A 批临时; 见 DECISION_LOG 条目 004)
# ============================================================

def _canonicalize(obj: Any) -> Any:
    """规范化用于 hash 的结构。NaN/inf 不参与语义 hash, 换成显式标记。"""
    if isinstance(obj, dict):
        return {str(k): _canonicalize(obj[k]) for k in sorted(obj, key=str)}
    if isinstance(obj, (list, tuple)):
        return [_canonicalize(x) for x in obj]      # 有序数组保留顺序
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return "__INVALID_NUMBER__"
    if isinstance(obj, (int, float, str)) or obj is None:
        return obj
    return str(obj)


def compute_quality_input_hash(facts: dict | None,
                               derived: dict | None = None) -> str:
    """
    对本次消费的 facts + derived 算一个规范化指纹, 供复核记录绑定 (验收 N08)。

    **边界**: 这不是 fact_snapshot_hash, 也不是 generation_input_hash。
    它不写入冻结包、不进 manifest、不对外承诺稳定性。P0-06 实施后由
    generation_input_hash 取代 (DECISION_LOG 条目 004)。
    """
    payload = {
        "schema": QUALITY_INPUT_HASH_SCHEMA_VERSION,
        "facts": _canonicalize(facts or {}),
        "derived": _canonicalize(derived or {}),
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ============================================================
# 6. 复核账本: 判断"这条结论现在还成立吗"
# ============================================================

class ReviewLedger:
    """
    解析 ReviewRecord, 回答"某个 target 现在的复核状态"。

    两道关卡, 缺一不可:

      1. **绑定**: 记录的 input_hash 与当前输入指纹一致。不一致 → STALE;
         当前指纹未知 (调用方没传) → 也按 STALE, 因为无法证明仍然适用。
      2. **完整**: 记录本身是一次成形的确认 —— 有审核人引用、复核时间、
         可解析的证据引用。只对上 hash 的空壳记录 → NEEDS_REVIEW + REVIEW_INCOMPLETE。

    只有 1 和 2 同时满足的 CONFIRMED 才算"当前有效的专业确认"。
    REJECTED 方向保守, 不要求完整性 —— 否决一个结论不需要额外证据。
    """

    def __init__(self, quality_inputs: QualityInputs | None = None,
                 current_input_hash: str | None = None) -> None:
        self.inputs = quality_inputs or QualityInputs(is_legacy=True)
        self.current_input_hash = current_input_hash
        self._evidence: dict[str, EvidenceRecord] = {
            e.evidence_id: e for e in self.inputs.evidence_records
        }

    def evidence_state(self, target_ref: str) -> EvidenceState:
        recs = [e for e in self.inputs.evidence_records if target_ref in e.target_refs]
        if not recs:
            return EvidenceState.UNASSESSED if self.inputs.is_legacy else EvidenceState.MISSING
        if any(e.verification_status == "REJECTED" for e in recs):
            return EvidenceState.INVALID
        if all(e.is_verified for e in recs):
            return EvidenceState.READY
        return EvidenceState.UNVERIFIED

    def review_state(self, target_ref: str) -> tuple[ReviewState, ReviewRecord | None]:
        recs = [r for r in self.inputs.review_records if target_ref in r.target_refs]
        if not recs:
            return ReviewState.NOT_REVIEWED, None
        # REJECTED 优先, 且不要求记录完整 (否定方向保守)
        for r in recs:
            if r.verdict == "REJECTED" and self._binds_current(r):
                return ReviewState.REJECTED, r
        for r in recs:
            if r.verdict == "CONFIRMED" and self._binds_current(r):
                if self.completeness_gaps(r):
                    continue          # 空壳记录不得升级为专业确认
                return ReviewState.CONFIRMED, r
        # 绑定当前输入但记录不完整 → 待复核, 不是失效
        incomplete = [r for r in recs
                      if r.verdict == "CONFIRMED" and self._binds_current(r)]
        if incomplete:
            return ReviewState.NEEDS_REVIEW, incomplete[0]
        # 有明确结论但绑定到别的输入 → 失效
        if any(r.verdict in ("CONFIRMED", "REJECTED") for r in recs):
            return ReviewState.STALE, recs[0]
        return ReviewState.NEEDS_REVIEW, recs[0]

    def completeness_gaps(self, r: ReviewRecord) -> list[str]:
        return r.completeness_gaps(self._evidence)

    def _binds_current(self, r: ReviewRecord) -> bool:
        if not self.current_input_hash:
            return False
        return bool(r.input_hash) and r.input_hash == self.current_input_hash

    def supports_judgment(self, target_ref: str) -> bool:
        """
        本项目"合理/可行/符合"类判断是否有当前有效的专业确认。

        要求: 复核记录 CONFIRMED 且绑定当前输入指纹。
        仅引用标准、仅有一张表、义务已触发, 都**不满足** (04 文档第 5 节)。
        """
        state, _ = self.review_state(target_ref)
        return state is ReviewState.CONFIRMED

    def stale_finding(self, target_ref: str) -> QualityFinding | None:
        """复核记录本身有问题时的诊断 (失效 / 不完整)。没问题返回 None。"""
        state, rec = self.review_state(target_ref)
        if state is ReviewState.STALE:
            return QualityFinding(
                code="REVIEW_STALE",
                severity=Severity.BLOCK,
                message=(f"{target_ref}: 已有复核记录 {rec.review_id if rec else '?'} "
                         f"绑定的输入指纹与当前不一致, 旧结论不再适用"),
                target_ref=target_ref,
                remediation="对当前输入重新复核后再引用该结论",
                stage=Stage.EVALUATION,
            )
        if state is ReviewState.NEEDS_REVIEW and rec is not None \
                and rec.verdict == "CONFIRMED":
            gaps = self.completeness_gaps(rec)
            if gaps:
                return QualityFinding(
                    code="REVIEW_INCOMPLETE",
                    severity=Severity.BLOCK,
                    message=(f"{target_ref}: 复核记录 {rec.review_id} 标为 CONFIRMED "
                             f"但记录不完整 ({'; '.join(gaps)}), 不作专业确认"),
                    target_ref=target_ref,
                    evidence_refs=list(rec.evidence_refs),
                    remediation="补齐审核人引用、复核时间与可解析的证据引用",
                    stage=Stage.EVALUATION,
                )
        return None


def ledger_from_snapshot(snapshot: dict | None) -> ReviewLedger:
    """从 snapshot dict 取质量输入与当前输入指纹, 构造复核账本。

    放在本模块而不是 narrative 层: 表格投影也要用它判断"某个效果值是否
    已被确认", 而表格层不应该依赖 narrative 层。

    P0-06 起**优先绑定 generation_input_hash** —— 它覆盖事实、来源层、规则、
    registry、模板与计算实现版本, 才是"这版结论对应哪一版输入"的正确判据。
    `quality_input_hash` 是 A 批的临时指纹 (DECISION_LOG 条目 004), 仅在
    snapshot 尚未带 generation_input_hash 时兜底。
    """
    snap = snapshot or {}
    qi = QualityInputs.from_raw(snap.get("quality_inputs"))
    h = snap.get("generation_input_hash") or snap.get("quality_input_hash")
    if not h:
        h = compute_quality_input_hash(snap.get("_original_facts") or {},
                                       snap.get("derived_fields") or {})
    return ReviewLedger(qi, h)


# ============================================================
# 7. 内容规范 (最小形态; 完整清单属 P0-05)
# ============================================================

@dataclass
class ContentRequirement:
    """一条内容规范要求。叶子要求才进覆盖率分母 (父标题引言不算成果)。"""
    requirement_id: str
    section_id: str
    title: str = ""
    is_leaf: bool = True
    applicability_condition_ref: str | None = None
    required_artifact_refs: list[str] = dc_field(default_factory=list)
    implemented: bool = True    # False = 模板尚未实现, 仍计入分母 (验收 R02)


@dataclass
class ContentRequirementSet:
    schema_version: str = SCHEMA_VERSION
    source_ref: str = ""        # 规范来源定位; 未核验时留空并由调用方标 UNVERIFIED_PROFILE
    verified: bool = False
    requirements: list[ContentRequirement] = dc_field(default_factory=list)
    display_numbers: dict[str, str] = dc_field(default_factory=dict)
    """{stable_id: display_number} —— 显示位置晚绑定, 不写进 stable id"""
    migrations: list[dict] = dc_field(default_factory=list)
    absorbed: list[dict] = dc_field(default_factory=list)

    def leaves_for(self, section_id: str) -> list[ContentRequirement]:
        return [r for r in self.requirements if r.section_id == section_id and r.is_leaf]

    @property
    def leaf_count(self) -> int:
        return sum(1 for r in self.requirements if r.is_leaf)

    def display_number_of(self, stable_id: str) -> str | None:
        return self.display_numbers.get(stable_id)

    def absorbed_entry(self, stable_id: str) -> dict | None:
        for a in self.absorbed:
            if a.get("stable_id") == stable_id:
                return a
        return None


def load_content_requirements(
        species: str = "报告书",
        path: Any = None) -> ContentRequirementSet | None:
    """
    加载 governance/ReportContentRequirements_v1.yaml。

    找不到文件或 species 不匹配时返回 None —— 调用方据此保持
    coverage_state="unknown" (验收 Q02), **不得**自己编一份清单顶上。
    """
    import yaml
    from cpswc.paths import GOVERNANCE_DIR

    p = path or (GOVERNANCE_DIR / "ReportContentRequirements_v1.yaml")
    if not p.exists():
        return None
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if species and doc.get("species") and doc["species"] != species:
        return None

    src = doc.get("source") or {}
    reqs: list[ContentRequirement] = []
    display: dict[str, str] = {}
    for r in (doc.get("requirements") or []):
        if not isinstance(r, dict):
            continue
        stable_id = r.get("stable_id") or ""
        if stable_id:
            display[stable_id] = str(r.get("display_number", ""))
        reqs.append(ContentRequirement(
            requirement_id=r["id"],
            section_id=stable_id,
            title=str(r.get("title", "")),
            is_leaf=bool(r.get("is_leaf")),
            applicability_condition_ref=(r.get("condition_note")
                                         if r.get("applicability") == "conditional"
                                         else None),
            implemented=bool(r.get("implemented")),
        ))
    for a in (doc.get("absorbed_stable_ids") or []):
        if isinstance(a, dict) and a.get("stable_id"):
            display[a["stable_id"]] = str(a.get("display_hint", ""))

    return ContentRequirementSet(
        schema_version=str(doc.get("schema_version") or SCHEMA_VERSION),
        source_ref=str(src.get("document_number") or ""),
        verified=(src.get("verification_status") == "VERIFIED"),
        requirements=reqs,
        display_numbers=display,
        migrations=list(doc.get("stable_id_migrations") or []),
        absorbed=list(doc.get("absorbed_stable_ids") or []),
    )


# ============================================================
# 8. 章节质量与汇总 (04 文档第 2 节)
# ============================================================

@dataclass
class SectionQuality:
    section_id: str
    requirement_refs: list[str] = dc_field(default_factory=list)
    applicability: Applicability = Applicability.UNKNOWN
    applicability_evidence_refs: list[str] = dc_field(default_factory=list)
    content_state: ContentState = ContentState.UNASSESSED
    evidence_state: EvidenceState = EvidenceState.UNASSESSED
    review_state: ReviewState = ReviewState.NOT_REVIEWED
    input_hash: str = ""
    finding_codes: list[str] = dc_field(default_factory=list)
    render_status: str = ""          # 旧 RenderStatus, 仅作对照, 不参与质量判定
    is_parent_intro: bool = False

    def to_dict(self) -> dict:
        return {
            "section_id": self.section_id,
            "requirement_refs": list(self.requirement_refs),
            "applicability": self.applicability.value,
            "applicability_evidence_refs": list(self.applicability_evidence_refs),
            "content_state": self.content_state.value,
            "evidence_state": self.evidence_state.value,
            "review_state": self.review_state.value,
            "input_hash": self.input_hash,
            "finding_codes": list(self.finding_codes),
            "render_status": self.render_status,
            "is_parent_intro": self.is_parent_intro,
        }


@dataclass
class ReportQualitySummary:
    """
    汇总必须保留分项数量, 不只给总分 (04 文档第 2 节)。

    `content_coverage` 语义:
      None  = coverage_state 为 unknown 时不给数
      float = 已完成叶子要求 / 适用叶子要求
    任何情况下都同时给出 unknown 与 unassessed 数量, 禁止只显示一个百分比。
    """
    schema_version: str = SCHEMA_VERSION
    sections: list[SectionQuality] = dc_field(default_factory=list)
    findings: list[QualityFinding] = dc_field(default_factory=list)

    # 04 文档要求的最小分项计数
    unresolved_critical_count: int = 0
    unknown_applicability_count: int = 0
    missing_artifact_count: int = 0
    unreviewed_requirement_count: int = 0
    unassessed_requirement_count: int = 0
    render_error_count: int = 0

    # 覆盖率
    coverage_state: str = "unknown"         # "unknown" | "measured"
    content_coverage: float | None = None
    applicable_leaf_count: int = 0
    complete_leaf_count: int = 0
    unimplemented_leaf_count: int = 0

    # 渲染层旧口径, 保留但重命名语义: 只表示"文字已渲染的块数"
    rendered_block_count: int = 0
    parent_intro_block_count: int = 0

    input_hash: str = ""
    input_hash_schema_version: str = QUALITY_INPUT_HASH_SCHEMA_VERSION

    # 只能由正式导出门禁 (P0-08) 写入。本模块永远留 None。
    is_submittable: bool | None = None

    @property
    def blocks(self) -> list[QualityFinding]:
        return [f for f in self.findings if f.severity is Severity.BLOCK]

    @property
    def warnings(self) -> list[QualityFinding]:
        return [f for f in self.findings if f.severity is Severity.WARN]

    def coverage_display(self) -> str:
        """给 UI / CLI 的诚实覆盖率串。无规范清单时绝不显示百分比。"""
        if self.coverage_state != "measured" or self.content_coverage is None:
            return (f"内容完成度: 未知（无内容规范清单）; "
                    f"未审查要求 {self.unassessed_requirement_count} 项")
        return (f"内容完成度: {self.content_coverage * 100:.0f}% "
                f"({self.complete_leaf_count}/{self.applicable_leaf_count} 叶子要求); "
                f"未审查 {self.unassessed_requirement_count} 项, "
                f"适用性未知 {self.unknown_applicability_count} 项, "
                f"未实现 {self.unimplemented_leaf_count} 项")

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "sections": [s.to_dict() for s in self.sections],
            "findings": [f.to_dict() for f in self.findings],
            "counts": {
                "unresolved_critical_count": self.unresolved_critical_count,
                "unknown_applicability_count": self.unknown_applicability_count,
                "missing_artifact_count": self.missing_artifact_count,
                "unreviewed_requirement_count": self.unreviewed_requirement_count,
                "unassessed_requirement_count": self.unassessed_requirement_count,
                "render_error_count": self.render_error_count,
            },
            "coverage": {
                "coverage_state": self.coverage_state,
                "content_coverage": self.content_coverage,
                "applicable_leaf_count": self.applicable_leaf_count,
                "complete_leaf_count": self.complete_leaf_count,
                "unimplemented_leaf_count": self.unimplemented_leaf_count,
            },
            "render_layer": {
                "rendered_block_count": self.rendered_block_count,
                "parent_intro_block_count": self.parent_intro_block_count,
                "note": "rendered_block_count 只表示文字已渲染的块数, 不代表专业完成",
            },
            "input_hash": self.input_hash,
            "input_hash_schema_version": self.input_hash_schema_version,
            "is_submittable": self.is_submittable,
        }


# ============================================================
# 9. 汇总算法
# ============================================================

def _block_attr(block: Any, name: str, default: Any = None) -> Any:
    return getattr(block, name, default)


def evaluate_report_quality(
    context: Any,
    narrative: Any = None,
    tables: Any = None,
    content_requirements: ContentRequirementSet | None = None,
    inventory: Any = None,
    *,
    quality_inputs: QualityInputs | None = None,
    current_input_hash: str | None = None,
    obligation_applicability: dict[str, Applicability] | None = None,
) -> ReportQualitySummary:
    """
    把渲染结果 + 内容规范 + 质量输入汇总成 ReportQualitySummary。

    参数:
      context:  A 批传 RuntimeSnapshot 的 dict 形式; B 批 (P0-04) 改为 BuildContext。
      narrative: NarrativeProjectionResult 或 blocks 序列。
      tables / inventory: C 批 (P0-07) 接入; A 批传 None 时只记未评估。
      content_requirements: 没有清单时 coverage_state 保持 "unknown" (验收 Q02)。

    硬约束:
      - 父标题引言不计成果 (验收 Q01)
      - 缺清单不输出 100%
      - is_submittable 永远返回 None
    """
    summary = ReportQualitySummary()
    summary.input_hash = current_input_hash or ""
    ledger = ReviewLedger(quality_inputs, current_input_hash)

    blocks: Sequence[Any] = []
    if narrative is not None:
        blocks = list(getattr(narrative, "blocks", narrative) or [])

    # ---- 逐 block 汇总 ----
    for b in blocks:
        section_id = _block_attr(b, "section_id", "")
        render_status = _block_attr(b, "render_status", "")
        render_status = getattr(render_status, "value", render_status) or ""
        content_role = _block_attr(b, "content_role", None)
        role_value = getattr(content_role, "value", content_role) or "LEAF_CONTENT"
        is_parent = (role_value == "PARENT_INTRO")

        sq = SectionQuality(section_id=section_id,
                            render_status=str(render_status),
                            input_hash=current_input_hash or "",
                            is_parent_intro=is_parent)

        # 适用性: 优先取 block 自己声明的; 否则从渲染状态保守推断
        declared = _block_attr(b, "applicability", None)
        if isinstance(declared, Applicability):
            sq.applicability = declared
        elif render_status == "not_applicable":
            sq.applicability = Applicability.NOT_APPLICABLE
        elif render_status in ("full", "skeleton"):
            sq.applicability = Applicability.APPLICABLE
        else:
            sq.applicability = Applicability.UNKNOWN

        block_findings = list(_block_attr(b, "quality_findings", []) or [])
        summary.findings.extend(block_findings)
        sq.finding_codes = sorted({f.code for f in block_findings})

        # 内容状态: 渲染出文字只到 DRAFTED, 绝不因为 FULL 就 COMPLETE
        if is_parent:
            sq.content_state = ContentState.DRAFTED
            summary.parent_intro_block_count += 1
        elif render_status == "full":
            sq.content_state = ContentState.DRAFTED
        elif render_status == "skeleton":
            sq.content_state = ContentState.MISSING
        elif render_status == "not_applicable":
            sq.content_state = ContentState.UNASSESSED
        else:
            sq.content_state = ContentState.UNASSESSED

        if str(render_status) == "full":
            summary.rendered_block_count += 1

        sq.evidence_state = ledger.evidence_state(section_id)
        sq.review_state, _ = ledger.review_state(section_id)
        stale = ledger.stale_finding(section_id)
        if stale is not None:
            summary.findings.append(stale)
            sq.finding_codes = sorted(set(sq.finding_codes) | {stale.code})

        if any(w for w in (_block_attr(b, "block_warnings", []) or [])
               if "Template error" in str(w)):
            summary.render_error_count += 1
            summary.findings.append(QualityFinding(
                code="RENDER_FAILED",
                severity=Severity.BLOCK,
                message=f"{section_id}: 模板渲染失败",
                target_ref=section_id,
                remediation="修复模板或补齐其依赖输入",
                stage=Stage.RENDER,
            ))

        summary.sections.append(sq)

    # ---- 投影层全局告警 ----
    for w in (getattr(narrative, "projection_warnings", []) or []):
        if "Template error" in str(w):
            continue  # 已在 block 层计数
    for f in (getattr(narrative, "quality_findings", []) or []):
        summary.findings.append(f)

    # ---- 义务适用性未知 ----
    if obligation_applicability:
        for ob_id, ap in obligation_applicability.items():
            if ap is Applicability.UNKNOWN:
                summary.unknown_applicability_count += 1
                summary.findings.append(QualityFinding(
                    code="CONDITION_UNKNOWN",
                    severity=Severity.WARN,
                    message=f"{ob_id}: 适用性无法确定, 未计入不涉及",
                    target_ref=ob_id,
                    remediation="补齐该义务触发条件依赖的输入",
                    stage=Stage.EVALUATION,
                ))

    summary.unknown_applicability_count += sum(
        1 for s in summary.sections if s.applicability is Applicability.UNKNOWN)

    # ---- 覆盖率 ----
    if content_requirements is None or not content_requirements.requirements:
        summary.coverage_state = "unknown"
        summary.content_coverage = None
        # 分母未知时, 每个已渲染叶子块都算"未审查要求"
        summary.unassessed_requirement_count = sum(
            1 for s in summary.sections if not s.is_parent_intro)
        summary.findings.append(QualityFinding(
            code="CONTENT_INCOMPLETE",
            severity=Severity.WARN,
            message="没有可用的内容规范清单, 无法计算内容完成度",
            target_ref="",
            remediation="提供适用报告种类的内容规范清单 (P0-05)",
            stage=Stage.EVALUATION,
        ))
    else:
        summary.coverage_state = "measured"
        by_section = {s.section_id: s for s in summary.sections}
        applicable = 0
        complete = 0
        for req in content_requirements.requirements:
            if not req.is_leaf:
                continue
            sq = by_section.get(req.section_id)
            # 适用性未知的要求不能从分母里删掉
            if sq is not None and sq.applicability is Applicability.NOT_APPLICABLE:
                continue
            applicable += 1
            if sq is not None:
                sq.requirement_refs = sorted(set(sq.requirement_refs) | {req.requirement_id})
            if not req.implemented:
                summary.unimplemented_leaf_count += 1
                summary.findings.append(QualityFinding(
                    code="CONTENT_INCOMPLETE",
                    severity=Severity.BLOCK,
                    message=f"{req.requirement_id}: 必需内容尚未实现 ({req.title or req.section_id})",
                    target_ref=req.section_id,
                    remediation="实现该内容或说明其不适用的依据",
                    stage=Stage.RENDER,
                ))
                continue
            # 已完成的判据: 有对应块、不是父引言、且内容状态达到 COMPLETE。
            # A 批没有任何机制能把内容判到 COMPLETE, 因此这里恒为 0 ——
            # 这是诚实的结果, 不是 bug。P0-05 接入规范清单后才可能 > 0。
            if sq is not None and not sq.is_parent_intro \
                    and sq.content_state is ContentState.COMPLETE:
                complete += 1
            else:
                summary.findings.append(QualityFinding(
                    code="CONTENT_INCOMPLETE",
                    severity=Severity.WARN,
                    message=f"{req.requirement_id}: 未确认完成 ({req.title or req.section_id})",
                    target_ref=req.section_id,
                    remediation="对照内容规范确认该要求是否写完",
                    stage=Stage.EVALUATION,
                ))
        summary.applicable_leaf_count = applicable
        summary.complete_leaf_count = complete
        summary.content_coverage = (complete / applicable) if applicable else None
        if applicable == 0:
            summary.coverage_state = "unknown"
        summary.unassessed_requirement_count = applicable - complete

    # ---- 制品台账 (C 批 P0-07 接入) ----
    if inventory is not None:
        for entry in (getattr(inventory, "entries", inventory) or []):
            status = getattr(entry, "status", None) or (
                entry.get("status") if isinstance(entry, dict) else None)
            if status in ("MISSING", "FAILED"):
                summary.missing_artifact_count += 1

    # ---- 复核计数 ----
    summary.unreviewed_requirement_count = sum(
        1 for s in summary.sections
        if s.review_state in (ReviewState.NOT_REVIEWED, ReviewState.NEEDS_REVIEW,
                              ReviewState.STALE))

    summary.unresolved_critical_count = len(summary.blocks)

    # is_submittable 保持 None: 只有正式门禁能判定 (P0-08)
    summary.is_submittable = None
    return summary


__all__ = [
    "SCHEMA_VERSION", "QUALITY_INPUT_HASH_SCHEMA_VERSION",
    "ValueState", "Applicability", "ContentState", "EvidenceState", "ReviewState",
    "Severity", "Stage", "ValueKind", "KNOWN_UNITS", "STABLE_FINDING_CODES",
    "QualityFinding", "ResolvedValue", "Provenance", "resolve_value", "resolve_from",
    "EvidenceRecord", "ReviewRecord", "AssuranceRecord", "QualityInputs",
    "compute_quality_input_hash", "ReviewLedger", "ledger_from_snapshot",
    "ContentRequirement", "ContentRequirementSet", "load_content_requirements",
    "SectionQuality", "ReportQualitySummary", "evaluate_report_quality",
]
