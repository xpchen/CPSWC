# P0 决策记录

本文件按 `01_RFC_SCOPE.md` 第 6 节要求留痕：RFC 版本、批准范围、决策者、时间、确认消息引用、保留意见。
**不得由执行者自行填写"用户已批准"。** 未收到明确批准前，条目状态保持 `PENDING`。

---

## 条目 001

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-20 |
| 事项 | 执行 P0-00 只读基线核查 |
| 依据 | `03_P0_TASKS.md` P0-00 明确"只读基线核查可先做"，`01_RFC_SCOPE.md` 第 6 节同义 |
| 授权类型 | 无需 RFC 批准 |
| 结果 | 完成，见 `P0_BASELINE.md`。12 项诊断中 D01—D05、D10—D12 全部复现；D06—D09 通过代码核查确认（未生成产物） |
| 状态 | DONE |

## 条目 002

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-20 |
| 事项 | RFC-RP-001 v1.0 的 P0 范围与兼容性决定 |
| 请求批准的内容 | ①质量 sidecar 与 `RenderStatus` 解耦（旧数据默认 UNASSESSED）②条件 UNKNOWN 态（`triggered=None` 不再落入 not_triggered）③关键断言缺证据时不作肯定结论 ④统一只读 BuildContext + 别名冲突显式化 ⑤2026 章节结构映射（保留 stable ID）⑥`hash_schema_version` + 事实/生成输入双哈希 ⑦制品台账 ⑧`export_mode=draft/formal`，旧调用默认 draft ⑨诚实的质量展示 |
| 明确不含 | P1—P4；通用图数据库；在线大模型服务；联网自动采集；SaaS/计费/用户体系；激活 `registries/reserved/`；迁移措施真源；改变收费计算方法；重写 31 个模板；真实 CAD/GIS 制图 |
| 决策者 | 项目负责人（陈晓鹏） |
| 批准范围 | **仅 A 批**：P0-01、P0-02、P0-03。B/C 批未批准 |
| 确认消息引用 | 2026-09-20 会话内答复："这个产品我不怕慢，但是质量一定要高。所以按照你推荐的来，但要严格做好测试剧本，用于验证，且一定要严谨诚实。"（对应选项"只批 A 批"） |
| 附加要求 | ①测试剧本必须严格、可复验 ②严谨诚实，不得以绿灯掩盖缺口 |
| 保留意见 | 无 |
| 状态 | **APPROVED（A 批）**；P0-04—P0-09 仍为 PENDING，完成 A 批后停点等待验收 |

---

## 条目 003

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-20 |
| 事项 | P0-04 别名语义（`strippable_volume`/`stripable_volume`、`topsoil.fill`/`backfill_volume`、`prediction.total_loss`/`predicted_total_loss`） |
| 决策 | **不按同义合并。** 待水保工程师确认语义后再登记别名表 |
| 实施要求 | 两侧都有值 → `INPUT_CONFLICT`；仅单侧有值 → 标 `SOURCE_UNVERIFIED`/未核验别名，不静默取值 |
| 决策者 | 项目负责人（陈晓鹏），2026-09-20 会话内选择"待工程师确认，先报 CONFLICT" |
| 状态 | APPROVED（约束已记录，具体实施属 B 批 P0-04，本轮不动） |

## 条目 004

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-20 |
| 事项 | A 批需要一个"输入是否变化"的判据来判定复核记录失效（验收项 N08），但双哈希契约属 B 批 P0-06 |
| 决策 | A 批引入**临时**的 `quality_input_hash`，`hash_schema_version = "quality_input_v0a"`，仅覆盖本次消费的 facts + derived |
| 边界 | 它**不是** `fact_snapshot_hash`，也**不是** `generation_input_hash`；不写入冻结包、不进 manifest、不对外承诺稳定性 |
| 后续 | P0-06 实施后由 `generation_input_hash` 取代；届时 `quality_input_v0a` 标 legacy，不做原地迁移 |
| 状态 | 执行者决定，已留痕，待 B 批验收时一并复核 |

## 条目 005

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-20 |
| 事项 | **实施中发现**：`field.derived.target.*` 同一结构里混用了两套相反的约定 |
| 证据 | `samples/huizhou_housing_v0.json` 的 derived 节：<br>• `control_degree`：`value=98` 是**目标**（`target_by_standard: 南方红壤区一级标准 = 98`），效果在 `actual_derived=99.47`<br>• `soil_loss_control_ratio`：`value=1.0` 是**目标**（`target_by_standard: 一级 = 1.0`），无效果值<br>• `spoil_protection_rate`：`value=99` 带 `derivation: protected_spoil_volume/spoil*100`，是**效果**；目标另存 `施工期目标=95 / 水平年目标=97`<br>• `topsoil_protection_rate` / `vegetation_restoration_rate`：`value` 带 derivation 是**效果**，目标在 `target_by_standard`<br>• `vegetation_coverage_rate`：`value=25` 带 derivation 是**效果**，无目标 |
| 影响 | 六项指标复核表旧实现把 `value` 当实现值，6 行全部"达标"（其中 2 行是目标与自己比较）。本批采用保守规则：**只承认显式的 `actual_derived` 为效果**。代价是 4 个可能真实的效果值（渣土防护率 99、表土保护率 93、林草植被恢复率 99、林草覆盖率 25）现在显示为"待计算" |
| 决策 | 保守规则先行。宁可少显示 4 个数，不可把目标当成绩 |
| 待确认（需水保工程师） | ①这 4 个 `value` 是否确为设计水平年效果？②`spoil_protection_rate` 的"施工期目标/水平年目标"与 `weighted_comprehensive_target` 的关系？③确认后是否给 `field.derived.target.*` 定义统一 schema（如 `target` / `effect` 分字段）——这属规范变更，需单独 RFC |
| 状态 | **PENDING**（本批已按保守方向实现并留痕；语义确认后可在 B/C 批调整） |

