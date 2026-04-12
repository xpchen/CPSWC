# Investment Facts Backfill Contract (v1 数据回填契约)

> **文档性质**: 准制度文件。定义 v1 投资估算链需要补充的全部 fact 字段、粒度、来源归口和附表映射。
> **上游依据**: INVESTMENT_SUBSYSTEM_CONTRACT.md + 样稿 01/02 附表结构
> **版本**: 2026-04-12
> **核心目标**: 回答"v1 到底要补哪些数据，谁提供，喂到哪"

---

## 一、目标与边界

本契约定义 InvestmentEstimationSubsystem 需要的**全部输入 facts**，使得：
- 投资估算总表（正文主表）从"补偿费行 live + 其余 —"变成"全部行 live"
- 9 张附表从 ENGINE_STUB 变成 CAN_GENERATE 或 LIVE
- 主体已列 / 方案新增拆分可自动化

**本契约不负责**：
- 定额抓取/同步的具体实现
- 前端录入 UI 设计
- 措施布设引擎的内部逻辑

---

## 二、分层输入模型

投资估算的输入分 6 层，每层有明确的来源归口：

```
Layer 1: measures_items    — 措施条目 (名称/类型/分区归属)
Layer 2: quantity_items    — 工程量 (数值/单位)
Layer 3: price_items       — 单价 (元/单位)
Layer 4: fee_rate_items    — 费率 (独立费用/预备费的百分比)
Layer 5: source_attribution — 来源标记 (主体已列 vs 方案新增)
Layer 6: summary_overrides — 汇总覆盖 (极少数需人工调整合计的情况)
```

---

## 三、最小必需 Facts 清单

### 3.1 措施条目层 (Layer 1)

```yaml
field.fact.investment.measures_registry:
  semantic_type: list_of_records
  record_schema:
    measure_id: string              # 唯一标识, 如 "eng_01"
    measure_name: string            # 名称, 如 "浆砌石挡土墙"
    fee_category: enum              # 归类: 工程措施 / 植物措施 / 临时措施 / 监测措施
    prevention_zone: string         # 所属防治分区, 如 "主体工程区"
    source_attribution: enum        # 主体已列 / 方案新增
    description: string             # 规格/备注
  protection_level: CRITICAL
  fact_class: F1_manual             # 必须人工提供
  feeds_tables:
    - 附表2 (新增分部估算)
    - 附表3 (主体已列)
    - 正文投资总表 (汇总)
```

### 3.2 工程量层 (Layer 2)

```yaml
field.fact.investment.quantities:
  semantic_type: list_of_records
  record_schema:
    measure_id: string              # 关联 measures_registry
    unit: string                    # 单位, 如 "m³" / "hm²" / "m"
    quantity: number                # 工程量数值
    quantity_source: string         # 来源说明 (措施设计/现场实测/估算)
  protection_level: CRITICAL
  fact_class: F1_manual             # 由设计院按措施布设确定
  feeds_tables:
    - 附表2 (新增分部估算)
    - 附表9 (工程单价表)
```

### 3.3 单价层 (Layer 3)

```yaml
field.fact.investment.unit_prices:
  semantic_type: list_of_records
  record_schema:
    measure_id: string              # 关联 measures_registry
    unit_price: number              # 单价 (元)
    price_source: enum              # 定额查询 / 市场调查 / 指导价
    price_reference: string         # 依据文号, 如 "粤水建设函〔2021〕532号"
  protection_level: PROTECTED
  fact_class: F2_external_sync      # 可由定额站/价格库同步
  feeds_tables:
    - 附表5 (材料预算价格)
    - 附表6 (机械台班费)
    - 附表8 (工程单价汇总)
    - 附表9 (工程单价表)
```

### 3.4 材料价格层 (Layer 3 子项)

```yaml
field.fact.investment.material_prices:
  semantic_type: list_of_records
  record_schema:
    material_name: string           # 材料名称
    spec: string                    # 规格
    unit: string                    # 单位
    market_price: number            # 市场价 (元)
    transport_cost: number          # 运杂费 (元)
    budget_price: number            # 预算价 = 市场价 + 运杂费
    price_reference: string         # 依据
  fact_class: F2_external_sync
  feeds_tables:
    - 附表5 (材料预算价格)
    - 附表7 (砂浆材料单价)
```

### 3.5 机械台班层 (Layer 3 子项)

```yaml
field.fact.investment.machine_hours:
  semantic_type: list_of_records
  record_schema:
    machine_name: string
    spec: string
    unit: string                    # "台班" / "台时"
    depreciation: number            # 折旧费
    maintenance: number             # 维修费
    fuel: number                    # 燃料费
    operator: number                # 人工费
    total_rate: number              # 合计台班费
    price_reference: string
  fact_class: F2_external_sync
  feeds_tables:
    - 附表6 (机械台班费)
```

