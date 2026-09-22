# 前端接线计划（F 批）

版本：**1.1**｜编制 2026-09-22｜代码基线：`fa3a9ae`
状态：**计划，待批准。** 本文件不是已实施的证明。

> **v1.1 修订说明。** v1.0 经评审发现 5 个生产级漏洞，核心判断是：
> **v1.0 把"后端已经有统一状态"想得过于乐观**，照它实施会把刚消灭的多套口径
> 重新复制到 payload 和 JSX 里。五条全部核实属实（其中两条已在代码里复现），
> 本版据此重写。主要变化：
>
> 1. 取消逐字段 mock 回落，改**全局三态** `PROJECT_SNAPSHOT / DEMO / PAYLOAD_ERROR`
> 2. 新增 **F-0 契约补强**——前端接线前必须先让后端有唯一的字段状态出口
> 3. ExportGate 停止二次合并 derived（**已复现的活 bug**，独立修复）
> 4. 新增后端 `intake_issues` 投影，取代"按 stage=INPUT 过滤"
> 5. 新增 **F-1B 全壳诚实化**——只改 7 个页面不够，全局壳仍会说假话

## 0. 为什么现在做这件事

P0 A/B 批把内核从"会说假话"改成"会说缺什么"，但**这些结果目前一个都到不了用户眼前**——前端是纯静态 mock，和后端零连接。

更要命的是：**mock 与后端现在的真实输出互相矛盾**。逐条实测对照：

| 前端 mock 现在显示 | 后端 `1e8da8a` 实际产出 |
| --- | --- |
| `SIX_RATES` 六项全 `ok: true`，实现值 97.6% / 1.0 / 95.0% … | 六项全部"**待确认效果来源**"——候选值语义未经确认，不进达标比较 |
| `Delivery.CHECKS`：规则审查"通过 · 无阻塞项" | `export_gate` 返回 **BLOCK**，含 GATE_001/005/006 多条 |
| `Delivery.CHECKS`：正文状态"通过 · 覆盖率 92%" | 对照 2026 模板真实覆盖率 **0 / 64**，其中 38 项未实现 |
| `TODOS`：「当前无导出阻塞项 · 通过」 | 惠州样本 84 条 BLOCK 级诊断 |
| `INTAKE_MISSING` 全部 `block: false` | BuildContext 产出的缺口带 BLOCK/WARN 分级 |
| `KEY_FACTS.src` 是一句自由文本（"土石方平衡"） | 每个字段有 `Provenance`（计算/enrich/预存/事实）+ `ValueState` |

**接线不是换数据源，是让界面有能力表达"不知道""待确认""未实现"。** 现在的 UI 只有"通过 / 待确认"两档，装不下后端的状态。

这条也是 [[product_layer_pivot]] 的评估口径：看**契约咬合**，不看 UI 漂亮与否。

## 1. 接线方式：构建期 payload，不起服务端

现状：`index.html` 用 Babel-in-browser 直接加载 `data.jsx` 与 16 个 `pages/*.jsx`，全局变量传递，**没有任何 `fetch`，没有服务端**。双击 `index.html` 就能跑。

**不为这件事起 API 服务。** 起服务会把"双击就能看"的 demo 变成需要部署的东西，违背产品壳当前的用途。

方案：Python 侧导出一份 payload，前端按**全局三态**消费。

```
samples/huizhou_housing_v0.json
        │
        ▼  python -m cpswc.frontend_payload <project.json> -o output/frontend/
   output/frontend/<project-code>/<generation-input-hash>/
        index.html  payload.js  pages/...      ← 自包含, 双击可开
        │
        ▼  window.CPSWC_PAYLOAD = { ... }
```

### 全局三态（**不得逐字段回落**）

v1.0 写的 `LIVE('six_rates') ?? MOCK_SIX_RATES` 是最危险的写法：payload 已加载但某字段缺失时，页面会**悄悄混入 mock**，用户看到一半真实一半演示。取消。

| `data_mode` | 触发条件 | 行为 |
| --- | --- | --- |
| `PROJECT_SNAPSHOT` | payload 存在且 schema 全量校验通过 | **完全禁止 mock**。任何业务数值只能来自 payload |
| `DEMO` | 根本没有 payload | 全部用 mock，全局「演示数据」斜纹角标 |
| `PAYLOAD_ERROR` | payload 存在但不完整 / 版本不兼容 / 解析失败 / 壳与 payload 不匹配 | **阻断错误页**，绝不回落 mock |

判定在**加载时一次完成**，之后不再逐字段判断。

