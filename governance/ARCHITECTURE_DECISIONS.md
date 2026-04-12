# CPSWC 架构决议

**项目**：生产建设项目水土保持方案智能编制与审查平台（CPSWC）
**文件编号**：CPSWC-ARCHDEC-v0
**生效日期**：2026-04-11
**收敛来源**：2026 模板细读 + 三轮架构争论

本文件是 CPSWC 的架构宪法。任何违反本文件的工程决策都必须先更新本文件，否则代码不得合入。本文件写完后进入"逐条审阅 + 改字眼"模式，不再做结构性发散。

---

## 零、架构前提

本节不是决议，但所有决议都运作在这两个前提之上。

### 前提 A. 四层真源边界

CPSWC 内部的真源（source of truth）划分为四层，每层保护语义不同：

| 层 | 内容 | 编辑路径 | 保护规则 |
|---|---|---|---|
| **Fact** | 面积、土石方、级别、时点、坐标、证据锚等 | 仅走表单或上传 | 不允许由正文渲染反向修改 |
| **Obligation** | 义务集（必写/必算/必附/必监/必承诺/必签章） | 由规则引擎生成 | 导出时强制 gate，不可绕过 |
| **Narrative** | 正文章节与段落 | 受控生成 + 受控 override | 在 slot 框架内允许润色，override 须追踪依赖 |
| **Artifact** | 表、图、附件、专题册、交付包 | registry 驱动 | 不允许手工塞入未登记制品 |

四层之间有严格的方向：Fact → Obligation → (Narrative, Artifact)。反向依赖被禁止。

### 前提 B. 三轴分派

CPSWC 的文档生成由三个正交轴共同决定，任一轴不得被其余轴吸收：

- **Species**（法律物种）：报告书 / 报告表 / 整体变更报告书 / 弃渣场补充报告书。承载 obligation 触发。
- **Grammar**（渲染语法）：NarrativeBook / MatrixForm / FocusedSubreport / DeliveryBundle。承载 renderer 选择。
- **SubmissionContext**（申报上下文）：分为静态的 `SubmissionProfile` 与动态的 `SubmissionLifecycle`。前者承载 obligation 输入，后者承载 gate 输入。

核心计算边界：

```
ObligationSet = f(ProjectSemanticGraph, SubmissionProfile)
ExportGate    = g(ObligationSet, AssuranceState, SubmissionLifecycle)
```

Lifecycle（stage / review_round / freeze_state）**不进入** ObligationSet 的输入，仅作用于 gate。这条边界防止 review 轮次换代导致 obligation 整张重算。

---

## 一、5 条硬决议

### 决议 1. 特性表是法定主投影，不是唯一语义根

2026 模板附件 1 表 1《水土保持方案特性表》是报告书的法定汇总表，但它承不住分期设计水平年、已扰动时点快照、表土链条、承诺书状态、监测视频义务、责任页签章等对象。

**规则**：特性表是 `SpecSheetProjection`，与 `ReportFormProjection` / `NarrativeProjection` / `ArtifactProjection` 并列，共同从 `ProjectSemanticGraph` 派生。系统内任何组件不得以特性表为根对象实现。

### 决议 2. 规则引擎输出 Obligation，不输出章节可见性

`ConditionEngine` 的输出是 `ObligationSet`（v0） / `ObligationGraph`（v1），不得直接输出章节可见性、字段可见性或附图列表。章节可见性、附图生成清单、附件要求均为 obligation 的派生投影。

**规则**：每条 obligation 在 v0 即必须携带以下字段，为 v1 升级预留接口：
- `obligation_id`（稳定 id）
- `source_rule_id`（溯源到具体触发规则）
- `requirement_type`（narrative / calculation / artifact / evidence / monitoring / surveillance / commitment / signature / seal）
- `required_artifact_refs`（指向 ArtifactRegistry 的 id 列表）
- `required_assurance_refs`（指向 AssuranceRegistry 的 id 列表）
- `status`（UNKNOWN / REQUIRED / PROVIDED / VERIFIED）

### 决议 3. 内部 stable id，显示编号晚绑定

系统内部**禁止**使用显示章节号（如 "2.2.4"）作为主键。章节、条件节、表、图、附件一律使用 `stable_id`（snake_case 路径式，如 `sec.project_overview.construction.diversion`）。显示编号在渲染期绑定。

**章节号显隐策略（三级）**：

| 级别 | 例 | 策略 | 章节号 |
|---|---|---|---|
| 末级条件小节 | 2.2.4 施工导流 | 保留节壳，写"本项目不涉及" | 保留原号 |
| 整章级条件模块 | 第 5 章 弃渣场选址与堆置 | 整章不出现 | 不前移 |
| 一级子节条件模块 | 3.5 取土场设置评价 | 整节不出现 | 不前移 |

**章节号不前移是硬原则**。违反将导致审查意见引用、修改对照表、跨版本 diff 全部失效。

### 决议 4. Fact → Narrative 必须经过 Projection