### 3.6 费率层 (Layer 4)

```yaml
field.fact.investment.fee_rates:
  semantic_type: record
  record_schema:
    management_fee_rate: number     # 建设管理费率 (%)
    bid_fee_rate: number            # 招标业务费率 (%)
    consulting_fee_rate: number     # 经济技术咨询费率 (%)
    supervision_fee_rate: number    # 监理费率 (%)
    cost_consulting_rate: number    # 造价咨询费率 (%)
    research_design_rate: number    # 科研勘测设计费率 (%)
    acceptance_fee: number          # 验收咨询费 (固定额)
    reserve_rate: number            # 预备费率 (%, 通常 10%)
  protection_level: CRITICAL
  fact_class: F3_system_derived     # 按水总[2024]323号查表, 系统可自动填充
  feeds_tables:
    - 附表4 (独立费用/预备费)
    - 正文投资总表 (独立费用行 + 预备费行)
```

### 3.7 来源标记层 (Layer 5)

```yaml
# 不是独立 fact, 而是 measures_registry 里的 source_attribution 字段
# 取值: "主体已列" | "方案新增"
# 由设计院在录入措施条目时标注
# 系统不自动判断, 缺标注时默认"方案新增"(保守原则)
```

---

## 四、附表映射关系

| 附表 | 消费的 facts 层 | 计算规则 |
|---|---|---|
| **附表1** 投资估算总表 | 全部 → 五部分汇总 | sum by fee_category |
| **附表2** 新增分部估算表 | L1+L2+L3 (source=方案新增) | quantity × unit_price |
| **附表3** 主体已列投资表 | L1+L2+L3 (source=主体已列) | quantity × unit_price |
| **附表4** 独立费用/预备费 | L4 fee_rates + 一至四部分合计 | base × rate |
| **附表5** 材料预算价格表 | L3.4 material_prices | 直接展示 |
| **附表6** 机械台班费 | L3.5 machine_hours | 直接展示 |
| **附表7** 砂浆材料单价 | L3.4 子集 | 配比计算 |
| **附表8** 工程单价汇总 | L3 unit_prices | 直接展示 |
| **附表9** 工程单价表 | L1+L2+L3 逐项展开 | 工料机组价 |

---

## 五、空值与校验规则

| 场景 | 处理 |
|---|---|
| 缺 quantity (工程量) | 该措施行 amount = "—", 不参与汇总 |
| 缺 unit_price (单价) | 该措施行 amount = "—", 不参与汇总 |
| 缺 source_attribution | 默认 "方案新增" (保守) + 加 warning |
| 缺 fee_rates | 独立费用全行 "—" + 加 warning |
| 缺 price_reference | 允许为空, 但 lint 报 INFO (来源铁律宽松口径) |
| quantity × unit_price 计算结果 | 四舍五入到 0.01 万元 |

**硬禁令**: 不允许从 total_investment / civil_investment 反推任何分项。

---

## 六、Fact 三分类 (F1 / F2 / F3)

| 分类 | 含义 | 来源 | 举例 |
|---|---|---|---|
| **F1** | 必须人工提供 | 设计院/建设单位 | 工程量、措施名称、是否主体已列 |
| **F2** | 可由外部价格源同步 | 定额站/价格库/Excel 导入 | 材料价、机械台班、定额基价 |
| **F3** | 可系统派生 | calculator / 规范费率 | 独立费用、预备费、补偿费、小计合计 |

**后续定额数据源对接时，只接 F2 层，不碰 F1 和 F3。**

```
设计院 → F1 (measures + quantities + attribution)
定额站 → F2 (prices)
系统   → F3 (fee_rates + subtotals + grand_total)
         ↓
    附表1~9 + 正文主表
```

---

## 七、v0 → v1 迁移路径

| 阶段 | 状态 | 投资表填充度 |
|---|---|---|
| **v0 现在** | 仅 cal.compensation.fee live | ~5% (补偿费行) |
| **v1 Phase 1** | 补 F1 facts (措施条目+工程量) + F2 (单价) → 附表2/3/5/6/8/9 可生成 | ~60% |
| **v1 Phase 2** | 补 F3 facts (fee_rates) → 附表4 + 正文独立费用/预备费行 live | ~90% |
| **v1 Phase 3** | 接定额站 F2 自动同步 | ~95% (仅 F1 需手动) |

---

## 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-04-12 | v1 | 初版: 6 层输入模型 + 最小 facts 清单 + 附表映射 + F1/F2/F3 三分类 |
