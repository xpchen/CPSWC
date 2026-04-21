# PreventionSystem 契约 (v0.6 Planning Baseline)

> **文档性质**: 准制度文件。定义防治体系域 (分区 / 措施界定 / 措施布设) 的真源归属、schema、一致性约束与投影边界。
> **上游依据**: `governance/ARCHITECTURE_DECISIONS.md` (决议 1/2/3/4/5/6/8) + `governance/INVESTMENT_SUBSYSTEM_CONTRACT.md` + `governance/INVESTMENT_FACTS_BACKFILL_CONTRACT.md` + `governance/REPORT_ARTIFACT_CLASSIFICATION_v1.md`
> **覆盖章节**: 第 3 章 3.7 水保功能措施界定 / 第 7 章 7.4 防治分区 / 7.5 措施总体布局 / 7.7 分区措施布设
> **下游消费方**: InvestmentEstimationSubsystem · NarrativeProjection · ArtifactProjection · ObligationSet
> **版本**: 2026-04-21 (v0.6 Planning Baseline)

---

## 一、文档性质、域边界与真源声明

### 1.1 文档性质

本契约是 v0.6 阶段"可审报告骨架"的结构宪法。任何触及 Ch3.7 / Ch7.4 / Ch7.5 / Ch7.7 的 schema 设计、字段登记、narrative 投影、表图渲染、投资归口逻辑的代码改动，必须先通过本契约约束。违反者按 `ARCHITECTURE_DECISIONS.md` 反升级条款同等严重度处理。

### 1.2 域边界

**本契约覆盖**:

- Ch3.7 水保功能措施界定 (主体工程措施的水保功能认定)
- Ch7.4 防治分区 (分区划分与责任范围归属)
- Ch7.5 措施总体布局 (措施体系的整体组织)
- Ch7.7 分区措施布设 (各分区的具体措施与工程量)

**本契约不覆盖** (以免发散):

- Ch7.6 工程级别与设计标准 (暴雨公式 / 排水设计 → 独立契约)
- Ch7.8 施工组织 (已有 `field.fact.construction_schedule.*`, 不重叠)
- Ch8 监测方案本体 (仅在 Ch7 侧建立关联引用, 不定义监测 schema)
- 分区自动划分算法 (GIS 级任务, 属 v1 GeoPipeline 扩展)
- 措施推荐引擎 (属 v0.7 范畴)
- 报告表格式下的分区简化表达 (第二 Grammar 分支)

### 1.3 三大真源声明 (本契约的宪法核心)

| 真源对象 | 命名空间 | 唯一性语义 | 下游消费方 |
|---|---|---|---|
| **防治分区** | `field.fact.prevention.zones[]` | 本方案防治分区的**唯一真源** | Ch7.4 narrative / 分区汇总表 / F-04 责任范围图 / F-10 措施布置图 / 投资分区归口 |
| **措施布设** | `field.fact.prevention.measures_layout[]` | **纳入本方案水保体系的措施**的唯一真源 | Ch7.5 / Ch7.7 narrative / 措施布设表 / F-10 / 投资估算附表 2/3/9 |
| **措施界定** | `field.fact.measures.classification[]` | 主体工程措施是否具有水保功能的**认定真源** | Ch3.7 narrative / 措施界定表 / measures_layout 的路径 A 流入源 |

**SoT 边界精确定义 (D1 批示落地)**:

> `prevention.measures_layout[]` 是**纳入本方案水保体系的措施记录真源**，**不是全主体工程措施宇宙真源**。

主体工程侧的设计措施宇宙属于主体工程设计文件域，不在本契约覆盖范围。只有经 `measures.classification[]` 认定为"纳入水保"的主体措施，与方案新增的水保措施，才进入本契约的 `measures_layout[]`。这条边界是为了防止域无限膨胀。

### 1.4 消费方的消费纪律

所有下游消费方对上述三大真源的访问必须经过 `FieldIdentityRegistry` 的 projection 机制 (决议 4)。**禁止**任何消费方:

- 维护与真源平行的独立副本 (含"临时缓存""兼容清单"等任何名义)
- 对真源执行反向写入
- 在 narrative 模板 / AST 生成器中硬编码分区名、措施名、工程量

违反者视同 decision 4 违规。

---

## 二、与上游治理文件的接口

### 2.1 决议沿用清单 (逐条声明)

| 决议 | 在本契约的生效方式 |
|---|---|
| **决议 1** (特性表非语义根) | 防治分区不经由特性表派生, 特性表中任何分区/措施字段必须标注为 `projection_of: field.fact.prevention.*` |
| **决议 2** (ConditionEngine 输出 Obligation) | 本契约**不新增** obligation。已有 obligation 在触发 Ch7 义务时以本契约字段作为 `evidence_anchor_refs` |
| **决议 3** (stable_id 优先) | 分区、措施、界定记录一律使用 stable_id, 显示编号晚绑定; 具体命名空间见 3.5 |
| **决议 4** (Fact→Narrative 过 Projection) | Ch3.7 / Ch7.4 / Ch7.5 / Ch7.7 全部 narrative node 必须声明 `projection_source_refs`, 禁止硬编码 |
| **决议 5** (RulesetVersion 按项目申报时间) | v0.6 仅支持新版规则集 (2026 模板 + 2018 格式 + 2024 估算 + 广东包); 其他版本不进入本契约 |
| **决议 6** (ExpertSwitch Governance) | `measures.classification[]` 的 `verdict` 字段作为典型 expert-switch, 必须携带完整 `governance_block` |
| **决议 8** (Source Provenance 双锚) | 分区类型枚举的每条扩展登记、每条 classification 的认定依据, 必须同时携带 `normative_basis_refs` + `evidence_anchor_refs` |