任何正文段落对事实字段的引用必须经过 `FieldIdentityRegistry` 的 projection 机制。**禁止**在 Narrative 模板或 AST 生成器中硬编码数字、面积、单位、派生量。

**规则**：
- `FieldIdentityRegistry` 中每个 Field 必须声明 `protection_level`，且必须携带 `lineage`（四子字段：`upstream_deps` / `derivation` / `projection_target_refs` / `invalidation_targets`）。
- CI / lint 须能检测"字面数字出现在 Narrative 模板内"这类违规绑定并阻止合入。
- 同一事实字段在特性表、报告表、正文、附图四路投影中必须 100% 一致；不一致由 Projection 层保证，不由业务层补偿。

### 决议 5. RulesetVersion 由项目申报时间决定，而非"当前最新"

规则集（2026 模板版、2018 格式版、2024 估算版、省市包版本）必须按项目属性选择，不跟随系统当前版本。

v0 仅支持新版规则集（2026 模板 + 2018 格式 + 2024 估算 + 广东包）。旧版规则集将于 2026-06-01 后废除，CPSWC 不支持过渡期旧版编制。本决议的存在是为了在未来（2028 / 2030 ... 规则更新时）系统能按项目归属版本正确切换，而非为了当下的双轨期。

**candidate → locked 实施细则**：

1. **项目创建时**：系统按申报时间估计值推荐一个 `candidate` ruleset，界面可见、可改。
2. **编辑期**：`candidate` 变更时，`ObligationSet` 整体重算。现有 facts **不删**，但被标记 `possibly_incomplete`，提示专家补填新规则要求的新字段。
3. **第一次 PRE_SUBMIT 冻结**（生成首个 `SubmissionPackageVersion`）时：`candidate` 升为 `locked`，之后不可改。

---

## 二、3 条保留主张

方向锁定，但 v0 暂不强实现。

### 主张 A. Narrative hand_override 的依赖追踪与分级 gate

**方向**：专家对正文的 hand_override 须记录 `fact_deps[]` 与 `obligation_deps[]`；依赖变动时按 `protection_level` 分四档触发：

| 档位 | 触发 | 行为 |
|---|---|---|
| CRITICAL | fact 或 obligation 的 protection_level = CRITICAL | BLOCK 导出 |
| PROTECTED | protection_level = PROTECTED | BLOCK_OVERRIDABLE（审核角色可豁免） |
| ADVISORY | protection_level = ADVISORY | WARN |
| EDITORIAL | 无依赖 | INFO |

**v0 实现**：Narrative 全部由 projection 生成，**不开放 hand_override**。专家只能改 Fact 或 slot 值。
**v1 实现**：开放 override，落地依赖追踪与分级 gate。

### 主张 B. SubmissionPackageVersion 的 content-addressed commit

**方向**：SemanticGraph 采用 content-addressed hash，`SubmissionPackageVersion` 通过 hash 引用而非深拷贝。冻结 = 一个不可变的 commit 指针，类比 git。

**v0 实现**：存一份扁平 `fact_snapshot` JSON blob + `rendered_outputs` 文件快照 + manifests。
**v1 实现**：升级为 content-addressed commit + 可复现 replay。

**命名约束**：`fact_snapshot` 名称 v0 与 v1 一致，v0 存原始 JSON，v1 存 hash 引用，演化路径不换名。

### 主张 C. ObligationGraph 的 DAG 与增量重算

**方向**：Obligation 之间以 DAG 表达依赖边（例如：弃渣场级别 → 稳定监测 → 视频监控 → 真实性承诺书）。支持增量 reactive 重算。

**v0 实现**：Obligation 为 Set 形态，任一事实变动触发全量重算。决议 2 要求的六字段（obligation_id / source_rule_id / requirement_type / required_artifact_refs / required_assurance_refs / status）保证 v0 → v1 可平滑升级。
**v1 实现**：Set 升 Graph，加依赖边与增量重算。

---

## 三、v0 / v1 / v2 阶段边界

### v0（MVP，首期交付）

**硬范围收敛**：

| 维度 | v0 取值 |
|---|---|
| Species | 仅报告书 |
| Grammar | 仅 NarrativeBook |
| compilation_intent | 仅 NEW |
| 行业 | 仅 29 房地产 + 30 其他城建 |
| 地方包 | 仅广东 + 惠州 |
| Ruleset | 单一版本（2026 模板 + 2018 格式 + 2024 估算 + 广东包） |

**必做清单（16 项）**：

