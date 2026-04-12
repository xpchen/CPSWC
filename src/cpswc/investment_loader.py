"""
investment_loader.py — Investment F1 Import Path

Step 18: Mock overlay injection (YAML fixture, demo_only).
Step 19: Formal CSV/YAML import with strict validation.

核心函数:
  load_investment_overlay(fixture_path) → dict          # Step 18 (YAML mock)
  inject_overlay(snapshot_dict, overlay) → snapshot_dict
  load_csv(path) → ImportResult                         # Step 19
  load_import_file(path) → ImportResult                 # Step 19 (CSV or YAML)

设计边界:
  - overlay 只注入 investment 相关 facts, 不碰其他 facts
  - canonical sample 保持不动
  - CSV 导入模板对齐 INVESTMENT_FACTS_BACKFILL_CONTRACT L1+L2+L3
  - 校验失败 (errors > 0) 时不允许注入
"""
from __future__ import annotations

import copy
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ============================================================
# Constants & validation rules
# ============================================================

VALID_FEE_CATEGORIES = {"工程措施", "植物措施", "临时措施", "监测措施"}
VALID_SOURCE_ATTRIBUTIONS = {"主体已列", "方案新增"}
MEASURE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

CSV_REQUIRED_COLUMNS = {
    "measure_id", "measure_name", "fee_category",
    "prevention_zone", "unit", "quantity", "unit_price",
}
CSV_OPTIONAL_COLUMNS = {"source_attribution", "description"}
CSV_ALL_COLUMNS = CSV_REQUIRED_COLUMNS | CSV_OPTIONAL_COLUMNS


# ============================================================
# Import result
# ============================================================

@dataclass
class ImportResult:
    """Validated import result from CSV or YAML."""
    records: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    source_path: str = ""
    source_type: str = ""  # "csv" | "yaml_mock"

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    @property
    def summary(self) -> str:
        return (
            f"ImportResult: {len(self.records)} records, "
            f"{len(self.errors)} errors, {len(self.warnings)} warnings"
        )


# ============================================================
# CSV loader (Step 19)
# ============================================================

def load_csv(path: str | Path) -> ImportResult:
    """
    读取 F1 措施导入 CSV, 逐行校验, 返回 ImportResult。

    CSV 列 (对齐 INVESTMENT_FACTS_BACKFILL_CONTRACT L1+L2+L3):
      必填: measure_id, measure_name, fee_category, prevention_zone,
            unit, quantity, unit_price
      选填: source_attribution (缺省=方案新增+warn), description

    校验规则:
      - measure_id 唯一, 匹配 ^[a-z][a-z0-9_]*$
      - fee_category ∈ {工程措施, 植物措施, 临时措施, 监测措施}
      - source_attribution ∈ {主体已列, 方案新增} (缺省=方案新增)
      - quantity > 0, unit_price ≥ 0
      - amount_wan = quantity × unit_price / 10000, 四舍五入到 0.01
    """
    path = Path(path)
    result = ImportResult(source_path=str(path), source_type="csv")

    if not path.exists():
        result.errors.append(f"文件不存在: {path}")
        return result

    try:
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                result.errors.append("CSV 文件为空或无表头")
                return result

            # 列校验
            actual_cols = set(reader.fieldnames)
            missing = CSV_REQUIRED_COLUMNS - actual_cols
            if missing:
                result.errors.append(f"缺少必填列: {sorted(missing)}")
                return result
            unknown = actual_cols - CSV_ALL_COLUMNS
            if unknown:
                result.warnings.append(f"忽略未知列: {sorted(unknown)}")

            seen_ids: set[str] = set()

            for row_num, row in enumerate(reader, start=2):  # header is row 1
                _validate_row(row, row_num, seen_ids, result)

    except UnicodeDecodeError as e:
        result.errors.append(f"编码错误 (请使用 UTF-8): {e}")
    except csv.Error as e:
        result.errors.append(f"CSV 解析错误: {e}")

    return result


