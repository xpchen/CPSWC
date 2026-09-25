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

## 条目 012

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-22 / 23 |
| 事项 | 前端接线计划 v1.0 经评审驳回，修订为 **v1.1**；随后实施 **F-0 契约补强** |
| 评审结论 | 方向正确，但 v1.0 **把"后端已经有统一状态"想得过于乐观**，照它实施会把刚消灭的多套口径重新复制到 payload 和 JSX 中。指出 5 个生产级漏洞 |
| 五条核实结果 | **全部属实**，其中两条在代码里复现：<br>①逐字段 `?? MOCK` 回落会让页面半真半演示<br>②`build_snapshot_dict()` 无完整 `ResolvedValue`，`unified_view()` 显式跳过 MISSING<br>③**ExportGate 仍二次合并 `_pre_stored_derived`（活 bug，已复现）**<br>④findings 四源重叠、`stage=INPUT` 过滤漏掉 RENDER 阶段缺失<br>⑤全局壳 50 处硬编码肯定状态（12 个文件） |
| 执行者补充的 4 点 | ①三态需划边界：`NAV`/`STATUS_STYLES` 等 UI 配置不是 mock，保持静态<br>②自包含复制壳会产生"壳漂移"，需 `shell_digest` 比对<br>③`output/` 不在 .gitignore 且已有他项目客户材料，补 `/output/` 必须进 F-0<br>④「已建立实现映射 26」与「本次有产出」应分开测，不做减法推断 |
| F-0 交付 | `BuildContext.project_fields()`（唯一字段状态出口，FIR ∪ 消费字段，含 MISSING）；ExportGate 只读统一视图；`src/cpswc/intake_issues.py`（分层 findings + 去重计数 + `intake_issues` 投影，影响范围取自 FIR `projection_target_refs`）；`.gitignore` 补 `/output/` |
| F-0.2 实测 | 修复前：计算失败字段被 BuildContext 隔离，门禁重新合并旧 derived 后 **GATE_001 认为"有值"而放行**。修复后正确阻断，有回归测试 |
| F-0.3 实测 | 惠州四层管线 **180 条原始 → 132 去重**；`disposal_highrisk` 的 24 条收资项中 **22 条来自 RENDER 阶段** —— 证实"按 stage=INPUT 过滤"会几乎全漏 |
| 测试 | 730 → **759**（新增 `tests/test_intake_contract.py` 29 条） |
| 状态 | F-0 **DONE**；F-1A 起尚未开始，**停在计划审批点** |

---

