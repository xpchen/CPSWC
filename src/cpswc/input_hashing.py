"""
input_hashing.py — CPSWC P0-06 冻结输入、哈希与审核失效

任务来源: docs/report_production_plan/03_P0_TASKS.md P0-06
接口依据: 04_CONTRACTS_AND_ACCEPTANCE.md 第 7 节
批准记录: implementation/DECISION_LOG.md 条目 008 (B 批)

修的是 P0_BASELINE 的 D10: `freeze_submission` 里那个叫 `fact_snapshot_hash`
的东西, 散列的其实是 `derived_fields`。实测把项目名换成完全不同的字符串,
该 hash **一字不变** —— 也就是说"事实变没变"这个判断从来没成立过。

本模块提供两个分工明确的 hash (04 文档第 7 节):

    fact_snapshot_hash     规范化后的**事实集合**本身。
                           事实不变而来源版本变动时它可以不变 ——
                           所以它**不能单独决定**审核是否仍然有效。

    generation_input_hash  事实 + 预存派生量的来源与状态 + 项目静态 profile
                           + 规则/registry 摘要 + 模板摘要 + 计算实现版本。
                           **审核有效性、重生成与变更判定都看它。**

运行时间、run ID、临时输出路径一律**不进**语义 hash: 同一份输入在不同时间
跑两次, 语义 hash 必须相同 (验收 F03)。

发布文件的 SHA256 另算 (`content_hash`), 那只证明文件完整性, 不证明内容正确。
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

# 语义 hash 的 schema 版本。**改变任何规范化规则都必须改这个版本号** ——
# 否则新旧 hash 会在同一个命名空间里互相冒充。
HASH_SCHEMA_VERSION = "cpswc_hash_v1"

# 旧包没有这个字段。加载时据此判定 legacy, 不重算、不覆盖 (验收 F05)。
LEGACY_SCHEMA_MARKER = "legacy_unverified"


class NonFiniteNumberError(ValueError):
    """语义 hash 拒绝 NaN / inf。它们不是确定的值, 不能参与内容寻址。"""


# ============================================================
# 1. canonical JSON
# ============================================================

def _canonical(obj: Any, path: str = "") -> Any:
    """
    规范化用于 hash 的结构。

    规则 (04 文档第 7 节):
      - dict 按 key 排序; key 统一转 str
      - **有序数组保留顺序** —— 只对显式声明为集合的列表另行排序, 本函数不猜
      - bool 先于 int 判断 (bool 是 int 的子类)
      - 整值浮点归一为 int, 避免 3.0 与 3 产生不同 hash
      - NaN / inf 直接报错, 不静默替换
    """
    if isinstance(obj, dict):
        return {str(k): _canonical(obj[k], f"{path}.{k}") for k in sorted(obj, key=str)}
    if isinstance(obj, (list, tuple)):
        return [_canonical(x, f"{path}[{i}]") for i, x in enumerate(obj)]
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise NonFiniteNumberError(
                f"{path or '<root>'}: 非有限数 {obj!r} 不能参与语义 hash")
        return int(obj) if obj.is_integer() else obj
    if isinstance(obj, (int, str)) or obj is None:
        return obj
    return str(obj)


def canonical_json(obj: Any) -> str:
    """确定性 JSON 串。同一语义内容必得同一串。"""
    return json.dumps(_canonical(obj), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_of(obj: Any) -> str:
    return _sha256(canonical_json(obj))


# ============================================================
# 2. 事实哈希
# ============================================================

def fact_snapshot_hash(facts: dict | None) -> str:
    """
    规范化**事实集合**的内容哈希。

    这是 D10 的修复点: 原实现散列的是 derived_fields, 于是改项目名 hash 不变。
    现在改一个字也会变 (验收 F01)。
    """
    return _sha256(canonical_json({
        "schema": HASH_SCHEMA_VERSION,
        "kind": "fact_snapshot",
        "facts": facts or {},
    }))


# ============================================================
# 3. 来源摘要
# ============================================================

def file_digest(path: Path) -> str:
    """单个文件内容的 sha256。文件不存在返回哨兵值, 不假装成功。"""
    p = Path(path)
    if not p.exists():
        return "MISSING"
    return hashlib.sha256(p.read_bytes()).hexdigest()


def directory_digest(directory: Path, patterns: Iterable[str] = ("*.yaml",)) -> str:
    """
    目录内容摘要 (按相对路径排序后串联各文件的 sha256)。

    用于 registry / governance: **文件内容变了, 即使文件名与数值不变,
    生成输入 hash 也要变** (验收 F04)。
    """
    d = Path(directory)
    if not d.exists():
        return "MISSING"
    entries: list[tuple[str, str]] = []
    for pattern in patterns:
        for f in sorted(d.rglob(pattern)):
            if f.is_file():
                entries.append((str(f.relative_to(d)), file_digest(f)))
    return _sha256(canonical_json(sorted(entries)))


def template_digest(package_dir: Path) -> str:
    """narrative 模板源码摘要。模板改了, 生成输入就变了。"""
    return directory_digest(package_dir, patterns=("*.py",))


def collect_input_digests(*, registries_dir: Path, governance_dir: Path,
                          templates_dir: Path,
                          extra_sources: dict[str, Path] | None = None) -> dict:
    """
    收集本次生成实际消费的来源摘要。

    **不含**运行时间、run ID、输出路径 —— 那些是审计元数据, 不是输入。
    """
    digests = {
        "hash_schema_version": HASH_SCHEMA_VERSION,
        "registries": directory_digest(registries_dir),
        "governance": directory_digest(governance_dir),
        "narrative_templates": template_digest(templates_dir),
    }
    for name, path in (extra_sources or {}).items():
        digests[f"source:{name}"] = file_digest(Path(path))
    return digests


# ============================================================
# 4. 生成输入哈希
# ============================================================

def generation_input_hash(*,
                          facts: dict | None,
                          pre_stored_derived: dict | None = None,
                          source_map: dict | None = None,
                          profile: dict | None = None,
                          input_digests: dict | None = None,
                          calculator_versions: dict | None = None,
                          ruleset: str = "") -> str:
    """
    覆盖"这一次生成到底吃了什么"的语义哈希。

    组成 (04 文档第 7 节):
      事实 + 预存派生量 + 各字段实际选用的来源层 + 静态 profile
      + 规则/registry/模板摘要 + 计算实现版本 + 规则集标识

    **排除**: 运行时间、run ID、snapshot_id、临时目录。
    因此同一语义输入重复执行, 本 hash 不变 (验收 F03)。
    """
    payload = {
        "schema": HASH_SCHEMA_VERSION,
        "kind": "generation_input",
        "ruleset": ruleset,
        "facts": facts or {},
        "pre_stored_derived": pre_stored_derived or {},
        # 来源选择本身是输入的一部分: 同样的值取自不同层, 结论可能不同
        "source_map": source_map or {},
        "profile": profile or {},
        "input_digests": input_digests or {},
        "calculator_versions": calculator_versions or {},
    }
    return _sha256(canonical_json(payload))


# ============================================================
# 5. 冻结包的 hash 语义识别 (验收 F05)
# ============================================================

def describe_hash_schema(frozen: dict | None) -> dict:
    """
    判断一份冻结记录用的是哪一版 hash 语义。

    旧包没有 hash_schema_version —— **不重算、不覆盖**, 只如实标 legacy。
    重算后覆盖旧 manifest 会让历史签署看起来适用于新包, 那是最危险的一种"修复"。
    """
    f = frozen or {}
    version = f.get("hash_schema_version")
    if not version:
        return {
            "hash_schema_version": LEGACY_SCHEMA_MARKER,
            "is_legacy": True,
            "generation_input_hash_available": False,
            "note": ("该冻结记录产生于 P0-06 之前, 其 fact_snapshot_hash 散列的是 "
                     "derived_fields 而非事实集合, 不能用于判断事实是否变化; "
                     "也没有 generation_input_hash。**只读**, 不重算、不迁移。"),
        }
    return {
        "hash_schema_version": version,
        "is_legacy": version != HASH_SCHEMA_VERSION,
        "generation_input_hash_available": bool(f.get("generation_input_hash")),
        "note": ("当前 hash 语义" if version == HASH_SCHEMA_VERSION
                 else f"hash 语义版本 {version} 与当前 {HASH_SCHEMA_VERSION} 不同"),
    }


# ============================================================
# 6. 保守全量失效 (验收 F04 / F06)
# ============================================================

def invalidates_prior_review(previous_generation_input_hash: str | None,
                             current_generation_input_hash: str | None) -> bool:
    """
    之前的复核/签署确认是否已失效。

    P0 采用**保守全量失效**: 生成输入的任何一部分变了 (事实、来源层、规则、
    registry、模板、计算实现), 之前的确认都要重新检查。不实现精细增量 DAG。

    任一侧缺失 → 视为失效: 无法证明仍然适用, 就不能当作仍然适用。
    """
    if not previous_generation_input_hash or not current_generation_input_hash:
        return True
    return previous_generation_input_hash != current_generation_input_hash


__all__ = [
    "HASH_SCHEMA_VERSION", "LEGACY_SCHEMA_MARKER", "NonFiniteNumberError",
    "canonical_json", "digest_of", "fact_snapshot_hash",
    "file_digest", "directory_digest", "template_digest",
    "collect_input_digests", "generation_input_hash",
    "describe_hash_schema", "invalidates_prior_review",
]
