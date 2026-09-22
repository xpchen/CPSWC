"""
sec_6_soil_loss — 第6章 水土流失分析与预测 narrative templates

两个子节:
  sec.soil_loss_analysis.current_state    — 6.1 水土流失现状
  sec.soil_loss_analysis.prediction_result — 6.2 水土流失预测

消费 facts:
  natural.soil_erosion_type / intensity / original_erosion_modulus / allowable_loss
  prediction.total_loss / new_loss / reducible_loss
  land.total_area

B 批 P0-04 改造 (任务 B-T2):

  本节的风险最高, 因为它**把计算结果当成预测成果直接写进正文**, 而
  `prediction_engine` 的扰动模数在没有项目覆盖时取自内建"典型值"矩阵
  (`_DEFAULT_DISTURBED` / `_MODULUS_MATRIX`, 注释里写着"类比: …典型值")。
  这正是 P0_BASELINE 的 D09 与验收项 I05 所指的"演示假设流入正式成果"。

  改造内容:
    1. 取值统一经 BuildContext, 缺失不再显示成"—"。
    2. 预测结果照常给出, 但**逐段标明有多少分区用的是默认典型模数**,
       并登记 DEMO_ASSUMPTION; 全部使用默认值时明确说"本轮预测量不可用于
       正式成果"。
    3. 类比工程可比性结论 ("两项目基本相同，具有较强可比性") 是专业判断,
       改走 judgment() —— 它决定了整章预测取值是否成立, 不能由 registry
       里有一条记录就自动成立。
"""
from __future__ import annotations

from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity, Stage

SEC_CURRENT = "sec.soil_loss_analysis.current_state"
SEC_PREDICTION = "sec.soil_loss_analysis.prediction_result"


# ── sec.soil_loss_analysis.current_state ─────────────────────

SPEC_CURRENT = NarrativeTemplateSpec(
    template_id="nt.sec_6_1.current_state.v2",
    section_id=SEC_CURRENT,
    template_version="v2",
    template_author="cpswc_p0_04",
    normative_basis=[
        "rule.template_2026.section_6",
        "standard.gb_50433_2018.section_6",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.soil_erosion_type",
        "field.fact.natural.soil_erosion_intensity",
        "field.fact.natural.original_erosion_modulus",
        "field.fact.natural.allowable_loss",
        "field.fact.land.total_area",
    ],
)


