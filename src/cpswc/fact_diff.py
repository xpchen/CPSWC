#!/usr/bin/env python3
"""
fact_diff.py — CPSWC v0 Step 27: Fact Change Diff + Review Trace

改一个 fact → 跑两次管线 → 输出 before/after 对比:
  - 哪些 facts 变了
  - 哪些 derived fields (calculator 产出) 变了
  - 哪些 obligations 触发状态变了
  - 哪些 narrative sections 变了 (文本/状态)
  - 哪些 tables 数据变了

用法:
  # 对比两个 facts 文件
  python -m cpswc.fact_diff samples/shiwei_logistics_v0.json --patch '{"facts":{"field.fact.land.total_area":{"value":10.0,"unit":"hm²"}}}'

  # 对比两个完整的 sample JSON
  python -m cpswc.fact_diff before.json after.json
"""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any


# ============================================================
# Diff result dataclasses
# ============================================================

@dataclass
class FieldChange:
    field_id: str
    before: Any
    after: Any
    change_type: str  # "added" | "removed" | "modified"


@dataclass
class ObligationChange:
    obligation_id: str
    before_triggered: bool | None
    after_triggered: bool | None
    change_type: str  # "newly_triggered" | "no_longer_triggered" | "unchanged"


@dataclass
class NarrativeChange:
    section_id: str
    title: str
    change_type: str  # "text_changed" | "status_changed" | "both" | "unchanged"
    before_status: str
    after_status: str
    text_diff_summary: str  # brief description


@dataclass
class TableChange:
    table_id: str
    changed: bool
    cell_changes: int  # number of cells that differ


@dataclass
class FactDiffReport:
    """Complete diff between two pipeline runs."""
    # Input
    patch_description: str

    # Changes
    fact_changes: list[FieldChange]
    derived_changes: list[FieldChange]
    obligation_changes: list[ObligationChange]
    narrative_changes: list[NarrativeChange]
    table_changes: list[TableChange]

    # Summary
    total_facts_changed: int = 0
    total_derived_changed: int = 0
    total_obligations_changed: int = 0
    total_sections_changed: int = 0
    total_tables_changed: int = 0


# ============================================================
# Core diff engine
# ============================================================

def _run_pipeline(project_input: dict) -> tuple[Any, dict, list]:
    """Run full pipeline, return (RuntimeSnapshot, snapshot_dict, narrative_blocks)."""
    from cpswc.runtime import run_project, _serialize_snapshot

    snapshot = run_project(project_input)
    snapshot_dict = json.loads(_serialize_snapshot(snapshot))
    snapshot_dict["_original_facts"] = project_input.get("facts") or {}

    from cpswc.narrative.projection import project_narrative
    narrative_result = project_narrative(snapshot_dict)

    return snapshot, snapshot_dict, narrative_result.blocks


def _run_tables(snapshot_dict: dict) -> dict[str, Any]:
    """Run all table projections, return {table_id: TableData}."""
    from cpswc.renderers.table_projections import TABLE_PROJECTIONS
    results = {}
    for table_id, func in TABLE_PROJECTIONS.items():
        try:
            results[table_id] = func(snapshot_dict)
        except Exception:
            results[table_id] = None
    return results


def _compare_values(a: Any, b: Any) -> bool:
    """Return True if values are meaningfully different."""
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    # Normalize Quantity dicts
    if isinstance(a, dict) and isinstance(b, dict):
        return json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True)
    if isinstance(a, (list, dict)) or isinstance(b, (list, dict)):
        return json.dumps(a, sort_keys=True, default=str) != json.dumps(b, sort_keys=True, default=str)
    return a != b


def _diff_facts(before_facts: dict, after_facts: dict) -> list[FieldChange]:
    """Compare two facts dicts."""
    changes = []
    all_keys = sorted(set(list(before_facts.keys()) + list(after_facts.keys())))
    for key in all_keys:
        bv = before_facts.get(key)
        av = after_facts.get(key)
        if key not in before_facts:
            changes.append(FieldChange(key, None, av, "added"))
        elif key not in after_facts:
            changes.append(FieldChange(key, bv, None, "removed"))
        elif _compare_values(bv, av):
            changes.append(FieldChange(key, bv, av, "modified"))
    return changes


