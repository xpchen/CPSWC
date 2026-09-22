"""
sec_8_3_monitoring_points — 8.3 点位布设与监测设施

2026 模板要求:
  明确监测点位布设位置、数量、土建设施和设备配置安装情况。

实现策略:
  - 从 county_breakdown 分区数推导点位数 (每分区 1-2 个)
  - 标准布设原则文本
  - 引用 art.figure.F_06_monitoring_points (ENGINE_STUB)
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_8_3.monitoring_points.v1",
    section_id="sec.monitoring.point_layout",
    template_version="v1",
    template_author="cpswc_v1",
    normative_basis=[
        "rule.template_2026.section_8",
        "standard.gb_50433_2018",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.land.county_breakdown",
        "field.fact.land.total_area",
    ],
)


def render(facts: dict, derived: dict, triggered: set[str],
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence("sec.monitoring.point_layout", facts, derived,
                         ledger=ledger, context=context)
    area_rv = ev.quantity("field.fact.land.total_area")
    bd_rv = ev.items("field.fact.land.county_breakdown", severity=Severity.WARN)
    breakdown = bd_rv.value if (bd_rv.is_present
                                and isinstance(bd_rv.value, list)) else []

    # Derive point count from zones
    zone_count = len(breakdown) if breakdown else 1
    # Small projects: 1 point per zone, minimum 2 total
    point_count = max(2, zone_count)

    # Point layout by zone
    if breakdown:
        zone_details = []
        for i, zone in enumerate(breakdown):
            zone_name = zone.get("type", f"分区{i+1}")
            zone_details.append(f"{zone_name}设监测点1个")
        zone_text = "，".join(zone_details)
        layout_text = (
            f"根据项目防治分区和水土流失特点，"
            f"本项目共布设水土保持监测点{point_count}个，其中{zone_text}。"
        )
    elif area_rv.is_present:
        layout_text = (
            f"根据项目防治责任范围（{area_rv.display()}）和水土流失特点，"
            f"本项目共布设水土保持监测点{point_count}个，"
            f"分布于项目主要扰动区域。"
        )
    else:
        # 既无防治分区也无责任范围面积 —— 点位数不是算出来的, 是兜底常数。
        ev.add_finding(
            "VALUE_MISSING",
            "sec.monitoring.point_layout: 既无防治分区也无责任范围面积, "
            "监测点数量无依据",
            severity=Severity.BLOCK,
            target_ref="sec.monitoring.point_layout",
            missing_input_refs=["field.fact.land.county_breakdown",
                                "field.fact.land.total_area"],
            remediation="补充防治分区或责任范围面积后确定监测点布设")
        layout_text = (
            "防治分区与责任范围面积均未提供，本节尚无法确定监测点数量与布设位置。"
        )

    p1 = NarrativeParagraph(
        text=layout_text,
        evidence_refs=[
            "field.fact.land.county_breakdown",
            "field.fact.land.total_area",
        ],
        source_rule_refs=["rule.template_2026.section_8"],
    )

    # Layout principles
    p2 = NarrativeParagraph(
        text=(
            "监测点位布设遵循以下原则："
            "（1）在各防治分区的代表性位置设置监测点，"
            "能够反映该分区的水土流失状况和防治效果；"
            "（2）重点关注扰动面积较大、地形变化显著的区域；"
            "（3）监测点应便于观测和维护，避免施工干扰。"
        ),
        evidence_refs=[],
        source_rule_refs=[
            "rule.template_2026.section_8",
            "standard.gb_50433_2018",
        ],
    )

    # Facilities and figure reference
    p3 = NarrativeParagraph(
        text=(
            "各监测点配备必要的监测设施，包括固定标桩、量测标尺等。"
            "监测点位布设详见水土保持监测点布置图。"
        ),
        evidence_refs=[],
        source_rule_refs=["rule.template_2026.section_8"],
    )

    return NarrativeBlock(
        section_id="sec.monitoring.point_layout",
        title="点位布设与监测设施",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2, p3],
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
        quality_findings=ev.findings,
    )