1. `ProjectFactSheet_v0`：特性表 + 扩展字段的扁平 jsonb（非 graph）
2. `FieldIdentityRegistry_v0`：带 lineage 的字段登记表，YAML 形态
3. `SubmissionProfile` + `SubmissionLifecycle`：静态/动态分离结构
4. `ObligationSet_v0`：Set 形态，每条带决议 2 要求的六字段
5. `AssuranceRegistry_v0`：两态状态机（REQUIRED / PROVIDED）
6. `DisplayNumberingPolicy`：三级章节号策略 config
7. `ConditionEngine_v0`：决策表形态，覆盖 2026 细读产出的 30 条硬规则
8. `GeoPipeline_v0`：上传 shp → 面积/拐点/分县/叠加基础敏感图层；自动出 F-01 / F-04 / F-12 三张附图
9. `InvestmentEstimation_v0`：10 张估算表；广东定额；房地产城建
10. `DocumentRenderer_v0`：Word + PDF；页眉用 docx field 域；封面湖蓝色；装订参数按 2018 格式
11. `FrozenSubmissionInput_v0`：扁平 JSON blob，含 submission_profile / fact_snapshot / obligation_payload_resolved / assurance_manifest / artifact_manifest
12. `SubmissionPackageVersion_v0`：manifest + 文件快照 + metadata
13. `ReviewComment_v0`：手工录入，绑定 field_id / narrative_node_id / obligation_id
14. `ModificationReport_v0`：基于 FactDiff + ProjectionDiff 生成（不含 ObligationDiff）
15. `ProtectedBoundaryPolicy_v0`：机器可读 config，供 CI / lint / 导出 gate 共用
16. `CPSWC_SAMPLE_Huizhou_Housing_v0.json`：集成测试输入，用于 Registry + ObligationSet 的交叉验收

### v1（首期上线后 3 个月内）

- `ObligationSet` 升为 `ObligationGraph`（DAG + 依赖追踪）
- SemanticGraph 升为 content-addressed commit
- Narrative 开放 hand_override + staleness + 分级 gate
- `ObligationDiff` 加入 ModificationReport
- `GeoLayerProvenance` + 刷新策略 + `on_stale: BLOCK_EXPORT`
- `SubmissionLifecycle` 完整状态机
- `AssuranceRegistry` 扩展为六态（UNKNOWN / REQUIRED / PENDING / PROVIDED / VERIFIED / FROZEN）

### v2（再议）

- Reactive 增量重算运行时
- 第二个行业领域（线性 / 管网 / 矿山 任选）
- 多用户协作与字段级锁
- `OwnershipModel`（责任归属链）
- `ReplayHarness` 自动化集成
- `IndustryProfile` 升 `IndustryPlugin`
- `RealWorldCase` 结构化回流

---

## 四、治理与约束

### 反升级条款（Anti-Scope-Creep Clause）

未列入 v0 清单的能力，**不得**以"顺手做了""应该不难""后面反正要做""更通用一点"等理由进入 v0 代码。如需提前实施，必须：

1. 提交 RFC 文档，说明理由、范围与影响面
2. 更新本决议文档的 v0 清单
3. 获得架构决策者书面批准

违反本条款的代码合入属于**架构回滚事件**，须整体 revert，不得以"已经写了"为由保留。

本条款的存在是为了防止 v0 在三周后变成 v0.5，在两个月后变成 v1 demo，最终无法出厂。这是三轮架构讨论中被反复强调的风险点，不是形式主义。

### 前向兼容预埋豁免条款（Forward-Compatible Reservation Clause）

为了允许为未来版本 (v1+) **预留 schema 槽位**而**不污染 v0 生效规则**，在满足全部下列约束的前提下，可以在 `specs/` 下创建预埋文件：

1. **文件命名约定**：预埋文件必须在文件名中含 `_v1_reserved` 或 `v1_reservations` 标识（如 `v1_reservations.yaml`、`penalty_warning_table_v1_reserved.yaml`）。
2. **v0 lint 必须显式跳过**：`cross_registry_lint.py` 须将匹配 `*_v1_reserved*.yaml` / `*v1_reservations*.yaml` 的文件加入跳过集合，不纳入 v0 硬约束。未来可以增加 `--include-reserved` 开关用于主动检查 reserved 文件的内部一致性，但该开关不在 v0 默认 CI 路径上。
3. **Schema 扩展的默认值规则**：对已有 schema 新增 optional 字段时，必须提供不改变 v0 现有行为的默认值。例如给 obligation 加 `phase` 属性时默认 `pre_submission`，保证 v0 现有 24 条 obligation 无需重写。
4. **单向引用铁律**：reserved 文件**可以**引用 v0 已有 id（用于表达"未来这条义务会依赖 v0 的某字段"），但 **v0 的任何文件不得反向引用 reserved 条目**。任何违反——无论是 sample / ObligationSet_v0 / AssuranceRegistry_v0 / ArtifactRegistry_v0 / FieldIdentityRegistry_v0 里出现 reserved id——都属于 **v0 基线破坏事件**，按反升级条款同等严重度处理。
5. **v0 registry 纪律**：`ObligationSet_v0.yaml` / `AssuranceRegistry_v0.yaml` / `ArtifactRegistry_v0.yaml` / `FieldIdentityRegistry_v0.yaml` 只允许包含 v0 生效的条目。reserved 条目不以任何形式（含"disabled 标记"或"注释行"）出现在这些文件中，必须住在独立的 `_v1_reserved` 文件里。
6. **提升到正式 v1 必须走 RFC**：reserved 条目从独立文件"提升"到 v1 正式 registry 时，不能静默发生。须走与反升级条款相同的 RFC 流程（RFC 文档 + 更新 v1 清单 + 架构决策者批准）。reserved 状态本身不是"准批准"。

