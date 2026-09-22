"""
test_report_structure.py — P0-05 验收测试

对应 04_CONTRACTS_AND_ACCEPTANCE.md 第 9 节:

    R01  报告书 2026 结构      → 10 章主体, 关键位置正确, 不存在伪 section_11 依据
    R02  模板未实现必需叶子内容 → 仍进要求清单及缺口, 不从分母删除
    R03  条件章不适用 / 未知   → 前者按策略省略且不前移; 后者不能伪 N/A
    R04  Species 缺失 / 报告表暂不支持 → 显示未知 / 格式未就绪
    R05  旧编号审查引用与新显示映射 → stable ID 保留, 旧语境可辨, 无悬空静默丢失

来源核验 (决议 8 双锚):
  本文件断言的章节结构取自 `governance/ReportContentRequirements_v1.yaml`,
  该文件的结构逐页取自本地扫描原件
  `docs/水利部办公厅关于印发生产建设项目水土保持方案编制模板的通知.pdf`
  (sha256 57a682a1…, 28 页, 附件 1 位于第 3—22 页),
  并与昌都市水利局公开 HTML 全文交叉核对 —— 章节结构逐条一致。

  **文号以原件为准: 办水保函〔2026〕232 号。** 该 HTML 页面标注为
  "办水保函〔2026〕23号"(少一位), 属页面笔误。
"""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.narrative.projection import (
    _SECTION_CONDITIONALS, _SECTION_SPECIAL_TOPICS, project_narrative,
)
from cpswc.paths import GOVERNANCE_DIR
from cpswc.report_quality import (
    Applicability, ContentRequirementSet, evaluate_report_quality,
    load_content_requirements,
)

REQ_PATH = GOVERNANCE_DIR / "ReportContentRequirements_v1.yaml"
_DOC = yaml.safe_load(REQ_PATH.read_text(encoding="utf-8"))
REQS = load_content_requirements()


# ============================================================
# R01 — 2026 结构与关键位置
# ============================================================

def test_r01_requirements_are_loadable_and_verified():
    assert REQS is not None
    assert REQS.verified is True
    assert REQS.source_ref == "办水保函〔2026〕232号"


def test_r01_source_records_both_primary_and_cross_check():
    """决议 8 双锚: 要有责任署名/时间/版本, 且记录交叉核对结果。"""
    src = _DOC["source"]
    assert src["issuing_authority"] == "中华人民共和国水利部办公厅"
    assert src["issued_at"] == "2026-04-03"
    assert src["primary_evidence"]["content_sha256"].startswith("57a682a1")
    assert src["primary_evidence"]["attachment_1_pages"] == "3-22"
    assert src["cross_check"]["structure_match"] == "identical"
    assert "23号" in src["cross_check"]["discrepancy"], "网页文号笔误必须留痕"


def test_r01_ocr_is_not_treated_as_normative_text():
    assert "OCR 仅用于定位" in _DOC["source"]["ocr_policy"]


def test_r01_main_body_has_exactly_ten_chapters():
    chapters = [r for r in _DOC["requirements"]
                if "." not in str(r["display_number"])
                and str(r["display_number"]).isdigit()]
    numbers = sorted(int(r["display_number"]) for r in chapters)
    assert numbers == list(range(1, 11)), f"主体章应为 1—10, 实为 {numbers}"


def test_r01_chapter_ten_is_the_last_body_chapter():
    ten = next(r for r in _DOC["requirements"] if r["display_number"] == "10")
    assert ten["title"] == "水土保持管理"
    assert ten["stable_id"] == "sec.management"


@pytest.mark.parametrize("stable_id,expected_display,label", [
    ("sec.conclusion", "1.9", "结论"),
    ("sec.soil_loss_prevention.design_horizon", "7.2", "设计水平年"),
    ("sec.soil_loss_prevention.targets", "7.3.2", "防治目标"),
    ("sec.soil_loss_prevention.benefit_analysis", "9.2", "效益分析"),
    ("sec.management", "10", "水土保持管理"),
])
def test_r01_key_positions(stable_id, expected_display, label):
    """用户在 B 批指示中要求确认的五处映射, 逐条锁定。"""
    assert REQS.display_number_of(stable_id) == expected_display, label


def test_r01_no_chapter_eleven_anywhere():
    """2026 模板没有第 11 章。任何"section_11"式依据都不成立。"""
    for r in _DOC["requirements"]:
        assert not str(r["display_number"]).startswith("11"), r


