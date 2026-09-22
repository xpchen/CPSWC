# P0 Batch A 交付

日期：2026-09-20（初版）／2026-09-20 修正版｜模板依据：`06_CLAUDE_HANDOFF.md` 第 6 节

> **修正版说明**：项目负责人对 A 批初版做了独立验收，在既有 217 条测试之外补构造反例，发现四个漏洞。本版记录这四项的修复与回归测试，并更正初版交付记录中一处不准确的证据表述（见"§ 验收修正"与"§ 对初版交付记录的更正"）。

## 版本与授权

| 项 | 内容 |
| --- | --- |
| 开始 HEAD | `adba408`（与计划核查基线一致） |
| 结束 HEAD | `adba408`（**未提交、未 push、未开 PR**；改动留在工作区） |
| 工作区状态 | 用户原有的 4 项未跟踪内容全部保留未动：`docs/CPSWC_商务白皮书…textClipping`、`docs/SLT447-2026…pdf`、`docs/report_production_plan/`、`output/` |
| 批准的 RFC | RFC-RP-001 v1.0，**仅 A 批**（P0-00/01/02/03），见 `DECISION_LOG.md` 条目 002 |
| 批准附加要求 | ①测试剧本严格可复验 ②严谨诚实，不得以绿灯掩盖缺口 |
| 环境 | Python 3.14.3；PyYAML / jinja2 / python-docx / matplotlib 可用；reportlab / PyMuPDF / pyshp / pyproj 不可用；LibreOffice `soffice` 可用 |
| 与原计划的差异 | 5 项差异记录在 `P0_BASELINE.md` 第 6 节；本批实施中新增 2 项决策，见 `DECISION_LOG.md` 条目 004、005 |

## 本批任务

| Task ID | 状态 | 变更文件 / 符号 | 对应 Test ID | 证据 |
| --- | --- | --- | --- | --- |
| P0-00 | DONE | `implementation/P0_BASELINE.md`、`DECISION_LOG.md` | A00、A01、F01(复现) | 12 项诊断全部复现或核实 |
| P0-01 | DONE | **新增** `src/cpswc/report_quality.py`；`narrative/contract.py`（新增 `ContentRole` / `AssertionClass` / `content_role` / `applicability` / `quality_findings` / `paragraph_id` / `review_refs`）；`narrative/projection.py` 产出 quality sidecar | S01—S05、Q01、Q02 | `tests/test_report_quality.py` 38 passed |
| P0-02 | DONE | `condition_engine.py`（三值 AST 解释器 + 闭集校验 + 环检测）；`runtime.py`（`unknown_obligations` / `obligation_applicability` / `quality_input_hash`）；`narrative/projection.py`（适用性三分）；`export_gate.py`（GATE_005）；`renderers/document.py`、`renderers/workbench.py`、`fact_diff.py`（展示未知态） | U01—U07 | `tests/test_condition_unknown.py` 35 passed |
| P0-03 | DONE | **新增** `src/cpswc/narrative/evidence.py`；改造 9 个模板 + `table_projections.project_six_indicator_review`；清点表 `TEMPLATE_ASSERTION_INVENTORY.md` | N01—N08 | `tests/test_narrative_assertions.py` 53 passed；`tests/test_target_effect_separation.py` 21 passed |
| A 批验收修正 | DONE | `report_quality.py`（复核记录完整性 + `REVIEW_INCOMPLETE` + `ledger_from_snapshot`）；`narrative/evidence.py`（`judgment` 前提与阻断）；`condition_engine.py`（有限性 / 成员属性 / 分支级未知）；`sec_7_5` + 六率表（候选效果） | R-1—R-4 | `tests/test_a_batch_review_regressions.py` 41 passed |

**未在本批范围**：P0-04—P0-09（B/C 批）。未激活 `registries/reserved/`；未改动任何 registry、governance 生效文件、samples、`tests/baselines`、用户 `output/`。

## 实际执行的验证

