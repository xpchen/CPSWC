# P0 文件级实施任务

版本：1.0｜前提：先读RFC和接口/验收文档。除P0-00只读核查外，实施须有RFC批准记录。

## 分批与依赖

| 批次 | 任务 | 批次成果 | 停点 |
| --- | --- | --- | --- |
| A：消除错误结论 | P0-00、01、02、03 | 反例基线、质量契约、未知态、保守正文 | 提交测试与前后对照，等待验收 |
| B：统一输入和版本 | P0-04、05、06 | 同源上下文、章节映射、冻结/失效 | 提交映射与迁移测试，等待验收 |
| C：安全交付 | P0-07、08、09 | 制品台账、发布门禁、诚实工作台 | 提交全量测试、实际草稿与阻断记录 |

依赖：00→01→02→03；01/03→04→05；04→06；05/06→07→08→09。允许在单个任务内迭代，但不跳过验收停点。不要一次性执行到P4。

跨批验收分层：A批完成值/条件/断言的单元与模板集成，B批完成上下文/结构/失效集成，C批完成发布端到端。N08在A批只验证确认记录绑定不同input hash即失效，B批再验证真实输入变化；F06在B批验证失效状态，C批验证正式拒绝；A04在P0-07验证失败台账，P0-08验证无正式发布。Q01/Q02在A批用显式要求夹具验证汇总算法，B/C批再接实际要求和界面。交付记录须把UNIT、INTEGRATION、END_TO_END分开；待后续集成的项不能提前标全部PASS。

代码路径以下均相对仓库根。新文件名是推荐设计，不是已存在能力；变更名字时同步任务和测试，不要保留两套同义模块。

## P0-00 基线、调用入口与治理确认

目标：在Claude接手时重新确认真实状态，防止基于过时代码实施。

读取：本目录全部文件、现有架构约束、`pyproject.toml`；搜索新的AGENTS/CLAUDE项目指令。不得输出`.claude/settings.local.json`等配置中的敏感值。

动作：

1. 记录HEAD、工作区已有修改、Python解释器和依赖可用性；保留用户文件。
2. 运行原测试、lint；记录INFO类型，不只记录“通过”。
3. 搜索`build_package`、`render_report`、`freeze_submission`、`project_narrative`、`_serialize_snapshot`和各CLI调用方，形成入口清单。
4. 用原创合成夹具复现：空资料肯定结论；缺借方值被当无借方；仅目标值导致达标；资料缺失导致N/A；更改项目名称未改变事实hash。先保留只读probe；引入失败测试时与对应修复一起交付，不用skip掩盖。
5. 建立`docs/report_production_plan/implementation/P0_BASELINE.md`及`DECISION_LOG.md`，记载与本计划的差异。
6. 没有RFC批准时停止在此，提交所需的范围确认；不修改生效治理文件。

禁止：覆盖samples、tests/baselines、既有output；为跑通演示更改事实；安装外部服务；自动清理环境。

验收：A00、A01；F01在本任务只复现当前缺陷，不要求尚未实施的修复通过。提交命令退出码、问题复现、入口清单及审批状态。数据变化导致本计划失效时，先出差异提案。

## P0-01 质量旁路与值状态：不再用FULL表示完成

目标：增设专业完成度的最小契约，保留渲染层兼容。

建议修改：

- 新增`src/cpswc/report_quality.py`：ValueState、Applicability、ContentState、EvidenceState、ReviewState、QualityFinding、SectionQuality、ReportQualitySummary及序列化。
- `src/cpswc/narrative/contract.py`：仅按需要新增可选绑定/稳定段落标识；默认UNASSESSED，不改变旧enum字符串含义。
- `src/cpswc/narrative/projection.py`：产出质量sidecar或由统一编排计算；旧full_count保留但标签为“已渲染块数”。
- 新增`tests/test_report_quality.py`。
- RFC批准后在`CORE_CONTRACTS.yaml`登记新增对象/ID语义或明确其为诊断内嵌记录；不得发明不受lint管理的跨对象命名空间。

实施：

