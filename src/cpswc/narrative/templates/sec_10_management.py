"""
sec_10_management — 第 10 章 水土保持管理

2026 模板要求:
  从组织管理、后续设计、水土保持监测、水土保持监理、水土保持施工
  和水土保持设施验收等方面明确水土保持管理内容与要求。

实现策略: 纯模板文，插入项目名/建设单位名。
"""
from __future__ import annotations
from cpswc.narrative.contract import (
    NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec, RenderStatus,
)


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_10.management.v1",
    section_id="sec.management",
    template_version="v1",
    template_author="cpswc_v1",
    normative_basis=[
        "rule.template_2026.section_10",
        "standard.gb_50433_2018",
    ],
    supported_variants=["default"],
    input_fields=[
        "field.fact.project.name",
        "field.fact.project.builder",
    ],
)


def render(facts: dict, derived: dict, triggered: set[str],
           **kwargs) -> NarrativeBlock:
    name = facts.get("field.fact.project.name", "本项目")
    builder = facts.get("field.fact.project.builder", "建设单位")

    p1 = NarrativeParagraph(
        text=(
            f"为确保{name}水土保持方案的有效实施，"
            f"{builder}应建立健全水土保持管理体系，"
            f"明确水土保持管理机构和责任人，"
            f"将水土保持工作纳入项目建设管理全过程。"
        ),
        evidence_refs=[
            "field.fact.project.name",
            "field.fact.project.builder",
        ],
        source_rule_refs=["rule.template_2026.section_10"],
    )

    p2 = NarrativeParagraph(
        text=(
            f"水土保持管理主要包括以下内容："
            f"（1）组织管理：成立水土保持工作领导小组，"
            f"明确项目经理、施工负责人、水保专员等岗位职责，"
            f"建立日常巡查和定期检查制度。"
            f"（2）后续设计：根据施工实际情况和监测成果，"
            f"及时调整和完善水土保持措施设计。"
            f"（3）水土保持监测：按本方案第 8 章要求开展水土保持监测工作，"
            f"及时掌握水土流失动态和防治效果。"
            f"（4）水土保持监理：委托具有相应资质的单位开展水土保持施工监理，"
            f"确保措施按设计施工。"
            f"（5）水土保持施工：严格按照批准的水土保持方案和设计文件组织施工，"
            f"做到先拦后弃、先排后挖、及时恢复。"
            f"（6）水土保持设施验收：工程竣工后，"
            f"按照《水利部关于加强事中事后监管规范生产建设项目"
            f"水土保持设施自主验收的通知》（水保〔2017〕365号）要求，"
            f"组织水土保持设施验收。"
        ),
        evidence_refs=["field.fact.project.name"],
        source_rule_refs=[
            "rule.template_2026.section_10",
            "standard.gb_50433_2018",
        ],
    )

    p3 = NarrativeParagraph(
        text=(
            f"{builder}应建立水土保持档案管理制度，"
            f"妥善保管水土保持方案及批复文件、设计文件、施工记录、"
            f"监测报告、监理报告、验收资料等，确保资料完整可追溯。"
        ),
        evidence_refs=["field.fact.project.builder"],
        source_rule_refs=["rule.template_2026.section_10"],
    )

    return NarrativeBlock(
        section_id="sec.management",
        title="水土保持管理",
        render_status=RenderStatus.FULL,
        paragraphs=[p1, p2, p3],
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
    )
