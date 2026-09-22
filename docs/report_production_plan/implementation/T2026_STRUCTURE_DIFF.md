# 2026 模板结构差异表（P0-05 交付物）

生成日期：2026-09-21｜对应任务：`03_P0_TASKS.md` P0-05 验收项 R01—R05

## 来源与核验状态

| 项 | 内容 |
| --- | --- |
| 规范 | 《生产建设项目水土保持方案报告书编制内容》（**办水保函〔2026〕232 号** 附件 1） |
| 发文机关 | 中华人民共和国水利部办公厅 |
| 成文日期 | 2026 年 4 月 3 日 |
| 施行 | 自印发之日起实施；**2026 年 6 月 1 日后不再接收不符合模板要求的方案** |
| 第一依据 | 本地扫描原件 `docs/水利部办公厅关于印发生产建设项目水土保持方案编制模板的通知.pdf`<br>sha256 `57a682a12bc43b13a1a4f0ed64a641f52b1465d324dc49178233a19770a2ab00`，共 28 页，**附件 1 位于第 3—22 页**，逐页读取可视页面 |
| 交叉核对 | 昌都市水利局公开 HTML 全文（2026-09-21 核对）——**第 1—10 章及各级小节与原件逐条一致** |
| 发现的差异 | 该页面标注文号为"办水保函〔2026〕**23**号"，比原件少一位。**以原件 232 号为准。** 这证实了 `04_CONTRACTS_AND_ACCEPTANCE.md` 第 6 节所记"页面标题文号有误" |
| OCR 用途 | 仅用于定位页码，**不作为规范原文** |
| 核验状态 | **VERIFIED**（双锚齐全：责任署名 / 成文时间 / 文号版本） |

机器可读清单：`governance/ReportContentRequirements_v1.yaml`。

## 五处关键位置（已由原件逐条证实）

| stable ID | v0.1 旧显示 | 2026 显示 | 原件页码 |
| --- | --- | --- | --- |
| `sec.conclusion` | 第 11 章 | **1.9 结论** | PDF p.5 |
| `sec.soil_loss_prevention.design_horizon` | 7.3 | **7.2 设计水平年** | PDF p.16 |
| `sec.soil_loss_prevention.targets` | 7.2 | **7.3.2 防治目标**（7.3 水土流失防治目标之下） | PDF p.17 |
| `sec.soil_loss_prevention.benefit_analysis` | 7.5 | **9.2 效益分析**（跨章迁移） | PDF p.20 |
| `sec.management` | 10 | **10 水土保持管理**（最后主体章） | PDF p.20 |

**2026 模板没有第 11 章。** 任何以 `rule.template_2026.section_11` 为依据的表述都不成立——该引用仍存在于 `sec_11_conclusion.py` 的 `normative_basis` 中，属待迁移项（见下节遗留）。

## stable ID 处置原则

**一个都没改名。** 显示位置变了就改 `display_number`，`stable_id` 保持不变——改名会让历史审查意见的定位全部失联。

- **迁移**（5 条）：显示位置变化，ID 不动，旧编号语境留痕。
- **被吸收**（3 条）：v0.1 里是独立显示节，2026 里并入别节，内容仍产出：

| stable ID | 并入 | 理由 |
| --- | --- | --- |
| `sec.investment_estimation.compensation_fee` | 9.1.2 估算成果 | 9.2 已是效益分析；补偿费计算表是 9.1.2 明列的估算成果之一 |
| `sec.project_overview.water_soil_zoning` | 1.1.2 自然简况 / 表 1 | 2026 的 2.7 自然概况七个子项中**没有**独立的"水土保持区划"节 |
| `sec.soil_loss_prevention.responsibility_range_by_county` | 7.1 + 附表 | 7.1 本身要求"按县级行政区…分别列明"；另有"防治责任范围统计表"附表 |

`projection` 中登记的 stable ID **全部有归属，无悬空**（测试 `test_r05_every_registered_section_has_a_home` 守着）。

## 完成度：新旧口径对照

以惠州样本为例：