1. 按04文档分离值、适用性、正文、证据、复核状态，禁止一个总状态混用。
2. 给缺失、非法、冲突、未证实来源、旧审核失效等finding稳定code和target_ref。
3. legacy snapshot可读但无来源记录的输入只能是unverified；不得补上系统自己虚构的confirmed_by。
4. 质量汇总以适用内容规范的叶子要求为分母；父标题引言不能计成一份完成成果。
5. 缺少内容规范时返回coverage=unknown和finding，不输出100%。百分比若保留，必须同时列unknown和unassessed数量。
6. 保留原结构校验；新增质量校验不声称能证明任意自然语言命题。

验收：S01—S05、Q01、Q02；旧dataclass调用仍可解析，旧数据不再自动获得专业“已完成”。

不做：通用工作流平台、用户角色后台、跨项目知识图谱、自动专家签署。

## P0-02 条件未知态与常规章节适用性

目标：资料不足、DSL错误和未触发不能再都表现为“不涉及”。

修改：`condition_engine.py`、`runtime.py`、`narrative/projection.py`、`renderers/document.py`的条件可见性辅助函数；`export_gate.py`接收未知义务；新增`tests/test_condition_unknown.py`。

实施：

1. 在ObligationResult保留triggered: bool|None，增加默认可选字段evaluation_status、missing_field_refs、diagnostic_code。错误不能回False。
2. 对现有有限DSL做依赖解析和类型检查。非必要不重写DSL；如确需解释器，限定现有表达式集合，不增加任意Python求值能力。无法安全处理的表达式返回UNKNOWN/ERROR。
3. 明确0和False为有效值，None/缺键不能经`or 0`、`or []`转换后当成事实。bare bool与Quantity值分别检查；NaN/inf/非法单位不能参与证明。
4. 按04文档处理逻辑未知态；允许保守UNKNOWN，禁止在依赖未知时产生未经证明的False。always触发与其他已明确条件不能因无关字段缺失全部丢失。
5. driven_by级联迭代至稳定，顺序无关；依赖unknown时保留unknown。缺失依赖或循环不能默认False；形成明确finding。此处不是引入通用DAG服务。
6. 常规敏感区说明、选址评价与“是否触发不可避让专题”分开。前两者不能只受redline_conflict控制；必要的专题仍由原义务投影驱动。
7. 敏感区空列表只表示提供了空列表；没有完整核查记录时不能生成全类型“经核查不涉及”。已明确False/空结果的义务逻辑不等于该输入已专业核验，来源状态另行阻断。
8. renderer、workbench、diff和CLI都能展示未知状态，不因旧`not in triggered`判断把它隐藏。

验收：U01—U07；另比较四个现有样本的义务差异并逐项解释。不能强行维持旧计数。

## P0-03 关键断言保护与目标/效果分离

目标：没有支持材料时，文字必须说明缺口，不作合理、可行、符合、已完成或达标的肯定判断。

优先修改模板：

- `sec_3_evaluation.py`、`sec_3_1_site_selection.py`
- `sec_2_5_sensitive_areas.py`
- `sec_4_topsoil.py`、`sec_5_disposal.py`
- `sec_7_5_benefit_analysis.py`、`sec_11_conclusion.py`
- `sec_0_overview.py`（汇总结论不能绕过下游缺口）
- `renderers/table_projections.py::project_six_indicator_review`
- 新增`tests/test_narrative_assertions.py`、`tests/test_target_effect_separation.py`。

实施：

1. 先清点全部已注册render函数中的“合理/符合/可行/已核查/全部用于/无需/均达到”等判断。检索只是定位手段，不是质量证明。输出模板覆盖清单及未审查状态。
2. 无条件结论替换为基于已确认输入的事实复述或具体缺口。空字典不得生成肯定结论，不能只把文字隐藏到脚注。
3. 规则引用只支持规范要求描述，不支持项目合规断言；art.*登记存在不证明制品已提供；ob.*触发不证明义务完成；sec.*关联不证明技术判断成立。
4. P0只建立关键断言的受控检查点：证据不足即NEEDS_EVIDENCE/NEEDS_REVIEW；涉及专业论证的正向结论必须有当前输入绑定的确认记录。缺专业结果时保守不作结论，不能让LLM新造理由。
5. 六率的目标只使用target绑定；设计效果需独立结果及过程；监测实测需独立时点与来源。旧`field.derived.target.*`不因命名或含actual_derived就自动当成实测/设计效果，先确认生产者及语义。
6. 若目前没有可信效果计算器，允许保留目标表、把效果标成待计算。不得为了正向测试临时建一套六率算法。
7. 不再把reducible/new简单称为“水土流失治理度”，不通过`min(...,100)`掩盖口径问题。只能在输入定义和比较口径均明确时给出对应量的算术描述；领域指标另待P2。
8. 所有关键声明测试同时检查正文、汇总、结论、表格，不只修一个模板。未改造模板的输出必须维持UNASSESSED/NEEDS_REVIEW，不能全册绿色。

