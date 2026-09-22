"""
sec_3_1_site_selection — 3.1 选址选线水土保持评价 narrative template

消费 facts: natural.other_sensitive_areas
           location.province_list / prefecture_list

措辞原则:
  - 严格复述 facts 中的 spatial_relation 和 approval_status
  - 不替代审批部门做审批结论
  - approval_status 显示"待确认"时如实表述为"待审批确认"

P0-02 / P0-03 变更:
  1. 本节过去挂在 `ob.unavoidability.redline_conflict` 上作为整节适用性开关
     (projection._SECTION_CONDITIONALS)。选址选线评价是**每个项目都要做的
     常规评价**, 不是不可避让专题; 现已解耦, 见 projection 的注释。
  2. 原实现在敏感区清单为空 (含字段缺失) 时输出"本项目不涉及生态保护红线、
     自然保护区等敏感区域，选址符合水土保持相关法律法规要求" —— 两个问题:
     前半句是"字典查不到"推出来的核查结论, 后半句是没有任何项目证据的合规判断。
  3. 有敏感区时原实现输出"相关不可避让论证程序已启动或完成""项目选址基本符合
     水土保持相关法律法规要求", 同样没有证据支持。

  现在三类结论都走 judgment(): 没有绑定当前输入的复核记录就只陈述事实与缺口。
"""
from __future__ import annotations

from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity, Stage

SECTION_ID = "sec.evaluation.site_selection"
_F_SENSITIVE = "field.fact.natural.other_sensitive_areas"

SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_3_1.site_selection.v2",
    section_id=SECTION_ID,
    template_version="v2",
    template_author="cpswc_p0_03",
    normative_basis=[
        "rule.template_2026.section_3",
        "standard.gb_50433_2018.section_3",
    ],
    supported_variants=["default"],
    input_fields=[
        _F_SENSITIVE,
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
    ],
)

_RULES = ["rule.template_2026.section_3", "standard.gb_50433_2018.section_3"]


def render(facts: dict, derived: dict, triggered: set[str],
           ledger=None, unknown=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence(SECTION_ID, facts, derived, ledger=ledger, context=context)
    sensitive = ev.items(_F_SENSITIVE)

    paragraphs: list[NarrativeParagraph] = []

    if not sensitive.is_present:
        paragraphs.append(ev.gap_paragraph(
            sensitive,
            lead="未提供敏感区排查结果，无法开展选址选线水土保持评价",
            source_rule_refs=_RULES,
            paragraph_id="narr.evaluation.site_selection.inputs",
        ))
    elif sensitive.value:
        for i, area in enumerate(sensitive.value, 1):
            if not isinstance(area, dict):
                continue
            paragraphs.append(NarrativeParagraph(
                text=(f"本项目涉及{area.get('area_type', '敏感区域')}"
                      f"（{area.get('name', '名称未填')}），"
                      f"{area.get('spatial_relation', '空间关系未填')}。"
                      f"目前{area.get('approval_status', '审批状态未填')}。"),
                evidence_refs=[_F_SENSITIVE],
                source_rule_refs=_RULES,
                assertion_class=AssertionClass.FACT_RESTATEMENT,
                paragraph_id=f"narr.evaluation.site_selection.area_{i}",
            ))
        paragraphs.append(ev.judgment(
            "从水土保持角度分析，项目选址已对涉及的敏感区域进行了核查，"
            "相关不可避让论证程序已启动或完成。在落实本方案提出的水土保持措施后，"
            "项目选址符合水土保持相关法律法规要求。",
            target_ref=SECTION_ID,
            pending_text=(
                "上述敏感区的涉及情况来自项目填报。选址是否符合水土保持相关法律"
                "法规要求、不可避让论证是否已按要求开展，须由水土保持工程师结合"
                "各敏感区的主管部门意见与论证材料复核确认；"
                "复核记录形成前，本节不作选址合规性结论。"),
            evidence_refs=[_F_SENSITIVE, "ob.unavoidability.redline_conflict"],
            source_rule_refs=_RULES,
            paragraph_id="narr.evaluation.site_selection.conclusion",
            remediation="收集各敏感区主管部门意见与不可避让论证材料后复核",
        ))
    else:
        # 提供了空清单: 可以复述"未填报任何敏感区", 但"不涉及"是核查结论。
        paragraphs.append(NarrativeParagraph(
            text="本项目填报的敏感区清单为空，即未填报涉及任何水土保持敏感区。",
            evidence_refs=[_F_SENSITIVE],
            source_rule_refs=_RULES,
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.evaluation.site_selection.empty_list",
        ))
        para = ev.judgment(
            "本项目不涉及生态保护红线、自然保护区等敏感区域，"
            "选址符合水土保持相关法律法规要求。",
            target_ref=SECTION_ID,
            pending_text=(
                "清单为空只说明未填报，不等于已逐项核查确认不涉及，"
                "也不足以支持选址合规性结论。需先按敏感区类型清单完成核查"
                "（说明核查范围、所依据材料及版本），再由水土保持工程师"
                "就选址合规性作出复核结论。"),
            evidence_refs=[_F_SENSITIVE],
            source_rule_refs=_RULES,
            paragraph_id="narr.evaluation.site_selection.conclusion",
            remediation="完成敏感区逐项核查并复核选址合规性",
        )
        if para.assertion_class is AssertionClass.GAP_STATEMENT:
            ev.add_finding(
                "SOURCE_UNVERIFIED",
                f"{SECTION_ID}: 空敏感区清单不构成选址合规性的证据",
                severity=Severity.BLOCK,
                target_ref=SECTION_ID,
                remediation="完成敏感区逐项核查并复核选址合规性",
                stage=Stage.INPUT,
            )
        paragraphs.append(para)

    return NarrativeBlock(
        section_id=SECTION_ID,
        title="选址选线水土保持评价",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
        quality_findings=ev.findings,
    )