def test_r01_conclusion_is_a_leaf_of_chapter_one():
    conclusion = next(r for r in _DOC["requirements"]
                      if r["stable_id"] == "sec.conclusion")
    assert conclusion["display_number"] == "1.9"
    assert conclusion["is_leaf"] is True


def test_r01_benefit_analysis_moved_across_chapters():
    """效益分析从第 7 章跨到第 9 章 —— 这是跨章迁移, 必须显式登记。"""
    m = next(m for m in REQS.migrations
             if m["stable_id"] == "sec.soil_loss_prevention.benefit_analysis")
    assert m["old_display"] == "7.5"
    assert m["new_display"] == "9.2"
    assert m.get("cross_chapter") is True


def test_r01_compensation_fee_no_longer_occupies_9_2():
    """9.2 是效益分析; 补偿费属 9.1 的估算成果。"""
    assert REQS.display_number_of(
        "sec.investment_estimation.compensation_fee") != "9.2"
    m = next(m for m in REQS.migrations
             if m["stable_id"] == "sec.investment_estimation.compensation_fee")
    assert m["new_display"] == "9.1.2"


# ============================================================
# R02 — 未实现的必需内容仍进分母
# ============================================================

def test_r02_unimplemented_requirements_stay_in_the_list():
    unimplemented = [r for r in REQS.requirements
                     if r.is_leaf and not r.implemented]
    assert len(unimplemented) >= 30, "未实现的必需叶子内容不得从清单里消失"


def test_r02_unimplemented_counts_into_the_denominator():
    summary = evaluate_report_quality(context={}, narrative=[],
                                      content_requirements=REQS)
    assert summary.applicable_leaf_count == REQS.leaf_count
    assert summary.unimplemented_leaf_count >= 30
    assert summary.complete_leaf_count == 0


def test_r02_real_project_coverage_is_honest():
    """惠州样本: 旧口径 38 个 FULL 看起来接近完成; 对照 2026 模板的真实分母
    是 0/64 已确认完成, 其中 38 项根本没实现。"""
    import json

    from cpswc.paths import SAMPLES_DIR
    from cpswc.runtime import build_snapshot_dict, run_project

    pi = json.loads((SAMPLES_DIR / "huizhou_housing_v0.json").read_text(encoding="utf-8"))
    d = build_snapshot_dict(run_project(pi), pi)
    result = project_narrative(d)
    summary = evaluate_report_quality(
        context=d, narrative=result, content_requirements=REQS,
        current_input_hash=d["quality_input_hash"])

    assert summary.coverage_state == "measured"
    assert summary.applicable_leaf_count == 64
    assert summary.complete_leaf_count == 0
    assert summary.unimplemented_leaf_count == 38
    assert "100%" not in summary.coverage_display()
    # 旧口径的"已渲染块数"仍在, 但它不是完成度
    assert summary.rendered_block_count > summary.complete_leaf_count


def test_r02_unimplemented_produces_blocking_findings():
    summary = evaluate_report_quality(context={}, narrative=[],
                                      content_requirements=REQS)
    blocking = [f for f in summary.findings
                if f.code == "CONTENT_INCOMPLETE" and f.severity.value == "BLOCK"]
    assert len(blocking) >= 30


# ============================================================
# R03 — 条件章: 不适用 vs 未知
# ============================================================

def test_r03_conditional_requirements_declare_their_condition():
    conditional = [r for r in _DOC["requirements"]
                   if r.get("applicability") == "conditional"]
    assert conditional
    for r in conditional:
        assert r.get("condition_note"), f"{r['id']} 未说明适用条件"


def test_r03_disposal_chapter_is_conditional_per_the_template():
    ch5 = next(r for r in _DOC["requirements"] if r["display_number"] == "5")
    assert ch5["applicability"] == "conditional"
    assert "不设弃渣场" in ch5["condition_note"]


def test_r03_unknown_applicability_is_not_rendered_as_not_applicable():
    result = project_narrative({
        "_original_facts": {}, "derived_fields": {},
        "triggered_obligations": [],
        "unknown_obligations": ["ob.disposal_site.site_selection"],
    })
    blk = {b.section_id: b for b in result.blocks}["sec.disposal_site"]
    assert blk.applicability is Applicability.UNKNOWN
    assert blk.render_status.value != "not_applicable"


