#!/usr/bin/env python3
"""
cross_registry_lint.py — CPSWC 跨注册表静态校验器

读入 specs/ 下所有已产出的 YAML 注册表, 执行以下 lint 规则:

  CORE_CONTRACTS_001  所有 *_refs 必须 resolve (dangling ref)
  CORE_CONTRACTS_002  所有 id 必须符合 namespace 格式
  CORE_CONTRACTS_007  每个 field / obligation 必须声明 protection_level
  ART_004             artifact.data_source_refs 中的 field.* 必须 resolve
  ART_006             artifact.chapter_ref 必须是合法 sec.* id
  FIR_002             派生字段必须声明 upstream_deps 与 derivation
  FIR_003             每个 field 的 projection_target_refs 必须符合 id 格式

依赖: PyYAML  (pip install pyyaml)

用法:
    python3 specs/cross_registry_lint.py           # 自动发现 specs/
    python3 specs/cross_registry_lint.py --json    # 输出 JSON

退出码:
    0  全部通过 (仅有 INFO / PENDING)
    1  存在 ERROR
    2  文件或依赖缺失

约束来源: CPSWC_CORE_CONTRACTS.yaml (生效于 2026-04-11)
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: 缺少 PyYAML。请执行: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

SPECS_DIR = Path(__file__).resolve().parent

# ------------------------------------------------------------------
# 命名空间定义 (与 CPSWC_CORE_CONTRACTS.yaml 保持一致)
# ------------------------------------------------------------------
# loaded_in_v0 = True 表示本 v0 阶段该 registry 应已存在, 可查 dangling
# virtual      = True 表示没有独立 registry, 只校验 id 格式
# extension    = True 表示 contracts 未列, 但允许使用 (标 INFO)
NAMESPACES: dict[str, dict[str, Any]] = {
    "field.":  {"registry": "FieldIdentityRegistry"},
    "proj.":   {"registry": "Projection",        "virtual": True},
    "ob.":     {"registry": "ObligationSet"},
    "art.":    {"registry": "ArtifactRegistry"},
    "as.":     {"registry": "AssuranceRegistry"},
    "sec.":    {"registry": "Section",           "virtual": True},
    "narr.":   {"registry": "NarrativeNode",     "virtual": True},
    "rule.":   {"registry": "Rule",              "virtual": True},
    "sample.": {"registry": "Sample",            "virtual": True},
    "cal.":    {"registry": "CalculatorRegistry"},  # Step 11A
    "engine.": {"registry": "Engine",            "virtual": True, "extension": True},
}

FIELD_DOMAIN_ENUM = {"fact", "derived"}
PROJ_FORM_ENUM    = {"spec_sheet", "report_form"}
OB_TOPIC_ENUM     = {"disposal_site", "borrow_site", "topsoil", "monitoring",
                     "surveillance", "commitment", "unavoidability", "evaluation",
                     "investment", "schedule", "signature", "seal", "sensitive_overlay"}
ART_KIND_ENUM     = {"table", "figure", "attachment", "subreport", "spec_sheet", "cover"}

# 文件里不应被当作 ref 解析的字段名 (描述文字/注释/示例/DSL 表达式)
NON_REF_PATHS = re.compile(
    r"\.(note|description|rule|rationale|human|content_spec|format_spec"
    r"|v0_note|v0_input|v0_scope_note|anti_pattern|correct_pattern"
    r"|bad_example|good_example|fix|detector|error_msg|check|desc"
    r"|rendering.*|examples.*|example.*|render_rule|projection_scope_note"
    r"|trigger\.when|trigger\.human|trigger\.mode"
    r"|condition\.human|derivation"
    r"|validation\.required_when|validation\.rule|validation\.standard_ref"
    r"|validation\.v0_constraint|validation\.trigger_condition)"
)

# 顶层路径段完全跳过 (schema 定义/lint 规则/排除声明等)
SKIP_TOP_SEGMENTS = {
    # contracts.yaml 全部顶级段 (schema 定义文件, 不含业务 ref)
    "naming_style", "list_naming", "tense_semantics", "id_namespaces",
    "cross_object_references", "projection_contract", "protection_levels",
    "freeze_semantics", "lint_rules", "versioning",
    # fields.yaml / artifacts.yaml / assurances.yaml 的非业务段
    "registry_lints", "v0_excluded_fields", "v0_excluded_artifacts",
    "v0_excluded_assurances", "semantic_types",
}

# 整个文件跳过 walk (schema 定义文件)
SKIP_FILES = {"contracts"}

# 前向兼容预埋文件识别 (CPSWC_ARCHITECTURE_DECISIONS.md 前向兼容预埋豁免条款)
# 匹配 *_v1_reserved*.yaml / *v1_reservations*.yaml 等命名
# v0 lint 默认**不加载**这些文件; 未来可加 --include-reserved 开关主动检查
RESERVED_FILE_PATTERN = re.compile(
    r"(_v1_reserved|v1_reservations).*\.ya?ml$", re.IGNORECASE
)

def discover_reserved_files(specs_dir: Path) -> list[Path]:
    """扫描 specs/ 下所有匹配前向兼容预埋命名的文件, 返回 Path 列表。"""
    return sorted(
        p for p in specs_dir.iterdir()
        if p.is_file() and RESERVED_FILE_PATTERN.search(p.name)
    )

# TODO(v1_plan_lint): 将来实现 v1_plan_lint.py (或本脚本的 --include-reserved 开关),
# 专门检查 reserved 文件之间的内部一致性:
#   1. reserved id 的 namespace 格式合法
#   2. reserved 条目对 v0 id 的引用 resolve (v0 → reserved 禁止, reserved → v0 允许)
#   3. reserved 条目之间的相互引用 resolve
# 该 lint 不在 v0 CI 强制路径, 只在触发 v1 开发前主动跑。


# ------------------------------------------------------------------
# 数据结构
# ------------------------------------------------------------------
SEVERITIES = ["ERROR", "WARN", "PENDING", "INFO"]


@dataclass
class Finding:
    severity: str
    rule: str
    message: str
    location: str

    def to_dict(self):
        return {"severity": self.severity, "rule": self.rule,
                "message": self.message, "location": self.location}


@dataclass
class LintReport:
    findings: list[Finding] = dc_field(default_factory=list)

    def add(self, severity, rule, message, location):
        assert severity in SEVERITIES
        self.findings.append(Finding(severity, rule, message, location))

    def count(self, severity):
        return sum(1 for f in self.findings if f.severity == severity)


# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------
def namespace_of(ref: str) -> str | None:
    for prefix in NAMESPACES:
        if ref.startswith(prefix):
            return prefix
    return None


def check_id_format(ref: str, allow_wildcard: bool = True) -> tuple[bool, str]:
    ns = namespace_of(ref)
    if ns is None:
        return False, "unknown namespace"
    tail = ref[len(ns):]
    if not tail:
        return False, "empty tail after prefix"
    # 通配符: ob.* / field.derived.target.* 等, 跳过 enum 校验
    if allow_wildcard and (tail == "*" or tail.endswith(".*")):
        return True, "wildcard"
    if not re.match(r"^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$", tail):
        return False, f"bad characters in tail '{tail}'"
    # 命名空间特定段 enum 校验
    seg = tail.split(".", 1)[0]
    if ns == "field." and seg not in FIELD_DOMAIN_ENUM:
        return False, f"field.* domain must be one of {sorted(FIELD_DOMAIN_ENUM)}, got '{seg}'"
    if ns == "proj." and seg not in PROJ_FORM_ENUM:
        return False, f"proj.* form must be one of {sorted(PROJ_FORM_ENUM)}, got '{seg}'"
    if ns == "ob." and seg not in OB_TOPIC_ENUM:
        return False, f"ob.* topic must be one of {sorted(OB_TOPIC_ENUM)}, got '{seg}'"
    if ns == "art." and seg not in ART_KIND_ENUM:
        return False, f"art.* kind must be one of {sorted(ART_KIND_ENUM)}, got '{seg}'"
    return True, "ok"


def walk_refs(obj: Any, path: str = ""):
    """遍历嵌套结构, 产出 (ref_string, path, kind) 三元组; 跳过 schema/lint/excluded 段。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            sub_path = f"{path}.{k}" if path else k
            # 顶层段跳过 (schema 定义 / lint 规则 / v0_excluded 等)
            top = sub_path.split(".", 1)[0]
            if top in SKIP_TOP_SEGMENTS:
                continue
            yield from walk_refs(v, sub_path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_refs(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        if NON_REF_PATHS.search(f".{path}"):
            return
        # 匹配以 namespace 前缀开头且长度 < 200 的字符串
        for prefix in NAMESPACES:
            if obj.startswith(prefix) and len(obj) < 200 and "\n" not in obj:
                # 通配符引用 (如 field.derived.target.*)
                if obj == prefix + "*" or obj.endswith(".*"):
                    yield (obj, path, "wildcard")
                else:
                    yield (obj, path, "literal")
                break


# ------------------------------------------------------------------
# 加载所有 registries
# ------------------------------------------------------------------
def load_registries():
    files = {
        "contracts":  SPECS_DIR / "CPSWC_CORE_CONTRACTS.yaml",
        "fields":     SPECS_DIR / "FieldIdentityRegistry_v0.yaml",
        "artifacts":  SPECS_DIR / "CPSWC_ARTIFACT_REGISTRY_v0.yaml",
        "obligations": SPECS_DIR / "ObligationSet_v0.yaml",
        "assurances": SPECS_DIR / "AssuranceRegistry_v0.yaml",
        "calculators": SPECS_DIR / "CalculatorRegistry_v0.yaml",  # Step 11A
    }
    loaded = {}
    missing = []
    for name, path in files.items():
        if path.exists():
            with path.open(encoding="utf-8") as f:
                loaded[name] = yaml.safe_load(f)
        else:
            missing.append(name)

    # 前向兼容预埋豁免条款: 不加载 *_v1_reserved*.yaml / *v1_reservations*.yaml
    # 但把它们记录下来, 报告里标注 v0 已识别但未纳入 lint
    reserved_files = discover_reserved_files(SPECS_DIR)
    loaded["_reserved_files_detected"] = [p.name for p in reserved_files]

    return loaded, missing


# ------------------------------------------------------------------
# Lint 规则
# ------------------------------------------------------------------
def collect_defined_ids(registries):
    """返回 {namespace_prefix: set(id)}"""
    defined = {prefix: set() for prefix in NAMESPACES}
    if "fields" in registries:
        for fid in (registries["fields"].get("fields") or {}).keys():
            defined["field."].add(fid)
    if "artifacts" in registries:
        for aid in (registries["artifacts"].get("artifacts") or {}).keys():
            defined["art."].add(aid)
    if "obligations" in registries:
        for oid in (registries["obligations"].get("obligations") or {}).keys():
            defined["ob."].add(oid)
    if "assurances" in registries:
        for asid in (registries["assurances"].get("assurances") or {}).keys():
            defined["as."].add(asid)
    if "calculators" in registries:  # Step 11A
        for cid in (registries["calculators"].get("calculators") or {}).keys():
            defined["cal."].add(cid)
    return defined


def lint_id_formats(registries, report: LintReport):
    """CORE_CONTRACTS_002 — 所有 key 与引用必须符合命名空间格式"""
    for reg_name in ("fields", "artifacts", "obligations", "assurances", "calculators"):
        if reg_name not in registries:
            continue
        top_key = {"fields": "fields", "artifacts": "artifacts",
                   "obligations": "obligations", "assurances": "assurances",
                   "calculators": "calculators"}[reg_name]
        items = registries[reg_name].get(top_key) or {}
        for key in items.keys():
            ok, reason = check_id_format(key)
            if not ok:
                report.add("ERROR", "CORE_CONTRACTS_002",
                           f"registry key id format invalid: {reason}",
                           f"{reg_name}.yaml:{key}")


def lint_dangling_refs(registries, defined_ids, report: LintReport):
    """CORE_CONTRACTS_001 — 所有引用必须 resolve"""
    for reg_name in ("fields", "artifacts", "obligations", "assurances", "calculators"):
        # contracts.yaml 是 schema 定义文件, 不走 dangling 检查
        if reg_name in SKIP_FILES or reg_name not in registries:
            continue
        seen = set()
        for ref, path, kind in walk_refs(registries[reg_name]):
            if (ref, path) in seen:
                continue
            seen.add((ref, path))

            # wildcard 直接跳过 (不查格式 enum, 不查 resolve)
            if kind == "wildcard":
                continue

            # 决议 6: governance_block 内部的 planned_split_fields 指向 v1 未来字段,
            # 属于 forward reference, 不走 v0 dangling 检查
            if "governance_block" in path and "upgrade_path" in path:
                continue

            # 校验 id 格式
            ok, reason = check_id_format(ref, allow_wildcard=False)
            if not ok:
                report.add("ERROR", "CORE_CONTRACTS_002",
                           f"reference id format invalid: {ref} ({reason})",
                           f"{reg_name}.yaml:{path}")
                continue

            ns = namespace_of(ref)
            ns_meta = NAMESPACES[ns]

            # virtual 命名空间无需 resolve
            if ns_meta.get("virtual"):
                if ns_meta.get("extension"):
                    report.add("INFO", "CORE_CONTRACTS_002",
                               f"extension namespace '{ns}' used: {ref}",
                               f"{reg_name}.yaml:{path}")
                continue

            # 实名命名空间: 需要 resolve
            target_set = defined_ids.get(ns, set())
            if not target_set:
                # 该 registry 尚未产出
                report.add("PENDING", "CORE_CONTRACTS_001",
                           f"unresolvable (target registry '{ns_meta['registry']}' not yet produced): {ref}",
                           f"{reg_name}.yaml:{path}")
                continue

            if ref not in target_set:
                report.add("ERROR", "CORE_CONTRACTS_001",
                           f"dangling reference: {ref} not found in {ns_meta['registry']}",
                           f"{reg_name}.yaml:{path}")


def lint_field_protection_levels(registries, report: LintReport):
    """CORE_CONTRACTS_007 + FIR 系列: 每个 field 必须声明 protection_level 与 lineage"""
    if "fields" not in registries:
        return
    fields = registries["fields"].get("fields") or {}
    for fid, fdef in fields.items():
        if not isinstance(fdef, dict):
            report.add("ERROR", "FIR_001", f"field definition is not a mapping",
                       f"fields.yaml:{fid}")
            continue

        if "protection_level" not in fdef:
            report.add("ERROR", "CORE_CONTRACTS_007",
                       f"field missing protection_level: {fid}",
                       f"fields.yaml:{fid}")

        lineage = fdef.get("lineage")
        if lineage is None:
            report.add("ERROR", "FIR_002", f"field missing lineage block: {fid}",
                       f"fields.yaml:{fid}")
            continue

        # 派生字段额外要求 derivation 与 upstream_deps
        if fid.startswith("field.derived."):
            if not lineage.get("upstream_deps"):
                report.add("ERROR", "FIR_002",
                           f"derived field missing upstream_deps: {fid}",
                           f"fields.yaml:{fid}.lineage")
            if not lineage.get("derivation"):
                report.add("ERROR", "FIR_002",
                           f"derived field missing derivation: {fid}",
                           f"fields.yaml:{fid}.lineage")

        # projection_target_refs 必须有值 (除了 placeholder stub 可以空)
        is_placeholder = fdef.get("placeholder") is True
        if not is_placeholder and not lineage.get("projection_target_refs"):
            report.add("WARN", "FIR_003",
                       f"field has no projection_target_refs: {fid}",
                       f"fields.yaml:{fid}.lineage")


def lint_expert_switch_governance(registries, report: LintReport):
    """
    EXPERT_SWITCH_001 (决议 6 ExpertSwitch Governance):

    对于 expert-switch 型 bool 字段 (semantic_type=bool,
    protection_level ∈ {CRITICAL, PROTECTED}, origin != derived),
    必须声明 governance_block。否则本批次报 INFO, 下一次新增未治理
    即升 WARN, 进入 v1 升 ERROR。
    """
    if "fields" not in registries:
        return
    fields = registries["fields"].get("fields") or {}

    # 治理块最少字段 (决议 6 定义)
    REQUIRED_KEYS = [
        "source_rule_id",
        "human_decision_question",
        "decision_owner_role",
        "default_value",
        "evidence_expectation",
        "replaced_normative_semantics",
        "upgrade_path",
        "authored_by",
        "authored_at",
    ]

    for fid, fdef in fields.items():
        if not isinstance(fdef, dict):
            continue
        if fdef.get("semantic_type") != "bool":
            continue
        if fdef.get("origin") == "derived":
            continue
        # derived 字段通常通过 id 前缀 field.derived.* 识别; 双保险
        if fid.startswith("field.derived."):
            continue
        level = fdef.get("protection_level")
        if level not in ("CRITICAL", "PROTECTED"):
            continue

        gb = fdef.get("governance_block")
        if gb is None:
            report.add("INFO", "EXPERT_SWITCH_001",
                       f"expert-switch bool missing governance_block: {fid}",
                       f"fields.yaml:{fid}")
            continue

        if not isinstance(gb, dict):
            report.add("INFO", "EXPERT_SWITCH_001",
                       f"governance_block is not a mapping: {fid}",
                       f"fields.yaml:{fid}.governance_block")
            continue

        # 逐字段检查最小必填
        missing = [k for k in REQUIRED_KEYS if k not in gb]
        if missing:
            report.add("INFO", "EXPERT_SWITCH_001",
                       f"governance_block missing keys {missing}: {fid}",
                       f"fields.yaml:{fid}.governance_block")

        # upgrade_path 内部纪律: strategy 必填, 条件分支校验
        up = gb.get("upgrade_path") if isinstance(gb, dict) else None
        if isinstance(up, dict):
            strategy = up.get("strategy")
            if strategy not in ("splittable", "refinable", "irreducible"):
                report.add("INFO", "EXPERT_SWITCH_001",
                           f"upgrade_path.strategy invalid or missing "
                           f"(expect splittable/refinable/irreducible): {fid}",
                           f"fields.yaml:{fid}.governance_block.upgrade_path")
            if strategy == "splittable":
                if not up.get("planned_split_fields"):
                    report.add("INFO", "EXPERT_SWITCH_001",
                               f"splittable upgrade_path missing "
                               f"planned_split_fields: {fid}",
                               f"fields.yaml:{fid}.governance_block.upgrade_path")
                if not gb.get("sunset_target_version"):
                    report.add("INFO", "EXPERT_SWITCH_001",
                               f"splittable upgrade_path missing "
                               f"sunset_target_version: {fid}",
                               f"fields.yaml:{fid}.governance_block")
            elif strategy == "irreducible":
                if not up.get("irreducibility_justification"):
                    report.add("INFO", "EXPERT_SWITCH_001",
                               f"irreducible upgrade_path missing "
                               f"irreducibility_justification: {fid}",
                               f"fields.yaml:{fid}.governance_block.upgrade_path")


def lint_calculator_structure(registries, report: LintReport):
    """
    CAL_001 (Step 11A, ERROR 级):

    CalculatorRegistry_v0 中每条 live calculator 必须满足决议 8 双锚必备 +
    决议 8 九类 authority_class + inputs/outputs 引用已登记 field id。

    本规则对 live calculator 直接发 ERROR, 不走宽松口径, 因为 calculator
    是影响法定金额的 CRITICAL 对象。
    """
    if "calculators" not in registries:
        return
    calcs_root = registries["calculators"] or {}
    calcs = calcs_root.get("calculators") or {}

    REQUIRED_KEYS = [
        "canonical_name",
        "protection_level",
        "status",
        "authority_class",
        "precedence_rank",
        "normative_basis_refs",
        "evidence_anchor_refs",
        "inputs",
        "outputs",
        "formula",
        "error_branches",
    ]

    for cid, cdef in calcs.items():
        loc = f"calculators.yaml:{cid}"
        if not isinstance(cdef, dict):
            report.add("ERROR", "CAL_001",
                       f"calculator is not a mapping: {cid}", loc)
            continue
        if cdef.get("status") != "live":
            continue  # reserved / draft 不强校

        # 必填字段
        missing = [k for k in REQUIRED_KEYS if not cdef.get(k)]
        if missing:
            report.add("ERROR", "CAL_001",
                       f"live calculator missing required keys {missing}: {cid}",
                       loc)

        # 决议 8 双锚: normative_basis_refs + evidence_anchor_refs 必须非空
        nbr = cdef.get("normative_basis_refs") or []
        ear = cdef.get("evidence_anchor_refs") or []
        if not nbr:
            report.add("ERROR", "CAL_001",
                       f"live calculator missing normative_basis_refs (决议 8 双锚): {cid}",
                       loc)
        if not ear:
            report.add("ERROR", "CAL_001",
                       f"live calculator missing evidence_anchor_refs (决议 8 双锚): {cid}",
                       loc)

        # authority_class 必须在决议 8 九类中
        AUTHORITY_ENUM = {
            "statute", "regulation", "mandatory_standard", "official_approval",
            "recommended_standard", "authoritative_guide", "meeting_memo",
            "expert_consensus", "expert_individual",
        }
        ac = cdef.get("authority_class")
        if ac and ac not in AUTHORITY_ENUM:
            report.add("ERROR", "CAL_001",
                       f"calculator authority_class '{ac}' not in 决议 8 九类: {cid}",
                       loc)

        # inputs / outputs 必须引用已登记 field id (dangling 由 CORE_CONTRACTS_001
        # 在通用 walk_refs 路径上处理, 这里只检查结构形状)
        inputs = cdef.get("inputs") or []
        if not isinstance(inputs, list) or len(inputs) == 0:
            report.add("ERROR", "CAL_001",
                       f"calculator inputs must be non-empty list: {cid}",
                       loc)
        else:
            for i, inp in enumerate(inputs):
                if not isinstance(inp, dict) or "ref" not in inp:
                    report.add("ERROR", "CAL_001",
                               f"calculator input[{i}] missing 'ref': {cid}",
                               loc)

        outputs = cdef.get("outputs") or []
        if not isinstance(outputs, list) or len(outputs) == 0:
            report.add("ERROR", "CAL_001",
                       f"calculator outputs must be non-empty list: {cid}",
                       loc)
        else:
            for i, out in enumerate(outputs):
                if not isinstance(out, dict) or "ref" not in out:
                    report.add("ERROR", "CAL_001",
                               f"calculator output[{i}] missing 'ref': {cid}",
                               loc)
                    continue
                # Step 11B: record-type output 必须声明 record_keys 非空
                shape = out.get("shape")
                if shape == "record":
                    record_keys = out.get("record_keys")
                    if not isinstance(record_keys, list) or len(record_keys) == 0:
                        report.add("ERROR", "CAL_001",
                                   f"calculator output[{i}] shape=record must "
                                   f"declare non-empty record_keys: {cid}",
                                   loc)

        # override_resolution.enabled 在 v0 必须为 false (决议 9: v0 不消费 override)
        ores = cdef.get("override_resolution") or {}
        if isinstance(ores, dict) and ores.get("enabled") is True:
            report.add("ERROR", "CAL_001",
                       f"calculator override_resolution.enabled=true 违反决议 9 "
                       f"(v0 不消费 override): {cid}",
                       loc)


def lint_source_provenance(registries, report: LintReport):
    """
    SOURCE_AUTH_001 (决议 8 来源铁律, v0 宽松口径):

    扫描所有 v0 生效对象, 只对**明显缺失来源锚**的对象发 INFO。
    宽松口径三条:
      (1) 只检测"完全缺 source_rule_id / source / 等价字段"的对象
      (2) 不校验本批次新引入的字段 (authority_class / sample_usage_mode /
          normative_basis_refs / evidence_anchor_refs / precedence_rank)
      (3) reserved 文件按既有规则继续豁免 (load_registries 已 pop)

    本批次严重度: INFO
    升级节奏: v0 INFO → v1 WARN → v2 ERROR
    """
    # 对各 registry 的"来源锚字段"做适配: 每个 registry 的字段名可能
    # 不同 (source / source_rule_id / source_ref / ...), 统一走等价集合
    EQUIV_ANCHOR_KEYS = (
        "source_rule_id",
        "source",
        "source_ref",
        "source_refs",
        "normative_basis_refs",  # 新字段, 若已填也算已锚
    )

    def has_source_anchor(entity: Any) -> bool:
        if not isinstance(entity, dict):
            return False
        for k in EQUIV_ANCHOR_KEYS:
            v = entity.get(k)
            if v is None:
                continue
            # 空字符串 / 空列表 不算有效锚点
            if isinstance(v, str) and v.strip():
                return True
            if isinstance(v, list) and len(v) > 0:
                return True
            if isinstance(v, dict) and len(v) > 0:
                return True
        return False

    # --- Obligations ---
    if "obligations" in registries:
        obs = registries["obligations"].get("obligations") or {}
        for oid, odef in obs.items():
            if not has_source_anchor(odef):
                report.add("INFO", "SOURCE_AUTH_001",
                           f"obligation missing source anchor (source_rule_id/etc): {oid}",
                           f"obligations.yaml:{oid}")

    # --- Fields ---
    # 宽松口径: field.fact.* 是 evidence 源头, 它们的"来源"就是项目输入本身,
    # 不是规范条款, 所以整体豁免 SOURCE_AUTH_001 扫描。
    # 只扫 field.derived.* — derived 字段必须能追溯到"根据什么规则 / 公式推导",
    # 这正是决议 8 要显影的"关键缺口"。
    if "fields" in registries:
        fields = registries["fields"].get("fields") or {}
        for fid, fdef in fields.items():
            if not isinstance(fdef, dict):
                continue
            if fdef.get("placeholder") is True:
                continue
            # 只扫 derived 字段
            if not fid.startswith("field.derived."):
                continue
            if not has_source_anchor(fdef):
                report.add("INFO", "SOURCE_AUTH_001",
                           f"derived field missing source anchor: {fid}",
                           f"fields.yaml:{fid}")

    # --- Artifacts ---
    if "artifacts" in registries:
        arts = registries["artifacts"].get("artifacts") or {}
        for aid, adef in arts.items():
            if not isinstance(adef, dict):
                continue
            # artifact 的"来源"可以是 data_source_refs / source_rule_id / normative_basis_refs
            has_anchor = has_source_anchor(adef) or bool(adef.get("data_source_refs"))
            if not has_anchor:
                report.add("INFO", "SOURCE_AUTH_001",
                           f"artifact missing source anchor (source/data_source_refs): {aid}",
                           f"artifacts.yaml:{aid}")

    # --- Assurances ---
    if "assurances" in registries:
        ass = registries["assurances"].get("assurances") or {}
        for asid, asdef in ass.items():
            if not has_source_anchor(asdef):
                report.add("INFO", "SOURCE_AUTH_001",
                           f"assurance missing source anchor: {asid}",
                           f"assurances.yaml:{asid}")


# ------------------------------------------------------------------
# Region Override Reserved-only Lint Skeletons (决议 9)
# ------------------------------------------------------------------
# 以下三个函数是 Step 10 预埋的 reserved-only lint 规则骨架。
# 本批次不进入 main() 默认执行序列, 不污染 v0 绿灯。
# v1 启用 Region Override 时通过 --include-reserved 开关激活。
#
# 调用方式 (未来 v1):
#     lint_region_override_target_refs(reserved_registries, report)
#     lint_region_override_provenance(reserved_registries, report)
#     lint_region_override_conflict_keys(reserved_registries, report)
# ------------------------------------------------------------------

def lint_region_override_target_refs(reserved_registries, report: LintReport):
    """
    REGION_OVERRIDE_001 (决议 9 预埋, reserved-only, 骨架):

    校验 RegionOverridePrototype 中每个 override.target_ref 是否能
    resolve 到已登记的 field.* / ob.* / art.* / as. id。
    v1 启用时对正式 RegionOverrideRegistry_v1.yaml 做 dangling 检查。

    当前状态: SKELETON ONLY - 不进入 main() 默认执行序列
    """
    # TODO(v1): 解析 reserved_registries['region_override_prototype']
    # TODO(v1): 对每个 override.target_ref 查 collect_defined_ids
    # TODO(v1): dangling 时发 ERROR
    pass


def lint_region_override_provenance(reserved_registries, report: LintReport):
    """
    REGION_OVERRIDE_002 (决议 9 预埋, reserved-only, 骨架):

    校验两件事:
      (1) 每个 override 的 provenance 字段完整性:
          normative_basis_refs / authority_class / precedence_rank /
          effective_since / issued_by_scope / provenance_verified
      (2) target_attribute_path 必须命中 override_capable_slots 登记表中
          显式声明的 override-capable 槽位。

    当前状态: SKELETON ONLY - 不进入 main() 默认执行序列
    """
    # TODO(v1): 解析 override_capable_slots 节为 (target_ref, path) 查找表
    # TODO(v1): 对每个 override 校验 provenance 六字段齐全
    # TODO(v1): 对 target_attribute_path 做槽位命中校验,
    #           未命中者发 ERROR (决议 9 核心硬门槛)
    # TODO(v1): authority_class 必须在决议 8 九类之中
    # TODO(v1): provenance_verified = false 的 override 不得 status = active
    pass


def lint_region_override_conflict_keys(reserved_registries, report: LintReport):
    """
    REGION_OVERRIDE_003 (决议 9 预埋, reserved-only, 骨架):

    校验三件事:
      (1) 冲突消解键合法性: precedence_rank / effective_since /
          issued_by_scope / manual_arbitration 的取值合规
      (2) refine_applicability action 必须严格收窄, 不放宽
          (对 payload.narrower_scope 做集合包含检查)
      (3) region_scope.province 不得取 "*"
          (province="*" 意味着全国生效, 违反决议 9 核心第 1 条)

    当前状态: SKELETON ONLY - 不进入 main() 默认执行序列
    """
    # TODO(v1): 遍历 overrides.*, 对 region_scope.province 做 != "*" 硬校验
    # TODO(v1): 对 action == refine_applicability 的 override,
    #           比对 payload.narrower_scope 与 target 的原 applicability,
    #           若出现"放宽"(新的 scope 包含更多项), 直接 ERROR
    # TODO(v1): 冲突消解键取值合法性校验
    pass


def lint_obligation_structure(registries, report: LintReport):
    """OBL_001 / OBL_005 + CORE_CONTRACTS_007 on obligations"""
    if "obligations" not in registries:
        return
    obs = registries["obligations"].get("obligations") or {}
    required_six = {"obligation_id", "source_rule_id", "requirement_type",
                    "required_artifact_refs", "required_assurance_refs", "status"}

    for key, odef in obs.items():
        if not isinstance(odef, dict):
            report.add("ERROR", "OBL_001", f"obligation is not a mapping: {key}",
                       f"obligations.yaml:{key}")
            continue

        # OBL_001: 决议 2 的六字段
        missing = required_six - set(odef.keys())
        if missing:
            report.add("ERROR", "OBL_001",
                       f"obligation missing six-field: {key} -> missing {sorted(missing)}",
                       f"obligations.yaml:{key}")

        # OBL_005: obligation_id 必须与 yaml key 一致
        obid = odef.get("obligation_id")
        if obid and obid != key:
            report.add("ERROR", "OBL_005",
                       f"obligation_id '{obid}' does not match yaml key '{key}'",
                       f"obligations.yaml:{key}")

        # CORE_CONTRACTS_007 对 obligation 同样适用
        if "protection_level" not in odef:
            report.add("WARN", "CORE_CONTRACTS_007",
                       f"obligation missing protection_level (not in required six, but strongly recommended): {key}",
                       f"obligations.yaml:{key}")


def lint_artifact_structure(registries, report: LintReport):
    """ART_001 ~ ART_006 — artifact registry 结构校验"""
    if "artifacts" not in registries:
        return
    arts = registries["artifacts"].get("artifacts") or {}
    required_keys = {"kind", "canonical_name", "source", "requirement"}

    for aid, adef in arts.items():
        if not isinstance(adef, dict):
            report.add("ERROR", "ART_001", f"artifact is not a mapping: {aid}",
                       f"artifacts.yaml:{aid}")
            continue

        # 子制品 (有 parent) 允许从 parent 继承 source / requirement
        parent_id = adef.get("parent")
        inheritable = set()
        if parent_id and parent_id in arts:
            parent = arts[parent_id]
            if isinstance(parent, dict):
                inheritable = {"source", "requirement"}

        for k in required_keys:
            if k not in adef and k not in inheritable:
                report.add("ERROR", "ART_001",
                           f"artifact missing required field '{k}': {aid}",
                           f"artifacts.yaml:{aid}")

        # ART_002: conditional artifact 必须有 condition.trigger_obligation_id(s)
        if adef.get("requirement") == "conditional":
            cond = adef.get("condition") or {}
            if not (cond.get("trigger_obligation_id") or cond.get("trigger_obligation_ids")):
                report.add("ERROR", "ART_002",
                           f"conditional artifact missing trigger_obligation_id(s): {aid}",
                           f"artifacts.yaml:{aid}.condition")

        # ART_006: chapter_ref 必须是 sec.* 或 None
        chapter_ref = adef.get("chapter_ref")
        if chapter_ref is not None and not str(chapter_ref).startswith("sec."):
            report.add("ERROR", "ART_006",
                       f"chapter_ref must be sec.* or null: {aid} -> {chapter_ref}",
                       f"artifacts.yaml:{aid}.chapter_ref")

        # kind 必须在 enum
        kind = adef.get("kind")
        if kind and kind not in ART_KIND_ENUM:
            report.add("ERROR", "ART_001",
                       f"artifact kind '{kind}' not in {sorted(ART_KIND_ENUM)}: {aid}",
                       f"artifacts.yaml:{aid}.kind")


# ------------------------------------------------------------------
# 输出
# ------------------------------------------------------------------
ANSI = {
    "ERROR":   "\033[31m",   # red
    "WARN":    "\033[33m",   # yellow
    "PENDING": "\033[36m",   # cyan
    "INFO":    "\033[90m",   # bright black
    "RESET":   "\033[0m",
    "BOLD":    "\033[1m",
}

def pretty_print(report: LintReport, missing: list[str], reserved_files: list[str] | None = None):
    use_color = sys.stdout.isatty()
    def colored(text, color):
        if use_color:
            return f"{ANSI[color]}{text}{ANSI['RESET']}"
        return text

    print(colored("=" * 72, "BOLD"))
    print(colored(" CPSWC Cross-Registry Lint Report", "BOLD"))
    print(colored("=" * 72, "BOLD"))

    # 缺失文件
    if missing:
        print()
        print(colored("Registries not yet produced:", "PENDING"))
        for m in missing:
            print(f"  - {m}")

    # 前向兼容预埋文件 (已识别, 不纳入 v0 lint, 但提示用户它们存在)
    if reserved_files:
        print()
        print(colored(f"Reserved files detected (excluded from v0 lint): {len(reserved_files)}", "INFO"))
        for f in reserved_files:
            print(colored(f"  - {f}", "INFO"))
        print(colored("  (Forward-Compat Reservation Clause; use --include-reserved for v1 plan lint)", "INFO"))

    # 按严重度分组
    by_sev = {s: [] for s in SEVERITIES}
    for f in report.findings:
        by_sev[f.severity].append(f)

    for sev in SEVERITIES:
        items = by_sev[sev]
        if not items:
            continue
        print()
        print(colored(f"[{sev}]  {len(items)} finding(s)", sev))
        for f in items:
            line = f"  {f.rule:22s}  {f.message}"
            loc = f"       at {f.location}"
            print(colored(line, sev))
            print(colored(loc, "INFO"))

    # 汇总
    print()
    print(colored("-" * 72, "BOLD"))
    print("Summary: " + "  ".join(
        f"{colored(sev, sev)}={report.count(sev)}" for sev in SEVERITIES
    ))
    print(colored("-" * 72, "BOLD"))


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------
def main():
    json_mode = "--json" in sys.argv

    registries, missing = load_registries()

    # 提取预埋文件清单后从 registries 里移除, 避免污染后续 lint 迭代
    reserved_files = registries.pop("_reserved_files_detected", [])

    # 最低要求: fields + contracts
    if "contracts" not in registries:
        print("ERROR: CPSWC_CORE_CONTRACTS.yaml 未找到", file=sys.stderr)
        return 2
    if "fields" not in registries:
        print("ERROR: FieldIdentityRegistry_v0.yaml 未找到", file=sys.stderr)
        return 2

    report = LintReport()
    defined_ids = collect_defined_ids(registries)

    # 执行 lint 规则
    lint_id_formats(registries, report)
    lint_dangling_refs(registries, defined_ids, report)
    lint_field_protection_levels(registries, report)
    lint_expert_switch_governance(registries, report)  # 决议 6
    lint_source_provenance(registries, report)          # 决议 8
    lint_calculator_structure(registries, report)       # Step 11A (CAL_001)
    lint_artifact_structure(registries, report)
    lint_obligation_structure(registries, report)

    if json_mode:
        out = {
            "missing_registries": missing,
            "reserved_files_detected": reserved_files,
            "findings": [f.to_dict() for f in report.findings],
            "summary": {sev: report.count(sev) for sev in SEVERITIES},
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        pretty_print(report, missing, reserved_files)

    return 1 if report.count("ERROR") > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
