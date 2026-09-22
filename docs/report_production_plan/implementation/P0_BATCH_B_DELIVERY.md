# P0 Batch B 交付

日期：2026-09-20 起草／2026-09-21 完成｜授权：`DECISION_LOG.md` 条目 008｜模板依据：`06_CLAUDE_HANDOFF.md` 第 6 节

> **状态：B 批全部完成，停在验收点。** 用户指定的优先级 ①②③④⑤ 全部交付。
> 第 ④ 项（2026 章节映射）一度因模板原件不全受阻，用户指出附件 1 位于 PDF 第 3—22 页后解除（条目 009→010）。

## 版本与授权

| 项 | 内容 |
| --- | --- |
| 开始 / 结束 HEAD | `adba408`（**未提交、未 push、未开 PR**） |
| 批准范围 | B 批：P0-04 / P0-05 / P0-06 + 18 个 section 逐模板改造 |
| 指定优先级 | ①统一 BuildContext ②别名冲突 ③18 section 改造 ④2026 章节映射 ⑤双哈希与复核失效 |
| 用户原有未跟踪内容 | 4 项全部保留未动 |
| A 批前置动作 | 六率旧口径的非代码勘误 —— **已完成**（`P0_BATCH_A_DELIVERY.md` § 3 按两种读取口径重写） |

## 进度

| 优先级 | 任务 | 状态 | 证据 |
| --- | --- | --- | --- |
| ① | P0-04 统一 BuildContext，消除三套读取口径 | **DONE** | `src/cpswc/snapshot_adapter.py`；`tests/test_snapshot_adapter.py` 48 条 |
| ② | 别名冲突（不合并，报 CONFLICT） | **DONE** | `ALIAS_CANDIDATES` + `check_alias_candidates`；I02 共 6 条测试 |
| ③ | 18 个 section 逐模板改造 | **DONE** | 31 个已注册 render section 全部迁移；`tests/test_template_input_classes.py` 349 条 |
| ④ | P0-05 2026 章节映射 | **DONE** | `governance/ReportContentRequirements_v1.yaml`；`tests/test_report_structure.py` 34 条；差异表 `T2026_STRUCTURE_DIFF.md` |
| ⑤ | P0-06 双哈希与复核失效 | **DONE** | `src/cpswc/input_hashing.py`；`tests/test_submission_freeze.py` 37 条 |

## ① P0-04：统一读取上下文

### 解决的问题（`DECISION_LOG` 条目 007）

系统里原有**三套 derived 读法**：

| 消费者 | 读到的 derived |
| --- | --- |
| `run_project` 评估义务、`fact_sheet` | facts + 预存 derived + 计算 derived |
| `RuntimeSnapshot.derived_fields` | **只有计算 derived** |
| 正文、表格 | `derived_fields`（即只有计算 derived） |
| `export_gate` | 自己再合并一次 `_pre_stored_derived` |

惠州样本 9 个预存 derived 中有 **8 个**（含全部六率）对正文和表格不可见。

### 实现

`BuildContext` 是一次构建期间的唯一只读视图，按固定优先级选一个读值并记录选了哪一层：

```
计算 derived（权威） > enrich 消费视图 > 预存 derived（外部结果） > 项目事实
```

| 规则 | 行为 |
| --- | --- |
| 当前计算**失败** | 旧值**不顶上**；隔离为 `STALE_HISTORICAL` + `DERIVED_STALE`(BLOCK)；该字段不进统一视图 |
| 有优先级可依 + 各层不一致 | 选高优先层，留 `INPUT_CONFLICT`(WARN) 说明差异 |
| 无优先级可依（预存 vs 事实） | 判 `CONFLICT`，**不给任何值**，`INPUT_CONFLICT`(BLOCK) |
| 外部结果 | `SOURCE_UNVERIFIED`(WARN)，不伪装成本次重算 |
| 单位 | 以 FIR 的 `semantic_type` / `unit_enum` / `unit` 为准，不再用手工白名单 |
| 裸数字 + FIR 登记了单位 | 合法（04 文档第 3 节"或来自有单位的登记契约"），单位取自登记 |
| 演示假设 | `_note`/`source_note` 含"典型值/默认/估算/placeholder/暂按"等标记 → `DEMO_ASSUMPTION`(BLOCK) |

`build_snapshot_dict()` 成为**唯一**的 snapshot 组装入口，原先 5 处各自拼 `_original_facts` 的代码已全部改为调用它。

### 首次统一后立刻暴露的两件事

1. **惠州六率的计算输入全部是 placeholder stub**：`field.fact.prevention.` 下 `treated_loss_area` / `total_loss_area` / `should_restore_area` / `planned_vegetation_area` / `protected_topsoil_volume` / `protected_spoil_volume` 六个字段的 `_note` 都写着 `placeholder stub`。也就是说六率的分子分母本身就是占位估算。此前没有任何地方提示过。
2. **误报也被发现并修掉了**：`weighted_comprehensive_target` 的预存值与计算值"不一致"，实为预存那份多带了 Step 11B 的纠错审计元数据，六个业务值完全相同。比较逻辑已改为剥离注解/审计键后再比。

