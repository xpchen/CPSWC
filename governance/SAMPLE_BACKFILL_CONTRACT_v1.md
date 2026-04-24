# Sample Backfill Contract (v1 样本回填契约)

> **文档性质**: 准制度文件。定义 CPSWC 仓库内样本 (合成样本 + 真实项目样本) 的事实层回填纪律、来源优先级、反作弊规则与验收标准。
> **上游依据**:
> - `governance/ARCHITECTURE_DECISIONS.md` (反升级条款 / 决议 8 source_provenance)
> - `governance/PREVENTION_SYSTEM_CONTRACT.md` (PreventionSystem 三真源 + 四红线)
> - `governance/INVESTMENT_FACTS_BACKFILL_CONTRACT.md` (投资侧消费视图与兼容期)
> - `registries/PreventionZoneTypeRegistry_v0.yaml` (核心五类 + Step 52-0 RFC 激活的 spoil_disposal)
> **下游约束对象**: `samples/*.json` 的 facts 部分、`fixtures/` 构造脚本、未来新样本引入流程
> **版本**: 2026-04-24 (v1 · Step 52-A1)
>
> **核心目标**: 回答"样本 facts 从哪里来, 不能从哪里来, 怎样算合格"

---

## 一、目标与适用范围

本契约规范 CPSWC 仓库内**所有 v0 样本**在进行事实层回填时必须遵循的治理纪律。回填动作包括:

- 新增样本时的 facts 构造
- 既有样本扩展新字段时的事实补齐 (如 Step 52-A2 的 PreventionSystem 三字段)
- 样本事实的阶段性审计复核

**本契约覆盖**:

| 样本类型 | 代表 | 回填策略 |
|---|---|---|
| 合成样本 | `huizhou_housing_v0` / `disposal_highrisk_v0` | 从已有 facts 推导最小合法骨架 |
| 真实项目样本 | `huinan_zhigu_v0` / `shiwei_logistics_v0` | 优先 structured facts, PDF 仅作人工核验来源备注 |

**本契约不覆盖** (明确划出):

- 样本字段**契约**本身 (字段定义归 `FieldIdentityRegistry_v0.yaml` + 对应 governance 契约)
- 样本渲染 (TABLE_PROJECTIONS / narrative templates)
- intake/validator 运行时的样本实例业务校验
- PDF 自动抽取 (本契约明确**不引入**, 见 §三)
- 前端录入 UI

---

## 二、样本回填来源优先级 (Source Priority)

任何字段回填必须按以下优先级取值, **不得逆序**, **不得跨级跳接**:

```
优先级 1  既有 structured facts          (FIR 已登记, 字段已存在)
优先级 2  investment.measures_registry / other 已存在的 registry 视图
优先级 3  已有契约文档列举的标准条目      (如 PreventionZoneTypeRegistry 核心五类)
优先级 4  manually curated sample intent (合成样本设计意图)
优先级 5  真实样本 PDF 的人工核验        (仅 real samples, 仅 source 备注, 不自动抽)
```

**硬禁令**:

- 任何回填不得为优先级 5 以下来源 (如"网络搜索""样稿抄袭""LLM 生成")
- 优先级 5 不得跳过优先级 1~4 直接使用
- 合成样本**禁止**使用优先级 5 (合成样本不接入 PDF 来源)

---

## 三、反作弊规则 (Anti-Cheating Rules)

### 3.1 非空实质回填

消除 CRITICAL 字段的 export gate BLOCK **必须**通过非空、可解释的实质回填。

**禁止的作弊模式**:

| 作弊模式 | 禁令级别 |
|---|---|
| 空 list `[]` 填充 CRITICAL list_of_records | **ERROR** |
| 空对象 `{}` / `null` 填充必填字段 | **ERROR** |
| 占位字符串 `"TBD"` / `"待补"` / `"N/A"` | **ERROR** |
| 占位数字 `0` 代替实际量 (混淆"已确认为零"与"未提供") | **ERROR** |
| 为降低回填工作量而压缩事实粒度 (如将多个分区合并为一个"项目区") | **WARN** (合成样本) / **ERROR** (真实样本) |

