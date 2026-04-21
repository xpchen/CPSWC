# Investment Facts Backfill Contract (v1 数据回填契约)

> **文档性质**: 准制度文件。定义 v1 投资估算链需要补充的全部 fact 字段、粒度、来源归口和附表映射。
> **上游依据**:
> - `governance/INVESTMENT_SUBSYSTEM_CONTRACT.md` (费用结构骨架)
> - `governance/PREVENTION_SYSTEM_CONTRACT.md` (措施条目、分区归属、主体已列/方案新增标注的真源)
> - 样稿 01/02 附表结构
> **版本**: 2026-04-21 (v1.1 · PreventionSystem 对齐修订版)
> **核心目标**: 回答"v1 到底要补哪些数据，谁提供，喂到哪"
>
> **本版修订摘要**: 承接 `PREVENTION_SYSTEM_CONTRACT.md` v0.6 Planning Baseline 的三大真源声明, 本契约将 `investment.measures_registry` 以及 Layer 1 / Layer 2 / Layer 5 的"措施条目/工程量/来源标注" 语义正式**降级为投资消费视图**。投资侧的主责边界 (单价、费率、造价合计) 保持不变。兼容期规则与 `PREVENTION_SYSTEM_CONTRACT.md` §2.3 完全一致。

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
- **措施条目、分区归属、主体已列/方案新增标注的真源定义** (归 `PREVENTION_SYSTEM_CONTRACT.md`, 本契约仅作为下游消费方引用)

---

## 一·附 真源引用声明 (PreventionSystem 对齐)

本契约所涉及的以下字段语义**不在本契约中定义**, 真源位于 `PREVENTION_SYSTEM_CONTRACT.md`:

| 字段 (投资侧视图名) | 真源位置 | 语义归属 |
|---|---|---|
| `measure_id` | `field.fact.prevention.measures_layout[].measure_id` | PreventionSystem |
| `measure_name` | `field.fact.prevention.measures_layout[].measure_name` | PreventionSystem |
| `fee_category` | `field.fact.prevention.measures_layout[].measure_type` (三类映射: engineering→工程措施 / plant→植物措施 / temporary→临时措施) | PreventionSystem |
| `prevention_zone` | `field.fact.prevention.measures_layout[].primary_zone_ref` → `field.fact.prevention.zones[].zone_label` | PreventionSystem |
| `source_attribution` | `field.fact.prevention.measures_layout[].source_attribution` (两值: existing_main_engineering / new_in_plan) | PreventionSystem |
| `quantity` / `unit` | `field.fact.prevention.measures_layout[].quantity` / `.unit` | PreventionSystem |

**消费纪律**: 投资侧**禁止**维护与上述真源平行的独立副本 (含"临时缓存""兼容清单"等任何名义), **禁止**对真源执行反向写入, **禁止**以文字描述"主体已列"或"方案新增"之外的第三值。违反视同 `ARCHITECTURE_DECISIONS.md` 决议 4 违规。

**兼容期规则** (与 `PREVENTION_SYSTEM_CONTRACT.md` §2.3 对齐):

| 过渡期状态 | 允许 | 禁止 |
|---|---|---|
| 代码层 `investment.measures_registry` 结构未迁移 | ✓ 读路径继续工作 | ✗ 作为独立 SoT 被新代码写入 |
| 新增任何消费 measures 的功能 | 必须直接消费 `prevention.measures_layout[]` | ✗ 消费 `investment.measures_registry` |
| 文档/schema 声明 | 必须标注 `investment.measures_registry` 为"投资消费视图" | ✗ 在任何新文档中以 SoT 语义描述它 |

**迁移截止点**: v0.6 契约补齐后的第一个 InvestmentEstimationSubsystem 实动改动步骤 (预计 v0.7 启动时) 必须完成代码层对齐, 届时 `investment.measures_registry` 降级为纯视图或被取消。过渡期不得无限延长; 若 v0.7 未能完成迁移, 须走 RFC 明示延期理由。

---

## 二、分层输入模型

投资估算的输入分 6 层，每层有明确的来源归口:

