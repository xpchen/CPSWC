"""
sec_2_5_sensitive_areas — 2.x 敏感区域 narrative template

按 SensitiveAreaTypeRegistry_v0 的 12 类 canonical 清单逐项排查:
  - 命中项 (来自 facts.natural.other_sensitive_areas) 逐条详述
  - 未命中项汇总说明
  - 重点预防/治理区 (key_prevention_treatment_areas) 单独成段

消费 facts: natural.other_sensitive_areas / key_prevention_treatment_areas

P0-03 变更 (验收 S03 / N02):
  原实现用 `facts.get(key) or []`, 于是"字段整个没填"和"填了空清单"都会输出
  "经逐项排查，项目区不涉及 流域管理范围、河湖管理范围、……等水土保持敏感区"。
  这是一句**核查结论**, 而它的全部依据只是字典里查不到这个键。

  04 文档第 5 节写得很清楚: 空 list、默认 False、字典查不到, 都不构成
  "已核查不涉及"的充分支持; 充分支持是"本项核查覆盖范围、材料版本、结果和确认"。

  现在:
    - 字段缺失            → 缺口段, 说明未提供敏感区排查结果
    - 提供了空清单        → 复述"填报清单为空", 排查结论走 judgment() 待确认
    - 有核查确认记录      → 才输出"经逐项排查不涉及…"

  本模板不改变 12 类 canonical 清单本身 (它镜像 registry)。
"""
from __future__ import annotations

