"""
sec_2_1_2_land_earthwork — 2.1 占地面积 + 2.2 土石方平衡 narrative templates

facts 密集章节。关键纪律: 像报告语言, 不能变成字段串烧。
单 variant (default)。

B 批 P0-04 改造 (任务 B-T1, 见 implementation/B_BATCH_TEMPLATE_TASKS.md):

  本模板是全册数字的源头之一, 且与已改造的 sec_3_evaluation 读同一批
  earthwork 字段 —— 两处口径必须一致。

  原实现的两个问题:
    1. `_v(facts, key, default="—")`: 缺失显示成短横线仍能成句。
    2. `borrow_val.get("value", 0) if isinstance(...) else 0`:
       借方/弃方/综合利用**缺失时当 0**, 三个都"为 0"就输出
       "土石方基本平衡" —— 这是从"资料没填"推出来的结论。

  现在统一经 BuildContext / SectionEvidence 读值, 缺失、明确零、非法值、
  来源冲突四类输入分别处理 (验收项 T-a/T-b/T-c/T-d)。
"""
from __future__ import annotations

from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence

SEC_LAND = "sec.project_overview.land_occupation"
SEC_EARTHWORK = "sec.project_overview.earthwork_balance"

TEMPLATE_SPEC_2_1 = NarrativeTemplateSpec(
    template_id="nt.sec_2_1.land_occupation.v2",
    section_id=SEC_LAND,
    template_version="v2",
    template_author="cpswc_p0_04",
    normative_basis=["rule.template_2026.section_2_1"],
    supported_variants=["default"],
    input_fields=[
        "field.fact.land.total_area",
        "field.fact.land.permanent_area",
        "field.fact.land.temporary_area",
    ],
)

TEMPLATE_SPEC_2_2 = NarrativeTemplateSpec(
    template_id="nt.sec_2_2.earthwork_balance.v2",
    section_id=SEC_EARTHWORK,
    template_version="v2",
    template_author="cpswc_p0_04",
    normative_basis=["rule.template_2026.section_2_2"],
    supported_variants=["default"],
    input_fields=[
        "field.fact.earthwork.excavation",
        "field.fact.earthwork.fill",
        "field.fact.earthwork.spoil",
        "field.fact.earthwork.borrow",
        "field.fact.earthwork.comprehensive_reuse",
        "field.fact.earthwork.self_reuse",
    ],
)