| 命令 | 实际退出码 | 结果 | 说明 |
| --- | --- | --- | --- |
| `PYTHONPATH=src python3 -m pytest -q` | 0 | **262 passed** | 原 74 + 新增 188（其中验收修正新增 45） |
| `PYTHONPATH=src python3 -m pytest tests/test_investment_import.py tests/test_quota_connector.py tests/test_table_projections.py -q` | 0 | 74 passed | 原有测试**一条未改、一条未删** |
| `PYTHONPATH=src python3 -m cpswc.lint` | 0 | ERROR=0 WARN=0 PENDING=0 INFO=26 | 与基线完全一致 |
| `PYTHONPATH=src python3 -m cpswc.renderers.package_builder samples/huinan_zhigu_v0.json -o <scratch>/pkg_huinan` | 0 | 18 个文件，含 DOCX/PDF/3 张 PNG | 输出在会话临时目录，未写入仓库 |
| `git diff --stat adba408 -- src tests` | 0 | 18 改 + 6 新增 | 见下节 |

**未执行**（NOT_RUN，如实记录）：

- 制品台账、草稿/正式模式、原子发布相关验收（A02—A06、G01—G09）——属 C 批，本批未实现，不作 PASS。
- 结构映射验收（R01—R05）、统一上下文与哈希验收（I01—I06、F02—F06）——属 B 批。
- 人工专业复核：**NOT_REVIEWED**。本批没有任何真实工程师对输出内容作技术确认。
- 逐页视觉 QA：只做了文本层抽查（见"成果检查"），未做全册页面核对。

## 关键反例前后对照

全部使用原创合成夹具或既有样本，**未修改任何样本文件**。

### 1. 空输入仍下肯定结论（D02 / 验收 N01）

| | 旧 | 新 |
| --- | --- | --- |
| `sec_11_conclusion.render({}, {}, set(), {})` | `render_status=full`，`validate_block` **0 错误**，正文："综上所述，—的水土保持方案编制依据充分，各项防治指标目标值符合 GB/T 50434-2018 的要求""本方案各项内容符合现行法律法规和技术标准要求，水土保持措施布局合理，投资估算依据充分" | 4 段全部 `GAP_STATEMENT`/`FACT_RESTATEMENT`；0 个 `PROJECT_JUDGMENT`；5 条诊断（4×`VALUE_MISSING` + 1×`ASSERTION_UNSUPPORTED`），每条带 `missing_input_refs` |
| `sec_3_evaluation.render_earthwork_balance({}, {}, set())` | "本项目挖方总量—……**项目无需外借土石方**。可剥离表土—，**全部用于后期绿化覆土**。综上，本项目**土石方平衡合理，弃方有明确去向，借方有可靠来源**，表土剥离利用方案可行。" | "土石方平衡缺少基础数据……缺少 5 项必需输入（逐一列出 field id）""借方数据缺失，无法判断本项目是否需要外借土石方""……须由水土保持工程师对照土石方平衡表与现场资料复核确认；复核记录形成前，本节不作上述结论。" |
| `sec_4_topsoil.render_stripping({}, {}, set())` | "**经现场踏勘**，项目用地范围内无可剥离表土" | "表土剥离数据不完整，无法说明剥离范围与剥离量：缺少 3 项必需输入（…）"——不再编造现场踏勘 |

### 2. 缺失 vs 明确为 0（D05 / 验收 N03、U01、U02）

| 输入 | 旧 | 新 |
| --- | --- | --- |
| 借方字段完全缺失 | `ob.borrow_site.land_use_approval` → `not_triggered`；正文"项目无需外借土石方" | 义务 → `unknown`（`UNKNOWN_MISSING_INPUT`，点名 `field.fact.earthwork.borrow_source_type`）；正文"借方数据缺失，无法判断…" |
| 借方明确填 0 | 同上，**完全不可区分** | 义务 → `not_triggered`（`EVALUATED`）；正文"本项目填报借方量为 0，即不从项目区外借取土石方" |

### 3. 目标值当成绩（D03 / 验收 N04、N05、N06）

> **本节为勘误后版本。** 初版此处给出的"旧：达标×6"对照是在"合并了 derived"的快照形态下测出的，与当前包管线的实际渲染不同。下表按**两种读取口径分别给出实测值**，不再混用。原因见 `DECISION_LOG.md` 条目 007。

`samples/huizhou_housing_v0.json` 的六项指标复核表。之所以要分两种口径，是因为系统当前**存在三套 derived 读法**（条目 007）：`run_project` 评估义务用"facts + pre-stored derived + 计算 derived"，而 `RuntimeSnapshot.derived_fields` **只含计算 derived**，正文与表格读的正是后者。

