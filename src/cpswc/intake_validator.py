#!/usr/bin/env python3
"""
intake_validator.py — CPSWC v0 项目录入校验器

功能:
  1. 读取 YAML 或 JSON 格式的 intake 文件
  2. 转换为标准 facts.json 格式
  3. 校验必填/推荐/可选字段
  4. 输出缺失清单 + 影响报告 (哪些章节/表/计算器受影响)

使用方式:
  python -m cpswc.intake_validator templates/project_intake_minimal.yaml
  python -m cpswc.intake_validator examples/intake_shiwei_v0/intake.yaml
  python -m cpswc.intake_validator samples/shiwei_logistics_v0.json --check-only
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any


# ============================================================
# Field definitions: key, priority, affected sections
# ============================================================

@dataclass
class FieldDef:
    key: str                    # e.g. "field.fact.project.name"
    intake_path: str            # e.g. "project.name"
    priority: str               # "required" | "recommended" | "optional"
    affected: list[str]         # affected section/table/calculator IDs
    description: str = ""


FIELD_DEFS: list[FieldDef] = [
    # ── Pack A: 项目基本信息 ──
    FieldDef("field.fact.project.name", "project.name", "required",
             ["sec.overview", "sec.overview.project_basic", "sec.overview.spec_sheet_end", "sec.conclusion"],
             "项目名称"),
    FieldDef("field.fact.project.code", "project.code", "optional",
             ["sec.overview.project_basic"], "项目代码"),
    FieldDef("field.fact.project.industry_category", "project.industry_category", "required",
             ["sec.overview.project_basic"], "行业类别"),
    FieldDef("field.fact.project.nature", "project.nature", "required",
             ["sec.overview.project_basic"], "建设性质"),
    FieldDef("field.fact.project.builder", "project.builder", "recommended",
             ["sec.overview.spec_sheet_end"], "建设单位"),
    FieldDef("field.fact.project.compiler", "project.compiler", "recommended",
             ["sec.overview.spec_sheet_end"], "编制单位"),
    FieldDef("field.fact.location.province_list", "location.province_list", "required",
             ["sec.overview.project_basic", "sec.investment_estimation.compensation_fee"], "省份"),
    FieldDef("field.fact.location.prefecture_list", "location.prefecture_list", "required",
             ["sec.overview.project_basic"], "地市"),
    FieldDef("field.fact.location.county_list", "location.county_list", "recommended",
             ["sec.overview.spec_sheet_end"], "县区"),
    FieldDef("field.fact.location.river_basin_agency", "location.river_basin_agency", "optional",
             ["sec.overview.spec_sheet_end"], "流域管理机构"),
    FieldDef("field.fact.investment.total_investment", "investment.total_investment", "required",
             ["sec.overview", "sec.overview.project_basic", "sec.overview.spec_sheet_end"], "总投资"),
    FieldDef("field.fact.investment.civil_investment", "investment.civil_investment", "required",
             ["sec.overview.project_basic", "sec.overview.spec_sheet_end"], "土建投资"),
    FieldDef("field.fact.schedule.start_time", "schedule.start_time", "required",
             ["sec.overview.project_basic", "sec.project_overview.progress"], "动工时间"),
    FieldDef("field.fact.schedule.end_time", "schedule.end_time", "required",
             ["sec.overview.project_basic", "sec.project_overview.progress",
              "sec.soil_loss_prevention.design_horizon"], "完工时间"),
    FieldDef("field.fact.schedule.design_horizon_year", "schedule.design_horizon_year", "recommended",
             ["sec.soil_loss_prevention.design_horizon"], "设计水平年"),

    # ── Pack B: 占地 / 土石方 / 表土 ──
    FieldDef("field.fact.land.total_area", "land.total_area", "required",
             ["sec.project_overview.land_occupation", "sec.soil_loss_prevention.responsibility_range",
              "cal.compensation.fee", "art.table.total_land_occupation"], "总占地面积"),
    FieldDef("field.fact.land.permanent_area", "land.permanent_area", "required",
             ["sec.project_overview.land_occupation", "cal.compensation.fee"], "永久占地"),
    FieldDef("field.fact.land.temporary_area", "land.temporary_area", "required",
             ["sec.project_overview.land_occupation", "cal.compensation.fee"], "临时占地"),
    FieldDef("field.fact.land.county_breakdown", "land.county_breakdown", "recommended",
             ["art.table.total_land_occupation", "sec.overview.spec_sheet_end",
              "sec.soil_loss_prevention.responsibility_range"], "项目组成分区"),
    FieldDef("field.fact.earthwork.excavation", "earthwork.excavation", "required",
             ["sec.evaluation.earthwork_balance", "sec.project_overview.earthwork_balance",
              "art.table.earthwork_balance"], "挖方"),
    FieldDef("field.fact.earthwork.fill", "earthwork.fill", "required",
             ["sec.evaluation.earthwork_balance", "sec.project_overview.earthwork_balance"], "填方"),
    FieldDef("field.fact.earthwork.self_reuse", "earthwork.self_reuse", "recommended",
             ["sec.evaluation.earthwork_balance", "sec.project_overview.earthwork_balance"], "场内自用"),
    FieldDef("field.fact.earthwork.comprehensive_reuse", "earthwork.comprehensive_reuse", "recommended",
             ["sec.evaluation.earthwork_balance"], "综合利用"),
    FieldDef("field.fact.earthwork.spoil", "earthwork.spoil", "required",
             ["sec.disposal_site", "sec.overview.spec_sheet_end"], "弃方"),
    FieldDef("field.fact.earthwork.borrow", "earthwork.borrow", "recommended",
             ["sec.evaluation.earthwork_balance", "sec.overview.spec_sheet_end"], "借方"),
    FieldDef("field.fact.earthwork.borrow_source_type", "earthwork.borrow_source_type", "optional",
             ["sec.evaluation.earthwork_balance"], "借方来源"),
    FieldDef("field.fact.topsoil.stripable_area", "topsoil.stripable_area", "recommended",
             ["sec.topsoil.stripping"], "可剥离表土面积"),
    FieldDef("field.fact.topsoil.stripable_volume", "topsoil.stripable_volume", "recommended",
             ["sec.topsoil.stripping", "sec.topsoil.balance", "sec.overview.spec_sheet_end"], "可剥离表土量"),
    FieldDef("field.fact.topsoil.excavation", "topsoil.excavation", "recommended",
             ["sec.topsoil.balance"], "表土挖方"),
    FieldDef("field.fact.topsoil.fill", "topsoil.fill", "recommended",
             ["sec.topsoil.balance"], "表土回覆量"),

    # ── Pack C: 自然条件 / 侵蚀预测 ──
    FieldDef("field.fact.natural.climate_type", "natural.climate_type", "recommended",
             ["sec.project_overview.climate"], "气候类型"),
    FieldDef("field.fact.natural.landform_type", "natural.landform_type", "recommended",
             ["sec.project_overview.climate"], "地貌类型"),
    FieldDef("field.fact.natural.soil_erosion_type", "natural.soil_erosion_type", "recommended",
             ["sec.soil_loss_analysis.current_state", "sec.evaluation"], "侵蚀类型"),
    FieldDef("field.fact.natural.soil_erosion_intensity", "natural.soil_erosion_intensity", "recommended",
             ["sec.soil_loss_analysis.current_state"], "侵蚀强度"),
    FieldDef("field.fact.natural.original_erosion_modulus", "natural.original_erosion_modulus", "recommended",
             ["sec.soil_loss_analysis.current_state", "sec.overview.spec_sheet_end"], "原地貌侵蚀模数"),
    FieldDef("field.fact.natural.allowable_loss", "natural.allowable_loss", "recommended",
             ["sec.soil_loss_analysis.current_state", "sec.overview.spec_sheet_end"], "容许土壤流失量"),
    FieldDef("field.fact.natural.water_soil_zoning", "natural.water_soil_zoning", "required",
             ["sec.project_overview.water_soil_zoning", "sec.soil_loss_prevention.targets",
              "cal.target.weighted_comprehensive"], "水土保持区划"),
    FieldDef("field.fact.natural.key_prevention_treatment_areas", "natural.key_prevention_treatment_areas", "optional",
             ["sec.project_overview.water_soil_zoning"], "重点防治区"),
    FieldDef("field.fact.natural.other_sensitive_areas", "natural.other_sensitive_areas", "optional",
             ["sec.project_overview.sensitive_areas"], "其他敏感区"),
    FieldDef("field.fact.prediction.total_loss", "prediction.total_loss", "recommended",
             ["sec.soil_loss_analysis.prediction_result", "sec.soil_loss_prevention.benefit_analysis"], "预测流失总量"),
    FieldDef("field.fact.prediction.new_loss", "prediction.new_loss", "recommended",
             ["sec.soil_loss_analysis.prediction_result", "sec.overview",
              "sec.soil_loss_prevention.benefit_analysis"], "新增流失量"),
    FieldDef("field.fact.prediction.reducible_loss", "prediction.reducible_loss", "recommended",
             ["sec.soil_loss_prevention.benefit_analysis"], "可治理流失量"),

    # ── Pack D: 防治标准 / 弃渣 / 法规 ──
    FieldDef("field.fact.prevention.control_standard_level", "prevention.control_standard_level", "recommended",
             ["sec.soil_loss_prevention.targets", "sec.conclusion"], "防治标准等级"),
    FieldDef("field.fact.disposal_site.level_assessment", "disposal_site.level_assessment", "optional",
             ["sec.conclusion", "cal.disposal_site.level_assessment"], "弃渣场级别评定"),
    FieldDef("field.fact.disposal_site.failure_analysis_required", "disposal_site.failure_analysis_required", "optional",
             [], "是否需要破坏分析"),
    FieldDef("field.fact.regulatory.compensation_fee_rate", "regulatory.compensation_fee_rate", "recommended",
             ["sec.investment_estimation.compensation_fee", "cal.compensation.fee"], "补偿费费率"),
]


# ============================================================
# YAML → facts conversion
# ============================================================

def _resolve_path(data: dict, path: str) -> Any:
    """Resolve dotted path like 'project.name' in nested dict."""
    parts = path.split(".")
    current = data
    for p in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(p)
        if current is None:
            return None
    return current


def _is_empty(value: Any) -> bool:
    """Check if a value is effectively empty."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    if isinstance(value, dict):
        # Quantity with no value
        if "value" in value and value["value"] is None:
            return True
        if "value" in value and value["value"] == "":
            return True
        if len(value) == 0:
            return True
    return False