本条款与反升级条款形成**互补约束**：
- 反升级条款防止"**向前冲**"（未批准的能力偷偷进 v0 代码）
- 本条款规范"**向后留**"（为未来预留槽位但不让其污染 v0）

两者一起定义 v0 与 v1+ 的清晰边界。预埋行为在架构上是合理的，本条款为它提供了合法化路径；同时通过单向引用铁律和命名约定，保证预埋不会成为 v0 基线侵蚀的入口。

### 决议 6. ExpertSwitch Governance（专家确认型开关治理）

**背景**：水保规范里约 70% 的条款无法完全可计算化，只能以"专家确认型 bool"形式落地（典型如 `field.fact.disposal_site.failure_analysis_required`）。若不治理，bool 会无上限蔓延，架构在半年内退化为"一堆开关 + 一堆散文"。本决议把 bool 从"字段类型"提升为**受治理的一等对象**。

**适用范围**：

- `semantic_type == bool` **且** `origin != derived`（非 calculator 产出）**且** `protection_level ∈ {CRITICAL, PROTECTED}` 的字段。
- DERIVED bool（如 `compensation_required` 由 calculator 产出）**不在本决议管辖内**，由 CalculatorRegistry 治理。

**核心规则**：

所有符合上述条件的 bool，必须在字段定义中声明 `governance_block`，最少包含以下字段：

```yaml
governance_block:
  source_rule_id: <法规/标准条款, 必须到条款级>
  human_decision_question: <对填写者展示的一句话决策问题>
  decision_owner_role: <填写者角色, 如 registered_wsc_engineer>
  default_value: <v0 默认值>
  evidence_expectation: <期望的证据材料类型>
  replaced_normative_semantics:      # 必填, 覆盖度治理
    - rule_ref: <条款引用>
      quoted_phrase: <原规范文字>
      why_not_calculable: <说明为何无法算法化>
  upgrade_path:
    strategy: enum[splittable, refinable, irreducible]   # 必填
    planned_split_fields: [...]                          # 仅 splittable 必填
    refinement_notes: ...                                # 仅 refinable 必填
    irreducibility_justification: ...                    # 仅 irreducible 必填, 且须引规范依据
  sunset_target_version: <v1 / v2 / ...>                 # 仅 splittable 必填
  authored_by: <登记人>
  authored_at: <ISO 日期>
```

**irreducible 出口条款**：允许某些 bool 永远不被拆分（如"是否涉及敏感区""监测数据是否属实"），但 strategy 必须显式声明为 `irreducible`，且 `irreducibility_justification` 必须引用至少一条规范条款说明"此处必须专家判断"。没有这条出口，真实世界会从"bool 蔓延"转成"假拆分计划蔓延"，两者同样构成架构腐烂。

**关联义务的透明要求**：所有由 expert-switch bool 驱动的 obligation，必须在 `v0_scope_note` 中写清"为什么暂时合并"和"未来拆成什么"。

**lint 约束**：

- 新增规则 `EXPERT_SWITCH_001`：符合适用范围的字段若缺 `governance_block`，按下列节奏升级严重度：
  - v0 当前批次：**INFO**（显影纪律，不破绿灯）
  - 下一次新增任何 live expert-switch bool 而未治理：升 **WARN**
  - 进入 v1 正式治理：升 **ERROR**
- `EXPERT_SWITCH_001` 不适用于 reserved 文件内的字段（与其他 lint 规则一致）。

**准入纪律**：没有 `upgrade_path` 的 bool，禁止进入 v0/v1 生效 registry。这条是硬纪律，违反者按反升级条款同等严重度处理。

**与 CalculatorRegistry 的边界**：当 splittable bool 到达 `sunset_target_version` 时，拆分结果通常会进入 CalculatorRegistry（如 `disposal_site.failure_analysis_required` 将在 v1 被 `cal.spoil.level` + `cal.spoil.downstream_sensitivity` 两个 calculator 替代）。本决议为 bool → calculator 的迁移提供合法路径。

---

### 决议 7. Narrative Overlay Layer（正文覆盖层）

**背景**：主张 A 已要求 v1 开放 hand_override 并做依赖追踪，但仍未定义**可执行的编辑模型**。现实场景是：专家改了散文、fact 未同步、下次重渲染覆盖手改——这是 narrative/fact 漂移的典型路径。本决议把 hand_override 从"方向"落到"结构"。

**与四层真源边界的关系**：

> Overlay 是**第五层非真源**，不是把四层真源改为五层。

Fact → Obligation → (Narrative, Artifact) 的单向铁律保持不变。Overlay 被定义为"对 NarrativeBase 的受控差量"，本身不是 source of truth，不参与 obligation 计算，不被 calculator 引用。

**Overlay 对象最小结构**：