```
Layer 1: measures_items    — 措施条目 (名称/类型/分区归属)     [真源: PreventionSystem]
Layer 2: quantity_items    — 工程量 (数值/单位)                 [真源: PreventionSystem]
Layer 3: price_items       — 单价 (元/单位)                     [真源: Investment 本契约]
Layer 4: fee_rate_items    — 费率 (独立费用/预备费的百分比)     [真源: Investment 本契约]
Layer 5: source_attribution — 来源标记 (主体已列 vs 方案新增)   [真源: PreventionSystem]
Layer 6: summary_overrides — 汇总覆盖 (极少数需人工调整合计的情况) [真源: Investment 本契约]
```

**投资侧主责边界**: Layer 3 (单价) / Layer 4 (费率) / Layer 6 (汇总覆盖) 由投资域全权定义, PreventionSystem 契约不触及。Layer 1 / 2 / 5 仅作为视图在本契约中出现, 真源归 PreventionSystem 契约。

---

## 三、最小必需 Facts 清单

### 3.1 措施条目层 (Layer 1) — **投资消费视图**

> **语义降级声明** (PreventionSystem 对齐): `field.fact.investment.measures_registry` 自本版起**不再作为独立真源**, 降级为对 `field.fact.prevention.measures_layout[]` 的投资消费视图。本节保留仅用于描述投资侧消费这些字段的视图结构与过渡期兼容行为。
>
> **监测类不再进入本层**: 原 `fee_category` 枚举中的"监测措施"已随 PreventionSystem 契约 §5.4 的三类闭集同步从本层移除。监测投资由独立子系统 (未来 monitoring 子系统) 驱动, 不再由本层消费。

```yaml
# 投资消费视图 (view), 非真源
investment.measures_registry (view of prevention.measures_layout[]):
  semantic_type: list_of_records  (derived view)
  source_of_truth: field.fact.prevention.measures_layout[]  # 必填, 真源位置
  view_field_mapping:
    measure_id:         prevention.measures_layout[].measure_id         # 直映, stable_id
    measure_name:       prevention.measures_layout[].measure_name        # 直映
    fee_category:       prevention.measures_layout[].measure_type        # 映射: engineering→工程措施 / plant→植物措施 / temporary→临时措施
    prevention_zone:    prevention.measures_layout[].primary_zone_ref
                        → prevention.zones[].zone_label                   # 两跳解析
    source_attribution: prevention.measures_layout[].source_attribution   # 映射: existing_main_engineering→主体已列 / new_in_plan→方案新增
    description:        prevention.measures_layout[].specification        # 直映 (原 description 字段在真源命名为 specification)
  protection_level: CRITICAL  (继承真源)
  fact_class: F1_prevention  (见第六节; 数据由 PreventionSystem 驱动提供, 非 investment 侧自主录入)
  feeds_tables:
    - 附表2 (新增分部估算)
    - 附表3 (主体已列)
    - 正文投资总表 (汇总)
  transitional_compatibility:
    v0.6: 允许旧 investment.measures_registry 读路径继续工作, 但新写入必须走真源
    v0.7: 代码层必须完成对齐, 本视图降级为纯 derived 或被取消
```

### 3.2 工程量层 (Layer 2) — **投资消费视图**

> **语义降级声明**: 工程量数值与单位的真源位于 `prevention.measures_layout[].quantity` / `.unit`。本层保留 `quantity_source` 作为投资侧的补充说明字段, 但 quantity 值本身不得在本层独立录入。

```yaml
# 投资消费视图 (view)
investment.quantities (view of prevention.measures_layout[]):
  semantic_type: list_of_records  (derived view)
  source_of_truth: field.fact.prevention.measures_layout[]
  view_field_mapping:
    measure_id:   prevention.measures_layout[].measure_id   # 真源 stable_id
    unit:         prevention.measures_layout[].unit          # 直映
    quantity:     prevention.measures_layout[].quantity      # 直映, 数值真源
  investment_side_only_fields:
    quantity_source: string   # 投资侧补充说明 (如定额套用口径), 允许本层承载
  protection_level: CRITICAL  (继承真源)
  fact_class: F1_prevention
  feeds_tables:
    - 附表2 (新增分部估算)
    - 附表9 (工程单价表)
  transitional_compatibility:
    v0.6: 允许旧 investment.quantities 读路径继续工作
    v0.7: quantity / unit 字段强制从真源读取, 旧独立录入路径作废
```