def _validate_row(
    row: dict, row_num: int, seen_ids: set[str], result: ImportResult
) -> None:
    """校验单行, 通过则 append 到 result.records"""
    prefix = f"行 {row_num}"
    has_error = False

    # --- measure_id ---
    mid = (row.get("measure_id") or "").strip()
    if not mid:
        result.errors.append(f"{prefix}: measure_id 不能为空")
        has_error = True
    elif not MEASURE_ID_PATTERN.match(mid):
        result.errors.append(
            f"{prefix}: measure_id '{mid}' 不合法 (需匹配 ^[a-z][a-z0-9_]*$)"
        )
        has_error = True
    elif mid in seen_ids:
        result.errors.append(f"{prefix}: measure_id '{mid}' 重复")
        has_error = True
    else:
        seen_ids.add(mid)

    # --- measure_name ---
    name = (row.get("measure_name") or "").strip()
    if not name:
        result.errors.append(f"{prefix}: measure_name 不能为空")
        has_error = True

    # --- fee_category ---
    cat = (row.get("fee_category") or "").strip()
    if cat not in VALID_FEE_CATEGORIES:
        result.errors.append(
            f"{prefix}: fee_category '{cat}' 不合法, "
            f"须为 {sorted(VALID_FEE_CATEGORIES)}"
        )
        has_error = True

    # --- prevention_zone ---
    zone = (row.get("prevention_zone") or "").strip()
    if not zone:
        result.errors.append(f"{prefix}: prevention_zone 不能为空")
        has_error = True

    # --- source_attribution ---
    attr = (row.get("source_attribution") or "").strip()
    if not attr:
        attr = "方案新增"
        result.warnings.append(
            f"{prefix}: source_attribution 未填, 默认 '方案新增' (保守原则)"
        )
    elif attr not in VALID_SOURCE_ATTRIBUTIONS:
        result.errors.append(
            f"{prefix}: source_attribution '{attr}' 不合法, "
            f"须为 {sorted(VALID_SOURCE_ATTRIBUTIONS)}"
        )
        has_error = True

    # --- unit ---
    unit = (row.get("unit") or "").strip()
    if not unit:
        result.errors.append(f"{prefix}: unit 不能为空")
        has_error = True

    # --- quantity ---
    qty_raw = (row.get("quantity") or "").strip()
    qty = None
    if not qty_raw:
        result.errors.append(f"{prefix}: quantity 不能为空")
        has_error = True
    else:
        try:
            qty = float(qty_raw)
            if qty <= 0:
                result.errors.append(f"{prefix}: quantity 须 > 0, 实际 {qty}")
                has_error = True
        except ValueError:
            result.errors.append(f"{prefix}: quantity '{qty_raw}' 不是数字")
            has_error = True

    # --- unit_price ---
    price_raw = (row.get("unit_price") or "").strip()
    price = None
    if not price_raw:
        result.errors.append(f"{prefix}: unit_price 不能为空")
        has_error = True
    else:
        try:
            price = float(price_raw)
            if price < 0:
                result.errors.append(f"{prefix}: unit_price 须 ≥ 0, 实际 {price}")
                has_error = True
        except ValueError:
            result.errors.append(f"{prefix}: unit_price '{price_raw}' 不是数字")
            has_error = True

    # --- description ---
    desc = (row.get("description") or "").strip()

    if has_error:
        return

    # --- amount 计算 ---
    amount_wan = round(qty * price / 10000, 2)

    result.records.append({
        "measure_id": mid,
        "measure_name": name,
        "fee_category": cat,
        "prevention_zone": zone,
        "source_attribution": attr,
        "unit": unit,
        "quantity": qty,
        "unit_price": price,
        "amount_wan": amount_wan,
        "description": desc,
    })


# ============================================================
# Unified import entry point (Step 19)
# ============================================================

