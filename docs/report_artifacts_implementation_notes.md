# CPSWC 报告书 19 张表格实现说明

> **文档性质**: 工程实现参考，逐表定义输入来源、表格结构、renderer 形态、插入位置和 v0/v1 边界。
> **上游依据**: governance/REPORT_ARTIFACT_CLASSIFICATION_v1.md
> **适用范围**: P0 CAN_GENERATE renderer 实现 + P1 InvestmentEstimationSubsystem 设计
> **版本**: 2026-04-12

---

## 一、已 LIVE（2 张）

### 1. art.table.investment.compensation_fee — 水土保持补偿费计费表

| 项目 | 说明 |
|---|---|
| **输入来源** | field.derived.investment.compensation_fee_amount (cal.compensation.fee) + field.fact.regulatory.compensation_fee_rate + field.fact.land.permanent_area + field.fact.land.temporary_area + field.fact.location.province_list |
| **表格结构** | 2 列 (项目 / 内容), 6 行 (计算器 / 公式 / 输出字段 / 金额 / 状态 / 费率依据) |
| **renderer 形态** | 简表, 表头灰底加粗, 数字右对齐 |
| **插入位置** | 正文 9.2 节内嵌; 同时在 AT-03 投资附件中作为子表 |
| **v0 状态** | ✅ LIVE — cal.compensation.fee + document_renderer.py 已全自动 |
| **v1 扩展** | 跨省项目需按 province_list 分省列出; 接入 region_override 后费率动态取值 |

### 2. art.table.weighted_target_calculation — 水土流失防治指标计算表 (AT-02)

| 项目 | 说明 |
|---|---|
| **输入来源** | field.derived.target.weighted_comprehensive_target (cal.target.weighted_comprehensive) + field.fact.prevention.control_standard_level_breakdown + field.fact.natural.water_soil_zoning |
| **表格结构** | 3 列 (防治指标 / 加权目标值 / 单位), 6 行 (治理度 / 控制比 / 渣土防护 / 表土保护 / 恢复率 / 覆盖率) |
| **renderer 形态** | 简表, 表头灰底加粗 |
| **插入位置** | 正文 7.2 节内嵌; 条件出现 (ob.evaluation.weighted_target_required 触发时) |
| **v0 状态** | ✅ LIVE — cal.target.weighted_comprehensive + document_renderer.py 已全自动 |
| **v1 扩展** | 多区划时需按 water_soil_zoning 分表; 单等级项目可简化为直接引述不出表 |

---

## 二、CAN_GENERATE（6 张）— P0 优先实现

### 3. art.table.earthwork_balance — 土石方 (不含表土) 平衡表

| 项目 | 说明 |
|---|---|
| **输入来源** | field.fact.earthwork.excavation / fill / borrow / self_reuse / spoil / comprehensive_reuse |
| **表格结构** | 矩阵表: 行=项目组成 (场地平整/基础开挖/...), 列=挖方/填方/借方/弃方/利用, 末行合计。v0 简化为单行汇总 (无分项拆分) |
| **合计行** | 有, 在表末 |
| **单位** | 万 m³, 精度 0.01 |
| **是否跨页** | 可能, 大型项目分项多时 |
| **renderer 形态** | 汇总表 (v0 单行), 后续升级为分组矩阵表 |
| **插入位置** | 正文 2.2 节引用 |
| **v0 实现** | 从 facts 6 个字段直接生成单行汇总表。不分项, 不分防治分区 |
| **v1 扩展** | 按项目组成分项拆分; 按防治分区交叉; 需 earthwork_breakdown 字段支撑 |

### 4. art.table.total_land_occupation — 工程总占地表

| 项目 | 说明 |
|---|---|
| **输入来源** | field.fact.land.total_area / permanent_area / temporary_area |
| **表格结构** | 4 列 (项目 / 永久占地 / 临时占地 / 小计), v0 单行汇总 |
| **合计行** | 有 |
| **单位** | hm², 精度 0.01 |
| **renderer 形态** | 简表 |
| **插入位置** | 正文 2.1 节引用 |
| **v0 实现** | 从 3 个 fact 字段直接生成 |
| **v1 扩展** | 按建设内容/项目组成分行; 区分占地类型 (耕地/林地/草地/...) |

### 5. art.table.land_occupation_by_county — 分县占地表