`is_live` 改名 `data_mode`——静态生成的文件不是"实时数据"。界面显示「**项目快照**」并同时显示项目名、生成时间、`generation_input_hash`。

### 边界：UI 配置不是 mock

`NAV` / `ROLES` / `STATUS_STYLES` / 图标映射是**界面配置**，不是项目数据。它们保持静态，不进 payload，也不受三态约束。三态只管**业务/项目数据**。把导航菜单 payload 化是走错方向。

### 输出位置与壳漂移防护

- 写到 `output/frontend/<project-code>/<generation-input-hash>/`，**不写 `src/frontend/`**——那会留下上一个项目的数据，也容易把真实客户数据混进源码目录。
- 不同项目、不同输入互不覆盖；**临时目录 + 原子替换**，不允许半写状态被打开。
- **壳漂移防护**：payload 记录 `shell_digest`（`src/frontend/` 源码摘要），生成时把同一摘要盖进复制出去的壳；加载时比对，不一致 → `PAYLOAD_ERROR`。否则"旧壳 + 新 payload"会无声错配。
- ⚠ **`output/` 当前不在 `.gitignore`**（只忽略了 `/outputs/` 复数），且已存放其他项目的客户材料。**F-0 必须补 `/output/`**，否则一次 `git add -A` 就会把客户数据推进仓库。

## 2. payload 契约（F-1A 的交付物）

由 `build_snapshot_dict()` + `project_narrative()` + `evaluate_report_quality()` + `check_export_readiness()` 组装，**不新增第五套事实**：

```jsonc
{
  "schema_version": "cpswc_frontend_payload_v1",
  "data_mode": "PROJECT_SNAPSHOT",    // 由生成器写死; 前端另判 DEMO / PAYLOAD_ERROR
  "generated_at": "...",              // 审计元数据，不进任何语义比较
  "shell_digest": "...",              // src/frontend 源码摘要, 防壳漂移
  "project": { "name": "...", "code": "...", "species": "..." },

  "hashes": {                          // P0-06
    "hash_schema_version": "cpswc_hash_v1",
    "fact_snapshot_hash": "...",
    "generation_input_hash": "..."     // 复核有效性看它
  },

  // Facts 页 —— **直接来自 BuildContext.project_fields()**, 见 F-0.1。
  // 前端与生成器都**不得**重新解析值状态。字段全集 = FIR 登记字段 ∪ 实际消费字段,
  // 含 MISSING(缺失字段必须出现, 否则"缺什么"就看不见了)。
  "facts": [{
    "field_id": "field.fact.land.total_area",
    "state": "PRESENT|MISSING|INVALID|CONFLICT|NOT_APPLICABLE",
    "value": 9.5,                      // 仅 state=PRESENT 时有意义
    "unit": "hm²",
    "provenance": "PROJECT_FACT|CALCULATED|PRE_STORED_DERIVED|ENRICHED_VIEW|STALE_HISTORICAL",
    "stale_value": null,               // 仅 STALE_HISTORICAL 时非空, 只作历史展示
    "conflicts": [["CALCULATED", 2.0], ["PRE_STORED_DERIVED", 1.0]],
    "note": "单位取自 FIR 登记契约 (万元), 数据本身未带单位",
    "canonical_name": "总占地面积"      // 取自 FIR, 供界面显示中文名
  }],

  "obligations": {                     // Rules 页
    "triggered": [], "not_triggered": [],
    "unknown": [{ "id": "...", "reason": "缺失依赖 field.xxx" }]
  },

  "quality": {                         // Overview 页
    "coverage_state": "measured|unknown",
    "content_coverage": 0.0,
    "applicable_leaf_count": 64, "complete_leaf_count": 0,
    "unimplemented_leaf_count": 38,
    "rendered_block_count": 38,        // 只表示"渲染出文字的块数"
    "mapped_leaf_count": 26,           // 已建立实现映射 (≠ 有产出)
    "with_output_leaf_count": 0,       // 本次实际产出文字的叶子数 (单独测)
    "counts": { "unresolved_critical_count": 84, ... },
    "is_submittable": null             // 只能由正式门禁写，P0-08 之前恒为 null
  },

  // 诊断**分层给出**, 不合并成一锅 —— 四个来源有重叠, 直接拼接会把数量放大,
  // 前端也分不清"输入问题 / 正文问题 / 门禁结果"。去重规则见 F-0.3。
  "findings": {
    "build":    [ /* BuildContext: 取值层 */ ],
    "narrative":[ /* 模板产出 */ ],
    "quality":  [ /* ReportQualitySummary 汇总层 */ ],
    "gate":     [ /* ExportGate */ ],
    "counts_by_severity": { "BLOCK": 0, "WARN": 0, "INFO": 0 }   // 去重后
  },

  // F-2 专用投影。**不是 findings 的别名**, 由后端单独生成, 见 F-0.3。
  "intake_issues": [{
    "issue_id": "...",
    "category": "MISSING|INVALID|CONFLICT|ASSUMPTION|UNVERIFIED_SOURCE",
    "severity": "BLOCK|WARN|INFO",
    "field_refs": [], "affected_section_refs": [], "affected_artifact_refs": [],
    "impact_known": true,              // false → 界面显示"影响范围尚未建立", 不得编造
    "message": "...", "remediation": "...",
    "origin": "build|narrative|quality"
  }],

  "narrative": [{                      // Narrative 页
    "section_id": "sec.conclusion",
    "display_number": "1.9",           // 取自 ReportContentRequirements_v1
    "title": "结论",
    "render_status": "full|skeleton|not_applicable",
    "applicability": "APPLICABLE|NOT_APPLICABLE|UNKNOWN",
    "content_role": "LEAF_CONTENT|PARENT_INTRO",
    "paragraphs": [{ "text": "...", "assertion_class": "...", "review_refs": [] }],
    "finding_codes": []
  }],

  "requirements": [{                   // 差异表 / 缺口清单
    "id": "req.t2026.1.9", "display_number": "1.9", "title": "结论",
    "stable_id": "sec.conclusion",     // **允许 null** —— 未实现要求确实尚未映射
    "implemented": true, "is_leaf": true,
    "has_output": true                 // 本次是否真的产出了文字 (可测, 与 implemented 分开)
  }],

  "six_rates": [{                      // 六率表
    "indicator": "水土流失治理度", "target": "97.49",
    "actual": "99.47（候选·待确认，源自 actual_derived）",
    "result": "待确认效果来源"
  }],

  "export_gate": { "verdict": "BLOCK|WARN|PASS", "findings": [...] }
}
```