验收：N01—N08。提供空资料、仅目标、有未达标效果三组前后对照；来源字段仍存在但内容变动时，旧审核不能支持新结论。

不做：增加通用套话、按字数填满章节、将其他项目结论复制进facts。

## P0-04 统一读取上下文和失效派生处理

目标：正文、表格、工作台、条件和导出看到相同的事实/派生选择及问题。

修改：新增`src/cpswc/snapshot_adapter.py`；`runtime.py`、`project_fact_sheet.py`、`fact_diff.py::_run_pipeline`、`renderers/package_builder.py`、`renderers/document.py`及表/正文入口。修改范围只限统一读取和诊断，不在本任务重写计算公式。

实施：

1. 实现04文档的只读BuildContext；所有入口复用；清点并移除新代码自己拼`_original_facts/_pre_stored_derived`的逻辑，保留旧snapshot输入适配。
2. 以FIR为登记依据制作别名表；确认stripable/strippable、topsoil fill/backfill、prediction total等实际语义后才映射。同义字段双填不一致时报CONFLICT，不采用静默优先级。
3. 数字必须带明确单位或来自有单位的登记契约；仅做必要的已确认换算。0不能失踪；bool不当数值；负值按字段约束处理，不全局截成0。
4. 当前成功计算结果优先。当前计算失败且存在旧derived时，旧值不能当fallback成功结果；隔离并显示stale。纯历史输入可以用于带警示草稿，但不能冒充当次计算。
5. `_original_facts`、fact_sheet、pre-stored derived、computed derived中同一字段不一致，留下冲突/选择依据。
6. `run_project`不原地修改调用者输入。价格enrich如保留，输出为带来源的计算/消费视图；P0不迁移投资整个子系统、不新设措施真源、不把机器enrich写成已确认facts。
7. 演示模数、默认时段、估算红线和未知源价格形成DEMO_ASSUMPTION/UNVERIFIED_INPUT finding。不会因为有source_note字符串就verified。
8. 序列化失败和enrich依赖异常不能静默；草稿可降级但必须留诊断，正式能力不可据此通过。

验收：I01—I06、F02。变更前后比较现有数值，所有数值改变要指出来源；“顺便校准金额”不属于本任务。

## P0-05 报告种类与章节结构映射

目标：用一个版本化内容清单统一章节要求、显示和覆盖率；先对齐结构，不宣称内容已写完。

修改：`governance/DisplayNumberingPolicy_v0.yaml`及必要的版本化替代文件、`narrative/projection.py`、`renderers/document.py`、`renderers/table_projections.py`的section绑定；建议新建`governance/ReportContentRequirements_v1.yaml`（RFC批准后才生效）；新增`tests/test_report_structure.py`。

实施：

1. 核对本地2026官方模板原件与公开正文，记录条款/页码定位、文件hash、核验状态；需要OCR时先校对。没有核验的条款不能补写为已verified。可先搭结构适配并保持UNVERIFIED_PROFILE。
2. 报告书以官方主体10章为基线。主要映射见04文档；第1章结论位于1.9，设计水平年/目标与投资效益位置需更正。不是简单删除第11章：既有stable ID保留，显示位置/父子关系迁移，并保留历史审查引用映射。
3. 两个章节词典与renderer目录树不能继续独立漂移；尽可能共享规范清单，或用校验强制一一对应。
4. 必需但未实现的章节/表图显示具体缺口并计入质量分母；不得因为模板没写就不计分。
5. optional章节须有适用性证据；遵守原章号不前移规则。未知不能按“不涉及”省略。
6. Species缺失/未知、旧样本声明2018格式与当前2026规则冲突时显示不兼容，不能从面积猜物种或改写样本。报告表renderer尚未实现时输出“报告表技术草稿，格式未就绪”，正式发布阻断，不能用报告书封面冒充。
7. 现有`rule.template_2026.section_11`等字符串不能只为通过resolver注册成“有效规范”；应移到核实的1.9或相应条款映射并记录模板版本变更。
8. 同步table section_id、cross-ref、审查意见定位、模板SPEC和测试；未知老引用显示orphaned/需迁移，不丢弃。