### 3.2 来源可解释性

每一条 list_of_records 回填记录, 在其 `evidence_anchor_refs` 或等价注释中, 必须能回答:

```
Q: 这条记录的依据是什么?
A: [优先级 1~5] + 具体引用 (facts 字段 / registry 条目 / 契约章节 / 样本设计意图 / PDF 页码)
```

无法回答视同作弊, 回滚重填。

### 3.3 禁用 `partially_included` 作为兜底

`verdict=partially_included` 是契约 §6.3 的逃生舱, **不是**回填装饰。禁止为"展示复杂性"或"降低 verdict=included 的置信度"而使用。触发条件见 `PREVENTION_SYSTEM_CONTRACT.md` §6.3。

---

## 四、合成样本回填规则

### 4.1 设计意图边界

合成样本的**唯一目标**是覆盖规则路径, 不是复刻真实报告。回填时必须保持:

1. **可解释来源**: 每个 zone / measure / classification 能追溯到已有样本事实或明确声明的样本设计意图
2. **不新增规范性结论**: 回填不得改变补偿费 / 六率目标 / 投资合计 等既有计算结果
3. **不引入高风险伪义务**: 不能因为回填而让样本触发本不应该触发的 obligation (如合成低风险样本不得因回填而让 `failure_analysis_required` 翻转为 true)

### 4.2 最小数量下限

| 字段 | 合成样本最低条数 |
|---|---|
| `field.fact.prevention.zones` | ≥ 2 |
| `field.fact.prevention.measures_layout` | ≥ 2 |
| `field.fact.measures.classification` | **等于** `source_attribution=existing_main_engineering` 的 measures_layout 条数 |

### 4.3 `huizhou_housing_v0` 特定规则 (低风险城建)

- 至少包含 3 个 core zone:
  - `main_engineering` (主体工程区)
  - `construction_living` (施工生产生活区)
  - `landscape_greening` (景观绿化区)
- 措施以 `engineering` + `plant` + `temporary` 三类覆盖为佳, 单条不合格
- 补偿费必须保持 `5.7 万元` 不变 (通过不动 `land.*` 与 `compensation_fee_rate` 保证)

### 4.4 `disposal_highrisk_v0` 特定规则 (高风险弃渣场)

- **必须**包含 `spoil_disposal` 分区 (Step 52-0 RFC 已激活, 详见 `PreventionZoneTypeRegistry_v0.yaml`)
- 至少包含 3 个 zone:
  - `main_engineering`
  - `construction_living`
  - `spoil_disposal` (弃渣场区)
- `spoil_disposal` zone 必须能引用或追溯到 `field.fact.disposal_site.*` facts
- 补偿费必须保持 `27.0 万元` 不变

---

## 五、真实项目样本回填规则

### 5.1 来源铁律

真实样本 (`huinan_zhigu_v0` / `shiwei_logistics_v0`) **优先使用已有 structured facts**, 不足部分通过**人工核验** PDF 后在 `evidence_anchor_refs` 中标注来源, 不进入自动抽取管线。

PDF 作为来源的标注约定:

```yaml
evidence_anchor_refs:
  - source_ref: sample_report_pdf
    note: "p.42 分区表 / 人工核验 2026-04-24"
  - source_ref: manually_verified
    note: "根据土地租赁合同补齐临时占地分区"
```

### 5.2 PDF 抽取边界

- 本契约明确**不引入** PDF 自动抽取工程 (页码/表格/OCR/置信度等)
- 允许使用 `ops_pdftotext_targeted_extraction.md` 记录的定向取材流程 (pdftotext → grep → Read offset) 做**人工提取**, 结果作为人工核验依据
- 人工提取过程不自动化, 不纳入 CI, 不进入任何 loader

