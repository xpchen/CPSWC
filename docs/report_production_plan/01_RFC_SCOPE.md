# RFC-RP-001：生产级报告可信度与交付边界

状态：PROPOSED（待批准）｜版本：1.0｜日期：2026-09-20

决策者：项目负责人。执行者：后续接受任务的 Claude。不得由执行者自填“用户已批准”。

## 1. 请求批准什么

批准 P0 的有限契约扩展和安全性行为变更：缺失/不适用区分、报告质量旁路记录、条件未知态、来源解析、目标/效果隔离、草稿/正式发布分离、版本哈希修正和最低限度章节结构校正。

P1—P4 为方向性蓝图，不在本 RFC 的实施授权范围。P0 不建设通用图数据库、不实现全套专业设计软件、不引入在线大模型服务、不增加联网自动采集。

## 2. 保留的架构原则

实施前完整阅读这些现有约束，文件中的旧路径如 `specs/` 应与当前 `registries/`、`governance/` 核对：

- `governance/ARCHITECTURE_DECISIONS.md`
- `governance/CORE_CONTRACTS.yaml`
- `governance/ProtectedBoundaryPolicy_v0.yaml`
- `governance/ProvenanceClassification.yaml`
- 涉及措施/投资时：`PREVENTION_SYSTEM_CONTRACT.md`、`INVESTMENT_FACTS_BACKFILL_CONTRACT.md`、`INVESTMENT_SUBSYSTEM_CONTRACT.md`。
- 涉及样本时：`SAMPLE_BACKFILL_CONTRACT_v1.md`、`REPORT_ARTIFACT_CLASSIFICATION_v1.md`。

必须保留：Fact→Obligation→Narrative/Artifact 的单向关系；stable ID 与显示编号分离；Species、Grammar、SubmissionContext 三轴分离；Lifecycle 不参与义务触发；措施以 `prevention.measures_layout[]` 为真源，投资侧为消费视图；规则按适用申报上下文选定，不跟随机器日期；reserved 不被静默启用。

报告质量模块是已有投影/交付流程的校验器，不是第五套项目事实真源。质量记录只存引用、状态和诊断，不复制可编辑的项目数值。

## 3. 已核查的问题与代码锚点

基线 `adba408`；行号仅用于定位，实施前以符号搜索复核。

| 编号 | 证据 | 风险 | 纳入任务 |
| --- | --- | --- | --- |
| D01 | `narrative/contract.py::RenderStatus.FULL`只代表可读文字；`projection.py::_PARENT_INTROS`一句话也计FULL | 完成度虚高 | P0-01、09 |
| D02 | `sec_3_evaluation.render_earthwork_balance({}, {}, set())`与`sec_11_conclusion.render`空输入仍肯定合规，`validate_block`无错误 | 无证据结论 | P0-03 |
| D03 | `sec_3_evaluation`与`sec_7_5_benefit_analysis`将目标值用于达标措辞 | 目标/预测效果混淆 | P0-03 |
| D04 | `projection.py::_SECTION_CONDITIONALS`把常规选址/敏感区内容绑定红线冲突 | 未触发误成不适用 | P0-02、05 |
| D05 | `condition_engine._get_value`缺值转0；异常转False；级联仅遍历一次 | 数据缺口被隐藏、顺序依赖 | P0-02 |
| D06 | `export_gate._check_assurances`硬编码WARN；`package_builder.build_package`遇BLOCK继续生成 | 失败仍像正式交付 | P0-08 |
| D07 | `package_builder`吞DOCX/GIS异常；required列表不等于实际文件齐全 | 残包被认作成功 | P0-07、08 |
| D08 | `DisplayNumberingPolicy_v0.yaml`有11章；7.2/7.3、效益分析位置与新报告书模板不一致 | 模板对齐不足 | P0-05 |
| D09 | `prediction_engine`典型模数、默认时段；`geo_pipeline`中心点/面积矩形 | 演示假设流入正式成果 | P0-04、07 |
| D10 | `runtime.freeze_submission`的fact_snapshot_hash实际散列derived_fields；snapshot含时间戳 | 不同事实可能同“事实哈希”；相同语义输入hash不稳定 | P0-06 |
| D11 | `runtime.run_project`价格enrich写回输入facts；多条snapshot构造路径补入私有键 | 重跑变输入、不同入口口径不一 | P0-04、06 |
| D12 | `project_fact_sheet._FACT_MAPPING`有strippable_volume/backfill_volume/predicted_total_loss等名称，现有样本用stripable_volume/fill/total_loss | 表文缺值或别名冲突 | P0-04 |

