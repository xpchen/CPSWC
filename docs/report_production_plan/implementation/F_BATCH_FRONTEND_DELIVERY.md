# 前端接线 F-1A / F-1B / F-2 交付说明

日期：2026-09-23 · 对应 `FRONTEND_WIRING_PLAN.md` v1.1 · 决议记录 `DECISION_LOG.md` 条目 013

本批的目标不是"把界面做完"，而是**让界面停止说谎**：真实项目快照里不许出现别的项目的名字、
不许出现写死的"通过 / 无阻塞 / 达标"，尚未接线的地方必须自己承认没接线。

---

## 1. 做了什么

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| F-1A | payload 生成管线：`src/cpswc/frontend_payload.py`（`build_payload` / `validate_payload` / `render_standalone_html` / `write_bundle` + CLI） | DONE |
| F-1B | 全壳诚实化：三态角标、未接线页自曝、Overview 首屏假结论下线 | DONE |
| F-2 | 收资清单接线：向导第 4 节由后端 `intake_issues` 驱动，可导出「待甲方提供资料清单」 | DONE |
| F-3..F-7 | Overview / Facts / Narrative / Delivery / 六率与表格逐页接线 | **未开始** |

生成命令：

```bash
PYTHONPATH=src python3 -m cpswc.frontend_payload samples/huizhou_housing_v0.json
# → output/frontend/<project-code>/<generation-input-hash>/index.html
```

---

## 2. 三个非预期发现

### 2.1 `file://` 下多文件壳必定白屏

原壳用 `<script type="text/babel" src="pages/X.jsx">`，而 Babel 是用 XHR 取这些文件的。
Chrome 在 `file://` 下按 CORS 直接拒绝（`origin 'null'`），结果是**整页白屏**——
"双击 index.html 就能跑"对拆成多文件的壳并不成立。

改为 `render_standalone_html()` 把全部 JSX 与 payload 内联进单个 HTML。
惠州样本 671 KB，可以整个发给别人，双击即开。

### 2.2 壳漂移检查曾经是摆设

`data.jsx` 靠比对 `<meta name="cpswc-shell-digest">` 与 `payload.shell_digest` 来发现
"旧壳配新数据"。但单文件内联时那个 meta **原本是抄 payload 里的值写进去的**，
两边永远相等 —— 浏览器验收实测把 `payload.shell_digest` 改成 `000…`，照样畅通无阻。

已改为**现场按壳文件算**。回归测试：`test_shell_digest_meta_is_computed_not_copied`。

### 2.3 喂错文件会静默产出"空项目快照"

`samples/review_comments_huizhou_v0.json` 是审查意见文档（`$schema: CPSWC_ReviewComment_v0`），
不是项目输入。把它喂进 `build_payload()`，管线一路畅通，最后产出一个项目名、编码全空的 bundle——
顶栏「项目快照」下面挂着一片空白，比直接报错危险得多。

已补 `_require_project_input()`（拒绝审查意见文档、拒绝没有 `project`/`facts` 的输入），
并让 `validate_payload()` 拒绝空 `project.name`。

---

## 3. F-1B 的取舍：为什么不是"消灭全部 mock"

各页的 mock 不是几个散落的字面量，而是页组件自带的整套演示数据
（`Facts.jsx` 有自己的事实表，`Narrative.jsx` 有自己的正文，`Tables.jsx` 有自己的六率行）。
把它们换成真数据 = F-3..F-7 的工作量，不是本批范围。

本批**不假装接线**，改为让未接线的页面自曝：

- `UnwiredNotice`（`App.jsx`）在快照模式下给每个未接线页面加一条琥珀色提示：
  「本页尚未接入项目数据。以下内容仍是示例工程的演示数据，与顶栏所示项目无关。」
- 判定依据是**白名单** `window.CPSWC.WIRED_PAGES`，不是黑名单。
  默认未接线，接好一个加一个 —— 漏加只会多显示一条提示（保守），
  而黑名单漏删会让 mock 冒充真数据（危险）。

### 三个例外：肯定状态整块下线

计划里的 F-1B 只要求给未接线页面加提示，但评审要求是
"**搜索并消除**全部硬编码的『通过、无阻塞、达标、可下载、覆盖率』等肯定状态"。
只加提示压不住三处最响的假结论，它们在快照模式下整块下线或改接真数据：

#### Overview 首屏 hero：整块下线

首屏 hero 写死了**另一个项目的名字**，以及「无导出阻塞」「2 项专家确认」
（惠州样本的真实门禁是 **BLOCK，7 条阻断**），下面四张卡写死 94% / 88% / 92% / 「可生成」。

这是用户一进来看到的第一屏，紧挨着顶栏的真项目名。只加一条提示压不住。
快照模式下**整块隐藏**，代之以一句指路：真实状态见顶栏的内容完成度、门禁结论，
以及收资向导第 4 节。等 F-3 正式接线后再恢复。

#### 交付包页：检查项改接真门禁，文件清单清空