```yaml
overlay:
  overlay_id: <命名空间合法>
  target_narrative_node_id: <sec.* 或 para.*>
  base_render_hash: <挂钩时 base 的哈希>
  patch_type: enum[annotate, append, redact, replace]
  patch_payload: <文本 / 结构化差量>
  fact_dep_refs: [...]          # 此 overlay 依赖的 field.* id
  obligation_dep_refs: [...]    # 此 overlay 依赖的 ob.* id
  staleness_state: enum[fresh, stale, blocked, orphaned, reviewed]
  review_status: enum[draft, pending_review, approved, rejected]
  edited_by: <角色>
  edited_at: <ISO 时间>
```

**重渲染后的 replay 语义（按 patch_type 分档）**：

| patch_type | base 变更后行为 |
|---|---|
| `annotate`（旁注） | **总是可重放**，不受 base 变更影响 |
| `append`（追加段落） | **总是可重放**，除非目标 node 被删除 → 转 `orphaned` |
| `redact`（删除某句） | **base_render_hash 比对**，hash 变则 `stale` |
| `replace`（替换句子） | **base_render_hash 比对 + 依赖比对**，任一变则 `stale` |

这张表是决议的一部分，不是注释。v1 实现 overlay 层时，替换语义不得按 append 处理，反之亦然。

**Staleness 五状态**：

- `fresh`：可直接合并
- `stale`：依赖或 hash 变更，需专家复核
- `blocked`：命中 CRITICAL/PROTECTED 变更，禁止自动继承
- `orphaned`：target node 已不存在，必须走专家决议
- `reviewed`：已复核，可回到 fresh

**硬规则**：

1. **基础正文 NarrativeBase 永远由 projection 生成**，不允许手动绕过。
2. **专家修改只写入 EditorialOverlay，不反写 Fact**。
3. **Fact / Obligation 变化后**：先重渲染 Base，再按上表尝试重放 Overlay。
4. **依赖命中 CRITICAL / PROTECTED 变更**：overlay 直接转 `stale` 或 `blocked`，不允许静默继承。
5. **导出 gate 检查的不是"有没有手改"**，而是"有没有 `stale` / `orphaned` 未处理的 overlay"。
6. **ModificationReport 从 v1 起必须包含 OverlayDiff**。
7. **防腐禁令（核心条款）**：**Overlay 不得在 `patch_payload` 中引入 NarrativeBase 里不存在的新数字、新计量、新结论**。Overlay 只能对表达方式做增删改，不得成为绕过 fact 层的地下通道。
8. **防腐禁令的 lint 口径**：v1 引入 overlay 层时需新增规则，对 `patch_payload` 中数字类 token 做**归一化后的语义对比**（normalized counterpart check），不是裸字符串比对——数字须先做单位归一、格式归一、百分号/小数位归一；枚举与结论词须按规范化集合比对。避免 `98%` / `98.0 %` / `0.98` 这种表达被误伤。无 counterpart 的数字 token 直接 ERROR。
9. **v0 阶段的状态**：v0 不实现 overlay 层，但本决议与主张 A 一起在宪法中定义了"v1 必须按什么形状实现 overlay"。v0 的 NarrativeBase 生成行为保持不变。

**与主张 A 的关系**：本决议是主张 A 在 v0→v1 过渡期的**结构化落地版**。主张 A 保留"依赖追踪 + 分级 gate"的方向性描述，本决议补全"overlay 对象形状 + replay 语义 + 防腐禁令"。v1 上线时两者合并实现。

---

### 决议 8. Source Provenance & Normative Authority（来源铁律）

**背景**：bool 治理（决议 6）解决"规则怎么不烂"；overlay（决议 7）解决"正文怎么不漂"；本决议解决"知识怎么不脏"。如果不先把来源铁律写死，后续 region override、calculator、narrative template 都会悄悄把"样稿经验""地方口耳相传"灌进系统，最后变成一套我们自己都说不清来源的规则网。本决议把 v0 已有的 `source_rule_id` / `source` 这类描述性备注**提升为机器可读的来源契约**。

**核心原则**：

1. **任何**规则、参数、段落模板、表格结构、结论文案，都必须能追溯到显式的权威锚点。
2. 样稿、历史项目、few-shot、RAG 片段，**永远**不能作为唯一权威来源。
3. 地方 override（v1 功能）必须声明来源级别，不同级别适用范围不同。
4. 最终输出的每一段字面表达都必须能在权威锚点中找到对应，否则构成"知识污染"。

**硬规则 1：双锚必备（Dual Anchor Requirement）**

所有生效对象（obligation / field / artifact / assurance / calculator）必须声明两类引用：

- **`normative_basis_refs`**：指向规范 / 法规 / 标准条款。回答"**这条规则为什么存在**"。
- **`evidence_anchor_refs`**：指向项目内的 fact / artifact。回答"**这条规则在当前项目是否触发 / 以什么证据成立**"。

两者**不可互相替代**。只有 normative 没有 evidence，规则不知道在本项目是否触发；只有 evidence 没有 normative，规则本身就是凭空的。v0 当前批次不强制补齐所有旧对象（宽松口径，见 lint 约束），但**新增**的对象必须双锚齐全。