def intake_to_facts(intake: dict) -> dict:
    """Convert intake YAML structure to flat facts dict."""
    facts = {}
    for fd in FIELD_DEFS:
        val = _resolve_path(intake, fd.intake_path)
        if not _is_empty(val):
            facts[fd.key] = val
    return facts


# ============================================================
# Validation
# ============================================================

@dataclass
class ValidationIssue:
    field_key: str
    intake_path: str
    priority: str
    description: str
    issue_type: str             # "missing" | "type_error"
    affected_sections: list[str]
    message: str = ""


@dataclass
class ValidationReport:
    total_fields: int
    provided_fields: int
    missing_required: list[ValidationIssue]
    missing_recommended: list[ValidationIssue]
    missing_optional: list[ValidationIssue]
    type_errors: list[ValidationIssue]
    affected_sections: dict[str, list[str]]  # section_id → [missing field descriptions]
    affected_calculators: list[str]
    can_run_pipeline: bool


def validate_intake(intake: dict) -> ValidationReport:
    """Validate intake data and produce a detailed report."""
    missing_req = []
    missing_rec = []
    missing_opt = []
    type_errors = []
    provided = 0

    for fd in FIELD_DEFS:
        val = _resolve_path(intake, fd.intake_path)
        if _is_empty(val):
            issue = ValidationIssue(
                field_key=fd.key,
                intake_path=fd.intake_path,
                priority=fd.priority,
                description=fd.description,
                issue_type="missing",
                affected_sections=fd.affected,
                message=f"缺失: {fd.description} ({fd.intake_path})",
            )
            if fd.priority == "required":
                missing_req.append(issue)
            elif fd.priority == "recommended":
                missing_rec.append(issue)
            else:
                missing_opt.append(issue)
        else:
            provided += 1
            # Type check for Quantity fields
            if fd.key.endswith(("_area", "_volume", "_investment", "_loss", "_modulus",
                                "_rate", "excavation", "fill", "spoil", "borrow",
                                "self_reuse", "comprehensive_reuse")):
                if isinstance(val, dict) and "value" in val:
                    v = val.get("value")
                    if v is not None and not isinstance(v, (int, float)):
                        type_errors.append(ValidationIssue(
                            field_key=fd.key,
                            intake_path=fd.intake_path,
                            priority=fd.priority,
                            description=fd.description,
                            issue_type="type_error",
                            affected_sections=fd.affected,
                            message=f"类型错误: {fd.description} value 应为数值，实际为 {type(v).__name__}",
                        ))

    # Compute affected sections
    all_missing = missing_req + missing_rec
    affected_map: dict[str, list[str]] = {}
    for issue in all_missing:
        for sec in issue.affected_sections:
            affected_map.setdefault(sec, []).append(issue.description)

    # Compute affected calculators
    calc_affected = []
    missing_keys = {i.field_key for i in missing_req + missing_rec}
    if "field.fact.land.total_area" in missing_keys or "field.fact.regulatory.compensation_fee_rate" in missing_keys:
        calc_affected.append("cal.compensation.fee")
    if "field.fact.natural.water_soil_zoning" in missing_keys:
        calc_affected.append("cal.target.weighted_comprehensive")

    can_run = len(missing_req) == 0 and len(type_errors) == 0

    return ValidationReport(
        total_fields=len(FIELD_DEFS),
        provided_fields=provided,
        missing_required=missing_req,
        missing_recommended=missing_rec,
        missing_optional=missing_opt,
        type_errors=type_errors,
        affected_sections=affected_map,
        affected_calculators=calc_affected,
        can_run_pipeline=can_run,
    )