def _diff_obligations(before_snap, after_snap) -> list[ObligationChange]:
    """Compare obligation trigger states."""
    before_triggered = set(before_snap.triggered_obligations)
    after_triggered = set(after_snap.triggered_obligations)
    all_obs = sorted(before_triggered | after_triggered |
                     set(before_snap.not_triggered_obligations) |
                     set(after_snap.not_triggered_obligations))

    changes = []
    for ob_id in all_obs:
        bt = ob_id in before_triggered
        at = ob_id in after_triggered
        if bt and not at:
            changes.append(ObligationChange(ob_id, True, False, "no_longer_triggered"))
        elif not bt and at:
            changes.append(ObligationChange(ob_id, False, True, "newly_triggered"))
        # Only report changes
    return changes


def _diff_narrative(before_blocks: list, after_blocks: list) -> list[NarrativeChange]:
    """Compare narrative blocks by section_id."""
    before_map = {b.section_id: b for b in before_blocks}
    after_map = {b.section_id: b for b in after_blocks}
    all_sids = sorted(set(list(before_map.keys()) + list(after_map.keys())))

    changes = []
    for sid in all_sids:
        bb = before_map.get(sid)
        ab = after_map.get(sid)
        if bb is None or ab is None:
            changes.append(NarrativeChange(
                sid, (ab or bb).title if (ab or bb) else sid,
                "added" if ab and not bb else "removed",
                bb.render_status.value if bb else "—",
                ab.render_status.value if ab else "—",
                "section added/removed",
            ))
            continue

        # Compare status
        status_changed = bb.render_status != ab.render_status

        # Compare text content
        def _block_text(block):
            parts = []
            for p in (block.paragraphs or []):
                parts.append(p.text)
            return "\n".join(parts)

        bt = _block_text(bb)
        at = _block_text(ab)
        text_changed = bt != at

        if not status_changed and not text_changed:
            continue

        if status_changed and text_changed:
            ct = "both"
        elif status_changed:
            ct = "status_changed"
        else:
            ct = "text_changed"

        # Build a brief diff summary
        if text_changed:
            # Find first difference
            bl = bt.split("\n")
            al = at.split("\n")
            diff_lines = []
            for i, (bline, aline) in enumerate(zip(bl, al)):
                if bline != aline:
                    diff_lines.append(f"  L{i+1}: '{bline[:60]}' → '{aline[:60]}'")
                    if len(diff_lines) >= 3:
                        break
            if len(bl) != len(al):
                diff_lines.append(f"  段落数: {len(bl)} → {len(al)}")
            summary = "\n".join(diff_lines) if diff_lines else "text differs"
        else:
            summary = f"status: {bb.render_status.value} → {ab.render_status.value}"

        changes.append(NarrativeChange(
            sid, bb.title, ct,
            bb.render_status.value, ab.render_status.value,
            summary,
        ))

    return changes


def _diff_tables(before_tables: dict, after_tables: dict) -> list[TableChange]:
    """Compare table projection outputs."""
    changes = []
    all_ids = sorted(set(list(before_tables.keys()) + list(after_tables.keys())))

    for tid in all_ids:
        bt = before_tables.get(tid)
        at = after_tables.get(tid)
        if bt is None and at is None:
            continue

        # Compare serialized table data
        def _serialize_td(td):
            if td is None:
                return "{}"
            if hasattr(td, 'rows'):
                return json.dumps(td.rows, default=str, sort_keys=True)
            return json.dumps(td, default=str, sort_keys=True)

        bs = _serialize_td(bt)
        as_ = _serialize_td(at)

        if bs != as_:
            # Count cell differences
            cell_diff = 0
            if bt and at and hasattr(bt, 'rows') and hasattr(at, 'rows'):
                for br, ar in zip(bt.rows, at.rows):
                    for bv, av in zip(br, ar):
                        if str(bv) != str(av):
                            cell_diff += 1
                # rows count difference
                row_diff = abs(len(bt.rows) - len(at.rows))
                if row_diff:
                    cols = max(
                        len(bt.rows[0]) if bt.rows else 0,
                        len(at.rows[0]) if at.rows else 0, 1)
                    cell_diff += row_diff * cols
                if cell_diff == 0:
                    # Rows matched pairwise but serialization differed —
                    # likely column count or metadata diff
                    cell_diff = 1
            else:
                cell_diff = 1  # can't count precisely
            changes.append(TableChange(tid, True, cell_diff))

    return changes