**硬规则 2：authority_class 与 precedence_rank 拆分**

为避免"类别标签与优先级编号绑定后反咬自己"（典型如 L4 推荐性标准 vs L5 正式批复的优先级悖论），将**类别标签**与**严格总序**彻底拆成两个字段：

- **`authority_class`**：九类分类标签（稳定命名，新增类别时其他标签不动）
  - `statute` — 法律（全国人大及其常委会立法）
  - `regulation` — 行政法规 / 部门规章 / 地方规章
  - `mandatory_standard` — 强制性标准（GB 系列不带 /T）
  - `official_approval` — 正式批复文件（省/市发改价格批文、主管部门正式复函等）
  - `recommended_standard` — 推荐性标准（GB/T / NB/T / SL/T 等）
  - `authoritative_guide` — 主管部门公开指南 / 技术要点
  - `meeting_memo` — 主管部门内部纪要 / 座谈口径
  - `expert_consensus` — 行业专家共识（需留痕）
  - `expert_individual` — 单一专家经验（需留痕 + 评审）

- **`precedence_rank`**：严格总序（数字越小优先级越高，允许在既有类别之间插入新位次）
  - v0 默认排序：
    1. `statute`
    2. `regulation`
    3. `mandatory_standard`
    4. `official_approval`
    5. `recommended_standard`
    6. `authoritative_guide`
    7. `meeting_memo`
    8. `expert_consensus`
    9. `expert_individual`

**这个顺序里的两个反常识**必须理解：

- 强制性标准（mandatory_standard, rank 3）> 推荐性标准（recommended_standard, rank 5）：GB/T 50434 是推荐性的，GB 50433 是强制性的，前者不能覆盖后者。
- 正式批复（official_approval, rank 4）> 推荐性标准（recommended_standard, rank 5）：省级正式批复在该省辖区内有法定效力，高于推荐性国标。粤发改 2021_231 号属于 official_approval，不是 recommended_standard。

**冲突消解规则**（严格顺序，逐级比较）：

1. 先比 `precedence_rank`，更小者胜
2. 同级时比 `effective_since`，更新者胜
3. 同级同期比 `issued_by_scope`，更贴近本项目适用地域者胜（市级 > 省级 > 国家级，仅在"本地法优于上位法未覆盖场景"成立；不适用于强制性规范）
4. 最后才进入**人工仲裁**，仲裁结论必须留痕并进入 `authority_chain_audit`

**硬规则 3：sample_usage_mode 三档**

样稿入库时必须显式标注以下三档之一（**没有默认值，没标注者不允许入库**）：

- `authority` — **永不允许**。样稿即使内容完全正确，也不得作为权威来源。规则层或 calculator 必须找到规范条款作为锚点，样稿只能作为交叉验证参考。
- `inspiration_only` — 可作为启发（few-shot prompt / RAG 片段 / 模板灵感来源），但以下约束必须同时满足：
  - （a）不得作为任何生效规则的**唯一依据**；
  - （b）**由启发式路径生成的最终输出，其字面表达必须能在 `source_rule_ref` / fact field / calculator 输出中找到对应权威锚点**。无法找到锚点的字面表达视为污染，进入 overlay 的 `stale` 状态或直接被拒绝合入。
- `prohibited_entirely` — 完全禁止入系统任何路径。典型场景：曾被审查退回的问题样稿、包含已知错误未更正的样稿、来源不明的扫描件（见 `ProvenanceClassification.yaml` 扫描件禁入条款）。

**与决议 7 的关系**：本硬规则的（b）条款是决议 7 "overlay 防腐禁令 normalized counterpart check" 在 LLM 生成路径上的**镜像规则**。决议 7 管人工手改引入的污染，本规则管 LLM 生成引入的污染，两者共用一个底层假设——**最终输出的每一段字面表达都必须有权威锚点**。

**硬规则 4：扫描件硬禁令**

**任何无责任署名、无制作时间、无版本号的 PDF / 扫描件**，无论内容如何，一律归入 `prohibited_entirely`。该条款不接受例外申请，不接受"反正内容没错"的辩护。这是唯一能真正切断"匿名培训材料 → LLM 训练 → 错误结论 → 规则污染"链路的方法。

**具体约束条款落地到独立文件** `specs/ProvenanceClassification.yaml`（本批次创建，就地生效，不走 reserved 通道）。

**lint 约束**：

新增规则 `SOURCE_AUTH_001`，v0 当前批次**宽松口径**：

- **扫描范围**：所有 v0 生效对象（obligation / field / artifact / assurance）
- **只对明显缺失发 INFO**：完全缺 `source_rule_id` / `source` / 等价字段者发 INFO
- **不校验**本批次新引入的字段（`authority_class` / `sample_usage_mode` / `normative_basis_refs` / `evidence_anchor_refs` / `precedence_rank`），避免把旧对象的未迁移状态当成违规
- **reserved 文件**按既有规则继续豁免
- 严重度升级节奏：v0 INFO → v1 WARN → v2 ERROR