验收：R01—R05。输出“正式模板要求—stable ID—显示位置—实现状态”差异表，不以新增标题数作为完成依据。

不做：完整重写31个模板、所有地方模板分支、MatrixForm全量实现或真实CAD/GIS制图。

## P0-06 冻结输入、哈希与审核失效

目标：修改任何被报告或审核依赖的输入后，不能复用过期的通过状态。

修改：`runtime.py::RuntimeSnapshot/FrozenSubmissionInput/freeze_submission/create_version`、`snapshot_adapter.py`、`fact_diff.py`、package序列化；新增`tests/test_submission_freeze.py`。

实施：

1. 明确保留原始facts与有效计算输入，固定canonical JSON算法及hash_schema_version，拒绝NaN/inf；不要随意排序有语义的list。
2. fact_snapshot_hash基于规范化事实内容，不再仅计算derived_fields。生成输入hash覆盖facts、pre-stored derived来源与状态、项目静态profile、规则/registry/模板/计算版本以及实际消费的source checksum；运行时间和临时输出路径排除。
3. 时间戳、运行ID保留为审计元数据；同语义输入重复执行可有不同run ID，但semantic hash应相同。DOCX ZIP字节和PDF元数据不要求天然完全相同，语义重现与文件完整性分开验收。
4. 资料文件内容变动，即使文件名、数值不变，生成输入hash也要变化；缺原件无法核对checksum要返回未核验。
5. freeze必须明确生命周期冻结含义；创建dataclass不等于“专业校审通过”。人工确认记录绑定input hash与目标，不能由build函数自动生成。
6. P0采用保守全量失效：相关输入/profile/template变化令之前的质量确认、签署适用性重新检查；不实现精细增量DAG。
7. 旧包保留旧schema/hash语义只读；加载旧包显示legacy_unverified。不能重算新hash后覆盖旧manifest，造成历史签署似乎适用于新包。
8. 不修改真实签名材料；仅保证签署证据与版本关联。签署用草稿和最终包不同文件hash，需记录其对应关系和非技术变更检查。

验收：F01—F06；名称改变、事实改变、规则改变、来源内容改变四种场景，输入hash必须按契约响应。

## P0-07 制品台账与生成异常可见化

目标：required清单与实际生成/导入的文件可逐一对应，不能存在“需要=已具备”的混淆。

修改：`renderers/package_builder.py`、`renderers/document.py`、`geo_pipeline.py`、`report_quality.py`；必要时新增`src/cpswc/artifact_inventory.py`；新增`tests/test_artifact_inventory.py`。

实施：

1. 按04契约为每个required artifact记录提供方式、路径或内嵌锚、文件hash、状态、验证结果及diagnostic。
2. 顶层附件包只有在所需子项有效时才能完成。一个Word内嵌多张表可以对应多个artifact，但需明确table ID/位置，不凭同一个文件存在就认为所有表完成。
3. 捕获DOCX/PDF/GIS失败并形成finding，记录原因。技术错误可以允许保留已有草稿，但不能被吞掉。
4. 验证实际文件存在、非空、可解析、类型符合要求、hash与本轮一致；具体图件语义/制图质量仍需专门验证，不把这些基础检查当成专业验收。
5. 中心点示意图明确标DEMONSTRATION，不计作正式边界制品；EPSG字符串不能替代真实几何与坐标核验。
6. 目录中的上轮残件不能自动补齐本轮缺件；人工材料须通过显式登记导入，不扫描目录“猜”对应关系。
7. 不创建空白pdf、空shp或只有标题的docx来满足数量；参考图片未授权/不完整也不得充正式成果。

验收：A02—A06。用mock测试工具失败，再用本机实际依赖生成一份明确草稿，区分mock通过和真实输出验证。