### F02：不再原地改写输入

`run_project` 原先把 quota enrich 结果写回 `project_input["facts"]`。现在 enrich 只产出独立的消费视图（`RuntimeSnapshot.enriched_views`），调用者的输入一个字节不动；enrich 失败也不再静默（记入 `runtime_diagnostics`）。四个样本各有一条参数化测试守住这条。

## ② 别名冲突

按 `DECISION_LOG` 条目 003（用户已拍板"不按同义合并，先报 CONFLICT"）：

| 情形 | 行为 |
| --- | --- |
| 两侧都有值且**不相等** | `INPUT_CONFLICT`(**BLOCK**)，两侧各自保留自己的读值，不择一 |
| 两侧都有值且相等 | `INPUT_CONFLICT`(WARN)——相同不等于同义 |
| 仅单侧有值 | 照常读该侧，标 `SOURCE_UNVERIFIED`(WARN) 提示别名未确认 |

5 对候选全部登记在 `ALIAS_CANDIDATES`，每对都有测试确认"真的被检查到"。

## ③ 18 个 section 逐模板改造

31 个已注册 render section **全部**迁移到 `SectionEvidence` / `BuildContext`；旧的 `_v(facts, ...)` / `_num(facts, ...)` 取值函数已从全部模板中**删除**（12 处死代码 + 2 处活调用）。两条结构性测试守住这一点，漏改一个模板就会红。

### 通用验收夹具

`tests/test_template_input_classes.py` 把 B_BATCH_TEMPLATE_TASKS 的四类输入参数化到**每一个** section 上（349 条）：

| 编号 | 输入 | 断言 |
| --- | --- | --- |
| T-a | 相关字段全缺 | 不得用"—"冒充数据（破折号除外）；无复核支持的项目判断为 0；每段都声明断言类型；报缺失必须点名字段 |
| T-b | 明确填 0 / 空清单 | 不崩溃；不得升级为"不涉及/无需/不设置"等核查结论 |
| T-c | NaN / inf / 未登记单位 / 空白串 | 不崩溃；**非法数字不得出现在正文** |
| T-d | 别名两侧冲突 | 模板不崩溃、不静默择一；每对候选都被检查 |

**这份夹具不能代替 T-e**（逐句人工确认断言分类）。T-e 状态：**NOT_REVIEWED**。

### 改造中发现并修掉的缺陷

| 模板 | 缺陷 |
| --- | --- |
| `sec_2_1_2_land_earthwork` | 借方/弃方/综合利用**缺失当 0**，三个都"为 0"就输出"土石方基本平衡" |
| `sec_6_soil_loss` | 预测总量直接写进正文，而 `prediction_engine` 的扰动模数在无项目覆盖时取自内建"典型值"矩阵；类比工程"两项目基本相同，具有较强可比性"是无复核支持的专业判断 |
| `prediction_engine._get_val` | `float(v["value"])` 不查有限性，NaN 一路算到总量，正文印出 `nan t`（由 T-c 夹具发现） |
| `sec_9_1_investment_summary` | 措施分项缺失按 0 累加，"合计"永远算得出来 |
| `sec_7_1_responsibility_range` | 临时占地**缺失当 0** → "无临时占地"；分县面积缺失按 0 累加 |
| `sec_10_management` / `sec_1_2_spec_sheet` | `facts.get(key, "建设单位")` 把没填的责任主体替换成看起来正常的通称 |
| `sec_8_2` / `sec_8_3` | 防治分区缺失时仍给出监测点数量与分区监测安排 |

`sec_6_soil_loss` 现在会明确写出"全部预测单元均采用内建默认扰动模数（类比典型值），**不得作为正式成果使用**"。

## ④ P0-05：2026 章节映射

### 来源核验（决议 8 双锚齐全 → VERIFIED）

| 项 | 内容 |
| --- | --- |
| 规范 | 《生产建设项目水土保持方案报告书编制内容》（**办水保函〔2026〕232 号** 附件 1） |
| 发文机关 / 成文 | 中华人民共和国水利部办公厅 / 2026-04-03 |
| 施行 | 自印发之日起实施；**2026-06-01 后不再接收不符合模板要求的方案** |
| 第一依据 | 本地扫描原件（sha256 `57a682a1…`，28 页，**附件 1 第 3—22 页**），逐页读取可视页面 |
| 交叉核对 | 昌都市水利局公开 HTML 全文 —— 第 1—10 章及各级小节**逐条一致** |
| OCR | 仅用于定位页码，不作为规范原文 |