### 2.2 与 INVESTMENT 契约的接口

| 投资契约条目 | 本契约对应 | 关系 |
|---|---|---|
| `field.fact.investment.measures_registry` | `field.fact.prevention.measures_layout[]` | **后者为真源**, 前者降级为投资视图投影 |
| 主体已列 vs 方案新增 拆分规则 | `measures_layout[].source_attribution` | 语义完全对齐, 不引入新概念 |
| 五部分费用分项 | `measures_layout[].measure_type` | 投资归口由 measure_type 派生 |
| F1/F2/F3 fact 三分类 | `measures_layout[]` 内部字段按粒度归属 | 措施名/归属/归口 → F1; 工程量/单价 → F2/F1 混合 |

### 2.3 兼容期与非破坏性对齐原则 (调整 2 落地)

**契约先行, 代码兼容可后移**。

v0.6 阶段的本契约先定义规范真相。现有代码中的 `investment.measures_registry` 在过渡期 **允许以兼容字段/兼容视图形式保留**，但其语义必须同步降级:

| 过渡期状态 | 允许 | 禁止 |
|---|---|---|
| 代码层 `investment.measures_registry` 结构未迁移 | ✓ 读路径继续工作 | ✗ 作为独立 SoT 被新代码写入 |
| 新增任何消费 measures 的功能 | 必须直接消费 `prevention.measures_layout[]` | ✗ 消费 `investment.measures_registry` |
| 文档/schema 声明 | 必须标注 `investment.measures_registry` 为"投资消费视图", 注明真源为 `prevention.measures_layout[]` | ✗ 在任何新文档中以 SoT 语义描述它 |

**迁移截止点**: v0.6 契约补齐后的第一个 InvestmentEstimationSubsystem 实动改动步骤 (预计 v0.7 启动时) 必须完成代码层对齐, 届时 `investment.measures_registry` 降级为纯视图或被取消。过渡期不得无限延长; 若 v0.7 未能完成迁移, 须走 RFC 明示延期理由。

---

## 三、概念与术语定义

### 3.1 责任范围 / 分区 / 占地 的关系 (硬区分)

| 概念 | 定义 | 在本契约中的归属 |
|---|---|---|
| **防治责任范围** (`responsibility_range`) | 法定义务承担的地表空间总和 (项目建设区 + 直接影响区, 按 GB 50433-2018 口径) | 已有 `field.fact.location.*` + `field.fact.land.*`, 本契约引用不重建 |
| **工程占地** (`land_occupation`) | 项目实际占用的土地分类与面积 (永久/临时, 按用地类型) | 已有 `field.fact.land.*`, 本契约引用不重建 |
| **防治分区** (`prevention.zones[]`) | 基于**水保防治逻辑**对责任范围做的划分单元, 每区内措施布设同质化 | **本契约定义** |

**硬区分**:

- 防治分区 ≠ 工程占地。工程占地按"永久/临时/用地类型"分类; 防治分区按"水保防治单元"分类。**两者不同构**。
- 工程占地可以作为分区划分的**依据之一** (如临时占地常对应临时堆土区), 但不得直接用占地分类冒充分区。
- 一个分区可跨多个占地类型; 一个占地类型可被切入多个分区。

### 3.2 措施 / 措施体系 / 措施布设

| 概念 | 粒度 | 归属 |
|---|---|---|
| **措施** (`measure`) | 单项具体工程/植物/临时措施, 如"浆砌石挡墙" | `prevention.measures_layout[]` 中的单条记录 |
| **措施体系** | 本方案全部措施的集合及其分类组织 | `prevention.measures_layout[]` 整体的投影视图 |
| **措施布设** | 措施在分区内的空间/数量/时序安排 | `measures_layout[].zone_ref` + `quantity` + `schedule_ref` 联合表达 |

### 3.3 措施界定 (Ch3.7 核心概念)

**定义**: 对主体工程设计中已有的工程/设施, 判断其是否具有水土保持功能, 从而决定是否纳入水保措施体系。

**对象**: 主体工程设计文件中的具体工程项 (如"项目红线内 6 米宽沥青道路"、"1200m² 景观绿化带"、"沿红线 150m 浆砌石挡墙"等)。

**产出**: 一条 `measures.classification[]` 记录, 携带 verdict (纳入 / 不纳入 / 部分纳入) 与依据。

**流向**: verdict=纳入 或 部分纳入 时, 本条界定记录成为 `measures_layout[]` 中新增一条或多条措施记录的 **source provenance** (路径 A, 详见第五节)。

### 3.4 标准分区集 与 自定义分区扩展规则

**v0.6 核心五大标准分区类型** (城建 + 工业项目, 覆盖 v0 硬范围 29 房地产 + 30 其他城建):

| `zone_parent_type` | 中文名 | 典型含义 |
|---|---|---|
| `main_engineering` | 主体工程区 | 建筑物、构筑物及其附属设施占地 |
| `road_square` | 道路广场区 | 场内道路、硬化广场、停车场 |
| `landscape_greening` | 景观绿化区 | 绿地、花坛、渗透铺装等绿化工程 |
| `construction_living` | 施工生产生活区 | 施工营地、临时办公、材料堆场 |
| `temp_soil_stockpile` | 临时堆土区 | 临时表土堆存、土石方中转堆场 |

