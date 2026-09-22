# 模板断言风险清点（P0-03 第 1 条交付物）

生成日期：2026-09-20｜对应任务：`03_P0_TASKS.md` P0-03 实施第 1 条
生成方式：遍历 `narrative/projection.py::_PILOT_TEMPLATES` 与 `_PARENT_INTROS` 的全部已注册 render 函数，扫描其源码**字符串字面量**中的判断词。

## 这份清单是什么、不是什么

- **是**：一份定位表。告诉后续实施者哪些模板里出现过判断性措辞，哪些模板本批已经改造、哪些还没有被审查。
- **不是**：质量证明。检索只是定位手段，命中关键词不等于有问题，没命中也不等于没问题。
  - 已改造模板的"命中判断词"多数来自**待复核说明**（如"是否合理…须复核确认"）与**判断的备用文本**（`judgment()` 的第一个参数，只有存在绑定当前输入的复核记录时才会输出）。
  - 未审查模板中**没有命中判断词**只说明没有这批关键词，它们的值状态处理（缺失是否转 0、空容器是否当核查结论）**本批未逐条审查**。

## 判断词表

`合理 / 符合 / 可行 / 已核查 / 经核查 / 全部用于 / 无需 / 均达到 / 达标 / 满足 / 充分 / 有效 / 可靠 / 不涉及 / 已完成 / 已提供`

## 清单

| section_id | 模板模块 | 本批状态 | 命中判断词 |
| --- | --- | --- | --- |
| `sec.disposal_site` | `projection._PARENT_INTROS` | **已改造** | — |
| `sec.investment` | `projection._PARENT_INTROS` | **已改造** | — |
| `sec.monitoring` | `projection._PARENT_INTROS` | **已改造** | — |
| `sec.project_overview` | `projection._PARENT_INTROS` | **已改造** | — |
| `sec.soil_loss_analysis` | `projection._PARENT_INTROS` | **已改造** | — |
| `sec.soil_loss_prevention` | `projection._PARENT_INTROS` | **已改造** | — |
| `sec.topsoil` | `projection._PARENT_INTROS` | **已改造** | — |
| `sec.overview` | `sec_0_overview` | **已改造** | 达标 |
| `sec.conclusion` | `sec_11_conclusion` | **已改造** | 不涉及、充分、合理、有效、满足、符合 |
| `sec.project_overview.climate` | `sec_2_3_climate_zoning` | **已改造** | 不涉及、充分、经核查 |
| `sec.project_overview.water_soil_zoning` | `sec_2_3_climate_zoning` | **已改造** | 不涉及、充分、经核查 |
| `sec.project_overview.sensitive_areas` | `sec_2_5_sensitive_areas` | **已改造** | 不涉及、充分、已核查、经核查 |
| `sec.evaluation.site_selection` | `sec_3_1_site_selection` | **已改造** | 不涉及、符合 |
| `sec.evaluation` | `sec_3_evaluation` | **已改造** | 全部用于、可行、可靠、合理、无需、满足、达标 |
| `sec.evaluation.earthwork_balance` | `sec_3_evaluation` | **已改造** | 全部用于、可行、可靠、合理、无需、满足、达标 |
| `sec.topsoil.balance` | `sec_4_topsoil` | **已改造** | 不涉及、全部用于、可行 |
| `sec.topsoil.stripping` | `sec_4_topsoil` | **已改造** | 不涉及、全部用于、可行 |
| `sec.disposal_site.site_selection` | `sec_5_disposal` | **已改造** | 不涉及、合理、无需、满足、经核查 |
| `sec.disposal_site.source_and_flow` | `sec_5_disposal` | **已改造** | 不涉及、合理、无需、满足、经核查 |
| `sec.soil_loss_prevention.benefit_analysis` | `sec_7_5_benefit_analysis` | **已改造** | 合理、有效、达标 |
| `sec.management` | `sec_10_management` | 未审查 | 有效 |
| `sec.overview.project_basic` | `sec_1_1_basic_info` | 未审查 | — |
| `sec.overview.spec_sheet_end` | `sec_1_2_spec_sheet` | 未审查 | — |
| `sec.project_overview.earthwork_balance` | `sec_2_1_2_land_earthwork` | 未审查 | — |
| `sec.project_overview.land_occupation` | `sec_2_1_2_land_earthwork` | 未审查 | — |
| `sec.project_overview.progress` | `sec_2_4_progress` | 未审查 | — |
| `sec.soil_loss_analysis.current_state` | `sec_6_soil_loss` | 未审查 | — |
| `sec.soil_loss_analysis.prediction_result` | `sec_6_soil_loss` | 未审查 | — |
| `sec.soil_loss_prevention.responsibility_range` | `sec_7_1_responsibility_range` | 未审查 | — |
| `sec.soil_loss_prevention.responsibility_range_by_county` | `sec_7_1_responsibility_range` | 未审查 | — |
| `sec.soil_loss_prevention.targets` | `sec_7_2_targets` | 未审查 | — |
| `sec.soil_loss_prevention.design_horizon` | `sec_7_3_design_horizon` | 未审查 | — |
| `sec.soil_loss_prevention.construction_schedule` | `sec_7_8_construction_schedule` | 未审查 | — |
| `sec.monitoring.scope_and_period` | `sec_8_1_monitoring_scope` | 未审查 | — |
| `sec.monitoring.contents_methods_frequency` | `sec_8_2_monitoring_content` | 未审查 | — |
| `sec.monitoring.point_layout` | `sec_8_3_monitoring_points` | 未审查 | — |
| `sec.investment.summary` | `sec_9_1_investment_summary` | 未审查 | — |
| `sec.investment_estimation.compensation_fee` | `sec_9_2_compensation` | 未审查 | — |