原本写死 11 项「通过」（含「规则审查：无阻塞项」「正文状态：覆盖率 92%」）
与 14 个「可下载」文件，而惠州样本的真实门禁是 **BLOCK，7 条阻断**，
正式导出根本未实现。

快照模式下：

- 检查项改为 `export_gate.findings` 的实际条目。**不补齐成一张全绿的表**——
  门禁只报问题，不出具「哪些项通过」，所以副标题写「门禁结论 BLOCK，报出 N 条；
  门禁只报问题，不出具『通过』结论」，也不再显示「N / M 项通过」。
- 门禁零条目时显示：「门禁未报出问题。注意：这只说明**已登记的门禁规则**没有拦下什么，
  不等于方案已具备报批条件。」
- 文件清单清空，代之以「正式导出能力尚未实现，本次快照**没有产出任何交付文件**」。
- 「模拟正文金额被人工改写」按钮隐藏——它会伪造一条本项目并不存在的风险。
- 绿色的「数文一致性检查通过」条隐藏。

#### 规则审查页：「无阻塞」下线

顶部 chip 与「审查状态：无阻塞」改为「未判定（本页未接线）」。

---

## 4. F-2 收资清单

### 界面（`pages/IntakeList.jsx`）

第 4 节「当前缺失资料 / 待甲方提供」完全由后端 `intake_issues` 驱动。
**界面不做二次判断**：分类、严重度、影响范围全部照搬后端结论。
后端解析不出影响关系时，如实显示「影响范围尚未建立」——
不用「可能影响全部章节」之类的话填充。

向导其余部分（1–3、5–6 节）标注为演示数据；「上传资料」「确认写入事实层」
在快照模式下**禁用并标注（未实现）**——它们只改浏览器本地 state，写不进事实层。

演示模式下**不产出收资清单**：收资清单是向甲方索要资料的依据，
用 mock 生成一份等于凭空向客户要东西。

### 导出件

「导出待甲方提供资料清单」产出独立 HTML，强制带上：

- 斜向水印「工作草稿 · 非正式报告附件」
- 顶部红框声明：不构成报告的任何正式组成部分，也不代表方案已通过任何审查
- 项目名 / 项目编码 / 生成时间 / `generation_input_hash`
- BLOCK / WARN / INFO 分级与计数
- 「标注『影响范围尚未建立』的条目，**不代表它不影响任何章节**」

文件名：`待甲方提供资料清单_<项目编码>_<hash前8位>.html`。

---

## 5. 惠州样本实测

```
内容要求 64 项 | 已建立映射 26 | 本次有产出 26 | 未实现 38 | 确认完成 0
收资清单 24 项 {'BLOCK': 11, 'WARN': 13, 'INFO': 0}
导出门禁 BLOCK (7 block)
```

注意「确认完成 0」：没有任何一项内容要求被确认完成。
「已建立映射 26」只证明有 26 项被标为 implemented，不证明它们都有合格产出。

---

## 6. 测试

| 层 | 文件 | 条数 |
| --- | --- | --- |
| Python | `tests/test_frontend_payload.py`（新增） | 107 |
| Python | 其余 | 759 |
| 浏览器 | `tests/browser/test_data_modes.py` | 27 |

Python 级验的是"payload 里装的是不是后端的真结论"，浏览器级验的是"页面上显示了什么"。
两者缺一不可：页面可以显示对的东西却装错数据，payload 也可以装对却渲染不出来。

浏览器验收自己抓到的三个真缺陷（都已修）：

- Overview 的三元分支里残留一行 JSX 注释 → 整页 JS 报错，16 条用例连带失败。
- Delivery 文件清单清空后，右侧「文件详情」仍取 `files.find(...)` → `undefined.name`，
  **整页白屏**。改为空态提示「本次快照没有产出交付文件」。
- 我自己写的 Overview 占位文案里**引用了**「无导出阻塞」四个字，被
  `test_no_page_claims_a_hardcoded_positive_state` 逮到。已改写措辞。

关键几条：

- `test_facts_are_verbatim_from_project_fields` —— payload.facts 必须**逐字段等于**
  `BuildContext.project_fields()`。生成器不得重新判定值状态。
- `test_failed_write_leaves_no_half_bundle` —— 渲染中途炸掉时不留能被双击打开的半成品。
- `test_unwired_pages_are_labelled` —— 逐页点过去，不在白名单里的都必须自曝。
- `test_wired_pages_contain_no_mock_values` —— 白名单一增长，无 mock 断言自动扩大覆盖面，
  **不需要改测试**。

跑法：

```bash
PYTHONPATH=src python3 -m pytest tests/ --ignore=tests/browser -q   # 866 passed
PYTHONPATH=src python3 -m pytest tests/browser -q                    # 需 playwright + chromium
```

---

## 7. 下一步

F-3..F-7 逐页接线。每接好一页：把页面 id 加进 `WIRED_PAGES`，
`test_wired_pages_contain_no_mock_values` 会自动开始检查该页是否还有 mock。
Overview（F-3）接线后恢复首屏 hero，数据改由 payload 驱动。
