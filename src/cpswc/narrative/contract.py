#!/usr/bin/env python3
"""
narrative_contract.py — CPSWC v0.5 Narrative Projection Contract

Step 14-0: 定义正文投影层的数据契约。

核心原则 (来自宪法 + v0.5 目标):
  1. NarrativeBlock 是语义层, 不承载渲染信息 (display_number 由 renderer 绑定)
  2. NarrativeParagraph 是追溯的最小单元, 每段至少有 evidence_refs 或 source_rule_refs
  3. 模板不创造信息, 只组织信息 — paragraphs 里的每个数字都必须能在 evidence_refs 中找到来源
  4. variant 必须静态注册, 不允许运行时拼接

使用方式:
  from cpswc.narrative.contract import NarrativeParagraph, NarrativeBlock, validate_block
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from enum import Enum
from typing import Any

from cpswc.report_quality import Applicability, QualityFinding


# ============================================================
# Enums
# ============================================================

class RenderStatus(str, Enum):
    """**渲染状态, 不是专业完成度。**

    P0-01 后语义收紧: FULL 只表示"这块有连续可读文字", 它不表示内容完整、
    证据齐全或已经专业复核。专业完成度由 cpswc.report_quality 的
    ContentState / EvidenceState / ReviewState 单独承载, 默认 UNASSESSED。
    任何消费方都不得把 FULL 映射成 ReviewState.CONFIRMED。
    """
    FULL = "full"                    # 有连续可读正文
    SKELETON = "skeleton"            # 占位符, 待扩展
    NOT_APPLICABLE = "not_applicable"  # 本项目不涉及


class ContentRole(str, Enum):
    """这一块在内容规范里算不算一份成果。"""
    LEAF_CONTENT = "LEAF_CONTENT"   # 叶子内容, 进覆盖率分母
    PARENT_INTRO = "PARENT_INTRO"   # 父标题引言, **不计完成成果** (验收 Q01)
    PLACEHOLDER = "PLACEHOLDER"     # 占位


class AssertionClass(str, Enum):
    """段落的断言类型。决定它需要什么级别的支持 (04 文档第 5 节)。"""
    FACT_RESTATEMENT = "FACT_RESTATEMENT"          # 复述当前有效值
    ARITHMETIC = "ARITHMETIC"                      # 可复算的算术结果
    NORMATIVE_REQUIREMENT = "NORMATIVE_REQUIREMENT"  # 复述规范要求本身
    TARGET_VALUE = "TARGET_VALUE"                  # 目标值 (不得当效果用)
    DESIGN_EFFECT = "DESIGN_EFFECT"                # 设计效果 (需独立计算)
    MONITORED_ACTUAL = "MONITORED_ACTUAL"          # 实测值 (需时点与来源)
    PROJECT_JUDGMENT = "PROJECT_JUDGMENT"          # 本项目合理/可行/符合 — 需当前复核记录
    GAP_STATEMENT = "GAP_STATEMENT"                # 如实说明缺口


# ============================================================
# Paragraph — 追溯的最小单元
# ============================================================

@dataclass
class NarrativeParagraph:
    """
    单段正文。

    追溯约束 (paragraph 级):
      evidence_refs 和 source_rule_refs 至少有一个非空。
      即: 每段要么追溯到事实, 要么追溯到规范, 或两者都有。
    """
    text: str
    evidence_refs: list[str] = dc_field(default_factory=list)
    """本段引用的 field.* / cal.* / ob.* / art.* id"""

    source_rule_refs: list[str] = dc_field(default_factory=list)
    """本段依据的 rule.* / standard.* 条款"""

    unresolved_placeholders: list[str] = dc_field(default_factory=list)
    """本段中仍需人工补充的位置标记 (如 '{待填}')"""

    warnings: list[str] = dc_field(default_factory=list)
    """生成本段时产生的告警"""

    paragraph_id: str | None = None
    """稳定段落标识, narr.* 命名空间 (CORE_CONTRACTS id_namespaces.narrative_node)"""

    assertion_class: AssertionClass = AssertionClass.FACT_RESTATEMENT
    """本段断言类型。PROJECT_JUDGMENT 必须附 review_refs, 见 validate_paragraph"""

    review_refs: list[str] = dc_field(default_factory=list)
    """支持本段专业判断的复核记录 id。只有 PROJECT_JUDGMENT 需要"""


# ============================================================
# Block — 章节级投影单元
# ============================================================

@dataclass
class NarrativeBlock:
    """
    章节级叙事投影单元。

    关键设计:
      - section_id 是语义锚, 不是显示编号 (决议 3)
      - display_number 不在此处, 由 renderer 根据 section tree 绑定
      - variant_id 必须来自 template 的静态注册集合
      - render_status 决定 renderer 的行为:
          full → 渲染 paragraphs 正文
          skeleton → 渲染占位符
          not_applicable → 渲染"本项目不涉及"说明
    """
    section_id: str
    """sec.* 命名空间的稳定标识"""

    title: str
    """章节中文标题 (不含编号, 编号由 renderer 绑定)"""

    render_status: RenderStatus

    paragraphs: list[NarrativeParagraph] = dc_field(default_factory=list)
    """正文段落 (render_status=full 时必须非空)"""

    variant_id: str | None = None
    """
    模板变体标识。一个 section 可以有多个 variant (如 sec.5: no_site / single_site / multi_site)。
    variant 集合必须在 template 中静态注册, projection 只能从已注册集合中选。
    render_status != full 时可为 None。
    """

    template_id: str | None = None
    """产出本 block 的模板 id (如 'nt.sec_1_1.basic_info.v1')"""

    template_version: str | None = None
    """模板版本"""

    normative_basis: list[str] = dc_field(default_factory=list)
    """本节整体的规范依据 (block 级, 与 paragraph 级的 source_rule_refs 互补)"""

    block_warnings: list[str] = dc_field(default_factory=list)
    """block 级告警 (如 variant 选择告警、数据不足告警)"""

    content_role: ContentRole = ContentRole.LEAF_CONTENT
    """父标题引言标 PARENT_INTRO, 不计入内容完成成果 (验收 Q01)"""

    applicability: Applicability | None = None
    """
    本节是否适用。None = 由消费方按渲染状态保守推断。
    UNKNOWN 必须显式表达, **不得**退化成 NOT_APPLICABLE (验收 U07 / R03)。
    """

    quality_findings: list[QualityFinding] = dc_field(default_factory=list)
    """本块产生的质量诊断。只存引用与状态, 不复制项目数值"""


# ============================================================
# Validation
# ============================================================

def validate_paragraph(p: NarrativeParagraph) -> list[str]:
    """
    校验单段追溯约束。

    规则: evidence_refs 和 source_rule_refs 至少有一个非空。
    返回: 违规消息列表 (空 = 通过)
    """
    errors = []
    if not p.evidence_refs and not p.source_rule_refs:
        errors.append(
            f"paragraph 无追溯: evidence_refs 和 source_rule_refs 都为空. "
            f"text 前 40 字: '{p.text[:40]}...'"
        )
    # P0-03: 本项目"合理/可行/符合"类判断必须绑定当前有效的复核记录。
    # 仅引用规范、仅有一张表、义务已触发都不构成充分支持 (04 文档第 5 节)。
    if p.assertion_class is AssertionClass.PROJECT_JUDGMENT and not p.review_refs:
        errors.append(
            f"paragraph 标为 PROJECT_JUDGMENT 但无 review_refs: "
            f"无当前复核记录不得作本项目合规/合理性判断. "
            f"text 前 40 字: '{p.text[:40]}...'"
        )
    return errors


def validate_block(block: NarrativeBlock) -> list[str]:
    """
    校验 NarrativeBlock 的契约完整性。

    规则:
      1. render_status=full 时 paragraphs 必须非空
      2. render_status=full 时 block 的所有 paragraphs 的 evidence_refs 并集必须非空
      3. render_status=full 时 block 的所有 paragraphs 的 source_rule_refs 并集必须非空
      4. 每个 paragraph 必须满足 validate_paragraph
      5. render_status=full 时 variant_id 和 template_id 必须非空

    返回: 违规消息列表 (空 = 全部通过)
    """
    errors = []

    if block.render_status == RenderStatus.FULL:
        if not block.paragraphs:
            errors.append(
                f"[{block.section_id}] render_status=full 但 paragraphs 为空"
            )

        # 并集检查
        all_evidence = set()
        all_rules = set()
        for p in block.paragraphs:
            all_evidence.update(p.evidence_refs)
            all_rules.update(p.source_rule_refs)
            errors.extend(validate_paragraph(p))

        if not all_evidence:
            errors.append(
                f"[{block.section_id}] full block 的 evidence_refs 并集为空"
            )
        if not all_rules:
            errors.append(
                f"[{block.section_id}] full block 的 source_rule_refs 并集为空"
            )

        if not block.variant_id:
            errors.append(
                f"[{block.section_id}] full block 缺 variant_id"
            )
        if not block.template_id:
            errors.append(
                f"[{block.section_id}] full block 缺 template_id"
            )

    return errors


# ============================================================
# Template Metadata Contract
# ============================================================

@dataclass
class NarrativeTemplateSpec:
    """
    模板规格 — 每个 section template 的元数据。

    模板不以 f-string 散落在代码里, 而是集中注册。
    每个 template 必须声明:
      - 它服务哪个 section
      - 它支持哪些 variant
      - 它需要哪些输入字段
      - 它的规范依据
    """
    template_id: str
    """唯一标识, 如 'nt.sec_1_1.basic_info.v1'"""

    section_id: str
    """对应的 sec.* id"""

    template_version: str
    """版本号"""

    template_author: str
    """作者/来源"""

    normative_basis: list[str]
    """本模板依据的规范条款"""

    supported_variants: list[str]
    """支持的 variant id 列表 (静态注册, projection 不可超出此集合)"""

    input_fields: list[str]
    """本模板需要读取的 field.* / derived.* / ob.* / cal.* id"""

    def validate_variant(self, variant_id: str) -> bool:
        """检查 variant 是否在已注册集合中"""
        return variant_id in self.supported_variants


# ============================================================
# Projection Result (顶层容器)
# ============================================================

@dataclass
class NarrativeProjectionResult:
    """project_narrative() 的完整返回值"""
    blocks: list[NarrativeBlock]
    """所有章节的 narrative blocks (按 section tree 顺序)"""

    full_count: int = 0
    """render_status=full 的 block 数量。

    **只表示"文字已渲染的块数"**, 不是完成度分子。内容完成度见
    cpswc.report_quality.ReportQualitySummary.content_coverage。"""

    skeleton_count: int = 0
    """render_status=skeleton 的 block 数量"""

    not_applicable_count: int = 0

    unknown_applicability_count: int = 0
    """适用性无法确定的块数。**不计入 not_applicable_count** (验收 U07)"""

    quality_findings: list[QualityFinding] = dc_field(default_factory=list)
    """投影层产生的全局质量诊断"""

    validation_errors: list[str] = dc_field(default_factory=list)
    """全部 block 的 validate_block 错误汇总"""

    projection_warnings: list[str] = dc_field(default_factory=list)
    """投影过程中的全局告警"""

    def validate_all(self) -> list[str]:
        """对所有 blocks 执行 validate_block, 返回全部错误"""
        errors = []
        for b in self.blocks:
            errors.extend(validate_block(b))
        self.validation_errors = errors
        return errors