| 项目 | 说明 |
|---|---|
| **输入来源** | field.fact.land.county_breakdown (list_of_records: county/nature/type/area) |
| **表格结构** | 4+ 列 (县名 / 占地性质 / 占地类型 / 面积), 每县一行或多行 |
| **合计行** | 有, 按县小计 + 总计 |
| **单位** | hm² |
| **renderer 形态** | 分组表 (按县分组) |
| **插入位置** | 正文 2.1 节, 跟在 total_land_occupation 之后 |
| **v0 实现** | 从 county_breakdown list 直接展开, 每条 record 一行 |
| **v1 扩展** | 无重大变化, 但需处理跨市项目的市级汇总 |

### 6. art.table.topsoil_balance — 表土平衡表

| 项目 | 说明 |
|---|---|
| **输入来源** | field.fact.topsoil.stripable_area / stripable_volume + field.fact.topsoil.excavation / fill (placeholder stubs) |
| **表格结构** | 类似土石方平衡: 行=表土来源/去向, 列=剥离量/回覆量/外运量/平衡 |
| **合计行** | 有 |
| **单位** | 万 m³ (体积) / hm² (面积) |
| **renderer 形态** | 汇总表 |
| **插入位置** | 正文 4.2 节引用 |
| **v0 实现** | 从 topsoil facts 直接生成单行汇总。注意: 部分上游字段仍是 placeholder stub |
| **v1 扩展** | 按防治分区分行; 接入措施布设引擎后上游数据填实 |
| **注意** | v0 上游 facts 部分为 placeholder stub (treated_topsoil_volume 等), 生成表时需标注"待措施布设确认" |

### 7. art.table.responsibility_range_by_admin_division — 防治责任范围统计表

| 项目 | 说明 |
|---|---|
| **输入来源** | field.fact.location.county_list + field.fact.land.county_breakdown + field.fact.prevention.responsibility_range_area |
| **表格结构** | 3+ 列 (行政区 / 责任范围面积 / 占总面积比例), 每县一行 |
| **合计行** | 有 |
| **单位** | hm² + % |
| **条件出现** | ob.sensitive_overlay.multi_admin_breakdown 触发时 |
| **renderer 形态** | 简表 |
| **插入位置** | 正文 7.1.1 节 |
| **v0 实现** | 从 county_list + county_breakdown 直接展开 |
| **v1 扩展** | 需要实际各县级区的责任范围面积数据 (目前 county_breakdown 只有占地, 没有独立的"责任范围"拆分) |

### 8. art.table.spoil_summary — 弃渣场和临时堆土场设置汇总表

| 项目 | 说明 |
|---|---|
| **输入来源** | field.fact.disposal_site.level_assessment + field.derived.disposal_site.level_assessment + field.fact.construction.temp_topsoil_site |
| **表格结构** | 多列: 编号/名称/位置/类型/占地/容量/堆渣量/最大高度/级别/堆置方案/恢复方向 |
| **合计行** | 有 (堆渣量合计) |
| **单位** | 万 m³ / m / hm² |
| **条件出现** | ob.disposal_site.site_selection 触发时 |
| **renderer 形态** | 宽幅明细表, 可能需要横向排版或缩小字号 |
| **插入位置** | 正文 5.2 节 |
| **v0 实现** | 合并两个来源 (disposal_site fact + temp_topsoil_site fact), 逐场一行; level 从 derived 取 |
| **v1 扩展** | 接入 SpoilStabilityEngine 后可补充稳定分析结论列 |
| **注意** | Huizhou 样本无弃渣场但有 temp_topsoil_site, 表中应只显示 temp_topsoil_site; Disposal 样本两者都有 |

---

## 三、ENGINE_STUB — 投资系列（11 张）

> 以下 11 张表全部依赖 InvestmentEstimationSubsystem (engine.InvestmentEstimationSubsystem)。
> v0 阶段为占位状态, v1 P1 优先级实现。

### 9. art.table.investment_appendix — 投资附件 (AT-03 总包)

| 项目 | 说明 |
|---|---|
| **性质** | 10 张投资子表的父容器, 本身不渲染独立表格, 而是包含子表 |
| **子表** | total_summary / engineering / plant / temporary / monitoring / annual / compensation_fee / unit_prices / machine_hours / material_prices / independent_fees |
| **插入位置** | 正文附件区, 9.1 节引用 |
| **v0 实现** | 子表之一 (compensation_fee) 已 LIVE, 其余占位 |

### 10. art.table.investment.total_summary — 投资估算总表