def load_import_file(path: str | Path) -> ImportResult:
    """
    根据文件扩展名自动分发: .csv → load_csv, .yaml/.yml → load_yaml_mock。
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv(path)
    elif suffix in (".yaml", ".yml"):
        return _load_yaml_as_import(path)
    else:
        r = ImportResult(source_path=str(path))
        r.errors.append(f"不支持的文件格式: {suffix} (支持 .csv / .yaml)")
        return r


def _load_yaml_as_import(path: str | Path) -> ImportResult:
    """
    把 Step 18 的 YAML mock fixture 转换为 ImportResult 格式,
    复用同样的校验逻辑。
    """
    path = Path(path)
    result = ImportResult(source_path=str(path), source_type="yaml_mock")

    try:
        overlay = load_investment_overlay(path)
    except Exception as e:
        result.errors.append(f"YAML 加载失败: {e}")
        return result

    measures = overlay.get("measures") or []
    seen_ids: set[str] = set()

    for i, m in enumerate(measures, start=1):
        row = {
            "measure_id": m.get("measure_id", ""),
            "measure_name": m.get("measure_name", ""),
            "fee_category": m.get("fee_category", ""),
            "prevention_zone": m.get("prevention_zone", ""),
            "source_attribution": m.get("source_attribution", ""),
            "unit": m.get("unit", ""),
            "quantity": str(m.get("quantity", "")),
            "unit_price": str(m.get("unit_price", "")),
            "description": m.get("description", ""),
        }
        _validate_row(row, i, seen_ids, result)

    return result


# ============================================================
# ImportResult → overlay injection (Step 19)
# ============================================================

def inject_import_result(snapshot: dict, imp: ImportResult) -> dict:
    """
    把 validated ImportResult 注入 snapshot。
    imp.ok 必须为 True, 否则 raise ValueError。

    注入的 facts:
      - field.fact.investment.measures_registry: list of records
      - field.fact.investment.measures_summary: 按 fee_category 汇总
    """
    if not imp.ok:
        raise ValueError(
            f"ImportResult 有 {len(imp.errors)} 个错误, 不允许注入。"
            f"首条: {imp.errors[0] if imp.errors else '?'}"
        )

    result = copy.deepcopy(snapshot)
    facts = result.setdefault("_original_facts", {})

    facts["field.fact.investment.measures_registry"] = imp.records

    # 按 fee_category 汇总
    summary: dict[str, dict[str, float]] = {}
    for r in imp.records:
        cat = r["fee_category"]
        attr = r["source_attribution"]
        if cat not in summary:
            summary[cat] = {"new": 0.0, "existing": 0.0, "total": 0.0}
        amt = r.get("amount_wan") or 0.0
        if attr == "主体已列":
            summary[cat]["existing"] += amt
        else:
            summary[cat]["new"] += amt
        summary[cat]["total"] += amt

    # 四舍五入汇总
    for cat_data in summary.values():
        for k in cat_data:
            cat_data[k] = round(cat_data[k], 2)

    facts["field.fact.investment.measures_summary"] = summary

    result["_investment_overlay_active"] = True
    result["_investment_overlay_source"] = imp.source_path

    return result


# ============================================================
# Step 18 legacy: YAML mock overlay (preserved for compatibility)
# ============================================================

def load_investment_overlay(fixture_path: str | Path) -> dict:
    """读取 investment mock fixture YAML"""
    with open(fixture_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data.get("demo_only"):
        raise ValueError("Investment fixture must have demo_only: true")
    return data


def inject_overlay(snapshot: dict, overlay: dict) -> dict:
    """
    Step 18 legacy: 把 overlay 的 measures 数据注入 snapshot。
    Step 19+: 推荐使用 load_import_file() + inject_import_result() 代替。
    """
    result = copy.deepcopy(snapshot)
    facts = result.setdefault("_original_facts", {})
    measures = overlay.get("measures") or []

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

    result["_investment_overlay_active"] = True
    result["_investment_overlay_source"] = str(overlay.get("target_sample", "unknown"))

    return result