**口径 A — 合并 derived**（`runtime` 评估义务、`export_gate`、`fact_sheet` 实际使用的口径）：

| 列 | 基线 `adba408` | A 批初版 | A 批验收修正后 |
| --- | --- | --- | --- |
| 达标判定 | `达标`×6 | `待复核`，`待计算`×5 | `待确认效果来源`×6 |
| 实现值 | `99.47 / 1.0 / 99 / 93 / 99 / 25` | `99.47`，`待计算`×5 | 6 项全部保留原值并标注来源，如 `1.0（候选·待确认，源自 value）` |

基线那一行里的 `1.0` 正是样本中的 `target_by_standard: 一级 = 1.0`——**目标在跟自己比较**，判出"达标"。这个缺陷真实存在。

**口径 B — 当前包管线实际渲染**（`rendered/report_v0.docx` 里那张表，只读计算 derived）：

| 列 | 基线 `adba408` | A 批验收修正后 |
| --- | --- | --- |
| 实现值 | `—`×6 | `待计算`×6 |
| 达标判定 | `—`×6 | `待计算`×6 |

即：在实际出包路径上，这 6 个值**从来没被读到过**，所以"达标×6"没有出现在任何一份实际生成的 Word 里。缺陷被另一个问题（三套读法）掩盖了。

**勘误结论**：

- 初版交付记录声称"实际包里旧为达标×6"——**这一表述不准确**，已更正为上表。
- 目标/效果混淆这个缺陷**本身成立**，且在 `export_gate`、`fact_sheet` 的口径下是活的。
- 两个问题都要靠 P0-04 统一读取上下文根治，已列入 B 批必办（条目 007）。

叙述层（不受口径影响，两种读法下结论一致）：仅给加权目标、无任何效果数据时，旧输出"各项指标可达到上述目标值要求""各项防治目标可以实现"；新输出"本轮尚无设计水平年各项指标的效果计算结果，因此无法判定是否达到上述目标值。目标值不能替代效果计算"。

### 4. 空清单当核查结论（验收 S03、N02）

`{"field.fact.natural.other_sensitive_areas": []}`：

- 旧：`sec_2_5` 输出"经逐项排查，项目区不涉及 流域管理范围、河湖管理范围、…等水土保持敏感区"；`sec_3_1` 输出"本项目不涉及生态保护红线、自然保护区等敏感区域，选址符合水土保持相关法律法规要求"。
- 新：两处都改为复述"填报清单为空"+ 说明逐项核查需要什么（核查范围、材料版本、确认记录），并登记 `SOURCE_UNVERIFIED`（BLOCK）。

### 5. 复核记录随输入失效（验收 N08）

构造一条 `CONFIRMED` 复核记录绑定旧输入 → 只改 `field.fact.earthwork.spoil` 的值（字段名不变）→ 结论段自动撤回为待复核，登记 `REVIEW_STALE`；`evaluate_report_quality` 的 section `review_state` 同步变 `STALE`。

### 6. DSL 语义漏洞（验收 U03）

`field.x.value >> 0` 在 Python 里是右移：旧实现在字段有值时会**悄悄算出 True**。新增闭集 AST 校验后判 `ERROR_DSL`，诊断写明"表达式含 DSL 不支持的语法节点 BinOp"。同一校验也拒绝 `__import__("os").system(...)` 这类写法。

### 哪些只做了 mock、哪些实际生成

- 复核记录、内容规范清单、效果值：**合成夹具**，仅用于验证契约行为，不代表任何真实专业成果。
- 四个既有样本的投影、六项指标表、DOCX/PDF/PNG：**本机实际生成**（见下节）。

## 成果检查

实际生成：`<会话临时目录>/pkg_huinan/`（18 个文件，未写入仓库）

| 文件 | 检查结果 |
| --- | --- |
| `rendered/report_v0.docx` | 258 段、21 张表、16240 字符；文本层抽查：`依据充分` 0 次、`无需外借土石方` 0 次、`经现场踏勘` 0 次；`复核记录形成前` 4 次、`待计算` 2 次、`不得按不涉及处理` 1 次 |
| `rendered/formal_tables_v0.docx` | 概览表已含"适用性未知义务数"行 |
| `rendered/report_v0.pdf` | 由 soffice 转出，存在 |
| `rendered/figures/*.png` | 3 张，**仍是 matplotlib 示意图**，本批未加 `DEMONSTRATION` 标识（属 P0-07，C 批） |
| `workbench.html` | 新增"适用性未知"卡片，逐条给出缺失字段名 |

