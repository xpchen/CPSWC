#!/usr/bin/env python3
"""
cpswc.demo — CPSWC v0 一键演示入口

用法:
  # 默认: 惠州样本 → runtime → package → 打开 workbench
  python -m cpswc.demo

  # 指定样本
  python -m cpswc.demo samples/shiwei_logistics_v0.json

  # diff 模式: 改一个 fact → 看影响
  python -m cpswc.demo --diff

  # 指定输出目录
  python -m cpswc.demo -o output/my_demo
"""

from __future__ import annotations

import argparse
import copy
import json
import platform
import subprocess
import sys
from pathlib import Path

from cpswc.paths import SAMPLES_DIR, PROJECT_ROOT


def _open_file(path: Path):
    """跨平台打开文件"""
    s = str(path)
    if platform.system() == "Darwin":
        subprocess.Popen(["open", s])
    elif platform.system() == "Windows":
        subprocess.Popen(["start", s], shell=True)
    else:
        subprocess.Popen(["xdg-open", s])


def _run_package(sample_path: Path, output_dir: Path) -> Path:
    """运行 runtime → package_builder, 返回 workbench 路径"""
    from cpswc.renderers.package_builder import build_package

    with open(sample_path, encoding="utf-8") as f:
        project_input = json.load(f)

    print(f"  样本: {sample_path.name}")
    print(f"  输出: {output_dir}")
    print()

    build_package(project_input=project_input, output_dir=output_dir)

    return output_dir / "workbench.html"


def _run_diff(sample_path: Path, output_dir: Path) -> Path:
    """运行 diff 演示: 改一个 fact → 对比两次管线"""
    from cpswc.modification_report import generate, render_html

    with open(sample_path, encoding="utf-8") as f:
        before = json.load(f)

    # 构造修改: 永久占地从 8.2 → 10.0 hm²
    after = copy.deepcopy(before)
    original_area = after["facts"].get("field.fact.land.permanent_area", {})
    old_val = original_area.get("value", "?") if isinstance(original_area, dict) else original_area
    new_val = round(float(old_val) * 1.2, 1) if old_val != "?" else 10.0

    after["facts"]["field.fact.land.permanent_area"] = {"value": new_val, "unit": "hm²"}

    print(f"  修改: field.fact.land.permanent_area {old_val} → {new_val} hm²")
    print()

    report = generate(before, after)
    html = render_html(report)

    output_dir.mkdir(parents=True, exist_ok=True)
    diff_path = output_dir / "diff_workbench.html"
    diff_path.write_text(html, encoding="utf-8")

    r = report.diff_report
    print(f"  变更统计:")
    print(f"    Facts:       {r.total_facts_changed}")
    print(f"    Derived:     {r.total_derived_changed}")
    print(f"    Obligations: {r.total_obligations_changed}")
    print(f"    Sections:    {r.total_sections_changed}")
    print(f"    Tables:      {r.total_tables_changed}")

    return diff_path


def main():
    parser = argparse.ArgumentParser(
        description="CPSWC v0 一键演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", nargs="?",
                        default=str(SAMPLES_DIR / "huizhou_housing_v0.json"),
                        help="样本 JSON 文件路径")
    parser.add_argument("-o", "--output", default=None,
                        help="输出目录 (默认 output/demo_<sample_name>)")
    parser.add_argument("--diff", action="store_true",
                        help="Diff 演示模式: 改一个 fact → 看影响")
    parser.add_argument("--no-open", action="store_true",
                        help="不自动打开浏览器")
    args = parser.parse_args()

    sample_path = Path(args.input)
    if not sample_path.exists():
        print(f"ERROR: 样本文件不存在: {sample_path}", file=sys.stderr)
        return 1

    sample_stem = sample_path.stem
    output_dir = Path(args.output) if args.output else PROJECT_ROOT / "output" / f"demo_{sample_stem}"

    print("=" * 60)
    print(" CPSWC v0 演示")
    print("=" * 60)
    print()

    if args.diff:
        print("▸ Diff 模式")
        result_path = _run_diff(sample_path, output_dir)
    else:
        print("▸ Package 模式")
        result_path = _run_package(sample_path, output_dir)

    print()
    print(f"  产出: {result_path}")
    print("=" * 60)

    if not args.no_open:
        _open_file(result_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