### 5.3 数量下限

真实样本按项目设计/PDF 实际分区数回填, 通常 3~5 个 zone。**禁止**为满足契约最小数量硬造 zone 或 measure; 也**禁止**为省事合并不同性质分区。

### 5.4 补偿费 / 六率不变原则

真实样本回填后, 以下计算结果必须与 Step 51 前一致 (见 `project_architecture_state.md` 4 样本表):

| 样本 | 补偿费 |
|---|---|
| huinan_zhigu_v0 | 0.468 万元 |
| shiwei_logistics_v0 | 4.248 万元 |

如果回填引发上述数值变动, 视为**回填副作用泄漏**, 必须回滚排查。

---

## 六、PreventionSystem 字段回填规则

承接 `PREVENTION_SYSTEM_CONTRACT.md` v0.6 Planning Baseline 的三真源声明。

### 6.1 `field.fact.prevention.zones[]`

- 每条 record 必须有合法 `zone_id` (`zone.*` snake_case) — 契约红线 2
- `zone_parent_type` 必须能在 `PreventionZoneTypeRegistry_v0.yaml` 的 `zone_types[]` 中解析到
  (`tier=core` 或已激活的 `tier=extended`)
- `within_responsibility_range` 必须为 `true` — 契约 §4.3 `PREVENTION_ZONE_002`
- `∑ zones[].area_ha ≤ responsibility_range.total_area_ha` — 契约 §4.3 `PREVENTION_ZONE_001` + `_003` 代数守恒
- 分区不得从样稿抄录 — 契约 §十 红线 1 + `PROV_ZONE_001`
- `evidence_anchor_refs[]` 每条至少一个非样稿来源

### 6.2 `field.fact.prevention.measures_layout[]`

- 每条 record 必须有合法 `measure_id` (`measure.*` snake_case) — 契约红线 2
- `zone_refs[]` 非空且每项能在 `zones[]` 解析 — 契约红线 3 + `PREVENTION_MEASURE_001`
- 跨区措施必须声明 `primary_zone_ref`, 且 `primary_zone_ref ∈ zone_refs` — 契约 §5.5 + `PREVENTION_XLAYER_005`
- `measure_type ∈ {engineering, plant, temporary}` — 契约 §5.4 (v0.6 不含 `monitoring`)

### 6.3 `field.fact.measures.classification[]` — Classification Boundary (**本契约核心**)

承接 `PREVENTION_SYSTEM_CONTRACT.md` §5.1 / §6.1 / §6.2 原版语义:

```
source_attribution = existing_main_engineering:
  - classification_ref 必填
  - 必须存在对应 classification record
  - 该 record 的 verdict ∈ {included, excluded, partially_included}
  - 无明确 excluded / partially_included 证据时, 默认 verdict=included
  - expert_switch_basis 必须完整 (9 键 governance_block)

source_attribution = new_in_plan:
  - classification_ref 可空
  - **不强制**生成 classification record
  - measures_layout 仅通过 source_attribution=new_in_plan 声明来源
  - 不得套用 verdict=included 默认 (会腐蚀 §6.2 三态闭集与红线 4 分层)
```

**禁止**为了"每条 measures_layout 都有 classification"硬造 `new_in_plan` 的 classification record。

### 6.4 `disposal_highrisk_v0` 专属规则 — SoT 边界

- `spoil_disposal` zone 已由 **Step 52-0 RFC** 正式激活 (见 `PreventionZoneTypeRegistry_v0.yaml` changelog)
- `field.fact.disposal_site.*` 仍是弃渣场专业事实的**唯一 SoT** (堆渣量 / 最大堆高 / 下游危害等级 / 评定级别)
- `prevention.zones` 内的 `spoil_disposal` 仅作防治分区投影, **不得复制**弃渣场专业事实字段
- 需要关联时通过事实 ID 引用, 不通过值复制

---

## 七、关联字段使用 (不新增, 用契约既有双向关联)