**未提供或未实现的必需制品**：真实空间数据、完整附件包、签署材料——本批全部未涉及。

**专业人工复核状态**：**NOT_REVIEWED**。

**视觉检查范围**：仅文本层与表格单元格抽查，**未做逐页排版核对**。

## 回归与兼容

### 四个样本的变化与逐项解释

| 样本 | 触发 | 未触发 | 未知 | FULL | 骨架 | 不适用 | 正文字符 | 契约校验错 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| huinan_zhigu_v0 | 8→8 | 14→13 | 0→**1** | 35→37 | 0→0 | 3→**1** | 5380→6395 | 0→0 |
| huizhou_housing_v0 | 14→14 | 8→8 | 0→0 | 38→38 | 0→0 | 0→0 | 6241→6920 | 0→0 |
| shiwei_logistics_v0 | 6→6 | 16→13 | 0→**3** | 32→34 | 0→**3** | 6→**1** | 4897→6009 | 0→0 |
| disposal_highrisk_v0 | 10→10 | 12→8 | 0→**4** | 35→37 | 0→0 | 3→**1** | 5197→6621 | 0→0 |

- **触发数一条未减**。三值逻辑保证 `TRUE OR UNKNOWN = TRUE`，本该要求的制品不会因为另一个分支缺字段而消失。
- **未触发 → 未知共 8 条**，全部是依赖字段缺失，逐条原因：

| 样本 | 义务 | 缺失依赖 |
| --- | --- | --- |
| huinan | `ob.disposal_site.land_use_approval` | `field.fact.construction.temp_topsoil_site` |
| shiwei | `ob.disposal_site.land_use_approval` / `.site_selection` / `.separate_prevention_zone` | 同上 |
| disposal_highrisk | `ob.unavoidability.redline_conflict` | `field.fact.natural.key_prevention_treatment_areas`、`field.fact.natural.other_sensitive_areas` |
| disposal_highrisk | `ob.borrow_site.land_use_approval` / `.external_purchase_evidence` | `field.fact.earthwork.borrow_source_type` |
| disposal_highrisk | `ob.topsoil.reuse_evidence` / `.soil_improvement_required` / `.external_topsoil_source` | `field.fact.topsoil.excavation`、`field.fact.topsoil.fill` |

- **不适用数下降**（3→1 / 6→1 / 3→1）：敏感区说明与选址选线评价从"红线冲突义务的附属品"解耦为常规章节；shiwei 另有 3 节因依赖义务未知改判为骨架 + UNKNOWN，**没有被当成不涉及**。
- **正文字符增加约 19%**：增量全部是缺口说明与待复核说明，不是新增内容。**字符数不作为质量指标**。
- **契约校验错误保持 0**：新增的"`PROJECT_JUDGMENT` 必须有 `review_refs`"规则下，没有一个模板违规。

### 原测试与 lint

- 原 74 个测试：**一条未改、一条未删、一个快照未批量更新**，全部通过。
- lint：INFO=26，与基线逐条相同（全部是 `ArtifactRegistry` 引用 `engine.*` 扩展命名空间）。

### API / 序列化 / CLI 变化

| 变化 | 兼容性 |
| --- | --- |
| `ObligationResult` 新增 5 个**有默认值**的字段 | 旧位置参数调用不受影响 |
| `ConditionEngineResult` 新增 `unknown` 集合 | 旧消费者读 `triggered` / `not_triggered` 仍可用；但**未知不再出现在 `not_triggered` 里**，这是有意的语义变更 |
| `RuntimeSnapshot` 新增 `unknown_obligations` / `obligation_applicability` / `quality_input_hash` | 均有默认值；`_serialize_snapshot` 输出多 3 个键 |
| `RuntimeManifest` 新增 `obligations_unknown` | 有默认值 |
| `NarrativeParagraph` / `NarrativeBlock` 新增可选字段 | 旧 dataclass 构造方式不变 |
| `transform_dsl` 输出形态改变（改为 6 个取值函数调用） | 仅内部使用；`py_expr` 是展示字段，语义未变 |
| `check_export_readiness` 新增 GATE_005（WARN） | 有未知义务的项目 verdict 可能从 PASS 变 WARN |
| 模板 render 函数新增 `ledger` / `unknown` 关键字参数 | 全部有默认值，且原签名已带 `**kwargs` |

