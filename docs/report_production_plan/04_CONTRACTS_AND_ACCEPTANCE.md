# P0 最小契约与验收矩阵

版本：1.0｜这是待实施设计，不是当前API文档。所有新增持久化结构应有schema_version；兼容适配不得提升旧数据可信等级。

## 1. 五类状态分开

| 维度 | 建议值 | 语义 |
| --- | --- | --- |
| ValueState | PRESENT / MISSING / INVALID / CONFLICT / NOT_APPLICABLE | 值是否可读取；PRESENT不代表来源已核验 |
| Applicability | APPLICABLE / NOT_APPLICABLE / UNKNOWN | 内容/义务是否适用；不适用必须能说明判定依据 |
| ContentState | UNASSESSED / MISSING / DRAFTED / INCOMPLETE / COMPLETE | 适用内容要求是否完成；COMPLETE不等于技术正确 |
| EvidenceState | UNASSESSED / MISSING / UNVERIFIED / READY / INVALID | 引用、项目来源与计算输入是否满足已声明证据要求 |
| ReviewState | NOT_REVIEWED / NEEDS_REVIEW / CONFIRMED / REJECTED / STALE | 实际复核记录及对当前输入的有效性 |

旧`RenderStatus.full/skeleton/not_applicable`继续服务渲染，不能映射为ReviewState.CONFIRMED。程序PASS只表示特定机器检查通过，不等于专业复核通过。

具体边界：

- 缺键、None、空白字符串：按字段类型判MISSING；不能转0。
- 数值0、布尔False：合法类型下是PRESENT；不能被`if not value`吞掉。
- 空list：容器已提供，但不能独自证明“已完整调查且无涉及”。具体事实的证据状态另判。
- `{"value": null, "unit": "万m³"}`仍是MISSING；非法数字字符串、NaN、inf、非法单位为INVALID。
- “/”是显示符号，不可作为业务值输入参与运算；NOT_APPLICABLE需要理由及证据。
- 数字相等但单位不同要先做有定义的换算；无单位不能直接比较；不同来源冲突不能悄悄选择。

## 2. 推荐最小类型

### QualityFinding（诊断，不复制事实）

```text
code: 稳定机器码
severity: BLOCK | WARN | INFO
target_ref: 现有field/ob/sec/art/as引用，或已登记的新类型引用
message: 可读问题
missing_input_refs: 缺哪些已登记输入
evidence_refs: 本诊断所依据的记录引用
remediation: 需要什么资料/动作
stage: INPUT | EVALUATION | RENDER | POSTFLIGHT
```

诊断code是检查标识，不冒充法律条款rule_id；不要将ENGINE_ERROR注册为规范条款。建议稳定码：VALUE_MISSING、VALUE_INVALID、INPUT_CONFLICT、CONDITION_UNKNOWN、CONDITION_ERROR、SOURCE_UNVERIFIED、ASSERTION_UNSUPPORTED、TARGET_EFFECT_CONFLATED、DERIVED_STALE、DEMO_ASSUMPTION、PROFILE_UNSUPPORTED、CONTENT_INCOMPLETE、ARTIFACT_MISSING、RENDER_FAILED、REVIEW_STALE、FORMAL_CAPABILITY_INCOMPLETE。

### SectionQuality

```text
section_id
requirement_refs                 # 对应内容规范中的叶子要求
applicability
applicability_evidence_refs
content_state
evidence_state
review_state
input_hash
finding_codes
```

ReportQualitySummary汇总必须保留分项数量，不仅总分。至少包括unresolved_critical_count、unknown_applicability_count、missing_artifact_count、unreviewed_requirement_count、unassessed_requirement_count、render_error_count、is_submittable。最后一项只能来自正式门禁完整结果，不能由前端计算。

### EvidenceRecord / ReviewRecord / AssuranceRecord（最小sidecar）

