"""
test_submission_freeze.py — P0-06 验收测试

对应 04_CONTRACTS_AND_ACCEPTANCE.md 第 9 节:

    F01  只改项目名称, 派生结果相同 → fact_snapshot_hash **变化**
    F02  对同一输入重复 run_project → 原输入深比较不变 (见 test_snapshot_adapter)
    F03  完全相同语义输入不同时间运行 → semantic hash 相同; run 元数据可不同
    F04  规则/模板/来源文件内容变化 → generation_input_hash 变化, 旧审核 STALE
    F05  读取旧冻结包 → 不重写、不伪新版, 显示 legacy 状态
    F06  更改输入后复用旧签署确认 → 拒绝; 草稿提示需重新确认

背景 (P0_BASELINE.md PROBE-8): 原 `freeze_submission` 里那个叫
`fact_snapshot_hash` 的字段散列的其实是 `derived_fields`。实测把项目名换成
完全不同的字符串, 该 hash 一字不变 —— "事实变没变"这个判断从来没成立过。
"""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cpswc.input_hashing import (
    HASH_SCHEMA_VERSION, LEGACY_SCHEMA_MARKER, NonFiniteNumberError,
    canonical_json, describe_hash_schema, directory_digest, fact_snapshot_hash,
    file_digest, generation_input_hash, invalidates_prior_review,
)
from cpswc.paths import SAMPLES_DIR
from cpswc.report_quality import (
    EvidenceRecord, QualityInputs, ReviewLedger, ReviewRecord, ReviewState,
)
from cpswc.runtime import build_snapshot_dict, freeze_submission, run_project


def _sample(name: str = "huizhou_housing_v0") -> dict:
    return json.loads((SAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


# ============================================================
# canonical JSON
# ============================================================

def test_canonical_json_is_key_order_independent():
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})


def test_canonical_json_preserves_ordered_arrays():
    """有序数组保留顺序 —— 只对声明为集合的列表另行排序, 本函数不猜。"""
    assert canonical_json([1, 2, 3]) != canonical_json([3, 2, 1])


def test_canonical_json_distinguishes_bool_from_int():
    assert canonical_json({"x": True}) != canonical_json({"x": 1})
    assert canonical_json({"x": False}) != canonical_json({"x": 0})


def test_canonical_json_normalizes_integral_floats():
    """3.0 与 3 不应产生不同 hash。"""
    assert canonical_json({"x": 3.0}) == canonical_json({"x": 3})


def test_canonical_json_keeps_null_distinct_from_missing():
    assert canonical_json({"x": None}) != canonical_json({})


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_canonical_json_rejects_non_finite(bad):
    """NaN / inf 不是确定的值, 不能参与内容寻址。"""
    with pytest.raises(NonFiniteNumberError):
        canonical_json({"x": bad})


def test_non_finite_error_names_the_path():
    with pytest.raises(NonFiniteNumberError) as e:
        canonical_json({"a": {"b": [1, float("nan")]}})
    assert "a.b[1]" in str(e.value)


# ============================================================
# F01 — 只改项目名称
# ============================================================

def test_f01_changing_only_the_project_name_changes_the_fact_hash():
    """PROBE-8 的精确回归。"""
    a = _sample()
    b = _sample()
    b["facts"]["field.fact.project.name"] = "XX 完全不同的项目名称 XX"

    sa, sb = run_project(a), run_project(b)
    assert sa.derived_fields == sb.derived_fields, "派生结果确实相同"
    assert sa.fact_snapshot_hash != sb.fact_snapshot_hash, \
        "事实变了, fact_snapshot_hash 必须变"


def test_f01_frozen_record_carries_the_corrected_fact_hash():
    a = _sample()
    b = _sample()
    b["facts"]["field.fact.project.name"] = "另一个项目"
    fa, fb = freeze_submission(run_project(a)), freeze_submission(run_project(b))
    assert fa.fact_snapshot_hash != fb.fact_snapshot_hash


def test_f01_fact_hash_no_longer_hashes_derived_fields():
    """旧实现散列的是 derived_fields。现在两者必须解耦。"""
    facts_only = fact_snapshot_hash({"field.fact.project.name": "甲"})
    same_facts_again = fact_snapshot_hash({"field.fact.project.name": "甲"})
    other = fact_snapshot_hash({"field.fact.project.name": "乙"})
    assert facts_only == same_facts_again
    assert facts_only != other


def test_f01_empty_and_missing_facts_differ():
    assert fact_snapshot_hash({}) != fact_snapshot_hash({"x": None})


# ============================================================
# F03 — 同语义输入, 不同时间
# ============================================================

def test_f03_semantic_hashes_are_stable_across_runs():
    pi = _sample()
    a, b = run_project(copy.deepcopy(pi)), run_project(copy.deepcopy(pi))
    assert a.fact_snapshot_hash == b.fact_snapshot_hash
    assert a.generation_input_hash == b.generation_input_hash


