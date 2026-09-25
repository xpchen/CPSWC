"""
test_frontend_payload.py — F-1A/F-2 payload 管线的 Python 级验收

浏览器级验收 (tests/browser/test_data_modes.py) 验的是"页面上显示了什么";
这里验的是"payload 里装的是不是后端的真结论"。两者缺一不可 ——
页面可以显示对的东西却装错的数据, payload 也可以装对却渲染不出来。

硬要求 (来自 FRONTEND_WIRING_PLAN.md v1.1 验收清单):
  1. payload 的值必须与 build_snapshot_dict / project_fields **完全一致**,
     生成器不得重新判定值状态;
  2. schema 校验必须挡住残缺 payload, 不得放行;
  3. 落盘必须原子, 中途失败不留半成品;
  4. 路径按 project-code / generation-input-hash 分开, 互不覆盖;
  5. 单文件 bundle 里的 shell_digest meta 必须现场按壳算, 不能抄 payload。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cpswc.frontend_payload import (  # noqa: E402
    build_payload, render_standalone_html, shell_digest, validate_payload,
    write_bundle)
from cpswc.paths import FRONTEND_DIR, SAMPLES_DIR  # noqa: E402
from cpswc.runtime import (  # noqa: E402
    build_snapshot_dict, load_all_registries, run_project)
from cpswc.snapshot_adapter import make_build_context  # noqa: E402

# 只有项目输入才能生成快照。审查意见文档 (CPSWC_ReviewComment_v0) 不是项目,
# 喂进来必须报错 —— 见 test_non_project_input_is_rejected。
def _is_project_input(path: Path) -> bool:
    d = json.loads(path.read_text(encoding="utf-8"))
    return bool(d.get("facts") or d.get("project"))


ALL_SAMPLES = sorted(SAMPLES_DIR.glob("*.json"))
SAMPLES = [p for p in ALL_SAMPLES if _is_project_input(p)]
NON_PROJECT_SAMPLES = [p for p in ALL_SAMPLES if not _is_project_input(p)]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module", params=[p.name for p in SAMPLES])
def sample_payload(request) -> dict:
    return build_payload(_load(SAMPLES_DIR / request.param))


# ============================================================
# 1. 与后端结论一致 —— 生成器不得重新判定
# ============================================================

def test_every_sample_builds(sample_payload):
    assert validate_payload(sample_payload) == []


def test_project_identity_matches_snapshot(sample_payload):
    """项目名/编码来自 snapshot, 不是 payload 生成器自己拼的。"""
    assert sample_payload["project"]["name"]
    assert sample_payload["data_mode"] == "PROJECT_SNAPSHOT"


@pytest.mark.parametrize("path", NON_PROJECT_SAMPLES,
                         ids=[p.name for p in NON_PROJECT_SAMPLES])
def test_non_project_input_is_rejected(path):
    """喂错文件必须立刻炸。

    实测: 审查意见文档一路畅通, 最后产出项目名、编码全空的 bundle ——
    顶栏"项目快照"下挂一片空白, 比直接报错危险得多。
    """
    with pytest.raises(ValueError, match="项目"):
        build_payload(_load(path))


def test_validate_rejects_blank_project_name(sample_payload):
    broken = dict(sample_payload, project=dict(sample_payload["project"], name=""))
    assert any("project.name" in p for p in validate_payload(broken))


@pytest.mark.parametrize("name", [p.name for p in SAMPLES])
def test_facts_are_verbatim_from_project_fields(name):
    """payload.facts 必须逐字段等于 BuildContext.project_fields()。

    这是最关键的一条: 前端和 payload 生成器**都不得重新解析值状态**。
    一旦这里出现"生成器顺手补了个默认值", 界面上的诚实就全是假的。
    """
    pi = _load(SAMPLES_DIR / name)
    snap = run_project(pi)
    expected = make_build_context(
        pi, snap, load_all_registries(),
        enriched_views=snap.enriched_views).project_fields()
    got = build_payload(pi)["facts"]
    assert got == expected


@pytest.mark.parametrize("name", [p.name for p in SAMPLES])
def test_hashes_match_the_snapshot(name):
    pi = _load(SAMPLES_DIR / name)
    snapshot = build_snapshot_dict(run_project(pi), pi)
    payload = build_payload(pi)
    assert payload["hashes"]["fact_snapshot_hash"] == snapshot["fact_snapshot_hash"]
    assert payload["hashes"]["generation_input_hash"] == snapshot["generation_input_hash"]


@pytest.mark.parametrize("name", [p.name for p in SAMPLES])
def test_same_input_gives_same_hash(name):
    """同输入同 hash —— 否则按 hash 分目录就没有意义。"""
    pi = _load(SAMPLES_DIR / name)
    a, b = build_payload(pi), build_payload(pi)
    assert a["hashes"] == b["hashes"]
    assert a["facts"] == b["facts"]


def test_no_field_claims_a_value_it_does_not_have(sample_payload):
    """非 PRESENT 的字段不得带 value —— 界面照着 value 显示就会说谎。"""
    for f in sample_payload["facts"]:
        if f["state"] != "PRESENT":
            assert f.get("value") is None, f"{f['field_id']} 非 PRESENT 却带了值"


def test_is_submittable_is_never_asserted(sample_payload):
    """系统不判断"能不能报"。这条是产品锚点, 不是实现细节。"""
    assert sample_payload["quality"]["is_submittable"] is None


def test_export_gate_never_claims_formal_export(sample_payload):
    assert sample_payload["export_gate"]["formal_export_implemented"] is False


# ============================================================
# 2. 收资清单 (F-2)
# ============================================================

def test_intake_summary_matches_issue_list(sample_payload):
    issues = sample_payload["intake_issues"]
    summary = sample_payload["intake_summary"]
    assert summary["total"] == len(issues)
    assert summary["by_severity"]["BLOCK"] == sum(
        1 for i in issues if i["severity"] == "BLOCK")
    assert summary["impact_unknown_count"] == sum(
        1 for i in issues if not i["impact_known"])


def test_intake_issue_ids_are_unique_and_ordered(sample_payload):
    ids = [i["issue_id"] for i in sample_payload["intake_issues"]]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids), "编号必须与展示顺序一致, 否则导出件对不上界面"


def test_unknown_impact_carries_no_fabricated_refs(sample_payload):
    """impact_known=False 时不得夹带任何影响项 —— 界面要显示"尚未建立"。"""
    for i in sample_payload["intake_issues"]:
        if not i["impact_known"]:
            assert not i["affected_section_refs"]
            assert not i["affected_artifact_refs"]
            assert not i["affected_projection_refs"]


# ============================================================
# 2b. F-3..F-7 新增块: field_lineage / tables
# ============================================================

def test_field_lineage_never_invents_a_relation(sample_payload):
    """影响关系只能来自 FIR 登记。**没登记的字段不许出现在这里** ——
    出现一个空壳条目, 界面就会把"没登记"显示成"不影响任何章节"。"""
    for fid, l in sample_payload["field_lineage"].items():
        assert any(l[k] for k in
                   ("section_refs", "artifact_refs", "projection_refs")), \
            f"{fid} 的 lineage 是空的, 不应出现在 field_lineage 里"


def test_field_lineage_keys_are_real_fields(sample_payload):
    known = {f["field_id"] for f in sample_payload["facts"]}
    assert set(sample_payload["field_lineage"]) <= known


def test_field_lineage_refs_are_well_formed(sample_payload):
    for fid, l in sample_payload["field_lineage"].items():
        for r in l["section_refs"]:
            assert r.startswith("sec."), f"{fid}: {r}"
        for r in l["artifact_refs"]:
            assert r.startswith("art."), f"{fid}: {r}"
        for r in l["projection_refs"]:
            assert r.startswith("proj."), f"{fid}: {r}"


def test_tables_declare_a_render_policy(sample_payload):
    """四态必须显式声明 —— 界面据此决定画值还是画占位, 不做推断。"""
    allowed = {"render_with_values", "render_with_placeholder",
               "render_not_applicable", "skip_render", "PROJECTION_FAILED"}
    assert sample_payload["tables"], "没有下发任何表投影"
    for t in sample_payload["tables"]:
        assert t["render_policy"] in allowed, t["render_policy"]


def test_no_table_projection_silently_failed(sample_payload):
    """投影炸了必须显式报出来, 不能少一张表还没人知道。"""
    failed = [t["table_id"] for t in sample_payload["tables"]
              if t["render_policy"] == "PROJECTION_FAILED"]
    assert not failed, f"表投影执行失败: {failed}"


def test_table_rows_only_use_declared_columns(sample_payload):
    """行里出现未声明的列 = 界面渲染时会整列丢掉且无人察觉。"""
    for t in sample_payload["tables"]:
        cols = {c["key"] for c in t["columns"]}
        for r in t["rows"]:
            extra = set(r) - cols
            assert not extra, f"{t['table_id']} 行里有未声明的列: {extra}"
        if t["total_row"]:
            assert set(t["total_row"]) <= cols, t["table_id"]


def test_placeholder_tables_are_labelled_not_hidden(sample_payload):
    """RENDER_WITH_PLACEHOLDER 的表必须仍带列定义 ——
    界面要把"结构就位、数值缺失"画出来, 而不是当成不存在。"""
    for t in sample_payload["tables"]:
        if t["render_policy"] == "render_with_placeholder":
            assert t["columns"], f"{t['table_id']} 占位表没有列定义"


# ============================================================
# 2c. F-8..F-10 新增块: obligations_detail / calculators / rule_refs
# ============================================================

def test_obligation_detail_keeps_unknown_as_none(sample_payload):
    """三值判定必须原样送到前端。

    把 None 折成 False = 把"条件算不出来"当成"条件不成立",
    等于悄悄放过一条可能适用的义务。
    """
    for o in sample_payload["obligations_detail"]:
        assert o["triggered"] in (True, False, None)


def test_obligation_detail_covers_every_obligation(sample_payload):
    """详情条数必须等于三态清单之和, 少一条就是有义务没被展示。"""
    ob = sample_payload["obligations"]
    total = len(ob["triggered"]) + len(ob["not_triggered"]) + len(ob["unknown"])
    assert len(sample_payload["obligations_detail"]) == total


def test_obligation_detail_matches_the_three_way_lists(sample_payload):
    detail = {o["obligation_id"]: o["triggered"]
              for o in sample_payload["obligations_detail"]}
    ob = sample_payload["obligations"]
    for oid in ob["triggered"]:
        assert detail[oid] is True, oid
    for oid in ob["not_triggered"]:
        assert detail[oid] is False, oid
    # unknown 条目是 {"id", "reason"} 对象 —— 未知必须带原因, 不是裸 id
    for entry in ob["unknown"]:
        assert isinstance(entry, dict) and entry.get("reason"), entry
        assert detail[entry["id"]] is None, entry["id"]


def test_unknown_obligations_carry_a_reason(sample_payload):
    """判定未知必须说得出为什么 —— 否则界面只能干瞪眼。"""
    for o in sample_payload["obligations_detail"]:
        if o["triggered"] is None:
            assert o["missing_field_refs"] or o["diagnostic_message"] \
                or o["diagnostic_code"], f"{o['obligation_id']} 未知却没有任何说明"


def test_calculators_report_failures_with_a_message(sample_payload):
    """执行失败必须带错误原文, 不能空着过去。"""
    for c in sample_payload["calculators"]:
        if c["status"] != "ok":
            assert c["error_message"], f"{c['calculator_id']} 失败却没有错误原文"


def test_calculators_are_only_the_ones_that_actually_ran(sample_payload):
    """这一块只装真跑过的。每条都得有输出字段, 否则就是个空壳。"""
    assert sample_payload["calculators"], "没有下发任何计算器结果"
    for c in sample_payload["calculators"]:
        assert c["calculator_id"] and c["output_field_id"]


def test_rule_refs_never_fake_a_title(sample_payload):
    """未登记的 ID 不许带标题。

    一旦有人给 title 填个默认值, 界面就会把"没登记"显示成"已登记",
    引用缺口随之消失。
    """
    for r in sample_payload["rule_refs"]:
        if not r["registered"]:
            assert r["title"] == "", f"{r['rule_id']} 未登记却带了标题"
            assert r["document_title"] == ""
            assert r["quoted_text"] == ""


def test_rule_refs_carry_the_registry_verdict_verbatim(sample_payload):
    """payload 只搬运 RuleRegistry 的结论, 不重新判定核验状态。"""
    from cpswc.rule_registry import load_rule_registry, resolve_rule
    regs = load_rule_registry()
    for r in sample_payload["rule_refs"]:
        expected = resolve_rule(r["rule_id"], regs)
        assert r["verification_status"] == expected["verification_status"]
        assert r["text_verified"] == expected["text_verified"]
        assert r["quoted_text"] == expected["quoted_text"]
        assert r["clause_ref"] == expected["clause_ref"]


def test_declared_rule_refs_show_no_quoted_text(sample_payload):
    """只定位到文件的条目不许带原文 —— 界面会把它当条文显示给审查人员。"""
    for r in sample_payload["rule_refs"]:
        if r["verification_status"] == "DECLARED":
            assert r["quoted_text"] == "", r["rule_id"]


def test_rule_coverage_matches_the_ref_list(sample_payload):
    cov = sample_payload["rule_coverage"]
    refs = sample_payload["rule_refs"]
    assert cov["cited_total"] == len(refs)
    assert cov["text_verified"] == sum(1 for r in refs if r["text_verified"])
    assert cov["unregistered"] == sum(1 for r in refs if not r["registered"])
    assert (cov["text_verified"] + cov["declared"] + cov["unregistered"]
            == len(refs))


def test_no_narrative_cites_a_retired_or_defective_rule(sample_payload):
    """正文不许引用退役或有缺陷的依据 ID。

    修好那两处陈旧引用 (section_11 → 1.9, section_7 → 9.2) 之后,
    `defects` 应当为空 —— 它非空就说明有正文又指回了坏 ID。
    """
    defects = sample_payload["rule_coverage"]["defects"]
    assert defects == [], f"仍有正文引用坏 ID: {defects}"


def test_conclusion_and_benefit_analysis_cite_the_migrated_clauses(sample_payload):
    """结论在 1.9、效益分析在 9.2 —— 引用必须跟着迁移走。"""
    by_id = {r["rule_id"]: r for r in sample_payload["rule_refs"]}
    assert "rule.template_2026.section_11" not in by_id, "退役 ID 仍被引用"

    concl = by_id.get("rule.template_2026.section_1_9")
    assert concl and concl["clause_ref"] == "1.9 结论"
    assert all(c["ref"].startswith("narr.conclusion") or c["ref"] == "sec.conclusion"
               for c in concl["cited_by"]), concl["cited_by"]

    benefit = by_id.get("rule.template_2026.section_9_2")
    assert benefit and benefit["clause_ref"] == "9.2 效益分析"
    assert all("benefit_analysis" in c["ref"] for c in benefit["cited_by"]), \
        benefit["cited_by"]


def test_rule_refs_are_traceable_to_a_citer(sample_payload):
    """每个依据 ID 都必须说得出是谁在引用, 否则清点没有意义。"""
    assert sample_payload["rule_refs"], "没有清点到任何依据 ID"
    for r in sample_payload["rule_refs"]:
        assert r["cited_by"], r["rule_id"]
        assert r["citation_count"] == len(r["cited_by"])
        assert r["rule_id"].startswith("rule.")
        for c in r["cited_by"]:
            assert c["kind"] in ("obligation", "calculator", "assurance", "narrative")


def test_required_artifacts_and_assurances_are_listed(sample_payload):
    assert isinstance(sample_payload["required_artifacts"], list)
    assert isinstance(sample_payload["required_assurances"], list)
    for a in sample_payload["required_artifacts"]:
        assert a.startswith("art."), a
    for a in sample_payload["required_assurances"]:
        assert a.startswith("as."), a


def test_figures_do_not_claim_a_renderer_that_does_not_exist(sample_payload):
    """ArtifactRegistry 里的 `renderer` 只是个类名声明, 不保证代码存在。

    实测 9 个图件渲染器一个都没实现。这条测试盯的是**不许靠登记表推断**:
    一旦有人把 renderer_implemented 写成 bool(renderer), 界面立刻会显示
    14 张图"可生成", 而实际一张也画不出来。
    """
    import cpswc.frontend_payload as fp
    for f in sample_payload["figures"]:
        expected = f["renderer"] in fp._IMPLEMENTED_RENDERERS
        assert f["renderer_implemented"] is expected, f["artifact_id"]


def test_figures_required_flag_comes_from_runtime(sample_payload):
    """"本项目需要哪些图"必须来自本次 runtime 推导, 不是登记表的 always/conditional。"""
    required = set(sample_payload["required_artifacts"])
    for f in sample_payload["figures"]:
        assert f["required_for_this_project"] is (f["artifact_id"] in required)


def test_every_figure_says_what_to_draw_or_admits_it_does_not(sample_payload):
    assert sample_payload["figures"], "没有下发任何图件要求"
    for f in sample_payload["figures"]:
        assert f["artifact_id"].startswith("art.figure.")
        assert f["canonical_name"]


# ============================================================
# 3. schema 校验必须挡住残缺 payload
# ============================================================

@pytest.mark.parametrize("key", [
    "schema_version", "data_mode", "generated_at", "shell_digest",
    "project", "hashes", "facts", "quality", "export_gate",
])
def test_validate_rejects_missing_top_level_key(sample_payload, key):
    broken = dict(sample_payload)
    broken.pop(key)
    problems = validate_payload(broken)
    assert any(key in p for p in problems), f"缺 {key} 竟然放行了"


def test_write_bundle_refuses_invalid_payload(sample_payload, tmp_path):
    broken = dict(sample_payload)
    broken.pop("quality")
    with pytest.raises(ValueError, match="拒绝落盘"):
        write_bundle(broken, tmp_path)


# ============================================================
# 4. 落盘: 原子、分目录、单文件自包含
# ============================================================

def test_bundle_path_is_keyed_by_project_and_hash(sample_payload, tmp_path):
    out = write_bundle(sample_payload, tmp_path)
    assert out.name == sample_payload["hashes"]["generation_input_hash"][:16]
    assert (out / "index.html").exists()
    assert (out / "payload.json").exists()


def test_two_projects_do_not_overwrite_each_other(tmp_path):
    if len(SAMPLES) < 2:
        pytest.skip("样本不足两个")
    a = write_bundle(build_payload(_load(SAMPLES[0])), tmp_path)
    b = write_bundle(build_payload(_load(SAMPLES[1])), tmp_path)
    assert a != b
    assert a.exists() and b.exists()


def test_failed_write_leaves_no_half_bundle(sample_payload, tmp_path, monkeypatch):
    """渲染中途炸掉时, 目标目录必须干干净净 —— 不能留下能被双击打开的半成品。"""
    import cpswc.frontend_payload as fp
    monkeypatch.setattr(fp, "render_standalone_html",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        write_bundle(sample_payload, tmp_path)
    leftovers = [p for p in tmp_path.rglob("index.html")]
    assert leftovers == [], f"留下了半成品: {leftovers}"


def test_standalone_html_inlines_every_shell_script(sample_payload):
    """file:// 下外链 .jsx 会被 CORS 拦成白屏, 所以一个外链都不能剩。"""
    html = render_standalone_html(sample_payload)
    assert 'src="pages/' not in html
    assert 'src="data.jsx"' not in html
    for src in ("data.jsx", "App.jsx", "Root.jsx"):
        assert f'data-source="{src}"' in html


def test_shell_digest_meta_is_computed_not_copied(sample_payload):
    """壳指纹 meta 必须现场按壳文件算。

    抄 payload 里的值会让"旧壳配新数据"永远检不出来 —— 浏览器验收实测踩过:
    把 payload.shell_digest 改成 000... 照样畅通无阻。
    """
    forged = dict(sample_payload, shell_digest="0" * 64)
    html = render_standalone_html(forged)
    assert shell_digest(FRONTEND_DIR) in html
    assert "0" * 64 not in html.split("</head>")[0]


def test_demo_render_has_no_payload_and_no_digest():
    html = render_standalone_html(None)
    assert "window.CPSWC_PAYLOAD =" not in html  # data.jsx 里的**读取**不算
    assert '<meta name="cpswc-shell-digest"' not in html  # 读取代码不算
    assert 'data-source="data.jsx"' in html
