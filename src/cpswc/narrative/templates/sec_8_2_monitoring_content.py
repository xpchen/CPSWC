"""
sec_8_2_monitoring_content — 8.2 监测内容、方法与频次 + 8.4 实施条件(合并)

2026 模板要求:
  8.2.1 明确监测内容。3级及以上弃渣场应开展稳定监测。
  8.2.2 针对不同监测内容和重点，明确具体监测方法与频次。
        3级及以上弃渣场应当采取视频监控方式。
  8.4   根据监测内容、方法，提出监测人员、设备，明确监测成果要求。

实现策略:
  - 代码内建监测内容矩阵 (分区类型 → 内容/方法/频次)
  - 从 county_breakdown 提取分区列表
  - 弃渣场条件分支由 obligation 触发状态驱动
  - 8.4 实施条件并入尾段
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_8_2.monitoring_content.v1",
    section_id="sec.monitoring.contents_methods_frequency",
    template_version="v1",
    template_author="cpswc_v1",
    normative_basis=[
        "rule.template_2026.section_8",
        "standard.gb_50433_2018",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.land.county_breakdown",
        "field.fact.earthwork.spoil",
    ],
)


# ============================================================
# 监测内容矩阵 (标准规范内容, 非项目级数据)
# ============================================================
# key = zone type keyword, value = (监测内容, 方法, 施工期频次, 恢复期频次)
_MONITORING_MATRIX: list[tuple[str, str, str, str, str]] = [
    # (zone_match, content, method, freq_construction, freq_recovery)
    ("主体", "扰动面积、地表径流、水土流失状况", "现场量测、定点照相", "月1次", "季1次"),
    ("建筑", "扰动面积、地表径流、水土流失状况", "现场量测、定点照相", "月1次", "季1次"),
    ("道路", "边坡稳定、排水设施完好性", "现场巡查、定点照相", "月1次", "季1次"),
    ("广场", "地表径流、硬化完好性", "现场巡查", "月1次", "—"),
    ("绿化", "植被恢复、覆盖度", "样方调查、定点照相", "—", "季1次"),
    ("景观", "植被恢复、覆盖度", "样方调查、定点照相", "—", "季1次"),
    ("临时堆土", "堆体稳定、拦挡完好性、苫盖情况", "现场巡查", "月2次", "—"),
    ("施工生产", "场地排水、临时覆盖", "现场巡查", "月1次", "—"),
    ("弃渣", "堆渣稳定性、拦挡完好性", "现场量测、位移观测", "月2次", "季1次"),
]

# Default for unmatched zones
_DEFAULT_MONITORING = ("扰动面积、水土流失状况", "现场量测、定点照相", "月1次", "季1次")


def _match_zone(zone_type: str) -> tuple[str, str, str, str]:
    """Match a zone type to monitoring content/method/frequency."""
    for keyword, content, method, freq_c, freq_r in _MONITORING_MATRIX:
        if keyword in zone_type:
            return content, method, freq_c, freq_r
    return _DEFAULT_MONITORING


def _v(facts: dict, key: str) -> float:
    v = facts.get(key)
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    if isinstance(v, (int, float)):
        return v
    return 0


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    breakdown = facts.get("field.fact.land.county_breakdown") or []
    spoil = _v(facts, "field.fact.earthwork.spoil")
    has_stability_monitoring = "ob.disposal_site.stability_monitoring" in triggered
    has_video_surveillance = "ob.disposal_site.video_surveillance" in triggered

    paragraphs = []

    # ---- 8.2.1 Monitoring content by zone ----
    if breakdown:
        zone_lines = []
        for zone in breakdown:
            zone_type = zone.get("type", "未知分区")
            content, method, freq_c, freq_r = _match_zone(zone_type)
            freq_parts = []
            if freq_c and freq_c != "—":
                freq_parts.append(f"施工期{freq_c}")
            if freq_r and freq_r != "—":
                freq_parts.append(f"恢复期{freq_r}")
            freq_text = "，".join(freq_parts) if freq_parts else "按需"
            zone_lines.append(
                f"（{len(zone_lines)+1}）{zone_type}：监测{content}，"
                f"采用{method}，频次为{freq_text}。"
            )
        content_text = (
            "根据项目防治分区特点，各分区监测内容、方法和频次如下：" +
            "".join(zone_lines)
        )
    else:
        content_text = (
            "本项目监测内容主要包括：扰动面积、水土流失状况、"
            "防治措施实施效果及植被恢复情况。"
            "监测方法以现场量测和定点照相为主，"
            "施工期监测频次为每月1次，恢复期为每季度1次。"
        )

    paragraphs.append(NarrativeParagraph(
        text=content_text,
        evidence_refs=["field.fact.land.county_breakdown"],
        source_rule_refs=["rule.template_2026.section_8"],
    ))

    # ---- Conditional: stability monitoring for ≥3级 disposal sites ----
    if has_stability_monitoring:
        paragraphs.append(NarrativeParagraph(
            text=(
                "本项目弃渣场（含临时堆土场）级别为3级及以上，"
                "应开展稳定监测。监测内容包括堆体表面位移、"
                "地下水位变化、渗出水量等，"
                "采用全站仪、位移计等设备进行监测，"
                "频次不低于每周1次。"
            ),
            evidence_refs=[
                "field.derived.disposal_site.level_assessment",
            ],
            source_rule_refs=[
                "rule.template_2026.section_8",
                "rule.t2026.spoil_level_3_monitoring",
            ],
        ))

    if has_video_surveillance:
        paragraphs.append(NarrativeParagraph(
            text=(
                "根据规范要求，3级及以上弃渣场（含临时堆土场）"
                "应采取视频监控方式，全过程记录弃渣和防护措施实施情况。"
            ),
            evidence_refs=[
                "field.derived.disposal_site.level_assessment",
            ],
            source_rule_refs=[
                "rule.template_2026.section_8",
                "rule.t2026.spoil_video_surveillance",
            ],
        ))

    # ---- 8.4 Implementation conditions (merged) ----
    paragraphs.append(NarrativeParagraph(
        text=(
            "水土保持监测由具有相应能力的监测机构承担，"
            "监测人员应具备水土保持相关专业知识。"
            "监测设备包括全站仪、GPS、量测标尺、照相设备等。"
            "监测成果应包括水土保持监测季报和总结报告，"
            "并在水土保持设施验收前提交。"
        ),
        evidence_refs=[],
        source_rule_refs=[
            "rule.template_2026.section_8",
            "standard.gb_50433_2018",
        ],
    ))

    return NarrativeBlock(
        section_id="sec.monitoring.contents_methods_frequency",
        title="监测内容、方法与频次",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
    )