| 项目 | 说明 |
|---|---|
| **输入** | 各分项表汇总 |
| **结构** | 行=费用项 (工程措施/植物措施/临时措施/独立费/补偿费/...), 列=金额 |
| **合计** | 有, 总投资 |
| **单位** | 万元 |
| **renderer** | 汇总表 |
| **依赖** | 所有分项子表先完成 |

### 11-14. 四张措施估算表

| 工件 | 名称 | 输入模式 | 结构 |
|---|---|---|---|
| art.table.investment.engineering_measures | 工程措施估算表 | A+B: 用户输入工程量, 系统按定额算价 | 行=措施项, 列=数量/单位/单价/合价 |
| art.table.investment.plant_measures | 植物措施估算表 | 同上 | 同上 |
| art.table.investment.temporary_measures | 临时措施估算表 | 同上 | 同上 |
| art.table.investment.monitoring_measures | 监测措施估算表 | 同上 (监测点数/频次输入) | 同上 |

**共性**: 行=具体措施条目, 列=名称/规格/单位/数量/单价/合价。单价来自 unit_prices + machine_hours + material_prices 三张基础单价表。

### 15. art.table.investment.independent_fees — 独立费用计算表

| 项目 | 说明 |
|---|---|
| **输入** | 工程造价总额 (从上面 4 张措施表汇总) |
| **结构** | 行=费用项 (建设管理费/监理费/科研勘测设计费/...), 列=费率/基数/金额 |
| **计算** | 全自动, 按水总[2024]323 号规定费率 |
| **单位** | 万元 |

### 16. art.table.investment.annual_breakdown — 分年度投资估算表

| 项目 | 说明 |
|---|---|
| **输入** | 总投资 + field.fact.schedule.start_time / end_time + 施工进度分配比例 |
| **结构** | 行=费用项, 列=年度 (施工期每年一列) |
| **v0/v1** | 需用户提供年度分配比例 (A 类输入), 系统按比例计算 |

### 17-19. 三张基础单价表

| 工件 | 名称 | 输入模式 | 说明 |
|---|---|---|---|
| art.table.investment.unit_prices | 工程单价汇总表 | A: 纯表单 | 设计院按当地定额确定 |
| art.table.investment.machine_hours | 施工机械台时费汇总表 | A: 纯表单 | 同上 |
| art.table.investment.material_prices | 主要材料单价汇总表 | A: 纯表单 | 同上 |

**共性**: 这三张表是投资估算的底层参数输入, 系统只提供结构化模板, 数值全部由用户/设计院填写。是 InvestmentEstimationSubsystem 的基础数据层。

---

## 四、P0 CAN_GENERATE Renderer 实现优先级

基于上述分析, P0 batch 的 6 张表推荐实现顺序:

| 顺序 | 表格 | 复杂度 | 理由 |
|---|---|---|---|
| 1 | art.table.total_land_occupation | 低 | 3 个 fact → 单行表, 最简单 |
| 2 | art.table.earthwork_balance | 低 | 6 个 fact → 单行汇总 |
| 3 | art.table.land_occupation_by_county | 中 | list_of_records → 分组表 |
| 4 | art.table.topsoil_balance | 中 | 部分上游 placeholder, 需处理缺值 |
| 5 | art.table.responsibility_range_by_admin_division | 中 | 条件表 + 需计算占比 |
| 6 | art.table.spoil_summary | 高 | 合并两个来源 + level 从 derived 取 + 宽幅明细 |

---

## 五、与 narrative section 的嵌入关系

| 表格 | 嵌入 narrative section | 引用方式 |
|---|---|---|
| total_land_occupation | sec.project_overview.land_occupation (2.1) | 正文后接表 |
| land_occupation_by_county | sec.project_overview.land_occupation (2.1) | 紧接上表 |
| earthwork_balance | sec.project_overview.earthwork_balance (2.2) | 正文后接表 |
| topsoil_balance | sec.topsoil.balance (4.2) | 正文后接表 |
| responsibility_range_by_admin_division | sec.soil_loss_prevention.responsibility_range_by_county (7.1.1) | 条件节内嵌 |
| spoil_summary | sec.disposal_site.site_selection (5.2) | 条件节内嵌 |
| weighted_target_calculation | sec.soil_loss_prevention.targets (7.2) | 已 LIVE, 正文后接表 |
| compensation_fee | sec.investment_estimation.compensation_fee (9.2) | 已 LIVE, 正文后接表 |

---

## 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-04-12 | v1 | 初版: 19 张表逐表实现说明 + P0 顺序 + narrative 嵌入关系 |
