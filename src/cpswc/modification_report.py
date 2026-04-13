"""
modification_report.py — CPSWC v0 ModificationReport

宪法收口: 对应 ARCHITECTURE_DECISIONS.md 宪法必做项 #14。
把 fact_diff.FactDiffReport + diff_workbench 渲染能力包装为正式的
ModificationReport_v0 契约对象。

底层能力 (Step 27/28 已完成):
  - fact_diff.py: FactDiffReport — 两次管线跑比产出 5 维变更清单
  - diff_workbench.py: render_diff_workbench() — HTML 五视图渲染

本模块职责:
  1. 声明 ModificationReport 为正式契约对象
  2. 提供 generate() 函数: 接受 before/after 两份 project_input → 产出 report
  3. 提供 render_html() 函数: 将 report 渲染为 HTML workbench

设计边界:
  - 不碰 runtime.py 的执行逻辑 (runtime 仍然 scope-out "不做 ModificationReport")
  - runtime 产出 snapshot, 本模块消费 snapshot 产出 report
  - v0 不做 Word/PDF 版修改对照表 (v1 升级路径)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cpswc.fact_diff import (
    FactDiffReport,
    compute_diff,
)


@dataclass
class ModificationReport:
    """v0 修改报告 — 对比两次管线运行的完整变更清单。

    核心数据: diff_report (FactDiffReport)
    渲染产出: html (可选, 由 render_html() 填充)
    """
    diff_report: FactDiffReport
    html: str | None = None

    # 便捷属性
    @property
    def has_changes(self) -> bool:
        r = self.diff_report
        return (r.total_facts_changed > 0
                or r.total_derived_changed > 0
                or r.total_obligations_changed > 0)

    @property
    def summary(self) -> str:
        r = self.diff_report
        return (
            f"ModificationReport: "
            f"{r.total_facts_changed} facts, "
            f"{r.total_derived_changed} derived, "
            f"{r.total_obligations_changed} obligations, "
            f"{r.total_sections_changed} sections, "
            f"{r.total_tables_changed} tables changed"
        )


def generate(before: dict, after: dict) -> ModificationReport:
    """
    从 before/after 两份 project_input 生成 ModificationReport。

    参数:
      before: 修改前的 project_input (sample JSON dict)
      after: 修改后的 project_input (sample JSON dict)

    返回:
      ModificationReport (含 diff_report, 不含 html)
    """
    diff_report = compute_diff(before, after)
    return ModificationReport(diff_report=diff_report)


def render_html(report: ModificationReport) -> str:
    """
    将 ModificationReport 渲染为 HTML workbench。

    返回 HTML 字符串, 同时回写到 report.html。
    """
    from cpswc.renderers.diff_workbench import render_diff_workbench
    html = render_diff_workbench(report.diff_report)
    report.html = html
    return html