实测范围：当前代码对现有惠南快照投影为35 FULL、3 N/A，正文3648字符（不含表格），21个FULL块不足100字符；既有惠南Word21张表、0嵌入媒体。数字用于定位问题，不作为验收字数目标。D02为模板级反例，不是空项目端到端测试。

本轮对D10/D11另做了只读内存测试：对惠南输入副本仅修改项目名称，两次derived_fields相等，fact_snapshot_hash也相等；调用run_project后，传入副本相对调用前发生变化。测试未改写样本文件。前者证明事实hash缺陷，后者证明当前机器环境下存在输入原地变更，不能只依靠函数文档的“纯读取”假设。

## 4. 需要明确批准的兼容性改变

| 决策 | 方案 | 不采用的替代方案 |
| --- | --- | --- |
| 状态分离 | 保留旧render_status作为渲染状态，新增质量sidecar；旧结果默认UNASSESSED，不自动变已审核 | 把FULL直接重新定义为专业完成，破坏全部旧消费者 |
| 条件求值 | 沿用triggered: bool\|None，None扩展为无法确定；附reason/missing refs；UNKNOWN不进入not_triggered | 缺失默认False，以便维持旧覆盖率 |
| 输入一致性 | 增加统一只读上下文适配器，列明冲突及派生来源；禁止失败计算回退旧值并装作成功 | 每个renderer自己拼一套unified |
| 发布语义 | build_package旧调用默认明确草稿；正式发布需显式模式与完整检查 | 保留正式外观只在stderr打印WARN |
| 保障状态 | 正式发布按required约束和有效证据执行；旧v0降级仅可用于明确草稿 | 将`provided=True`当作真实签署验证 |
| 冻结/哈希 | 新hash_schema_version；事实hash与生成输入hash分开；保留旧版本只读 | 无版本标识原地改变旧hash定义 |
| 编号与规则 | 建立新报告书结构映射，保留既有stable ID及旧编号信息；不能沿用不存在的section_11条款作为证明 | 全量改ID，导致审查意见失联 |
| 定性结论 | 原保护级别不自动改变；生产肯定性判断增加证据支持门槛，不以ADVISORY标签豁免 | 认为“基本合理”只是润色，无需证据 |

草稿模式仍要检测并展示所有问题，不能抹去BLOCK。其可生成不等于校验PASS。

P0结束时，生产发布能力应仍如实显示未完成：真实空间数据、完整报告种类、专业设计和校审条件尚未全部实现。完整的门禁基础设施可以验收，但不得为演示造一个“全绿正式项目”。

## 5. 现有治理与规划的冲突处理

1. 架构反升级条款要求RFC、更新阶段范围、书面批准。此目录只是RFC提案。收到批准后，先在架构变更记录中限定为“报告可信度修复阶段”，再实施新增契约；不要将v1所有能力一起启用。
2. `ProtectedBoundaryPolicy_v0.yaml`对保障、冻结的WARN是有意的v0豁免。新增formal策略必须明确区分模式，不能声称只是修一行bug。
3. 当前来源治理禁止问题样稿进入系统。本计划的“审查修改学习”不授权导入被退回/未校正原文到RAG、规则或生产样本。优先使用专家意见、经确认的纠正版本和原创合成负例；如需隔离研究库，另行RFC。
4. 既有治理文件中的法律解释、适用边界、费率、规范效力归类不因文件名为“宪法”就自动成为已核验法律事实。P0保持软件边界，争议条款进入专业确认清单；不按记忆重写法规。
5. 公开样本只能是inspiration_only，不能驱动规则或参数；网页正文、未校对OCR和不完整附件不能自动标记verified。

## 6. 审批与停点

P0-00的只读基线核查可先做。P0-01起需要项目负责人批准本RFC的范围和兼容性决定。需要增加新的外部服务、修改业务规范实质含义、迁移措施真源、改变收费计算方法或扩大到其他项目类型时，单独提交变更请求，不自动包含在本批准内。

批准记录应保存：RFC版本、批准范围（A/B/C批）、决策者、时间、原始确认消息引用、保留意见。不要伪造签字。用户在新任务中明确说“批准RFC-RP-001 v1.0的P0范围并执行A批”可作为该批书面授权，按项目既有规则留痕。

## 7. 回退边界

不覆盖历史报告、冻结包和tests/baselines；新的诊断和草稿输出放新目录。仅对本批新增改动做可审查回退，禁止`reset --hard`、全仓清理、批量删除输出。修复前的不安全正式发布行为不通过生产开关重新开启；需要旧展示时使用带警示的草稿。
