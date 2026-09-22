"""
intake_issues.py — F-0.3 诊断分层聚合 + 收资清单投影

任务来源: docs/report_production_plan/implementation/FRONTEND_WIRING_PLAN.md v1.1 F-0.3
批准记录: implementation/DECISION_LOG.md 条目 012

解决两件事。

一、**诊断有四个来源, 不能拼成一锅。**

    BuildContext      取值层 (缺失/非法/冲突/演示假设/未核验来源)
    narrative 模板    渲染层 (断言缺支持/条件未知)
    ReportQualitySummary  汇总层 (内容缺口/复核失效)
    ExportGate        门禁层

它们互相重叠 —— 同一个缺失字段会在取值层和渲染层各报一次。直接拼接会把数量
放大, 界面也分不清"输入问题 / 正文问题 / 门禁结果"。这里**分层保留 + 单独给
去重计数**, 不做破坏性合并。

二、**"缺资料清单"不等于按 stage=INPUT 过滤 findings。**

实测有 `VALUE_MISSING` 是在 RENDER 阶段发现的 (模板读值时才发现), 它们同样是
要向甲方收集的资料; 反过来 `DEMO_ASSUMPTION` / `INPUT_CONFLICT` /
`SOURCE_UNVERIFIED` 也不是简单的"缺资料"。因此单独产出 `intake_issues`,
用 `category` 区分五类。

**影响范围由后端按登记关系生成, 不由界面猜。** 依据是 FieldIdentityRegistry
每个字段的 `lineage.projection_target_refs` (sec.* / art.* / proj.*)。
建立不起来时 `impact_known=False`, 界面显示"影响范围尚未建立" —— 不得编造。
"""

from __future__ import annotations

from typing import Any, Iterable

SCHEMA_VERSION = "intake_issues_v1"

# 诊断码 → 收资清单分类。
# 不在表里的码**不进** intake_issues —— 它们不是"要向甲方收的东西"
# (例如 RENDER_FAILED 是我们自己的模板问题, CONTENT_INCOMPLETE 是功能未实现)。
CATEGORY_BY_CODE: dict[str, str] = {
    "VALUE_MISSING": "MISSING",
    "VALUE_INVALID": "INVALID",
    "INPUT_CONFLICT": "CONFLICT",
    "DEMO_ASSUMPTION": "ASSUMPTION",
    "SOURCE_UNVERIFIED": "UNVERIFIED_SOURCE",
}

CATEGORY_LABELS: dict[str, str] = {
    "MISSING": "资料缺失",
    "INVALID": "数据非法",
    "CONFLICT": "来源冲突",
    "ASSUMPTION": "演示/默认假设",
    "UNVERIFIED_SOURCE": "来源未核验",
}


# ============================================================
# 1. 分层聚合
# ============================================================

def _as_dict(f: Any) -> dict:
    if isinstance(f, dict):
        return f
    to_dict = getattr(f, "to_dict", None)
    return to_dict() if callable(to_dict) else {}


def _dedup_key(f: dict) -> tuple:
    return (f.get("code", ""), f.get("target_ref", ""), f.get("message", ""))


def canonical_findings(*,
                       build: Iterable[Any] = (),
                       narrative: Iterable[Any] = (),
                       quality: Iterable[Any] = (),
                       gate: Iterable[Any] = ()) -> dict:
    """
    把四个来源整理成分层结构 + 去重后的严重度计数。

    **分层保留**: 每层原样给出, 界面可以分别显示"输入问题 / 正文问题 /
    汇总缺口 / 门禁结果"。
    **计数去重**: `counts_by_severity` 按 (code, target_ref, message) 去重后统计,
    避免同一个缺失字段被数两遍。
    """
    layers = {
        "build": [_as_dict(f) for f in build],
        "narrative": [_as_dict(f) for f in narrative],
        "quality": [_as_dict(f) for f in quality],
        "gate": [_gate_finding_as_dict(f) for f in gate],
    }

    seen: set[tuple] = set()
    counts = {"BLOCK": 0, "WARN": 0, "INFO": 0}
    for name in ("build", "narrative", "quality", "gate"):
        for f in layers[name]:
            key = _dedup_key(f)
            if key in seen:
                continue
            seen.add(key)
            sev = f.get("severity") or "INFO"
            if sev in counts:
                counts[sev] += 1

    return {
        "schema_version": SCHEMA_VERSION,
        **layers,
        "counts_by_severity": counts,
        "distinct_count": len(seen),
        "raw_count": sum(len(v) for v in layers.values()),
    }


def _gate_finding_as_dict(f: Any) -> dict:
    """ExportGate 的 GateFinding 用的是 rule_id/action, 归一到统一形状。"""
    if isinstance(f, dict):
        d = dict(f)
    else:
        d = {
            "rule_id": getattr(f, "rule_id", ""),
            "action": getattr(f, "action", ""),
            "message": getattr(f, "message", ""),
            "target_ref": getattr(f, "target_ref", ""),
        }
    return {
        "code": d.get("code") or d.get("rule_id", ""),
        "severity": d.get("severity") or d.get("action", "INFO"),
        "message": d.get("message", ""),
        "target_ref": d.get("target_ref", ""),
        "missing_input_refs": d.get("missing_input_refs", []),
        "remediation": d.get("remediation", ""),
        "stage": d.get("stage", "POSTFLIGHT"),
    }