**契约纪律**：payload 是**只读投影**，前端不得回写；所有数值只能来自上述结构，不得在 JSX 里二次计算业务量。

## 3. 界面要新增的状态（这是真正的工作量）

现有 `STATUS_STYLES` 只有绿（通过/LIVE/已满足）、黄（待确认）、灰等几档。需要补：

| 新状态 | 用在哪 | 视觉建议 | 不能混同的旧状态 |
| --- | --- | --- | --- |
| **适用性未知** | 章节、义务 | 紫/靛 + `?` | ≠「不涉及」。这是整个 P0-02 的核心 |
| **候选·待确认** | 六率实现值、效果候选 | 黄底 + 虚线框 | ≠「已达标」也 ≠「未达标」 |
| **未实现** | 内容要求清单 | 灰 + 斜杠纹 | ≠「不适用」。未实现仍在分母里 |
| **BLOCK / WARN / INFO** | 所有 finding | 红 / 橙 / 蓝 | 现有「待确认」一档装不下 |
| **复核失效 STALE** | 结论段、复核记录 | 红 + 时钟 | ≠「未复核」。这是"曾经确认过但输入变了" |
| **历史值（计算失败）** | Facts 页 | 灰删除线 + 提示 | ≠ 当前有效值 |
| **演示数据** | 全局角标 | 斜纹页眉条 | 必须一眼可辨 |

**硬规则**：任何地方不得再出现凭空的「通过」「无阻塞项」「覆盖率 92%」。这些数只能来自 payload。

## 4. 分阶段

每阶段独立可验收、可停。**不要一次做完。**

### F-0 契约补强（**前端一行代码都不写之前必须先做**）

v1.0 最大的问题是假设"后端已经有统一状态"。实测不成立。不先补这一层，payload 生成器就得自己重新推断值状态——那等于把刚消灭的多套口径复制一份到生成器里。

**F-0.1 `BuildContext.project_fields()`——唯一的字段状态序列化出口**

当前 `build_snapshot_dict()` 只给出扁平值 + `_source_map` + `_build_findings`，**没有完整 `ResolvedValue`，缺失字段也不进统一视图**（`unified_view()` 显式 `continue` 掉 MISSING）。

新增单一出口，每项直接输出 `field_id / state / value(仅 PRESENT) / unit / provenance / stale_value / conflicts / note`。

- 字段全集 = **FIR 登记字段 ∪ 本次实际消费字段**，不是只遍历"已经有值"的。缺失字段必须出现——否则"缺什么"在界面上根本看不见。
- 前端与 payload 生成器**都不得**重新解析值状态。