**扩展类型登记机制** (半枚举落地):

- 非上述五类的分区 (如弃渣场区、取土场区、输变电塔基区、光伏阵列区、管线带状区等) 属于**合法扩展类型**。
- 扩展类型必须在 `registries/PreventionZoneTypeRegistry_v0.yaml` 中预登记, 携带 `normative_basis_refs` (决议 8 双锚)。
- v0.6 阶段仅要求核心五类的完整登记; 扩展类型登记可随行业扩展逐步补齐, 但**未登记的扩展类型不得在项目 facts 中使用**。
- 自定义 label 与扩展类型分离: `zone_parent_type` 指向登记表, `zone_label` 为项目内显示名可自由命名。

### 3.5 stable_id 命名空间

| 对象 | 前缀 | 示例 |
|---|---|---|
| 分区记录 | `zone.` | `zone.main_engineering_01` / `zone.temp_stockpile_north` |
| 措施记录 | `measure.` | `measure.slope_masonry_wall_01` / `measure.grass_sowing_north` |
| 界定记录 | `cls.` | `cls.main_road_01` / `cls.landscape_green_belt_02` |

**命名纪律**: 所有 id 使用 snake_case, 不含显示章节号, 不含中文字符, 不含时间戳。违反者 lint ERROR。

---

## 四、防治分区层 (Ch7.4)

### 4.1 `field.fact.prevention.zones[]` schema

```yaml
field.fact.prevention.zones:
  semantic_type: list_of_records
  stable_id_namespace: zone.*
  record_schema:
    zone_id: string                       # stable_id, 必须 zone.<snake_case>
    zone_label: string                    # 项目内显示名, 可自定义 (如 "1# 临时堆土区")
    zone_parent_type: enum                # 闭集枚举, 见 3.4 核心五类 + PreventionZoneTypeRegistry
    description: string                   # 分区范围/特征的简要描述
    area_ha: number                       # 分区面积, 单位 hm²
    area_permanent_ha: number             # 其中永久占地面积, 可选
    area_temporary_ha: number             # 其中临时占地面积, 可选
    land_use_refs: [string]               # 引用 field.fact.land.* 中的占地类型 id, 声明依据关系不代表同构
    within_responsibility_range: bool     # 必须为 true, 否则 lint ERROR
    evidence_anchor_refs: [string]        # 决议 8 双锚
    normative_basis_refs: [string]        # 决议 8 双锚
    authored_by: string
    authored_at: string                   # ISO 日期
  protection_level: CRITICAL
  fact_class: F1_manual                   # 由设计院/水保编制方提供
  feeds_tables:
    - art.table.prevention_zones_summary      (Ch7.4 分区汇总表)
    - art.table.responsibility_range_by_admin_division (责任范围统计表, 作为面积来源之一)
    - art.spec_sheet                           (特性表分区面积栏)
  feeds_narrative:
    - sec.prevention.zones                    (Ch7.4 分区划分段)
    - sec.prevention.overall_layout            (Ch7.5 措施总体布局段引用分区名)
    - sec.prevention.zone_measures             (Ch7.7 分区措施布设段引用分区 id)
  feeds_figures:
    - art.figure.F_04_responsibility_range     (分区叠加责任范围)
    - art.figure.F_10_measures_layout          (措施按分区落图)
  feeds_obligation_evidence:
    - ob.ch7.zones_declared                   (若该 obligation 存在, 以 zones[] 作为 evidence)
```

### 4.2 `zone_parent_type` 核心枚举闭集

见 3.4 节表格。v0.6 阶段核心五类在本契约内就地闭集生效; 扩展类型登记在 `registries/PreventionZoneTypeRegistry_v0.yaml` 同步补齐, 未登记扩展类型一律 lint ERROR。

### 4.3 硬约束 (调整 3 落地)

以下约束为 v0.6 硬规则, 由 `cross_registry_lint.py` 新增校验规则 `PREVENTION_ZONE_001~004` 强制:

| 规则 | 约束 | 违反级别 |
|---|---|---|
| `PREVENTION_ZONE_001` | `∑ zones[].area_ha ≤ responsibility_range.total_area_ha` (允许小于, 超出视为数据错误) | ERROR |
| `PREVENTION_ZONE_002` | 每个 `zone` 必须 `within_responsibility_range == true` | ERROR |
| `PREVENTION_ZONE_003` | **非超界代数约束** (面积守恒替代约束): 若 `∑ zones[].area_ha > responsibility_range.total_area_ha`, 立即 ERROR。本规则是 v0.6 阶段对"分区不重叠"的**代数替代检查**, 非重叠本身的证明 (几何层重叠校验留 v1 GeoPipeline) | ERROR |
| `PREVENTION_ZONE_004` | 分区不得直接等同于占地类型: `zone_label` 与任一 `land.*` 分类名完全相同时 WARN, 除非 `description` 显式声明分区边界与占地边界重合的理由 | WARN |

