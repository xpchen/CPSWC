"""
test_data_modes.py — F-1B 浏览器级验收

对应 FRONTEND_WIRING_PLAN.md v1.1 § 5.1「测试要求」：Python 单测不够，
必须有浏览器场景，否则"页面上到底显示了什么"没人验过。

    无 payload            → 全局演示模式角标
    完整 payload          → **页面上不出现任何 mock 数值**
    部分/版本不符/壳不匹配 → 阻断错误页，**绝不回落 mock**
    ExportGate=BLOCK      → 顶栏与 Delivery 都没有可用的交付按钮

跑法（需要本机 playwright + chromium，缺依赖时整文件 skip）：

    PYTHONPATH=src python3 -m pytest tests/browser -q

这些用例**自己生成 bundle**，不依赖仓库里已有的 output/。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

playwright_api = pytest.importorskip(
    "playwright.sync_api", reason="需要 playwright 才能跑浏览器级验收")
from playwright.sync_api import sync_playwright  # noqa: E402

from cpswc.frontend_payload import (  # noqa: E402
    build_payload, render_standalone_html, write_bundle)
from cpswc.paths import SAMPLES_DIR  # noqa: E402

# mock 里的标志性数值。
#
# 注意 "世维华南供应链": 它同时是 `samples/shiwei_logistics_v0.json` 的**真实**
# 项目名 —— 当初的演示数据就是照那份样本编的。所以这些断言只能跑在惠州样本的
# bundle 上; 换样本时它会变成合法内容, 不是泄漏。
MOCK_MARKERS = [
    "世维华南供应链",        # PROJECT.name
    "GD-HZ-2026-SWBC-0211",  # PROJECT.code
    "97.6%",                 # SIX_RATES 伪造的"实现值"
    "项目完成度 91",          # 顶栏硬编码完成度
    "无阻塞项",
]

# 快照模式下**必须**一个都不出现的 mock —— 这些是全局壳 (顶栏/侧栏/首屏)
# 自己在说的话, 与页面接线进度无关。
SHELL_MOCK_MARKERS = [
    "世维华南供应链",
    "GD-HZ-2026-SWBC-0211",
    "项目完成度 91",
]

# 其余 mock 仍存在于尚未接线的页面里 (F-3..F-7 逐页消除)。
# 对它们的要求不是"不存在", 而是"**必须被标记为未接线**" ——
# 见 test_unwired_pages_are_labelled。用 WIRED_PAGES 白名单驱动:
# 页面一旦接线就自动纳入无 mock 断言, 不需要改测试。


def _chromium_available() -> bool:
    try:
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _chromium_available(), reason="本机没有可用的 chromium")


@pytest.fixture(scope="module")
def snapshot_bundle(tmp_path_factory) -> Path:
    """用惠州样本生成一份真实 bundle。"""
    out = tmp_path_factory.mktemp("bundle")
    pi = json.loads(
        (SAMPLES_DIR / "huizhou_housing_v0.json").read_text(encoding="utf-8"))
    return write_bundle(build_payload(pi), out)


@pytest.fixture(scope="module")
def demo_bundle(tmp_path_factory) -> Path:
    """没有 payload 的壳 —— 即演示模式。

    同样走单文件内联: 直接拷壳目录在 file:// 下会被 CORS 拦成白屏,
    那样验的就不是"演示模式"而是"加载失败"。
    """
    out = tmp_path_factory.mktemp("demo")
    (out / "index.html").write_text(render_standalone_html(None),
                                    encoding="utf-8")
    return out


def _page_text(bundle: Path, page_obj) -> str:
    page_obj.goto((bundle / "index.html").as_uri())
    page_obj.wait_for_load_state("networkidle")
    page_obj.wait_for_timeout(700)      # Babel 在浏览器里转译需要一点时间
    return page_obj.inner_text("body")


@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # accept_downloads: 收资清单导出要真下载一次才验得了内容
        pg = browser.new_context(accept_downloads=True).new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.errors = errors
        yield pg
        browser.close()


# ============================================================
# 场景 1 — 无 payload → 演示模式
# ============================================================

def _demo_workbench_text(bundle: Path, page_obj) -> str:
    """演示模式从登录页进, 要走完登录才看得到工作台的角标。

    (快照模式则直接进工作台 —— 见 Root.jsx: 登录页属于演示流程,
    快照是一份已生成的静态结果, 没有"登录"这回事。)
    """
    page_obj.goto((bundle / "index.html").as_uri())
    page_obj.wait_for_load_state("networkidle")
    page_obj.wait_for_timeout(700)
    page_obj.get_by_role("button", name="登录", exact=True).first.click()
    page_obj.wait_for_timeout(600)
    # 登录后落在项目列表, 还要打开一个项目才进工作台
    page_obj.get_by_text("惠州", exact=False).first.click()
    page_obj.wait_for_timeout(600)
    return page_obj.inner_text("body")


def test_login_page_says_it_is_a_demo(demo_bundle, page):
    assert "演示环境" in _page_text(demo_bundle, page)


def test_no_payload_shows_demo_banner(demo_bundle, page):
    text = _demo_workbench_text(demo_bundle, page)
    assert "演示数据" in text
    assert "不来自任何真实项目" in text


def test_demo_mode_does_not_claim_to_be_a_snapshot(demo_bundle, page):
    text = _demo_workbench_text(demo_bundle, page)
    assert "项目快照" not in text


# ============================================================
# 场景 2 — 完整 payload → 无 mock 数值
# ============================================================

def test_snapshot_shows_the_real_project(snapshot_bundle, page):
    text = _page_text(snapshot_bundle, page)
    assert "项目快照" in text
    assert "静态快照，非实时数据" in text
    assert "惠州市大亚湾" in text, "应显示 payload 里的真实项目名"


@pytest.mark.parametrize("marker", SHELL_MOCK_MARKERS)
def test_shell_contains_no_mock_values(snapshot_bundle, page, marker):
    """全局壳 (顶栏/侧栏/首屏) 在快照模式下**完全禁止 mock**。"""
    text = _page_text(snapshot_bundle, page)
    assert marker not in text, f"全局壳在快照模式下出现了 mock 数值: {marker}"


def test_unwired_pages_are_labelled(snapshot_bundle, page):
    """尚未接线的页面必须自曝, 否则 mock 就在冒充真项目数据。

    逐页点过去: 凡不在 WIRED_PAGES 白名单里的页面, 都要出现未接线提示。
    """
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)

    nav = page.evaluate("() => window.CPSWC.NAV.map(n => n.id)")
    wired = set(page.evaluate("() => window.CPSWC.WIRED_PAGES || []"))
    assert nav, "取不到导航项, 断言没有意义"

    unlabelled = []
    for key in nav:
        if key in wired:
            continue
        page.evaluate(f"() => window.__cpswcGo && window.__cpswcGo({key!r})")
        page.wait_for_timeout(120)
        if "本页尚未接入项目数据" not in page.inner_text("body"):
            unlabelled.append(key)
    assert not unlabelled, f"这些未接线页面没有标注, 会让 mock 冒充真数据: {unlabelled}"


def test_intake_drawer_shows_real_issues(snapshot_bundle, page):
    """收资抽屉第 4 节必须来自后端 intake_issues, 其余节自曝演示。"""
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    page.get_by_role("banner").get_by_role("button", name="智能收资向导").click()
    page.wait_for_timeout(400)
    text = page.inner_text("body")

    summary = _payload_of(snapshot_bundle)["intake_summary"]
    assert summary["total"] > 0, "样本没有收资条目, 断言没有意义"
    assert f'{summary["total"]} 项，来自本次生成快照' in text
    assert f'阻断 {summary["by_severity"]["BLOCK"]}' in text
    assert "第 1–3、5–6 节为演示数据" in text, "未接线的节必须自曝"
    if summary["impact_unknown_count"]:
        assert "影响范围尚未建立" in text, "影响关系建立不起来时必须如实说, 不得编造"


def test_intake_export_button_is_available(snapshot_bundle, page):
    """收资清单是本阶段唯一真能交付的产物, 按钮必须可用 (不同于导出交付包)。"""
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    page.get_by_role("banner").get_by_role("button", name="智能收资向导").click()
    page.wait_for_timeout(400)
    btn = page.get_by_role("button", name="导出待甲方提供资料清单")
    assert btn.count() == 1 and btn.first.is_enabled()


def test_intake_export_produces_a_watermarked_list(snapshot_bundle, tmp_path, page):
    """真下载一次, 验导出件的内容 —— 这是本阶段唯一能交到甲方手上的东西。

    硬要求: 水印 + 项目名 + 生成时间 + generation_input_hash + 分级,
    以及"影响范围尚未建立不代表不影响任何章节"的说明。
    """
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    page.get_by_role("banner").get_by_role("button", name="智能收资向导").click()
    page.wait_for_timeout(400)

    with page.expect_download() as dl:
        page.get_by_role("button", name="导出待甲方提供资料清单").click()
    saved = tmp_path / "intake.html"
    dl.value.save_as(saved)
    html = saved.read_text(encoding="utf-8")

    payload = _payload_of(snapshot_bundle)
    assert "工作草稿 · 非正式报告附件" in html
    assert "不构成水土保持方案报告的任何正式组成部分" in html
    assert payload["project"]["name"] in html
    assert payload["hashes"]["generation_input_hash"] in html
    assert payload["generated_at"] in html
    assert "不代表它不影响任何章节" in html
    # 每一条收资项都必须在导出件里, 不许截断 —— 少一条就是少向甲方要一样东西
    import html as _html
    for issue in payload["intake_issues"]:
        assert _html.escape(issue["message"], quote=False) in html, f"导出件漏了 {issue['issue_id']}"
    assert html.count("<tr>") == payload["intake_summary"]["total"] + 2  # 表头 + 表尾
    for marker in MOCK_MARKERS:
        assert marker not in html, f"导出件里混进了 mock: {marker}"


def test_intake_fake_write_actions_are_disabled(snapshot_bundle, page):
    """"确认写入事实层"只改浏览器本地 state, 快照模式下不得可按。"""
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    page.get_by_role("banner").get_by_role("button", name="智能收资向导").click()
    page.wait_for_timeout(400)
    for name in ("确认写入事实层（未实现）", "上传资料（未实现）"):
        btn = page.get_by_role("button", name=name)
        assert btn.count() >= 1, f"找不到按钮: {name}"
        assert btn.first.is_disabled(), f"{name} 不应可按"


# ============================================================
# 场景 5 — 硬编码的"肯定状态"必须消失
#   用户原话: "搜索并消除全部硬编码的'通过、无阻塞、达标、可下载、覆盖率'
#   等肯定状态, 而不只修改计划列出的几个组件"
# ============================================================

def _goto(page_obj, key: str) -> str:
    page_obj.evaluate(f"() => window.__cpswcGo && window.__cpswcGo({key!r})")
    page_obj.wait_for_timeout(250)
    return page_obj.inner_text("body")


def test_delivery_shows_the_real_gate_verdict(snapshot_bundle, page):
    """交付页原本写死 11 项"通过"/14 个"可下载", 而真实门禁是 BLOCK。"""
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    text = _goto(page, "delivery")

    gate = _payload_of(snapshot_bundle)["export_gate"]
    assert gate["verdict"] == "BLOCK", "样本门禁不是 BLOCK, 断言没有意义"
    assert f'门禁结论 {gate["verdict"]}' in text
    assert "项通过" not in text, "门禁只报问题, 不出具通过数"
    assert "可下载" not in text, "正式导出未实现, 不得列出可下载文件"
    assert "没有产出任何交付文件" in text
    assert "数文一致性检查通过" not in text


def test_no_page_claims_a_hardcoded_positive_state(snapshot_bundle, page):
    """全壳扫一遍: 逐页点过去, 这些写死的肯定说法一个都不许出现。"""
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    banned = ["无阻塞项", "可下载", "项通过", "数文一致性检查通过",
              "项目完成度", "无导出阻塞"]
    offenders = {}
    for key in page.evaluate("() => window.CPSWC.NAV.map(n => n.id)"):
        text = _goto(page, key)
        hit = [b for b in banned if b in text]
        if hit:
            offenders[key] = hit
    assert not offenders, f"仍有页面在说写死的肯定状态: {offenders}"


# ============================================================
# 场景 6 — F-3..F-7 逐页接线
# ============================================================

@pytest.fixture
def wired_page(snapshot_bundle, page):
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    return page


def test_overview_shows_the_real_coverage_and_gate(wired_page, snapshot_bundle):
    """首屏原本写死"无导出阻塞""91% 完成度"。现在必须是 payload 的真数字。"""
    text = _goto(wired_page, "overview")
    pl = _payload_of(snapshot_bundle)
    q, g = pl["quality"], pl["export_gate"]
    assert f'导出门禁 {g["verdict"]}' in text
    assert f'（阻断 {g["block_count"]} · 提醒 {g["warn_count"]}）' in text
    assert "「确认完成」为 0 不是显示故障" in text, "0 必须解释, 否则被当成显示故障"
    assert str(q["applicable_leaf_count"]) in text
    assert pl["project"]["name"] in text


def test_overview_six_rates_are_not_drawn_as_progress_bars(wired_page):
    """实现值是候选值。画一根绿进度条等于宣布达标。"""
    text = _goto(wired_page, "overview")
    assert "候选·待确认" in text
    assert "实现值来源待确认" in text


def test_facts_lists_missing_fields_too(wired_page, snapshot_bundle):
    """缺失字段必须看得见 —— 看不见的缺口等于不存在。"""
    text = _goto(wired_page, "facts")
    pl = _payload_of(snapshot_bundle)
    missing = [f for f in pl["facts"] if f["state"] != "PRESENT"]
    assert missing, "样本没有缺失字段, 断言没有意义"
    assert f'未取到值 {len(missing)} 项' in text
    assert "均未复核" in text
    assert "事实完整度" not in text, "不得给出合成的完整度百分比"


def test_facts_never_claims_a_field_is_verified(wired_page):
    """快照里的事实只是"有取值", 不是"已校验"。"""
    text = _goto(wired_page, "facts")
    assert "已校验" not in text


def test_narrative_shows_unimplemented_sections_as_gaps(wired_page, snapshot_bundle):
    """未实现的小节必须以缺口块出现, 不能跳过 ——
    跳过会让目录看起来连续, 读者默认它写完了。"""
    text = _goto(wired_page, "narrative")
    pl = _payload_of(snapshot_bundle)
    q = pl["quality"]
    assert f'未实现 {q["unimplemented_leaf_count"]}' in text
    assert "本节未实现" in text
    assert "缺口以红框显示，未做任何省略" in text


def test_narrative_editing_is_disabled(wired_page):
    text = _goto(wired_page, "narrative")
    assert "编辑正文（未实现）" in text
    assert "导出 Word（未实现）" in text


def test_tables_show_only_real_projections(wired_page, snapshot_bundle):
    """演示版列了 12 张表 9 张 LIVE; 后端实际只有 payload.tables 这些。"""
    text = _goto(wired_page, "tables")
    tables = _payload_of(snapshot_bundle)["tables"]
    assert tables, "样本没有表投影, 断言没有意义"
    for t in tables:
        assert t["title"] in text, f"表 {t['table_id']} 没有出现在页面上"
    assert "LIVE" not in text, "不得沿用演示版的 LIVE 角标"
    assert "后端未实现" in text, "后端没有的表必须列出来, 不能悄悄消失"


def test_placeholder_table_is_explicitly_labelled(wired_page, snapshot_bundle):
    tables = _payload_of(snapshot_bundle)["tables"]
    ph = [t for t in tables if t["render_policy"] == "render_with_placeholder"]
    if not ph:
        pytest.skip("本样本没有占位表")
    _goto(wired_page, "tables")
    # 占位说明只在选中该表时出现 —— 先点开它
    wired_page.get_by_role("button", name=ph[0]["title"]).first.click()
    wired_page.wait_for_timeout(250)
    text = wired_page.inner_text("body")
    assert "结构占位·缺值" in text
    assert "不要把它当成一张已经算好的表" in text


def test_delivery_never_says_it_is_submittable(wired_page, snapshot_bundle):
    """「是否可提交：可提交（非阻塞）」是整个界面最危险的一句话。

    后端 `is_submittable` 恒为 None —— 系统不判断能不能报。
    """
    text = _goto(wired_page, "delivery")
    assert _payload_of(snapshot_bundle)["quality"]["is_submittable"] is None
    assert "系统不作判断" in text
    assert "可提交（非阻塞）" not in text


def test_delivery_only_real_action_is_the_intake_list(wired_page):
    """这一列里唯一真能按的是收资清单导出, 其余必须禁用并标注。"""
    text = _goto(wired_page, "delivery")
    assert "导出待甲方提供资料清单" in text
    for label in ("生成预览（未实现）", "导出 Word（未实现）",
                  "导出审查包（未实现）"):
        assert label in text
        assert wired_page.get_by_role("button", name=label).first.is_disabled()


def test_overview_intake_shortcut_opens_the_drawer(wired_page):
    """首屏那句"逐条清单见智能收资向导"必须真能点开, 否则就是一句空话。"""
    _goto(wired_page, "overview")
    wired_page.get_by_role("main").get_by_role(
        "button", name="智能收资向导").click()
    wired_page.wait_for_timeout(400)
    assert "当前缺失资料 / 待甲方提供" in wired_page.inner_text("body")


def test_rules_shows_every_obligation_with_its_expression(wired_page, snapshot_bundle):
    """演示版顶上挂「无阻塞」chip, 而真实门禁是 BLOCK。现在逐条摆判定。"""
    text = _goto(wired_page, "rules")
    obs = _payload_of(snapshot_bundle)["obligations_detail"]
    yes = sum(1 for o in obs if o["triggered"] is True)
    no = sum(1 for o in obs if o["triggered"] is False)
    assert f"已触发 {yes}" in text
    assert f"未触发 {no}" in text
    assert f"共 {len(obs)} 条义务" in text
    assert "无阻塞" not in text


def test_rules_keeps_unknown_separate_from_not_triggered(wired_page, snapshot_bundle):
    """「判定未知」不得并入「未触发」—— 那等于悄悄放过一条可能适用的义务。"""
    text = _goto(wired_page, "rules")
    assert "「判定未知」单独成类，不并入未触发" in text
    unk = [o for o in _payload_of(snapshot_bundle)["obligations_detail"]
           if o["triggered"] is None]
    if unk:
        assert f"判定未知 {len(unk)}" in text


def test_rules_gate_tab_shows_real_findings(wired_page, snapshot_bundle):
    _goto(wired_page, "rules")
    wired_page.get_by_role("button", name="导出门禁").click()
    wired_page.wait_for_timeout(250)
    text = wired_page.inner_text("body")
    g = _payload_of(snapshot_bundle)["export_gate"]
    assert f"门禁结论 {g['verdict']}" in text
    assert "门禁只报问题，不出具「通过」结论" in text


def test_rules_required_artifacts_are_not_claimed_as_provided(wired_page, snapshot_bundle):
    """需附文件清单是"需要什么", 不是"已经有什么"。系统收不到附件。"""
    _goto(wired_page, "rules")
    wired_page.get_by_role("button", name="需附文件").click()
    wired_page.wait_for_timeout(250)
    text = wired_page.inner_text("body")
    n = len(_payload_of(snapshot_bundle)["required_artifacts"])
    assert f"{n} 项" in text
    assert "系统没有接收附件的能力" in text
    assert "无法核对其中任何一项是否已提供" in text


def test_calculators_show_only_what_actually_ran(wired_page, snapshot_bundle):
    text = _goto(wired_page, "calc")
    calcs = _payload_of(snapshot_bundle)["calculators"]
    assert f"已执行 {sum(1 for c in calcs if c['status'] == 'ok')}" in text
    for c in calcs:
        assert c["canonical_name"] in text
    assert "这一页只显示真正跑过的" in text
    assert "4 / 5 已计算" not in text, "不得沿用演示版的计数"


def test_calculators_do_not_equate_success_with_trustworthy(wired_page):
    text = _goto(wired_page, "calc")
    assert "执行成功不等于结果可信" in text


def test_calculators_flag_unreliable_inputs(wired_page, snapshot_bundle):
    """输入是 placeholder stub 或空清单时, 输出再精确也只是把一个
    未经核实的前提算了一遍。两种都必须在输入行上标出来。"""
    pl = _payload_of(snapshot_bundle)
    facts = {f["field_id"]: f for f in pl["facts"]}
    weak = [(c, r) for c in pl["calculators"] for r in c["input_refs"]
            if "placeholder" in (facts.get(r, {}).get("note") or "").lower()
            or facts.get(r, {}).get("is_empty_container")]
    assert weak, "样本里没有不可靠输入, 断言没有意义"
    calc, _ = weak[0]
    _goto(wired_page, "calc")
    wired_page.get_by_role("button", name=calc["canonical_name"]).first.click()
    wired_page.wait_for_timeout(250)
    text = wired_page.inner_text("body")
    assert ("该输入带演示/默认假设标记" in text
            or "该输入是空清单，且未经核实" in text)


def test_footnotes_split_verification_into_three_states(wired_page, snapshot_bundle):
    """「定位到文件了」和「条文核对过了」是两回事, 不许压成一个覆盖率。"""
    text = _goto(wired_page, "footnotes")
    cov = _payload_of(snapshot_bundle)["rule_coverage"]
    assert f"依据 ID {cov['cited_total']} 个" in text
    assert f"已核原文 {cov['text_verified']}" in text
    assert f"已定位 {cov['declared']}" in text
    assert f"未登记 {cov['unregistered']}" in text
    assert "依据覆盖率" not in text, "不得给出单一覆盖率百分比"


def test_footnotes_expose_the_unregistered_basis_ids(wired_page, snapshot_bundle):
    """未登记的依据 ID 是该让人看见的缺口, 并且要说清下一步怎么补。"""
    text = _goto(wired_page, "footnotes")
    cov = _payload_of(snapshot_bundle)["rule_coverage"]
    if not cov["unregistered"]:
        pytest.skip("本样本依据已全部登记")
    assert f"{cov['unregistered']} 个依据 ID 未登记" in text
    assert "无法向审查人员出示条文" in text
    for ns in cov["unregistered_namespaces"]:
        assert ns["namespace"] in text
        assert ns["next_step"] in text


def test_footnotes_show_verified_clause_text(wired_page, snapshot_bundle):
    """已核原文的条目必须真把条文摆出来 —— 这是这份注册表的全部意义。"""
    refs = _payload_of(snapshot_bundle)["rule_refs"]
    verified = [r for r in refs if r["text_verified"]]
    assert verified, "样本里没有已核原文的依据, 断言没有意义"
    _goto(wired_page, "footnotes")
    wired_page.get_by_role("button", name="已核原文", exact=False).last.click()
    wired_page.wait_for_timeout(200)
    wired_page.get_by_text(verified[0]["rule_id"], exact=True).first.click()
    wired_page.wait_for_timeout(250)
    text = wired_page.inner_text("body")
    assert verified[0]["document_number"] in text
    assert verified[0]["clause_ref"] in text
    first_line = verified[0]["quoted_text"].strip().splitlines()[0]
    assert first_line in text, "条文原文没有显示出来"


def test_footnotes_never_show_text_for_declared_entries(wired_page, snapshot_bundle):
    """只定位到文件的条目必须说"未抓取", 不能让人以为拿得出条文。"""
    refs = _payload_of(snapshot_bundle)["rule_refs"]
    declared = [r for r in refs if r["verification_status"] == "DECLARED"]
    assert declared, "样本里没有 DECLARED 条目"
    _goto(wired_page, "footnotes")
    wired_page.get_by_text(declared[0]["rule_id"], exact=True).first.click()
    wired_page.wait_for_timeout(250)
    text = wired_page.inner_text("body")
    assert "不能直接向审查人员出示" in text


def test_footnotes_report_citation_defects(wired_page, snapshot_bundle):
    """有陈旧引用就必须在页面顶部报出来; 没有就不许凭空显示一条。

    当前两处已修 (section_11 → 1.9, section_7 → 9.2), 所以走的是"不显示"分支。
    谁再引入一个坏引用, 上面那半边会开始生效。
    """
    cov = _payload_of(snapshot_bundle)["rule_coverage"]
    text = _goto(wired_page, "footnotes")
    if cov["defects"]:
        assert f"{len(cov['defects'])} 条依据引用有缺陷" in text
        for d in cov["defects"]:
            assert d["rule_id"] in text
            assert d["defect"] in text
    else:
        assert "条依据引用有缺陷" not in text


def test_footnotes_page_is_not_an_editor(wired_page):
    """系统没有注脚能力: 不能编号、不能插入正文、不能导出、没有存储。"""
    text = _goto(wired_page, "footnotes")
    assert "这一页不是注脚编辑器" in text
    assert "不能编号、不能插入正文" in text
    assert "也没有存储" in text


def test_maps_admits_no_figure_can_be_generated(wired_page, snapshot_bundle):
    """演示版是个能"生成图件"的地图中心。实际 9 个渲染器一个都没实现。"""
    text = _goto(wired_page, "maps")
    figs = _payload_of(snapshot_bundle)["figures"]
    req = [f for f in figs if f["required_for_this_project"]]
    ok = [f for f in figs if f["renderer_implemented"]]
    assert f"本项目需要 {len(req)} 张" in text
    assert f"可生成 {len(ok)} 张" in text
    if not ok:
        assert "一张也生成不了" in text
        assert "这些渲染器没有一个有代码实现" in text
    assert "已生成" not in text, "不得沿用演示版的「已生成」角标"


def test_maps_lists_every_required_figure_as_a_task(wired_page, snapshot_bundle):
    """这份清单的用处是当制图任务单, 所以一张都不能漏。"""
    text = _goto(wired_page, "maps")
    for f in _payload_of(snapshot_bundle)["figures"]:
        if f["required_for_this_project"]:
            assert f["canonical_name"] in text, f["artifact_id"]


@pytest.mark.parametrize("key,title", [("changes", "改动追踪"), ("history", "历史与版本")])
def test_unbacked_pages_show_nothing_instead_of_fake_logs(wired_page, key, title):
    """后端完全没有产出的页面, 不显示任何示例内容。

    一屏具体到人名、时间、金额的演示记录会被当成真的,
    一条提示条压不住它。
    """
    text = _goto(wired_page, key)
    assert "该功能尚未实现，本页不显示任何内容" in text
    assert "刻意不显示示例内容" in text
    # 演示版这两页的伪造记录特征: 人名 + 精确时间
    for fake in ("李工 · 编制", "今天 09:4", "v0.3", "5 名成员"):
        assert fake not in text, f"{title} 仍在显示伪造记录: {fake}"


def test_no_nav_page_is_left_unwired(wired_page):
    """全部 NAV 页面都已接线。白名单机制保留 —— 将来新增页面仍默认未接线。"""
    nav = wired_page.evaluate("() => window.CPSWC.NAV.map(n => n.id)")
    wired = set(wired_page.evaluate("() => window.CPSWC.WIRED_PAGES || []"))
    assert set(nav) <= wired, f"仍未接线: {sorted(set(nav) - wired)}"


def test_wired_pages_contain_no_mock_values(snapshot_bundle, page):
    """已声明接线的页面必须彻底无 mock。白名单一增长, 覆盖面自动扩大。"""
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    wired = page.evaluate("() => window.CPSWC.WIRED_PAGES || []")
    for key in wired:
        page.evaluate(f"() => window.__cpswcGo && window.__cpswcGo({key!r})")
        page.wait_for_timeout(200)
        text = page.inner_text("body")
        for marker in MOCK_MARKERS:
            assert marker not in text, f"已接线页 {key} 仍有 mock: {marker}"


def test_snapshot_shows_no_single_completeness_percentage(snapshot_bundle, page):
    """覆盖率必须四行分开看; 压成一个百分比会重新制造"接近完成"的错觉。"""
    text = _page_text(snapshot_bundle, page)
    assert "项目完成度" not in text
    assert "内容完成度" in text


def test_snapshot_page_has_no_js_errors(snapshot_bundle, page):
    _page_text(snapshot_bundle, page)
    assert page.errors == [], f"页面报错: {page.errors}"


# ============================================================
# 场景 3 — payload 有问题 → 阻断, 绝不回落 mock
# ============================================================

def _payload_of(bundle: Path) -> dict:
    """bundle 是单文件 index.html + payload.json 旁证; 取旁证读。"""
    return json.loads((bundle / "payload.json").read_text(encoding="utf-8"))


def _corrupt(bundle: Path, tmp_path: Path, mutate) -> Path:
    """按 mutate 破坏 payload 后重新内联 —— 绕开 validate_payload,
    模拟"别人手里那份 bundle 被改过/壳版本对不上"。"""
    payload = _payload_of(bundle)
    mutate(payload)
    broken = tmp_path / "broken"
    broken.mkdir(parents=True, exist_ok=True)
    (broken / "index.html").write_text(render_standalone_html(payload),
                                       encoding="utf-8")
    return broken


def test_incompatible_schema_version_blocks(snapshot_bundle, tmp_path, page):
    broken = _corrupt(snapshot_bundle, tmp_path,
                      lambda p: p.__setitem__("schema_version", "v0_old"))
    text = _page_text(broken, page)
    assert "数据包无法加载" in text
    assert "schema_version 不匹配" in text


def test_missing_key_blocks(snapshot_bundle, tmp_path, page):
    broken = _corrupt(snapshot_bundle, tmp_path, lambda p: p.pop("quality"))
    text = _page_text(broken, page)
    assert "数据包无法加载" in text
    assert "缺顶层键 quality" in text


def test_shell_drift_blocks(snapshot_bundle, tmp_path, page):
    """把新 payload 拷进旧壳 (或反之) —— shell_digest 对不上就必须拒绝。"""
    broken = _corrupt(snapshot_bundle, tmp_path,
                      lambda p: p.__setitem__("shell_digest", "0" * 64))
    text = _page_text(broken, page)
    assert "数据包无法加载" in text
    assert "shell_digest 不一致" in text


@pytest.mark.parametrize("mutate,label", [
    (lambda p: p.__setitem__("schema_version", "v0_old"), "版本不符"),
    (lambda p: p.pop("quality"), "缺键"),
    (lambda p: p.__setitem__("shell_digest", "0" * 64), "壳漂移"),
])
def test_payload_error_never_falls_back_to_mock(snapshot_bundle, tmp_path,
                                                page, mutate, label):
    """最关键的一条: 出错时宁可什么都不显示, 也不能半真半演示。"""
    broken = _corrupt(snapshot_bundle, tmp_path, mutate)
    text = _page_text(broken, page)
    for marker in MOCK_MARKERS:
        assert marker not in text, f"{label}: 回落了 mock ({marker})"
    # 错误页自己的说明里会出现"演示数据"四个字 (解释为什么停止加载),
    # 所以只能拿演示模式角标的专有措辞来判定是否降级成了演示态。
    assert "不来自任何真实项目" not in text, f"{label}: 错误态不应降级成演示态"
    assert "数据包无法加载" in text


# ============================================================
# 场景 4 — ExportGate=BLOCK → 没有可用的交付按钮
# ============================================================

def test_export_button_is_disabled_in_snapshot_mode(snapshot_bundle, page):
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    buttons = page.locator("button", has_text="导出交付包")
    assert buttons.count() >= 1
    for i in range(buttons.count()):
        assert buttons.nth(i).is_disabled(), "门禁未通过时导出按钮不得可用"


def test_export_button_says_it_is_unimplemented(snapshot_bundle, page):
    text = _page_text(snapshot_bundle, page)
    assert "导出交付包（未实现）" in text


def test_freeze_button_is_disabled_in_snapshot_mode(snapshot_bundle, page):
    """原"冻结"只改浏览器本地状态, 什么也没冻。快照模式下禁用。"""
    page.goto((snapshot_bundle / "index.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    buttons = page.locator("button", has_text="冻结版本")
    assert buttons.count() >= 1
    for i in range(buttons.count()):
        assert buttons.nth(i).is_disabled()


def test_gate_verdict_is_block_for_this_sample(snapshot_bundle):
    """前提确认: 这份样本的门禁确实是 BLOCK, 否则上面的断言没有意义。"""
    payload = _payload_of(snapshot_bundle)
    assert payload["export_gate"]["verdict"] == "BLOCK"
    assert payload["export_gate"]["formal_export_implemented"] is False
