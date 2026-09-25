"""
test_rule_registry.py — RuleRegistry 的验收

对应 DECISION_LOG 条目 015 清点出的第一号缺口: 53 个 `rule.*` 依据 ID,
已登记标题 0 个。报告里每句"依据 XXX"都指向空壳。

本文件盯的不是"登记了多少", 而是**"登记的东西是不是真的"**:

  · VERIFIED_TEXT 必须真有原文, DECLARED 必须**没有**原文
    —— 看起来像证据的东西, 比没有证据更危险
  · source_file 必须真实存在 —— 登记一个查不到的出处等于伪造脚注
  · 未登记必须如实报 UNREGISTERED, 不许靠命名空间猜
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cpswc.rule_registry import (  # noqa: E402
    DECLARED, UNREGISTERED, VERIFIED_TEXT, lint_rule_registry,
    load_rule_registry, resolve_rule, summarize_rule_coverage)


@pytest.fixture(scope="module")
def registry() -> dict:
    return load_rule_registry()


# ============================================================
# 1. 自检
# ============================================================

def test_registry_passes_its_own_lint(registry):
    assert lint_rule_registry(registry) == []


def test_every_declared_source_file_exists(registry):
    """登记一个查不到的出处, 比不登记更糟 —— 它看起来像证据。"""
    for rid in registry["rules"]:
        src = resolve_rule(rid, registry)["source_file"]
        assert src, rid
        assert (ROOT / src).exists(), f"{rid}: {src} 不存在"


def test_verified_entries_carry_real_quoted_text(registry):
    for rid, e in registry["rules"].items():
        if e.get("verification_status") == VERIFIED_TEXT:
            r = resolve_rule(rid, registry)
            assert r["quoted_text"].strip(), rid
            assert r["text_verified"] is True, rid
            assert r["verified_at"], f"{rid}: 必须写 verified_at"


def test_declared_entries_never_carry_quoted_text(registry):
    """DECLARED 贴原文 = 没核对却声称核对过。这是本注册表最要命的一种错。"""
    for rid, e in registry["rules"].items():
        if e.get("verification_status") == DECLARED:
            assert not (e.get("quoted_text") or "").strip(), rid
            assert resolve_rule(rid, registry)["text_verified"] is False, rid


# ============================================================
# 2. lint 必须拦得住伪造
# ============================================================

def _mutate(registry: dict, rid: str, **kw) -> dict:
    rules = {k: dict(v) for k, v in registry["rules"].items()}
    rules[rid].update(kw)
    return dict(registry, rules=rules)


def test_lint_catches_verified_without_text(registry):
    rid = next(r for r, e in registry["rules"].items()
               if e.get("verification_status") == VERIFIED_TEXT)
    bad = _mutate(registry, rid, quoted_text="")
    assert any("没有 quoted_text" in p for p in lint_rule_registry(bad))


def test_lint_catches_declared_with_text(registry):
    rid = next(r for r, e in registry["rules"].items()
               if e.get("verification_status") == DECLARED)
    bad = _mutate(registry, rid, quoted_text="第 X 条 伪造的原文")
    assert any("DECLARED 不得带 quoted_text" in p for p in lint_rule_registry(bad))


def test_lint_catches_missing_source_file(registry):
    rid = next(iter(registry["rules"]))
    bad = _mutate(registry, rid, source_file="docs/不存在的文件.pdf",
                  parent_rule_id=None)
    assert any("source_file 不存在" in p for p in lint_rule_registry(bad))


def test_lint_catches_dangling_parent(registry):
    rid = next(r for r, e in registry["rules"].items() if e.get("parent_rule_id"))
    bad = _mutate(registry, rid, parent_rule_id="rule.does.not.exist")
    assert any("不存在" in p for p in lint_rule_registry(bad))


# ============================================================
# 3. 解析
# ============================================================

def test_unknown_id_resolves_to_unregistered_not_an_error(registry):
    """未登记本身就是要显示的信息, 不是异常。"""
    r = resolve_rule("rule.completely.made.up", registry)
    assert r["registered"] is False
    assert r["verification_status"] == UNREGISTERED
    assert r["text_verified"] is False
    assert r["document_title"] == ""


def test_t2026_namespace_stays_unregistered(registry):
    """`rule.t2026.*` 刻意不登记 —— ObligationSet 没声明单条义务的来源,
    前缀不构成证据。有人哪天"顺手"按前缀批量补上, 这条会拦住。"""
    r = resolve_rule("rule.t2026.disposal_site_location_map", registry)
    assert r["registered"] is False


def test_child_inherits_document_but_not_verification(registry):
    """子条继承文件信息, **不继承核验状态** —— 父条核过不代表子条核过。"""
    child = resolve_rule("rule.gb_t_50434_2018.table_4_0_2_5", registry)
    parent = resolve_rule("rule.gb_t_50434_2018.chapter_4", registry)
    assert child["document_number"] == parent["document_number"]
    assert child["source_file"] == parent["source_file"]
    assert child["clause_ref"] != parent["clause_ref"]
    assert child["verification_status"] == DECLARED


def test_known_defects_are_recorded(registry):
    """两处引用缺陷必须留在册: 2026 模板没有第 11 章; 效益分析已迁到 9.2。"""
    s11 = resolve_rule("rule.template_2026.section_11", registry)
    assert s11["defect"] == "NONEXISTENT_CLAUSE"
    assert "没有第 11 章" in s11["defect_note"]
    s7 = resolve_rule("rule.template_2026.section_7", registry)
    assert s7["defect"] == "STALE_CITER"


# ============================================================
# 4. 覆盖统计
# ============================================================

def test_coverage_counts_add_up(registry):
    ids = list(registry["rules"]) + ["rule.t2026.whatever", "rule.nope"]
    c = summarize_rule_coverage(ids, registry)
    assert c["cited_total"] == len(ids)
    assert c["text_verified"] + c["declared"] + c["unregistered"] == len(ids)
    assert c["unregistered"] == 2


def test_coverage_gives_no_single_percentage(registry):
    """**不给单一覆盖率。** 压成一个数会抹掉"定位到文件"和"核对过原文"的区别。"""
    c = summarize_rule_coverage(list(registry["rules"]), registry)
    assert not any("percent" in k or "ratio" in k or "coverage" in k
                   for k in c), c.keys()