**v0.6 几何重叠校验说明**: v0.6 无 GIS 能力, 本契约仅强制"分区面积之和不超出责任范围面积"这一**代数守恒替代约束** (`PREVENTION_ZONE_003`)。此约束不等价于"分区之间几何上不重叠"的证明 —— 只是在代数层堵住"加和超界"这一典型错误模式。分区之间的几何重叠校验属 GeoPipeline 扩展, 留 v1 落地。这条差距必须在 narrative 投影中以明示脚注声明, 不允许静默。

### 4.4 治理属性

- `protection_level`: **CRITICAL**。分区是 Ch7 全部 narrative 的骨架, 不得以任何方式绕过。
- `fact_class`: **F1_manual**。设计院/水保编制方提供; 不可由 calculator 派生, 不可由样稿反推。
- 全部字段走 FIR 登记, 携带 `lineage` 四子字段 (决议 4)。

---

## 五、措施布设层 (Ch7.5 + Ch7.7)

### 5.1 `field.fact.prevention.measures_layout[]` canonical schema

**这是本契约最核心的 schema**。两条流入路径 (路径 A 主体界定 / 路径 B 方案新增) 进入此 schema 后必须归一化为同一结构。

```yaml
field.fact.prevention.measures_layout:
  semantic_type: list_of_records
  stable_id_namespace: measure.*
  record_schema:
    measure_id: string                    # stable_id, 必须 measure.<snake_case>
    measure_name: string                  # 显示名, 如 "浆砌石挡墙"
    measure_type: enum                    # 三类闭集 (见 5.4): engineering / plant / temporary
    zone_refs: [string]                   # 关联 zone_id, 至少 1 个 (见红线 3)
    primary_zone_ref: string              # 若跨区, 必须声明主归属分区 (用于投资归口)
    source_attribution: enum              # existing_main_engineering / new_in_plan (两条路径归一化的来源)
    classification_ref: string            # 若 source_attribution=existing_main_engineering, 必填, 指向 cls.*
                                          # 若 source_attribution=new_in_plan, 可空
    specification: string                 # 规格/结构描述 (如 "M7.5 浆砌石, 宽 0.5m, 高 1.2m")
    quantity: number                      # 工程量数值
    unit: string                          # 单位 (m / m² / m³ / hm² / 株 / 处)
    quantity_source: string               # 工程量来源 (措施设计 / 类比估算 / 设计院提供)
    related_monitoring_refs: [string]     # 关联监测点/布设项 (若有), 不把监测本体并入 measures 域
    evidence_anchor_refs: [string]        # 决议 8 双锚
    normative_basis_refs: [string]        # 决议 8 双锚
    authored_by: string
    authored_at: string
  protection_level: CRITICAL
  fact_class: F1_manual                   # 措施名/类型/归属/工程量由设计院提供
                                          # (单价在 investment 侧, 属 F2)
  feeds_tables:
    - art.table.measures_layout_by_zone       (Ch7.7 分区措施布设表)
    - art.table.measures_overall_layout        (Ch7.5 措施体系表)
    - art.table.measures_quantity              (工程量汇总)
    - art.table.investment.* (投资估算附表 2/3/9, 作为投资视图消费源)
  feeds_narrative:
    - sec.prevention.overall_layout            (Ch7.5)
    - sec.prevention.zone_measures             (Ch7.7, 逐区展开)
    - sec.evaluation.measures_classification   (Ch3.7, 反向索引作为 cls 的结果视图)
  feeds_figures:
    - art.figure.F_10_measures_layout
```

### 5.2 SoT 边界声明 (D1 批示)

> `prevention.measures_layout[]` 是**纳入本方案水保体系的措施真源**, 不是**全主体工程措施宇宙真源**。

具体边界:

- 主体工程中**经 classification 认定为"不纳入"** 的措施, **不进入** `measures_layout[]`。它们仅作为 `classification[]` 的记录存在, 用于 Ch3.7 narrative 说明界定结果。
- 主体工程中未被界定的设施 (本方案未触及的部分), **不进入** `measures_layout[]`, 也不强制进入 `classification[]`。
- 方案新增的水保措施**直接进入** `measures_layout[]`, 无需先走 classification。
- 任何不在 `measures_layout[]` 中的措施, 不得出现在 Ch7.5 / Ch7.7 的 narrative、表格、投资附表中。

### 5.3 两条流入路径与归一化要求 (D + 两条路径批示落地)

```
路径 A (主体已列):
  主体工程设计文件
    → classification[] 一条记录 (verdict=included 或 partially_included)
    → measures_layout[] 一条或多条记录 (source_attribution=existing_main_engineering,
                                         classification_ref 必填)

路径 B (方案新增):
  水保方案设计
    → measures_layout[] 一条记录 (source_attribution=new_in_plan,
                                    classification_ref 可空)
```

**归一化硬规则**: 无论从哪条路径进入 `measures_layout[]`, 记录必须满足同一套 canonical schema (5.1)。`source_attribution` 与 `classification_ref` 字段是两条路径的**差异标记**, 不是结构分叉。

### 5.4 `measure_type` 闭集 (调整 4 落地: 去掉监测)

| `measure_type` | 中文名 | 投资归口 (对齐 INVESTMENT 契约五部分结构) |
|---|---|---|
| `engineering` | 工程措施 | 第一部分 工程措施 |
| `plant` | 植物措施 | 第二部分 植物措施 |
| `temporary` | 临时措施 | 第四部分 临时措施 |