| 口径 | 数字 | 含义 |
| --- | --- | --- |
| 旧（`full_count`） | **38** | 渲染出连续文字的块数——看起来接近完成 |
| 新（对照 2026 模板叶子要求） | **0 / 64** | 已确认完成的叶子要求数 |
| 其中未实现 | **38 / 64** | 模板要求但当前没有任何 narrative 产出 |
| 其中有产出未确认 | **26 / 64** | 有文字，但内容完整性未对照规范确认 |

未实现项**仍在分母里**（验收 R02）——不因为模板没写就不计分。

## 完整差异表

| 显示位置 | 正式模板要求 | stable ID | 实现状态 |
| --- | --- | --- | --- |
| 1 | 综合说明 | `sec.overview` | （章标题） |
| 1.1.1 | 项目基本情况 | `sec.overview.project_basic` | **已实现** |
| 1.1.2 | 自然简况 | — | 未实现 |
| 1.2 | 项目水土保持评价结论 | — | 未实现 |
| 1.3 | 表土资源保护与利用 | — | 未实现 |
| 1.4 | 弃渣场选址与堆置 | — | 未实现 |
| 1.5 | 水土流失预测结果 | — | 未实现 |
| 1.6.1 | 水土流失防治责任范围及目标 | — | 未实现 |
| 1.6.2 | 水土流失防治分区及措施 | — | 未实现 |
| 1.7 | 水土保持监测方案 | — | 未实现 |
| 1.8 | 水土保持投资及效益分析成果 | — | 未实现 |
| 1.9 | 结论 | `sec.conclusion` | **已实现** |
| 表1 | 水土保持方案特性表 | `sec.overview.spec_sheet_end` | **已实现** |
| 2 | 项目概况 | `sec.project_overview` | （章标题） |
| 2.1 | 项目组成及工程布置 | — | 未实现 |
| 2.2 | 施工组织 | — | 未实现 |
| 2.3 | 工程占地 | `sec.project_overview.land_occupation` | **已实现** |
| 2.4 | 土石方平衡 | `sec.project_overview.earthwork_balance` | **已实现** |
| 2.5 | 拆迁（移民）安置与专项设施改（迁）建（条件性：原文标注"不涉及的不列"） | — | 未实现 |
| 2.6 | 工程进度 | `sec.project_overview.progress` | **已实现** |
| 2.7.1 | 地质 | — | 未实现 |
| 2.7.2 | 地貌 | — | 未实现 |
| 2.7.3 | 气候气象 | `sec.project_overview.climate` | **已实现** |
| 2.7.4 | 水文 | — | 未实现 |
| 2.7.5 | 土壤 | — | 未实现 |
| 2.7.6 | 植被 | — | 未实现 |
| 2.7.7 | 水土保持敏感区及其他敏感区 | `sec.project_overview.sensitive_areas` | **已实现** |
| 3 | 项目水土保持评价 | `sec.evaluation` | （章标题） |
| 3.1 | 主体工程选址（线）水土保持评价 | `sec.evaluation.site_selection` | **已实现** |
| 3.2 | 建设方案与布局水土保持评价 | — | 未实现 |
| 3.3 | 工程占地评价 | — | 未实现 |
| 3.4 | 土石方平衡评价 | `sec.evaluation.earthwork_balance` | **已实现** |
| 3.5 | 取土场设置评价（条件性：原文标注"不设取土场的不列"） | — | 未实现 |
| 3.6 | 施工方法与工艺评价 | — | 未实现 |
| 3.7 | 主体工程设计中具有水土保持功能工程的分析评价 | — | 未实现 |
| 4 | 表土资源保护与利用 | `sec.topsoil` | （章标题） |
| 4.1.1 | 表土资源调查 | — | 未实现 |
| 4.1.2 | 表土资源评价 | — | 未实现 |
| 4.2.1 | 表土剥离保护 | `sec.topsoil.stripping` | **已实现** |
| 4.2.2 | 表土就地保护 | — | 未实现 |
| 4.3.1 | 表土堆存 | — | 未实现 |
| 4.3.2 | 表土养护 | — | 未实现 |
| 4.4.1 | 表土需求分析 | — | 未实现 |
| 4.4.2 | 表土回覆 | `sec.topsoil.balance` | **已实现** |
| 4.4.3 | 表土再利用 | — | 未实现 |
| 5 | 弃渣场选址与堆置（条件性：原文标注"不设弃渣场、临时堆土场的不列"） | `sec.disposal_site` | （章标题） |
| 5.1 | 渣土来源及流向（条件性：同上） | `sec.disposal_site.source_and_flow` | **已实现** |
| 5.2 | 弃渣场选址、堆置方案与级别（条件性：同上） | `sec.disposal_site.site_selection` | **已实现** |
| 6 | 水土流失分析与预测 | `sec.soil_loss_analysis` | （章标题） |
| 6.1 | 水土流失现状 | `sec.soil_loss_analysis.current_state` | **已实现** |
| 6.2 | 水土流失影响因素分析 | — | 未实现 |
| 6.3 | 土壤流失量预测 | `sec.soil_loss_analysis.prediction_result` | **已实现** |
| 6.4 | 水土流失危害分析 | — | 未实现 |
| 7 | 水土流失防治 | `sec.soil_loss_prevention` | （章标题） |
| 7.1 | 水土流失防治责任范围 | `sec.soil_loss_prevention.responsibility_range` | **已实现** |
| 7.2 | 设计水平年 | `sec.soil_loss_prevention.design_horizon` | **已实现** |
| 7.3.1 | 执行标准等级 | — | 未实现 |
| 7.3.2 | 防治目标 | `sec.soil_loss_prevention.targets` | **已实现** |
| 7.4 | 防治区划分 | — | 未实现 |
| 7.5 | 措施总体布局 | — | 未实现 |
| 7.6 | 工程级别与设计标准 | — | 未实现 |
| 7.7 | 分区措施布设 | — | 未实现 |
| 7.8 | 施工组织 | `sec.soil_loss_prevention.construction_schedule` | **已实现** |
| 8 | 水土保持监测 | `sec.monitoring` | （章标题） |
| 8.1 | 范围和时段 | `sec.monitoring.scope_and_period` | **已实现** |
| 8.2 | 内容、方法与频次 | `sec.monitoring.contents_methods_frequency` | **已实现** |
| 8.3 | 点位布设与监测设施 | `sec.monitoring.point_layout` | **已实现** |
| 8.4 | 实施条件和成果 | — | 未实现 |
| 9 | 水土保持投资及效益分析 | `sec.investment` | （章标题） |
| 9.1.1 | 编制原则及依据 | — | 未实现 |
| 9.1.2 | 编制说明与估算成果 | `sec.investment.summary` | **已实现** |
| 9.2 | 效益分析 | `sec.soil_loss_prevention.benefit_analysis` | **已实现** |
| 10 | 水土保持管理 | `sec.management` | **已实现** |