### 是否修改用户原文件或历史输出

**否。** `samples/`、`tests/baselines/`、`registries/`、`governance/`、`output/` 全部未改动，`git status` 可核。

## 剩余风险与下一批条件

### 必须先修复（阻断生产，但属 B/C 批）

1. `run_project` 仍会**原地改写调用者输入**（`field.fact.investment.measures_registry` 被 quota enrich 写回）——P0-04。
2. `fact_snapshot_hash` 仍散列 `derived_fields` 而非 facts，改项目名哈希不变——P0-06。
3. `build_package` 遇 BLOCK 仍继续产包，没有草稿/正式之分——P0-08。
4. `_check_assurances` 仍硬编码 WARN，`provided=True` 裸 bool 即算满足——P0-08。
5. 附图仍是 matplotlib 示意图，未标 `DEMONSTRATION`——P0-07。

### 不阻断本批但阻断生产

- **18 个模板未审查**（见 `TEMPLATE_ASSERTION_INVENTORY.md`），仍用 `_v(..., default="—")` / `_num(..., default=0.0)`。建议与 P0-04 的 `BuildContext` 一起改，避免两套取值方式并存。
- `evaluate_report_quality` 已实现并有测试覆盖，但**尚未接入包构建与工作台展示**——按批次约定属 P0-09。
- `quality_input_hash` 是 A 批临时指纹（`DECISION_LOG` 条目 004），P0-06 完成后应由 `generation_input_hash` 取代。
- `sec.conclusion` 仍引用 `rule.template_2026.section_11`；2026 模板是否存在第 11 章**本批未核验**，属 P0-05。

### 需用户 / 工程师确认

1. **`field.derived.target.*` 的两套约定**（`DECISION_LOG` 条目 005）：同一结构里 `value` 有时是目标、有时是效果。本批按保守规则只认 `actual_derived`，代价是 4 个可能真实的效果值显示为"待计算"。需工程师逐项确认语义。
2. 别名语义（条目 003）——已确认走 CONFLICT 路线，实施在 B 批。

### 下一批建议范围

按计划的 B 批：P0-04（统一读取上下文 + 别名冲突 + 输入不被原地修改）、P0-05（章节结构映射）、P0-06（双哈希与审核失效）。建议 P0-04 顺带把剩余 18 个模板的取值方式统一到 `SectionEvidence`。

---

# § 验收修正（2026-09-20，A 批第二次提交）

## 验收意见与处理结果

| # | 验收发现 | 状态 | 位置 |
| --- | --- | --- | --- |
| R-1 | 复核记录只校验 hash，不校验完整性；空壳记录（`reviewer_ref`/`reviewed_at`/`evidence_refs` 全空）可输出专业肯定结论 | **已修复** | `report_quality.py::ReviewRecord.completeness_gaps` / `ReviewLedger.review_state` |
| R-2 | 复核记录可以盖过已知的不达标与数据缺失 | **已修复** | `narrative/evidence.py::SectionEvidence.judgment`（新增 `preconditions` + `blocking_findings`）；`sec_7_5_benefit_analysis` 声明三条前提 |
| R-3 | 非法数值、清单成员缺关键属性仍被判成"不触发" | **已修复** | `condition_engine.py::_Reader.value` / `any_in` / `count_distinct` / `_member_attr` |
| R-4 | 三值逻辑遇非法输入抛异常退出，丢掉另一分支已确定的 True | **已修复** | `condition_engine.py::_eval3`（异常分型 + 分支级 UNKNOWN） |

四项反例均先复现、后修复，全部有回归测试：`tests/test_a_batch_review_regressions.py`（41 条）。

## 逐项前后对照

### R-1 空壳复核记录

| 输入 | 修复前 | 修复后 |
| --- | --- | --- |
| `verdict=CONFIRMED` + 匹配 hash，其余全空 | `review_state=CONFIRMED`，`supports_judgment=True` | `NEEDS_REVIEW`，`supports_judgment=False`，诊断 `REVIEW_INCOMPLETE`(BLOCK) 列出缺哪几项 |
| 只有审核人 / 有人有时间无证据 / 证据引用悬空 / 所引证据被否决 | 同上，全部放行 | 全部拦下 |
| 记录完整（人 + 时间 + 可解析证据 + hash） | 放行 | 仍放行 |
| `verdict=REJECTED` 且记录不完整 | — | 仍按 REJECTED 处理（否决方向保守，不要求额外证据） |