**v0.6 不包含** `monitoring` 类。原因: 监测虽有章节/投资关联, 但**不属于 Ch7.5/7.7 防治措施布设的核心对象**。把监测塞进 `measure_type` 主枚举会污染本契约的领域边界。

**监测关联的替代路径**: 通过 `measures_layout[].related_monitoring_refs[]` 做**引用关联**, 监测本体仍归属监测子系统。v0.6 阶段该字段可全部为空; v0.7 监测 schema 落地时再正式接线。

**投资第三/五部分归口**:
- 第三部分 监测措施 → 不由 `measures_layout[]` 驱动, 由未来 monitoring 子系统驱动 (本契约不定义)
- 第五部分 独立费用 → 由 `investment.fee_rates` 派生 (INVESTMENT 契约已定)

### 5.5 跨区措施 (红线 3 落地)

若某措施跨越多个分区 (如沿责任范围边界的统一排水沟贯穿两个分区), 处理方式:

- `zone_refs[]` 登记全部涉及分区
- `primary_zone_ref` 必须声明**主归属分区** (用于投资归口时归到单一分区, 避免双计)
- 工程量按**主归属分区计一次**, 不得在跨区各分区分别登记
- narrative 中描述该措施时必须同时列出涉及分区

**禁止**: 通过"在 description 文本里说一下跨区"绕过 `zone_refs[]` 多值机制。

### 5.6 与 `investment.measures_registry` 的视图投影关系

| 方面 | 规定 |
|---|---|
| 真源归属 | `prevention.measures_layout[]` |
| 投资视图 | `investment.measures_registry` 降级为从真源投影的视图 (过渡期为兼容视图, 见 2.3) |
| 字段映射 | `measure_id` / `measure_name` / `measure_type` (→ `fee_category`) / `primary_zone_ref` (→ `prevention_zone`) / `source_attribution` 直接映射; 单价 / 造价合计由 investment 侧补 |
| 单价归属 | 单价字段**仍归 investment 侧** (F2 外部同步), 本契约不定义 |

---

## 六、措施界定层 (Ch3.7)

### 6.1 `field.fact.measures.classification[]` schema

```yaml
field.fact.measures.classification:
  semantic_type: list_of_records
  stable_id_namespace: cls.*
  record_schema:
    classification_id: string             # stable_id, 必须 cls.<snake_case>
    source_item_name: string              # 主体工程项名称, 如 "项目红线内 6m 宽沥青道路"
    source_item_type: string              # 主体工程项类型, 如 "道路 / 绿化 / 挡墙 / 排水 / 边坡防护"
    source_item_ref: string               # 若主体工程设计已结构化, 指向主体 id; 否则为空字符串
    verdict: enum                         # included / excluded / partially_included
    inclusion_reason: string              # verdict=included 时必填; 说明水保功能
    exclusion_reason: string              # verdict=excluded 时必填; 说明不纳入的专业判断
    partial_scope_note: string            # verdict=partially_included 时必填 (见 6.3 硬规则)
    expert_switch_basis:                  # 决议 6 governance_block 最小集
      source_rule_id: string              # 法规/标准条款
      human_decision_question: string     # 决策问题
      decision_owner_role: string         # 填写者角色 (通常 registered_wsc_engineer)
      default_value: null                 # 无默认, 必须专家判断
      evidence_expectation: string        # 期望证据 (如 "主体施工图 + 水保功能分析")
      replaced_normative_semantics:
        - rule_ref: string
          quoted_phrase: string
          why_not_calculable: string
      upgrade_path:
        strategy: irreducible             # 本字段永久不可计算化
        irreducibility_justification: string  # 必须引规范条款说明
      authored_by: string
      authored_at: string
    resulting_measure_refs: [string]      # 若 verdict=included 或 partially_included, 指向 measures_layout[].measure_id
    evidence_anchor_refs: [string]        # 决议 8 双锚
    normative_basis_refs: [string]        # 决议 8 双锚
  protection_level: PROTECTED
  fact_class: F1_manual                   # 专家认定, 不可派生
  feeds_tables:
    - art.table.measures_classification         (Ch3.7 措施界定表)
  feeds_narrative:
    - sec.evaluation.measures_classification    (Ch3.7 界定叙述)
```

### 6.2 `verdict` 三态闭集

| `verdict` | 语义 | 对 measures_layout 的作用 |
|---|---|---|
| `included` | 完全纳入本方案水保体系 | 产生一条或多条 measures_layout 记录 (source_attribution=existing_main_engineering) |
| `excluded` | 不具备水保功能, 不纳入 | 仅在 classification[] 留痕, 不进 measures_layout |
| `partially_included` | 部分具备水保功能 / 仅部分纳入 | 产生对应范围的 measures_layout 记录, 必须有范围界定 (见 6.3) |

### 6.3 "部分纳入" 硬规则 (调整 5 落地)

**`partially_included` 的使用治理**:

1. **可拆则拆**: 能拆分为"完全纳入部分"+"不纳入部分" 两条 classification 记录的, **必须拆分**, 不得使用 `partially_included` 逃避。
2. **不可拆才允许**: 仅在界定客体不可再拆 (如同一构筑物同时承担多重功能, 分拆会破坏工程完整性) 且专家明确判断确有必要时, 允许 `partially_included`。
3. **强制补字段**: 使用 `partially_included` 时, 以下字段必须全部非空, 否则 lint ERROR:
   - `partial_scope_note` (部分纳入的具体范围/比例/方式的文字说明)
   - `expert_switch_basis` (完整 governance_block, 说明为何不可拆)
   - `source_rule_id` (界定依据的具体条款)