# ============================================================
# Main diff function
# ============================================================

def compute_diff(
    before_input: dict,
    after_input: dict,
    patch_description: str = "",
) -> FactDiffReport:
    """
    Run two pipeline instances and compare everything.

    Args:
        before_input: original project_input dict (with "facts" key)
        after_input: modified project_input dict (with "facts" key)
        patch_description: human-readable description of what changed

    Returns:
        FactDiffReport with all changes
    """
    # Run both pipelines
    before_snap, before_sd, before_blocks = _run_pipeline(before_input)
    after_snap, after_sd, after_blocks = _run_pipeline(after_input)

    # Diff facts
    fact_changes = _diff_facts(
        before_input.get("facts") or {},
        after_input.get("facts") or {},
    )

    # Diff derived fields
    derived_changes = _diff_facts(
        before_snap.derived_fields,
        after_snap.derived_fields,
    )

    # Diff obligations
    obligation_changes = _diff_obligations(before_snap, after_snap)

    # Diff narrative
    narrative_changes = _diff_narrative(before_blocks, after_blocks)

    # Diff tables
    before_tables = _run_tables(before_sd)
    after_tables = _run_tables(after_sd)
    table_changes = _diff_tables(before_tables, after_tables)

    return FactDiffReport(
        patch_description=patch_description,
        fact_changes=fact_changes,
        derived_changes=derived_changes,
        obligation_changes=obligation_changes,
        narrative_changes=narrative_changes,
        table_changes=table_changes,
        total_facts_changed=len(fact_changes),
        total_derived_changed=len(derived_changes),
        total_obligations_changed=len(obligation_changes),
        total_sections_changed=len(narrative_changes),
        total_tables_changed=len(table_changes),
    )


def apply_patch(base_input: dict, patch: dict) -> dict:
    """
    Apply a JSON patch to a project_input dict.

    patch format:
        {"facts": {"field.fact.X": new_value, ...}}
    """
    result = copy.deepcopy(base_input)
    patch_facts = patch.get("facts") or {}
    for key, val in patch_facts.items():
        result.setdefault("facts", {})[key] = val
    return result


# ============================================================
# Human-readable report
# ============================================================