**F-0.2 ExportGate 停止二次合并 derived（已复现的活 bug，独立修复）**

当前 `check_export_readiness()` 仍执行 `facts + _pre_stored_derived + derived_fields`，与 `build_snapshot_dict()` 的约束（`_pre_stored_derived` 只供对照）直接矛盾。

**已复现的后果**：某字段本次计算失败 → BuildContext 判 MISSING / `STALE_HISTORICAL` 并把它挡在统一视图外 → 门禁重新合并旧 derived → **GATE_001 认为该 CRITICAL 字段"有值"而放行**。历史值被当成当前值通过了门禁。

这不只是 F-6 的前置条件，它是已提交代码里的正确性缺陷，**应独立修复并加回归测试**，与前端做不做无关。修复方向：门禁只消费 BuildContext 选定的统一视图与诊断。

**F-0.3 canonical findings + `intake_issues` 投影**

- 四个来源（build / narrative / quality / gate）**分层给出**，不拼成一锅；定义去重键（`code` + `target_ref` + `message`）与 `counts_by_severity`。
- 新增 `intake_issues`：F-2 专用，**不是按 `stage=INPUT` 过滤**——实测有 `VALUE_MISSING` 是在 `RENDER` 阶段发现的，它们同样要向甲方收资；而 `DEMO_ASSUMPTION` / `INPUT_CONFLICT` / `SOURCE_UNVERIFIED` 也不是简单的"缺资料"，需要 `category` 区分。
- **"影响哪些章节/表格"由后端生成**，依据：模板 `TEMPLATE_SPEC.input_fields`、表格 `data_source_refs`、`ReportContentRequirements_v1` 的 stable_id 映射。建立不起来可靠关系时 `impact_known=false`，界面显示"影响范围尚未建立"，**不得由 JSX 猜测或编造**。

**F-0.4 三态与 schema 定义**

`PROJECT_SNAPSHOT / DEMO / PAYLOAD_ERROR` 的判定条件、schema 全量校验清单、`shell_digest` 比对规则。

**F-0.5 `.gitignore` 补 `/output/`**

当前只忽略 `/outputs/`（复数）。`output/` 里已有其他项目的客户材料（docx/pptx/bid）。payload 要写进 `output/frontend/`，不补这一行就是在制造客户数据泄漏进仓库的路径。

**F-0 验收**：`project_fields()` 与 gate 修复各有回归测试；四样本 `intake_issues` 可生成且影响关系要么可靠要么显式标未建立。

### F-1A payload 管道

- `src/cpswc/frontend_payload.py`：CLI 输出到 `output/frontend/<project-code>/<generation-input-hash>/`
- 自包含复制壳（`index.html` + `pages/` + `data.jsx`）+ `payload.js`；**临时目录 + 原子替换**
- schema **全量**校验；`shell_digest` 盖章
- **测试**：四样本各生成一次，断言 schema 完整、数值与 `build_snapshot_dict` / `project_fields()` 逐项一致、原子性（中断不留半成品）

### F-1B 全壳诚实化（**只改 7 个页面不够**）

即使页面接好，全局壳仍会让用户以为系统能冻结、能写入、能正式导出。实测全壳有 **50 处**硬编码肯定状态，散在 12 个文件里。

- 顶栏「项目完成度 91%」「冻结状态」「冻结版本」按钮、「导出交付包」按钮
- `Workspace` 的 mock 项目列表与完成度百分比
- `IntakeWizard` 的模拟上传 / 确认写入事实层

处置：

- 项目名称、完成状态全部取自 payload
- `PROJECT_SNAPSHOT` 模式下**禁止本地假冻结**（当前"冻结"只改浏览器状态）
- P0-08 之前，「导出交付包」**禁用**并显示"正式发布能力未实现"
- 所有上传 / 确认写入等假交互标为演示或禁用
- **payload 项目与 Workspace 所选项目不一致时，拒绝进入工作台**
- 全仓搜索消除硬编码的「通过 / 无阻塞 / 达标 / 可下载 / 覆盖率」，**不只是改计划列出的那几个组件**

### F-2 缺资料与数据问题清单（产品价值最高）

- 数据源是后端 `intake_issues`，不是前端过滤 findings
- 每条显示：category / severity / 缺哪个登记字段 / 影响范围（或"尚未建立"）/ remediation
- 可导出一页"待甲方提供资料清单"，必须带：**「工作草稿，非正式报告附件」水印** + 项目名 + 生成时间 + `generation_input_hash` + BLOCK/WARN 分级 + 未确认影响范围的明确提示
- **验收**：拿惠州样本给编制单位看，判断它是否真的能指导收资（含那 6 条 `placeholder stub` 的 DEMO_ASSUMPTION）

