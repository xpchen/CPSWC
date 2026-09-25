"""
frontend_payload.py — F-1A 前端 payload 管道

任务来源: docs/report_production_plan/implementation/FRONTEND_WIRING_PLAN.md v1.1
批准记录: implementation/DECISION_LOG.md 条目 012

把一次真实运行的结果导出成前端可直接消费的 payload, 并连同前端壳复制成一个
**自包含目录**, 双击 index.html 就能看。

    python -m cpswc.frontend_payload samples/huizhou_housing_v0.json

    → output/frontend/<project-code>/<generation-input-hash>/
          index.html  data.jsx  pages/*.jsx  payload.js

硬约束 (照抄 v1.1 计划, 违反即是把刚消灭的多套口径复制一份到这里):

  1. **只搬运, 不推断。** 字段状态一律取自 `BuildContext.project_fields()`,
     本模块不得自己判断 MISSING/PRESENT/单位/来源。
  2. **payload 是只读投影**, 不含任何可回写入口。
  3. **原子替换。** 先写临时目录再整体换名, 不允许半成品被打开。
  4. **壳漂移防护。** payload 记 `shell_digest`, 生成时盖进复制出去的壳;
     加载时比对不上 → PAYLOAD_ERROR, 不回落 mock。
  5. 输出到 `output/frontend/`, **不写 `src/frontend/`** —— 那会把真实客户
     数据留在源码目录里。`/output/` 已在 .gitignore。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cpswc.export_gate import check_export_readiness
from cpswc.input_hashing import directory_digest
from cpswc.intake_issues import (
    build_intake_issues, canonical_findings, summarize_intake,
)
from cpswc.narrative.projection import project_narrative
from cpswc.paths import FRONTEND_DIR, OUTPUT_DIR
from cpswc.report_quality import (
    evaluate_report_quality, load_content_requirements,
)
from cpswc.runtime import build_snapshot_dict, load_all_registries, run_project
from cpswc.snapshot_adapter import make_build_context

SCHEMA_VERSION = "cpswc_frontend_payload_v1"

# 前端壳里参与摘要的文件类型。改动其中任何一个文件, shell_digest 就变,
# 已生成的旧 bundle 会因比对不上而进 PAYLOAD_ERROR —— 这正是想要的。
_SHELL_PATTERNS = ("*.html", "*.jsx")

# payload 顶层必须齐全的键。缺任何一个 → 前端判 PAYLOAD_ERROR, 不回落 mock。
REQUIRED_TOP_LEVEL_KEYS: tuple[str, ...] = (
    "schema_version", "data_mode", "generated_at", "shell_digest",
    "project", "hashes", "facts", "field_lineage", "obligations",
    "obligations_detail", "calculators", "rule_refs",
    "required_artifacts", "required_assurances", "figures", "quality",
    "findings", "intake_issues", "intake_summary",
    "narrative", "requirements", "six_rates", "tables", "export_gate",
)


# ============================================================
# 1. 组装
# ============================================================

def build_payload(project_input: dict, registries: dict | None = None,
                  *, shell_dir: Path | None = None) -> dict:
    """
    跑一次完整管线, 组装 payload。**纯函数**, 不写任何文件。

    组装顺序刻意与后端的依赖顺序一致: snapshot → narrative → quality → gate,
    全部经 `build_snapshot_dict()` 的同一份统一视图 (验收 I01)。
    """
    _require_project_input(project_input)

    regs = registries if registries is not None else load_all_registries()
    fir_fields = (regs.get("fields") or {}).get("fields") or {}

    snapshot = run_project(project_input)
    snap_dict = build_snapshot_dict(snapshot, project_input, regs)

    # 字段状态: 唯一出口, 本模块不重新解析 (F-0.1)
    ctx = make_build_context(project_input, snapshot, regs,
                             enriched_views=snapshot.enriched_views)
    facts = ctx.project_fields()

    narrative = project_narrative(snap_dict)
    requirements = load_content_requirements(
        species=(snapshot.submission_profile.species
                 if snapshot.submission_profile else "报告书") or "报告书")
    quality = evaluate_report_quality(
        context=snap_dict, narrative=narrative,
        content_requirements=requirements,
        current_input_hash=snap_dict.get("generation_input_hash"))
    gate = check_export_readiness(snap_dict)

    findings = canonical_findings(
        build=snap_dict.get("_build_findings") or [],
        narrative=narrative.quality_findings,
        quality=quality.findings,
        gate=gate.findings)
    issues = build_intake_issues(
        {"build": snap_dict.get("_build_findings") or [],
         "narrative": narrative.quality_findings,
         "quality": quality.findings},
        fir_fields)

    return {
        "schema_version": SCHEMA_VERSION,
        # 生成器只会写 PROJECT_SNAPSHOT。DEMO / PAYLOAD_ERROR 由前端判定。
        "data_mode": "PROJECT_SNAPSHOT",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "shell_digest": shell_digest(shell_dir),

        "project": _project_block(snapshot, project_input),
        "hashes": {
            "hash_schema_version": snapshot.hash_schema_version,
            "fact_snapshot_hash": snapshot.fact_snapshot_hash,
            "generation_input_hash": snapshot.generation_input_hash,
        },

        "facts": facts,
        "field_lineage": _field_lineage(facts, fir_fields),
        "obligations_detail": _obligations_detail_block(
            snapshot, (regs.get("obligations") or {}).get("obligations") or {}),
        "calculators": _calculators_block(
            snapshot, (regs.get("calculators") or {}).get("calculators") or {}),
        "rule_refs": _rule_refs_block(
            (regs.get("obligations") or {}).get("obligations") or {},
            (regs.get("calculators") or {}).get("calculators") or {},
            (regs.get("assurances") or {}).get("assurances") or {},
            narrative),
        "required_artifacts": sorted(snapshot.required_artifacts or []),
        "figures": _figures_block(
            snapshot, (regs.get("artifacts") or {}).get("artifacts") or {}),
        "required_assurances": sorted(snapshot.required_assurances or []),
        "source_layers": snap_dict.get("_source_map") or {},

        "obligations": {
            "triggered": sorted(snapshot.triggered_obligations),
            "not_triggered": sorted(snapshot.not_triggered_obligations),
            "unknown": _unknown_obligations(snapshot),
        },

        "quality": _quality_block(quality, narrative, requirements),
        "findings": findings,
        "intake_issues": issues,
        "intake_summary": summarize_intake(issues),

        "narrative": _narrative_block(narrative, requirements),
        "requirements": _requirements_block(requirements, narrative),
        "six_rates": _six_rates_block(snap_dict),
        "tables": _tables_block(snap_dict),

        "export_gate": {
            "verdict": gate.verdict,
            "findings": [
                {"rule_id": f.rule_id, "action": f.action,
                 "message": f.message, "target_ref": f.target_ref}
                for f in gate.findings
            ],
            "block_count": len(gate.blocks),
            "warn_count": len(gate.warnings),
            # P0-08 未实现: 没有草稿/正式之分, 界面不得显示"可正式交付"
            "formal_export_implemented": False,
        },

        "runtime_diagnostics": list(snapshot.runtime_diagnostics or []),
    }


def _field_lineage(facts: list[dict], fir_fields: dict) -> dict:
    """每个字段影响到哪些章节 / 图件 / 投影, 取自 FIR `lineage`。

    **单独成块, 不并进 `facts`。** `facts` 是 `BuildContext.project_fields()`
    的逐字原样搬运 (有回归测试盯着), 往里塞字段会让"唯一出口"失去意义。

    解析不出来的字段**不出现在这里** —— 界面据此显示"影响范围尚未建立",
    而不是显示一个空列表然后被读成"不影响任何章节"。
    """
    out: dict[str, dict] = {}
    for f in facts:
        fid = f.get("field_id") or ""
        fdef = fir_fields.get(fid)
        if not isinstance(fdef, dict):
            continue
        refs = list((fdef.get("lineage") or {}).get("projection_target_refs") or [])
        if not refs:
            continue
        out[fid] = {
            "section_refs": sorted(r for r in refs if r.startswith("sec.")),
            "artifact_refs": sorted(r for r in refs if r.startswith("art.")),
            "projection_refs": sorted(r for r in refs if r.startswith("proj.")),
        }
    return out


def _obligations_detail_block(snapshot, obligation_registry: dict) -> list[dict]:
    """逐条义务的判定结果 + 登记元数据。

    `triggered` 直接来自三值判定: True / False / **None (未知)**。
    None 不折成 False —— "条件算不出来"和"条件不成立"是两回事,
    把前者当后者就等于悄悄放过一条可能适用的义务。
    """
    regs = obligation_registry or {}
    out: list[dict] = []
    for d in snapshot.obligation_details:
        meta = regs.get(d.obligation_id) or {}
        trigger = meta.get("trigger") or {}
        out.append({
            "obligation_id": d.obligation_id,
            "triggered": d.triggered,                    # True / False / None
            "applicability": snapshot.obligation_applicability.get(d.obligation_id, ""),
            "evaluation_status": d.evaluation_status,
            "mode": d.mode,
            "expression": d.py_expr or "",
            "human": trigger.get("human") or "",
            "source_rule_id": meta.get("source_rule_id") or "",
            "requirement_type": meta.get("requirement_type") or "",
            "protection_level": meta.get("protection_level") or "",
            "required_artifact_refs": list(meta.get("required_artifact_refs") or []),
            "required_assurance_refs": list(meta.get("required_assurance_refs") or []),
            "depends_on_field_refs": list(d.field_refs or []),
            "missing_field_refs": list(d.missing_field_refs or []),
            "diagnostic_code": d.diagnostic_code or "",
            "diagnostic_message": d.diagnostic_message or "",
            "v0_scope_note": meta.get("v0_scope_note") or "",
        })
    out.sort(key=lambda o: (o["triggered"] is not True, o["obligation_id"]))
    return out


def _calculators_block(snapshot, calculator_registry: dict) -> list[dict]:
    """计算器执行结果 + 登记元数据。

    **只列本次真跑过的计算器。** 登记表里有而没跑的单独由
    `registered_but_not_run` 给出, 界面要把"没跑"和"跑了"分开显示 ——
    混在一起会让人以为每个计算器都出过数。
    """
    regs = calculator_registry or {}
    out: list[dict] = []
    for r in snapshot.calculator_results:
        meta = regs.get(r.calculator_id) or {}
        out.append({
            "calculator_id": r.calculator_id,
            "canonical_name": meta.get("canonical_name") or r.calculator_id,
            "purpose": (meta.get("purpose") or "").strip(),
            "output_field_id": r.output_field_id,
            "value": r.value,
            "unit": r.unit or "",
            "status": r.status,
            "error_message": r.error_message or "",
            "protection_level": meta.get("protection_level") or "",
            "registry_status": meta.get("status") or "",
            "authority_class": meta.get("authority_class") or "",
            "provenance_verified": bool(meta.get("provenance_verified")),
            "normative_basis_refs": list(meta.get("normative_basis_refs") or []),
            "input_refs": [i.get("ref") for i in (meta.get("inputs") or [])
                           if isinstance(i, dict) and i.get("ref")],
            "formula": (meta.get("formula") or "").strip()
                       if isinstance(meta.get("formula"), str) else "",
        })
    return out


def _rule_refs_block(obligation_registry: dict, calculator_registry: dict,
                     assurance_registry: dict, narrative) -> list[dict]:
    """系统引用过的全部 `rule.*` 依据 ID, 以及谁在引用它。

    **这些 ID 在任何注册表里都没有登记标题或条文原文。** 这不是疏漏记录,
    而是要让界面把它说出来: 系统在引用自己从未登记的依据。
    """
    cited: dict[str, dict] = {}

    def add(rule_id: str, kind: str, who: str) -> None:
        if not rule_id or not str(rule_id).startswith("rule."):
            return
        e = cited.setdefault(rule_id, {"rule_id": rule_id, "cited_by": []})
        entry = {"kind": kind, "ref": who}
        if entry not in e["cited_by"]:
            e["cited_by"].append(entry)

    for oid, meta in (obligation_registry or {}).items():
        add(meta.get("source_rule_id"), "obligation", oid)
    for cid, meta in (calculator_registry or {}).items():
        for r in (meta.get("normative_basis_refs") or []):
            add(r, "calculator", cid)
    for aid, meta in (assurance_registry or {}).items():
        add(meta.get("source_rule_id"), "assurance", aid)
    for sec in (narrative.blocks if narrative else []):
        for para in (getattr(sec, "paragraphs", None) or []):
            for r in (getattr(para, "source_rule_refs", None) or []):
                add(r, "narrative", getattr(para, "paragraph_id", "") or sec.section_id)

    out = list(cited.values())
    for e in out:
        e["cited_by"].sort(key=lambda c: (c["kind"], c["ref"]))
        e["citation_count"] = len(e["cited_by"])
        # 全系统没有规则注册表, 所以标题/条文一律缺失。如实标出。
        e["title"] = ""
        e["title_registered"] = False
    out.sort(key=lambda e: (-e["citation_count"], e["rule_id"]))
    return out


# 已实现的渲染器。**名单在这里手工维护**, 因为 ArtifactRegistry 里的
# `renderer` 只是一个声明性的类名, 不保证代码存在 —— 实测 9 个图件渲染器
# 一个都没实现。界面据此如实显示"无法生成", 不画一张占位图糊弄过去。
_IMPLEMENTED_RENDERERS: frozenset[str] = frozenset()


def _figures_block(snapshot, artifact_registry: dict) -> list[dict]:
    """本项目需要的图件, 以及它们**能不能生成**。

    `required` 取自本次 runtime 推导出的 required_artifacts;
    `renderer_implemented` 取自上面的白名单, 不看登记表怎么写 ——
    登记表写了 renderer 名字不代表那个渲染器存在。
    """
    required = set(snapshot.required_artifacts or [])
    out: list[dict] = []
    for aid, meta in (artifact_registry or {}).items():
        if (meta.get("kind") or "") != "figure":
            continue
        renderer = meta.get("renderer") or ""
        out.append({
            "artifact_id": aid,
            "canonical_name": meta.get("canonical_name") or aid,
            "requirement": meta.get("requirement") or "",
            "required_for_this_project": aid in required,
            "content_spec": meta.get("content_spec") or "",
            "chapter_ref": meta.get("chapter_ref") or "",
            "data_source_refs": list(meta.get("data_source_refs") or []),
            "renderer": renderer,
            "renderer_implemented": renderer in _IMPLEMENTED_RENDERERS,
            "output_formats": list(meta.get("output_formats") or []),
        })
    out.sort(key=lambda f: (not f["required_for_this_project"], f["artifact_id"]))
    return out


def _require_project_input(project_input: dict) -> None:
    """喂错文件时立刻炸, 不许产出"项目名为空"的快照。

    实测踩到过: 把 `review_comments_*.json` (审查意见文档, 不是项目输入)
    喂进来, 管线一路畅通, 最后生成一个项目名、编码全空的 bundle ——
    顶栏"项目快照"下面挂着一片空白, 比报错危险得多。
    """
    schema = str(project_input.get("$schema") or "")
    if "ReviewComment" in schema:
        raise ValueError(
            f"这是审查意见文档 ($schema={schema})，不是项目输入，无法生成项目快照")
    if not (project_input.get("project") or project_input.get("facts")):
        raise ValueError("项目输入缺少 project / facts 节，无法生成项目快照")


def _project_block(snapshot, project_input: dict) -> dict:
    summary = snapshot.project_input_summary or {}
    profile = snapshot.submission_profile
    return {
        "name": summary.get("name") or "",
        "code": summary.get("code") or "",
        "industry": summary.get("industry") or "",
        "species": (profile.species if profile else "") or "",
        "ruleset": snapshot.ruleset,
        "lifecycle": snapshot.lifecycle,
        "source_file": str(project_input.get("_source_file") or ""),
    }


def _unknown_obligations(snapshot) -> list[dict]:
    reasons: dict[str, str] = {}
    for d in (snapshot.obligation_details or []):
        ob_id = getattr(d, "obligation_id", None)
        if ob_id in set(snapshot.unknown_obligations or []):
            reasons[ob_id] = (getattr(d, "diagnostic_message", "")
                              or "依赖输入不足")
    return [{"id": ob_id, "reason": reasons.get(ob_id, "依赖输入不足")}
            for ob_id in sorted(snapshot.unknown_obligations or [])]


def _quality_block(quality, narrative, requirements) -> dict:
    """
    覆盖率四行, **不做减法推断**。

    `64 - 38 = 26` 只能说明 26 项有实现映射, 不能说明它们有产出。
    `with_output_leaf_count` 单独测: 该 stable_id 确实产出了非空叶子内容。
    """
    d = quality.to_dict()
    mapped = 0
    with_output = 0
    if requirements is not None:
        produced = {
            b.section_id for b in narrative.blocks
            if getattr(b, "paragraphs", None)
            and str(getattr(b.render_status, "value", b.render_status)) == "full"
            and str(getattr(getattr(b, "content_role", None), "value", "")) != "PARENT_INTRO"
        }
        for r in requirements.requirements:
            if not r.is_leaf:
                continue
            if r.implemented:
                mapped += 1
                if r.section_id and r.section_id in produced:
                    with_output += 1

    cov = d["coverage"]
    return {
        **cov,
        "mapped_leaf_count": mapped,
        "with_output_leaf_count": with_output,
        "rendered_block_count": quality.rendered_block_count,
        "parent_intro_block_count": quality.parent_intro_block_count,
        "counts": d["counts"],
        "input_hash": quality.input_hash,
        # 只能由正式门禁写 (P0-08)。在那之前恒为 null, 界面显示"未判定"。
        "is_submittable": quality.is_submittable,
        "coverage_display": quality.coverage_display(),
    }


def _narrative_block(narrative, requirements) -> list[dict]:
    display = requirements.display_numbers if requirements else {}
    out = []
    for b in narrative.blocks:
        out.append({
            "section_id": b.section_id,
            "display_number": display.get(b.section_id, ""),
            "title": b.title,
            "render_status": str(getattr(b.render_status, "value", b.render_status)),
            "applicability": (b.applicability.value if b.applicability else ""),
            "content_role": str(getattr(b.content_role, "value", b.content_role)),
            "variant_id": b.variant_id or "",
            "template_id": b.template_id or "",
            "block_warnings": list(b.block_warnings or []),
            "finding_codes": sorted({f.code for f in (b.quality_findings or [])}),
            "paragraphs": [
                {
                    "paragraph_id": p.paragraph_id or "",
                    "text": p.text,
                    "assertion_class": str(getattr(p.assertion_class, "value",
                                                   p.assertion_class)),
                    "review_refs": list(p.review_refs or []),
                    "evidence_refs": list(p.evidence_refs or []),
                    "source_rule_refs": list(p.source_rule_refs or []),
                }
                for p in (b.paragraphs or [])
            ],
        })
    return out


def _requirements_block(requirements, narrative) -> list[dict]:
    if requirements is None:
        return []
    produced = {
        b.section_id for b in narrative.blocks
        if getattr(b, "paragraphs", None)
        and str(getattr(b.render_status, "value", b.render_status)) == "full"
    }
    return [
        {
            "id": r.requirement_id,
            "display_number": requirements.display_numbers.get(r.section_id, ""),
            "title": r.title,
            # **允许 null** —— 未实现要求确实尚未映射 stable ID
            "stable_id": r.section_id or None,
            "is_leaf": r.is_leaf,
            "implemented": r.implemented,
            "has_output": bool(r.section_id and r.section_id in produced),
            "condition_note": r.applicability_condition_ref or "",
        }
        for r in requirements.requirements
    ]


def _six_rates_block(snap_dict: dict) -> list[dict]:
    from cpswc.renderers.table_projections import project_six_indicator_review

    table = project_six_indicator_review(snap_dict)
    return [
        {"indicator": r["indicator"], "formula": r["formula"],
         "target": r["target"], "actual": r["actual"], "result": r["result"]}
        for r in table.rows
    ]


# 后端真正实现了的表投影。界面只能显示这些 ——
# **不在这里的表就是没有**, 界面必须说"未实现", 不许画一张空表糊弄过去。
_TABLE_PROJECTIONS = (
    "project_total_land_occupation",
    "project_land_occupation_by_county",
    "project_responsibility_range",
    "project_earthwork_balance",
    "project_topsoil_balance",
    "project_spoil_summary",
    "project_six_indicator_review",
    "project_investment_total_summary",
)


def _tables_block(snap_dict: dict) -> list[dict]:
    """把每个表投影跑一遍, 原样下发 spec + rows + 渲染策略 + warnings。

    渲染策略照搬后端的 `TableRenderPolicy` —— 界面不得把
    `RENDER_AS_SKELETON` 当成有值的表来画, 也不得把它藏起来。
    """
    from cpswc.renderers import table_projections as tp

    out: list[dict] = []
    for name in _TABLE_PROJECTIONS:
        fn = getattr(tp, name, None)
        if fn is None:
            continue
        try:
            data = fn(snap_dict)
        except Exception as exc:                     # noqa: BLE001
            # 投影炸了要**说出来**, 不能静默少一张表
            out.append({
                "table_id": f"art.table.{name}",
                "title": name, "columns": [], "rows": [], "total_row": None,
                "render_policy": "PROJECTION_FAILED",
                "warnings": [f"表投影执行失败: {type(exc).__name__}: {exc}"],
                "section_id": "", "footnote": "",
            })
            continue
        spec = data.spec
        out.append({
            "table_id": spec.table_id,
            "title": spec.title,
            "columns": [
                {"key": c.key, "header": c.header, "unit": c.unit,
                 "align": c.align, "fmt": c.fmt}
                for c in spec.columns
            ],
            "rows": [dict(r) for r in data.rows],
            "total_row": dict(data.total_row) if data.total_row else None,
            "has_total_row": spec.has_total_row,
            "render_policy": getattr(data.render_policy, "value", str(data.render_policy)),
            "warnings": list(data.warnings or []),
            "section_id": spec.section_id or "",
            "footnote": spec.footnote or "",
        })
    return out


# ============================================================
# 2. 校验
# ============================================================

def validate_payload(payload: Any) -> list[str]:
    """
    全量 schema 校验。返回问题清单, 空 = 通过。

    前端加载时做同样的检查; 任一条不通过 → PAYLOAD_ERROR, **绝不回落 mock**。
    """
    problems: list[str] = []
    if not isinstance(payload, dict):
        return ["payload 不是对象"]

    if payload.get("schema_version") != SCHEMA_VERSION:
        problems.append(
            f"schema_version 不匹配: 期望 {SCHEMA_VERSION}, "
            f"实为 {payload.get('schema_version')!r}")
    if payload.get("data_mode") != "PROJECT_SNAPSHOT":
        problems.append(f"data_mode 应为 PROJECT_SNAPSHOT, "
                        f"实为 {payload.get('data_mode')!r}")

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            problems.append(f"缺顶层键 {key}")

    hashes = payload.get("hashes") or {}
    for key in ("hash_schema_version", "fact_snapshot_hash",
                "generation_input_hash"):
        if not hashes.get(key):
            problems.append(f"hashes.{key} 为空")

    if not payload.get("shell_digest"):
        problems.append("shell_digest 为空, 无法做壳漂移比对")

    # 项目名是顶栏"这是哪个项目的快照"的唯一依据。空名字的快照没有意义,
    # 而且会让界面在真项目名的位置上留一片空白 —— 宁可拒绝加载。
    proj = payload.get("project")
    if isinstance(proj, dict) and not str(proj.get("name") or "").strip():
        problems.append("project.name 为空, 无法确认这是哪个项目的快照")

    facts = payload.get("facts")
    if not isinstance(facts, list) or not facts:
        problems.append("facts 为空 —— 字段状态是 Facts 页的全部内容")
    else:
        for f in facts[:  # 抽查全部, 但只报前几条, 避免刷屏
                       len(facts)]:
            missing = [k for k in ("field_id", "state", "provenance")
                       if k not in f]
            if missing:
                problems.append(f"facts 条目缺 {missing}: {f.get('field_id')}")
                break
            if f["state"] != "PRESENT" and f.get("value") is not None:
                problems.append(
                    f"{f['field_id']}: 非 PRESENT 却带 value —— "
                    f"调用方可能绕过 state 直接用值")
                break

    findings = payload.get("findings") or {}
    for layer in ("build", "narrative", "quality", "gate"):
        if layer not in findings:
            problems.append(f"findings 缺分层 {layer}")
    if "counts_by_severity" not in findings:
        problems.append("findings 缺 counts_by_severity")

    quality = payload.get("quality") or {}
    if "is_submittable" not in quality:
        problems.append("quality.is_submittable 缺失 (未判定也要显式给 null)")

    return problems


# ============================================================
# 3. 落盘 (自包含 + 原子替换)
# ============================================================

def shell_digest(shell_dir: Path | None = None) -> str:
    """前端壳源码摘要。壳改了这个值就变, 旧 bundle 会因比对不上而拒绝加载。"""
    return directory_digest(shell_dir or FRONTEND_DIR, patterns=_SHELL_PATTERNS)


def _payload_js(payload: dict) -> str:
    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return (
        "// 由 `python -m cpswc.frontend_payload` 生成, 请勿手工编辑。\n"
        "// 这是某个具体项目某一次运行的快照, 不是实时数据。\n"
        f"window.CPSWC_PAYLOAD = {body};\n"
    )


def write_bundle(payload: dict, out_root: Path | None = None,
                 shell_dir: Path | None = None) -> Path:
    """
    把壳 + payload 写成**一个自包含的 index.html**。

    路径: `<out_root>/<project-code>/<generation-input-hash>/index.html`
    不同项目、不同输入互不覆盖。

    ### 为什么必须内联成单文件

    浏览器实测发现: 原壳用 `<script type="text/babel" src="pages/X.jsx">`,
    而 Babel 是用 XHR 去取这些文件的。在 `file://` 下 Chrome 按 CORS 策略
    直接拒绝 (`Access to XMLHttpRequest ... from origin 'null' has been
    blocked`), 结果是**整个页面白屏**。

    也就是说"双击 index.html 就能跑"这个前提, 对拆成多文件的壳并不成立。
    因此 bundle 把全部 JSX 与 payload 内联进单个 HTML —— 既保住了双击可开,
    也让这份快照可以整个发给别人。

    ### 原子替换

    先写同级临时目录, 全部就绪后再整体换名。中途失败不会留下半成品被打开。
    """
    problems = validate_payload(payload)
    if problems:
        raise ValueError("payload 未通过校验, 拒绝落盘:\n  - "
                         + "\n  - ".join(problems))

    shell = Path(shell_dir or FRONTEND_DIR)
    root = Path(out_root or (OUTPUT_DIR / "frontend"))
    code = _safe_name(payload["project"].get("code")
                      or payload["project"].get("name") or "unknown")
    gen_hash = payload["hashes"]["generation_input_hash"][:16]
    target = root / code / gen_hash
    target.parent.mkdir(parents=True, exist_ok=True)

    html = render_standalone_html(payload, shell)

    staging = Path(tempfile.mkdtemp(prefix=f".{gen_hash}.", dir=target.parent))
    try:
        (staging / "index.html").write_text(html, encoding="utf-8")
        # 另存一份 payload, 便于排查与外部核对 (页面本身不依赖它)
        (staging / "payload.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        if target.exists():
            doomed = target.with_name(target.name + ".replaced")
            target.rename(doomed)
            shutil.rmtree(doomed, ignore_errors=True)
        staging.rename(target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target


_SCRIPT_RE = re.compile(
    r'<script\s+type="text/babel"\s+src="([^"]+)"\s*>\s*</script>')


def render_standalone_html(payload: dict | None,
                           shell_dir: Path | None = None) -> str:
    """把壳的全部 JSX 与 payload 内联进一个 HTML 字符串。

    脚本顺序照抄原 index.html 的 `<script src=...>` 顺序 —— 那个顺序是有
    依赖关系的 (data.jsx 定义全局, pages 用它, App/Root 最后)。

    `payload=None` 产出**演示模式**的单文件壳。原壳目录本身在 `file://` 下
    会因 CORS 白屏 (见 `write_bundle` 说明), 所以"演示壳"也必须走同一条内联
    路径, 否则我们验的演示模式和用户看到的不是一个东西。
    """
    shell = Path(shell_dir or FRONTEND_DIR)
    index = shell / "index.html"
    if not index.exists():
        raise FileNotFoundError(f"找不到前端壳 {index}")
    html = index.read_text(encoding="utf-8")

    sources = _SCRIPT_RE.findall(html)
    missing = [s for s in sources if not (shell / s).exists()]
    if missing:
        raise FileNotFoundError(f"壳里引用的脚本不存在: {missing}")

    # payload 先于一切业务脚本, data.jsx 判三态时要先拿到它
    blocks = []
    if payload is not None:
        blocks.append('<script>\n' + _payload_js(payload) + '</script>')
    for src in sources:
        code = (shell / src).read_text(encoding="utf-8")
        blocks.append(
            f'<script type="text/babel" data-source="{src}">\n{code}\n</script>')

    # 移除原来的外链 script (它们在 file:// 下会被 CORS 拦掉)
    html = _SCRIPT_RE.sub("", html)
    if payload is not None and 'name="cpswc-shell-digest"' not in html:
        # **必须现场按壳文件算**, 不能抄 payload 里的值。
        # 抄了的话两边永远相等, 壳漂移检查就成了摆设 —— 浏览器验收实测踩到过:
        # 把 payload.shell_digest 改成 000... 仍然畅通无阻。
        meta = (f'<meta name="cpswc-shell-digest" '
                f'content="{shell_digest(shell)}" />')
        html = html.replace("</head>", f"{meta}\n</head>", 1)
    return html.replace("</body>", "\n".join(blocks) + "\n</body>", 1)


def _safe_name(raw: str) -> str:
    keep = [c if (c.isalnum() or c in "-_.") else "_" for c in str(raw)]
    return ("".join(keep)[:60] or "unknown").strip("._") or "unknown"


# ============================================================
# 4. CLI
# ============================================================

def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="生成前端 payload 与自包含 bundle")
    parser.add_argument("input", help="项目 JSON 文件")
    parser.add_argument("-o", "--output", default=None,
                        help="输出根目录 (默认 output/frontend)")
    parser.add_argument("--payload-only", action="store_true",
                        help="只把 payload JSON 打到 stdout, 不落盘")
    args = parser.parse_args(argv)

    path = Path(args.input)
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 2

    project_input = json.loads(path.read_text(encoding="utf-8"))
    project_input.setdefault("_source_file", str(path))
    payload = build_payload(project_input)

    problems = validate_payload(payload)
    if problems:
        print("ERROR: payload 未通过校验:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 4

    if args.payload_only:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return 0

    target = write_bundle(payload, Path(args.output) if args.output else None)
    q = payload["quality"]
    s = payload["intake_summary"]
    print("=" * 68)
    print(f" 项目快照已生成: {target}")
    print(f" 项目: {payload['project']['name']}")
    print(f" generation_input_hash: {payload['hashes']['generation_input_hash'][:16]}")
    print("-" * 68)
    print(f" 内容要求 {q.get('applicable_leaf_count')} 项"
          f" | 已建立映射 {q.get('mapped_leaf_count')}"
          f" | 本次有产出 {q.get('with_output_leaf_count')}"
          f" | 未实现 {q.get('unimplemented_leaf_count')}"
          f" | 确认完成 {q.get('complete_leaf_count')}")
    print(f" 收资清单 {s['total']} 项 {s['by_severity']}")
    print(f" 导出门禁 {payload['export_gate']['verdict']}"
          f" ({payload['export_gate']['block_count']} block)")
    print("=" * 68)
    print(f" 双击打开: {target / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