def test_f03_run_metadata_may_differ():
    """运行时间与 run ID 是审计元数据, 允许不同 —— 但不得进语义 hash。"""
    pi = _sample()
    a, b = run_project(copy.deepcopy(pi)), run_project(copy.deepcopy(pi))
    assert a.snapshot_id != b.snapshot_id or a.timestamp != b.timestamp
    assert a.generation_input_hash == b.generation_input_hash


def test_f03_timestamp_is_absent_from_the_semantic_payload():
    h1 = generation_input_hash(facts={"a": 1}, ruleset="r")
    h2 = generation_input_hash(facts={"a": 1}, ruleset="r")
    assert h1 == h2


def test_f03_content_hash_may_change_but_semantic_hash_may_not():
    """content_hash 是文件完整性 (含时间戳), 语义 hash 才是判据。"""
    pi = _sample()
    fa = freeze_submission(run_project(copy.deepcopy(pi)))
    fb = freeze_submission(run_project(copy.deepcopy(pi)))
    assert fa.content_hash != fb.content_hash        # 含 timestamp
    assert fa.generation_input_hash == fb.generation_input_hash


# ============================================================
# F04 — 规则 / 模板 / 来源内容变化
# ============================================================

def test_f04_generation_hash_covers_more_than_facts():
    base = dict(facts={"a": 1})
    assert (generation_input_hash(**base, ruleset="v1")
            != generation_input_hash(**base, ruleset="v2"))
    assert (generation_input_hash(**base, input_digests={"registries": "x"})
            != generation_input_hash(**base, input_digests={"registries": "y"}))
    assert (generation_input_hash(**base, profile={"species": "报告书"})
            != generation_input_hash(**base, profile={"species": "报告表"}))
    assert (generation_input_hash(**base, calculator_versions={"c": "1"})
            != generation_input_hash(**base, calculator_versions={"c": "2"}))


def test_f04_source_layer_choice_is_part_of_the_input():
    """同一个值取自 CALCULATED 还是 PRE_STORED, 结论可能不同。"""
    assert (generation_input_hash(facts={"a": 1}, source_map={"a": "CALCULATED"})
            != generation_input_hash(facts={"a": 1},
                                     source_map={"a": "PRE_STORED_DERIVED"}))


def test_f04_file_content_change_changes_the_digest(tmp_path):
    """文件名与数值都不变, 只改内容 → 摘要必须变。"""
    f = tmp_path / "rule.yaml"
    f.write_text("a: 1\n", encoding="utf-8")
    first = file_digest(f)
    f.write_text("a: 1  # 增加一条注释\n", encoding="utf-8")
    assert file_digest(f) != first


def test_f04_missing_source_is_reported_not_silently_zero():
    assert file_digest(Path("/nonexistent/whatever.yaml")) == "MISSING"
    assert directory_digest(Path("/nonexistent/dir")) == "MISSING"


def test_f04_directory_digest_changes_when_any_file_changes(tmp_path):
    (tmp_path / "a.yaml").write_text("x: 1\n", encoding="utf-8")
    (tmp_path / "b.yaml").write_text("y: 2\n", encoding="utf-8")
    first = directory_digest(tmp_path)
    (tmp_path / "b.yaml").write_text("y: 3\n", encoding="utf-8")
    assert directory_digest(tmp_path) != first


def test_f04_real_run_records_the_consumed_source_digests():
    s = run_project(_sample())
    for key in ("registries", "governance", "narrative_templates"):
        assert s.input_digests[key] not in ("", "MISSING")


def test_f04_changed_input_invalidates_prior_review():
    assert invalidates_prior_review("abc", "def") is True
    assert invalidates_prior_review("abc", "abc") is False


def test_f04_missing_hash_on_either_side_invalidates():
    """无法证明仍然适用, 就不能当作仍然适用。"""
    assert invalidates_prior_review(None, "abc") is True
    assert invalidates_prior_review("abc", None) is True
    assert invalidates_prior_review(None, None) is True


# ============================================================
# F05 — 旧冻结包
# ============================================================

def test_f05_legacy_record_is_flagged_not_recomputed():
    legacy = {"content_hash": "x" * 64, "fact_snapshot_hash": "y" * 64,
              "frozen_at": "2026-04-11T00:00:00+00:00"}
    d = describe_hash_schema(legacy)
    assert d["is_legacy"] is True
    assert d["hash_schema_version"] == LEGACY_SCHEMA_MARKER
    assert d["generation_input_hash_available"] is False
    assert "只读" in d["note"]
    # 原记录不得被改写
    assert legacy["fact_snapshot_hash"] == "y" * 64


def test_f05_legacy_note_explains_why_the_old_hash_is_untrustworthy():
    d = describe_hash_schema({})
    assert "derived_fields" in d["note"]


def test_f05_current_record_is_not_legacy():
    f = freeze_submission(run_project(_sample()))
    d = describe_hash_schema({
        "hash_schema_version": f.hash_schema_version,
        "generation_input_hash": f.generation_input_hash,
    })
    assert d["is_legacy"] is False
    assert d["generation_input_hash_available"] is True


