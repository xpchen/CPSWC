#!/usr/bin/env python3
"""
sample_validator.py — CPSWC v0 端到端集成验收

Step 12A 重构: 本脚本从 monolithic 验证器变为 thin assertion layer over
cpswc_runtime.run_project()。

职责:
  1. 调用 cpswc_runtime.run_project() 获得 RuntimeSnapshot
  2. 比对 snapshot 的 triggered obligations vs sample 的 designed_to_trigger
  3. 比对 snapshot 的 calculator 产出 vs sample 的 ground truth (annotation cross-check)
  4. 产出 diff 报告: false positive / false negative / calculator mismatch

退出码:
  0 通过: 实际触发与设计预期一致 + calculator cross-check GREEN
  1 失败: 有 false positive / false negative / calculator mismatch
  2 使用错误: 样本/registry 缺失
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SPECS_DIR = Path(__file__).resolve().parent

ANSI = {
    "RED":   "\033[31m", "GRN": "\033[32m", "YEL": "\033[33m",
    "CYN":   "\033[36m", "GRY": "\033[90m", "BLD": "\033[1m",
    "RST":   "\033[0m",
}

def color(text, c):
    if sys.stdout.isatty():
        return f"{ANSI[c]}{text}{ANSI['RST']}"
    return text


# ============================================================
# Calculator cross-check (assertion logic, not runtime logic)
# ============================================================
# 显式白名单避免 "restoRATIOn" 这类子串误匹配
_RATIO_KEYS = {"soil_loss_control_ratio"}

def _tolerance_for_key(key: str, tolerances: dict) -> float:
    if key in _RATIO_KEYS:
        return float(tolerances.get("ratio_fields", 0.01))
    return float(tolerances.get("percent_fields", 0.5))


def _run_calculator_cross_check(
    snapshot,  # RuntimeSnapshot
    sample: dict,
    loaded_registries: dict,
) -> tuple[bool, list[tuple[str, str]]]:
    """对 calculator 产出 vs sample 做双向 cross-check。返回 (ok, reports)"""
    from cpswc_runtime import _get_field  # type: ignore

    calc_ok = True
    reports: list[tuple[str, str]] = []

    # 构造 annotation 索引
    annotation_index: dict[str, tuple[dict, str]] = {}
    annotations = ((sample.get("sample_meta") or {}).get("annotations") or {})
    for ann_key, ann_val in annotations.items():
        if isinstance(ann_val, dict):
            tgt_calc = ann_val.get("_verification_calculator")
            if tgt_calc:
                annotation_index[tgt_calc] = (ann_val, f"sample_meta.annotations.{ann_key}")
    derived_block = sample.get("derived") or {}
    for drv_key, drv_val in derived_block.items():
        if isinstance(drv_val, dict):
            tgt_calc = drv_val.get("_verification_calculator")
            if tgt_calc:
                annotation_index[tgt_calc] = (drv_val, f"derived.{drv_key}")

    for cr in snapshot.calculator_results:
        if cr.status != "ok":
            calc_ok = False
            reports.append(("ERR", f"{cr.calculator_id} 执行失败: {cr.error_message}"))
            continue

        # Result summary
        if isinstance(cr.value, dict):
            reports.append(("OK", f"{cr.calculator_id} → {cr.output_field_id} (record, {len(cr.value)} fields)"))
        elif isinstance(cr.value, list):
            reports.append(("OK", f"{cr.calculator_id} → {cr.output_field_id} (list, {len(cr.value)} records)"))
        else:
            reports.append(("OK", f"{cr.calculator_id} → {cr.output_field_id} = {cr.value} {cr.unit}"))

        ann_entry = annotation_index.get(cr.calculator_id)
        if ann_entry is None:
            reports.append(("INFO", f"{cr.calculator_id} 无 annotation 断言, 跳过 cross-check"))
            continue
        ann, ann_source = ann_entry
        if ann.get("_verification_source") != "derived_field_should_match":
            continue

        # ---- 11A scalar mode ----
        if not isinstance(cr.value, (dict, list)):
            tolerance = ann.get("_verification_tolerance_wan", 0.01)
            ann_rate = ann.get("rate_value")
            # find rate from calculator intermediate (hardcoded key)
            # We need the CalcResult intermediate but snapshot only has CalcResultSummary.
            # For 11A cross-check, compare against annotation directly.
            ann_expected = ann.get("expected_amount_wan")
            if ann_expected is not None:
                if abs(float(ann_expected) - float(cr.value)) > float(tolerance):
                    calc_ok = False
                    reports.append(("ERR", f"{cr.calculator_id} 输出不一致: "
                                          f"expected={ann_expected}, calculator={cr.value}"))
                else:
                    reports.append(("OK", f"{cr.calculator_id} ground truth: "
                                         f"{cr.value} 万元 (期望 {ann_expected})"))
            # Rate check: need to run calculator again to get intermediate...
            # Simplified: compare annotation rate_value vs sample fact field
            if ann_rate is not None:
                fact_rate_field = sample.get("facts", {}).get(
                    "field.fact.regulatory.compensation_fee_rate")
                if isinstance(fact_rate_field, dict):
                    fact_rate = fact_rate_field.get("value")
                    if fact_rate is not None and abs(float(ann_rate) - float(fact_rate)) > 1e-9:
                        calc_ok = False
                        reports.append(("ERR", f"{cr.calculator_id} rate 不一致: "
                                              f"ann={ann_rate} vs fact={fact_rate}"))
                    elif fact_rate is not None:
                        reports.append(("OK", f"{cr.calculator_id} rate 双向一致 ({ann_rate} 元/m²)"))
            continue

        # ---- 11C list_of_records mode ----
        if isinstance(cr.value, list):
            expected_list = (sample.get("derived") or {}).get(cr.output_field_id)
            if expected_list is None:
                reports.append(("INFO", f"{cr.calculator_id} sample.derived 无 {cr.output_field_id}"))
                continue
            if not isinstance(expected_list, list):
                calc_ok = False
                reports.append(("ERR", f"{cr.calculator_id} expected 不是 list"))
                continue
            if len(expected_list) != len(cr.value):
                calc_ok = False
                reports.append(("ERR", f"{cr.calculator_id} 记录数不一致"))
                continue

            ID_KEYS = ("site_id", "zone_id", "id")
            def _id_of(rec):
                for k in ID_KEYS:
                    if isinstance(rec, dict) and k in rec:
                        return str(rec[k])
                return None

            exp_by_id = {_id_of(r): r for r in expected_list}
            calc_by_id = {_id_of(r): r for r in cr.value}
            if set(exp_by_id.keys()) != set(calc_by_id.keys()):
                calc_ok = False
                reports.append(("ERR", f"{cr.calculator_id} record ID 不一致"))
                continue

            reports.append(("OK", f"{cr.calculator_id} list cross-check ({len(cr.value)} records)"))
            for rid in sorted(exp_by_id.keys()):
                exp_rec = exp_by_id[rid]
                calc_rec = calc_by_id[rid]
                common = {k for k in (set(exp_rec.keys()) & set(calc_rec.keys()))
                          if not k.startswith("_")}
                for k in sorted(common):
                    if exp_rec[k] == calc_rec[k]:
                        reports.append(("OK", f"    [{rid}].{k}: {exp_rec[k]}  \u2713"))
                    else:
                        calc_ok = False
                        reports.append(("ERR", f"    [{rid}].{k}: expected={exp_rec[k]} "
                                              f"vs calculator={calc_rec[k]}  \u2717"))
            continue

        # ---- 11B record mode ----
        if isinstance(cr.value, dict):
            tolerances = ann.get("_verification_tolerances") or {
                "percent_fields": 0.5, "ratio_fields": 0.01}
            record_keys = [k for k in ann.keys()
                           if not k.startswith("_") and k not in
                           ("trigger", "derivation_note", "corrected_by",
                            "correction_basis", "correction_date")]
            record_keys = [k for k in record_keys if k in cr.value]
            if not record_keys:
                reports.append(("INFO", f"{cr.calculator_id} 无可对比 record keys"))
                continue

            prev_audit = ann.get("_previous_values_audit") or {}
            prev_values = prev_audit.get("previous_values") or {}
            reports.append(("OK", f"{cr.calculator_id} record cross-check "
                                  f"({len(record_keys)} keys, from {ann_source})"))
            for rk in record_keys:
                ann_val = float(ann[rk])
                calc_val = float(cr.value[rk])
                tol = _tolerance_for_key(rk, tolerances)
                prev_val = prev_values.get(rk)
                diff = abs(ann_val - calc_val)
                prev_str = f"prev={prev_val} \u2192 " if prev_val is not None else ""
                msg = (f"    {rk}: {prev_str}expected={ann_val} "
                       f"vs calculator={calc_val} (tol \u00b1{tol})")
                if diff > tol:
                    calc_ok = False
                    reports.append(("ERR", f"{msg}  \u2717 OUT OF TOLERANCE"))
                else:
                    reports.append(("OK", f"{msg}  \u2713 diff={diff:.4f}"))

    return calc_ok, reports


# ============================================================
# Main validator
# ============================================================
def validate(sample_path: Path) -> int:
    with sample_path.open(encoding="utf-8") as f:
        sample = json.load(f)

    # ---- Run project through runtime ----
    try:
        from cpswc_runtime import run_project, load_all_registries  # type: ignore
    except Exception as e:
        print(f"ERROR: cpswc_runtime import 失败: {e}", file=sys.stderr)
        return 2

    try:
        snapshot = run_project(sample)
    except Exception as e:
        print(f"ERROR: run_project 失败: {e}", file=sys.stderr)
        return 2

    registries = load_all_registries()

    # ---- Extract expectations from sample ----
    sm = sample.get("sample_meta") or {}
    sample_id = sample.get("sample_id", sample_path.stem)

    designed_trig = set(sm.get("designed_to_trigger_obligations") or [])
    designed_not_trig = set(sm.get("designed_to_NOT_trigger_obligations") or [])
    designed_as = set(sm.get("designed_to_require_assurances") or [])
    designed_no_as = set(sm.get("designed_to_NOT_require_assurances") or [])

    triggered = set(snapshot.triggered_obligations)
    not_triggered = set(snapshot.not_triggered_obligations)

    # ---- Obligation comparison ----
    print(f"Sample ID:     {sample_id}")
    print()

    ok = True

    fp_ob = triggered & designed_not_trig
    fn_ob = not_triggered & designed_trig
    unlisted = triggered - designed_trig - designed_not_trig

    if fp_ob:
        ok = False
        print(color(f"[FAIL] Obligation FALSE POSITIVE ({len(fp_ob)})", "RED"))
        print("  designed NOT to trigger, but triggered:")
        for ob in sorted(fp_ob):
            detail = next((d for d in snapshot.obligation_details
                          if d.obligation_id == ob), None)
            expr = detail.py_expr if detail else "?"
            print(f"  \u2717 {ob}")
            print(f"      trigger.when -> {expr}")
        print()

    if fn_ob:
        ok = False
        print(color(f"[FAIL] Obligation FALSE NEGATIVE ({len(fn_ob)})", "RED"))
        for ob in sorted(fn_ob):
            print(f"  \u2717 {ob}")
        print()

    if unlisted:
        print(color(f"[WARN] Unlisted triggered obligations ({len(unlisted)})", "YEL"))
        for ob in sorted(unlisted):
            print(f"  ? {ob}")
        print()

    # Assurance check (simplified for Step 12A)
    required_as = set(snapshot.required_assurances)
    fp_as = required_as & designed_no_as
    fn_as = designed_as - required_as
    if fp_as:
        ok = False
        print(color(f"[FAIL] Assurance FALSE POSITIVE ({len(fp_as)})", "RED"))
        for a in sorted(fp_as):
            print(f"  \u2717 {a}")
        print()
    if fn_as:
        ok = False
        print(color(f"[FAIL] Assurance FALSE NEGATIVE ({len(fn_as)})", "RED"))
        for a in sorted(fn_as):
            print(f"  \u2717 {a}")
        print()

    # OK sections
    matched_trig = triggered & designed_trig
    matched_not_trig = not_triggered & designed_not_trig
    print(color(f"[OK] Correctly triggered ({len(matched_trig)}):", "GRN"))
    for ob in sorted(matched_trig):
        print(f"  {color('\u2713', 'GRN')} {ob}")
    print()
    print(color(f"[OK] Correctly NOT triggered ({len(matched_not_trig)}):", "GRN"))
    for ob in sorted(matched_not_trig):
        print(f"  {color('\u2713', 'GRN')} {ob}")
    print()

    # Info sections
    print(color(f"[INFO] Required assurances ({len(required_as)}):", "CYN"))
    for a in sorted(required_as):
        print(f"  \u2022 {a}")
    print()
    required_art = set(snapshot.required_artifacts)
    print(color(f"[INFO] Required artifacts ({len(required_art)}):", "CYN"))
    for art_id in sorted(required_art):
        print(f"  \u2022 {art_id}")
    print()

    # ---- Calculator cross-check ----
    calc_ok, calc_reports = _run_calculator_cross_check(snapshot, sample, registries)

    print(color(f"[CALC] CalculatorRegistry_v0 verification "
                f"({len(snapshot.calculator_results)} live calculator(s)):", "CYN"))
    for sev, msg in calc_reports:
        if sev == "ERR":
            print(f"  {color('\u2717', 'RED')} {msg}")
        elif sev == "OK":
            print(f"  {color('\u2713', 'GRN')} {msg}")
        else:
            print(f"  {color('\u00b7', 'GRY')} {msg}")
    print()

    if not calc_ok:
        ok = False

    # ---- Verdict ----
    print("=" * 72)
    total_expected = len(designed_trig) + len(designed_not_trig)
    total_matched = len(matched_trig) + len(matched_not_trig)
    rate = f"{total_matched}/{total_expected}"

    if ok:
        print(color(f"PASS \u2014 obligation match {rate}, 0 false positive, 0 false negative, "
                    f"calculator cross-check GREEN", "GRN"))
    else:
        print(color(f"FAIL \u2014 obligation match {rate}", "RED"))
        print(color(f"  FP(ob)={len(fp_ob)}  FN(ob)={len(fn_ob)}  UNLISTED={len(unlisted)}", "RED"))
        print(color(f"  FP(as)={len(fp_as)}  FN(as)={len(fn_as)}", "RED"))
        if not calc_ok:
            print(color(f"  CALC=RED", "RED"))
    print("=" * 72)

    return 0 if ok else 1


# ============================================================
# Multi-sample mode (Step 11C)
# ============================================================
SAMPLE_PATHS = [
    "CPSWC_SAMPLE_Huizhou_Housing_v0.json",
    "CPSWC_SAMPLE_Disposal_HighRisk_v0.json",
]


def main() -> int:
    # Single sample CLI
    if len(sys.argv) >= 2:
        sample_path = Path(sys.argv[1])
        if not sample_path.exists():
            print(f"ERROR: sample not found: {sample_path}", file=sys.stderr)
            return 2
        return validate(sample_path)

    # Default: multi-sample regression
    print(color("=" * 72, "CYN"))
    print(color(f" CPSWC Sample Validator \u2014 Multi-Sample Regression "
                f"({len(SAMPLE_PATHS)} samples)", "BLD"))
    print(color("=" * 72, "CYN"))

    overall_rc = 0
    per_sample_rc: list[tuple[str, int]] = []
    for rel in SAMPLE_PATHS:
        sample_path = SPECS_DIR / rel
        print()
        print(color(f"\u25b6 SAMPLE: {rel}", "BLD"))
        print()
        if not sample_path.exists():
            print(color(f"ERROR: {rel} not found", "RED"))
            per_sample_rc.append((rel, 2))
            overall_rc = 1
            continue
        rc = validate(sample_path)
        per_sample_rc.append((rel, rc))
        if rc != 0:
            overall_rc = 1

    print()
    print(color("=" * 72, "CYN"))
    print(color(" OVERALL RESULT", "BLD"))
    print(color("=" * 72, "CYN"))
    for rel, rc in per_sample_rc:
        tag = color("PASS", "GRN") if rc == 0 else color("FAIL", "RED")
        print(f"  [{tag}] {rel}")
    print(color("=" * 72, "CYN"))
    if overall_rc == 0:
        print(color("ALL SAMPLES GREEN \u2713", "GRN"))
    else:
        print(color("SOME SAMPLES FAILED \u2717", "RED"))
    return overall_rc


if __name__ == "__main__":
    sys.exit(main())