**准入纪律**：决议 8 生效后，**新增**的生效对象（任何进入 v0/v1 registry 的新条目）必须满足：

1. `source_rule_id` 非空且指向 `rule.*` 或规范条款
2. `authority_class` 非空且取值在九类之中
3. 双锚必备（`normative_basis_refs` + `evidence_anchor_refs`，除非对象本身是 evidence 源头）
4. 不得引用 `sample_usage_mode == prohibited_entirely` 的任何样稿

违反准入纪律的新增对象按反升级条款同等严重度处理。

**与决议 6 / 决议 7 的关系**：

- 决议 6 的 `governance_block.source_rule_id` 是本决议的**下游具体落地**——expert-switch bool 的来源锚就是本决议所要求的双锚之一（normative_basis_refs）。
- 决议 7 的 overlay 防腐禁令与本决议的 sample_usage_mode (b) 条款**互为镜像**，共同定义"最终输出必须有权威锚点"。
- 本决议为 v1 的 region override / calculator 激活提供**上游红线**，未通过来源铁律的 override / calculator 禁止进入生效 registry。

---

### 决议 9. Regional Override Layer（地方特化层）

**背景**：v1 必须面对"一个项目落到不同省份时规则要不同"的现实（典型：广东补偿费 0.6 元/m² vs 其他省不同）。若不把 override 结构化，v1 要么污染 ObligationSet（给每条规则加 `if region == 广东 then ...`），要么放任地方规则散布在代码里。本决议把 override 从"散点补丁"提升为**受来源铁律约束的局部特化层**。

**与四层真源 + 第五层 Overlay 的关系**：

> Region Override 是**第五类非真源配置层**（与 Overlay 并列，不是 Overlay 的子集），不是 Fact / Obligation / Narrative / Artifact 的真源，也不参与 obligation 推导的本体。它是一个"在运行时选择链中注入的特化层"。

Fact → Obligation → (Narrative, Artifact) 的单向铁律保持不变。Overlay 管"人工手改的表达差量"，Region Override 管"地方对国家基准的局部特化"，两者互不替代。

**核心 6 条（写死，不接受弱化）**：

1. **Region override 是第五类非真源配置层**，不是 Fact/Obligation/Narrative/Artifact 的真源。它不直接定义规则，只对**已登记**的规则做局部特化。

2. **override 只能针对已登记对象生效，不得创建匿名地方规则**。target_ref 必须指向 FieldIdentityRegistry / ObligationSet / ArtifactRegistry / AssuranceRegistry 中已登记的 id。v0 reserved 上下文下允许指向 v1 将登记的 id（forward reference），但 v1 启用 override 之前必须完成 target 登记。

3. **override 必须受决议 8 的 provenance 约束**：每个 override 必须同时携带 `normative_basis_refs` / `authority_class` / `precedence_rank` / `effective_since` / `issued_by_scope` / `provenance_verified`。没有这些字段的 override 不算 override，只算野生口径。

4. **override 不得削弱更高 authority 的 mandatory 约束**。低权威地方 override 不得削弱高权威上位规则，除非上位规则明确授权地方细化。这条和决议 8 的冲突消解规则一致，但在 override 层更严格——即使消解出"本 override 胜"，只要它削弱了 mandatory_standard（rank 3）或更高的约束，仍然禁止生效。

5. **override 冲突按严格顺序消解**：`precedence_rank` → `effective_since`（更新者胜）→ `issued_by_scope`（更贴近本项目适用地域者胜）→ `manual_arbitration`（人工仲裁，结论记入 `authority_chain_audit`）。

6. **v0 不消费 override，v1 才允许进入运行时选择链**。本决议在 v0 阶段只定义结构，不接入 runtime。v1 启用 override 时须走 RFC + 提升 prototype 为正式 RegionOverrideRegistry_v1.yaml。

**非 override 的禁区**：以下内容**不得**通过 override 层改动，必须走正式 RFC：

- 四层真源边界
- Species / Grammar / SubmissionContext 三轴分派
- Overlay 防腐规则（决议 7）
- Source provenance 铁律（决议 8）本身
- Anti-Scope-Creep Clause 与 Forward-Compatible Reservation Clause

**action 闭集（不接受弱化，新增必须 RFC）**：

override 的 `action` 字段只能取以下 5 值之一：

| action | 语义 | 典型场景 |
|---|---|---|
| `replace_scalar` | 替换一个标量值 | 补偿费费率替换 |
| `replace_map_entry` | 替换 map 类 field 的某个 key 值 | `region_specific_rate[广东省] = 0.6` |
| `add_constraint` | 追加约束（不改现有约束） | 地方要求某字段额外声明 |
| `add_required_artifacts` | 追加所需工件 | 地方条例要求额外附件 |
| `refine_applicability` | **收窄**适用条件 | 承诺制仅对某类项目免报 |

**`refine_applicability` 的硬约束**：**只能收窄，不能放宽**。放宽本身不是 override 能做的动作，放宽意味着"让本来该管的项目不管了"，这是上位规则级变更，必须走 RFC 修改正式 ObligationSet，不得通过 override 层实现。本条不是示例性要求，**是决议 9 的强制文字条款**。