def test_f05_a_different_schema_version_is_legacy_too():
    d = describe_hash_schema({"hash_schema_version": "cpswc_hash_v0"})
    assert d["is_legacy"] is True
    assert HASH_SCHEMA_VERSION in d["note"]


def test_f05_freeze_states_it_is_not_professional_approval():
    """创建 dataclass 不等于"专业校审通过"。"""
    f = freeze_submission(run_project(_sample()))
    assert "不表示" in f.lifecycle_freeze_note


# ============================================================
# F06 — 输入变了, 旧确认不得复用
# ============================================================

def _complete_review(target: str, bound_hash: str) -> QualityInputs:
    return QualityInputs(
        evidence_records=[EvidenceRecord(
            evidence_id="ev.f06", target_refs=[target],
            locator="fixture.synthetic 合成夹具")],
        review_records=[ReviewRecord(
            review_id="rev.f06", target_refs=[target], input_hash=bound_hash,
            verdict="CONFIRMED", reviewer_ref="fixture.synthetic.reviewer",
            reviewed_at="2026-09-21", evidence_refs=["ev.f06"])])


def test_f06_review_bound_to_current_generation_hash_holds():
    pi = _sample()
    d = build_snapshot_dict(run_project(copy.deepcopy(pi)), pi)
    ledger = ReviewLedger(_complete_review("sec.conclusion",
                                           d["generation_input_hash"]),
                          d["generation_input_hash"])
    assert ledger.review_state("sec.conclusion")[0] is ReviewState.CONFIRMED
    assert ledger.supports_judgment("sec.conclusion") is True


def test_f06_changing_a_fact_invalidates_the_prior_confirmation():
    old = _sample()
    new = _sample()
    new["facts"]["field.fact.project.name"] = "改过名字的项目"

    d_old = build_snapshot_dict(run_project(copy.deepcopy(old)), old)
    d_new = build_snapshot_dict(run_project(copy.deepcopy(new)), new)
    assert d_old["generation_input_hash"] != d_new["generation_input_hash"]

    ledger = ReviewLedger(_complete_review("sec.conclusion",
                                           d_old["generation_input_hash"]),
                          d_new["generation_input_hash"])
    assert ledger.review_state("sec.conclusion")[0] is ReviewState.STALE
    assert ledger.supports_judgment("sec.conclusion") is False
    f = ledger.stale_finding("sec.conclusion")
    assert f is not None and f.code == "REVIEW_STALE"


def test_f06_narrative_withdraws_the_conclusion_after_input_change():
    """草稿要提示需重新确认 —— 结论段自动撤回。"""
    from cpswc.narrative.contract import AssertionClass
    from cpswc.narrative.templates.sec_11_conclusion import render

    old = _sample()
    new = _sample()
    new["facts"]["field.fact.project.name"] = "改过名字的项目"
    d_old = build_snapshot_dict(run_project(copy.deepcopy(old)), old)
    d_new = build_snapshot_dict(run_project(copy.deepcopy(new)), new)

    ledger = ReviewLedger(_complete_review("sec.conclusion",
                                           d_old["generation_input_hash"]),
                          d_new["generation_input_hash"])
    block = render(d_new["_original_facts"], d_new["derived_fields"], set(),
                   snapshot=d_new, ledger=ledger)
    judgments = [p for p in block.paragraphs
                 if p.assertion_class is AssertionClass.PROJECT_JUDGMENT]
    assert judgments == []
    assert any(f.code == "REVIEW_STALE" for f in block.quality_findings)


def test_f06_ledger_prefers_generation_hash_over_the_provisional_one():
    """A 批的 quality_input_hash 只是兜底; 有 generation_input_hash 就用它。"""
    from cpswc.report_quality import ledger_from_snapshot

    snap = {"generation_input_hash": "GEN", "quality_input_hash": "QUAL",
            "_original_facts": {}, "derived_fields": {}}
    assert ledger_from_snapshot(snap).current_input_hash == "GEN"


def test_f06_ledger_falls_back_when_generation_hash_absent():
    from cpswc.report_quality import ledger_from_snapshot

    snap = {"quality_input_hash": "QUAL", "_original_facts": {},
            "derived_fields": {}}
    assert ledger_from_snapshot(snap).current_input_hash == "QUAL"


# ============================================================
# 冻结记录的完整性
# ============================================================

def test_frozen_record_exposes_both_hashes_and_the_schema():
    f = freeze_submission(run_project(_sample()))
    assert f.hash_schema_version == HASH_SCHEMA_VERSION
    assert len(f.fact_snapshot_hash) == 64
    assert len(f.generation_input_hash) == 64
    assert f.fact_snapshot_hash != f.generation_input_hash


def test_snapshot_dict_carries_the_hashes_to_consumers():
    pi = _sample()
    d = build_snapshot_dict(run_project(copy.deepcopy(pi)), pi)
    assert d["hash_schema_version"] == HASH_SCHEMA_VERSION
    assert d["generation_input_hash"]
    assert d["fact_snapshot_hash"]