4. **lint 规则 `CLASSIFICATION_PARTIAL_001`**: 扫描所有 verdict=partially_included 的记录, 检查上述三字段完整性; 缺任一为 ERROR。

**治理目标**: 防止 `partially_included` 变成审查灰区的兜底垃圾桶。v0.6 上线时需对真实样本项目的 classification 做 `partially_included` 占比**健康度观察**, 异常集中时触发架构层复核。具体观察阈值不写入正式契约条文, 放入实施期 review checklist 作为经验指标, 待数据积累后再决定是否提升为强制规则。

### 6.4 `expert_switch_basis` (决议 6 落地)

每条 classification 记录的 `verdict` 字段是典型的 expert-switch bool (三态版本), 因此必须携带完整 `governance_block`。

**`upgrade_path.strategy` 锁定为 `irreducible`**: 措施界定本质上是对规范文字 (如 GB 50433-2018 相关条款中的"具有水土保持功能") 的专家解读, 无法被算法化。v0.6 及之后版本永不接 calculator。`irreducibility_justification` 必须显式引用规范条款。

### 6.5 数据流向

```
(Ch3.7 评价域)                       (Ch7 防治域)                   (其他消费)
主体工程项                            measures_layout[]              investment 视图
   │                                    ▲                              ▲
   ▼                                    │                              │
measures.classification[]               │                              │
   ├─ verdict=included      ────────────┘ (source_attribution=
   │                                        existing_main_engineering,
   │                                        classification_ref 指向本记录)
   ├─ verdict=partially_included ───────┘ (同上 + partial_scope_note)
   └─ verdict=excluded                   (仅在 Ch3.7 叙述中出现)
```

---

## 七、与 Obligation 的挂钩点

**本契约不新增 obligation** (决议 2)。已有 obligation 中对 Ch7 防治义务、Ch3 评价义务的条目, 在 v0.6 配合本契约时, 必须将 `evidence_anchor_refs` 指向本契约字段:

| obligation 语义 | 建议挂接 evidence |
|---|---|
| 防治分区完整声明义务 | `field.fact.prevention.zones[*]` |
| 分区面积与责任范围一致性义务 | `field.fact.prevention.zones[*].area_ha` + `field.fact.land.*.total_area` |
| 措施体系完整性义务 | `field.fact.prevention.measures_layout[*]` |
| 主体措施水保功能界定义务 | `field.fact.measures.classification[*]` |
| 主体已列/方案新增标注义务 | `field.fact.prevention.measures_layout[*].source_attribution` |

**本契约不规定上述 obligation 的具体 id 与触发条件**, 由 `ObligationSet_v0.yaml` 维护。若在 v0.6 实施过程中发现已有 obligation 与上述语义缺口, 按决议 2 走 obligation 扩展 RFC, 不在本契约内处理。

---

## 八、与 Artifact 的投影清单

### 8.1 本契约新增 Artifact (需登记到 ArtifactRegistry_v0.yaml)

| artifact_id | 名称 | 类型 | v0_status | 数据来源 |
|---|---|---|---|---|
| `art.table.prevention_zones_summary` | 防治分区汇总表 | 表 | CAN_GENERATE | `prevention.zones[]` |
| `art.table.measures_overall_layout` | 措施总体布局表 | 表 | CAN_GENERATE | `prevention.measures_layout[]` |
| `art.table.measures_layout_by_zone` | 分区措施布设表 | 表 | CAN_GENERATE | `prevention.measures_layout[]` + `prevention.zones[]` |
| `art.table.measures_classification` | 水保功能措施界定表 | 表 | CAN_GENERATE | `measures.classification[]` |

### 8.2 本契约重用/关联的现有 Artifact

| artifact_id | 与本契约关系 |
|---|---|
| `art.figure.F_04_responsibility_range` | 分区叠加责任范围, 依赖 `prevention.zones[]` |
| `art.figure.F_10_measures_layout` | 措施按分区落图, 依赖 `prevention.zones[]` + `prevention.measures_layout[]` |
| `art.table.investment.*` (附表 2/3/9) | 作为投资视图消费 `prevention.measures_layout[]` |
| `art.spec_sheet` | 特性表中的分区面积/措施摘要字段, 作为投影消费 |

### 8.3 v0.6 artifact 产出目标

v0.6 阶段本契约对应的 4 张新表从 CAN_GENERATE 推进到 LIVE。F-10 措施布置图仍为 ENGINE_STUB (依赖 GeoPipeline), 但其数据依赖已通过本契约就绪; v1 GeoPipeline 启动时直接接入。

---

## 九、与 Narrative 的投影清单

### 9.1 narrative node 登记清单

| narrative_node_id | 章节 | projection_source_refs |
|---|---|---|
| `sec.evaluation.measures_classification` | 3.7 | `measures.classification[*]` |
| `sec.prevention.zones` | 7.4 | `prevention.zones[*]` + `land.*` (面积校验) + `responsibility_range.total_area` |
| `sec.prevention.overall_layout` | 7.5 | `prevention.measures_layout[*]` + `prevention.zones[*]` |
| `sec.prevention.zone_measures` | 7.7 | `prevention.measures_layout[*]` by zone |

### 9.2 决议 4 硬绑定 (再钉一次, 与第十节跨层校验呼应)