## 附表 / 附件 / 附图（原件 p.21—22）

模板另要求 3 类附表、7 类附件、13 张附图。其中特别注明：

- 水土流失防治责任范围图需**提供完整的防治责任范围 shapefile 格式矢量数据**；
- 取土场和弃渣场（含临时堆土场）位置图需**含地形和影像图**，且相关图件应能反映周边及下游影响范围内的地形及敏感因素信息。

当前 GeoPipeline 产出的是 matplotlib 示意图，与上述要求差距很大。制品台账与校验属 P0-07（C 批），本轮只登记清单，不计入内容覆盖率。

## 本轮未做的事

1. **未改 renderer 的章节树**。`renderers/document.py` 与 `DisplayNumberingPolicy_v0.yaml` 仍按 v0.1 编号输出。本轮只建立映射与差异表；把显示编号真正切到 2026 需要同步改章节树、交叉引用与既有测试基线，属独立改动。
2. **未改 `sec_11_conclusion.py` 的 `normative_basis`**（仍写 `rule.template_2026.section_11`）。改它会牵动 `validate_block` 的规范引用校验与既有断言测试，留作单独一步。
3. **未实现 38 项缺失内容**。清单的作用是让它们**可见且计分**，不是自动补写。
4. **未处理报告表（附件 3）**。那是另一套结构，`load_content_requirements(species="报告表")` 返回 `None`，不得拿报告书清单顶替。