### 3.3 单价层 (Layer 3) — **投资域主责 (保留)**

> **主责边界**: 单价本体是投资域主责字段, 真源位于本契约。`measure_id` 作为外键引用 `prevention.measures_layout[].measure_id`, 但单价数值、来源、依据文号由本层独立承载, PreventionSystem 契约不消费。

```yaml
field.fact.investment.unit_prices:
  semantic_type: list_of_records
  record_schema:
    measure_id: string              # 外键引用 prevention.measures_layout[].measure_id (stable_id)
    unit_price: number              # 单价 (元), 投资域主责
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

### 3.7 来源标记层 (Layer 5) — **PreventionSystem 真源, 投资侧仅消费**

> **语义归属重定位**: `source_attribution` 的真源位于 `prevention.measures_layout[].source_attribution`, 取值闭集为 `existing_main_engineering` / `new_in_plan` (两值)。投资侧消费时做显示层映射 (主体已列 / 方案新增), 但**不得**在投资侧独立标注或修改该字段。
>
> **标注责任转移**: 原"由设计院在录入投资条目时标注"的做法作废。source_attribution 由设计院在**措施条目录入阶段** (PreventionSystem 上游) 完成, 投资侧继承真源值。
>
> **缺值处理**: 真源侧缺 source_attribution 时, 由 PreventionSystem 契约的 lint 规则处理 (走决议 4/8 的 evidence/ provenance 约束), 投资侧**不得**再用"默认方案新增 + warning"的保守兜底逻辑, 以免与真源侧的 PREVENTION_XLAYER_001 / PREVENTION_XLAYER_001B 硬约束冲突。
>
> 本层无独立 field.fact.investment.* 对象, 仅为语义层说明。

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

| 场景 | 处理 | 归属 |
|---|---|---|
| 缺 quantity (工程量) | 该措施行 amount = "—", 不参与汇总; 真源侧同步触发 PreventionSystem 契约的 measures_layout 字段完整性校验 | PreventionSystem + Investment 联动 |
| 缺 unit_price (单价) | 该措施行 amount = "—", 不参与汇总 | Investment 主责 |
| 缺 source_attribution | **不得在投资侧兜底**; 由 PreventionSystem 契约的 PREVENTION_XLAYER_001 / PREVENTION_XLAYER_001B 硬约束承担 (ERROR 级); 投资侧消费视图直接跟随真源结果 | PreventionSystem 主责 |
| 缺 fee_rates | 独立费用全行 "—" + 加 warning | Investment 主责 |
| 缺 price_reference | 允许为空, 但 lint 报 INFO (来源铁律宽松口径) | Investment 主责 |
| 缺 prevention_zone (真源缺 primary_zone_ref) | 投资侧消费视图报 ERROR, 且 PreventionSystem 侧 PREVENTION_MEASURE_001 红线同步 ERROR | PreventionSystem 主责 |
| quantity × unit_price 计算结果 | 四舍五入到 0.01 万元 | Investment 主责 |

**硬禁令** (本契约原有):
- 不允许从 total_investment / civil_investment 反推任何分项。

**硬禁令** (本版新增, PreventionSystem 对齐):
- 不允许在投资侧对 `measure_id` / `measure_name` / `fee_category` / `prevention_zone` / `source_attribution` / `quantity` / `unit` 做独立写入或修改, 必须通过真源变更 (修改 `prevention.measures_layout[]`) 实现。
- 不允许在投资侧用"默认方案新增 + warning"兜底缺失的 source_attribution, 以免掩盖真源侧的结构性错误。
- 不允许在投资侧引入"监测措施"作为 `fee_category` 枚举值 (已随 PreventionSystem §5.4 三类闭集同步移除)。

---

## 六、Fact 三分类 (F1 / F2 / F3)

> **PreventionSystem 对齐修订**: F1 原为单一类, 本版拆为 **F1-prevention** 与 **F1-investment** 两个子类, 以精确标注真源归属。F2 / F3 保持不变。

| 分类 | 含义 | 来源 | 真源归属 | 举例 |
|---|---|---|---|---|
| **F1-prevention** | 必须人工提供, 真源位于 PreventionSystem 契约 | 设计院/水保编制方 (在措施条目录入阶段) | **PreventionSystem 契约** (本契约仅作视图消费) | 措施名称、工程量、分区归属、主体已列/方案新增标注 |
| **F1-investment** | 必须人工提供, 真源位于投资域 | 设计院/建设单位 (在投资录入阶段) | **本契约** | 单价来源说明 `price_source` / `quantity_source` (补充说明层) |
| **F2** | 可由外部价格源同步 | 定额站/价格库/Excel 导入 | 本契约 | 材料价、机械台班、定额基价、工程单价 |
| **F3** | 可系统派生 | calculator / 规范费率 | 本契约 | 独立费用、预备费、补偿费、小计合计 |

**后续定额数据源对接时, 只接 F2 层, 不碰 F1 和 F3。F1-prevention 层的维护走 PreventionSystem 契约路径, 不由本契约或定额源驱动。**

```
PreventionSystem → F1-prevention (measures + quantities + zones + attribution)
                         │
                         ▼