from cpswc.narrative.contract import (
    AssertionClass, NarrativeBlock, NarrativeParagraph, NarrativeTemplateSpec,
    RenderStatus,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.report_quality import Severity, Stage

SECTION_ID = "sec.project_overview.sensitive_areas"

# SensitiveAreaTypeRegistry_v0 canonical 12 类 (display_name 顺序与 registry 一致)
# 与 registries/SensitiveAreaTypeRegistry_v0.yaml 保持镜像; 任一处变更需同步.
SENSITIVE_AREA_CANONICAL: tuple[str, ...] = (
    "流域管理范围",
    "河湖管理范围",
    "饮用水水源保护区",
    "水功能一级区（保护区与保留区）",
    "自然保护区",
    "世界文化和自然遗产地",
    "风景名胜区",
    "地质公园",
    "森林公园",
    "重要湿地",
    "生态保护红线",
    "永久基本农田",
)

_F_SENSITIVE = "field.fact.natural.other_sensitive_areas"
_F_KEY_AREAS = "field.fact.natural.key_prevention_treatment_areas"


SPEC = NarrativeTemplateSpec(
    template_id="nt.sec_2_x.sensitive_areas.v3",
    section_id=SECTION_ID,
    template_version="v3",
    template_author="cpswc_p0_03",
    normative_basis=[
        "rule.template_2026.section_2",
        "standard.gb_50433_2018.section_2",
        "registry.sensitive_area_type_v0",
    ],
    supported_variants=["default"],
    input_fields=[
        _F_SENSITIVE,
        _F_KEY_AREAS,
        "field.fact.location.province_list",
        "field.fact.location.prefecture_list",
    ],
)

_RULES = [
    "rule.template_2026.section_2",
    "standard.gb_50433_2018.section_2",
    "registry.sensitive_area_type_v0",
]


def render(facts: dict, derived: dict, triggered: set[str],
           ledger=None, context=None, **kwargs) -> NarrativeBlock:
    ev = SectionEvidence(SECTION_ID, facts, derived, ledger=ledger, context=context)

    key_areas = ev.items(_F_KEY_AREAS)
    sensitive = ev.items(_F_SENSITIVE)

    paragraphs: list[NarrativeParagraph] = []

    # ---------- 段 1: 水土流失重点预防区/治理区 ----------
    if not key_areas.is_present:
        paragraphs.append(ev.gap_paragraph(
            key_areas,
            lead="未提供水土流失重点预防区、重点治理区的排查结果",
            source_rule_refs=["rule.template_2026.section_2"],
            paragraph_id="narr.project_overview.sensitive_areas.key_areas",
        ))
    elif key_areas.value:
        paragraphs.append(NarrativeParagraph(
            text=(f"项目区涉及水土流失重点预防区或重点治理区："
                  f"{'、'.join(str(a) for a in key_areas.value)}。"),
            evidence_refs=[_F_KEY_AREAS],
            source_rule_refs=["rule.template_2026.section_2"],
            assertion_class=AssertionClass.FACT_RESTATEMENT,
            paragraph_id="narr.project_overview.sensitive_areas.key_areas",
        ))
    else:
        paragraphs.append(_empty_list_paragraph(
            ev,
            confirmed_text=("经核查，项目区不属于国家级、省级及市级划定的"
                            "水土流失重点预防区和重点治理区。"),
            pending_text=("本项目填报的水土流失重点预防区、重点治理区清单为空。"
                          "是否确实不属于国家级、省级及市级划定的重点预防区与"
                          "重点治理区，须有相应区划文件的核查记录支持；"
                          "核查记录形成前，本节不作“不属于”的结论。"),
            target_ref=f"{SECTION_ID}.key_areas",
            evidence_refs=[_F_KEY_AREAS],
            paragraph_id="narr.project_overview.sensitive_areas.key_areas",
            remediation="核对国家/省/市级水土流失重点防治区划文件并记录核查结论",
        ))

    # ---------- 段 2..N: 命中的敏感区逐条详述 ----------
    hit_types: set[str] = set()
    if sensitive.is_present:
        for area in sensitive.value:
            if not isinstance(area, dict):
                continue
            area_type = area.get("area_type", "敏感区域")
            hit_types.add(area_type)
            paragraphs.append(NarrativeParagraph(
                text=(f"经核查，项目区涉及{area_type}：{area.get('name', '（名称未填）')}。"
                      f"空间关系为：{area.get('spatial_relation', '（未填）')}。"
                      f"审批状态：{area.get('approval_status', '（未填）')}。"),
                evidence_refs=[_F_SENSITIVE],
                source_rule_refs=_RULES,
                assertion_class=AssertionClass.FACT_RESTATEMENT,
                paragraph_id=f"narr.project_overview.sensitive_areas.hit_{len(hit_types)}",
            ))

    # ---------- 段末: 未命中类型 ----------
    if not sensitive.is_present:
        paragraphs.append(ev.gap_paragraph(
            sensitive,
            lead=f"未提供敏感区排查结果，无法说明本项目与 "
                 f"{len(SENSITIVE_AREA_CANONICAL)} 类水土保持敏感区的关系",
            source_rule_refs=_RULES,
            paragraph_id="narr.project_overview.sensitive_areas.screening",
        ))
    else:
        not_hit = [x for x in SENSITIVE_AREA_CANONICAL if x not in hit_types]
        if not_hit:
            lead = "除上述涉及项外，" if hit_types else ""
            paragraphs.append(_empty_list_paragraph(
                ev,
                confirmed_text=(f"{lead}经逐项排查，项目区不涉及"
                                f"{'、'.join(not_hit)}等水土保持敏感区。"),
                pending_text=(
                    f"{lead}本项目填报的敏感区清单中未出现以下 {len(not_hit)} 类："
                    f"{'、'.join(not_hit)}。清单未列出只说明未填报，"
                    f"不等于已逐项核查确认不涉及；逐项核查须说明核查范围、"
                    f"所依据的区划/红线材料及其版本，并留下确认记录。"
                    f"核查记录形成前，本节不作“不涉及”的结论。"),
                target_ref=f"{SECTION_ID}.screening",
                evidence_refs=[_F_SENSITIVE],
                paragraph_id="narr.project_overview.sensitive_areas.screening",
                remediation="按 12 类清单逐项核查并记录核查材料版本与结论",
            ))

    return NarrativeBlock(
        section_id=SECTION_ID,
        title="敏感区域",
        render_status=RenderStatus.FULL,
        paragraphs=paragraphs,
        variant_id="default",
        template_id=SPEC.template_id,
        template_version=SPEC.template_version,
        normative_basis=SPEC.normative_basis,
        quality_findings=ev.findings,
    )


def _empty_list_paragraph(ev: SectionEvidence, *, confirmed_text: str,
                          pending_text: str, target_ref: str,
                          evidence_refs: list[str], paragraph_id: str,
                          remediation: str) -> NarrativeParagraph:
    """空清单 → 待核查说明; 有核查确认记录 → 才输出"经核查不涉及"。"""
    para = ev.judgment(
        confirmed_text,
        target_ref=target_ref,
        pending_text=pending_text,
        evidence_refs=evidence_refs,
        source_rule_refs=_RULES,
        paragraph_id=paragraph_id,
        remediation=remediation,
    )
    if para.assertion_class is AssertionClass.GAP_STATEMENT:
        ev.add_finding(
            "SOURCE_UNVERIFIED",
            f"{target_ref}: 空清单不构成“已核查不涉及”的证据",
            severity=Severity.BLOCK,
            target_ref=target_ref,
            remediation=remediation,
            stage=Stage.INPUT,
        )
    return para