def render_2_1(facts: dict, derived: dict, triggered: set[str],
               ledger=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence(SEC_LAND, facts, derived, ledger=ledger, context=context)

    total = ev.quantity("field.fact.land.total_area")
    perm = ev.quantity("field.fact.land.permanent_area")
    temp = ev.quantity("field.fact.land.temporary_area")

    paragraphs: list[NarrativeParagraph] = []
    if ev.all_present(total, perm, temp):
        paragraphs.append(NarrativeParagraph(
            text=(f"本项目总占地面积为{total.display()}，"
                  f"其中永久占地{perm.display()}，临时占地{temp.display()}。"),
            evidence_refs=[v.field_id for v in (total, perm, temp)],
            source_rule_refs=["rule.template_2026.section_2_1"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.project_overview.land_occupation.areas",
        ))
        # 永久/临时占地的构成是规范对这两类用地的界定, 不是本项目的实测结论
        paragraphs.append(NarrativeParagraph(
            text=("按占地性质划分，永久占地包括建筑物基底、道路及永久性附属设施占地；"
                  "临时占地包括施工生产生活区、施工道路、临时堆土场"
                  "及其他施工临时用地。各类用地的具体构成详见占地面积表。"),
            evidence_refs=["art.table.total_land_occupation"],
            source_rule_refs=["rule.template_2026.section_2_1"],
            assertion_class=AssertionClass.NORMATIVE_REQUIREMENT,
            paragraph_id="narr.project_overview.land_occupation.composition",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            total, perm, temp,
            lead="占地面积数据不完整，无法说明本项目占地构成",
            source_rule_refs=["rule.template_2026.section_2_1"],
            paragraph_id="narr.project_overview.land_occupation.areas",
        ))

    return NarrativeBlock(
        section_id=SEC_LAND,
        title="占地面积",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_2_1.template_id,
        template_version=TEMPLATE_SPEC_2_1.template_version,
        normative_basis=TEMPLATE_SPEC_2_1.normative_basis,
        quality_findings=ev.findings,
    )


def render_2_2(facts: dict, derived: dict, triggered: set[str],
               ledger=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence(SEC_EARTHWORK, facts, derived, ledger=ledger,
                         context=context)

    exc = ev.quantity("field.fact.earthwork.excavation")
    fill = ev.quantity("field.fact.earthwork.fill")
    self_reuse = ev.quantity("field.fact.earthwork.self_reuse")
    spoil = ev.quantity("field.fact.earthwork.spoil")
    borrow = ev.quantity("field.fact.earthwork.borrow")
    reuse = ev.quantity("field.fact.earthwork.comprehensive_reuse")

    paragraphs: list[NarrativeParagraph] = []

    # ── 段 1: 挖填与场内利用 ──
    if ev.all_present(exc, fill, self_reuse):
        paragraphs.append(NarrativeParagraph(
            text=(f"本项目挖方总量{exc.display()}（不含表土），"
                  f"填方总量{fill.display()}。"
                  f"项目自身利用挖方{self_reuse.display()}用于场地回填及地基处理。"),
            evidence_refs=[v.field_id for v in (exc, fill, self_reuse)],
            source_rule_refs=["rule.template_2026.section_2_2"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.project_overview.earthwork_balance.excavation",
        ))
    else:
        paragraphs.append(ev.gap_paragraph(
            exc, fill, self_reuse,
            lead="挖填方数据不完整",
            source_rule_refs=["rule.template_2026.section_2_2"],
            paragraph_id="narr.project_overview.earthwork_balance.excavation",
        ))

    # ── 段 2: 借方 / 弃方 / 综合利用 ──
    # 三个量必须齐全才谈得上"平衡"。缺任何一个都不能说"基本平衡" ——
    # 原实现把缺失当 0, 三个都"是 0"就宣布平衡。
    if not ev.all_present(spoil, borrow, reuse):
        paragraphs.append(ev.gap_paragraph(
            spoil, borrow, reuse,
            lead="弃方、借方或综合利用量缺失，无法说明土石方平衡情况",
            source_rule_refs=["rule.template_2026.section_2_2"],
            paragraph_id="narr.project_overview.earthwork_balance.flow",
        ))
    else:
        parts: list[str] = []
        if borrow.value:
            parts.append(f"需外购借方{borrow.display()}")
        else:
            parts.append("填报借方量为 0，即不从项目区外借取土石方")
        if spoil.value:
            if reuse.value:
                parts.append(f"产生弃渣{spoil.display()}，"
                             f"其中综合利用{reuse.display()}")
            else:
                parts.append(f"产生弃渣{spoil.display()}，填报综合利用量为 0")
        else:
            parts.append("填报弃渣量为 0")
        paragraphs.append(NarrativeParagraph(
            text="；".join(parts) + "。各项去向详见土石方平衡表。",
            evidence_refs=[v.field_id for v in (spoil, borrow, reuse)]
                          + ["art.table.earthwork_balance"],
            source_rule_refs=["rule.template_2026.section_2_2"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.project_overview.earthwork_balance.flow",
        ))

    return NarrativeBlock(
        section_id=SEC_EARTHWORK,
        title="土石方平衡",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=TEMPLATE_SPEC_2_2.template_id,
        template_version=TEMPLATE_SPEC_2_2.template_version,
        normative_basis=TEMPLATE_SPEC_2_2.normative_basis,
        quality_findings=ev.findings,
    )