## 条目 013

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-23 |
| 事项 | 实施 **F-1A（payload 管线）/ F-1B（全壳诚实化）/ F-2（收资清单）** |
| F-1A 关键发现 | `file://` 下 Babel 用 XHR 取外链 `.jsx` 被 CORS 拦死 → **整页白屏**。"双击 index.html 就能跑"这个前提对多文件壳**不成立**。改为 `render_standalone_html()` 把全部 JSX + payload 内联成单文件（惠州样本 671 KB） |
| F-1A 落盘 | `output/frontend/<project-code>/<generation-input-hash>/`，先写同级临时目录再整体换名（原子替换）；同目录另存 `payload.json` 旁证供检视 |
| 壳漂移检查曾是摆设 | 单文件内联时 `<meta cpswc-shell-digest>` 原本**抄自 payload**，两边恒等 → 浏览器实测把 `payload.shell_digest` 改成 `000…` 仍畅通无阻。改为**现场按壳文件算**，才真正能挡住"旧壳配新数据" |
| 喂错文件静默产出空项目 | `review_comments_huizhou_v0.json`（审查意见文档，非项目输入）能一路跑通，产出项目名/编码全空的 bundle —— 顶栏「项目快照」下挂一片空白，比报错危险。补 `_require_project_input()` + `validate_payload` 拒绝空 `project.name` |
| F-1B 取舍 | 各页 mock 深埋在页组件自带的数据里（Facts/Narrative/Tables 各一套），属 F-3..F-7 范围。本批不假装接线，改为**让未接线页面自曝**：`UnwiredNotice` + **白名单** `WIRED_PAGES`（默认未接线，接好一个加一个；漏加只会多一条提示，黑名单漏删则会让 mock 冒充真数据） |
| Overview 例外 | 首屏 hero 写死了**另一个项目的名字**与「无导出阻塞」「2 项专家确认」（真实门禁为 BLOCK），四状态卡写死 94/88/92%。仅加提示不够——快照模式下**整块隐藏**，代之以指向顶栏与收资抽屉的真实结论 |
| 肯定状态整块下线 | 评审原话是"**搜索并消除**全部硬编码的肯定状态"。三处最响的假结论不只是加提示：Overview 首屏 hero（另一个项目名 + 无导出阻塞 + 2 项专家确认）整块隐藏；交付包页检查项改接 `export_gate.findings`（**不补齐成全绿表**——门禁只报问题，不出具"通过"结论）、14 个「可下载」清空为「本次快照没有产出任何交付文件」、隐藏"模拟人工改写"按钮与"数文一致性检查通过"绿条；规则审查页「无阻塞」改「未判定（本页未接线）」 |
| F-2 交付 | 收资向导第 4 节改由后端 `intake_issues` 驱动（分类/严重度/影响范围**照搬**，不做二次判断）；`impact_known=false` 如实显示「影响范围尚未建立」。第 1–3、5–6 节标注为演示，「上传资料」「确认写入事实层」在快照模式**禁用**（它们只改浏览器本地 state） |
| 导出件 | 「待甲方提供资料清单」HTML：斜向水印「工作草稿 · 非正式报告附件」+ 项目名/编码/生成时间/`generation_input_hash` + BLOCK/WARN/INFO 分级 + 「影响范围尚未建立不代表不影响任何章节」的说明 |
| 惠州样本实测 | 内容要求 64 项（已建立映射 26 / 本次有产出 26 / 未实现 38 / **确认完成 0**）；收资 24 项（BLOCK 11 · WARN 13）；门禁 BLOCK(7) |
| 测试 | 759 → **866**（新增 `tests/test_frontend_payload.py` 107 条）；浏览器级 `tests/browser/test_data_modes.py` 扩至 23 条，mock 断言改为**白名单驱动**——页面一接线自动纳入无 mock 检查，不需改测试 |
| 状态 | F-1A / F-1B / F-2 **DONE**；F-3..F-7（Overview / Facts / Narrative / Delivery / 六率与表格）未开始 |

---