**交叉核对发现一处差异**：该页面标注文号为"办水保函〔2026〕**23**号"，原件为"**232** 号"（少一位）。以原件为准——这再次证实 `04_CONTRACTS_AND_ACCEPTANCE.md` 第 6 节所记"页面标题文号有误"。

### 五处关键位置（全部有原件页码）

| stable ID | v0.1 旧显示 | 2026 显示 | 原件页码 |
| --- | --- | --- | --- |
| `sec.conclusion` | 第 11 章 | **1.9 结论** | p.5 |
| `sec.soil_loss_prevention.design_horizon` | 7.3 | **7.2 设计水平年** | p.16 |
| `sec.soil_loss_prevention.targets` | 7.2 | **7.3.2 防治目标** | p.17 |
| `sec.soil_loss_prevention.benefit_analysis` | 7.5 | **9.2 效益分析**（跨章） | p.20 |
| `sec.management` | 10 | **10 水土保持管理**（最后主体章） | p.20 |

**2026 模板没有第 11 章。**

### stable ID 处置：一个都没改名

- **迁移 5 条**：显示位置变，`stable_id` 不动，旧编号语境留痕（按"第 11 章"或"7.5"定位的历史审查意见仍可解析）。
- **被吸收 3 条**：v0.1 里是独立显示节、2026 里并入别节，内容仍产出——`compensation_fee` → 9.1.2；`water_soil_zoning` → 1.1.2 + 表 1；`responsibility_range_by_county` → 7.1 + 附表。
- `projection` 中登记的 stable ID **全部有归属，无悬空**，由 `test_r05_every_registered_section_has_a_home` 守着。

### 完成度：新旧口径对照（惠州样本）

| 口径 | 数字 | 含义 |
| --- | --- | --- |
| 旧 `full_count` | **38** | 渲染出连续文字的块数——看起来接近完成 |
| 对照 2026 叶子要求 | **0 / 64** | 已确认完成的叶子要求 |
| 其中未实现 | **38 / 64** | 模板要求但当前无任何 narrative 产出 |
| 其中有产出未确认 | **26 / 64** | 有文字，但内容完整性未对照规范确认 |

未实现项**仍在分母里**（R02）。这是整个 P0 想要的那个差别：从"38 个 FULL"到"0/64 已确认、38/64 未实现"。

完整差异表见 `T2026_STRUCTURE_DIFF.md`。

### 本轮未做

1. **未改 renderer 章节树**与 `DisplayNumberingPolicy_v0.yaml`——仍按 v0.1 编号输出。本轮只建映射与差异表；真正切换显示编号要同步改章节树、交叉引用与既有测试基线，属独立改动。
2. **未改 `sec_11_conclusion.py` 的 `rule.template_2026.section_11` 引用**——它会牵动规范引用校验与既有断言测试。
3. **未实现那 38 项缺失内容**。清单的作用是让它们可见且计分，不是自动补写。
4. **未处理报告表（附件 3）**。`load_content_requirements(species="报告表")` 返回 `None`，不得拿报告书清单顶替（R04）。

## ⑤ P0-06：双哈希与复核失效

### 修的是 D10

原 `freeze_submission` 里那个叫 `fact_snapshot_hash` 的字段，散列的其实是 `derived_fields`。实测把项目名换成完全不同的字符串，该 hash **一字不变**——"事实变没变"这个判断从来没成立过。

| hash | 覆盖 | 用途 |
| --- | --- | --- |
| `fact_snapshot_hash` | 规范化**事实集合**本身 | 检测事实是否变化。事实不变而来源版本变动时可以不变，**不单独决定审核有效性** |
| `generation_input_hash` | 事实 + 预存派生量 + **来源层选择** + 静态 profile + registry/governance/模板内容摘要 + 计算实现版本 + 规则集 | **审核有效性、重生成与变更判定都看它** |
| `content_hash` | snapshot JSON 字节 | 文件完整性，含时间戳，每次必变；不是语义判据 |

语义 hash **排除**运行时间、run ID、snapshot_id、临时目录——同语义输入重复执行结果相同（F03）。

### canonical JSON

固定 key 排序；**有序数组保留顺序**（不猜哪个列表是集合）；bool 与 int 区分；整值浮点归一（3.0 == 3）；null 与缺键区分；**NaN/inf 直接报错并给出字段路径**，不静默替换。

### 来源内容变化

`registries/` `governance/` `narrative/templates/` 三个目录按文件内容算摘要。**文件名与数值都不变、只改一行注释，生成输入 hash 也会变**（F04）。来源文件缺失返回 `MISSING` 哨兵，不假装成功。

### 复核绑定迁移（兑现条目 004 的承诺）