def test_r03_site_selection_is_routine_not_a_special_topic_gate():
    """3.1 是常规评价内容; 不可避让论证是节内专题, 不是整节开关。"""
    assert _SECTION_CONDITIONALS["sec.evaluation.site_selection"] is None
    assert (_SECTION_SPECIAL_TOPICS["sec.evaluation.site_selection"]
            == "ob.unavoidability.redline_conflict")
    req = next(r for r in _DOC["requirements"]
               if r["stable_id"] == "sec.evaluation.site_selection")
    assert req["applicability"] == "always"
    assert "常规评价内容" in req["note"]


def test_r03_not_applicable_does_not_shift_numbering():
    """原章号不前移: 不适用的 5 章不会让 6 章变成 5 章。"""
    five = REQS.display_number_of("sec.disposal_site")
    six = REQS.display_number_of("sec.soil_loss_analysis")
    assert five == "5" and six == "6"


# ============================================================
# R04 — Species
# ============================================================

def test_r04_requirements_declare_their_species():
    assert _DOC["species"] == "报告书"


def test_r04_report_form_species_has_no_requirement_set():
    """报告表是另一套结构 (附件 3), 本清单不覆盖 —— 不得拿报告书的清单顶替。"""
    assert load_content_requirements(species="报告表") is None


def test_r04_unknown_species_yields_unknown_coverage():
    """没有可用清单时 coverage=unknown, 不显示 100% (验收 Q02)。"""
    summary = evaluate_report_quality(context={}, narrative=[],
                                      content_requirements=None)
    assert summary.coverage_state == "unknown"
    assert summary.content_coverage is None
    assert "100%" not in summary.coverage_display()


# ============================================================
# R05 — 旧编号映射与悬空
# ============================================================

def test_r05_every_registered_section_has_a_home():
    """projection 里每个 stable ID 都要能落位 —— 要么是要求, 要么被吸收。"""
    mapped = {r.section_id for r in REQS.requirements if r.section_id}
    mapped |= {a["stable_id"] for a in REQS.absorbed}
    orphans = sorted(set(_SECTION_CONDITIONALS) - mapped)
    assert orphans == [], f"未落位的 stable ID: {orphans}"


def test_r05_requirements_reference_no_unknown_section():
    known = set(_SECTION_CONDITIONALS)
    referenced = {r.section_id for r in REQS.requirements if r.section_id}
    referenced |= {a["stable_id"] for a in REQS.absorbed}
    assert referenced <= known


def test_r05_migrations_keep_the_stable_id_unchanged():
    """显示位置可以变, ID 不许改名。"""
    known = set(_SECTION_CONDITIONALS)
    for m in REQS.migrations:
        assert m["stable_id"] in known, f"{m['stable_id']} 被改名或已消失"
        assert m["old_display"] != m["new_display"]


def test_r05_migrations_record_the_old_review_context():
    """按旧编号写的审查意见要能辨认出它属于哪一版编号语境。"""
    for m in REQS.migrations:
        assert m.get("reason"), m["stable_id"]
    conclusion = next(m for m in REQS.migrations
                      if m["stable_id"] == "sec.conclusion")
    assert conclusion["old_display"] == "11"
    assert "v0.1" in conclusion["review_reference_note"]


def test_r05_absorbed_ids_say_where_they_went():
    assert len(REQS.absorbed) == 3
    for a in REQS.absorbed:
        assert a.get("absorbed_into"), a["stable_id"]
        assert a.get("reason"), a["stable_id"]
        assert a.get("status") == "ACTIVE_CONTENT"


def test_r05_no_duplicate_requirement_ids():
    ids = [r["id"] for r in _DOC["requirements"]]
    assert len(ids) == len(set(ids))


def test_r05_one_stable_id_never_maps_to_two_conflicting_nodes():
    """严禁同一 ID 出现两个相互冲突的节点 (04 文档第 6 节)。"""
    seen: dict[str, str] = {}
    for r in _DOC["requirements"]:
        sid = r.get("stable_id")
        if not sid:
            continue
        assert sid not in seen, f"{sid} 同时绑定 {seen.get(sid)} 与 {r['display_number']}"
        seen[sid] = str(r["display_number"])


def test_r05_old_display_numbers_resolve_to_a_current_section():
    """拿 v0.1 的旧编号来定位, 仍要能找到当前的 section。"""
    by_old = {m["old_display"]: m["stable_id"] for m in REQS.migrations}
    assert by_old["11"] == "sec.conclusion"
    assert by_old["7.5"] == "sec.soil_loss_prevention.benefit_analysis"
    for stable_id in by_old.values():
        assert REQS.display_number_of(stable_id)