- 上述每个 narrative node 在模板文件中**禁止**出现任何字面量的分区名、分区面积、措施名、工程量、数量单位。
- 所有数值必须走 projection 读取; 所有文字必须引用 projection 返回的 canonical 表达。
- lint 规则 `NARRATIVE_HARDCODE_001` (已存在) 的扫描范围扩展到本契约相关模板文件。

---

## 十、空值规则与跨层一致性校验

### 10.1 三态语义在本契约的具体含义 (对齐 INVESTMENT 契约第七节)

| 显示 | 本契约适用场景 |
|---|---|
| `—` | 分区面积未提供 / 工程量未提供 / 界定未完成 |
| `0` (或 `0.00`) | 明确为零 (如某分区临时面积确实为 0, 但该分区存在) |
| `/` | 该项目不适用 (如无临时堆土区的项目, 该分区类型整体不出现) |

**禁令**:
- 不允许用 `0` 代替 `—` (混淆"已确认为零"与"数据未提供")
- 不允许用 `—` 代替 `/` (混淆"数据缺失"与"项目不适用")
- 不允许在分区整体不存在时仍用空记录填充 zones[] (应直接不收录该分区)

### 10.2 跨层一致性校验 (调整 6 落地)

**v0.6 强制校验规则** (`cross_registry_lint.py` 新增):

| 规则 id | 约束 | 级别 |
|---|---|---|
| `PREVENTION_XLAYER_001` | 每条 `measures_layout[]` 中 `source_attribution=existing_main_engineering` 的记录, 必须满足 (a) `classification_ref` 非空且能解析到 `classification[]` 一条记录; 或 (b) 显式声明 `bypass_classification_reason` 且取值在闭集豁免枚举内 (见 10.2.1) 且 `evidence_anchor_refs[]` 非空且至少一项指向官方批复/正式设计文件 | ERROR |
| `PREVENTION_XLAYER_002` | 每条 `classification[]` 中 `verdict=included` 或 `partially_included` 的记录, 必须有至少一条 `measures_layout[]` 通过 `classification_ref` 反向关联到本条; 否则为孤立界定, WARN (允许界定先行、布设暂缓, 但需显式注明) | WARN |
| `PREVENTION_XLAYER_003` | narrative 模板中出现的分区名称, 必须在 `zones[].zone_label` 中找到对应 (字符串归一化后比对); 措施名称同理 | ERROR |
| `PREVENTION_XLAYER_004` | `measures_layout[].zone_refs[]` 中引用的每个 zone_id, 必须能在 `zones[]` 中解析到 | ERROR |
| `PREVENTION_XLAYER_005` | `measures_layout[].primary_zone_ref` 必须是 `zone_refs[]` 的成员 | ERROR |

**v0.6 不含** (留 v1):
- narrative 文本中数字类 token 的归一化比对 (决议 7 overlay 配套规则, v1 落地)
- 几何层面的分区重叠校验 (GeoPipeline 扩展)

#### 10.2.1 `bypass_classification_reason` 闭集豁免枚举

为防止掏空 Ch3.7 的界定链条, `PREVENTION_XLAYER_001` 的 (b) 分支所依据的 `bypass_classification_reason` 不是自由文本, 而是**闭集枚举**:

| 豁免枚举值 | 适用场景 | 证据挂接硬要求 |
|---|---|---|
| `approved_prior_soil_conservation_scheme` | 本措施来源于本项目**已获批**的前一版水土保持方案, 且本次申报未修改其水保功能归属 | `evidence_anchor_refs[]` 必须含前方案的**官方批复文件** id (如 `art.attachment.AF_1_project_approval` 的对应条目) |
| `formally_designed_and_unchanged` | 措施已在主体工程**正式设计文件**(施工图或更高阶段)中完成水保功能认定, 且本次申报不改变其水保功能归属 | `evidence_anchor_refs[]` 必须含**正式设计文件** id, 文件必须具备设计单位署名、版本号、出图时间三要素 |
| `upstream_regulatory_conclusion` | 上位主管部门 (省级或以上) 对该类措施已作出**普适性功能认定**, 本项目直接适用 | `evidence_anchor_refs[]` 必须含上位认定文件 id, 且该文件的 `authority_class ∈ {regulation, official_approval, authoritative_guide}` (决议 8) |

**硬禁令**:

1. `bypass_classification_reason` 必须取上表三值之一, **不接受自由文本**, 不接受"待补充""情况说明见 description"等兜底写法。lint 规则 `PREVENTION_XLAYER_001B` 扫描 bypass 分支的取值合法性, 非闭集值为 ERROR。
2. `evidence_anchor_refs[]` 必须**非空**, 且至少一项指向与豁免枚举值相匹配的证据类别。匹配关系按上表硬绑定 (如 `formally_designed_and_unchanged` 要求指向正式设计文件而非官方批复)。
3. bypass 本身是**路径 A 的证据前置**, 不是**路径 A 的替代**。即使走 bypass 豁免, 该措施在项目证据链上仍归属于"主体已列 → 已有功能认定"路径, narrative 与审查 workbench 不得将其呈现为"方案新增"或"未界定"。
4. 同一项目内 bypass 使用占比在实施期作为健康度观察指标 (与 6.3 `partially_included` 同级别), 异常集中时触发架构层复核。具体阈值不写入契约。

