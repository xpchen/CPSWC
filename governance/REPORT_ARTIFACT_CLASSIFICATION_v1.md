# CPSWC 报告书工件分类与自动化边界（v1 Planning Baseline）

> **文档性质**: 准制度文件，定义 46 个工件的产出机制归口与 v1 开发优先级。
> **生效范围**: 本文档直接影响产品表单设计、引擎实现、renderer 排期和工件注册表的演进方向。
> **引用方式**: 后续讨论工件、表格、上传、引擎优先级时，以本文档为默认依据。
> **版本**: v1 Planning Baseline · 2026-04-12
> **上游依据**: ArtifactRegistry_v0.yaml / CalculatorRegistry_v0.yaml / FieldIdentityRegistry_v0.yaml

---

## 一、四分类定义

| 分类代号 | 名称 | 定义 | 系统职责 |
|---|---|---|---|
| **A** | 表单提交 (form_input) | 用户/设计院通过表单录入事实数据 | 提供结构化模板 + 校验规则 |
| **B** | 计算生成 (calculator_generated) | 系统从 facts / derived / calculators 自动计算产出 | 全自动或半自动，用户只需确认 |
| **C** | 附件导入 (attachment_import) | 用户上传外部文件（审批件/证明/CAD 图） | 提供上传通道 + 格式校验 + 归档 |
| **D** | 人工审阅 (expert_review) | 必须由具备专业资质的专家编写或审核 | 提供框架/模板 + 审核流程 |

---

## 二、v0_status 六种状态定义

| 状态 | 含义 | v1 动作 |
|---|---|---|
| `LIVE` | 已有 live calculator + renderer，全自动 | 维护 |
| `CAN_GENERATE` | facts 已就绪，只缺 renderer 实现 | 实现 renderer |
| `ENGINE_STUB` | 挂着 engine.* 占位符，需要 v1 实现引擎 | 实现对应 subsystem |
| `IMPORT_ONLY` | 只需文件上传功能 | 实现上传 UI + 归档 |
| `EXPERT_ONLY` | 系统提供框架，专家填内容 | 实现协作编辑 + 审核流程 |
| `PARTIAL` | 部分自动，部分需专家 | 按子项拆分，分别处理 |

---

## 三、46 工件总表

### A. 表单提交 (7 件, 15%)

| 工件 ID | 名称 | v0_status | 说明 |
|---|---|---|---|
| art.table.investment.engineering_measures | 工程措施估算表 | ENGINE_STUB | 工程量由设计院输入，造价由系统按定额计算 |
| art.table.investment.plant_measures | 植物措施估算表 | ENGINE_STUB | 同上 |
| art.table.investment.temporary_measures | 临时措施估算表 | ENGINE_STUB | 同上 |
| art.table.investment.monitoring_measures | 监测措施估算表 | ENGINE_STUB | 监测点数/频次输入，费用系统计算 |
| art.table.investment.unit_prices | 工程单价汇总表 | ENGINE_STUB | 单价由设计院按当地定额和市场调查确定 |
| art.table.investment.machine_hours | 施工机械台时费汇总表 | ENGINE_STUB | 机械台班单价，设计院确定 |
| art.table.investment.material_prices | 主要材料单价汇总表 | ENGINE_STUB | 材料单价，设计院确定 |

**共性特征**: 全部是投资估算体系的输入端，全部挂 engine.InvestmentEstimationSubsystem。v1 实现该 subsystem 后，这 7 张表变为"用户输入工程量/单价 → 系统计算造价"的 A+B 混合模式。

### B. 计算生成 (29 件, 63%)

#### B-1. 已 LIVE（2 件）

| 工件 ID | 名称 | calculator | 说明 |
|---|---|---|---|
| art.table.investment.compensation_fee | 水土保持补偿费计算表 | cal.compensation.fee | 全自动，ground truth 5.7/27.0 万元 |
| art.table.weighted_target_calculation | 水土流失防治指标计算表 | cal.target.weighted_comprehensive | 全自动，6 率加权 |

#### B-2. CAN_GENERATE（11 件）— facts 已就绪，只缺 renderer

| 工件 ID | 名称 | 数据来源 |
|---|---|---|
| art.table.earthwork_balance | 土石方平衡表 | field.fact.earthwork.* |
| art.table.total_land_occupation | 工程总占地表 | field.fact.land.* |
| art.table.land_occupation_by_county | 分县占地表 | field.fact.land.county_breakdown |
| art.table.topsoil_balance | 表土平衡表 | field.fact.topsoil.* |
| art.table.responsibility_range_by_admin_division | 防治责任范围统计表 | field.fact.location + land |
| art.spec_sheet | 水土保持工程特性表 | facts + derived 大量字段 |
| art.figure.schedule_gantt | 双线横道图 | field.fact.schedule.* |
| art.cover.report_book_cover | 封面 | field.fact.project/party |
| art.cover.title_page | 扉页 | field.fact.project/party |
| art.cover.responsibility_page | 责任页 | field.fact.party + 人工签名确认 |
| art.cover.toc | 目录 | 从章节结构自动生成 |

#### B-3. ENGINE_STUB（15 件）— 需要 v1 实现引擎