# ============================================================
# 2. 影响范围 (按登记关系, 不猜)
# ============================================================

def _projection_targets(field_id: str, fir_fields: dict) -> list[str]:
    fdef = fir_fields.get(field_id)
    if not isinstance(fdef, dict):
        return []
    return list((fdef.get("lineage") or {}).get("projection_target_refs") or [])


def resolve_impact(field_refs: Iterable[str], fir_fields: dict) -> dict:
    """
    按 FIR 的 `lineage.projection_target_refs` 解析一条问题影响到哪里。

    返回 {section_refs, artifact_refs, projection_refs, impact_known}。
    没有任何登记关系时 `impact_known=False` —— 调用方必须显示
    "影响范围尚未建立", **不得**用"可能影响全部章节"之类的话填充。
    """
    sections: list[str] = []
    artifacts: list[str] = []
    projections: list[str] = []
    for field_id in field_refs:
        for ref in _projection_targets(field_id, fir_fields):
            bucket = (sections if ref.startswith("sec.")
                      else artifacts if ref.startswith("art.")
                      else projections if ref.startswith("proj.")
                      else None)
            if bucket is not None and ref not in bucket:
                bucket.append(ref)
    return {
        "affected_section_refs": sorted(sections),
        "affected_artifact_refs": sorted(artifacts),
        "affected_projection_refs": sorted(projections),
        "impact_known": bool(sections or artifacts or projections),
    }


# ============================================================
# 3. intake_issues 投影
# ============================================================

def _field_refs_of(f: dict) -> list[str]:
    """一条诊断牵涉哪些登记字段。"""
    refs = list(f.get("missing_input_refs") or [])
    target = f.get("target_ref") or ""
    if target.startswith("field.") and target not in refs:
        refs.append(target)
    return refs


def build_intake_issues(findings_by_origin: dict,
                        fir_fields: dict | None = None) -> list[dict]:
    """
    产出"要向甲方收什么 / 哪些数据有问题"的清单。

    参数:
      findings_by_origin: {origin: [finding...]}，origin ∈ build/narrative/quality
      fir_fields: FieldIdentityRegistry 的 fields 节, 用于解析影响范围

    规则:
      - 只收 CATEGORY_BY_CODE 里登记的码。模板渲染失败、功能未实现之类
        **不是**向甲方收资的事, 不进本清单。
      - 同一 (category, 字段集合, message) 只出一条, 跨来源去重 ——
        同一个缺失字段在取值层和渲染层各报一次, 对收资的人是同一件事。
      - 影响范围按登记关系解析; 解析不出就 impact_known=False。
    """
    fir = fir_fields or {}
    out: list[dict] = []
    seen: dict[tuple, dict] = {}

    for origin in ("build", "narrative", "quality"):
        for raw in (findings_by_origin.get(origin) or []):
            f = _as_dict(raw)
            category = CATEGORY_BY_CODE.get(f.get("code", ""))
            if category is None:
                continue
            field_refs = _field_refs_of(f)
            key = (category, tuple(sorted(field_refs)), f.get("message", ""))
            if key in seen:
                # 同一件事被多层报到: 记下它还出现在哪一层, 不新增条目
                if origin not in seen[key]["origins"]:
                    seen[key]["origins"].append(origin)
                continue

            impact = resolve_impact(field_refs, fir)
            issue = {
                "issue_id": f"intake.{len(out) + 1:04d}",
                "category": category,
                "category_label": CATEGORY_LABELS[category],
                "severity": f.get("severity") or "INFO",
                "field_refs": field_refs,
                "field_names": [
                    (fir.get(fid) or {}).get("canonical_name") or fid
                    for fid in field_refs
                ],
                "message": f.get("message", ""),
                "remediation": f.get("remediation", ""),
                "origin": origin,
                "origins": [origin],
                "source_code": f.get("code", ""),
                **impact,
            }
            seen[key] = issue
            out.append(issue)

    # BLOCK 在前, 其次按分类、字段名排序 —— 收资的人先看阻断项
    order = {"BLOCK": 0, "WARN": 1, "INFO": 2}
    out.sort(key=lambda i: (order.get(i["severity"], 3), i["category"],
                            i["field_refs"]))
    for n, issue in enumerate(out, 1):
        issue["issue_id"] = f"intake.{n:04d}"
    return out


def summarize_intake(issues: list[dict]) -> dict:
    """给界面用的分项计数。不给总分, 不做加权。"""
    by_category: dict[str, int] = {}
    by_severity = {"BLOCK": 0, "WARN": 0, "INFO": 0}
    unknown_impact = 0
    for i in issues:
        by_category[i["category"]] = by_category.get(i["category"], 0) + 1
        if i["severity"] in by_severity:
            by_severity[i["severity"]] += 1
        if not i["impact_known"]:
            unknown_impact += 1
    return {
        "total": len(issues),
        "by_category": by_category,
        "by_severity": by_severity,
        "impact_unknown_count": unknown_impact,
    }


__all__ = [
    "SCHEMA_VERSION", "CATEGORY_BY_CODE", "CATEGORY_LABELS",
    "canonical_findings", "resolve_impact", "build_intake_issues",
    "summarize_intake",
]