### F-3 Overview 诚实仪表盘

覆盖率按四行显示，**不做减法推断**：

```
正式要求      64
已建立实现映射 26     ← 只说明映射存在
其中本次有产出  N      ← 单独测, 与映射分开
未实现        38
确认完成       0
```

- `rendered_block_count` 标注"仅表示渲染出文字的块数"，不得当完成度
- `TODOS` 换成去重后的 findings；删掉「当前无导出阻塞项」
- `is_submittable=null` 显示"未判定（正式门禁未实现）"

### F-4 Facts 页来源与状态

直接渲染 `project_fields()`：Provenance 标签、MISSING 不显示成"—"、CONFLICT 并列各来源值、计算失败显示历史值并标 stale、别名候选冲突就地提示。

### F-5 Narrative 页质量态

按 `ReportContentRequirements_v1` 的 `display_number` 排序（1.9 结论、9.2 效益分析…）；UNKNOWN 章节显示"待定"而非"不涉及"；段落按 `assertion_class` 着色；38 项未实现列为灰条占位。

### F-6 Delivery 门禁真相

**依赖 F-0.2 已修**，否则展示的是不一致的门禁结果。`CHECKS` 全换成实际 findings；BLOCK 时不得显示"可下载"；显示两个 hash 与 `lifecycle_freeze_note`。

### F-7 六率与表格

六率表用 payload 的 `six_rates`（含"候选·待确认"）；Tables 页接真实 `TABLE_PROJECTIONS`。

## 5. 依赖与顺序

```
F-0 契约补强 ──▶ F-1A payload 管道 ──▶ F-1B 全壳诚实化 ──▶ F-2 缺资料清单
                                                              │
                                              F-3 / F-4 / F-5 / F-7
                                                              │
                                              F-6 (依赖 F-0.2 已修)
```

**F-0 之前不写任何前端代码。** F-1B 必须在 F-2 之前——否则清单做得再好，用户仍会被顶栏的"完成度 91%"和"导出交付包"按钮误导。

## 5.1 测试要求

Python 单测不够，**必须加浏览器级场景**（建议 `webapp-testing` / Playwright）：

| 场景 | 断言 |
| --- | --- |
| 无 payload | 全局显示演示模式角标；不显示任何项目快照标识 |
| 完整 payload | **页面上不出现任何 mock 数值**（逐项比对 mock 常量不出现） |
| 部分 / 版本不兼容 / 壳不匹配 payload | 显示阻断错误页；**绝不回落 mock** |
| ExportGate=BLOCK | 顶栏与 Delivery 页**都没有**可用的交付按钮 |

## 6. 与 C 批的关系

**F 批不依赖 C 批，也不替代 C 批。**

- F-6 会把 `export_gate` 的真实结论显示出来，但门禁本身仍无草稿/正式之分（P0-08 未做）。界面必须写明"当前无正式发布能力"，不得让 BLOCK 看起来像可以点"导出"。
- 附图仍是 matplotlib 示意图；Maps 页接线时必须标 DEMONSTRATION（P0-07 未做）。

## 7. 不做的事

- 不起 API 服务、不引入构建工具（保持双击 `index.html` 可跑）。
- 不在 JSX 里算任何业务量——数只能来自 payload。
- **不逐字段回落 mock。** 三态是全局的；`PROJECT_SNAPSHOT` 下 mock 完全禁用。
- **不在 payload 生成器里重新推断值状态**——只能搬运 `project_fields()` 的输出。
- 不为了界面好看而隐藏 BLOCK；不新增前端自算的百分比。
- **不做减法推断**：`64-38=26` 只能说明 26 项有映射，不能说明它们有产出。
- 不把 payload 写进 `src/frontend/`。
- 不碰 `registries/` 与既有 governance 文件。
- 不实现那 38 项缺失内容——前端的职责是让它们**可见**。

## 8. 建议的起点

**F-0 单独做完并验收。** 它全部是后端契约工作，不含任何前端代码，但决定了后面每一步是"搬运"还是"重新推断"。其中 F-0.2（ExportGate 停止二次合并）是已复现的活 bug，无论 F 批是否继续都应该修。

F-0 通过后再做 F-1A → F-1B → F-2。**F-2 之前必须先过 F-1B**——否则清单做得再好，用户仍会被顶栏的"完成度 91%"和"导出交付包"按钮误导。

v1.0 曾建议"F-1+F-2 一起做"，**该建议作废**：它跳过了契约补强与全壳诚实化两道必要工序。
