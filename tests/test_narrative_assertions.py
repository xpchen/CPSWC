"""
test_narrative_assertions.py — P0-03 验收测试 (断言准入部分)

对应 04_CONTRACTS_AND_ACCEPTANCE.md 第 9 节:

    N01  空 facts 调用评价/结论模板   → 无肯定结论, 质量检查给具体缺口
    N02  有规范 ref、无项目证据       → 不准确认项目合规
    N03  借方缺失 / 明确 0 两组       → 前者待确认; 后者可复述提供值但不泛化合规
    N07  obligation 触发 / artifact 仅登记 → 不描述为已完成/已提供
    N08  改已引用输入, ref 名字不变   → 旧结论确认 STALE; 汇总也同步失效

方法说明 (重要):
  关键词检索只是**定位手段**, 不是质量证明。本文件的断言主要建立在结构上:
  段落的 AssertionClass、review_refs 绑定、以及 QualityFinding 的稳定码。
  只有在检查"某句肯定结论有没有出现"时才辅以字符串匹配, 且同时检查结构。

夹具全部为原创合成数据。复核记录是为测试构造的技术结构, 不代表任何真实
工程师的专业确认。
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.narrative.contract import (
    AssertionClass, RenderStatus, validate_block,
)
from cpswc.narrative.evidence import SectionEvidence
from cpswc.narrative.templates import (
    sec_0_overview, sec_2_3_climate_zoning, sec_2_5_sensitive_areas,
    sec_3_1_site_selection, sec_3_evaluation, sec_4_topsoil, sec_11_conclusion,
)
from cpswc.report_quality import (
    EvidenceRecord, QualityInputs, ReviewLedger, ReviewRecord, Severity,
    compute_quality_input_hash,
)


def _complete_review(review_id: str, target: str, input_hash: str,
                     verdict: str = "CONFIRMED") -> QualityInputs:
    """构造一条**完整**的复核记录 + 它引用的证据记录。

    A 批验收后, 只对上 input_hash 的空壳记录不再升级为专业确认, 因此测试
    夹具也必须成形: 审核人引用、复核时间、可解析的证据引用。

    这些是为测试构造的技术结构, **不代表任何真实工程师的专业确认**。
    """
    return QualityInputs(
        evidence_records=[EvidenceRecord(
            evidence_id=f"ev.for.{review_id}",
            target_refs=[target],
            source_kind="project_document",
            locator="fixture.synthetic 合成夹具, 无真实出处",
        )],
        review_records=[ReviewRecord(
            review_id=review_id, target_refs=[target], input_hash=input_hash,
            verdict=verdict, reviewer_ref="fixture.synthetic.reviewer",
            reviewed_at="2026-09-20",
            evidence_refs=[f"ev.for.{review_id}"])])

# 本项目合规/合理/可行类肯定结论的关键词。只用于定位, 不用于证明。
POSITIVE_MARKERS = (
    "依据充分", "布局合理", "平衡合理", "方案可行", "来源可靠",
    "有明确去向", "均达到", "均满足", "可以实现", "全部用于",
)


def _all_text(block) -> str:
    return "".join(p.text for p in block.paragraphs)


def _judgments(block) -> list:
    return [p for p in block.paragraphs
            if p.assertion_class is AssertionClass.PROJECT_JUDGMENT]


def _assert_no_unsupported_judgment(block):
    """任何 PROJECT_JUDGMENT 段落都必须绑定复核记录, 否则契约校验会报错。"""
    assert validate_block(block) == []
    for p in _judgments(block):
        assert p.review_refs, f"{block.section_id} 出现无复核记录的项目判断"


# ============================================================
# N01 — 空 facts 不得产出肯定结论
# ============================================================

EMPTY_RENDERERS = [
    ("sec.conclusion", lambda: sec_11_conclusion.render({}, {}, set(), snapshot={})),
    ("sec.evaluation", lambda: sec_3_evaluation.render_evaluation({}, {}, set())),
    ("sec.evaluation.earthwork_balance",
     lambda: sec_3_evaluation.render_earthwork_balance({}, {}, set())),
    ("sec.topsoil.stripping", lambda: sec_4_topsoil.render_stripping({}, {}, set())),
    ("sec.topsoil.balance", lambda: sec_4_topsoil.render_balance({}, {}, set())),
    ("sec.overview", lambda: sec_0_overview.render({}, {}, set(), snapshot={})),
    ("sec.project_overview.sensitive_areas",
     lambda: sec_2_5_sensitive_areas.render({}, {}, set())),
    ("sec.evaluation.site_selection",
     lambda: sec_3_1_site_selection.render({}, {}, set())),
    ("sec.project_overview.water_soil_zoning",
     lambda: sec_2_3_climate_zoning.render_zoning({}, {}, set())),
]


@pytest.mark.parametrize("section_id,fn", EMPTY_RENDERERS,
                         ids=[s for s, _ in EMPTY_RENDERERS])
def test_n01_empty_facts_produce_no_project_judgment(section_id, fn):
    block = fn()
    assert _judgments(block) == [], \
        f"{section_id} 在空输入下仍输出了本项目判断"
    _assert_no_unsupported_judgment(block)


@pytest.mark.parametrize("section_id,fn", EMPTY_RENDERERS,
                         ids=[s for s, _ in EMPTY_RENDERERS])
def test_n01_empty_facts_report_concrete_gaps(section_id, fn):
    block = fn()
    codes = {f.code for f in block.quality_findings}
    assert codes, f"{section_id} 空输入下没有任何质量诊断"
    assert codes & {"VALUE_MISSING", "ASSERTION_UNSUPPORTED",
                    "SOURCE_UNVERIFIED", "CONDITION_UNKNOWN"}
    # 缺口必须能定位到具体登记字段, 不能只说"资料不全"
    missing = {r for f in block.quality_findings for r in f.missing_input_refs}
    if "VALUE_MISSING" in codes:
        assert missing, f"{section_id} 报了缺失却没说缺哪个字段"


@pytest.mark.parametrize("section_id,fn", EMPTY_RENDERERS,
                         ids=[s for s, _ in EMPTY_RENDERERS])
def test_n01_empty_facts_do_not_emit_positive_markers(section_id, fn):
    """定位性检查: 空输入下不应出现肯定措辞的陈述句。

    待复核说明里可以出现"是否合理"这类**疑问式**表述, 因此只检查
    POSITIVE_MARKERS 这些明确的肯定短语。
    """
    text = _all_text(fn())
    hit = [m for m in POSITIVE_MARKERS if m in text]
    assert hit == [], f"{section_id} 空输入下出现肯定措辞: {hit}"


def test_n01_empty_facts_never_render_a_dash_as_data():
    """缺失不得显示成"—": 读者会把它当成一个已填写的值。"""
    for _, fn in EMPTY_RENDERERS:
        block = fn()
        for p in block.paragraphs:
            assert "—" not in p.text, f"{block.section_id} 用短横线冒充数据"


def test_n01_conclusion_no_longer_claims_sufficient_basis():
    """PROBE-1 的精确回归: 空输入下的结论正文。"""
    block = sec_11_conclusion.render({}, {}, set(), snapshot={})
    text = _all_text(block)
    assert "编制依据充分" not in text
    assert "各项防治指标目标值符合" not in text
    assert any(f.code == "ASSERTION_UNSUPPORTED" for f in block.quality_findings)


def test_n01_earthwork_balance_no_longer_claims_no_borrow_needed():
    """PROBE-1b 的精确回归: 借方缺失不得写成"无需外借土石方"。"""
    block = sec_3_evaluation.render_earthwork_balance({}, {}, set())
    text = _all_text(block)
    assert "无需外借土石方" not in text
    assert "全部用于后期绿化覆土" not in text


def test_n01_topsoil_missing_data_does_not_claim_a_site_survey():
    """资料缺失不得写成"经现场踏勘无可剥离表土"——那是编造的现场调查。"""
    block = sec_4_topsoil.render_stripping({}, {}, set())
    assert "经现场踏勘" not in _all_text(block)


# ============================================================
# N02 — 有规范 ref、无项目证据 → 不准确认项目合规
# ============================================================

def test_n02_normative_refs_alone_do_not_authorize_compliance_claim():
    block = sec_11_conclusion.render({}, {}, set(), snapshot={})
    rules = {r for p in block.paragraphs for r in p.source_rule_refs}
    assert rules, "规范引用仍应保留"
    assert _judgments(block) == [], "仅有规范引用不得支撑项目合规结论"


def test_n02_empty_sensitive_list_cannot_prove_screening_done():
    """空清单 + 规范引用 ≠ 经逐项排查不涉及 (04 文档第 5 节)。"""
    facts = {"field.fact.natural.other_sensitive_areas": [],
             "field.fact.natural.key_prevention_treatment_areas": []}
    block = sec_2_5_sensitive_areas.render(facts, {}, set())
    text = _all_text(block)
    assert "经逐项排查，项目区不涉及" not in text
    assert any(f.code == "SOURCE_UNVERIFIED" for f in block.quality_findings)
    assert _judgments(block) == []


def test_n02_empty_sensitive_list_site_selection_no_compliance_claim():
    facts = {"field.fact.natural.other_sensitive_areas": []}
    block = sec_3_1_site_selection.render(facts, {}, set())
    text = _all_text(block)
    assert "选址符合水土保持相关法律法规要求" not in text
    assert "本项目填报的敏感区清单为空" in text, "应如实复述填报内容"
    assert any(f.code == "SOURCE_UNVERIFIED" for f in block.quality_findings)


def test_n02_empty_key_area_list_cannot_prove_not_in_key_zone():
    """与 sec_2_5 同源的缺陷: 区划清单为空不等于"经核查不涉及重点防治区"。"""
    facts = {"field.fact.natural.water_soil_zoning": "南方红壤区",
             "field.fact.natural.key_prevention_treatment_areas": []}
    block = sec_2_3_climate_zoning.render_zoning(facts, {}, set())
    text = _all_text(block)
    assert "经核查，项目区不涉及国家级" not in text
    assert "核查记录形成前" in text
    assert any(f.code == "SOURCE_UNVERIFIED" for f in block.quality_findings)


def test_n02_missing_key_area_field_is_a_gap_not_a_clearance():
    block = sec_2_3_climate_zoning.render_zoning({}, {}, set())
    text = _all_text(block)
    assert "不涉及国家级水土流失重点预防区" not in text
    assert "未提供国家级水土流失重点预防区" in text


def test_n02_confirmed_review_record_unlocks_the_judgment():
    """有绑定当前输入的复核记录时, 结论才允许输出 —— 且必须留下 review_refs。"""
    facts = {"field.fact.natural.other_sensitive_areas": []}
    h = compute_quality_input_hash(facts, {})
    ledger = ReviewLedger(
        _complete_review("rev.0001", "sec.evaluation.site_selection", h), h)
    block = sec_3_1_site_selection.render(facts, {}, set(), ledger=ledger)
    js = _judgments(block)
    assert len(js) == 1
    assert js[0].review_refs == ["rev.0001"]
    assert validate_block(block) == []


# ============================================================
# N03 — 借方缺失 vs 明确为 0
# ============================================================

_EARTHWORK_BASE = {
    "field.fact.earthwork.excavation": {"value": 8.5, "unit": "万m³"},
    "field.fact.earthwork.fill": {"value": 5.0, "unit": "万m³"},
    "field.fact.earthwork.self_reuse": {"value": 5.0, "unit": "万m³"},
    "field.fact.earthwork.comprehensive_reuse": {"value": 2.0, "unit": "万m³"},
    "field.fact.earthwork.spoil": {"value": 3.5, "unit": "万m³"},
    "field.fact.topsoil.stripable_volume": {"value": 0.3, "unit": "万m³"},
}


def test_n03_missing_borrow_is_reported_as_unknown():
    block = sec_3_evaluation.render_earthwork_balance(dict(_EARTHWORK_BASE), {}, set())
    text = _all_text(block)
    assert "借方数据缺失" in text
    assert "无需外借" not in text
    assert any(f.code == "VALUE_MISSING"
               and "field.fact.earthwork.borrow" in f.missing_input_refs
               for f in block.quality_findings)


def test_n03_explicit_zero_borrow_is_restated_as_filed_value():
    facts = dict(_EARTHWORK_BASE)
    facts["field.fact.earthwork.borrow"] = {"value": 0, "unit": "万m³"}
    block = sec_3_evaluation.render_earthwork_balance(facts, {}, set())
    text = _all_text(block)
    assert "填报借方量为 0" in text
    # 复述填报值, 但不得升级成合规性结论
    assert _judgments(block) == []
    assert "借方有可靠来源" not in text


def test_n03_missing_and_zero_produce_different_text():
    a = _all_text(sec_3_evaluation.render_earthwork_balance(
        dict(_EARTHWORK_BASE), {}, set()))
    facts = dict(_EARTHWORK_BASE)
    facts["field.fact.earthwork.borrow"] = {"value": 0, "unit": "万m³"}
    b = _all_text(sec_3_evaluation.render_earthwork_balance(facts, {}, set()))
    assert a != b


def test_n03_zero_excavation_does_not_divide():
    """挖方为 0 时不得做除法, 也不得写成"利用率—%"。"""
    facts = dict(_EARTHWORK_BASE)
    facts["field.fact.earthwork.excavation"] = {"value": 0, "unit": "万m³"}
    facts["field.fact.earthwork.self_reuse"] = {"value": 0, "unit": "万m³"}
    block = sec_3_evaluation.render_earthwork_balance(facts, {}, set())
    text = _all_text(block)
    assert "利用率不适用" in text
    assert "—%" not in text


# ============================================================
# N07 — 触发/登记 ≠ 已完成/已提供
# ============================================================

def test_n07_triggered_obligations_are_described_as_requirements():
    snapshot = {"required_artifacts": ["art.table.earthwork_balance"] * 3,
                "required_assurances": ["as.signature.responsibility_page"],
                "unknown_obligations": []}
    block = sec_11_conclusion.render({}, {}, {"ob.topsoil.balance_required"},
                                     snapshot=snapshot)
    text = _all_text(block)
    assert "不代表相应内容已经完成或已经提供" in text
    for bad in ("已编制", "已提供", "已满足"):
        assert bad not in text, f"触发不等于{bad}"


def test_n07_artifact_registration_is_not_provision():
    """art.* 登记存在不证明制品已提供。"""
    snapshot = {"required_artifacts": ["art.figure.F_01_location"],
                "required_assurances": [], "unknown_obligations": []}
    block = sec_11_conclusion.render({}, {}, set(), snapshot=snapshot)
    stats = [p for p in block.paragraphs
             if p.paragraph_id == "narr.conclusion.obligation_stats"]
    assert stats
    assert stats[0].assertion_class is AssertionClass.FACT_RESTATEMENT


def test_n07_unknown_obligations_are_surfaced_in_the_conclusion():
    snapshot = {"required_artifacts": [], "required_assurances": [],
                "unknown_obligations": ["ob.disposal_site.site_selection"]}
    block = sec_11_conclusion.render({}, {}, set(), snapshot=snapshot)
    text = _all_text(block)
    assert "无法判定是否适用" in text
    assert "不得按不涉及处理" in text
    assert any(f.code == "CONDITION_UNKNOWN" for f in block.quality_findings)


def test_n07_overview_does_not_speak_for_downstream_gaps():
    snapshot = {"unknown_obligations": ["ob.a", "ob.b"]}
    block = sec_0_overview.render({}, {}, set(), snapshot=snapshot)
    assert "尚未定稿" in _all_text(block)
    assert _judgments(block) == []


# ============================================================
# N08 — 输入变了, 旧复核结论失效
# ============================================================

def _ledger_for(facts: dict, derived: dict, target: str,
                bound_to: dict | None = None) -> ReviewLedger:
    """构造一条**完整**的 CONFIRMED 复核记录, 绑定到 bound_to (默认为当前输入)。"""
    bound = bound_to if bound_to is not None else facts
    qi = _complete_review("rev.n08", target,
                          compute_quality_input_hash(bound, derived))
    return ReviewLedger(qi, compute_quality_input_hash(facts, derived))


def test_n08_confirmed_review_on_current_input_supports_the_judgment():
    facts = dict(_EARTHWORK_BASE)
    facts["field.fact.earthwork.borrow"] = {"value": 0, "unit": "万m³"}
    ledger = _ledger_for(facts, {}, "sec.evaluation.earthwork_balance")
    block = sec_3_evaluation.render_earthwork_balance(facts, {}, set(),
                                                      ledger=ledger)
    assert len(_judgments(block)) == 1
    assert "土石方平衡合理" in _all_text(block)


def test_n08_changing_a_referenced_value_invalidates_the_old_conclusion():
    """字段名不变, 只改值 → 旧复核记录 STALE, 结论必须撤回。"""
    old_facts = dict(_EARTHWORK_BASE)
    old_facts["field.fact.earthwork.borrow"] = {"value": 0, "unit": "万m³"}
    new_facts = dict(old_facts)
    new_facts["field.fact.earthwork.spoil"] = {"value": 9.9, "unit": "万m³"}

    ledger = _ledger_for(new_facts, {}, "sec.evaluation.earthwork_balance",
                         bound_to=old_facts)
    block = sec_3_evaluation.render_earthwork_balance(new_facts, {}, set(),
                                                      ledger=ledger)
    assert _judgments(block) == [], "输入变了, 旧结论不得继续成立"
    assert "土石方平衡合理" not in _all_text(block)
    assert any(f.code == "REVIEW_STALE" for f in block.quality_findings)


def test_n08_stale_review_state_is_reported():
    old = {"field.fact.project.name": "甲"}
    new = {"field.fact.project.name": "乙"}
    ledger = _ledger_for(new, {}, "sec.conclusion", bound_to=old)
    state, rec = ledger.review_state("sec.conclusion")
    assert state.value == "STALE"
    assert rec.review_id == "rev.n08"
    assert ledger.supports_judgment("sec.conclusion") is False


def test_n08_summary_also_goes_stale():
    """汇总同步失效: section 级 review_state 与 finding 都要反映出来。"""
    from cpswc.narrative.contract import NarrativeBlock
    from cpswc.report_quality import evaluate_report_quality

    old = {"field.fact.project.name": "甲"}
    new = {"field.fact.project.name": "乙"}
    qi = _complete_review("rev.n08", "sec.conclusion",
                          compute_quality_input_hash(old, {}))
    current = compute_quality_input_hash(new, {})
    block = NarrativeBlock(section_id="sec.conclusion", title="结论",
                           render_status=RenderStatus.SKELETON)
    summary = evaluate_report_quality(context={}, narrative=[block],
                                      quality_inputs=qi,
                                      current_input_hash=current)
    sq = summary.sections[0]
    assert sq.review_state.value == "STALE"
    assert any(f.code == "REVIEW_STALE" for f in summary.findings)
    assert summary.unreviewed_requirement_count >= 1


def test_n08_review_without_current_hash_cannot_support_judgment():
    """拿不到当前输入指纹时无法证明旧结论仍适用 → 保守失效。"""
    rec = ReviewRecord(review_id="r", target_refs=["sec.x"],
                       input_hash="whatever", verdict="CONFIRMED")
    ledger = ReviewLedger(QualityInputs(review_records=[rec]), None)
    assert ledger.supports_judgment("sec.x") is False


# ============================================================
# SectionEvidence 本身的行为
# ============================================================

def test_evidence_reader_does_not_coerce_missing_to_zero():
    ev = SectionEvidence("sec.x", {}, {})
    rv = ev.quantity("field.fact.earthwork.borrow")
    assert rv.value is None
    assert ev.findings and ev.findings[0].code == "VALUE_MISSING"


def test_evidence_reader_prefers_derived_over_facts():
    ev = SectionEvidence("sec.x", {"field.y": 1}, {"field.y": 2})
    assert ev.raw("field.y").value == 2


def test_gap_paragraph_lists_the_missing_field_ids():
    ev = SectionEvidence("sec.x", {}, {})
    a = ev.quantity("field.fact.a")
    b = ev.quantity("field.fact.b")
    p = ev.gap_paragraph(a, b, lead="缺数据")
    assert "field.fact.a" in p.text and "field.fact.b" in p.text
    assert p.assertion_class is AssertionClass.GAP_STATEMENT
    assert p.unresolved_placeholders == ["field.fact.a", "field.fact.b"]
