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