**target_ref 命名空间约束**：

- `target_ref` 必须指向既有 id，使用现有命名空间（`field.*` / `ob.*` / `art.*` / `as.*`），**不得开设新的顶级命名空间**（如 `field.region_specific_rate.*`）。
- `target_attribute_path` 用于指向 target 对象内部的属性槽位，但**只能指向显式声明为 override-capable 的属性**。schema 上通过 `override_capable: true` 或 `override_slots: [...]` 标记 override-capable 槽位。未标记的属性**不得**被 override 修改，即使语法上可达。
- 这条约束是**硬门槛**：未来 lint 规则 `REGION_OVERRIDE_002` 会在 v1 启用时对此做强制校验。

**最小必备字段**（每个 override 对象的 schema 最小集）：

```yaml
override_id:           <ro.* 命名空间>
target_kind:           enum[field_rate, obligation_applicability, artifact_addition, assurance_addition]
target_ref:            <指向已登记 id>
target_attribute_path: <指向 override-capable 槽位, 可选>
region_scope:
  country: CN
  province: <省级名称, 不允许 "*">
  prefecture: <市级名称, 可 null>
  county: <县级名称, 可 null>
applicability:
  species: [...]
  industry_categories: [...] | "*"
  phases: [...]
action: <action 闭集之一>
payload: <按 action 分型>
normative_basis_refs: [...]
authority_class: <决议 8 九类之一>
precedence_rank: <决议 8 严格总序>
effective_since: <ISO 日期>
effective_until: <ISO 日期 | null>
issued_by_scope: <发文机构辖区>
provenance_verified: <bool>
authored_by: <登记人>
authored_at: <ISO 日期>
status: <active | representative_structure_not_factually_final>
factual_validation_required: <bool>
```

**province 字段强约束**：不允许 `"*"`。`province="*"` 意味着全国生效，全国生效的规则**不是 override，是 national baseline**，应该进入正式 ObligationSet / ArtifactRegistry。允许 `"*"` 会把 override 层变成"全能规则入口"，直接撕破本决议的边界。

**lint 约束**：

预埋三条 reserved-only lint 规则骨架（本批次不进入 v0 默认执行序列）：

- `REGION_OVERRIDE_001`: target_ref 必须能 resolve（v1 启用时对正式 registry 做 dangling 检查）
- `REGION_OVERRIDE_002`: provenance 字段完整性 + target_attribute_path 必须命中 override-capable 槽位
- `REGION_OVERRIDE_003`: 冲突消解键合法性 + `refine_applicability` 不放宽 + province != "*"

这三条 reserved-only 规则在 v0 阶段以函数骨架形式存在于 `cross_registry_lint.py`，但**不被 main() 调用**，避免污染 v0 绿灯。v1 启用时通过 `--include-reserved` 开关激活。

---

### 对内 / 对外双层叙事

CPSWC 在不同受众面前使用不同的系统叙事。两者不矛盾，但**不得混用**：

- **对内**（架构文档、代码注释、技术 RFC、本决议文档）：
  CPSWC 是一个**监管语义投影系统**。核心是 `ProjectSemanticGraph` + `ObligationGraph` + 四路 projection。
- **对外**（产品手册、销售材料、客户汇报、工程师 onboarding 首周材料）：
  CPSWC 是一个**法规模板驱动的文档装配引擎**，底层保证三路同源与规则校验。

对内叙事是系统的真相，对外叙事是系统的认知入口。新成员 onboarding 一般先接触对外叙事，进入核心模块开发后才切换到对内叙事。

---

## 五、变更记录

| 日期 | 版本 | 变更 | 责任人 |
|---|---|---|---|
| 2026-04-11 | v0-archdec | 初版收敛（三轮架构讨论后） | - |
| 2026-04-11 | v0-archdec-patch1 | 新增决议 6 ExpertSwitch Governance、决议 7 Narrative Overlay Layer；同批在 v1_reservations 预埋 source_authority / region_override / region_specific_rate / visibility_scope / audience_scope / contributed_by / reviewed_by 槽位 | v1 前置宪法修补包 |
| 2026-04-11 | v0-archdec-patch2 | 新增决议 8 Source Provenance & Normative Authority（来源铁律）：双锚必备 + authority_class/precedence_rank 拆分 + sample_usage_mode 三档 + 扫描件硬禁令；同批在 Core Contracts 新增 source_provenance 节，新建 ProvenanceClassification.yaml 就地生效 | Step 9 来源铁律包 |
| 2026-04-11 | v0-archdec-patch3 | 新增决议 9 Regional Override Layer：5 action 闭集 + province != "*" 硬约束 + refine_applicability 只收窄不放宽 + target_attribute_path 仅命中 override-capable 槽位；同批新建 RegionOverridePrototype_v1_reserved.yaml（reserved, 2 个示例: 广东补偿费 / 广东条例责任范围附加工件） | Step 10 地方特化层结构原型 |

