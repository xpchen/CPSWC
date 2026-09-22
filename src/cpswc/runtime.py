#!/usr/bin/env python3
"""
cpswc_runtime.py — CPSWC v0 Runtime Service Layer

Step 12A: 把 5 个脚本 (lint / validator / calculator_engine / registries / sample)
收成 1 个可调用的运行时, 第一次产出可冻结、可比较、可回放的 RuntimeSnapshot。

核心函数:
    run_project(project_input, *, ruleset=None, lifecycle=None) -> RuntimeSnapshot

执行顺序 (关键: calculators BEFORE obligations):
    1. 加载全部 v0 registries
    2. 读取 project_input 的 facts
    3. 运行全部 live calculators → 产出 derived fields
    4. 合并 facts + derived → unified lookup (供 obligation DSL 使用)
    5. 评估全部 obligations
    6. 收集 required artifacts / assurances
    7. 打包 RuntimeSnapshot + RuntimeManifest

设计边界:
    - 纯 Python, 不涉及 UI / web / CLI panels
    - 不做 override runtime (决议 9: v0 不消费 override)
    - 签名预留 ruleset / lifecycle 参数, 本轮走默认值

已闭项的宪法模块 (runtime 不直接执行, 但对象挂在 snapshot 上):
    - DocumentRenderer_v0 → renderers/document.py (render_report)
    - ReviewComment_v0 → review_comment.py (独立对象层, runtime 不消费)
    - ModificationReport_v0 → modification_report.py (消费 snapshot 产出 diff)
    - ConditionEngine_v0 → condition_engine.py (runtime 委托调用)
    - ProjectFactSheet_v0 → project_fact_sheet.py (挂在 RuntimeSnapshot.fact_sheet)
    - ExportGate → export_gate.py (package_builder 调用)

退出码 (CLI 模式):
    0 成功
    1 运行时错误
    2 使用错误 (输入缺失)
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import dataclass, field as dc_field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: 缺少 PyYAML — 请先 pip install pyyaml", file=sys.stderr)
    sys.exit(2)


from cpswc.paths import REGISTRIES_DIR, SAMPLES_DIR, GOVERNANCE_DIR, PROJECT_ROOT  # noqa
from cpswc.condition_engine import (  # noqa: F401 — re-export for backward compat
    ObligationResult,
    EvaluationStatus,
    evaluate_all as _evaluate_all_obligations,
)
from cpswc.report_quality import compute_quality_input_hash
from cpswc.input_hashing import (
    HASH_SCHEMA_VERSION,
    collect_input_digests,
    fact_snapshot_hash as _fact_snapshot_hash,
    generation_input_hash as _generation_input_hash,
)
from cpswc.project_fact_sheet import (  # noqa: F401
    ProjectFactSheet,
    build as _build_fact_sheet,
)

SPECS_DIR = REGISTRIES_DIR  # backward compat alias

# ============================================================
# Dataclasses
# ============================================================

@dataclass
class CalcResultSummary:
    calculator_id: str
    output_field_id: str
    value: Any
    unit: str
    status: str  # "ok" | "error"
    error_message: str | None = None


# ============================================================
# 宪法 #3: SubmissionProfile + SubmissionLifecycle
# 对应 ARCHITECTURE_DECISIONS.md 前提 B (三轴分派):
#   ObligationSet = f(ProjectSemanticGraph, SubmissionProfile)
#   ExportGate    = g(ObligationSet, AssuranceState, SubmissionLifecycle)
# ============================================================

@dataclass
class SubmissionProfile:
    """静态申报上下文 — 承载 obligation 输入。

    v0 字段:
      species: 法律物种 (报告书 / 报告表 / 整体变更报告书 / 弃渣场补充报告书)
      compilation_intent: 编制意图 (NEW / MODIFICATION / SUPPLEMENT)
      industry_category: 行业代码 (如 "29-房地产")
      ruleset: 规则集标识 (如 "v2026_gd_package")
    """
    species: str                   # 法律物种
    compilation_intent: str        # 编制意图
    industry_category: str         # 行业代码
    ruleset: str                   # 规则集


@dataclass
class SubmissionLifecycle:
    """动态申报上下文 — 承载 gate 输入, 不进入 ObligationSet 计算。

    v0 字段:
      stage: 当前阶段 (pre_submission / under_review / approved / modification)
      review_round: 审查轮次 (0 = 首次)
      freeze_state: 冻结状态 (unfrozen / frozen)
    """
    stage: str = "pre_submission"
    review_round: int = 0
    freeze_state: str = "unfrozen"


@dataclass
class RuntimeManifest:
    """本次运行包含了什么"""
    registries_loaded: list[str]
    calculators_executed: list[CalcResultSummary]
    obligations_evaluated: int
    obligations_triggered: int
    artifacts_required: int
    assurances_required: int
    ruleset: str
    lifecycle: str
    obligations_unknown: int = 0
    """适用性无法确定的义务数。**不属于 not_triggered** (P0-02)"""


@dataclass
class RuntimeSnapshot:
    """run_project() 的完整输出"""
    # 输入
    project_input_summary: dict        # project name/code/industry 等摘要
    facts_count: int
    ruleset: str
    lifecycle: str

    # Derived (calculator 产出)
    derived_fields: dict               # field_id -> value
    calculator_results: list[CalcResultSummary]

    # Obligation 解析
    triggered_obligations: list[str]
    not_triggered_obligations: list[str]
    obligation_details: list[ObligationResult]

    # 所需产出
    required_artifacts: list[str]
    required_assurances: list[str]

    # Manifest
    manifest: RuntimeManifest

    # 元数据
    snapshot_id: str
    timestamp: str

    # 宪法 #1 ProjectFactSheet 收口
    fact_sheet: ProjectFactSheet | None = None

    # 宪法 #3 SubmissionProfile + SubmissionLifecycle 收口
    submission_profile: SubmissionProfile | None = None
    submission_lifecycle: SubmissionLifecycle | None = None

    # P0-02: 适用性无法确定的义务。下游不得把它们当作"本项目不涉及"。
    unknown_obligations: list[str] = dc_field(default_factory=list)
    obligation_applicability: dict[str, str] = dc_field(default_factory=dict)

    # P0-01/03: 本次消费输入的指纹, 供复核记录绑定 (DECISION_LOG 条目 004)。
    # 不是 fact_snapshot_hash, 也不是 generation_input_hash。
    quality_input_hash: str = ""

    # P0-04: 运行时 enrich 产出的消费视图。**不写回 facts** (验收 F02)。
    enriched_views: dict = dc_field(default_factory=dict)
    runtime_diagnostics: list[str] = dc_field(default_factory=list)

    # P0-06: 两个分工明确的语义哈希 (04 文档第 7 节)。
    #   fact_snapshot_hash    规范化事实集合本身
    #   generation_input_hash 事实 + 来源 + 规则/registry/模板/计算版本
    # 都**不含**运行时间与 run ID, 因此同语义输入重复执行结果相同。
    hash_schema_version: str = ""
    fact_snapshot_hash: str = ""
    generation_input_hash: str = ""
    input_digests: dict = dc_field(default_factory=dict)


@dataclass
class FrozenSubmissionInput:
    """
    可冻结的提交输入快照。

    **冻结 = 生命周期冻结, 不等于专业校审通过。** 构造这个 dataclass 不代表
    任何人确认过内容 (03 文档 P0-06 第 5 条)。
    """
    snapshot_json: str          # RuntimeSnapshot 的 JSON 序列化
    content_hash: str           # SHA256(snapshot_json) —— 文件完整性, 非语义
    frozen_at: str              # ISO 时间 (审计元数据, 不进语义 hash)
    fact_snapshot_hash: str     # P0-06: 规范化**事实集合**的 hash (原来错散列了 derived)

    artifact_manifest: list[str]    # 本次要求的 artifact id 列表
    assurance_manifest: list[str]   # 本次要求的 assurance id 列表
    calculator_manifest: list[str]  # 本次执行的 calculator id 列表
    obligation_manifest: list[str]  # 本次触发的 obligation id 列表

    # P0-06 新增
    hash_schema_version: str = ""
    generation_input_hash: str = ""
    """审核有效性、重生成与变更判定看它, 不看 fact_snapshot_hash"""
    input_digests: dict = dc_field(default_factory=dict)
    lifecycle_freeze_note: str = (
        "本记录只表示输入已冻结, **不表示**内容已经专业校审通过。")


@dataclass
class SubmissionPackageVersion:
    """最小版本对象"""
    version_id: str
    frozen_input_hash: str
    timestamp: str
    previous_version_id: str | None = None
    diff_summary: dict | None = None


# ============================================================
# Registry loading (统一入口, 供 runtime 和 lint 共用)
# ============================================================

def load_all_registries(specs_dir: Path | None = None) -> dict:
    """加载全部 v0 registries, 返回 {name: parsed_yaml}"""
    d = specs_dir or SPECS_DIR
    files = {
        "contracts":   GOVERNANCE_DIR / "CORE_CONTRACTS.yaml",
        "fields":      d / "FieldIdentityRegistry_v0.yaml",
        "artifacts":   d / "ArtifactRegistry_v0.yaml",
        "obligations": d / "ObligationSet_v0.yaml",
        "assurances":  d / "AssuranceRegistry_v0.yaml",
        "calculators": d / "CalculatorRegistry_v0.yaml",
        "sensitive_area_types": d / "SensitiveAreaTypeRegistry_v0.yaml",
        "analog_projects":      d / "AnalogProjectRegistry_v0.yaml",
    }
    loaded = {}
    for name, path in files.items():
        if path.exists():
            with path.open(encoding="utf-8") as f:
                loaded[name] = yaml.safe_load(f)
    return loaded


# ============================================================
# run_project — 核心运行时入口
# ============================================================

def run_project(
    project_input: dict,
    *,
    ruleset: str | None = None,
    lifecycle: str | None = None,
    specs_dir: Path | None = None,
) -> RuntimeSnapshot:
    """
    CPSWC v0 统一运行时入口。

    参数:
        project_input: sample JSON 格式 dict (含 facts / derived / sample_meta 等)
        ruleset: 规则集标识 (v0 默认 "v2026_gd_package")
        lifecycle: 生命周期阶段 (v0 默认 "pre_submission")
        specs_dir: specs 目录路径 (默认 SPECS_DIR)

    返回:
        RuntimeSnapshot 对象
    """
    ruleset = ruleset or "v2026_gd_package"
    lifecycle = lifecycle or "pre_submission"

    # Step 1: 加载 registries
    registries = load_all_registries(specs_dir)
    registries_loaded = list(registries.keys())

    obligations_reg = (registries.get("obligations") or {}).get("obligations") or {}
    assurances_reg = (registries.get("assurances") or {}).get("assurances") or {}
    artifacts_reg = (registries.get("artifacts") or {}).get("artifacts") or {}
    calc_registry = registries.get("calculators") or {}
    fir = registries.get("fields") or {}

    # Step 2: 读取 facts
    facts = project_input.get("facts") or {}
    existing_derived = project_input.get("derived") or {}

    # Step 3: 运行 live calculators → 产出 derived fields
    from cpswc.calculator_engine import (  # type: ignore
        evaluate as calc_evaluate,
        CalculatorError,
    )

    derived_fields: dict[str, Any] = {}
    calculator_results: list[CalcResultSummary] = []
    live_calcs = (calc_registry.get("calculators") or {})

    for calc_id, calc_def in live_calcs.items():
        if (calc_def or {}).get("status") != "live":
            continue
        try:
            result = calc_evaluate(calc_id, project_input,
                                   registry=calc_registry, fir=fir)
            derived_fields[result.output_field_id] = result.value
            calculator_results.append(CalcResultSummary(
                calculator_id=calc_id,
                output_field_id=result.output_field_id,
                value=result.value,
                unit=result.unit,
                status="ok",
            ))
        except CalculatorError as e:
            calculator_results.append(CalcResultSummary(
                calculator_id=calc_id,
                output_field_id="",
                value=None,
                unit="",
                status="error",
                error_message=str(e),
            ))

    # Step 3.5: F2 Price Layer enrich (仅白名单措施)
    #
    # P0-04 (验收 F02): 原实现把 enrich 结果**写回 project_input["facts"]**,
    # 于是调用一次 run_project 就改了调用者的输入 —— 重跑会基于被改过的数据。
    # 现在 enrich 只产出一份独立的**消费视图**, 原始 facts 一个字节都不动。
    enriched_views: dict[str, Any] = {}
    enrich_diagnostics: list[str] = []
    measures_registry = facts.get("field.fact.investment.measures_registry")
    if isinstance(measures_registry, list) and measures_registry:
        try:
            from cpswc.quota_connector import (  # type: ignore
                enrich_measures, PS_QUOTA_CALIBRATED,
            )
            enriched = enrich_measures(copy.deepcopy(measures_registry))
            # 只标注白名单结果, 非白名单保留原始 CSV 价格
            for m in enriched:
                if m.get("price_source") == PS_QUOTA_CALIBRATED:
                    m["quota_enriched"] = True
            enriched_views["field.fact.investment.measures_registry"] = enriched
        except Exception as e:
            # 不再静默: 依赖缺失也要留痕 (04 文档第 3 节第 8 条)
            enrich_diagnostics.append(f"价格 enrich 未执行: {type(e).__name__}: {e}")

    # Step 4: 合并 facts + derived → unified lookup
    # 优先级与 BuildContext 一致:
    #   计算 derived > enrich 消费视图 > 预存 derived > 项目事实
    unified: dict[str, Any] = {}
    unified.update(facts)
    unified.update(existing_derived)  # sample 里的 pre-stored derived
    unified.update(enriched_views)    # 运行时 enrich 的消费视图
    unified.update(derived_fields)    # runtime 计算的 derived 覆盖 pre-stored

    # Step 5: 评估 obligations (委托 ConditionEngine_v0)
    engine_result = _evaluate_all_obligations(obligations_reg, unified)
    obligation_details = engine_result.obligation_details
    triggered = engine_result.triggered
    not_triggered = engine_result.not_triggered
    unknown_obligations = engine_result.unknown

    # Step 6: 收集 required artifacts / assurances
    required_artifacts: set[str] = set()
    required_assurances: set[str] = set()
    for ob_id in triggered:
        ob_def = obligations_reg.get(ob_id) or {}
        for art_ref in (ob_def.get("required_artifact_refs") or []):
            required_artifacts.add(art_ref)
            # artifact 的子表/子件
            art_def = artifacts_reg.get(art_ref) or {}
            for child in (art_def.get("children") or []):
                required_artifacts.add(child)
        for as_ref in (ob_def.get("required_assurance_refs") or []):
            required_assurances.add(as_ref)

    # Always-required artifacts (requirement == "always")
    for art_id, art_def in artifacts_reg.items():
        if isinstance(art_def, dict) and art_def.get("requirement") == "always":
            required_artifacts.add(art_id)
            for child in (art_def.get("children") or []):
                required_artifacts.add(child)

    # Assurance trigger resolution (mode=always / driven_by_obligation)
    for as_id, as_def in assurances_reg.items():
        if not isinstance(as_def, dict):
            continue
        # always-required (via requirement or trigger.mode)
        if as_def.get("requirement") == "always":
            required_assurances.add(as_id)
            continue
        as_trigger = as_def.get("trigger") or {}
        as_mode = as_trigger.get("mode", "conditional")
        if as_mode == "always" or str(as_trigger.get("when", "")).strip().lower() == "always":
            required_assurances.add(as_id)
            continue
        # driven_by_obligation
        if as_mode == "driven_by_obligation":
            driven_by = as_trigger.get("driven_by_refs") or []
            if any(d in triggered for d in driven_by):
                required_assurances.add(as_id)

    # Step 7: 打包
    project_summary = {
        "name": (facts.get("field.fact.project.name") or ""),
        "code": (facts.get("field.fact.project.code") or ""),
        "industry": (facts.get("field.fact.project.industry_category") or ""),
        "species": (project_input.get("sample_meta") or {}).get("species", ""),
    }

    manifest = RuntimeManifest(
        registries_loaded=registries_loaded,
        calculators_executed=calculator_results,
        obligations_evaluated=len(obligation_details),
        obligations_triggered=len(triggered),
        obligations_unknown=len(unknown_obligations),
        artifacts_required=len(required_artifacts),
        assurances_required=len(required_assurances),
        ruleset=ruleset,
        lifecycle=lifecycle,
    )

    now = datetime.now(timezone.utc).isoformat()
    snapshot_id = f"snap_{hashlib.sha256(now.encode()).hexdigest()[:12]}"

    # ---- P0-06: 语义哈希 ----
    from cpswc.paths import NARRATIVE_TEMPLATES_DIR

    input_digests = collect_input_digests(
        registries_dir=(specs_dir or SPECS_DIR),
        governance_dir=GOVERNANCE_DIR,
        templates_dir=NARRATIVE_TEMPLATES_DIR,
    )
    calculator_versions = {
        cid: str((cdef or {}).get("version", ""))
        for cid, cdef in sorted(live_calcs.items())
        if (cdef or {}).get("status") == "live"
    }
    sample_meta_for_profile = project_input.get("sample_meta") or {}
    static_profile = {
        "species": sample_meta_for_profile.get("species", ""),
        "compilation_intent": sample_meta_for_profile.get("compilation_intent", "NEW"),
        "industry_category": facts.get("field.fact.project.industry_category") or "",
    }
    # 来源层选择本身属于输入: 同一个值取自 CALCULATED 还是 PRE_STORED, 结论不同
    source_layers = {}
    for field_id in sorted(set(facts) | set(existing_derived)
                           | set(enriched_views) | set(derived_fields)):
        if field_id in derived_fields:
            source_layers[field_id] = "CALCULATED"
        elif field_id in enriched_views:
            source_layers[field_id] = "ENRICHED_VIEW"
        elif field_id in existing_derived:
            source_layers[field_id] = "PRE_STORED_DERIVED"
        else:
            source_layers[field_id] = "PROJECT_FACT"

    fact_hash = _fact_snapshot_hash(facts)
    gen_hash = _generation_input_hash(
        facts=facts,
        pre_stored_derived=existing_derived,
        source_map=source_layers,
        profile=static_profile,
        input_digests=input_digests,
        calculator_versions=calculator_versions,
        ruleset=ruleset,
    )

    # ProjectFactSheet: unified = facts + pre-stored derived + runtime derived
    # 与 Step 4 的 unified lookup 口径一致
    fact_sheet = _build_fact_sheet(facts, unified)

    # 宪法 #3: SubmissionProfile (静态) + SubmissionLifecycle (动态)
    sample_meta = project_input.get("sample_meta") or {}
    profile = SubmissionProfile(
        species=sample_meta.get("species", ""),
        compilation_intent=sample_meta.get("compilation_intent", "NEW"),
        industry_category=facts.get("field.fact.project.industry_category") or "",
        ruleset=ruleset,
    )
    lc = SubmissionLifecycle(stage=lifecycle)

    return RuntimeSnapshot(
        project_input_summary=project_summary,
        facts_count=len(facts),
        ruleset=ruleset,
        lifecycle=lifecycle,
        derived_fields=derived_fields,
        calculator_results=calculator_results,
        triggered_obligations=sorted(triggered),
        not_triggered_obligations=sorted(not_triggered),
        obligation_details=obligation_details,
        required_artifacts=sorted(required_artifacts),
        required_assurances=sorted(required_assurances),
        unknown_obligations=sorted(unknown_obligations),
        obligation_applicability=engine_result.applicability_map(),
        quality_input_hash=compute_quality_input_hash(facts, unified),
        enriched_views=enriched_views,
        runtime_diagnostics=enrich_diagnostics,
        hash_schema_version=HASH_SCHEMA_VERSION,
        fact_snapshot_hash=fact_hash,
        generation_input_hash=gen_hash,
        input_digests=input_digests,
        fact_sheet=fact_sheet,
        submission_profile=profile,
        submission_lifecycle=lc,
        manifest=manifest,
        snapshot_id=snapshot_id,
        timestamp=now,
    )


# ============================================================
# Freeze / Version
# ============================================================

def _serialize_snapshot(snapshot: RuntimeSnapshot) -> str:
    """将 RuntimeSnapshot 序列化为确定性 JSON (用于 content-addressing)"""
    def _default(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return str(obj)
    return json.dumps(asdict(snapshot), ensure_ascii=False,
                      sort_keys=True, indent=2, default=_default)


def build_snapshot_dict(snapshot: RuntimeSnapshot,
                        project_input: dict,
                        registries: dict | None = None) -> dict:
    """
    产出**唯一**一份供下游消费的 snapshot dict (P0-04 / 验收 I01)。

    在此之前, 每个调用点各自拼 `_original_facts` / `_pre_stored_derived`,
    而 `derived_fields` 只含计算 derived —— 结果是正文、表格、工作台、导出门禁
    看到的 derived 各不相同 (DECISION_LOG 条目 007)。

    现在统一经 BuildContext 选定读值:
      `_original_facts`   = 统一视图里的 field.fact.*   (含 enrich 消费视图)
      `derived_fields`    = 统一视图里的 field.derived.* (含预存派生量)
      `_pre_stored_derived` 保留原样, 仅供对照, **不应**再被用来二次合并
      `_source_map`       每个字段实际选了哪一层
      `_build_findings`   读取过程中的诊断 (冲突 / 失效 / 未核验 / 演示假设)

    计算失败的字段**不进视图** —— 旧值不顶替失败结果。
    """
    from cpswc.snapshot_adapter import make_build_context

    regs = registries if registries is not None else load_all_registries()
    ctx = make_build_context(project_input, snapshot, regs,
                             enriched_views=snapshot.enriched_views)
    view = ctx.unified_view()

    d = json.loads(_serialize_snapshot(snapshot))
    d["_original_facts"] = {k: v for k, v in view.items()
                            if not k.startswith("field.derived.")}
    d["derived_fields"] = {k: v for k, v in view.items()
                           if k.startswith("field.derived.")}
    d["_pre_stored_derived"] = project_input.get("derived") or {}
    d["_source_map"] = ctx.source_map()
    d["_build_findings"] = [f.to_dict() for f in ctx.findings]
    d["quality_inputs"] = project_input.get("quality_inputs")
    d["quality_input_hash"] = snapshot.quality_input_hash
    d["generation_input_hash"] = snapshot.generation_input_hash
    d["fact_snapshot_hash"] = snapshot.fact_snapshot_hash
    d["hash_schema_version"] = snapshot.hash_schema_version
    if snapshot.fact_sheet is not None:
        d["fact_sheet"] = asdict(snapshot.fact_sheet)
    return d


def freeze_submission(snapshot: RuntimeSnapshot) -> FrozenSubmissionInput:
    """
    从 RuntimeSnapshot 产出 FrozenSubmissionInput。

    P0-06: 两个语义 hash 在 run_project 里就算好了 (那里才拿得到 facts),
    这里只搬运 —— 不再像原来那样在冻结时现算, 更不再把 derived_fields
    当成 facts 去散列 (D10)。
    """
    snapshot_json = _serialize_snapshot(snapshot)
    content_hash = hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()

    return FrozenSubmissionInput(
        snapshot_json=snapshot_json,
        content_hash=content_hash,
        frozen_at=datetime.now(timezone.utc).isoformat(),
        fact_snapshot_hash=snapshot.fact_snapshot_hash,
        hash_schema_version=snapshot.hash_schema_version or HASH_SCHEMA_VERSION,
        generation_input_hash=snapshot.generation_input_hash,
        input_digests=dict(snapshot.input_digests or {}),
        artifact_manifest=snapshot.required_artifacts,
        assurance_manifest=snapshot.required_assurances,
        calculator_manifest=[c.calculator_id for c in snapshot.calculator_results
                             if c.status == "ok"],
        obligation_manifest=snapshot.triggered_obligations,
    )


def create_version(
    frozen: FrozenSubmissionInput,
    previous_version_id: str | None = None,
) -> SubmissionPackageVersion:
    """创建 SubmissionPackageVersion"""
    version_id = f"v0_{frozen.content_hash[:16]}"
    return SubmissionPackageVersion(
        version_id=version_id,
        frozen_input_hash=frozen.content_hash,
        timestamp=frozen.frozen_at,
        previous_version_id=previous_version_id,
        diff_summary=None,  # v0 不实现 diff, v1 升级
    )


# ============================================================
# CLI
# ============================================================

def _cli() -> int:
    """CLI 入口: python cpswc_runtime.py <facts.json> [--freeze] [--version]"""
    import argparse
    parser = argparse.ArgumentParser(description="CPSWC v0 Runtime Service")
    parser.add_argument("input", nargs="?",
                        default=str(SAMPLES_DIR / "huizhou_housing_v0.json"),
                        help="项目 facts JSON 文件路径")
    parser.add_argument("--freeze", action="store_true",
                        help="输出 FrozenSubmissionInput (含 content hash)")
    parser.add_argument("--version", action="store_true",
                        help="输出 SubmissionPackageVersion")
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出 RuntimeSnapshot")
    parser.add_argument("--html", metavar="OUTPUT",
                        help="生成 Workbench HTML 到指定文件 (Step 12B)")
    parser.add_argument("--package", metavar="DIR",
                        help="生成完整 Submission Package 到指定目录 (Step 13A)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: {input_path} not found", file=sys.stderr)
        return 2

    with input_path.open(encoding="utf-8") as f:
        project_input = json.load(f)

    # Run
    snapshot = run_project(project_input)

    if args.package:
        from cpswc.renderers.package_builder import build_package  # type: ignore
        pkg_path = build_package(project_input, args.package)
        print(f"Submission package built: {pkg_path}")
        return 0

    if args.json:
        print(_serialize_snapshot(snapshot))
        return 0

    # --html: 生成 Workbench HTML (Step 12B)
    if args.html:
        from cpswc.renderers.workbench import render_workbench  # type: ignore
        registries = load_all_registries()

        # 把 original facts 附到 snapshot dict 里供 renderer 使用
        snapshot_dict = build_snapshot_dict(snapshot, project_input, registries)

        frozen_dict = None
        version_dict = None
        if args.freeze:
            frozen = freeze_submission(snapshot)
            frozen_dict = {
                "content_hash": frozen.content_hash,
                "fact_snapshot_hash": frozen.fact_snapshot_hash,
                "frozen_at": frozen.frozen_at,
                "artifact_manifest": frozen.artifact_manifest,
                "assurance_manifest": frozen.assurance_manifest,
                "calculator_manifest": frozen.calculator_manifest,
                "obligation_manifest": frozen.obligation_manifest,
            }
            if args.version:
                ver = create_version(frozen)
                version_dict = {
                    "version_id": ver.version_id,
                    "frozen_input_hash": ver.frozen_input_hash,
                    "timestamp": ver.timestamp,
                    "previous_version_id": ver.previous_version_id,
                }

        html = render_workbench(snapshot_dict, frozen_dict, version_dict, registries)
        Path(args.html).write_text(html, encoding="utf-8")
        print(f"Workbench HTML written to: {args.html}")
        return 0

    # Human-readable summary
    print("=" * 72)
    print(f" CPSWC Runtime Snapshot")
    print(f" Project: {snapshot.project_input_summary.get('name', '?')}")
    print(f" Snapshot ID: {snapshot.snapshot_id}")
    print(f" Timestamp: {snapshot.timestamp}")
    print("=" * 72)
    print()
    print(f"  Facts loaded:        {snapshot.facts_count}")
    print(f"  Derived fields:      {len(snapshot.derived_fields)}")
    print(f"  Calculators run:     {len(snapshot.calculator_results)}")
    for cr in snapshot.calculator_results:
        status = "OK" if cr.status == "ok" else f"ERR: {cr.error_message}"
        if isinstance(cr.value, (list, dict)):
            val_str = f"({type(cr.value).__name__})"
        else:
            val_str = f"= {cr.value} {cr.unit}"
        print(f"    [{status}] {cr.calculator_id} → {cr.output_field_id} {val_str}")
    print()
    print(f"  Obligations triggered:     {len(snapshot.triggered_obligations)}")
    for ob in snapshot.triggered_obligations:
        print(f"    + {ob}")
    print(f"  Obligations not triggered: {len(snapshot.not_triggered_obligations)}")
    print()
    print(f"  Required artifacts:  {len(snapshot.required_artifacts)}")
    print(f"  Required assurances: {len(snapshot.required_assurances)}")

    if args.freeze:
        frozen = freeze_submission(snapshot)
        print()
        print("=" * 72)
        print(f" FrozenSubmissionInput")
        print(f"   content_hash: {frozen.content_hash}")
        print(f"   fact_snapshot_hash: {frozen.fact_snapshot_hash}")
        print(f"   frozen_at: {frozen.frozen_at}")
        print(f"   artifact_manifest: {len(frozen.artifact_manifest)} items")
        print(f"   assurance_manifest: {len(frozen.assurance_manifest)} items")
        print(f"   calculator_manifest: {frozen.calculator_manifest}")
        print(f"   obligation_manifest: {len(frozen.obligation_manifest)} items")
        print("=" * 72)

        if args.version:
            version = create_version(frozen)
            print()
            print(f" SubmissionPackageVersion")
            print(f"   version_id: {version.version_id}")
            print(f"   frozen_input_hash: {version.frozen_input_hash}")
            print(f"   timestamp: {version.timestamp}")
            print("=" * 72)

    return 0


if __name__ == "__main__":
    sys.exit(_cli())