边界：只校验记录是否**成形**，不声称验证了签名真实性或身份。新增诊断码 `REVIEW_INCOMPLETE` 已记入 `DECISION_LOG` 条目 006。

### R-2 复核记录不是通行证

`judgment()` 现在要求**三个条件同时成立**才输出肯定结论：

1. 有当前有效的复核记录（CONFIRMED + 绑定当前输入 + 记录完整）；
2. 本节没有未解决的数据类 BLOCK 诊断（缺值/非法/冲突/适用性未知/目标效果混淆/复核失效或不完整）；
3. 调用方声明的领域前提全部成立。

验收原始反例（目标 95 / 效果 80 / 另五项缺失 + 一条匹配的复核记录）：

- 修复前：同一节同时出现"该指标未达到目标值"和"各项防治目标可以实现"。
- 修复后：无 `PROJECT_JUDGMENT` 段落；结论段变为"…本节暂不作上述结论。（未成立的原因：5 项指标尚无效果计算结果；1 项指标的候选效果值语义未确认；本节尚有 6 项未解决的阻断性问题（TARGET_EFFECT_CONFLATED、VALUE_MISSING））"。
- 另单独登记一条诊断，说明"已有当前输入的复核记录，但本节仍有 N 项未解决的阻断性问题"——避免被误读成"没人复核过"。

两条防止过度收紧的护栏也有测试覆盖：WARN 级诊断不阻断；同一节里指向不同 target 的两个子判断互不牵连。

### R-3 非法数值与成员属性

| 输入 | 修复前 | 修复后 |
| --- | --- | --- |
| `{"value": "NaN"}` 上 `> 0` | `False` / EVALUATED | `None` / UNKNOWN_INVALID_INPUT |
| `{"value": "-Infinity"}` | `False` / EVALUATED | `None` / UNKNOWN_INVALID_INPUT |
| `{"value": "inf"}` | **`True`** / EVALUATED（凭空伪造一个触发） | `None` / UNKNOWN_INVALID_INPUT |
| `ob.disposal_site.land_use_approval` + 清单 `[{}]` | `False` / EVALUATED | `None` / UNKNOWN_INVALID_INPUT，诊断写明"清单成员缺少属性 'outside_permanent_land'" |
| 清单 `[{}, {"outside_permanent_land": true}]` | — | `True`（成员级三值：有一个确定命中就是 True） |
| 清单 `[]`（明确空） | `False` | `False`（不变——提供空清单是可确定的结果） |

`"inf"` 这一条是验收意见之外发现的更严重变体：它不是漏判，而是**伪造触发**。

### R-4 分支级未知

| 表达式 `A OR/AND B`，B 为非法类型 | 修复前 | 修复后 |
| --- | --- | --- |
| A=True，OR | `None`（丢掉已确定的 True） | `True` + 分支诊断 |
| A=False，OR | `None` | `None` |
| A=True，AND | `None` | `None` |
| A=False，AND | `None` | `False` + 分支诊断 |
| DSL 语法错（`>>`） | ERROR | 仍为 ERROR（输入错误降级为分支未知，语法错误不降级） |

结果可确定时，读值过程中登记的缺失/非法**照实保留在诊断里**（`diagnostic_message` 写"结果不受这些问题影响，但输入仍需修正"），不会因为结论没变就把问题抹掉。

## 六率：按验收建议改为"保留原值 + 标注来源 + 不进比较"

验收建议原文："保留原值及来源，在诊断中标为'历史值，语义待确认'，暂不进入效果比较……`actual_derived` 也只是候选效果输入，名称本身不证明可信。"

实现：

- `value` 与 `actual_derived` **一律降级为候选效果输入**，不再凭字段名区分可信度。
- 候选值**照实显示并标注来源键**：`99.47（候选·待确认，源自 actual_derived）`、`1.0（候选·待确认，源自 value）`。判定列为"待确认效果来源"。
- 每个候选值登记一条 `TARGET_EFFECT_CONFLATED`(BLOCK)，说明需要确认的是什么（目标值 / 设计预测效果 / 监测实测值，及时段、口径、计算依据）。
- 只有该字段有**可解析、未被否决的证据记录**（`EvidenceState.READY`）时才进入比较：低于目标 → 未达标；不低于目标 → 待复核。任何情况下都不出现"达标"。