**治理目标**: 允许界定链条在项目已有正式批复/正式设计时合理省略重复工作, 但禁止通过模糊理由绕过界定。

### 10.3 四条红线 (最终批示的独立条款)

**红线 1: zone 不允许从样稿抄录 (决议 8 sample_usage_mode 落地)**

分区设置必须基于本项目责任范围、占地结构、主体工程布置的实际情况独立判断得出。**禁止**将样稿项目的分区配置 (含分区类型组合、面积比例、命名) 作为本项目分区的直接来源。违反视同 decision 8 的 sample_usage_mode=authority 违规, 按硬禁令处理。v0.6 lint 规则 `PROV_ZONE_001` 扫描分区 `evidence_anchor_refs[]`, 若全部指向样稿相关资源, ERROR。

**红线 2: zone 与 measure 必须有 stable_id**

每一条 `zones[]` 记录必须有 `zone_id` (`zone.*`), 每一条 `measures_layout[]` 记录必须有 `measure_id` (`measure.*`), 每一条 `classification[]` 记录必须有 `classification_id` (`cls.*`)。**禁止**以 (zone_label, zone_parent_type) 或 (measure_name, measure_type) 等元组组合作为主键。lint 规则 `STABLE_ID_001` 扫描全部三类记录, 缺 id 为 ERROR。

**红线 3: measure 不得脱离 zone 单独存在**

`measures_layout[].zone_refs[]` 必须非空, 至少一个 zone_id。跨区措施必须声明全部涉及分区并指定 `primary_zone_ref`, **禁止**用"description 文本里写一下跨区"绕过结构。lint 规则 `PREVENTION_MEASURE_001` 扫描 measures_layout, zone_refs 为空者 ERROR。

**红线 4: classification 不等于 measures_layout**

两者是**分层独立对象**, 必须分属不同 registry 与不同章节投影。**禁止**将两者合并为单一记录结构 (即使看似可以"一条记录同时承担界定与布设")。这条红线保证 Ch3.7 (评价) 与 Ch7 (防治) 的语义分离不被腐蚀。违反属于架构回滚事件, 按反升级条款处理。

---

## 十一、v0.6 → v0.7 迁移路径

### 11.1 v0.6 本契约交付范围

| 交付项 | 状态 |
|---|---|
| 本契约文档 | v0.6 Planning Baseline (本次落地) |
| FieldIdentityRegistry 新增三组字段登记 | 待实施 (契约生效后) |
| `registries/PreventionZoneTypeRegistry_v0.yaml` 核心五类 + 扩展登记框架 | 待实施 |
| 4 张新表 (8.1) 从 CAN_GENERATE → LIVE | 待实施 |
| 4 个 narrative node (9.1) 投影实现 | 待实施 |
| lint 规则 PREVENTION_ZONE_001~004 + PREVENTION_XLAYER_001~005 + PREVENTION_MEASURE_001 + CLASSIFICATION_PARTIAL_001 + PROV_ZONE_001 + STABLE_ID_001 | 待实施 |
| INVESTMENT_FACTS_BACKFILL_CONTRACT 对齐修订 (见 2.3) | 独立步骤, 本契约写完后启动 |
| 4 个现有样本 facts 按本契约回填 | 独立步骤, 契约与 registry 就绪后启动 |

### 11.2 v0.7 预埋槽位

| 预埋项 | 文件 | 状态 |
|---|---|---|
| `cal.prevention.measure_recommender` | `specs/v1_reservations/*_v1_reserved.yaml` | 仅预埋, v0.6 不执行 |
| 监测与措施关联的正式 schema | 预埋在 `measures_layout[].related_monitoring_refs[]` 字段 | 字段存在, 值 v0.6 为空 |
| 几何重叠校验 (GeoPipeline 联动) | 规则骨架 | 规则占位, 不进 v0.6 执行序列 |
| 报告表 Grammar 下的分区简化表达 | — | 不处理, v1 以后 |

### 11.3 迁移门禁

从 v0.6 推进到 v0.7 的前置条件:

1. 所有 v0.6 交付项 LIVE
2. 4 个样本在本契约生效后零 ERROR, WARN ≤ 5
3. `INVESTMENT_FACTS_BACKFILL_CONTRACT` 完成对齐修订, `investment.measures_registry` 完成降级为视图
4. 架构状态文档 (`project_architecture_state.md`) + v0 freeze feedback 更新到位

---

## 十二、变更记录

| 日期 | 版本 | 变更 | 责任人 |
|---|---|---|---|
| 2026-04-21 | v0.6 Planning Baseline | 初版: 防治体系三真源 (zones / measures_layout / classification) + 12 节骨架 + 跨层校验 + 四红线 | 架构决策 (含 6 处骨架修正 + D1-D4 批示 + 两条 measures 流入路径归一化) |
| 2026-04-21 | v0.6 Planning Baseline (终审修订) | 三处定点修订: (1) `PREVENTION_ZONE_003` 改名并明确为"非超界代数约束 / 面积守恒替代约束", 不再以"不重叠声明"描述; (2) §六 6.3 移除 15% 经验阈值具体数值, 降级为实施期 review checklist 观察指标; (3) §十 新增 10.2.1 `bypass_classification_reason` 闭集豁免枚举 (三值) + `evidence_anchor_refs` 非空 + 证据类别硬绑定 + lint 规则 `PREVENTION_XLAYER_001B` | 终审批示 |
