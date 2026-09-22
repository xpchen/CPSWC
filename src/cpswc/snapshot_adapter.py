"""
snapshot_adapter.py — CPSWC P0-04 统一读取上下文

任务来源: docs/report_production_plan/03_P0_TASKS.md P0-04
接口依据: 04_CONTRACTS_AND_ACCEPTANCE.md 第 3 节
批准记录: implementation/DECISION_LOG.md 条目 008 (B 批)

本模块解决 A 批验收暴露的问题 (DECISION_LOG 条目 007): **系统里有三套 derived 读法。**

    runtime.run_project 评估义务用   facts + pre-stored derived + 计算 derived
    RuntimeSnapshot.derived_fields   只含计算 derived
    正文 / 表格                      读 derived_fields
    export_gate                      自己再合并一次 _pre_stored_derived

实测后果: 惠州样本 9 个 pre-stored derived 里有 8 个 (含全部六率) 对正文和表格
不可见 —— 六项指标表长期显示"—", 看起来像保守处理, 其实是根本没读到。

BuildContext 是**一次构建期间的唯一只读视图**。它:

  - 保存 facts / pre-stored derived / 计算 derived 三层原样, 不篡改任何一层
  - 按固定的来源优先级选出**一个**读值, 并记下选了哪一层、为什么
  - 冲突、失效、未核验、演示假设全部产出诊断, 不静默择一
  - **不提供任何写回接口** —— 它不是第四套事实真源

边界 (硬约束):
  - 本模块不重写任何业务公式, 不做单位换算之外的计算。
  - 别名**不自动合并**。两侧都有值 → INPUT_CONFLICT; 单侧有值 → 标未核验别名。
    语义确认前不得登记为同义 (DECISION_LOG 条目 003, 项目负责人已拍板)。
  - 演示模数、默认时段、估算红线一律产出 DEMO_ASSUMPTION, 不因为带了
    source_note 字符串就当已核验。
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field as dc_field
from typing import Any, Iterable

from cpswc.report_quality import (
    Provenance, QualityFinding, ResolvedValue, Severity, Stage, ValueKind,
    ValueState, resolve_value,
)

SCHEMA_VERSION = "build_context_v0b"


# ============================================================
# 1. FIR 驱动的类型与单位
# ============================================================
# A 批的 KNOWN_UNITS 是手工维护的白名单。这里改为以 FIR 的 semantic_type /
# unit_enum / unit 为准 —— registry 才是登记处, 代码不另立一套。

_SCALAR_KINDS: dict[str, ValueKind] = {
    "string": ValueKind.TEXT,
    "text": ValueKind.TEXT,
    "enum": ValueKind.TEXT,
    "year": ValueKind.TEXT,
    "year_month": ValueKind.TEXT,
    "geo_ref": ValueKind.TEXT,
    "number": ValueKind.NUMBER,
    "percent": ValueKind.NUMBER,
    "bool": ValueKind.BOOL,
}


def _kind_for(semantic_type: str | None, semantic_types: dict) -> ValueKind:
    """把 FIR 的 semantic_type 映射成读值期望的 ValueKind。"""
    if not semantic_type:
        return ValueKind.ANY
    if semantic_type in _SCALAR_KINDS:
        return _SCALAR_KINDS[semantic_type]
    if semantic_type.startswith("list_of") or semantic_type.endswith("List"):
        return ValueKind.LIST
    if semantic_type.endswith("Dict") or semantic_type == "record":
        return ValueKind.ANY
    # Quantity 及其 extends 链 (Area / Volume / Mass / Currency / ErosionModulus)
    base = semantic_type
    seen = set()
    while base and base not in seen:
        seen.add(base)
        if base == "Quantity":
            return ValueKind.QUANTITY
        base = (semantic_types.get(base) or {}).get("extends")
    return ValueKind.ANY


def _allowed_units(field_def: dict, semantic_types: dict) -> set[str]:
    """该字段允许的单位集合。空集表示 FIR 未约束。"""
    units: set[str] = set()
    declared = field_def.get("unit")
    if isinstance(declared, str) and declared.strip():
        units.add(declared)
    st = field_def.get("semantic_type")
    seen = set()
    while st and st not in seen:
        seen.add(st)
        st_def = semantic_types.get(st) or {}
        for u in (st_def.get("unit_enum") or []):
            units.add(u)
        if st_def.get("unit"):
            units.add(st_def["unit"])
        st = st_def.get("extends")
    return units


# ============================================================
# 2. 别名候选 (**候选, 不是已登记的同义词**)
# ============================================================
# DECISION_LOG 条目 003: 项目负责人已决定"不按同义合并, 先报 CONFLICT"。
# 因此这里登记的是"**疑似指同一件事、但语义未经工程师确认**"的字段对。
#
# 处理规则:
#   两侧都有值且不相等 → INPUT_CONFLICT (BLOCK), 不择一
#   两侧都有值且相等   → INPUT_CONFLICT (WARN), 相等只是巧合, 语义仍未确认
#   仅单侧有值         → 照常读该侧, 但标 SOURCE_UNVERIFIED (WARN) 提示别名未确认
#
# **不得**因为"跑起来方便"把任何一对提升为自动合并。提升需要工程师确认语义、
# 单位与包含关系, 并走 DECISION_LOG 留痕。
ALIAS_CANDIDATES: tuple[tuple[str, str, str], ...] = (
    ("field.fact.topsoil.stripable_volume",
     "field.fact.topsoil.strippable_volume",
     "是否同指可剥离量, 还是一个指可剥离、一个指已剥离"),
    ("field.fact.topsoil.fill",
     "field.fact.topsoil.backfill_volume",
     "回覆计划量与回覆实际量口径未确认"),
    ("field.fact.prediction.total_loss",
     "field.fact.prediction.predicted_total_loss",
     "预测方法、时段与是否含现状流失未确认"),
    ("field.fact.project.compiler",
     "field.fact.project.compile_unit",
     "是否仅同义名称 (人 vs 单位)"),
    ("field.fact.project.builder",
     "field.fact.project.construction_unit",
     "是否仅同义名称 (建设单位 vs 施工单位)"),
)


# ============================================================
# 3. 演示假设识别
# ============================================================
# 04 文档 I05: 默认模数 / 默认时段 / 近似红线必须产出 DEMO_ASSUMPTION,
# 不能因为带了 source_note 字符串就当已核验。
_DEMO_MARKERS: tuple[str, ...] = (
    "典型值", "典型模数", "经验值", "默认", "估算", "示意", "假设",
    "demo", "DEMO", "placeholder", "待实测", "暂按",
)


def _demo_note(raw: Any) -> str | None:
    """检查一个值的附注里有没有演示假设标记。返回命中的标记。"""
    if not isinstance(raw, dict):
        return None
    for key in ("source_note", "_note", "note", "derivation", "source"):
        text = raw.get(key)
        if isinstance(text, str):
            for marker in _DEMO_MARKERS:
                if marker in text:
                    return f"{key}={text[:60]}"
    return None


# ============================================================
# 4. BuildContext
# ============================================================

@dataclass
class LayerHit:
    """某一层里读到的原始值。"""
    layer: Provenance
    raw: Any


class BuildContext:
    """
    一次构建期间的只读事实视图。

    所有投影 (正文 / 表格 / 工作台 / diff / 导出) 都应经此读取, 以保证
    "同事实同读值同来源" (验收 I01)。

    来源优先级 (04 文档第 3 节):
      1. 本次**成功**计算的派生量 —— 权威
      2. 本次计算**失败**时, 旧 pre-stored 值不得顶上; 隔离为 stale 历史展示
      3. 没有本次计算但有外部结果 → 明确标 PRE_STORED_DERIVED, 不伪装成重算
      4. 运行时 enrich 出来的消费视图 → 标 ENRICHED_VIEW
      5. 项目填报事实
    """

    def __init__(self, project_input: dict | None = None,
                 runtime_snapshot: Any = None,
                 registries: dict | None = None,
                 *, enriched_views: dict | None = None) -> None:
        pi = project_input or {}
        # 全部深拷贝: BuildContext 绝不持有调用者可变对象的引用, 也就不可能写回
        self.facts: dict = copy.deepcopy(pi.get("facts") or {})
        self.pre_stored_derived: dict = copy.deepcopy(pi.get("derived") or {})
        self.enriched_views: dict = copy.deepcopy(enriched_views or {})

        snap = runtime_snapshot
        self.computed_derived: dict = copy.deepcopy(
            _attr(snap, "derived_fields", {}) or {})
        self.failed_calc_fields: dict[str, str] = {}
        for cr in (_attr(snap, "calculator_results", []) or []):
            status = _attr(cr, "status", None) or (
                cr.get("status") if isinstance(cr, dict) else None)
            if status == "ok":
                continue
            out = _attr(cr, "output_field_id", "") or (
                cr.get("output_field_id") if isinstance(cr, dict) else "")
            calc_id = _attr(cr, "calculator_id", "") or (
                cr.get("calculator_id") if isinstance(cr, dict) else "")
            msg = _attr(cr, "error_message", "") or (
                cr.get("error_message") if isinstance(cr, dict) else "")
            # 计算失败时 output_field_id 常为空, 退而用 calculator_id 记录
            self.failed_calc_fields[out or f"<{calc_id}>"] = (
                f"{calc_id}: {msg or '计算失败'}")

        regs = registries or {}
        fir = regs.get("fields") or {}
        self.fir_fields: dict = fir.get("fields") or {}
        self.semantic_types: dict = fir.get("semantic_types") or {}

        self.findings: list[QualityFinding] = []
        self._cache: dict[str, ResolvedValue] = {}
        self._alias_checked = False

    # ---------- 分层读取 ----------

    def _layers(self, field_id: str) -> list[LayerHit]:
        """按优先级列出各层里存在的原始值。"""
        hits: list[LayerHit] = []
        if field_id in self.computed_derived:
            hits.append(LayerHit(Provenance.CALCULATED,
                                 self.computed_derived[field_id]))
        if field_id in self.enriched_views:
            hits.append(LayerHit(Provenance.ENRICHED_VIEW,
                                 self.enriched_views[field_id]))
        if field_id in self.pre_stored_derived:
            hits.append(LayerHit(Provenance.PRE_STORED_DERIVED,
                                 self.pre_stored_derived[field_id]))
        if field_id in self.facts:
            hits.append(LayerHit(Provenance.PROJECT_FACT, self.facts[field_id]))
        return hits

    def kind_of(self, field_id: str) -> ValueKind:
        fdef = self.fir_fields.get(field_id)
        if not isinstance(fdef, dict):
            return ValueKind.ANY
        return _kind_for(fdef.get("semantic_type"), self.semantic_types)

    # ---------- 核心 resolve ----------

    def resolve(self, field_id: str,
                kind: ValueKind | None = None) -> ResolvedValue:
        """读一个字段, 返回带来源与状态的 ResolvedValue。结果缓存, 多次调用一致。"""
        if field_id in self._cache:
            return self._cache[field_id]

        expected = kind or self.kind_of(field_id)
        hits = self._layers(field_id)

        # --- 当前计算失败: 旧值不得顶上 (04 文档第 3 节第 2 条) ---
        if field_id in self.failed_calc_fields:
            stale = next((h.raw for h in hits
                          if h.layer is Provenance.PRE_STORED_DERIVED), None)
            rv = ResolvedValue(
                field_id, ValueState.MISSING, raw=None,
                provenance=Provenance.STALE_HISTORICAL,
                stale_value=stale,
                note=f"本次计算失败 ({self.failed_calc_fields[field_id]})")
            self._note(QualityFinding(
                code="DERIVED_STALE", severity=Severity.BLOCK,
                message=(f"{field_id}: 本次计算失败, "
                         f"{'旧值已隔离为历史展示' if stale is not None else '无可用值'}; "
                         f"{self.failed_calc_fields[field_id]}"),
                target_ref=field_id,
                remediation="修复计算或补齐其输入; 旧值不得作为本次结果使用",
                stage=Stage.EVALUATION))
            return self._cached(field_id, rv)

        if not hits:
            rv = resolve_value(field_id, None, kind=expected, present=False)
            return self._cached(field_id, rv)

        # --- 多层都有值: 比较是否一致 ---
        #
        # 04 文档第 3 节给了明确的优先级: 本次成功计算的派生量是权威读值。
        # 所以"计算结果 vs 旧预存值不一致"是**有解**的 —— 选计算结果, 留诊断
        # (验收 I06: "各入口同选当前结果, 并保留来源诊断")。
        # 只有当没有权威层、几个非权威层互相打架时, 才是真的无从择一 → CONFLICT。
        chosen = hits[0]
        if len(hits) > 1:
            distinct = {_comparable(h.raw) for h in hits}
            if len(distinct) > 1:
                others = "、".join(
                    f"{h.layer.value}={_comparable(h.raw)!r}" for h in hits[1:])
                # 有明确优先级规则的层 = 有解, 选它并留诊断;
                # ENRICHED_VIEW 是同一条 fact 的派生消费视图, 天然高于原始值
                # (它已另有 SOURCE_UNVERIFIED 提示来源), 不是"无从择一"。
                if chosen.layer in (Provenance.CALCULATED, Provenance.ENRICHED_VIEW):
                    self._note(QualityFinding(
                        code="INPUT_CONFLICT", severity=Severity.WARN,
                        message=(
                            f"{field_id}: {chosen.layer.value} 层取值与其他来源不一致 "
                            f"({others}); 按来源优先级以 {chosen.layer.value} 为准"),
                        target_ref=field_id,
                        remediation="核对其他来源是否已过期; 需要保留时应说明其语义与时点",
                        stage=Stage.INPUT))
                else:
                    rv = ResolvedValue(
                        field_id, ValueState.CONFLICT, raw=chosen.raw,
                        provenance=chosen.layer,
                        conflicts=[(h.layer.value, h.raw) for h in hits],
                        note="多个非权威来源层的取值不一致, 无规则可择一")
                    f = rv.to_finding(severity=Severity.BLOCK, stage=Stage.INPUT)
                    if f is not None:
                        self._note(f)
                    return self._cached(field_id, rv)

        rv = resolve_value(field_id, chosen.raw, kind=expected, present=True)
        rv.provenance = chosen.layer

        # 04 文档第 3 节: "数字必须带明确单位**或来自有单位的登记契约**"。
        # 计算器把值与单位分开返回 (CalcResultSummary.unit), derived_fields 里只
        # 存裸数字。这类值不是"无单位", 而是单位由 FIR 登记 —— 不能判非法。
        if rv.state is ValueState.INVALID and expected is ValueKind.QUANTITY \
                and isinstance(chosen.raw, (int, float)) \
                and not isinstance(chosen.raw, bool):
            declared = (self.fir_fields.get(field_id) or {}).get("unit")
            if isinstance(declared, str) and declared.strip():
                rv = ResolvedValue(
                    field_id, ValueState.PRESENT, value=chosen.raw,
                    unit=declared, raw=chosen.raw, provenance=chosen.layer,
                    note=f"单位取自 FIR 登记契约 ({declared}), 数据本身未带单位")

        # --- 单位是否在 FIR 登记范围内 ---
        if rv.state is ValueState.PRESENT and rv.unit:
            fdef = self.fir_fields.get(field_id)
            if isinstance(fdef, dict):
                allowed = _allowed_units(fdef, self.semantic_types)
                if allowed and rv.unit not in allowed:
                    rv = ResolvedValue(
                        field_id, ValueState.INVALID, unit=rv.unit, raw=chosen.raw,
                        provenance=chosen.layer,
                        note=f"单位 {rv.unit!r} 不在 FIR 登记范围 {sorted(allowed)}")
                    self._note(QualityFinding(
                        code="VALUE_INVALID", severity=Severity.BLOCK,
                        message=f"{field_id}: {rv.note}", target_ref=field_id,
                        remediation="改用登记单位, 或在 FIR 中补登记该单位",
                        stage=Stage.INPUT))
                    return self._cached(field_id, rv)

        # --- 外部结果不伪装成本次重算 ---
        if rv.state is ValueState.PRESENT \
                and chosen.layer is Provenance.PRE_STORED_DERIVED:
            self._note(QualityFinding(
                code="SOURCE_UNVERIFIED", severity=Severity.WARN,
                message=(f"{field_id}: 取自输入中预存的派生量 (外部结果), "
                         f"不是本次计算所得; 其方法、输入绑定与复核状态未知"),
                target_ref=field_id,
                remediation="补充该结果的计算依据与证据记录, 或改由计算器产出",
                stage=Stage.INPUT))

        if rv.state is ValueState.PRESENT \
                and chosen.layer is Provenance.ENRICHED_VIEW:
            self._note(QualityFinding(
                code="SOURCE_UNVERIFIED", severity=Severity.WARN,
                message=(f"{field_id}: 取自运行时 enrich 的消费视图, "
                         f"非项目填报原值; 价格来源与时点需单独核验"),
                target_ref=field_id,
                remediation="核验 enrich 所用定额库版本与价格时点",
                stage=Stage.INPUT))

        # --- 演示假设 ---
        demo = _demo_note(chosen.raw)
        if demo and rv.state is ValueState.PRESENT:
            self._note(QualityFinding(
                code="DEMO_ASSUMPTION", severity=Severity.BLOCK,
                message=f"{field_id}: 取值带演示/默认假设标记 ({demo})",
                target_ref=field_id,
                remediation="用项目实测或专项计算结果替换该假设值",
                stage=Stage.INPUT))

        return self._cached(field_id, rv)

    # ---------- 别名冲突 ----------

    def check_alias_candidates(self) -> list[QualityFinding]:
        """
        检查别名候选对。**不合并**, 只产出诊断 (DECISION_LOG 条目 003)。

        幂等: 重复调用不会重复登记诊断。
        """
        if self._alias_checked:
            return [f for f in self.findings if f.code in
                    ("INPUT_CONFLICT", "SOURCE_UNVERIFIED")
                    and "别名" in f.message]
        self._alias_checked = True
        out: list[QualityFinding] = []
        for a, b, why in ALIAS_CANDIDATES:
            ra, rb = self.resolve(a), self.resolve(b)
            if ra.is_present and rb.is_present:
                same = _comparable(ra.raw) == _comparable(rb.raw)
                f = QualityFinding(
                    code="INPUT_CONFLICT",
                    severity=Severity.WARN if same else Severity.BLOCK,
                    message=(f"别名候选 {a} 与 {b} 同时有值"
                             f"{'（数值相同，但相同不等于同义）' if same else '且不相等'}; "
                             f"待确认: {why}"),
                    target_ref=a,
                    remediation="由水保工程师确认两者语义、单位与包含关系后再登记",
                    stage=Stage.INPUT)
                out.append(f)
                self._note(f)
            elif ra.is_present != rb.is_present:
                present_id = a if ra.is_present else b
                absent_id = b if ra.is_present else a
                f = QualityFinding(
                    code="SOURCE_UNVERIFIED", severity=Severity.WARN,
                    message=(f"别名候选中仅 {present_id} 有值, {absent_id} 缺失; "
                             f"两者是否同义**未经确认**, 不做自动映射; 待确认: {why}"),
                    target_ref=present_id,
                    remediation="确认语义后再决定是否登记为同一字段",
                    stage=Stage.INPUT)
                out.append(f)
                self._note(f)
        return out

    # ---------- 统一视图 ----------

    def unified_view(self) -> dict:
        """
        产出**一份**选定读值的 flat dict, 供尚未迁移到 BuildContext 的消费者使用。

        这是消除"三套 derived 读法"的关键: 正文、表格、工作台、导出门禁
        拿到的都是这一份。计算失败的字段**不出现在视图里** (旧值不顶上)。
        """
        view: dict = {}
        for layer in (self.facts, self.pre_stored_derived,
                      self.enriched_views, self.computed_derived):
            for field_id in layer:
                if field_id in view:
                    continue
                rv = self.resolve(field_id)
                if rv.state is ValueState.MISSING:
                    continue        # 含计算失败被隔离的字段
                view[field_id] = rv.raw
        return view

    def derived_view(self) -> dict:
        """统一视图里属于 `field.derived.*` 的部分 (供 snapshot 的 derived_fields)。"""
        return {k: v for k, v in self.unified_view().items()
                if k.startswith("field.derived.")}

    # ---------- 唯一的字段状态序列化出口 (F-0.1) ----------

    def project_fields(self, include_registry_fields: bool = True) -> list[dict]:
        """
        **前端与 payload 生成器读字段状态的唯一出口。**

        为什么需要它: `unified_view()` 为了"旧值不顶上"而显式跳过 MISSING,
        `source_map()` 只给来源层字符串 —— 两者都拿不到完整的 ResolvedValue。
        没有这个出口, payload 生成器就得自己重新推断值状态, 等于把刚消灭的
        多套口径复制一份到生成器里。**调用方不得重新解析值状态。**

        字段全集 = FIR 登记字段 ∪ 本次实际消费字段。
        **缺失字段必须出现在结果里** —— 否则"缺什么"在界面上根本看不见。

        每项:
          field_id / state / value(仅 PRESENT) / unit / provenance
          / stale_value / conflicts / note / canonical_name / is_derived
        """
        ids: list[str] = []
        seen: set[str] = set()
        for field_id in self._all_field_ids():          # 本次实际消费的
            if field_id not in seen:
                seen.add(field_id)
                ids.append(field_id)
        if include_registry_fields:
            for field_id, fdef in self.fir_fields.items():   # FIR 登记的
                if not isinstance(fdef, dict) or fdef.get("placeholder") is True:
                    continue
                if field_id not in seen:
                    seen.add(field_id)
                    ids.append(field_id)

        out: list[dict] = []
        for field_id in sorted(ids):
            rv = self.resolve(field_id)
            fdef = self.fir_fields.get(field_id) or {}
            out.append({
                "field_id": field_id,
                "canonical_name": fdef.get("canonical_name") or "",
                "is_derived": field_id.startswith("field.derived."),
                "state": rv.state.value,
                # value 只在 PRESENT 时有意义; 其余一律 None, 不让调用方误用
                "value": rv.value if rv.state is ValueState.PRESENT else None,
                "unit": rv.unit or "",
                "provenance": rv.provenance.value,
                "stale_value": rv.stale_value,
                "conflicts": [[layer, val] for layer, val in rv.conflicts],
                "note": rv.note or "",
                "is_empty_container": rv.is_empty_container,
            })
        return out

    def source_map(self) -> dict[str, str]:
        """{field_id: 来源层}, 供工作台与交付记录展示"选了哪一层"。"""
        out: dict[str, str] = {}
        for field_id in self._all_field_ids():
            rv = self.resolve(field_id)
            out[field_id] = rv.provenance.value
        return out

    def _all_field_ids(self) -> list[str]:
        seen: list[str] = []
        for layer in (self.facts, self.pre_stored_derived,
                      self.enriched_views, self.computed_derived):
            for k in layer:
                if k not in seen:
                    seen.append(k)
        return seen

    # ---------- 内部 ----------

    def _note(self, finding: QualityFinding) -> None:
        key = (finding.code, finding.target_ref, finding.message)
        if key not in {(f.code, f.target_ref, f.message) for f in self.findings}:
            self.findings.append(finding)

    def _cached(self, field_id: str, rv: ResolvedValue) -> ResolvedValue:
        self._cache[field_id] = rv
        return rv


# ============================================================
# 5. 构造入口
# ============================================================

def make_build_context(project_input: dict | None = None,
                       runtime_snapshot: Any = None,
                       registries: dict | None = None,
                       *, enriched_views: dict | None = None) -> BuildContext:
    """04 文档第 3 节约定的构造入口。"""
    ctx = BuildContext(project_input, runtime_snapshot, registries,
                       enriched_views=enriched_views)
    ctx.check_alias_candidates()
    return ctx


def resolve_value_in(context: BuildContext, field_id: str) -> ResolvedValue:
    """04 文档第 3 节约定的读值入口 (`resolve_value(context, field_id)`)。"""
    return context.resolve(field_id)


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


# 注解/审计类键。它们描述"这个值怎么来的", 不是值本身。
# 比较多来源是否一致时必须剔除, 否则会把"同一组数字 + 一段审计说明"误报成冲突 ——
# 惠州样本的 weighted_comprehensive_target 就是这种情况: 六个业务值与计算结果
# 完全相同, 只是 pre-stored 那份额外带了 Step 11B 的纠错审计记录。
_ANNOTATION_KEYS: frozenset[str] = frozenset({
    "derivation", "derivation_note", "note", "source_note", "source",
    "trigger", "corrected_by", "correction_basis", "correction_date",
    "target_by_standard", "unit_note",
})


def _business_payload(raw: dict) -> dict:
    """剥掉注解与审计键, 只留业务值。`_` 开头的键一律视为元数据。"""
    return {k: v for k, v in raw.items()
            if not str(k).startswith("_") and k not in _ANNOTATION_KEYS}


def _comparable(raw: Any) -> Any:
    """把值规范化到可比较形态, 用于判断多来源是否一致。"""
    import json
    if isinstance(raw, dict) and "value" in raw:
        return (raw.get("value"), raw.get("unit") or "")
    if isinstance(raw, dict):
        return json.dumps(_business_payload(raw), ensure_ascii=False,
                          sort_keys=True, default=str)
    if isinstance(raw, (list, tuple)):
        return json.dumps(raw, ensure_ascii=False, sort_keys=True, default=str)
    return raw


__all__ = [
    "SCHEMA_VERSION", "BuildContext", "make_build_context", "resolve_value_in",
    "ALIAS_CANDIDATES",
]
