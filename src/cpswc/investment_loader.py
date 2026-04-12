"""
investment_loader.py — Investment Mock Data Overlay Injection

Step 18: 以 overlay 方式将 mock F1 投资数据注入 RuntimeSnapshot,
不修改 canonical sample facts。

核心函数:
  load_investment_overlay(fixture_path) → dict
  inject_overlay(snapshot_dict, overlay) → snapshot_dict (mutated copy)

设计边界:
  - overlay 只注入 investment 相关 facts, 不碰其他 facts
  - canonical sample 保持不动
  - overlay 数据标记 demo_only=true
  - 关闭 overlay 后, 产出与 canonical 完全一致
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


def load_investment_overlay(fixture_path: str | Path) -> dict:
    """读取 investment mock fixture YAML"""
    with open(fixture_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data.get("demo_only"):
        raise ValueError("Investment fixture must have demo_only: true")
    return data


def inject_overlay(snapshot: dict, overlay: dict) -> dict:
    """
    把 overlay 的 measures 数据注入 snapshot 的 _original_facts,
    返回 snapshot 的深拷贝 (不修改原 snapshot)。

    注入的 facts:
      - field.fact.investment.measures_registry: list of measure records
      - field.fact.investment.measures_summary: 按 fee_category 汇总

    同时在 snapshot 顶层加:
      - _investment_overlay_active: true
      - _investment_overlay_source: fixture 路径
    """
    result = copy.deepcopy(snapshot)
    facts = result.setdefault("_original_facts", {})
    measures = overlay.get("measures") or []

    # 注入 measures registry
    registry = []
    for m in measures:
        amount = None
        qty = m.get("quantity")
        price = m.get("unit_price")
        if qty is not None and price is not None:
            amount = round(float(qty) * float(price) / 10000, 4)  # 元→万元
        registry.append({
            "measure_id": m.get("measure_id"),
            "measure_name": m.get("measure_name"),
            "fee_category": m.get("fee_category"),
            "prevention_zone": m.get("prevention_zone"),
            "source_attribution": m.get("source_attribution", "方案新增"),
            "unit": m.get("unit"),
            "quantity": qty,
            "unit_price": price,
            "amount_wan": amount,
            "description": m.get("description", ""),
            "demo_only": True,
        })

    facts["field.fact.investment.measures_registry"] = registry

    # 按 fee_category 汇总
    summary = {}
    for r in registry:
        cat = r["fee_category"]
        attr = r["source_attribution"]
        if cat not in summary:
            summary[cat] = {"new": 0.0, "existing": 0.0, "total": 0.0}
        amt = r["amount_wan"] or 0.0
        if attr == "主体已列":
            summary[cat]["existing"] += amt
        else:
            summary[cat]["new"] += amt
        summary[cat]["total"] += amt

    facts["field.fact.investment.measures_summary"] = summary

    # 标记 overlay 状态
    result["_investment_overlay_active"] = True
    result["_investment_overlay_source"] = str(overlay.get("target_sample", "unknown"))

    return result
