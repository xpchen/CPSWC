"""
rule_registry.py — `rule.*` 依据 ID 的解析

任务来源: DECISION_LOG 条目 015 清点出的第一号缺口 ——
**53 个 `rule.*` 依据 ID, 已登记标题 0 个**。报告里每句"依据 XXX"
都指向一个空壳, 无法向审查人员出示条文, 也无法核对引用是否正确。

本模块负责把 `registries/RuleRegistry_v0.yaml` 读进来, 并回答一个问题:
**这个依据 ID 指向哪部规范的哪一条, 核到什么程度了?**

三态, 一个都不许含糊:

    VERIFIED_TEXT  条文原文已从本地原件抽取并核对; quoted_text 非空
    DECLARED       已定位到文件 (可选到章/条), 但没抓原文
    UNREGISTERED   不在注册表里 —— 系统不知道它指向哪一条

**DECLARED 不许带 quoted_text。** 带了就等于声称核对过,
而"看起来像证据的东西"比没有证据更危险。`lint_rule_registry()` 会拦。

### 继承

子条目可以用 `parent_rule_id` 继承父条的文件级字段 (document_title /
document_number / source_file / …), 只覆盖 clause_ref 等自己的部分。
这样 `rule.template_2026.section_7` 不必把 232 号的文件信息抄 17 遍。
**verification_status 不继承** —— 父条核过不代表子条核过。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cpswc.paths import REGISTRIES_DIR, PROJECT_ROOT

SCHEMA_VERSION = "rule_registry_v0"

VERIFIED_TEXT = "VERIFIED_TEXT"
DECLARED = "DECLARED"
UNREGISTERED = "UNREGISTERED"

VERIFICATION_STATES = (VERIFIED_TEXT, DECLARED, UNREGISTERED)

# 子条目可从 parent_rule_id 继承的字段。**刻意不含 verification_status
# 与 quoted_text** —— 父条核对过, 不代表子条也核对过。
_INHERITABLE = (
    "document_title", "document_number", "issuing_authority",
    "authority_class", "issued_at", "effective_from", "mandatory_from",
    "source_file", "source_locator",
)

_DEFAULT_PATH = REGISTRIES_DIR / "RuleRegistry_v0.yaml"


def load_rule_registry(path: Path | None = None) -> dict:
    """读注册表。返回原始 dict (含 rules / unregistered_namespaces)。"""
    p = Path(path or _DEFAULT_PATH)
    if not p.exists():
        raise FileNotFoundError(f"找不到 RuleRegistry: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"RuleRegistry schema_version 不匹配: 期望 {SCHEMA_VERSION}, "
            f"实为 {data.get('schema_version')!r}")
    return data


def resolve_rule(rule_id: str, registry: dict | None = None) -> dict:
    """
    解析一个依据 ID。**永远返回一个 dict**, 不抛 KeyError ——
    未登记本身就是要显示出来的信息, 不是异常。

    返回:
      registered        是否在注册表里
      verification_status  三态之一
      text_verified     是否有核对过的原文 (VERIFIED_TEXT 且 quoted_text 非空)
      clause_located    是否定位到了具体条款 (clause_ref 非空)
      document_title / document_number / clause_ref / quoted_text / …
      defect            该条自身或其引用方的已知缺陷码 (可空)
    """
    regs = registry if registry is not None else load_rule_registry()
    rules = regs.get("rules") or {}
    entry = rules.get(rule_id)

    if not isinstance(entry, dict):
        return {
            "rule_id": rule_id,
            "registered": False,
            "verification_status": UNREGISTERED,
            "text_verified": False,
            "clause_located": False,
            "document_title": "", "document_number": "",
            "issuing_authority": "", "authority_class": "",
            "issued_at": "", "effective_from": "", "mandatory_from": "",
            "clause_ref": "", "quoted_text": "",
            "source_file": "", "source_locator": "",
            "verified_at": "", "verification_note": "",
            "defect": "", "defect_note": "",
        }

    merged: dict[str, Any] = {}
    parent_id = entry.get("parent_rule_id")
    if parent_id:
        # 单层继承就够用; 深链会让"这条到底核没核过"更难说清, v0 不开
        parent = rules.get(parent_id) or {}
        for k in _INHERITABLE:
            if parent.get(k):
                merged[k] = parent[k]
    merged.update({k: v for k, v in entry.items() if v not in (None,)})

    status = merged.get("verification_status") or DECLARED
    quoted = (merged.get("quoted_text") or "").strip()

    return {
        "rule_id": rule_id,
        "registered": True,
        "verification_status": status,
        "text_verified": status == VERIFIED_TEXT and bool(quoted),
        "clause_located": bool((merged.get("clause_ref") or "").strip()),
        "document_title": merged.get("document_title") or "",
        "document_number": merged.get("document_number") or "",
        "issuing_authority": merged.get("issuing_authority") or "",
        "authority_class": merged.get("authority_class") or "",
        "issued_at": str(merged.get("issued_at") or ""),
        "effective_from": str(merged.get("effective_from") or ""),
        "mandatory_from": str(merged.get("mandatory_from") or ""),
        "clause_ref": merged.get("clause_ref") or "",
        "quoted_text": quoted,
        "source_file": merged.get("source_file") or "",
        "source_locator": merged.get("source_locator") or "",
        "verified_at": str(merged.get("verified_at") or ""),
        "verification_note": (merged.get("verification_note") or "").strip(),
        "defect": merged.get("defect") or "",
        "defect_note": (merged.get("defect_note") or "").strip(),
        "parent_rule_id": parent_id or "",
    }


def summarize_rule_coverage(cited_ids: list[str],
                            registry: dict | None = None) -> dict:
    """对一批被引用的 ID 出一份覆盖统计。**不给单一百分比。**

    压成一个"依据覆盖率 78%"会立刻抹掉最要紧的区别:
    "定位到文件了"和"条文核对过了"完全是两回事。
    """
    regs = registry if registry is not None else load_rule_registry()
    total = len(cited_ids)
    verified = declared = unregistered = 0
    located = 0
    defects: list[dict] = []
    for rid in cited_ids:
        r = resolve_rule(rid, regs)
        if not r["registered"]:
            unregistered += 1
        elif r["text_verified"]:
            verified += 1
        else:
            declared += 1
        if r["clause_located"]:
            located += 1
        if r["defect"]:
            defects.append({"rule_id": rid, "defect": r["defect"],
                            "defect_note": r["defect_note"]})
    return {
        "cited_total": total,
        "text_verified": verified,
        "declared": declared,
        "unregistered": unregistered,
        "clause_located": located,
        "defects": defects,
        "unregistered_namespaces": list(regs.get("unregistered_namespaces") or []),
    }


# ============================================================
# lint
# ============================================================

def lint_rule_registry(registry: dict | None = None,
                       root: Path | None = None) -> list[str]:
    """
    注册表自检。返回问题清单, 空 = 通过。

    盯的都是"看起来像证据但其实不是"的情况:
      · VERIFIED_TEXT 却没有 quoted_text  → 谎称核对过
      · DECLARED 却带 quoted_text          → 没核对却贴了原文
      · source_file 指向不存在的文件       → 出处查无此文
      · parent_rule_id 指向不存在的条目    → 继承落空, 字段全空
    """
    regs = registry if registry is not None else load_rule_registry()
    base = Path(root or PROJECT_ROOT)
    rules = regs.get("rules") or {}
    problems: list[str] = []

    for rid, entry in rules.items():
        if not isinstance(entry, dict):
            problems.append(f"{rid}: 条目不是对象")
            continue

        status = entry.get("verification_status")
        if status not in (VERIFIED_TEXT, DECLARED):
            problems.append(
                f"{rid}: verification_status 必须是 {VERIFIED_TEXT} 或 "
                f"{DECLARED}, 实为 {status!r}")

        quoted = (entry.get("quoted_text") or "").strip()
        if status == VERIFIED_TEXT and not quoted:
            problems.append(f"{rid}: 声称 VERIFIED_TEXT 却没有 quoted_text")
        if status == DECLARED and quoted:
            problems.append(
                f"{rid}: DECLARED 不得带 quoted_text —— 贴了原文就等于声称核对过")

        parent = entry.get("parent_rule_id")
        if parent and parent not in rules:
            problems.append(f"{rid}: parent_rule_id {parent} 不存在")
        if parent and rules.get(parent, {}).get("parent_rule_id"):
            problems.append(f"{rid}: v0 只允许单层继承, {parent} 自身也有父条")

        resolved = resolve_rule(rid, regs)
        if not resolved["document_title"]:
            problems.append(f"{rid}: 解析后仍没有 document_title")

        src = resolved["source_file"]
        if not src:
            problems.append(f"{rid}: 解析后仍没有 source_file")
        elif not (base / src).exists():
            problems.append(f"{rid}: source_file 不存在 —— {src}")

        if status == VERIFIED_TEXT and not entry.get("verified_at"):
            problems.append(f"{rid}: VERIFIED_TEXT 必须写 verified_at")

    return problems


__all__ = [
    "SCHEMA_VERSION", "VERIFIED_TEXT", "DECLARED", "UNREGISTERED",
    "VERIFICATION_STATES", "load_rule_registry", "resolve_rule",
    "summarize_rule_coverage", "lint_rule_registry",
]
