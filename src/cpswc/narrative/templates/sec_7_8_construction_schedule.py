"""
sec_7_8_construction_schedule — 7.8 施工组织与进度安排

2026 模板要求:
  明确各单项措施的施工条件、方法、工艺和施工进度。
  以月或季度为单位分区列出水保施工进度安排表。
  附施工进度安排双线横道图。

实现策略 (v1 第一轮):
  - 章级施工组织说明，不伪造细排程
  - 从 schedule facts 推导三阶段
  - 措施实施原则: 先拦后弃、先排后挖、及时恢复
  - 双线横道图引用 ENGINE_STUB
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)
from cpswc.narrative.templates.schedule_phases import derive_phases, format_phases_text


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_7_8.construction_schedule.v1",
    section_id="sec.soil_loss_prevention.construction_schedule",
    template_version="v1",
    template_author="cpswc_v1",
    normative_basis=[
        "rule.template_2026.section_7",
        "standard.gb_50433_2018",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.schedule.start_time",
        "field.fact.schedule.end_time",
        "field.fact.schedule.design_horizon_year",
    ],
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        return f"{v['value']} {v.get('unit', '')}".strip()
    return str(v)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    start = _v(facts, "field.fact.schedule.start_time")
    end = _v(facts, "field.fact.schedule.end_time")
    phases = derive_phases(facts)

    # Phase overview
    if phases:
        phase_text = format_phases_text(phases)
        phase_intro = f"项目建设总工期自{start}至{end}，分为{phase_text}三个阶段。"
    else:
        phase_intro = f"项目建设总工期自{start}至{end}。"

    p1 = NarrativeParagraph(
        text=phase_intro,
        evidence_refs=[
            "field.fact.schedule.start_time",
            "field.fact.schedule.end_time",
            "field.fact.schedule.design_horizon_year",
        ],
        source_rule_refs=["rule.template_2026.section_7"],
    )

    # Construction organization principles
    p2_parts = [
        "水土保持措施施工组织遵循以下原则："
        "（1）先拦后弃——在弃渣和取土作业前，先完成拦挡和排水设施；"
        "（2）先排后挖——在土石方开挖前，先完成截排水沟等临时排水设施；"
        "（3）及时恢复——施工结束后及时进行植被恢复和土地整治。"
    ]

    p2 = NarrativeParagraph(
        text=p2_parts[0],
        evidence_refs=[],
        source_rule_refs=[
            "rule.template_2026.section_7",
            "standard.gb_50433_2018",
        ],
    )

    # Phase-specific schedule
    p3_parts = []
    if phases:
        prep = next((p for p in phases if p.phase_id == "prep"), None)
        cons = next((p for p in phases if p.phase_id == "construction"), None)
        recov = next((p for p in phases if p.phase_id == "recovery"), None)

        if prep:
            p3_parts.append(
                f"施工准备期（{prep.start}至{prep.end}）："
                f"完成施工场地围挡、临时排水和沉砂设施，设置表土临时堆放场地。"
            )
        if cons:
            p3_parts.append(
                f"施工期（{cons.start}至{cons.end}）："
                f"随主体工程施工同步实施水土保持工程措施和临时措施，"
                f"包括截排水沟、沉砂池、临时覆盖等。"
            )
        if recov:
            p3_parts.append(
                f"自然恢复期（{recov.start}至{recov.end}）："
                f"完成植物措施（绿化种植、植被恢复），拆除临时设施，"
                f"进行场地清理和土地整治。"
            )
    else:
        p3_parts.append(
            "水土保持措施随主体工程各阶段同步实施，"
            "工程措施和临时措施在施工期完成，"
            "植物措施在工程完工后及时实施。"
        )

    p3 = NarrativeParagraph(
        text="".join(p3_parts),
        evidence_refs=[
            "field.fact.schedule.start_time",
            "field.fact.schedule.end_time",
        ],
        source_rule_refs=["rule.template_2026.section_7"],
    )

    # Gantt chart reference (ENGINE_STUB)
    p4 = NarrativeParagraph(
        text=(
            "水土保持措施施工进度与主体工程施工进度的协调关系"
            "详见施工进度安排双线横道图。"
        ),
        evidence_refs=[],
        source_rule_refs=[
            "rule.template_2026.section_7",
            "rule.t2026.dual_line_gantt_chart",
        ],
    )

    return NarrativeBlock(
        section_id="sec.soil_loss_prevention.construction_schedule",
        title="施工组织与进度安排",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2, p3, p4],
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
    )