## P0-08 草稿/正式发布模式与原子发布

目标：所有对外入口明确草稿与正式结果，BLOCK绝不发布正式成果。

修改：`export_gate.py`、`renderers/package_builder.py`、`runtime.py`CLI、`renderers/document.py`CLI、`demo.py`及调用方；在批准范围内更新`ProtectedBoundaryPolicy_v0.yaml`模式策略；新增`tests/test_formal_export_gate.py`、`tests/test_export_cli.py`。

实施：

1. 按04文档增加export_mode=draft/formal；旧build_package调用默认draft并明确标识。所有CLI和直接render_report调用默认草稿，不能成为正式门禁后门。
2. draft保留原接口的Path返回值，允许有BLOCK的可读草稿；manifest写is_submittable=false，Word/PDF/HTML显著标“审阅草稿—不可送审”，带缺口清单和降级信息。
3. formal进行前置检查：适用profile、未知义务、关键值及来源、关键断言、冻结和当前审核、required assurances、必要计算、实现能力。缺输入不得自行补全。
4. required保障的PROVIDED必须关联当前证据与确认记录；裸bool不满足正式发布。P0不提供豁免所有BLOCK的force/bypass；已有PROTECTED override槽位不自动意味着可实现无人审批豁免。
5. 正式输出在同文件系统新staging目录生成；完成后检查实际制品、图表/正文一致性和后置验证，再原子发布到新目录。必须禁止覆盖非空已有发布目录。
6. 任一步失败：返回结构化诊断和非零退出码，不留下“可正式交付”的包。可保留明确failed的诊断/staging供排错，但不能用正式manifest或成功提示包装。
7. 门禁失败不自动退回draft并显示成功；用户要草稿须显式选择。输出转换工具缺失、PDF打不开、必需附图缺失，均不能formal成功。
8. P0的生产能力清单仍有未实现项，实际项目formal默认应被相关能力/内容检查拒绝。允许用原创合成夹具做门禁策略的正向单测，不允许把mock验证作为真实生产放行证明。
9. 文档签署草稿先于真实签名，流程避免循环依赖；签章上传/真实性确认在本阶段可以是文件侧车导入，不扩展账户权限平台。

验收：G01—G09。至少验证package CLI、runtime --package、document CLI和Python公开函数；覆盖同一输出目录残留、并发/重复发布失败后的保护。

## P0-09 诚实展示、回归与交接

目标：用户和后续实施者不会把渲染覆盖率或演示数据看成生产就绪。

修改：`renderers/workbench.py`、`renderers/diff_workbench.py`、`docs/DEMO_README.md`、`docs/PRODUCT_BRIEF.md`、`scripts/run_showcase_demo.sh`及最少必要的前端标签；新增`tests/test_quality_summary.py`。前端静态mock不接后端时必须明确“演示数据”，不要新造质量百分比。

实施：

1. 展示缺资料、未决义务、未核验结论、缺制品、未审查内容、生成故障、旧审核失效分别数量与定位。
2. 旧full_count只表示文字已渲染；新的适用要求分母包含未实现内容。父章节引言不计完成。
3. 使用统一质量summary，不在UI复制业务判断；断言和制品缺口能回到source/section/artifact。
4. 同步演示脚本为显式draft，不覆盖用户输出；文档不再泛称完整生产报告或每句话已证明。
5. 新建一组临时输出进行四样本冒烟，保留缺口，输出差异说明；不为了“全绿”改写样本真实性。
6. 按04验收矩阵运行，按06交付模板提交实际文件、前后截图/页检、命令退出码、未解决问题。
7. 停止在P0结束，不未经确认进入P1数据导入或P2引擎建设。

验收：Q01—Q04及全部P0测试。旧74测试是基线而非上限；允许有明确理由的语义期望调整，不允许降低断言或仅批量更新快照。

## 公共停止条件

遇到用户未提交改动与任务重叠、治理实质冲突、规范原文缺失/相互矛盾、需新增项目事实、模型不能安全表达专业判断、新外部依赖/服务、真实签章/确认记录缺失时，完成不依赖这些条件的工作并提交具体问题；不得靠猜测继续发布。资料缺失不阻止P0修复，但会阻止把真实报告标为生产完成。