```text
quality_inputs:
  schema_version
  evidence_records:
    - evidence_id
      target_refs
      source_kind                 # project_document / structured_input / calculation / normative_source
      source_document_ref
      locator                     # 页/表/图/字段或计算明细位置，不编造页码
      content_sha256
      source_version
      verification_status         # UNVERIFIED / VERIFIED / REJECTED
      verified_by                 # 真实确认记录，系统不得自行填写人名
      verified_at
  review_records:
    - review_id
      target_refs
      input_hash
      verdict                     # CONFIRMED / REJECTED / NEEDS_REVIEW
      reviewer_ref
      evidence_refs
      reviewed_at
  assurance_records:
    - assurance_id                # 复用as.*
      state                       # REQUIRED / PROVIDED；沿用既有两态，不擅改为第三套状态机
      evidence_refs
      input_hash
      confirmed_by
      confirmed_at
```

这只是技术结构提案。文件有姓名、状态或hash不等于身份与签章真实性已被软件证明；证据核验/确认必须经过项目受控人工流程。P0不实现身份鉴别平台、不声称能自动验证公章真伪。质量输入缺失时legacy适配为UNVERIFIED，不自动制造记录。所有引用要解析，记录自称VERIFIED但无原始证据/版本对应仍不满足发布。

新增evidence/review跨对象ID前更新Core Contracts并通过lint。源码中的`rule.template_2026.*`/`standard.*`需要映射到已核验规范定位；注册一个字符串不等于核验了规范。P0允许未核验映射阻断，不允许自动把所有旧引用加入“可信白名单”。

## 3. 统一输入读取接口

建议接口（名称可小幅调整，语义不得改变）：

```python
make_build_context(project_input, runtime_snapshot, registries) -> BuildContext
resolve_value(context, field_id) -> ResolvedValue
evaluate_report_quality(context, narrative, tables, content_requirements, inventory) -> ReportQualitySummary
check_export_readiness(snapshot, *, assurance_state=None,
                       export_mode="draft", quality_summary=None,
                       artifact_inventory=None) -> ExportGateResult
build_package(project_input, output_dir, *, ruleset=None, lifecycle=None,
              previous_version_id=None, export_mode="draft") -> Path
```

BuildContext为一次构建的只读视图，保存现有facts/derived/registry引用和规范化读取接口、来源选择与诊断，不持有另一套可人工编辑facts。投影经此视图及FIR读取；旧dict入口由适配器桥接。禁止每个模板各自创建别名/单位/来源优先级。

来源选择规则：

1. 当前成功计算的派生量是对应计算结果的权威读值，保存计算ID、输入hash、方法/版本、单位。
2. 同字段有当前失败计算时，旧pre-stored derived不能遮盖失败；其值只能作为标记stale的历史展示。
3. 没有当前计算但存在外部结果时，明确EXTERNAL_RESULT及证据/确认状态，不伪装为系统重算结果。
4. 冲突显式报告。别名仅在语义、单位、包含关系确认后登记；原始资料不被静默修改。
5. 项目事实、运行时计算和对外表格均读取同一选定版本；render中不得反向写入。

最少需要查清的别名候选（候选不是授权直接合并）：

| 原始/样本用法 | 其他读取用法 | 处理前必须确认 |
| --- | --- | --- |
| topsoil.stripable_volume | topsoil.strippable_volume | 是否同指可剥离量，还是已剥离量 |
| topsoil.fill | topsoil.backfill_volume | 回覆计划与实际口径 |
| prediction.total_loss | prediction.predicted_total_loss | 预测方法、时段与包含范围 |
| project.builder/compiler | project.construction_unit/compile_unit | 是否仅同义名称 |

## 4. 条件未知态

既有triggered语义：True=条件成立；False=条件可确定地不成立；None=未知或错误待处理。False不是专业确认“完全不涉及”，其证据状态由质量检查另行判断。

推荐三值逻辑：NOT UNKNOWN=UNKNOWN；TRUE AND UNKNOWN=UNKNOWN；FALSE AND UNKNOWN=FALSE；TRUE OR UNKNOWN=TRUE；FALSE OR UNKNOWN=UNKNOWN。若当前DSL无法安全实现分支推理，P0允许保守地将含缺失依赖的整个表达式标UNKNOWN，但不得变False，且应列明这一限制。