## 条目 014

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-23 |
| 事项 | **F-3..F-7 逐页接线**（项目总览 / 事实填报 / 正文预览 / 交付包 / 表格中心） |
| 新增 payload 块 | `field_lineage`（字段→章节/图件/投影，取自 FIR `lineage`，**单独成块不并进 facts**，因为 facts 是 project_fields() 的逐字搬运且有回归测试盯着）；`tables`（8 个真实表投影的 spec+rows+`render_policy`+warnings，投影抛异常写 `PROJECTION_FAILED` 不静默少表） |
| 共享取值原语 | `fact/factText/factPresent/factValue` 在 data.jsx 落地，各页不得自解析 payload、不得兜底。空清单显示「空清单·未核实」——后端已写明"不能独自证明已完整调查且无涉及"，显示"无/否"等于替甲方下没人核过的结论。新增状态样式**刻意无绿色** |
| 自查出的真 bug | `LIVE_PROJECT` 里的 `{...PROJECT}` 展开把 mock 的 `scopeArea`/`rulesets` 带进真实项目对象，Facts 面板照着渲染 = 半真半演示。已改为显式构造 |
| 另起两个只读页 | 正文与表格没有改造演示版，而是新建 `NarrativeSnapshot.jsx` / `TablesSnapshot.jsx`。理由：演示版整页围绕"编辑/AI 润色/加注脚/模拟改金额"和 12 张 LIVE 表组织，这些能力一样没实现；把真数据塞进那套壳，用户会以为自己能改 |
| 正文缺口可见化 | 按 2026 章节顺序逐节对照，未实现的小节显示**红框缺口块**而不是跳过。跳过是最危险的做法——目录看起来连续，读者会默认它写完了。模板外产出（3 节）单列一章 |
| 最危险的一句话 | 交付包「是否可提交：可提交（非阻塞）」。后端 `is_submittable` 恒为 None（系统不判断能不能报），现照搬为「系统不作判断」 |
| 表格四态 | 后端 8 张投影中投资估算总表是 `RENDER_WITH_PLACEHOLDER`（有结构没值），界面明确标"结构已就位、数值缺失"。演示版列过而后端没有的 5 张表单列「后端未实现」——**消失会让人以为不需要这些表** |
| 门禁长消息 | 冲突诊断会把整个 measures_registry 的 JSON 贴进 message，一条撑满整页。截断 260 字 + title 挂完整原文，不丢内容 |
| 跨样本核验 | 4 份项目样本 × 5 个已接线页面：无 JS 错误、无 mock 残留。注意 `shiwei_logistics_v0` 命中"世维华南供应链"是它的**真实项目名**（演示数据当初照它编的），非泄漏；已在测试文件注明，防止以后被误"修" |
| 测试 | Python 866 → **894**（`test_frontend_payload.py` 107 → 135）；浏览器级 27 → **38** |
| 状态 | F-1A..F-7 **DONE**；未接线页面剩规则审查 / 计算器 / 附图与地图 / 注脚与依据库 / 改动追踪 / 历史与版本，均带「本页尚未接入项目数据」提示条 |

---

