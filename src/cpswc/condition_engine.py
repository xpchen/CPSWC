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

────────────────────────────────────────────────────────────────
P0-02 (docs/report_production_plan/03_P0_TASKS.md) 语义变更
────────────────────────────────────────────────────────────────
在此之前, "资料没给"、"DSL 写错了"、"条件确实不成立"三件事产出同一个结果:
triggered=False, 落进 not_triggered, 下游一律当作"本项目不涉及"。

现在三者分开:

    triggered=True   条件成立
    triggered=False  条件**可确定地**不成立 (所有依赖都读到了值)
    triggered=None   未知: 依赖缺失 / 值非法 / DSL 解析或求值出错 / 级联依赖未知

None **不进入 not_triggered**。求值异常**不再回落 False**。

求值改用 04 文档第 4 节的三值逻辑, 在 AST 上解释, 不再走 Python eval:

    NOT UNKNOWN   = UNKNOWN
    TRUE  AND UNKNOWN = UNKNOWN      FALSE AND UNKNOWN = FALSE
    TRUE  OR  UNKNOWN = TRUE         FALSE OR  UNKNOWN = UNKNOWN

为什么不用"整条表达式含缺失依赖就判 UNKNOWN"的保守做法: 实测惠南样本有
3 条本来**确定触发**的弃渣场义务 (site_selection / location_map /
separate_prevention_zone) 会因为 OR 的另一个分支缺字段而降级成未知, 反而
把本该要求的制品弄丢了。未知必须比 False 安全, 但不能比 True 还"安全"。

