"""
modification_report.py — CPSWC v0 ModificationReport

宪法必做项 #14: "基于 FactDiff + ProjectionDiff 生成（不含 ObligationDiff）"

v0 边界 (Step 43-1 修正):
  - FactDiff: facts 层面的增删改 → diff_report.fact_changes
  - ProjectionDiff: facts → narrative/table 投影的变化
      → diff_report.narrative_changes (= NarrativeProjectionDiff)
      → diff_report.table_changes     (= TableProjectionDiff)
      → diff_report.derived_changes   (= DerivedProjectionDiff)
  - ObligationDiff: v0 不含, 显式排除
      → obligation_changes 从正式输出中过滤
      → obligation_diff_deferred = True

底层能力 (Step 27/28):
  - fact_diff.py: FactDiffReport — 两次管线跑比产出 5 维变更清单
  - diff_workbench.py: render_diff_workbench() — HTML 五视图渲染

v1 升级路径:
  - ObligationDiff 加入 (宪法 v1 条款)
  - Word/PDF 版修改对照表
  - OverlayDiff (决议 7 要求)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cpswc.fact_diff import (
    FactDiffReport,
    compute_diff,
)


@dataclass
class ModificationReport:
    """v0 修改报告 — 对比两次管线运行的变更清单。

    v0 范围 = FactDiff + ProjectionDiff (不含 ObligationDiff)。
    ProjectionDiff 由 narrative_changes + table_changes + derived_changes 组成。

    核心数据: diff_report (FactDiffReport, 底层完整数据)
    正式输出: 通过 property 访问, obligation_changes 被过滤
    """
    diff_report: FactDiffReport
    html: str | None = None

    # v0 宪法边界: ObligationDiff 显式排除
    obligation_diff_deferred: bool = True

    # --- v0 正式输出 (过滤后) ---

    @property
    def fact_changes(self) -> list:
        """FactDiff: facts 层面的增删改"""
        return self.diff_report.fact_changes

    @property
    def derived_changes(self) -> list:
        """DerivedProjectionDiff: calculator 输出的变化"""
        return self.diff_report.derived_changes

    @property
    def narrative_changes(self) -> list:
        """NarrativeProjectionDiff: 叙述文本投影的变化"""
        return self.diff_report.narrative_changes

    @property
    def table_changes(self) -> list:
        """TableProjectionDiff: 表格投影的变化"""
        return self.diff_report.table_changes

    @property
    def has_changes(self) -> bool:
        """v0 判断: 只看 FactDiff + ProjectionDiff, 不看 ObligationDiff"""
        r = self.diff_report
        return (r.total_facts_changed > 0
                or r.total_derived_changed > 0
                or r.total_sections_changed > 0
                or r.total_tables_changed > 0)

    @property
    def summary(self) -> str:
        r = self.diff_report
        parts = [
            f"{r.total_facts_changed} facts",
            f"{r.total_derived_changed} derived",
            f"{r.total_sections_changed} sections",
            f"{r.total_tables_changed} tables",
        ]
        s = f"ModificationReport(v0): {', '.join(parts)} changed"
        if self.obligation_diff_deferred:
            s += " [obligation_diff=v1_deferred]"
        return s


def generate(before: dict, after: dict) -> ModificationReport:
    """
    从 before/after 两份 project_input 生成 ModificationReport。

    v0 行为:
      - 底层 compute_diff() 仍然计算 obligation_changes (内部诊断用)
      - ModificationReport 对象层过滤掉 obligation_changes, 不暴露为正式输出
      - diff_report.obligation_changes 仍可通过 diff_report 直接访问 (诊断后门)
    """
    diff_report = compute_diff(before, after)
    return ModificationReport(diff_report=diff_report)


def render_html(report: ModificationReport) -> str:
    """
    将 ModificationReport 渲染为 HTML workbench。

    注意: diff_workbench 目前仍渲染 obligation 视图 (作为诊断信息),
    v1 闭合 ObligationDiff 后该视图升级为正式输出。
    """
    from cpswc.renderers.diff_workbench import render_diff_workbench
    html = render_diff_workbench(report.diff_report)
    report.html = html
    return html