合计 38 个已注册 section（31 个模板 render + 7 个父章节引言）：**已改造 20 个，未审查 18 个**。

## 已改造模板的改动性质

| 模板 | 原问题 | 处理 |
| --- | --- | --- |
| `sec_11_conclusion` | 空输入仍输出"编制依据充分""符合现行法律法规""措施布局合理""投资估算依据充分" | 事实复述按值状态给出；综合结论改走 `judgment()` |
| `sec_3_evaluation` | 借方缺失写成"无需外借土石方"；"表土全部用于绿化覆土"；"平衡合理、去向明确、来源可靠"；用目标值说"均满足要求" | 缺失/明确 0 分开；去向断言删除；结论走 `judgment()`；目标只作目标复述 |
| `sec_4_topsoil` | 数据缺失走进"经现场踏勘，项目用地范围内无可剥离表土"（编造现场调查）；"全部用于绿化覆土""不外运" | 缺失走缺口段；明确 0 只复述填报值；去向结论走 `judgment()` |
| `sec_7_5_benefit_analysis` | 只有目标值就说"各项指标可达到目标值要求""各项防治目标可以实现"；`reducible/new` 被称"治理比例"并 `min(...,100)` 封顶 | 目标/效果分离；无效果结果标"待计算"；比值如实给出并声明口径未确认，取消封顶 |
| `sec_2_5_sensitive_areas` | 字段缺失与空清单都输出"经逐项排查，项目区不涉及…等敏感区" | 缺失走缺口段；空清单只复述填报内容，排查结论走 `judgment()` |
| `sec_3_1_site_selection` | 空清单输出"不涉及…敏感区域，选址符合法律法规要求"；有敏感区时输出"论证程序已启动或完成""基本符合要求" | 三种情况全部走 `judgment()` |
| `sec_2_3_climate_zoning` | 字段缺失与空清单都输出"项目区不涉及国家级水土流失重点预防区或重点治理区" | 同 `sec_2_5`（本批在清点中发现，属同源缺陷） |
| `sec_5_disposal` | `no_site` 分支由"derived 查不到级别评定"推出，却断言"弃渣全部综合利用消纳，不设置永久弃渣场" | 字段整个缺失 → SKELETON + 适用性 UNKNOWN；空清单 → 结论走 `judgment()` |
| `sec_0_overview` | 缺失显示为"—"仍成句；措施投资分项缺失按 0 累加；末段用目标值说"各项指标均满足防治标准要求" | 缺失如实标注；分项缺失不按 0 累加并报 `VALUE_MISSING`；末段只复述目标；新增"未决事项"段 |
| `projection._PARENT_INTROS` | 一句话引言计入 `full_count`，被当成一份成果 | 标 `ContentRole.PARENT_INTRO`，不计入内容完成度分母（验收 Q01） |

## 未审查模板的处置

按 `03_P0_TASKS.md` P0-03 第 8 条，未改造模板的输出维持 UNASSESSED / NEEDS_REVIEW：

- 它们产出的 `NarrativeBlock` 不带 `quality_findings`，`ContentState` 在质量层恒为 `DRAFTED`（不会升到 `COMPLETE`）；
- 它们没有 `PROJECT_JUDGMENT` 段落，因此不会伪造"已复核"的结论；
- 但它们**仍在使用** `_v(facts, key, default="—")` / `_num(facts, key, default=0.0)` 这类取值方式，缺失会显示成"—"或被当成 0。这是本批**未消除**的风险面。

已做的两处抽查（非系统审查）：

- `sec_7_2_targets`：全文用"目标值"表述，未发现目标/效果混淆。
- `sec_10_management`：命中的"有效"来自"为确保…方案的有效实施，建设单位应…"，是要求性表述，不是对本项目的判断。

## 后续建议（不在 A 批范围）

改造剩余 18 个模板需要与 P0-04 的统一读取上下文一起做——否则会出现两套取值方式并存。建议在 B 批 P0-04 完成 `BuildContext` 后，用 `SectionEvidence` 统一替换 `_v` / `_num`，而不是在 A 批再手工改 18 个文件。
