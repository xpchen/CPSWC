"""
condition_engine.py — CPSWC v0 ConditionEngine

宪法收口: 把 runtime.py 中的 trigger DSL 转换 + obligation 求值逻辑
抽取为独立模块, 对应 ARCHITECTURE_DECISIONS.md 决议 2 的 ConditionEngine 概念。

职责:
  1. 将 ObligationSet_v0.yaml 中的 trigger.when DSL 转为 Python 可求值表达式
  2. 对每条 obligation 求值, 产出 ObligationResult
  3. 解析 driven_by_obligation 级联触发
  4. 返回完整的 obligation 评估结果集

设计边界:
  - 纯函数, 不持有状态
  - 不加载 registry (由 runtime 传入)
  - 不做 override resolution (决议 9: v0 不消费 override)
  - DSL 语法集固定: any(...in[]), count(distinct(...)), count(),
    has_any(), field.X.value, bare field.X, AND/OR/NOT
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# ============================================================
# Result type (从 runtime.py 迁移, runtime.py 保留 re-export)
# ============================================================

@dataclass
class ObligationResult:
    """单条 obligation 的求值结果"""
    obligation_id: str
    triggered: bool | None  # None = pending (driven_by_obligation)
    mode: str
    py_expr: str


# ============================================================
# DSL → Python 转换
# ============================================================

def _get_field(path: str, unified: dict) -> Any:
    """从 unified lookup (facts + derived) 按 field id 取值"""
    return unified.get(path)


def _get_value(path: str, unified: dict) -> Any:
    """取值并处理 Quantity {value, unit} 结构"""
    v = _get_field(path, unified)
    if v is None:
        return 0
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    if isinstance(v, (int, float)):
        return v
    return 0


def transform_dsl(expr: str) -> str:
    """将 trigger.when DSL 转为 Python eval 可求值的表达式。

    支持的 DSL 语法:
      - any(field.X.Y.attr in [values])
      - count(distinct(field.X.Y.attr))
      - count(field.X.Y)
      - has_any(field.X.Y)
      - field.X.Y.value  (Quantity 取值)
      - field.X.Y        (裸引用)
      - AND / OR / NOT
      - true / false
      - "always" → "True"
    """
    if not expr or str(expr).strip().lower() == "always":
        return "True"
    s = re.sub(r"\s+", " ", str(expr)).strip()

    # any(field.X.Y.f in [values])
    def h_any_in(m: re.Match) -> str:
        list_path, attr, values = m.group(1), m.group(2), m.group(3)
        return (f'any(_item.get({attr!r}) in [{values}] '
                f'for _item in (_get_field({list_path!r}, unified) or []))')
    s = re.sub(r"any\((field\.[\w.]+?)\.(\w+)\s+in\s+\[([^\]]*)\]\)", h_any_in, s)

    # count(distinct(field.X.Y.f))
    def h_count_distinct(m: re.Match) -> str:
        list_path, attr = m.group(1), m.group(2)
        return (f'len(set(_item.get({attr!r}) '
                f'for _item in (_get_field({list_path!r}, unified) or [])))')
    s = re.sub(r"count\(distinct\((field\.[\w.]+?)\.(\w+)\)\)", h_count_distinct, s)

    # count(field.X.Y)
    s = re.sub(r"count\((field\.[\w.]+)\)",
               lambda m: f"len(_get_field({m.group(1)!r}, unified) or [])", s)

    # has_any(field.X.Y)
    s = re.sub(r"has_any\((field\.[\w.]+)\)",
               lambda m: f"bool(_get_field({m.group(1)!r}, unified))", s)

    # field.X.Y.value
    s = re.sub(r"(?<!')(field\.[\w.]+?)\.value\b",
               lambda m: f"_get_value({m.group(1)!r}, unified)", s)

    # bare field.X.Y
    s = re.sub(r"(?<!')field\.[\w.]+",
               lambda m: f"_get_field({m.group(0)!r}, unified)", s)

    s = re.sub(r"\bAND\b", " and ", s)
    s = re.sub(r"\bOR\b", " or ", s)
    s = re.sub(r"\bNOT\b", " not ", s)
    s = re.sub(r"(?<!')\btrue\b", "True", s)
    s = re.sub(r"(?<!')\bfalse\b", "False", s)
    return s


# ============================================================
# 单条 obligation 求值
# ============================================================

def evaluate_obligation(ob_id: str, ob_def: dict,
                        unified: dict) -> ObligationResult:
    """对单条 obligation 求值, 返回 ObligationResult"""
    trigger = ob_def.get("trigger") or {}
    mode = trigger.get("mode", "conditional")
    when = trigger.get("when", "")

    if mode == "always" or str(when).strip().lower() == "always":
        return ObligationResult(ob_id, True, mode, "True (always)")

    if mode == "driven_by_obligation":
        return ObligationResult(ob_id, None, mode, "pending driven_by")

    if not when:
        return ObligationResult(ob_id, False, mode, "no when clause")

    try:
        py_expr = transform_dsl(str(when))
    except Exception as e:
        return ObligationResult(ob_id, False, mode, f"DSL error: {e}")

    ns = {
        "_get_field": _get_field,
        "_get_value": _get_value,
        "unified": unified,
        "__builtins__": {"len": len, "set": set, "bool": bool, "any": any, "all": all},
    }
    try:
        result = eval(py_expr, ns)  # noqa: S307
    except Exception as e:
        return ObligationResult(ob_id, False, mode, f"eval error: {e} | {py_expr}")

    return ObligationResult(ob_id, bool(result), mode, py_expr)


# ============================================================
# 批量求值 + 级联解析
# ============================================================

@dataclass
class ConditionEngineResult:
    """ConditionEngine 的完整输出"""
    obligation_details: list[ObligationResult]
    triggered: set[str]
    not_triggered: set[str]


def evaluate_all(obligations_reg: dict, unified: dict) -> ConditionEngineResult:
    """
    对全部 obligations 求值, 含 driven_by_obligation 级联解析。

    参数:
      obligations_reg: ObligationSet_v0.yaml 的 obligations 节 (dict of ob_id → ob_def)
      unified: facts + derived 合并后的 field lookup

    返回:
      ConditionEngineResult
    """
    obligation_details: list[ObligationResult] = []
    triggered: set[str] = set()
    not_triggered: set[str] = set()

    # Pass 1: 直接求值
    for ob_id, ob_def in obligations_reg.items():
        if not isinstance(ob_def, dict):
            continue
        result = evaluate_obligation(ob_id, ob_def, unified)
        obligation_details.append(result)
        if result.triggered is True:
            triggered.add(ob_id)
        elif result.triggered is False:
            not_triggered.add(ob_id)

    # Pass 2: 解析 driven_by_obligation 级联
    for ob_result in obligation_details:
        if ob_result.triggered is not None:
            continue
        ob_def = obligations_reg.get(ob_result.obligation_id) or {}
        driven = (ob_def.get("trigger") or {}).get("driven_by_refs") or []
        if any(d in triggered for d in driven):
            ob_result.triggered = True
            triggered.add(ob_result.obligation_id)
        else:
            ob_result.triggered = False
            not_triggered.add(ob_result.obligation_id)

    return ConditionEngineResult(
        obligation_details=obligation_details,
        triggered=triggered,
        not_triggered=not_triggered,
    )