## 条目 015

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-25 |
| 事项 | **F-8..F-12 接完剩余 6 页**（规则审查 / 计算器 / 注脚依据库 / 附图地图 / 改动追踪 / 历史版本） |
| 新增 payload 块 | `obligations_detail`(22)、`calculators`(3)、`rule_refs`(53)、`required_artifacts`(63)、`required_assurances`(4)、`figures`(14) |
| 三值不许压扁 | `obligations_detail.triggered` 保持 True/False/**None**。None 折成 False = 把"条件算不出来"当成"条件不成立" = 悄悄放过一条可能适用的义务。有回归测试逐条比对三态清单 |
| 清点出的硬缺口一 | **53 个 `rule.*` 依据 ID，已登记标题 0 个。** 系统在义务、计算器、正文里引用这些 ID，但没有任何注册表记录它们指向哪部规范哪一条 —— 报告里每句"依据 XXX"都指向空壳，无法向审查人员出示条文。注脚功能（编号/插入正文/导出/存储）同样全部未实现 |
| 清点出的硬缺口二 | **14 张登记图件，9 个 renderer 类名，0 个有代码实现。** `renderer_implemented` 刻意取自手工维护的 `_IMPLEMENTED_RENDERERS`（空集），**不是** `bool(renderer)` —— 照登记表推断会让界面显示"14 张可生成"而实际一张画不出。有回归测试盯着 |
| 计算器页的口径 | 输入字段的取值状态同屏显示：placeholder stub 或空清单明确标注"输出只是把一个未经核实的前提算了一遍"；并写明**执行成功不等于结果可信** |
| F-12 的判断 | 改动追踪/历史版本后端完全没有产出。演示版那两页是具体到人名/时间/金额的伪造日志 —— **一条提示条压不住一屏看起来很具体的假数据**，所以直接不显示，代之以"缺什么 + 当前替代做法" |
| 接线定义 | "如实显示未实现"同样算接线: 它显示的是后端真实状态"没有这个能力", 而不是一屏演示数据。11 个 NAV 页面全部纳入 WIRED_PAGES |
| 白名单保留 | UnwiredNotice + WIRED_PAGES 机制不拆: 新增页面仍默认未接线, 自动带提示条并被 `test_no_nav_page_is_left_unwired` 拦下 |
| 跨样本核验 | 4 份样本 × 11 页 = 44 次渲染, 无 JS 错误、无 mock 残留 |
| 测试 | Python 894 → **942**（`test_frontend_payload.py` 135 → 183）；浏览器级 38 → **52** |
| 状态 | 前端接线 **全部完成**。剩余缺口都在内核: 38/64 内容要求未实现、53 个依据无条文、14 张图无渲染器、正式导出未实现 |

---

## 条目 016

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-09-25 |
| 事项 | **RuleRegistry v0** —— 补 `kernel_gaps_after_wiring` 的第一号缺口（53 个依据 ID 无条文登记） |
| 交付 | `registries/RuleRegistry_v0.yaml`(28 条) · `src/cpswc/rule_registry.py` · lint RULE_001..004 · payload `rule_coverage` · 依据库页三态改造 · `tests/test_rule_registry.py`(14) |
| 三态 | `VERIFIED_TEXT`(原文已核，可出示) / `DECLARED`(定位到文件，没抓原文) / `UNREGISTERED`(不在册)。**DECLARED 不许带 quoted_text** —— 贴原文就等于声称核对过，lint 会拦 |
| 不给覆盖率 | 刻意不出单一百分比。"定位到文件了"和"条文核对过了"是两回事，压成一个数就抹掉了 |
| 当前覆盖 | 惠州样本 53 条：**已核原文 4 / 已定位 24 / 未登记 25**，定位到条款 24 |
| 为什么只有 4 条 | 其余原件多为扫描件抽不出文字：232 号(28 页 **0 字符**)、GB 50433(0)、GB/T 50434(0)、GB 51018(127 页仅 5117 字符且 5.7.1 不在其中)、办水保 135 号(840 字符 OCR 质量差)。读图抓取是独立工作量，本批未做，状态老实写 DECLARED |
| **25 条刻意不登记** | `rule.t2026.*`。ObligationSet 头部自述是"2026 模板/2018 格式/广东惠州"混合来源，**单条义务没声明出处**；前缀不是证据（`spoil_level_4_geology` 实际更可能出自 GB 51018）。按前缀批量填会让缺口凭空消失而一条没查过。`test_t2026_namespace_stays_unregistered` 专门拦这个 |
| 顺带查出的缺陷 | 两处陈旧引用，**都对应 `stable_id_migrations` 里已登记的迁移**：① `section_11` —— 2026 模板没有第 11 章，结论已迁 1.9，但 `narr.conclusion.*` 仍写 section_11；② `section_7` —— 效益分析已跨章迁到 9.2，但 `narr.soil_loss_prevention.benefit_analysis.*` 仍引 section_7。章节 ID 迁移做对了，narrative 的 `source_rule_refs` 没跟着改 |
| 未动 narrative | 改引用是内容变更，应单独决策。本批只把缺陷记进注册表 `defect` 字段 + lint WARN + 界面提示 |
| 两个防伪点 | ① `source_file` 必须真实存在，lint 逐条查（登记查不到的出处比不登记更糟）；② 子条继承文件信息但**不继承 verification_status**（父条核过≠子条核过） |
| hash 变更 | 注册表进 `registries/` 目录摘要 → `generation_input_hash` 由 `8d0cc7ab2ac515e6` 变为 `eda8d8b5e8f243bf`。**改依据登记让旧快照失效是对的** |
| 测试 | Python 942 → **972**；浏览器级 52 → **56**；lint ERROR=0 WARN=2(RULE_004) INFO=27 |
| 下一步 | ①回 ObligationSet 补 25 条来源 ②读图抓 232 号/GB 条文原文(24 条 DECLARED→VERIFIED) ③决定是否改那两处陈旧引用 |

---

## 变更请求

（暂无。超出任务包范围时按 `06_CLAUDE_HANDOFF.md` 第 7 节模板登记。）