设计院 (投资录入)      → F1-investment (price_source / quantity_source 等补充说明)
定额站               → F2 (prices)
系统                 → F3 (fee_rates + subtotals + grand_total)
                         ↓
                    附表1~9 + 正文主表
```

---

## 七、v0 → v0.6 → v0.7 迁移路径

> **本版修订**: 原 "v0 → v1" 两阶段路径细化为 "v0 → v0.6 → v0.7" 三阶段, 明示 PreventionSystem 对齐的兼容期边界。

| 阶段 | 状态 | 投资表填充度 | PreventionSystem 对齐状态 |
|---|---|---|---|
| **v0 现在** | 仅 cal.compensation.fee live | ~5% (补偿费行) | 尚未对齐 (PreventionSystem 契约 v0.6 Planning Baseline 已签发) |
| **v0.6 兼容期** | PreventionSystem 契约已签发并进入 registry 回填; 旧 `investment.measures_registry` 读路径仍可工作 | ~5% (仍仅补偿费 live) | **契约层对齐完成, 代码层兼容期**: 新代码必须走真源, 旧读路径保留 |
| **v0.7 Phase 1** | 代码层完成对齐 + 补 F1-prevention (PreventionSystem 真源完整) + F2 (单价) → 附表2/3/5/6/8/9 可生成 | ~60% | **代码层对齐完成**, `investment.measures_registry` 降级为纯视图或被取消 |
| **v0.7 Phase 2** | 补 F3 facts (fee_rates) → 附表4 + 正文独立费用/预备费行 live | ~90% | 已对齐 |
| **v1 Phase 3** | 接定额站 F2 自动同步 | ~95% (仅 F1-prevention + F1-investment 需手动) | 已对齐 |

**迁移门禁** (与 `PREVENTION_SYSTEM_CONTRACT.md` §2.3 一致): v0.6 代码层兼容期不得无限延长; 若 v0.7 Phase 1 未能完成代码层对齐, 须走 RFC 明示延期理由。

---

## 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-04-12 | v1 | 初版: 6 层输入模型 + 最小 facts 清单 + 附表映射 + F1/F2/F3 三分类 |
| 2026-04-21 | v1.1 (PreventionSystem 对齐修订版) | 承接 `PREVENTION_SYSTEM_CONTRACT.md` v0.6 Planning Baseline, 四点对齐: (1) `investment.measures_registry` 语义正式降级为投资消费视图, 新增头部"语义降级声明"+ 一·附 "真源引用声明" 节; (2) Layer 1 / 2 / 5 标注真源位置, F1 拆为 F1-prevention + F1-investment 两个子类, 在 F1/F2/F3 归属表中写明"措施清单真源位于 PreventionSystem 契约"; (3) 保留投资侧对单价 (3.3) / 费率 (3.6) / 造价合计 (F3) 的主责边界, 不被 PreventionSystem 反向吞并; (4) 兼容期措辞与 PreventionSystem §2.3 完全一致, 新增 v0.6 兼容期阶段, 迁移截止点锁定 v0.7 Phase 1; 同步对 `fee_category` 枚举移除"监测措施" (对齐 PreventionSystem §5.4 三类闭集), 空值与校验规则新增跨契约联动列与三条新硬禁令。 |