mode=always 的义务不受依赖缺失影响, 仍为 True (否则无关字段缺失会把全部
常规义务一起冲掉)。
"""

from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass, field as dc_field
from enum import Enum
from typing import Any


# ============================================================
# 求值状态
# ============================================================

class EvaluationStatus(str, Enum):
    """为什么得到这个 triggered 值。"""
    EVALUATED = "EVALUATED"                      # 依赖齐全, 结果可确定
    ALWAYS = "ALWAYS"                            # mode=always, 不依赖输入
    NO_CONDITION = "NO_CONDITION"                # 没有 when 子句
    UNKNOWN_MISSING_INPUT = "UNKNOWN_MISSING_INPUT"   # 依赖字段缺失/为空
    UNKNOWN_INVALID_INPUT = "UNKNOWN_INVALID_INPUT"   # 依赖字段值非法 (NaN/inf 等)
    UNKNOWN_DEPENDENCY = "UNKNOWN_DEPENDENCY"    # 级联依赖未知
    UNKNOWN_CYCLE = "UNKNOWN_CYCLE"              # 级联出现环或无法收敛
    UNKNOWN_DANGLING_REF = "UNKNOWN_DANGLING_REF"     # driven_by 指向不存在的义务
    ERROR_DSL = "ERROR_DSL"                      # DSL 无法转换
    ERROR_EVAL = "ERROR_EVAL"                    # 转换后求值抛异常


_UNKNOWN_STATUSES = frozenset({
    EvaluationStatus.UNKNOWN_MISSING_INPUT,
    EvaluationStatus.UNKNOWN_INVALID_INPUT,
    EvaluationStatus.UNKNOWN_DEPENDENCY,
    EvaluationStatus.UNKNOWN_CYCLE,
    EvaluationStatus.UNKNOWN_DANGLING_REF,
})

_ERROR_STATUSES = frozenset({
    EvaluationStatus.ERROR_DSL,
    EvaluationStatus.ERROR_EVAL,
})


# ============================================================
# Result type (从 runtime.py 迁移, runtime.py 保留 re-export)
# ============================================================

@dataclass
class ObligationResult:
    """单条 obligation 的求值结果。

    triggered:
      True  = 条件成立
      False = 条件可确定地不成立 (**不等于**已专业核验"完全不涉及")
      None  = 未知或出错 — 不得当作不涉及
    """
    obligation_id: str
    triggered: bool | None
    mode: str
    py_expr: str
    evaluation_status: EvaluationStatus = EvaluationStatus.EVALUATED
    missing_field_refs: list[str] = dc_field(default_factory=list)
    diagnostic_code: str = ""       # report_quality 的稳定码: CONDITION_UNKNOWN / CONDITION_ERROR
    diagnostic_message: str = ""
    field_refs: list[str] = dc_field(default_factory=list)

    @property
    def is_unknown(self) -> bool:
        return self.triggered is None

    @property
    def is_error(self) -> bool:
        return self.evaluation_status in _ERROR_STATUSES


# ============================================================
# DSL → 受限表达式 + 三值求值
# ============================================================
# 转换后的表达式只含 6 个取值函数 + 逻辑/比较节点。不再生成 `x or []`、
# 生成器表达式这类 Python 惯用法 —— 它们在"值上下文"和"布尔上下文"里含义
# 不同, 会让三值解释器无从下手, 也让未知被 `or []` 悄悄吞成空列表。

UNKNOWN = object()
"""三值逻辑的第三个值。与 None 区分: None 是一个合法的业务值, UNKNOWN 不是。"""


def _u(x: Any) -> bool:
    return x is UNKNOWN


class ConditionValueError(Exception):
    """条件求值失败的基类。不得被静默转成 False。"""


class ConditionInputError(ConditionValueError):
    """**输入**有问题 (类型不对、成员缺关键属性)。

    这类问题只让**所在分支**变 UNKNOWN, 再参与三值组合 ——
    不能让它掀掉整条表达式, 否则 `A OR B` 里 A 已确定为 True 也会丢失。
    """


class ConditionGrammarError(ConditionValueError):
    """**表达式**有问题 (解释器遇到闭集外的节点)。整条判 ERROR。"""


class _Reader:
    """DSL 的 6 个取值原语。读不到 → UNKNOWN, 从不返回 0 / [] / False 替代。"""

    def __init__(self, unified: dict) -> None:
        self.unified = unified
        self.missing: list[str] = []
        self.invalid: list[str] = []
        self.reasons: dict[str, str] = {}
        self.branch_errors: list[str] = []

    def note_branch_error(self, message: str) -> None:
        """登记一次分支级输入错误。分支判 UNKNOWN, 但错误本身不能消失。"""
        if message not in self.branch_errors:
            self.branch_errors.append(message)

    # ---- 内部 ----
    def _present(self, path: str) -> Any:
        """返回原始值或 UNKNOWN。缺键 / None / 空白串 → UNKNOWN 并登记。"""
        if path not in self.unified:
            if path not in self.missing:
                self.missing.append(path)
            return UNKNOWN
        v = self.unified[path]
        if v is None or (isinstance(v, str) and not v.strip()):
            if path not in self.missing:
                self.missing.append(path)
            return UNKNOWN
        return v

    def _mark_invalid(self, path: str, reason: str = "") -> Any:
        if path not in self.invalid:
            self.invalid.append(path)
        if reason:
            self.reasons.setdefault(path, reason)
        return UNKNOWN

    # ---- DSL 原语 ----
    def field(self, path: str) -> Any:
        """bare field.X — 取原始值。"""
        return self._present(path)

    def value(self, path: str) -> Any:
        """field.X.value — 取 Quantity 数值。0 和 False 是有效值, 照常返回。"""
        v = self._present(path)
        if _u(v):
            return UNKNOWN
        if isinstance(v, dict) and "value" in v:
            inner = v["value"]
            if inner is None or (isinstance(inner, str) and not inner.strip()):
                if path not in self.missing:
                    self.missing.append(path)
                return UNKNOWN
            v = inner
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                return self._mark_invalid(path)
            return v
        if isinstance(v, str):
            try:
                parsed = float(v)
            except ValueError:
                return self._mark_invalid(path, f"{v!r} 不是合法数字")
            # float("NaN") / float("inf") / float("-Infinity") 都会成功。
            # 不查有限性的话: NaN > 0 静默判 False, inf > 0 更会**伪造出一个触发**。
            if math.isnan(parsed) or math.isinf(parsed):
                return self._mark_invalid(path, f"{v!r} 解析为非有限数")
            return parsed
        raise ConditionInputError(
            f"{path}: 值类型 {type(v).__name__} 不能作为 .value 参与比较")

    def has_any(self, path: str) -> Any:
        """has_any(field.X) — 空列表是"提供了空列表", 判 False; 缺键才是 UNKNOWN。"""
        v = self._present(path)
        if _u(v):
            return UNKNOWN
        return bool(v)

    def count(self, path: str) -> Any:
        """count(field.X) — 只数个数, 与成员内容无关, 因此不受成员缺属性影响。"""
        v = self._present(path)
        if _u(v):
            return UNKNOWN
        if not isinstance(v, (list, tuple, dict, str)):
            raise ConditionInputError(f"{path}: 值不是集合, 无法 count()")
        return len(v)

    def count_distinct(self, path: str, attr: str) -> Any:
        v = self._present(path)
        if _u(v):
            return UNKNOWN
        if not isinstance(v, (list, tuple)):
            raise ConditionInputError(f"{path}: 值不是列表, 无法 count(distinct())")
        vals = set()
        for item in v:
            got = self._member_attr(path, item, attr)
            if _u(got):
                return UNKNOWN     # 有成员读不到该属性 → 去重结果不可确定
            vals.add(got)
        return len(vals)

    def any_in(self, path: str, attr: str, values: list) -> Any:
        """any(field.X.attr in [...]) — 成员级三值。

        "提供了清单但成员缺关键属性" 与 "清单里明确没有匹配项" 是两回事:
        前者读不出结论。成员级同样按三值组合 ——
        只要有一个成员确定命中就是 True; 否则只要有成员读不到属性就是 UNKNOWN。
        """
        v = self._present(path)
        if _u(v):
            return UNKNOWN
        if not isinstance(v, (list, tuple)):
            raise ConditionInputError(f"{path}: 值不是列表, 无法 any(... in [...])")
        saw_unknown = False
        for item in v:
            got = self._member_attr(path, item, attr)
            if _u(got):
                saw_unknown = True
                continue
            if got in values:
                return True        # 有确定命中 → TRUE OR UNKNOWN = TRUE
        return UNKNOWN if saw_unknown else False

    def _member_attr(self, path: str, item: Any, attr: str) -> Any:
        """读列表成员的属性。缺键 / None → UNKNOWN 并登记。"""
        if isinstance(item, dict):
            if attr not in item:
                self._mark_invalid(path, f"清单成员缺少属性 {attr!r}")
                return UNKNOWN
            got = item[attr]
            if got is None:
                self._mark_invalid(path, f"清单成员的 {attr!r} 为 None")
                return UNKNOWN
            return got
        return item


_READER_METHODS = {
    "_field": "field",
    "_value": "value",
    "_has_any": "has_any",
    "_count": "count",
    "_count_distinct": "count_distinct",
    "_any_in": "any_in",
}


def transform_dsl(expr: str, refs: list[str] | None = None) -> str:
    """将 trigger.when DSL 转为受限的中间表达式 (供 AST 三值解释)。

    支持的 DSL 语法 (闭集, 本任务不扩展):
      - any(field.X.Y.attr in [values])   → _any_in('field.X.Y', 'attr', [values])
      - count(distinct(field.X.Y.attr))   → _count_distinct('field.X.Y', 'attr')
      - count(field.X.Y)                  → _count('field.X.Y')
      - has_any(field.X.Y)                → _has_any('field.X.Y')
      - field.X.Y.value                   → _value('field.X.Y')
      - field.X.Y                         → _field('field.X.Y')
      - AND / OR / NOT / true / false
      - "always" → "True"

    参数:
      refs: 传入一个 list 时, 把表达式依赖的 field id 按出现顺序收集进去。
            收集与替换共用同一组正则, 保证依赖清单与实际求值路径一致 ——
            不能另写一条 `field\\.[\\w.]+` 正则去猜, 那会把 any() 里的成员
            属性名 (如 field.X.Y.area_type 的 area_type) 误当成字段。
    """
    sink: list[str] = refs if refs is not None else []

    def _note(path: str) -> str:
        if path not in sink:
            sink.append(path)
        return path

    if not expr or str(expr).strip().lower() == "always":
        return "True"
    s = re.sub(r"\s+", " ", str(expr)).strip()

    s = re.sub(r"any\((field\.[\w.]+?)\.(\w+)\s+in\s+\[([^\]]*)\]\)",
               lambda m: f"_any_in({_note(m.group(1))!r}, {m.group(2)!r}, [{m.group(3)}])", s)
    s = re.sub(r"count\(distinct\((field\.[\w.]+?)\.(\w+)\)\)",
               lambda m: f"_count_distinct({_note(m.group(1))!r}, {m.group(2)!r})", s)
    s = re.sub(r"count\((field\.[\w.]+)\)",
               lambda m: f"_count({_note(m.group(1))!r})", s)
    s = re.sub(r"has_any\((field\.[\w.]+)\)",
               lambda m: f"_has_any({_note(m.group(1))!r})", s)
    s = re.sub(r"(?<!')(field\.[\w.]+?)\.value\b",
               lambda m: f"_value({_note(m.group(1))!r})", s)
    s = re.sub(r"(?<!')field\.[\w.]+",
               lambda m: f"_field({_note(m.group(0))!r})", s)

    s = re.sub(r"\bAND\b", " and ", s)
    s = re.sub(r"\bOR\b", " or ", s)
    s = re.sub(r"\bNOT\b", " not ", s)
    s = re.sub(r"(?<!')\btrue\b", "True", s)
    s = re.sub(r"(?<!')\bfalse\b", "False", s)
    # 收尾必须 strip: 逻辑词替换会留下前导空格, ast.parse 会当成缩进直接报
    # IndentationError, 把一条本来合法的 NOT 表达式误判成 DSL 错误。
    return re.sub(r"\s+", " ", s).strip()


# ------------------------------------------------------------
# 转换结果的闭集校验
# ------------------------------------------------------------
# DSL 语法集是固定的。转换后的表达式只应含下列节点。任何超出闭集的写法 ——
# 位运算、下标、lambda、属性访问 —— 说明 DSL 里写了引擎并不真正支持的东西。
# 此时必须报 ERROR, 不能让 Python 语义"碰巧"求出一个值。
# 典型反例: `field.x.value >> 0` 在 Python 里是右移, 会悄悄算出真值。
_ALLOWED_NODES: tuple[type, ...] = (
    ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
    ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn,
    ast.Call, ast.Name, ast.Load, ast.Constant, ast.List, ast.Tuple,
)
_ALLOWED_CALL_NAMES = frozenset(_READER_METHODS)


def validate_transformed_expr(py_expr: str) -> None:
    """校验转换结果只使用闭集内的语法。违反则抛 SyntaxError。"""
    tree = ast.parse(py_expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise SyntaxError(
                f"表达式含 DSL 不支持的语法节点 {type(node).__name__}; "
                f"引擎拒绝求值以免产生看似成立的结果")
        if isinstance(node, ast.Call):
            fn = node.func
            if not isinstance(fn, ast.Name) or fn.id not in _ALLOWED_CALL_NAMES:
                raise SyntaxError("表达式含未授权的调用")
            for a in node.args:
                if not isinstance(a, (ast.Constant, ast.List, ast.Tuple)):
                    raise SyntaxError("取值函数只接受字面量参数")


def extract_field_refs(expr: str) -> list[str]:
    """列出一条 DSL 表达式依赖的 field id (与实际求值路径一致)。"""
    refs: list[str] = []
    transform_dsl(expr, refs)
    return refs


# ------------------------------------------------------------
# 三值解释器 (04 文档第 4 节)
# ------------------------------------------------------------

_CMP_OPS = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}


def _eval3(node: ast.AST, reader: "_Reader") -> Any:
    """在 AST 上做三值求值。返回 True / False / UNKNOWN / 字面量。"""
    if isinstance(node, ast.Expression):
        return _eval3(node.body, reader)

    if isinstance(node, ast.BoolOp):
        vals = [_eval3(v, reader) for v in node.values]
        if isinstance(node.op, ast.And):
            if any(v is False for v in vals):
                return False                      # FALSE AND UNKNOWN = FALSE
            if any(_u(v) for v in vals):
                return UNKNOWN                    # TRUE AND UNKNOWN = UNKNOWN
            return all(bool(v) for v in vals)
        if any(v is True for v in vals):
            return True                           # TRUE OR UNKNOWN = TRUE
        if any(_u(v) for v in vals):
            return UNKNOWN                        # FALSE OR UNKNOWN = UNKNOWN
        return any(bool(v) for v in vals)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        v = _eval3(node.operand, reader)
        return UNKNOWN if _u(v) else (not v)      # NOT UNKNOWN = UNKNOWN

    if isinstance(node, ast.Compare):
        left = _eval3(node.left, reader)
        result: Any = True
        for op, comp in zip(node.ops, node.comparators):
            right = _eval3(comp, reader)
            if _u(left) or _u(right):
                return UNKNOWN
            fn = _CMP_OPS.get(type(op))
            if fn is None:
                raise ConditionGrammarError(f"不支持的比较运算 {type(op).__name__}")
            try:
                step = fn(left, right)
            except TypeError as e:
                # 比较两边类型对不上是**输入**问题: 本分支未知, 交给上层三值组合,
                # 不掀掉整条表达式 (否则 `A OR B` 里已确定为 True 的 A 会被丢掉)。
                reader.note_branch_error(f"比较类型不匹配: {e}")
                return UNKNOWN
            if not step:
                return False
            left = right
        return bool(result)

    if isinstance(node, ast.Call):
        method = _READER_METHODS[node.func.id]          # type: ignore[union-attr]
        args = [_literal(a) for a in node.args]
        try:
            return getattr(reader, method)(*args)
        except ConditionInputError as e:
            # 同上: 取值层的输入错误只让本分支未知。
            reader.note_branch_error(str(e))
            return UNKNOWN

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, (ast.List, ast.Tuple)):
        return [_literal(e) for e in node.elts]

    raise ConditionGrammarError(f"解释器遇到未预期节点 {type(node).__name__}")


def _literal(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_literal(e) for e in node.elts]
    raise ConditionGrammarError(f"参数必须是字面量, 收到 {type(node).__name__}")


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
        # always 不依赖任何输入: 无关字段缺失不得把它一起冲掉
        return ObligationResult(ob_id, True, mode, "True (always)",
                                evaluation_status=EvaluationStatus.ALWAYS)

    if mode == "driven_by_obligation":
        return ObligationResult(ob_id, None, mode, "pending driven_by",
                                evaluation_status=EvaluationStatus.UNKNOWN_DEPENDENCY)

    if not when:
        return ObligationResult(ob_id, False, mode, "no when clause",
                                evaluation_status=EvaluationStatus.NO_CONDITION)

    refs: list[str] = []
    try:
        py_expr = transform_dsl(str(when), refs)
        validate_transformed_expr(py_expr)
        tree = ast.parse(py_expr, mode="eval")
    except Exception as e:
        return ObligationResult(
            ob_id, None, mode, f"DSL error: {e}",
            evaluation_status=EvaluationStatus.ERROR_DSL,
            diagnostic_code="CONDITION_ERROR",
            diagnostic_message=f"trigger.when 无法转换: {e}",
            field_refs=refs,
        )

    reader = _Reader(unified)
    try:
        result = _eval3(tree, reader)
    except ConditionGrammarError as e:
        return ObligationResult(
            ob_id, None, mode, py_expr,
            evaluation_status=EvaluationStatus.ERROR_EVAL,
            diagnostic_code="CONDITION_ERROR",
            diagnostic_message=f"表达式无法解释: {e}",
            field_refs=refs,
        )
    except Exception as e:
        return ObligationResult(
            ob_id, None, mode, py_expr,
            evaluation_status=EvaluationStatus.ERROR_EVAL,
            diagnostic_code="CONDITION_ERROR",
            diagnostic_message=f"求值异常: {e}",
            field_refs=refs,
        )

    detail = _reader_detail(reader)

    if _u(result):
        status = (EvaluationStatus.UNKNOWN_INVALID_INPUT
                  if (reader.invalid or reader.branch_errors)
                  else EvaluationStatus.UNKNOWN_MISSING_INPUT)
        return ObligationResult(
            ob_id, None, mode, py_expr,
            evaluation_status=status,
            missing_field_refs=reader.missing + reader.invalid,
            diagnostic_code="CONDITION_UNKNOWN",
            diagnostic_message=(
                "; ".join(detail) + "; 三值求值后结果仍不可确定, 不作不涉及处理"),
            field_refs=refs,
        )

    # 结果可确定时, 读值过程中登记的 missing/invalid 仍可能非空 ——
    # 例如 `A OR B`, A 已为 True, B 缺失或非法但不影响结论。这些问题照实记下来
    # (`triggered` 不变, 但诊断必须保留), 供质量层提示资料缺口。
    return ObligationResult(
        ob_id, bool(result), mode, py_expr,
        evaluation_status=EvaluationStatus.EVALUATED,
        missing_field_refs=reader.missing + reader.invalid,
        diagnostic_code="CONDITION_UNKNOWN" if detail else "",
        diagnostic_message=(
            "; ".join(detail) + "; 结果不受这些问题影响, 但输入仍需修正"
            if detail else ""),
        field_refs=refs)


def _reader_detail(reader: "_Reader") -> list[str]:
    """把读值过程中攒下的问题整理成可读诊断。"""
    detail: list[str] = []
    if reader.missing:
        detail.append(f"缺失依赖 {'、'.join(reader.missing)}")
    if reader.invalid:
        parts = []
        for path in reader.invalid:
            why = reader.reasons.get(path)
            parts.append(f"{path}（{why}）" if why else path)
        detail.append(f"非法依赖 {'、'.join(parts)}")
    if reader.branch_errors:
        detail.append("分支输入错误 " + "; ".join(reader.branch_errors))
    return detail


# ============================================================
# 批量求值 + 级联解析
# ============================================================

@dataclass
class ConditionEngineResult:
    """ConditionEngine 的完整输出"""
    obligation_details: list[ObligationResult]
    triggered: set[str]
    not_triggered: set[str]
    unknown: set[str] = dc_field(default_factory=set)
    """无法确定的义务。**不属于 not_triggered**, 下游不得当作不涉及。"""

    def applicability_map(self) -> dict[str, str]:
        """{ob_id: APPLICABLE / NOT_APPLICABLE / UNKNOWN}, 供质量层消费。"""
        out: dict[str, str] = {}
        for ob_id in self.triggered:
            out[ob_id] = "APPLICABLE"
        for ob_id in self.not_triggered:
            out[ob_id] = "NOT_APPLICABLE"
        for ob_id in self.unknown:
            out[ob_id] = "UNKNOWN"
        return out

    def unknown_details(self) -> list[ObligationResult]:
        return [d for d in self.obligation_details if d.triggered is None]


def evaluate_all(obligations_reg: dict, unified: dict) -> ConditionEngineResult:
    """
    对全部 obligations 求值, 含 driven_by_obligation 级联解析。

    参数:
      obligations_reg: ObligationSet_v0.yaml 的 obligations 节 (dict of ob_id → ob_def)
      unified: facts + derived 合并后的 field lookup

    返回:
      ConditionEngineResult (triggered / not_triggered / unknown 三分)

    级联规则 (04 文档第 4 节):
      任一依赖 True            → True
      全部依赖明确 False       → False
      其余 (含依赖未知/环/悬空) → UNKNOWN
    迭代至不动点, 因此结果与 registry 中义务的书写顺序无关 (验收 U05)。
    """
    obligation_details: list[ObligationResult] = []
    triggered: set[str] = set()
    not_triggered: set[str] = set()
    unknown: set[str] = set()

    # Pass 1: 直接求值
    pending: list[ObligationResult] = []
    for ob_id, ob_def in obligations_reg.items():
        if not isinstance(ob_def, dict):
            continue
        result = evaluate_obligation(ob_id, ob_def, unified)
        obligation_details.append(result)
        if result.mode == "driven_by_obligation":
            pending.append(result)
            continue
        if result.triggered is True:
            triggered.add(ob_id)
        elif result.triggered is False:
            not_triggered.add(ob_id)
        else:
            unknown.add(ob_id)

    # Pass 2: driven_by_obligation 级联, 迭代至不动点
    for _ in range(len(pending) + 1):
        changed = False
        for res in pending:
            if res.triggered is not None:
                continue
            ob_def = obligations_reg.get(res.obligation_id) or {}
            driven = (ob_def.get("trigger") or {}).get("driven_by_refs") or []

            dangling = [d for d in driven if d not in obligations_reg]
            if dangling:
                res.evaluation_status = EvaluationStatus.UNKNOWN_DANGLING_REF
                res.diagnostic_code = "CONDITION_ERROR"
                res.diagnostic_message = (
                    f"driven_by_refs 指向未登记义务: {'、'.join(dangling)}")
                continue

            if any(d in triggered for d in driven):
                res.triggered = True
                res.evaluation_status = EvaluationStatus.EVALUATED
                res.diagnostic_code = ""
                res.diagnostic_message = ""
                triggered.add(res.obligation_id)
                changed = True
            elif driven and all(d in not_triggered for d in driven):
                res.triggered = False
                res.evaluation_status = EvaluationStatus.EVALUATED
                res.diagnostic_code = ""
                res.diagnostic_message = ""
                not_triggered.add(res.obligation_id)
                changed = True
            # 依赖里还有 pending / unknown → 本轮不定, 等下一轮
        if not changed:
            break

    # Pass 3: 收敛后仍未定的 → UNKNOWN (依赖未知 / 环 / 无 driven_by_refs)
    # 环和"上游未知"都会停在这里, 但它们的修法完全不同:
    #   上游未知 → 补资料; 环 → 改 registry。诊断必须分开。
    def _in_cycle(start: str, unresolved: set[str]) -> bool:
        stack = [(start, {start})]
        while stack:
            node, path = stack.pop()
            deps = ((obligations_reg.get(node) or {}).get("trigger") or {}).get(
                "driven_by_refs") or []
            for dep in deps:
                if dep == start:
                    return True
                if dep in unresolved and dep not in path:
                    stack.append((dep, path | {dep}))
        return False

    # 先把全部未定项并入 unknown, 再逐条判原因 —— 否则诊断消息会依赖遍历顺序。
    unresolved = {r.obligation_id for r in pending if r.triggered is None}
    unknown |= unresolved
    for res in pending:
        if res.triggered is not None:
            continue
        ob_def = obligations_reg.get(res.obligation_id) or {}
        driven = (ob_def.get("trigger") or {}).get("driven_by_refs") or []
        if res.evaluation_status is EvaluationStatus.UNKNOWN_DANGLING_REF:
            pass
        elif not driven:
            res.evaluation_status = EvaluationStatus.UNKNOWN_DEPENDENCY
            res.diagnostic_code = "CONDITION_ERROR"
            res.diagnostic_message = "mode=driven_by_obligation 但未声明 driven_by_refs"
        elif _in_cycle(res.obligation_id, unresolved):
            res.evaluation_status = EvaluationStatus.UNKNOWN_CYCLE
            res.diagnostic_code = "CONDITION_ERROR"
            res.diagnostic_message = (
                f"driven_by_refs 构成环, 级联无法收敛: "
                f"{'、'.join(driven)}")
        else:
            res.evaluation_status = EvaluationStatus.UNKNOWN_DEPENDENCY
            res.diagnostic_code = "CONDITION_UNKNOWN"
            res.diagnostic_message = (
                f"上游义务未知: "
                f"{'、'.join(d for d in driven if d in unknown) or '、'.join(driven)}")

    return ConditionEngineResult(
        obligation_details=obligation_details,
        triggered=triggered,
        not_triggered=not_triggered,
        unknown=unknown,
    )