# ============================================================
# Output formatting
# ============================================================

_PRIORITY_LABELS = {"required": "必填", "recommended": "推荐", "optional": "可选"}
_PRIORITY_ICONS = {"required": "!!!", "recommended": " ! ", "optional": "   "}


def format_report(report: ValidationReport) -> str:
    """Format validation report as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("CPSWC 项目录入校验报告")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    lines.append(f"字段总数: {report.total_fields}")
    lines.append(f"已提供:   {report.provided_fields}")
    lines.append(f"缺失必填: {len(report.missing_required)}")
    lines.append(f"缺失推荐: {len(report.missing_recommended)}")
    lines.append(f"缺失可选: {len(report.missing_optional)}")
    lines.append(f"类型错误: {len(report.type_errors)}")
    lines.append("")

    if report.can_run_pipeline:
        lines.append(">>> 管线状态: 可运行 (必填字段完整)")
    else:
        lines.append(">>> 管线状态: 不可运行 (缺少必填字段或存在类型错误)")
    lines.append("")

    # Missing required
    if report.missing_required:
        lines.append("-" * 40)
        lines.append("缺失必填字段 (必须补齐)")
        lines.append("-" * 40)
        for issue in report.missing_required:
            lines.append(f"  [!!!] {issue.description}")
            lines.append(f"        路径: {issue.intake_path}")
            lines.append(f"        影响: {', '.join(issue.affected_sections[:3])}")
        lines.append("")

    # Missing recommended
    if report.missing_recommended:
        lines.append("-" * 40)
        lines.append("缺失推荐字段 (建议补充)")
        lines.append("-" * 40)
        for issue in report.missing_recommended:
            lines.append(f"  [ ! ] {issue.description}")
            lines.append(f"        路径: {issue.intake_path}")
            lines.append(f"        影响: {', '.join(issue.affected_sections[:3])}")
        lines.append("")

    # Type errors
    if report.type_errors:
        lines.append("-" * 40)
        lines.append("类型错误")
        lines.append("-" * 40)
        for issue in report.type_errors:
            lines.append(f"  [ERR] {issue.message}")
        lines.append("")

    # Affected sections
    if report.affected_sections:
        lines.append("-" * 40)
        lines.append("受影响的章节/表格")
        lines.append("-" * 40)
        for sec_id, fields in sorted(report.affected_sections.items()):
            lines.append(f"  {sec_id}")
            lines.append(f"    缺: {', '.join(fields)}")
        lines.append("")

    # Affected calculators
    if report.affected_calculators:
        lines.append("-" * 40)
        lines.append("受影响的计算器")
        lines.append("-" * 40)
        for calc in report.affected_calculators:
            lines.append(f"  {calc}")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# Facts JSON output
# ============================================================

def build_sample_json(intake: dict, meta: dict | None = None) -> dict:
    """Build a complete CPSWC sample JSON from intake data."""
    facts = intake_to_facts(intake)
    sample = {
        "$schema": "CPSWC_SAMPLE_v0",
        "sample_id": f"sample.intake_{meta.get('project_id', 'unknown') if meta else 'unknown'}",
        "sample_meta": meta or {
            "purpose": "从录入模板生成",
            "generated_at": "",
        },
        "facts": facts,
    }
    return sample


# ============================================================
# CLI
# ============================================================

def _load_input(path: Path) -> dict:
    """Load YAML or JSON input file."""
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        import yaml
        return yaml.safe_load(text) or {}
    else:
        data = json.loads(text)
        # If it's a CPSWC sample JSON, extract facts and flatten
        if "facts" in data:
            return _facts_to_intake(data["facts"])
        return data


def _facts_to_intake(facts: dict) -> dict:
    """Convert flat facts dict back to intake structure for validation."""
    intake: dict = {}
    for fd in FIELD_DEFS:
        val = facts.get(fd.key)
        if val is not None:
            parts = fd.intake_path.split(".")
            current = intake
            for p in parts[:-1]:
                current = current.setdefault(p, {})
            current[parts[-1]] = val
    return intake


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m cpswc.intake_validator <intake.yaml|facts.json> [--check-only] [--output facts.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    check_only = "--check-only" in sys.argv
    output_idx = sys.argv.index("--output") if "--output" in sys.argv else -1
    output_path = Path(sys.argv[output_idx + 1]) if output_idx >= 0 else None

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    intake = _load_input(input_path)
    report = validate_intake(intake)
    print(format_report(report))

    if not check_only and output_path and report.can_run_pipeline:
        sample = build_sample_json(intake)
        output_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Facts JSON written to: {output_path}")

    sys.exit(0 if report.can_run_pipeline else 1)


if __name__ == "__main__":
    main()