def render_current_state(facts: dict, derived: dict, triggered: set[str],
                         ledger=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence(SEC_CURRENT, facts, derived, ledger=ledger,
                         context=context)

    erosion_type = ev.text("field.fact.natural.soil_erosion_type")
    intensity = ev.text("field.fact.natural.soil_erosion_intensity")
    modulus = ev.quantity("field.fact.natural.original_erosion_modulus")
    allowable = ev.quantity("field.fact.natural.allowable_loss")
    total_area = ev.quantity("field.fact.land.total_area")

    values = [erosion_type, intensity, modulus, allowable, total_area]
    if ev.all_present(*values):
        para = NarrativeParagraph(
            text=(f"项目区现状土壤侵蚀类型以{erosion_type.display()}为主，"
                  f"侵蚀强度等级为{intensity.display()}。"
                  f"原生土壤侵蚀模数{modulus.display()}，"
                  f"容许土壤流失量{allowable.display()}。"
                  f"项目总占地{total_area.display()}。"),
            evidence_refs=[v.field_id for v in values],
            source_rule_refs=["rule.template_2026.section_6",
                              "standard.gb_50433_2018.section_6"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.soil_loss_analysis.current_state.baseline",
        )
    else:
        para = ev.gap_paragraph(
            *values,
            lead="水土流失现状资料不完整，无法描述项目区侵蚀本底",
            source_rule_refs=["rule.template_2026.section_6"],
            paragraph_id="narr.soil_loss_analysis.current_state.baseline",
        )

    return NarrativeBlock(
        section_id=SEC_CURRENT,
        title="水土流失现状",
        render_status=RenderStatus.FULL,
        paragraphs=[para],
        variant_id="default",
        template_id=SPEC_CURRENT.template_id,
        template_version=SPEC_CURRENT.template_version,
        normative_basis=SPEC_CURRENT.normative_basis,
        quality_findings=ev.findings,
    )


# ── sec.soil_loss_analysis.prediction_result ─────────────────

SPEC_PREDICTION = NarrativeTemplateSpec(
    template_id="nt.sec_6_2.prediction_result.v4",
    section_id=SEC_PREDICTION,
    template_version="v4",
    template_author="cpswc_p0_04",
    normative_basis=[
        "rule.template_2026.section_6",
        "standard.gb_50433_2018.section_6",
        "registry.analog_project_v0",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.natural.original_erosion_modulus",
        "field.fact.land.county_breakdown",
        "field.fact.land.total_area",
        "field.fact.schedule.start_time",
        "field.fact.schedule.end_time",
        "field.fact.prediction.analog_project_ref",
    ],
)


def _load_analog_project(analog_id: str) -> dict | None:
    """从 AnalogProjectRegistry_v0 取出指定 id 的类比工程档案; 找不到返回 None."""
    if not analog_id:
        return None
    import yaml
    from cpswc.paths import REGISTRIES_DIR

    reg_path = REGISTRIES_DIR / "AnalogProjectRegistry_v0.yaml"
    if not reg_path.exists():
        return None
    with reg_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for ap in data.get("analog_projects") or []:
        if isinstance(ap, dict) and ap.get("id") == analog_id:
            return ap
    return None


def render_prediction(facts: dict, derived: dict, triggered: set[str],
                      ledger=None, context=None, **kwargs) -> NarrativeBlock:
    from cpswc.prediction_engine import compute_prediction

    ev = SectionEvidence(SEC_PREDICTION, facts, derived, ledger=ledger,
                         context=context)

    bg_modulus = ev.quantity("field.fact.natural.original_erosion_modulus")
    total_area = ev.quantity("field.fact.land.total_area")

    result = compute_prediction(facts)
    paragraphs: list[NarrativeParagraph] = []

    # ── 模数来源盘点 ──
    # prediction_engine 已经给每个分区标了 modulus_source。内建矩阵里的值是
    # "类比: …典型值", 不是本项目实测 —— 这一点必须让读者看见。
    default_zones = [r for r in result.zone_results
                     if r.modulus_source != "project_override"]
    override_zones = [r for r in result.zone_results
                      if r.modulus_source == "project_override"]
    all_default = bool(result.zone_results) and not override_zones

    if default_zones:
        ev.add_finding(
            "DEMO_ASSUMPTION",
            (f"{SEC_PREDICTION}: {len(default_zones)}/{len(result.zone_results)} "
             f"个预测单元使用内建默认扰动模数（类比典型值），非本项目实测或专项类比"),
            severity=Severity.BLOCK,
            target_ref=SEC_PREDICTION,
            remediation="按项目实际情况给出分区扰动模数, 或补充可核验的类比工程实测值",
            stage=Stage.EVALUATION,
        )

    # ── P1: 方法与范围 ──
    unit_count = len({r.zone_id for r in result.zone_results})
    analog_ref = facts.get("field.fact.prediction.analog_project_ref")
    analog = _load_analog_project(analog_ref) if isinstance(analog_ref, str) else None

    if analog:
        method_clause = (
            f"本项目采用类比分析法进行水土流失预测，"
            f"经筛选确定“{analog.get('name', analog_ref)}”"
            f"（{analog.get('location', '所在地未填')}）为类比工程，"
            f"数据来源：{analog.get('citation_source', '来源未填')}。")
        method_evidence = [
            "field.fact.natural.original_erosion_modulus",
            "field.fact.land.total_area",
            "field.fact.land.county_breakdown",
            "field.fact.prediction.analog_project_ref",
            "registry.analog_project_v0",
        ]
    else:
        method_clause = (
            "本项目预测尚未实名引用类比工程（AnalogProjectRegistry 绑定缺失），"
            "预测取值的类比依据不完整。")
        method_evidence = [
            "field.fact.natural.original_erosion_modulus",
            "field.fact.land.total_area",
            "field.fact.land.county_breakdown",
        ]
        ev.add_finding(
            "SOURCE_UNVERIFIED",
            f"{SEC_PREDICTION}: 未实名引用类比工程, 预测取值缺少可核验依据",
            severity=Severity.BLOCK,
            target_ref="field.fact.prediction.analog_project_ref",
            remediation="在 AnalogProjectRegistry 中登记类比工程并绑定",
            stage=Stage.INPUT,
        )

    scope_clause = (f"预测范围为项目防治责任范围（{total_area.display()}），"
                    if total_area.is_present else "预测范围面积缺失，")
    modulus_clause = (f"原地貌土壤侵蚀模数{bg_modulus.display()}。"
                      if bg_modulus.is_present else "原地貌土壤侵蚀模数缺失。")

    paragraphs.append(NarrativeParagraph(
        text=(f"{method_clause}{scope_clause}"
              f"共划分{unit_count}个预测单元。{modulus_clause}"),
        evidence_refs=method_evidence,
        source_rule_refs=["rule.template_2026.section_6"],
        assertion_class=AssertionClass.FACT_RESTATEMENT,
        paragraph_id="narr.soil_loss_analysis.prediction_result.method",
    ))

    # ── P1b: 类比工程可比性 ── 这是专业判断, 不是 registry 有记录就成立
    if analog:
        b = analog.get("comparability_baseline") or {}
        comp_parts = []
        if b.get("geographic"):
            comp_parts.append(f"地理位置同属{b['geographic']}")
        if b.get("climate_zone"):
            rain = b.get("annual_rainfall_mm")
            rain_clause = f"，多年平均降雨量约 {rain}mm" if rain else ""
            comp_parts.append(f"气候同为{b['climate_zone']}{rain_clause}")
        if b.get("soil_type"):
            comp_parts.append(f"土壤同以{b['soil_type']}为主")
        if b.get("vegetation_desc"):
            comp_parts.append(f"植被均为{b['vegetation_desc']}")
        if b.get("terrain_type"):
            comp_parts.append(f"地形地貌相近（类比工程为{b['terrain_type']}）")
        if b.get("soil_conservation_status"):
            comp_parts.append(f"水土保持现状{b['soil_conservation_status']}")
        if comp_parts:
            paragraphs.append(NarrativeParagraph(
                text="类比工程与本项目的对照情况：" + "；".join(comp_parts) + "。",
                evidence_refs=["field.fact.prediction.analog_project_ref",
                               "registry.analog_project_v0",
                               "art.table.prediction.analog_comparison"],
                source_rule_refs=["rule.template_2026.section_6"],
                assertion_class=AssertionClass.FACT_RESTATEMENT,
                paragraph_id="narr.soil_loss_analysis.prediction_result.analog_facts",
            ))
            paragraphs.append(ev.judgment(
                "两项目基本相同，具有较强可比性，其各扰动地表分区年均土壤侵蚀模数"
                "实测值可用于本项目预测取值。",
                target_ref=f"{SEC_PREDICTION}.comparability",
                pending_text=(
                    "上述对照仅为登记信息的罗列。类比工程与本项目是否具有足够可比性、"
                    "其实测模数能否用于本项目预测取值，须由水土保持工程师逐项论证"
                    "并复核确认；确认前不作可比性结论，相应预测取值的依据不完整。"),
                evidence_refs=["field.fact.prediction.analog_project_ref",
                               "registry.analog_project_v0"],
                source_rule_refs=["rule.template_2026.section_6"],
                paragraph_id="narr.soil_loss_analysis.prediction_result.comparability",
                remediation="逐项论证六维度可比性并录入复核记录",
            ))

    # ── P2: 结果 ── 给数, 同时给出这些数的可靠性前提
    if result.zone_results:
        text = (f"按上述方法计算，项目建设期及自然恢复期水土流失总量为 "
                f"{result.total_loss_t:.2f} t，其中新增水土流失量 "
                f"{result.total_new_loss_t:.2f} t。")
        summary_c = result.summary_by_period.get("施工期", {})
        summary_r = result.summary_by_period.get("自然恢复期", {})
        if summary_c:
            text += f"施工期新增流失量 {summary_c.get('new_loss_t', 0):.2f} t；"
        if summary_r:
            text += f"自然恢复期新增流失量 {summary_r.get('new_loss_t', 0):.2f} t。"
        if all_default:
            text += ("以上结果的全部预测单元均采用内建默认扰动模数（类比典型值），"
                     "非本项目实测或经确认的类比取值，**不得作为正式成果使用**。")
        elif default_zones:
            text += (f"其中 {len(default_zones)} 个预测单元采用内建默认扰动模数"
                     f"（类比典型值），相应结果待补充项目取值后重算。")
        paragraphs.append(NarrativeParagraph(
            text=text,
            evidence_refs=["art.table.prediction.result",
                           "art.table.prediction.summary"],
            source_rule_refs=["rule.template_2026.section_6"],
            assertion_class=AssertionClass.ARITHMETIC,
            paragraph_id="narr.soil_loss_analysis.prediction_result.totals",
        ))
    else:
        ev.add_finding(
            "VALUE_MISSING",
            f"{SEC_PREDICTION}: 无可用的预测单元, 未能产出预测结果",
            severity=Severity.BLOCK,
            target_ref=SEC_PREDICTION,
            remediation="补充防治分区与占地面积后重算",
            stage=Stage.EVALUATION,
        )
        paragraphs.append(NarrativeParagraph(
            text=("本轮未能划分出任何预测单元，因而没有水土流失预测结果。"
                  "需先补齐防治分区与各分区占地面积。"),
            evidence_refs=["field.fact.land.total_area", SEC_PREDICTION],
            source_rule_refs=["rule.template_2026.section_6"],
            assertion_class=AssertionClass.GAP_STATEMENT,
            paragraph_id="narr.soil_loss_analysis.prediction_result.totals",
        ))

    # ── P3: 重点区域 ──
    if result.zone_results:
        max_zone = max((r for r in result.zone_results if r.period == "施工期"),
                       key=lambda r: r.new_loss_t, default=None)
        if max_zone and max_zone.new_loss_t > 0:
            src = ("（该分区模数取自内建默认值）"
                   if max_zone.modulus_source != "project_override" else "")
            paragraphs.append(NarrativeParagraph(
                text=(f"按当前取值，施工期新增流失量最大的是{max_zone.zone_type}，"
                      f"为 {max_zone.new_loss_t:.2f} t{src}。"
                      f"详见水土流失预测成果表和预测汇总表。"),
                evidence_refs=["art.table.prediction.result"],
                source_rule_refs=["rule.template_2026.section_6"],
                assertion_class=AssertionClass.ARITHMETIC,
                paragraph_id="narr.soil_loss_analysis.prediction_result.hotspot",
            ))

    return NarrativeBlock(
        section_id=SEC_PREDICTION,
        title="水土流失预测",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=SPEC_PREDICTION.template_id,
        template_version=SPEC_PREDICTION.template_version,
        normative_basis=SPEC_PREDICTION.normative_basis,
        quality_findings=ev.findings,
    )