## 条目 006

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-20 |
| 事项 | 新增稳定诊断码 `REVIEW_INCOMPLETE`（超出 04 文档第 2 节的建议码清单） |
| 触发 | A 批验收意见第 1 项：复核记录只校验 input_hash、不校验记录完整性，空壳记录可输出专业肯定结论 |
| 为什么需要新码 | 该情形既不是 `REVIEW_STALE`（记录没过期，就是绑在当前输入上的），也不是 `SOURCE_UNVERIFIED`（问题出在复核记录本身而不是资料来源）。复用任一现有码都会让使用者定位错方向 |
| 边界 | 只校验记录是否**成形**（审核人引用 / 复核时间 / 可解析且未被否决的证据引用 / 输入指纹）。**不**声称验证了签名真实性或身份——那需要受控人工流程，软件不代签 |
| 状态 | 执行者决定，已留痕。若项目负责人认为不应扩展建议码清单，可改为复用 `SOURCE_UNVERIFIED` 并降低定位精度 |

## 条目 007

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-20 |
| 事项 | **实施中发现**：包构建管线里，正文/表格看到的 derived 与 runtime 评估义务用的 derived 不是同一套 |
| 证据 | `runtime.run_project` 的 `unified` = facts + 样本 pre-stored derived + 计算 derived（义务评估、fact_sheet 用它）；但 `RuntimeSnapshot.derived_fields` **只含计算 derived**。`narrative/projection.py` 与 `renderers/table_projections.py` 读的都是 `derived_fields`；`export_gate` 又另外自己合并 `_pre_stored_derived`。惠州样本有 9 个 pre-stored derived，其中 **8 个**（含全部六率）对正文和表格不可见 |
| 影响 | 六项指标复核表在实际包里一直是"—"或"待计算"，并不是因为保守规则生效，而是它根本没读到那 6 个值。A 批交付记录里"旧：达标×6"的对照是在**合并 derived** 的快照形态下测出的，与当前包管线的实际渲染不同——该表述已在交付记录中更正 |
| 决策 | **不在 A 批修**。这正是 P0-04（统一读取上下文 / 验收 I01）的职责，在 `BuildContext` 落地前单独改会让多处输出变化而没有统一纪律约束 |
| 状态 | PENDING，列入 B 批 P0-04 必办项 |

## 条目 008

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-20 |
| 事项 | A 批验收结论与 B 批批准 |
| A 批结论 | **通过验收**（经一轮验收修正：R-1 复核记录完整性 / R-2 复核不是通行证 / R-3 非法值与成员属性 / R-4 分支级未知） |
| 批准范围 | **B 批**：P0-04、P0-05、P0-06，含 `B_BATCH_TEMPLATE_TASKS.md` 的 18 个 section 逐模板改造 |
| 指定优先级 | ①**先做统一 BuildContext**，消除 facts / pre-stored derived / calculated derived 的三套读取口径（对应条目 007）②别名冲突 ③18 个 section 逐模板改造 ④2026 章节映射 ⑤双哈希与复核失效 |
| 前置动作 | 完成交付文档中六率旧口径的**非代码勘误** |
| 约束 | 严格按 B 批停点交付；不提前实施 C 批；不提交、不 push |
| 决策者 | 项目负责人（陈晓鹏），2026-09-20 会话内指示 |
| 状态 | **APPROVED（B 批）**；C 批（P0-07/08/09）仍为 PENDING |