| 工件 ID | 名称 | 依赖引擎 |
|---|---|---|
| art.table.investment_appendix | 投资附件总包 | InvestmentEstimationSubsystem |
| art.table.investment.total_summary | 投资估算总表 | InvestmentEstimationSubsystem |
| art.table.investment.annual_breakdown | 分年度投资估算表 | InvestmentEstimationSubsystem |
| art.table.investment.independent_fees | 独立费用计算表 | InvestmentEstimationSubsystem |
| art.figure.F_01_location | 项目地理位置图 | GeoPipeline |
| art.figure.F_02_river_system | 项目所在河流水系图 | GeoPipeline |
| art.figure.F_03_soil_erosion | 项目区水土流失现状图 | GeoPipeline |
| art.figure.F_04_responsibility_range | 防治责任范围图 | GeoPipeline |
| art.figure.F_05_overall_layout | 总体布置图 | GeoPipeline + 设计院标注 |
| art.figure.F_06_monitoring_points | 监测点位图 | MonitoringPlanner |
| art.figure.F_07_vegetation_distribution | 植被分布图 | GeoPipeline |
| art.figure.F_08_topsoil_survey | 表土调查图 | GeoPipeline |
| art.figure.F_09_topsoil_stripping_range | 表土剥离范围图 | GeoPipeline |
| art.figure.F_10_measures_layout | 措施总体布置图 | GeoPipeline + 设计院标注 |
| art.figure.F_12_borrow_and_disposal_location | 取土场弃渣场位置图 | GeoPipeline |

#### B-4. PARTIAL（1 件）

| 工件 ID | 名称 | 说明 |
|---|---|---|
| art.table.spoil_summary | 弃渣场/堆土场汇总表 | facts + cal.disposal_site.level 可生成数据部分；选址论证文字需专家审核 |

### C. 附件导入 (8 件, 17%)

| 工件 ID | 名称 | 说明 |
|---|---|---|
| art.attachment.AF_1_project_approval | 项目审批文件 | 用户上传原件扫描/电子件 |
| art.attachment.AF_3_land_use_confirmation | 用地确认文件 | 用户上传 |
| art.attachment.AF_4_external_earth_purchase | 外购土石方协议/证明 | 用户上传 |
| art.attachment.AF_5_geology_report | 地质勘察报告结论 | 外部地勘单位出具，用户上传 |
| art.attachment.AF_6_reuse_evidence | 弃渣综合利用证明 | 用户上传 |
| art.attachment.AF_7_other_supporting | 其他支撑材料 | 用户上传 |
| art.figure.F_11_typical_design | 典型设计图 | 设计院 CAD 出图后导入 |
| art.figure.F_13_vertical_layout | 竖向布置图 | 设计院 CAD 出图后导入 |

### D. 人工审阅 (2 件, 4%)

| 工件 ID | 名称 | 说明 |
|---|---|---|
| art.attachment.AF_2_unavoidability_justification | 不可避让论证报告 | 由专家编写或外部咨询单位提供 |
| art.subreport.spoil_failure_analysis | 弃渣场失事影响专题分析 | 需专家编写，cal.disposal_site.level 提供计算参数 |

---

## 四、自动化率总览

| 指标 | 数值 |
|---|---|
| 工件总数 | 46 |
| **系统可自动生成 (B 类)** | **29 (63%)** |
| 用户表单录入 (A 类) | 7 (15%) |
| 用户文件上传 (C 类) | 8 (17%) |
| 专家编写 (D 类) | 2 (4%) |

---

## 五、19 张表格来源分层

| 层级 | 表格数 | 说明 |
|---|---|---|
| **已 LIVE** | 2 | 补偿费 + 加权目标（有 calculator + renderer） |
| **CAN_GENERATE** | 6 | 土石方平衡/总占地/分县占地/表土平衡/防治范围/弃渣汇总（facts 就绪，缺 renderer） |
| **ENGINE_STUB** | 11 | 投资附件总包 + 10 张投资子表（全部挂 InvestmentEstimationSubsystem） |

---

## 六、v1 开发优先级（按"解锁工件数"排序）

| 优先级 | 工作项 | 解锁工件数 | 类型 |
|---|---|---|---|
| **P0** | CAN_GENERATE renderer（6 张表 + 4 封面 + 特性表） | 11 | 纯 renderer 工作 |
| **P1** | InvestmentEstimationSubsystem | 11 | subsystem + renderer |
| **P2** | GeoPipeline | 11 | GIS 引擎 |
| **P3** | 文件上传功能 | 8 | 产品 UI |
| **P4** | 专家协作编辑 | 2 | 产品 UI + 流程 |

**P0 最值钱**: 11 个工件的数据已就绪，只需要表格 renderer 实现，零引擎依赖，是 v1 最低成本最高产出的开发路径。

**P1 最大**: InvestmentEstimationSubsystem 一旦实现，一次性解锁 11 张投资表，对整体自动化率的提升从 63% 跃升到 ~85%。

---

## 七、与其他治理文件的映射

| 本文档概念 | 对应治理文件 | 关系 |
|---|---|---|
| 工件 ID (art.*) | registries/ArtifactRegistry_v0.yaml | 1:1 映射 |
| calculator (cal.*) | registries/CalculatorRegistry_v0.yaml | B-1 类工件由 calculator 驱动 |
| fact fields (field.fact.*) | registries/FieldIdentityRegistry_v0.yaml | A 类工件的数据来自 fact fields |
| engine.* | CORE_CONTRACTS.yaml id_namespaces | B-3 类工件的占位引用 |
| obligation trigger | registries/ObligationSet_v0.yaml | 条件工件的出现由 obligation 驱动 |
| authority_class | governance/ProvenanceClassification.yaml | B 类工件的来源权威由此约束 |

---

## 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-04-12 | v1 Planning Baseline | 初版：46 工件四分类 + 19 表来源分层 + v1 优先级 |
