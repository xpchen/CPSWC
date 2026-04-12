#!/usr/bin/env bash
# ============================================================
# CPSWC v0 Showcase Demo Runner
# ============================================================
# 固定演示路径:
#   1. 真实项目录入 (世维物流)
#   2. 完整 submission package 生成
#   3. 变更影响追溯 (弃方 0→5)
#   4. 另一个变更场景 (占地面积 7.08→10.0)
#   5. 两个真实项目对比
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH=src

DEMO_OUT="output/showcase_demo"
mkdir -p "$DEMO_OUT"

echo "================================================================"
echo " CPSWC v0 Showcase Demo"
echo "================================================================"
echo ""

# ---- Step 1: Intake ----
echo "[1/5] 真实项目录入: intake.yaml → facts.json"
python3 -m cpswc.intake_validator \
    examples/intake_shiwei_v0/intake.yaml \
    --output "$DEMO_OUT/shiwei_facts.json" 2>&1 | head -20
echo ""

# ---- Step 2: Full Package ----
echo "[2/5] 完整报告包生成: facts → submission package"
python3 -c "
import json
from cpswc.renderers.package_builder import build_package
with open('$DEMO_OUT/shiwei_facts.json') as f:
    data = json.load(f)
build_package(data, '$DEMO_OUT/shiwei_package')
print('  OK: submission package built')
"
echo ""

# ---- Step 3: Diff - Spoil Change ----
echo "[3/5] 变更追溯 A: 弃方 0→5 万m³ (触发义务翻转)"
python3 -m cpswc.fact_diff \
    "$DEMO_OUT/shiwei_facts.json" \
    --patch '{"facts":{"field.fact.earthwork.spoil":{"value":5.0,"unit":"万m³"}}}' \
    --html "$DEMO_OUT/diff_spoil_change.html"
echo ""

# ---- Step 4: Diff - Land Area Change ----
echo "[4/5] 变更追溯 B: 占地面积 7.08→10.0 hm² (正文联动)"
python3 -m cpswc.fact_diff \
    "$DEMO_OUT/shiwei_facts.json" \
    --patch '{"facts":{"field.fact.land.total_area":{"value":10.0,"unit":"hm²"}}}' \
    --html "$DEMO_OUT/diff_land_change.html"
echo ""

# ---- Step 5: Two-project Comparison ----
echo "[5/5] 两个真实项目对比: 世维物流 vs 惠南智谷"
python3 -m cpswc.fact_diff \
    samples/shiwei_logistics_v0.json \
    samples/huinan_zhigu_v0.json \
    --html "$DEMO_OUT/diff_project_comparison.html"
echo ""

# ---- Summary ----
echo "================================================================"
echo " Demo 输出目录: $DEMO_OUT"
echo "================================================================"
echo ""
echo " 交付件清单:"
echo "   $DEMO_OUT/shiwei_facts.json              <- 录入产出的 facts"
echo "   $DEMO_OUT/shiwei_package/                 <- 完整 submission package"
echo "     rendered/narrative_skeleton_v0.docx      <- 正文报告 (Word)"
echo "     rendered/formal_tables_v0.docx           <- 正式表格 (Word)"
echo "     workbench.html                           <- 运行时工作台"
echo "   $DEMO_OUT/diff_spoil_change.html          <- 弃方变更影响 (最强演示)"
echo "   $DEMO_OUT/diff_land_change.html           <- 占地变更影响"
echo "   $DEMO_OUT/diff_project_comparison.html    <- 两项目对比"
echo ""
echo " 推荐演示顺序:"
echo "   1. 打开 shiwei_package/workbench.html     (展示规则引擎)"
echo "   2. 打开 shiwei_package/rendered/*.docx     (展示报告生成)"
echo "   3. 打开 diff_spoil_change.html             (展示变更追溯 ★)"
echo "   4. 打开 diff_project_comparison.html       (展示多项目对比)"
echo "================================================================"