`ReviewLedger` 改绑 `generation_input_hash`；A 批的临时 `quality_input_hash` 降为兜底。改一个事实 → 生成输入 hash 变 → 旧 CONFIRMED 记录变 `STALE` → 结论段自动撤回并登记 `REVIEW_STALE`（F06，有端到端测试）。

### 旧包

`describe_hash_schema()` 识别缺 `hash_schema_version` 的旧记录 → 标 `legacy_unverified`，**不重算、不覆盖**。重算后覆盖旧 manifest 会让历史签署看起来适用于新包——那是最危险的一种"修复"。

### 冻结语义

`FrozenSubmissionInput.lifecycle_freeze_note` 明写"只表示输入已冻结，**不表示**内容已经专业校审通过"——构造这个 dataclass 不等于有人确认过内容。

## 实际执行的验证

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `PYTHONPATH=src python3 -m pytest -q` | 0 | **730 passed**（原 74 + A 批 188 + B 批 468） |
| 原 3 个测试文件单独运行 | 0 | 74 passed，仍是一条未改、一条未删 |
| `PYTHONPATH=src python3 -m cpswc.lint` | 0 | ERROR=0 WARN=0 PENDING=0 INFO=26，与基线一致 |
| `git diff --check` | 0 | 通过 |
| 包构建（惠州） | 0 | 正常产出 |

### 四样本

| 样本 | full / skel / na | 契约校验错 | derived 视图 | 读取诊断 |
| --- | --- | --- | --- | --- |
| huinan_zhigu_v0 | 37 / 0 / 1 | 0 | 3 | CONFLICT 1（WARN）、SOURCE_UNVERIFIED 6 |
| huizhou_housing_v0 | 38 / 0 / 0 | 0 | **3 → 11** | DEMO_ASSUMPTION 6、CONFLICT 1（WARN）、SOURCE_UNVERIFIED 12 |
| shiwei_logistics_v0 | 34 / 3 / 1 | 0 | 3 | CONFLICT 1（WARN）、SOURCE_UNVERIFIED 6 |
| disposal_highrisk_v0 | 37 / 0 / 1 | 0 | 3 | CONFLICT 1（WARN）、SOURCE_UNVERIFIED 1 |

章节计数与 A 批一致；变化全部在"读取诊断"与 derived 视图上——这正是 P0-04 的目的。

### 各测试文件

| 文件 | 条数 | 覆盖 |
| --- | --- | --- |
| `test_investment_import.py` / `test_quota_connector.py` / `test_table_projections.py` | 19 / 25 / 30 | **原有测试，一条未改、一条未删** |
| `test_report_quality.py` | 38 | S01—S05、Q01、Q02 |
| `test_condition_unknown.py` | 35 | U01—U07 |
| `test_narrative_assertions.py` | 53 | N01—N03、N07、N08 |
| `test_target_effect_separation.py` | 21 | N04—N06 |
| `test_a_batch_review_regressions.py` | 41 | A 批验收四项反例 R-1—R-4 |
| `test_snapshot_adapter.py` | 48 | I01—I06、F02 |
| `test_template_input_classes.py` | 349 | T-a—T-d × 31 个 section |
| `test_report_structure.py` | 34 | R01—R05 |
| `test_submission_freeze.py` | 37 | F01、F03—F06 |

**未执行**（NOT_RUN）：A02—A06 与 G01—G09（制品台账、草稿/正式门禁、原子发布）——属 C 批，未批准，本轮未实现，不作 PASS。
**人工专业复核**：NOT_REVIEWED。**T-e 逐句断言分类人工复核**：NOT_REVIEWED。

## 剩余风险与 C 批条件

### 仍阻断生产（属 C 批）

1. `build_package` 遇 BLOCK 仍继续产包，没有草稿/正式之分（P0-08）。
2. `_check_assurances` 仍硬编码 WARN，裸 `provided=True` 即算满足（P0-08）。
3. 附图仍是 matplotlib 示意图，未标 `DEMONSTRATION`；2026 模板要求防治责任范围图**提供完整 shapefile 矢量数据**、取土场弃渣场位置图**含地形和影像**——差距很大（P0-07）。
4. `evaluate_report_quality` 已能算出真实覆盖率，但尚未接入包构建与工作台展示（P0-09）。

### 不阻断本批但需注意

- renderer 仍按 v0.1 编号输出；切换到 2026 编号是独立改动。
- `sec_11_conclusion.py` 仍引用 `rule.template_2026.section_11`（该条款不存在）。
- 38 项模板要求的内容尚无任何 narrative 产出。

### 待工程师确认（两项，均未变）

- `DECISION_LOG` 条目 003：三组别名语义（已按 CONFLICT 路线实现，等确认后才谈合并）。
- `DECISION_LOG` 条目 005：`field.derived.target.*` 的两套约定（已按候选值保守处理）。

**B 批到此停止，等待验收。未进入 C 批、未提交、未 push。**