evaluate_all把None保留在unknown集合/详情中，不纳入not_triggered。级联“任一依赖触发”规则中：有True→True；全部明确False→False；否则UNKNOWN。缺引用、循环、解析错误形成对应diagnostic。

ConditionEngine只输出义务求值。章节是否保留、专题是否省略仍由投影策略决定；常规章节不能借某个专题义务的False直接省略。

## 5. 关键断言准入

| 断言类型 | 可接受支持 | 不能作为充分支持 |
| --- | --- | --- |
| 事实复述 | 当前有效值、正确单位、来源状态如实标记 | 只有字段名，没有值 |
| 算术结果 | 可复算方法、输入引用、单位和结果、当前计算成功 | 模板中手算且未保存过程、旧缓存 |
| 规范要求描述 | 可解析且适用的规范定位 | 搜索摘要、案例措辞、编造section_11 |
| 本项目合理/可行/符合 | 相应评价记录、项目证据与当前专业确认 | 仅引用标准、仅有一张表、义务已触发 |
| 目标达标预测 | 独立的设计效果计算与目标比较、适用性和专业复核 | 加权目标本身、用目标补效果空值 |
| 已核查不涉及 | 本项核查覆盖范围、材料版本、结果和确认 | 空list、默认False、字典查不到 |

P0采用受控模板检查与断言绑定，而非让模型自行给文本“可信度打分”。高风险模板之外尚未完成语义审查的段落统一保留UNASSESSED，不自动升级。

建议六率结果最小读结构：indicator_id、target_binding_ref、effect_binding_ref、effect_kind=DESIGN_EXPECTED/MONITORED_ACTUAL、period、numerator_ref、denominator_ref、method_ref、input_hash、review_ref。优先映射已有已确认结果；P0没有可信效果输入就显示待计算，不为满足结构虚造新业务字段或计算器。

## 6. 报告书显示结构：主要纠偏点

以下来自已检索的2026模板，实施时须核对项目适用正式原件。这里不是完整规范转录，也不是可直接自动激活的registry。

| 内容 | 本轮纠偏方向 |
| --- | --- |
| 综合说明 | 1.1—1.9及特性表，不能仅基本情况+特性表；结论在1.9 |
| 项目概况 | 项目组成/工程布置、施工组织、占地、土石方、适用的拆迁迁建、进度、自然概况 |
| 项目评价 | 常规选址、布局、占地、土石方、适用取土场、施工方法、主体措施评价 |
| 表土 | 调查评价、保护、堆存养护、利用，不能只剥离/平衡两节 |
| 预测 | 现状、影响因素、预测过程、危害，不能只填总量 |
| 防治第7章 | 7.2设计水平年、7.3目标、7.6工程级别与标准、7.7分区措施、7.8施工组织 |
| 投资第9章 | 9.1投资估算、9.2效益分析；补偿费作为相应估算内容，不占用9.2 |
| 管理第10章 | 最后主体章；不额外创建第11章结论替代1.9 |

稳定ID迁移原则：`sec.conclusion`可以作为历史稳定ID映射到1.9，不强制为了名字漂亮重命名；`sec.soil_loss_prevention.benefit_analysis`可保留稳定引用但显示到9.2，必须有迁移说明。严禁产生同一ID两个相互冲突的节点。旧审查意见中的显示编号保留原版本语境，不直接套新编号。

