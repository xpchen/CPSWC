"""
sec_1_1_basic_info — 1.1 项目基本情况 narrative template

最简单的 pilot section: 纯 facts 投影, 无条件分支, 单 variant。
用于验证 facts → NarrativeParagraph → NarrativeBlock 的完整链路。
"""
from __future__ import annotations
from narrative_contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


TEMPLATE_SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_1_1.basic_info.v1",
    section_id="sec.overview.project_basic",
    template_version="v1",
    template_author="cpswc_v0.5",
    normative_basis=[
        "rule.template_2026.section_1_1",  # 2026 模板 1.1 节要求列出基本信息
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.project.name",
        "field.fact.project.code",
        "field.fact.project.industry_category",
        "field.fact.project.nature",
        "field.fact.investment.total_investment",
        "field.fact.investment.civil_investment",
        "field.fact.schedule.start_time",
        "field.fact.schedule.end_time",
        "field.fact.land.total_area",
        "field.fact.land.permanent_area",
        "field.fact.land.temporary_area",
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
    ],
)


def _v(facts: dict, key: str, default: str = "—") -> str:
    """从 facts 取值, 处理 Quantity 和 list 类型"""
    v = facts.get(key)
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        unit = v.get("unit", "")
        return f"{v['value']} {unit}".strip()
    if isinstance(v, list):
        return "、".join(str(x) for x in v)
    return str(v)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    """渲染 1.1 项目基本情况"""
    name = _v(facts, "field.fact.project.name")
    code = _v(facts, "field.fact.project.code")
    industry = _v(facts, "field.fact.project.industry_category")
    nature = _v(facts, "field.fact.project.nature")
    total_inv = _v(facts, "field.fact.investment.total_investment")
    civil_inv = _v(facts, "field.fact.investment.civil_investment")
    start = _v(facts, "field.fact.schedule.start_time")
    end = _v(facts, "field.fact.schedule.end_time")
    total_area = _v(facts, "field.fact.land.total_area")
    perm_area = _v(facts, "field.fact.land.permanent_area")
    temp_area = _v(facts, "field.fact.land.temporary_area")
    province = _v(facts, "field.fact.location.province_list")
    prefecture = _v(facts, "field.fact.location.prefecture_list")

    p1 = NarrativeParagraph(
        text=(
            f"{name}（项目代码：{code}）为{nature}项目，"
            f"属{industry}类行业，位于{province}{prefecture}。"
            f"项目总投资{total_inv}，其中土建投资{civil_inv}。"
        ),
        evidence_refs=[
            "field.fact.project.name",
            "field.fact.project.code",
            "field.fact.project.industry_category",
            "field.fact.project.nature",
            "field.fact.investment.total_investment",
            "field.fact.investment.civil_investment",
            "field.fact.location.province_list",
            "field.fact.location.prefecture_list",
        ],
        source_rule_refs=["rule.template_2026.section_1_1"],
    )

    p2 = NarrativeParagraph(
        text=(
            f"施工期为{start}至{end}。"
            f"项目总占地面积{total_area}，"
            f"其中永久占地{perm_area}，临时占地{temp_area}。"
        ),
        evidence_refs=[
            "field.fact.schedule.start_time",
            "field.fact.schedule.end_time",
            "field.fact.land.total_area",
            "field.fact.land.permanent_area",
            "field.fact.land.temporary_area",
        ],
        source_rule_refs=["rule.template_2026.section_1_1"],
    )

    return NarrativeBlock(
        section_id="sec.overview.project_basic",
        title="项目基本情况",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2],
        variant_id="default",
        template_id=TEMPLATE_SPEC.template_id,
        template_version=TEMPLATE_SPEC.template_version,
        normative_basis=TEMPLATE_SPEC.normative_basis,
    )