def format_report(report: FactDiffReport) -> str:
    """Format a FactDiffReport as human-readable text."""
    lines = []
    lines.append("=" * 72)
    lines.append(" CPSWC Fact Change Diff Report")
    if report.patch_description:
        lines.append(f" Patch: {report.patch_description}")
    lines.append("=" * 72)
    lines.append("")

    # Summary
    lines.append("## 变更摘要")
    lines.append(f"  Facts 变更:       {report.total_facts_changed}")
    lines.append(f"  Derived 变更:     {report.total_derived_changed}")
    lines.append(f"  Obligations 变更: {report.total_obligations_changed}")
    lines.append(f"  Narrative 变更:   {report.total_sections_changed}")
    lines.append(f"  Tables 变更:      {report.total_tables_changed}")
    lines.append("")

    # Fact changes
    if report.fact_changes:
        lines.append("## Facts 变更")
        for fc in report.fact_changes:
            def _fmt(v):
                if isinstance(v, dict) and "value" in v:
                    return f"{v['value']} {v.get('unit', '')}"
                return str(v) if v is not None else "—"
            lines.append(f"  [{fc.change_type}] {fc.field_id}")
            lines.append(f"    before: {_fmt(fc.before)}")
            lines.append(f"    after:  {_fmt(fc.after)}")
        lines.append("")

    # Derived changes
    if report.derived_changes:
        lines.append("## Derived Fields 变更 (Calculator 产出)")
        for dc in report.derived_changes:
            def _fmt(v):
                if isinstance(v, dict) and "value" in v:
                    return f"{v['value']} {v.get('unit', '')}"
                if isinstance(v, (list, dict)):
                    return json.dumps(v, ensure_ascii=False)[:120]
                return str(v) if v is not None else "—"
            lines.append(f"  [{dc.change_type}] {dc.field_id}")
            lines.append(f"    before: {_fmt(dc.before)}")
            lines.append(f"    after:  {_fmt(dc.after)}")
        lines.append("")

    # Obligation changes
    if report.obligation_changes:
        lines.append("## Obligation 触发状态变更")
        for oc in report.obligation_changes:
            marker = "+" if oc.change_type == "newly_triggered" else "-"
            lines.append(f"  [{marker}] {oc.obligation_id}: {oc.change_type}")
        lines.append("")

    # Narrative changes
    if report.narrative_changes:
        lines.append("## Narrative 变更")
        for nc in report.narrative_changes:
            lines.append(f"  [{nc.change_type}] {nc.section_id} ({nc.title})")
            if nc.before_status != nc.after_status:
                lines.append(f"    status: {nc.before_status} → {nc.after_status}")
            if nc.text_diff_summary and nc.change_type in ("text_changed", "both"):
                for dl in nc.text_diff_summary.split("\n"):
                    lines.append(f"    {dl}")
        lines.append("")

    # Table changes
    if report.table_changes:
        lines.append("## Table 变更")
        for tc in report.table_changes:
            lines.append(f"  {tc.table_id}: {tc.cell_changes} cells changed")
        lines.append("")

    # Impact chain
    lines.append("## 影响链 (Fact → Calculator → Narrative/Table)")
    if report.fact_changes:
        changed_facts = {fc.field_id for fc in report.fact_changes}
        changed_derived = {dc.field_id for dc in report.derived_changes}
        changed_sections = {nc.section_id for nc in report.narrative_changes}
        changed_tables = {tc.table_id for tc in report.table_changes}
        lines.append(f"  输入变更: {', '.join(sorted(changed_facts))}")
        if changed_derived:
            lines.append(f"  → 计算变更: {', '.join(sorted(changed_derived))}")
        if changed_sections:
            lines.append(f"  → 叙述变更: {', '.join(sorted(changed_sections))}")
        if changed_tables:
            lines.append(f"  → 表格变更: {', '.join(sorted(changed_tables))}")
    lines.append("")
    lines.append("=" * 72)

    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def _cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="CPSWC Fact Change Diff — 改一个 fact, 看全部影响",
    )
    parser.add_argument("before", help="原始 sample JSON 文件")
    parser.add_argument("after", nargs="?", help="修改后 sample JSON (不提供时用 --patch)")
    parser.add_argument("--patch", help="JSON patch: {\"facts\":{\"field.X\":new_val}}")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--html", metavar="FILE", help="输出 Diff Workbench HTML")
    parser.add_argument("--output", "-o", help="输出到文件")
    args = parser.parse_args()

    before_path = Path(args.before)
    if not before_path.exists():
        print(f"ERROR: {before_path} not found", file=sys.stderr)
        return 2

    with before_path.open(encoding="utf-8") as f:
        before_input = json.load(f)

    if args.after:
        after_path = Path(args.after)
        if not after_path.exists():
            print(f"ERROR: {after_path} not found", file=sys.stderr)
            return 2
        with after_path.open(encoding="utf-8") as f:
            after_input = json.load(f)
        desc = f"{before_path.name} → {after_path.name}"
    elif args.patch:
        patch = json.loads(args.patch)
        after_input = apply_patch(before_input, patch)
        # Build description from patch keys
        changed_keys = list((patch.get("facts") or {}).keys())
        desc = f"patch: {', '.join(changed_keys)}"
    else:
        print("ERROR: 需要提供 after 文件或 --patch 参数", file=sys.stderr)
        return 2

    report = compute_diff(before_input, after_input, desc)

    # HTML workbench output
    if args.html:
        from cpswc.renderers.diff_workbench import (
            compute_diff_with_text, render_diff_workbench,
        )
        _, text_diffs = compute_diff_with_text(before_input, after_input, desc)
        html = render_diff_workbench(report, text_diffs)
        Path(args.html).write_text(html, encoding="utf-8")
        print(f"Diff Workbench HTML written to: {args.html}")
        return 0

    if args.json:
        from dataclasses import asdict
        output = json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str)
    else:
        output = format_report(report)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Diff report written to: {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(_cli())
