# 前端接线计划（F 批）

版本：1.0｜编制日期：2026-09-22｜代码基线：`1e8da8a`（P0 A/B 批已合入 main）
状态：**计划，待批准。** 本文件不是已实施的证明。

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

方案：Python 侧导出一份 payload，前端优先读它、读不到就回落 mock。

```
samples/huizhou_housing_v0.json
        │
        ▼  python -m cpswc.frontend_payload <project.json> -o src/frontend/payload.js
   payload.js   →  window.CPSWC_PAYLOAD = { ... }
        │
        ▼  data.jsx: const SIX_RATES = LIVE('six_rates') ?? MOCK_SIX_RATES
```

- `payload.js` 是 `window.CPSWC_PAYLOAD = {...}` 一行赋值，`<script src="payload.js">` 引入，**不需要构建工具、不需要跨域**。
- `payload.js` 进 `.gitignore`（它是某个具体项目的数据，不是源码）。
- 缺文件时全部回落 mock，并在界面顶部显示「**演示数据**」角标——这是 P0-09 的纪律：mock 必须可识别，不得冒充真实结果。

## 2. payload 契约（F-1 的交付物）

由 `build_snapshot_dict()` + `project_narrative()` + `evaluate_report_quality()` + `check_export_readiness()` 组装，**不新增第五套事实**：

```jsonc
{
  "schema_version": "cpswc_frontend_payload_v1",
  "is_live": true,
  "generated_at": "...",              // 审计元数据，不进任何语义比较
  "project": { "name": "...", "code": "...", "species": "..." },

  "hashes": {                          // P0-06
    "hash_schema_version": "cpswc_hash_v1",
    "fact_snapshot_hash": "...",
    "generation_input_hash": "..."     // 复核有效性看它
  },

  "facts": [{                          // Facts 页
    "field_id": "field.fact.land.total_area",
    "value": 9.5, "unit": "hm²",
    "state": "PRESENT|MISSING|INVALID|CONFLICT|NOT_APPLICABLE",
    "provenance": "PROJECT_FACT|CALCULATED|PRE_STORED_DERIVED|ENRICHED_VIEW|STALE_HISTORICAL",
    "stale_value": null,
    "conflicts": []
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
    "counts": { "unresolved_critical_count": 84, ... },
    "is_submittable": null             // 只能由正式门禁写，P0-08 之前恒为 null
  },

  "findings": [{                       // 贯穿各页的缺口清单
    "code": "VALUE_MISSING", "severity": "BLOCK|WARN|INFO",
    "message": "...", "target_ref": "...",
    "missing_input_refs": [], "remediation": "...", "stage": "INPUT|..."
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
    "stable_id": "sec.conclusion", "implemented": true, "is_leaf": true
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

### F-1 payload 管道（基础，必须先做）

- 新增 `src/cpswc/frontend_payload.py`：CLI `python -m cpswc.frontend_payload <project.json> -o <out.js>`
- `data.jsx` 顶部加 `LIVE(key)` 读取器 + mock 回落 + 全局「演示数据」角标
- `payload.js` 加入 `.gitignore`
- **契约咬合检查**：payload 的每个字段都能在后端对象上找到出处；无任何前端二次计算
- **测试**：`tests/test_frontend_payload.py` —— 四样本各生成一次，断言 schema 完整、数值与 `build_snapshot_dict` 一致、缺文件时 `is_live=false`

### F-2 缺资料清单进 IntakeWizard（**产品价值最高，建议紧接 F-1**）

这是 A/B 批真正的副产品：一张**字段级**的缺资料清单，直接对应编制单位最花时间的事——跟甲方要资料。

- `INTAKE_MISSING` 换成 payload 的 `findings`（按 `stage=INPUT` 过滤）
- 每条显示：缺哪个登记字段 → 影响哪些章节/表格 → `remediation` 怎么补 → BLOCK/WARN
- 支持按严重度、按章节分组；支持导出成一页"待甲方提供资料清单"
- **验收**：惠州样本能列出真实缺口（含那 6 条 `placeholder stub` 的 DEMO_ASSUMPTION）

### F-3 Overview 诚实仪表盘

- 覆盖率显示 `0/64`，并列出 `未实现 38 / 有产出未确认 26`
- `rendered_block_count` 标注"仅表示渲染出文字的块数"，**不得**当完成度
- `TODOS` 换成 findings 前 N 条；删掉「当前无导出阻塞项」这类硬编码
- `is_submittable` 为 `null` 时显示"未判定（正式门禁未实现）"，不显示"可交付"

### F-4 Facts 页来源与状态

- 每个字段显示 `Provenance` 标签（计算 / enrich 视图 / 预存外部结果 / 项目事实）
- `MISSING` 不显示成"—"；`CONFLICT` 并列显示各来源值；计算失败显示历史值并标 stale
- 别名候选冲突就地提示（条目 003 的两组仍待工程师确认）

### F-5 Narrative 页质量态

- 章节按 `ReportContentRequirements_v1` 的 `display_number` 排（1.9 结论、9.2 效益分析…）
- 适用性 UNKNOWN 的章节显示为紫色"待定"，**不显示"不涉及"**
- 段落按 `assertion_class` 着色；`GAP_STATEMENT` 与 `PROJECT_JUDGMENT` 视觉区分
- 未实现的 38 项要求列为灰条占位，点进去显示"模板要求什么"

### F-6 Delivery 门禁真相

- `CHECKS` 全部换成 `export_gate` 实际 findings
- verdict=BLOCK 时不得显示"可下载/已就绪"
- 显示两个 hash 与 `lifecycle_freeze_note`（"输入已冻结 ≠ 已专业校审通过"）

### F-7 六率与表格

- 六率表直接用 payload 的 `six_rates`（含"候选·待确认"文案）
- Tables 页接真实 `TABLE_PROJECTIONS` 输出

## 5. 依赖与顺序

```
F-1 ──┬── F-2（产品价值最高）
      ├── F-3
      ├── F-4
      ├── F-5 ← 依赖 ReportContentRequirements_v1（已就绪）
      ├── F-6 ← 注意：P0-08 未做，门禁尚无草稿/正式之分
      └── F-7
```

F-2 可以在 F-3~F-7 之前单独上线并拿去给客户看。

## 6. 与 C 批的关系

**F 批不依赖 C 批，也不替代 C 批。**

- F-6 会把 `export_gate` 的真实结论显示出来，但门禁本身仍无草稿/正式之分（P0-08 未做）。界面必须写明"当前无正式发布能力"，不得让 BLOCK 看起来像可以点"导出"。
- 附图仍是 matplotlib 示意图；Maps 页接线时必须标 DEMONSTRATION（P0-07 未做）。

## 7. 不做的事

- 不起 API 服务、不引入构建工具（保持双击 `index.html` 可跑）。
- 不在 JSX 里算任何业务量——数只能来自 payload。
- 不把 mock 悄悄换成"看起来是真的"的数据；回落 mock 时必须有「演示数据」角标。
- 不为了界面好看而隐藏 BLOCK；不新增前端自算的百分比。
- 不碰 `registries/` 与既有 governance 文件。
- 不实现那 38 项缺失内容——前端的职责是让它们**可见**。

## 8. 建议的起点

**F-1 + F-2 一起做**，约等于一个可验收单元：payload 管道打通 + 缺资料清单可用。做完就能拿惠州样本给编制单位看"这个工具能告诉你还差什么资料"，而不需要等整套报告能生成。