对 N05 的影响：验收前用"有 `actual_derived` 就比较"演示未达标，现在必须先构造完整证据记录。**这是前置条件变严，不是断言放松**——未达标仍必须被判出来，且多了一层"来源未确认时连比较都不做"的保护。相应测试已重写并在文件头说明理由。

## 对初版交付记录的更正（已完成勘误）

初版"关键反例前后对照 § 3"的六率对照混用了两种 derived 读取口径。**该节已按两种口径分别重写**，见上文 § 3（含勘误说明）。

追查原因发现的新问题已记入 `DECISION_LOG` 条目 007：惠州样本 9 个 pre-stored derived 中有 **8 个**（含全部六率）对正文和表格不可见。**不在 A 批修**——在 `BuildContext` 落地前单独改会让多处输出变化而没有统一纪律约束；已列入 B 批 P0-04 首要任务。

## 修正后的验证

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `PYTHONPATH=src python3 -m pytest -q` | 0 | **262 passed**（原 74 + A 批 143 + 验收修正 45） |
| 原 3 个测试文件单独运行 | 0 | 74 passed，仍是一条未改、一条未删 |
| `PYTHONPATH=src python3 -m cpswc.lint` | 0 | ERROR=0 WARN=0 PENDING=0 INFO=26，与基线一致 |
| `git diff --check` | 0 | 通过 |
| 四样本对照 | — | 触发/未触发/未知/FULL/骨架/不适用 **与 A 批初版完全一致**（见下） |
| 包构建（惠州） | 0 | 270 段、22 表、17655 字符；正文出现"未成立的原因" 10 次、"各项防治目标可以实现" 0 次 |

四样本与基线 `adba408` 的对照（与初版相同，说明 R-3/R-4 修的是样本没踩到的洞——这正是验收方需要构造反例才能发现的原因）：

| 样本 | 触发 | 未触发 | 未知 | FULL | 骨架 | 不适用 | 契约校验错 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| huinan_zhigu_v0 | 8→8 | 14→13 | 0→1 | 35→37 | 0→0 | 3→1 | 0→0 |
| huizhou_housing_v0 | 14→14 | 8→8 | 0→0 | 38→38 | 0→0 | 0→0 | 0→0 |
| shiwei_logistics_v0 | 6→6 | 16→13 | 0→3 | 32→34 | 0→3 | 6→1 | 0→0 |
| disposal_highrisk_v0 | 10→10 | 12→8 | 0→4 | 35→37 | 0→0 | 3→1 | 0→0 |

## 测试期望的修改及理由

| 文件 | 改了什么 | 为什么不是降低要求 |
| --- | --- | --- |
| `test_narrative_assertions.py` | 复核记录夹具由"只填 hash + 审核人"改为完整记录（含可解析证据） | 契约变严，夹具跟上。空壳夹具现在会被正确拒绝——这本身就是 R-1 想要的行为 |
| `test_target_effect_separation.py` | N05/N06 的比较用例改为先构造已核验证据 | 比较的**前置条件**变严（必须先确认来源）。"未达标必须判出来"的断言原样保留，另加"来源未确认时不比较"的新断言 |
| 同上 | 新增 `test_n05_no_row_ever_says_compliant_under_any_fixture` | 穷举本文件所有夹具，判定列不得出现"达标" |

## 仍未改变的结论

- 人工专业复核：**NOT_REVIEWED**。
- B/C 批验收项（A02—A06、G01—G09、R01—R05、I01—I06、F02—F06）：**NOT_RUN**。
- 剩余 18 个模板：未审查，清单见 `TEMPLATE_ASSERTION_INVENTORY.md`，B 批逐模板任务与验收项见 **`B_BATCH_TEMPLATE_TASKS.md`**。
- 待工程师确认的语义问题仍是两项：`DECISION_LOG` 条目 003（别名）、条目 005（六率两套约定）。

**本批到此停止，再次等待验收。未自动 push、未开 PR、未进入 B 批。**