- classification → measures_layout: `resulting_measure_refs: [string]` (契约 §6.1)
- measures_layout → classification: `classification_ref: string` (契约 §5.1)

**禁止新增**: `measure_id` / `measure_ref` / `related_measure_ref` 等别名字段。`classification_id` 只作 classification record 主键, **不得**作为 measure 关联字段使用。

---

## 八、引用完整性要求

以下硬约束在本契约中写入, **lint 规则实现留 Step 52-C**:

| 约束 | 约束文本 | 违反级别 |
|---|---|---|
| REF_INTEGRITY_001 | 所有 `measures_layout.classification_ref` 必须能解析到 `measures.classification[].classification_id` | ERROR |
| REF_INTEGRITY_002 | 所有 `measures_layout.zone_refs[]` 中的每个 zone_id 必须能在 `prevention.zones[]` 解析 | ERROR |
| REF_INTEGRITY_003 | 每条 `classification` 若 `resulting_measure_refs[]` 非空, 每项必须能在 `measures_layout[]` 解析 | ERROR |

本节规则**当前不强制 lint**, 由回填者在 commit 前自行人工校核。lint 规则在 Step 52-C 统一落地。

---

## 九、验收标准 (Acceptance Criteria)

样本回填的合格判定:

1. **回归基线保持**:
   - `lint` ERROR=0 WARN=0 PENDING=0
   - `validator` ALL SAMPLES GREEN
   - `pytest` 64 passed (或更多, 不得减少)

2. **运行时结果不变**:
   - 4 样本 3 calculator 输出与回填前完全一致
     (补偿费 5.7 / 27.0 / 0.468 / 4.248 万元, 六率与弃渣场级别同)
   - package_builder 仍能产出完整 submission package

3. **export gate 收口**:
   - `prevention.zones` 与 `prevention.measures_layout` 的 `CRITICAL 字段缺失` BLOCK 必须**消除**
   - 不得通过 §三 3.1 禁止的作弊模式消除

4. **引用完整性人工校核**:
   - §八 三条约束在回填结果上自检通过
   - 不通过视同回填失败, 必须回滚

---

## 十、Non-goals (本契约不做的事)

为防止契约失控, 明确列出 Step 52-A 阶段**不做**的动作:

| 不做的事 | 归属 |
|---|---|
| PDF 自动抽取 / OCR / 表格识别 | 非本契约范围, v0 阶段永不做 |
| TABLE_PROJECTIONS 投影实现 (§8.1 四张表) | Step 52-B |
| narrative template 新投影实现 (sec.prevention.* 等) | 后续独立 Step |
| `investment.measures_registry` 代码层降级视图 | v0.7 Phase 1 |
| 跨层 lint 规则实现 (PREVENTION_ZONE_001~004 / XLAYER_001~005+001B / MEASURE_001 / CLASSIFICATION_PARTIAL_001 / PROV_ZONE_001 / STABLE_ID_001 / REF_INTEGRITY_001~003) | Step 52-C |
| 行业扩展 (borrow_pit / linear_transmission / pv_array 等) | 独立 RFC, 非 Step 52 范围 |
| 前端录入 UI / 产品薄层 | `project_product_readiness_assessment.md` Gate 3 |
| 客户真实项目验证 | 项目级动作, 非本契约范围 |

---

## 十一、变更记录

| 日期 | 版本 | 变更 | 责任人 |
|---|---|---|---|
| 2026-04-24 | v1 (Step 52-A1) | 初版: 样本回填跨子系统治理契约; 含来源优先级五级 / 反作弊三条 / 合成+真实样本分治 / PreventionSystem 三字段回填规则 / classification 覆盖边界 (existing_main_engineering 必填 + new_in_plan 可空) / disposal_highrisk spoil_disposal SoT 边界 / 引用完整性三条 (lint 留 Step 52-C) / 验收四条 / Non-goals 八条. | Step 52-A1 |
