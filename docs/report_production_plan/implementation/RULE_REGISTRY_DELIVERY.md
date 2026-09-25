# RuleRegistry v0 交付说明

日期：2026-09-25 · 决议记录 `DECISION_LOG.md` 条目 016
针对 `kernel_gaps_after_wiring` 的**第一号缺口**

---

## 1. 问题

前端接完线后（条目 015）清点出：**53 个 `rule.*` 依据 ID，已登记标题 0 个。**

系统在义务判定、计算器、保证事项和正文里引用这些 ID，但没有任何注册表记录
它们指向哪部规范的哪一条。也就是说，报告里每一句"依据 XXX"都指向一个空壳——
**无法向审查人员出示条文，也无法核对引用是否正确。**

---

## 2. 做了什么

| 件 | 位置 |
| --- | --- |
| 注册表 | `registries/RuleRegistry_v0.yaml`（28 条） |
| 解析器 | `src/cpswc/rule_registry.py` |
| lint 规则 | `src/cpswc/lint.py` `lint_rule_registry_refs`（RULE_001..004） |
| payload | `rule_refs` 每条带核验结果；新增 `rule_coverage` 汇总块 |
| 界面 | 注脚与依据库页改为三态显示 + 条文原文 + 缺陷提示 |
| 测试 | `tests/test_rule_registry.py`（14）+ payload/浏览器用例 |

### 三态，一个都不许含糊

```
VERIFIED_TEXT  条文原文已从本地原件抽取并核对，可直接向审查人员出示
DECLARED       已定位到文件（可能到章/条），但没抓原文
UNREGISTERED   不在注册表里 —— 系统不知道这个 ID 指向哪一条
```

**DECLARED 不许带 quoted_text。** 贴了原文就等于声称核对过，
而"看起来像证据的东西"比没有证据更危险。`lint_rule_registry()` 会拦。

**不给单一"依据覆盖率"百分比。** 压成一个数会立刻抹掉最要紧的区别——
"定位到文件了"和"条文核对过了"完全是两回事。界面四档分开摆。

---

## 3. 当前覆盖（惠州样本）

```
引用 53 个 ID
  已核原文     4     条文可直接出示
  已定位      24     知道出自哪份文件，条文没抓
  未登记      25     不知道指向哪一条 —— 引用是空壳
  已定位到条款 24     其余只到文件级
引用缺陷      2
```

### 已核原文的 4 条

| ID | 文件 | 条款 |
| --- | --- | --- |
| `rule.ministry_order_53` | 水利部令第 53 号 | 第七条（报告书/报告表阈值） |
| `rule.guangdong.fa_gai_2021_231` | 粤发改价格〔2021〕231 号 | 二、征收标准（一）0.6 元/m² |
| `rule.guangdong.shui_gui_fan_zi_2026_1` | 粤水规范字〔2026〕1 号 | 一（转致 231 号，全额征收） |
| `rule.2023_177.review_dimension_county_breakdown` | 办水保〔2023〕177 号 | 二、关于项目概况 第 4 项 |

这四份 PDF 有完整文字层，`pdftotext` 直接抽取核对。

### 为什么只有 4 条

其余原件多为扫描件，抽不出文字：

| 原件 | 页数 | 文字层 |
| --- | --- | --- |
| 办水保函〔2026〕232 号（模板） | 28 | **0 字符**（Canon 扫描件） |
| GB 50433-2018 | 67 | **0 字符** |
| GB/T 50434-2018 | 27 | **0 字符** |
| GB 51018-2014 | 127 | 5117 字符（零散，5.7.1 不在其中） |
| 办水保〔2018〕135 号 | 15 | 840 字符，OCR 质量差 |

这些只能逐页读图抓取，是一次独立的工作量，本批未做——所以状态老实写 DECLARED，
界面上显示"**未抓取**，不能直接向审查人员出示"。

---

## 4. `rule.t2026.*` 25 条为什么刻意不登记

**不许推断来源。命名空间像什么不算证据。**

`ObligationSet_v0.yaml` 的头部自述覆盖"2026 模板 / 2018 格式 / 广东惠州 v0 范围"
的混合来源，而**单条义务并没有声明自己出自哪一份**。前缀 `t2026` 只是命名习惯：
例如 `rule.t2026.spoil_level_4_geology`（弃渣场 4 级需地质报告）的实际依据
更可能是 GB 51018 而不是 2026 模板。

按前缀批量补进去，会让界面从"25 条未登记"变成"25 条已登记"，
缺口凭空消失，而一条都没真正查过。这正是本项目最该避免的事。

`test_t2026_namespace_stays_unregistered` 就是拦这个的：
哪天有人"顺手"按前缀批量填，测试会失败。

**下一步**：回到 `ObligationSet_v0.yaml` 逐条补 `source_document` + `clause_ref`，
那是一次独立的溯源工作。

---

## 5. 顺带查出的两处引用缺陷

建注册表时发现的，不是本来要找的：

### `rule.template_2026.section_11` → `NONEXISTENT_CLAUSE`

**2026 模板没有第 11 章**，主体章止于第 10 章"水土保持管理"。
该 ID 沿用 2018 版的 11 章结构。结论已迁至 1.9（综合说明末节），
`stable_id: sec.conclusion` 正确地保持未改名，
但引用它的 `narr.conclusion.*` 四个段落仍写 `section_11`。

### `rule.template_2026.section_7` → `STALE_CITER`

规则本身没问题（第 7 章确实是"水土流失防治"），
但 `narr.soil_loss_prevention.benefit_analysis.*` 引用它，
而效益分析在 2026 模板已**跨章迁到 9.2**
（见 `ReportContentRequirements_v1.yaml` 的 `stable_id_migrations`）。

**两处都对应 `stable_id_migrations` 里已登记的迁移** ——
章节 ID 迁移做对了，但 narrative 模板里的 `source_rule_refs` 没跟着改。

这两条已记进注册表的 `defect` 字段，lint 报 WARN（RULE_004），
界面在依据库页顶部显示。**本批没有动 narrative 模板** —— 改引用是内容变更，
应当单独决策。

---

## 6. 设计上的两个防伪点

1. **`source_file` 必须是仓库内真实存在的路径**，lint 逐条检查文件在不在。
   登记一个查不到的出处，比不登记更糟——它看起来像证据。

2. **子条目继承文件信息，但不继承 `verification_status`**。
   `rule.gb_t_50434_2018.table_4_0_2_5` 从父条拿到文件号和路径，
   但"核没核过"必须自己声明。父条核过不代表子条核过。

---

## 7. 跑法

```bash
PYTHONPATH=src python3 -m pytest tests/test_rule_registry.py -q   # 14 passed
PYTHONPATH=src python3 -m cpswc.lint                              # ERROR=0 WARN=2(RULE_004)
PYTHONPATH=src python3 -m cpswc.frontend_payload samples/huizhou_housing_v0.json
```

注意：加入 RuleRegistry 后 `generation_input_hash` 变了
（`8d0cc7ab2ac515e6` → `eda8d8b5e8f243bf`）——注册表进了 `registries/` 目录摘要，
**改依据登记会让旧快照失效**，这是对的：依据变了，报告的引用就得重新核。

---

## 8. 下一步

1. **补 `rule.t2026.*` 的来源**——回 ObligationSet 逐条溯源（25 条）
2. **读图抓 232 号 / GB 标准的条文原文**——把 DECLARED 升成 VERIFIED_TEXT（24 条）
3. **决定要不要改那两处陈旧引用**——`section_11` → 1.9，`section_7` → 9.2