公开依据：[2026模板正文](https://slj.changdu.gov.cn/cdsslj/zcjd/202604/d9a22fa0f86b4ebeb39f59836c9ed3f2.shtml)。页面标题文号有误，实施时以原件和[引用232号的官方审批材料](https://www.cqbn.gov.cn/zwgk_252/fdzdgknr/zdxm/pzjgxx_1/fasp/202609/t20260904_16031551.html)交叉核对；不可把网页标题错误复制到规范库。

## 7. 哈希与失效

两个hash分工：

- `fact_snapshot_hash`：实际规范化事实集合。事实不变而来源版本变动时可不变，不能单独决定审核有效性。
- `generation_input_hash`：事实+有效输入来源/版本/内容hash+静态profile+规则与registry+模板+计算实现版本+被消费外部结果。用于审核有效性、重生成和变更判定。

canonical JSON固定key排序、编码、数字规范、空值语义；有序数组保留顺序，只对声明为集合的列表做稳定排序。运行时间、审计事件ID、临时目录不进入语义hash。外部依赖改变须体现在版本或内容指纹中。

发布文件的SHA256另算，用来证明文件完整性；它不证明内容正确。P0旧包不做原地迁移，明确hash_schema_version和legacy来源。审核记录引用的generation_input_hash不同即STALE。

## 8. 制品与发布契约

ArtifactInventoryEntry至少包含：artifact_id、required、applicability、delivery_form（FILE/EMBEDDED）、provider（GENERATED/IMPORTED）、relative_path、embedded_anchor、content_sha256、status（MISSING/PROVIDED/VALIDATED/FAILED/DEMONSTRATION）、validation_checks、finding_codes、generation_input_hash。

VALIDATED的含义必须附带checks列表，不能笼统代表专业合格。存在/可解析/内容定位/专业确认是不同检查。父artifact完成依赖必需子项；required列表、path存在或文件名正确均不是完整性证明。

正式发布流程：

`上下文与能力预检 → 当前版本冻结/确认核验 → staging生成 → 制品与内容后检 → 新目录原子发布`

正式模式的BLOCK至少包括：未知必需内容、缺关键输入、未支持断言、失效计算、必需保障未有效提供、旧审核、未实现必需能力、真实空间/必要附件缺失、渲染失败、签署版本不匹配。适用字段集合来自义务/内容要求，不能把registry里所有条件性CRITICAL字段不分场景一律要求；适用性未知则阻断，不能直接忽略。

草稿模式不丢失上述问题，只允许带显著标识生成审阅成果。manifest新增至少export_mode、is_submittable、quality_summary_ref、artifact_inventory_ref、hash_schema_version、generation_input_hash、build_status。`export_gate_result.json`本身也是输出证据，不应成为“该包已通过”的循环证明。

建议失败接口：正式拒绝抛`ExportBlockedError`，含稳定findings；工具/生成失败为`PackageBuildError`。CLI成功=0，参数错误=2，正式门禁拒绝=3，构建失败=4；可采用不同数字但须集中定义和一致测试。核心库不得sys.exit。未登记模式直接参数错误。

不允许正式失败后静默降级、`--force`、覆写既有正式目录、旧文件补缺、mock结果放行。P0仍缺生产能力时，门禁策略正向单测可以通过，真实formal包应因具体缺口拒绝；两者都必须验收。

## 9. 验收矩阵

每项必须由自动测试或明确人工记录覆盖；“看过代码”不是测试结果。以下编号应出现在每批交付报告中。

同一编号可能含单元、集成和发布端到端三层；按03文档的批次约定逐层完成。尚未到实施批次的集成层标NOT_IMPLEMENTED，不作为“跳过后通过”的证据。C批最终验收须覆盖全部层级或明确未完成，不能只保留早期mock结果。

| ID | 场景/输入 | 必须观察到的结果 | 主要测试文件 |
| --- | --- | --- | --- |
| A00 | 接手时HEAD与工作区状态 | 记录版本和用户已有变更，不覆盖 | P0_BASELINE.md |
| A01 | 原有测试与lint | 记录实际结果和环境，差异可解释 | 全量pytest/lint |
| S01 | 缺键/None/空白 | MISSING，不转换为0 | test_report_quality.py |
| S02 | 数值0/布尔False | PRESENT，正确按类型判断 | 同上 |
| S03 | 空list无调查记录 | 不生成“经核查不涉及” | 同上/断言测试 |
| S04 | NaN/inf/错误单位/Quantity空值 | INVALID或MISSING，禁止参与有效计算 | 同上 |
| S05 | legacy snapshot无quality | 可读，UNASSESSED/UNVERIFIED，非已审 | 同上 |
| U01 | 借方trigger依赖缺失 | UNKNOWN，不进入not_triggered | test_condition_unknown.py |
| U02 | 输入明确0/False | 可确定False，仍保留来源状态 | 同上 |
| U03 | DSL解析/求值异常 | ERROR finding，非False | 同上 |
| U04 | UNKNOWN经NOT/AND/OR | 满足三值或声明的保守策略，不伪判不涉及 | 同上 |
| U05 | 级联链调换registry顺序 | 相同求值结果 | 同上 |
| U06 | 缺依赖/循环 | UNKNOWN及诊断，不默认为False | 同上 |
| U07 | 无红线冲突但未做常规评价 | 常规选址内容保留为待核验 | 同上/结构测试 |
| N01 | 空facts调用评价/结论模板 | 无肯定结论，质量检查给具体缺口 | test_narrative_assertions.py |
| N02 | 有规范ref、无项目证据 | 不准确认项目合规 | 同上 |
| N03 | 借方缺失/明确0两组 | 前者待确认；后者可复述提供值但不泛化合规 | 同上 |
| N04 | 仅有加权目标 | 表文只显示目标，效果待计算，不达标 | test_target_effect_separation.py |
| N05 | 效果低于目标 | 该指标不达标；总述不得“各项均达标” | 同上 |
| N06 | 部分效果缺失/分母0 | 未决或有依据N/A，不强行100% | 同上 |
| N07 | obligation触发/artifact仅登记 | 不描述为已完成/已提供 | 断言测试 |
| N08 | 改已引用输入，ref名字不变 | 旧结论确认STALE；汇总也同步失效 | 断言/冻结测试 |
| I01 | 同一snapshot走表/正文/工作台/diff | 同事实同读值同来源/状态 | test_snapshot_adapter.py |
| I02 | 单侧别名、双侧一致、双侧冲突 | 正确映射/保留/报冲突，不静默吞值 | 同上 |
| I03 | 当前计算失败+旧derived存在 | 无有效回退，旧值明确stale | 同上 |
| I04 | 缺单位与可换算单位两组 | 前者非法；后者统一值与精度 | 同上 |
| I05 | 默认模数/默认时段/近似红线 | DEMO_ASSUMPTION，不能正式使用 | 同上/制品测试 |
| I06 | 当前成功derived与旧值不一致 | 各入口同选当前结果，并保留来源诊断 | 同上 |
| R01 | 报告书2026结构 | 10章主体，关键位置正确，不存在伪section_11依据 | test_report_structure.py |
| R02 | 模板未实现必需叶子内容 | 仍进入要求清单及缺口，不从分母删除 | 同上 |
| R03 | 条件章不适用/未知 | 前者按策略省略且不前移；后者不能伪N/A | 同上 |
| R04 | Species缺失/报告表暂不支持 | 显示未知/格式未就绪，不能假报告书正式输出 | 同上 |
| R05 | 旧编号审查引用与新显示映射 | stable ID保留，旧语境可辨，无悬空静默丢失 | 同上 |
| F01 | 只改项目名称，派生结果相同 | fact_snapshot_hash变化 | test_submission_freeze.py |
| F02 | 对同一输入重复run_project | 原输入深比较不变，无原地enrich写回 | 同上 |
| F03 | 完全相同语义输入不同时间运行 | semantic hash相同；run元数据可不同 | 同上 |
| F04 | 规则/模板/来源文件内容变化 | generation_input_hash变化，旧审核STALE | 同上 |
| F05 | 读取旧冻结包 | 不重写、不伪新版，显示legacy状态 | 同上 |
| F06 | 更改输入后复用旧签署确认 | 正式拒绝，草稿提示需重新确认 | 同上/门禁测试 |
| A02 | required列表存在但无文件/内嵌锚 | ARTIFACT_MISSING | test_artifact_inventory.py |
| A03 | 父附表包仅有部分子项 | 父项不得完成 | 同上 |
| A04 | DOCX/PDF/GIS模拟失败 | FAILED+诊断，formal非零且无正式包 | 同上/门禁测试 |
| A05 | output里有上轮同名文件 | 不自动作为本轮制品 | 同上 |
| A06 | 图只有CGCS2000文字/矩形示意 | DEMONSTRATION，非正式空间证据 | 同上 |
| G01 | 旧build_package调用未指定模式 | 明确草稿，is_submittable=false | test_formal_export_gate.py |
| G02 | formal有BLOCK | 结构化拒绝，无正式发布目录 | 同上 |
| G03 | 缺/假引用/旧版本assurance | formal拒绝；裸True不足 | 同上 |
| G04 | draft有BLOCK | 可读草稿+显著标识+完整问题清单，不冒充PASS | 同上 |
| G05 | 门禁合成正向夹具满足所有声明条件 | 策略检查可通过；明确不是生产样本 | 同上 |
| G06 | 实际样本缺未实现能力 | formal明确拒绝，不能靠mock能力表放行 | 同上 |
| G07 | 渲染后必需文件损坏/缺失 | postflight拒绝，正式输出未发布 | 同上 |
| G08 | 全部CLI/公开render与build路径 | 无绕过；退出码与提示一致 | test_export_cli.py |
| G09 | 非空发布目录/重复或并发发布 | 拒绝覆盖，既有文件hash不变 | 门禁集成测试 |
| Q01 | 父引言FULL、叶子缺失 | 内容完成度不增加，缺口仍在 | test_quality_summary.py |
| Q02 | 不存在完整要求清单 | coverage=unknown，不显示100% | 同上 |
| Q03 | 四个现有样本和原回归 | 保留数据，变化逐项解释，未假补证据 | 冒烟/回归 |
| Q04 | 实际草稿Word/PDF/HTML | 标识一致、问题可定位；页检记录与环境齐全 | 人工页面QA |

N05等正向/负向效果输入使用原创合成计算记录，不宣称其为真实专业设计；生成器未实现独立效果管线时，可以测试只读结果契约和保守输出，不得通过新增任意结果字段绕过登记。

## 10. 验收执行方法

基线命令（现在即可运行）：

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m cpswc.lint
git diff --check
```

下列是未来接口实施完成后的建议验收命令，当前版本尚无`--export-mode`：

```bash
PYTHONPATH=src python3 -m cpswc.renderers.package_builder samples/huinan_zhigu_v0.json --export-mode draft -o /ABSOLUTE/NEW/qa_huinan_draft
PYTHONPATH=src python3 -m cpswc.renderers.package_builder samples/huinan_zhigu_v0.json --export-mode formal -o /ABSOLUTE/NEW/qa_huinan_formal
```

`/ABSOLUTE/NEW/...`是占位路径，执行者须替换为新建的安全临时/本轮输出路径，不直接粘贴执行。formal在P0阶段应因具体未就绪项失败；验收要明确断言退出码和无发布结果，不把预期失败当执行失败，也不把所有异常都当正确阻断。

测试使用tmp_path和隔离registry/本地库夹具。不能依赖`data/`中某台机器的私有定额DB才能通过核心测试；真实DB/LibreOffice/字体/GIS相关集成测试单独标明依赖。缺依赖可以记录未执行，但不能在最终报告中计作PASS。

文档视觉验收：实际生成DOCX/PDF后渲染检查封面、含警示页、关键结论页、宽表/跨页表、附件页；记录页码和图片路径。有条件全页检查；只看几页就写全册通过是不允许的。输出仍是草稿，无需在P0做到正式排版全规范，但草稿身份必须清晰且不可因导出格式丢失。

## 11. 每批发布证据

保存task ID与test ID映射、运行环境和命令/退出码、变更文件清单、原测试差异理由、合成数据标识、实际生成文件、已检查页面、未执行测试、未解决生产缺口、适用RFC版本。未运行的测试写NOT_RUN，人工专业复核未发生写NOT_REVIEWED，不填写默认通过。