## 条目 009

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-20 |
| 事项 | P0-05 的 2026 模板原件核验 —— **部分可核验，整章结构核验受阻** |
| 已核实（双锚齐全，可作为已核验来源） | 文件：`docs/refs/06_2026模板预览/2026模板预览_01..07.png`<br>• 发文机关：中华人民共和国水利部办公厅<br>• **文号：办水保函〔2026〕232 号**（证实 `04_CONTRACTS_AND_ACCEPTANCE.md` 第 6 节所记"网页标题文号有误"，原件为 232 号）<br>• 成文日期：2026 年 4 月 3 日（盖章页）<br>• 施行：自印发之日起实施，**2026 年 6 月 1 日后不再接收不符合模板要求的方案**<br>• 附件构成：①报告书编制内容 ②报告书编制格式 ③报告表编制内容及格式<br>• 附件 1 起始结构：`1 综合说明` → `1.1 项目简况` → `1.1.1 项目基本情况` |
| 受阻原因 | ①`docs/水利部办公厅关于印发…模板的通知.pdf`（sha256 `57a682a1…`）是**纯图像 PDF**，`pdftotext` 抽出 0 行；②图片预览只有 7 页，止于工程特性表填表说明，**不含第 2—10 章的条款结构** |
| 因此不能做的事 | 不能据此写出"正式模板要求—stable ID—显示位置—实现状态"的完整差异表；不能把第 2—10 章的章节归属标为 verified；不能确认"第 11 章结论应迁到 1.9"这一判断（该判断目前只来自计划的 D08，仍未核验） |
| 需要用户提供 | 附件 1《生产建设项目水土保持方案报告书编制内容》的**完整**原件（文本版 PDF 或完整扫描页），或其正式转录件 |
| 状态 | **已解除**（2026-09-21）。用户指出本地通知 PDF 共 28 页、附件 1 位于第 3—22 页；此前 7 张预览图只是预览数量，不是原件全部。已逐页读取第 3—22 页并与昌都市水利局公开 HTML 全文交叉核对 —— 章节结构逐条一致。详见条目 010 |

## 条目 010

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-21 |
| 事项 | P0-05 完成：2026 模板结构核验与 `governance/ReportContentRequirements_v1.yaml` 生效 |
| 第一依据 | 本地扫描原件 `docs/水利部办公厅关于印发…模板的通知.pdf`（sha256 `57a682a1…`，28 页，附件 1 第 3—22 页），逐页读取可视页面 |
| 交叉核对 | 昌都市水利局公开 HTML 全文（2026-09-21）——第 1—10 章及各级小节与原件**逐条一致** |
| 交叉核对中发现的差异 | 该页面标注文号为"办水保函〔2026〕**23**号"，原件为"**232** 号"（少一位）。**以原件为准**。再次证实 04 文档第 6 节所记"页面标题文号有误" |
| OCR 用途 | 仅用于定位页码，**不作为规范原文**（`source.ocr_policy` 已写入 registry 文件） |
| 核验状态 | **VERIFIED**（决议 8 双锚齐全：水利部办公厅 / 2026-04-03 / 办水保函〔2026〕232 号） |
| 已确认的五处映射（均有原件页码） | 结论 → **1.9**（p.5）；设计水平年 → **7.2**（p.16）；防治目标 → **7.3.2**（p.17，在 7.3 水土流失防治目标之下）；效益分析 → **9.2**（p.20，跨章迁移）；管理 = **第 10 章**（p.20，最后主体章） |
| stable ID 处置 | **一个都没改名**。5 条显示位置迁移 + 3 条被吸收 ID，全部显式登记；`projection` 中登记的 stable ID 全部有归属，无悬空 |
| 新增生效文件 | `governance/ReportContentRequirements_v1.yaml`（73 条要求 / 64 条叶子 / 26 已实现 / 38 未实现） |
| 未做 | 未改 renderer 章节树与 `DisplayNumberingPolicy_v0.yaml`（仍按 v0.1 编号输出）；未改 `sec_11_conclusion.py` 的 `rule.template_2026.section_11` 引用。两项均列入遗留，见差异表末节 |
| 状态 | DONE |

## 条目 011

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-21 |
| 事项 | P0-06 完成：双哈希与保守全量失效 |
| 修复 | D10：原 `fact_snapshot_hash` 散列的是 `derived_fields`，改项目名 hash 不变。现改为规范化**事实集合**的哈希 |
| 新增 | `generation_input_hash` = 事实 + 预存派生量 + 来源层选择 + 静态 profile + registry/governance/模板内容摘要 + 计算实现版本 + 规则集。**审核有效性看它** |
| 语义 hash 排除项 | 运行时间、run ID、snapshot_id、临时目录 —— 同语义输入重复执行 hash 不变 |
| canonical JSON | 固定 key 排序；有序数组保留顺序；bool 与 int 区分；整值浮点归一；**NaN/inf 直接报错**并给出字段路径 |
| 复核绑定迁移 | `ReviewLedger` 改绑 `generation_input_hash`；A 批的 `quality_input_hash`（条目 004）降为兜底。条目 004 的"P0-06 后取代"承诺已兑现 |
| 旧包处理 | `describe_hash_schema()` 识别缺 `hash_schema_version` 的旧记录 → 标 `legacy_unverified`，**不重算、不覆盖**（重算后覆盖旧 manifest 会让历史签署看起来适用于新包） |
| 冻结语义 | `FrozenSubmissionInput.lifecycle_freeze_note` 明写"只表示输入已冻结，不表示内容已经专业校审通过" |
| 状态 | DONE |

---

## 变更请求

（暂无。超出任务包范围时按 `06_CLAUDE_HANDOFF.md` 第 7 节模板登记。）
