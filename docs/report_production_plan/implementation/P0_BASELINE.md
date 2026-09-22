# P0-00 基线核查记录

执行日期：2026-09-20｜执行者：Claude（本仓库会话）｜性质：**只读核查，未修改任何产品代码、registry、治理文件、样本或历史输出**

本文件是 `03_P0_TASKS.md` 中 P0-00 的交付物。它记录接手时的真实状态与缺陷复现结果，不代表任何修复已经实施。

---

## 1. 版本与工作区状态（验收项 A00）

| 项 | 实测值 |
| --- | --- |
| HEAD | `adba408` — feat(frontend): Step 53-B1 sync Phase A facts to product shell |
| 分支 | `main` |
| 与计划核查基线是否一致 | 一致（计划声明基线 `adba408`） |

工作区未提交内容（**全部保留，未改动**）：

```
?? docs/CPSWC_商务白皮书_客户领导汇报版_v2026-04.textClipping
?? docs/SLT447-2026水土保持项目前期设计文件编制技术规程.pdf
?? docs/report_production_plan/          # 本任务包（计划文档）
?? output/                               # 用户既有输出目录
```

本轮新增：`docs/report_production_plan/implementation/`（本文件与 DECISION_LOG.md）。除此之外未写入仓库任何路径。缺陷复现脚本写在会话 scratchpad，不入仓库。

## 2. 环境（验收项 A01）

| 项 | 实测值 |
| --- | --- |
| 解释器 | Python 3.14.3（`pyproject.toml` 要求 >=3.11） |
| PyYAML / jinja2 / python-docx | 可用 |
| matplotlib | 可用（GeoPipeline 附图不会静默跳过） |
| reportlab / PyMuPDF / pyshp / pyproj | **不可用** |
| LibreOffice | `/opt/homebrew/bin/soffice` 存在（DOCX→PDF 路径可用） |
| 仓库项目指令 | 根目录无 `CLAUDE.md` / `AGENTS.md`；`.claude/settings.local.json` 存在，**内容未输出** |

依赖结论：PDF/GIS 相关能力在本机是**部分可用**。P0-07/08 的真实产出验收必须分别标注"mock 通过"与"本机实际生成"，并说明 pyshp/pyproj 缺失对空间成果的限制。

## 3. 基线测试与 lint（验收项 A01）

```
$ PYTHONPATH=src python3 -m pytest -q
74 passed in 0.18s                                  # exit 0

$ PYTHONPATH=src python3 -m cpswc.lint
Summary: ERROR=0  WARN=0  PENDING=0  INFO=26        # exit 0
```

与计划记载完全一致。26 条 INFO 全部为 `CORE_CONTRACTS_002 extension namespace 'engine.' used`，来源于 `ArtifactRegistry_v0.yaml` 中 `data_source_refs` 引用 `engine.GeoPipeline` / `engine.MonitoringPlanner` / `engine.SpoilStabilityEngine` 等扩展命名空间。这是**已知的登记扩展**，不是业务缺陷；P0 期间不应为"清零 INFO"而改动这些引用。

测试覆盖面核实：现有 3 个测试文件（`test_investment_import.py` / `test_quota_connector.py` / `test_table_projections.py`）全部集中在投资导入、定额连接与表格投影。**没有任何测试覆盖 narrative 断言、条件未知态、冻结哈希、导出门禁、制品台账**。计划关于"既有测试不构成报告生产质量证明"的判断成立。

## 4. 入口清单（P0-00 动作 3）

以下是修改契约时必须同步的全部调用点。

### 4.1 `run_project`

| 调用方 | 位置 |
| --- | --- |
| CLI | `runtime.py::_cli` |
| 包构建 | `renderers/package_builder.py::build_package` |
| 事实差分 | `fact_diff.py::_run_pipeline`（第 94-97 行） |
| 校验器 | `validator.py`（第 221-229 行） |
| 投影 CLI | `narrative/projection.py::__main__` |

### 4.2 `freeze_submission` / `create_version` / `_serialize_snapshot`

`runtime.py::_cli`（`--freeze`/`--version`/`--json`/`--html`）、`package_builder.build_package`、`fact_diff.py`、`narrative/projection.py::__main__`。

### 4.3 `project_narrative`

`renderers/document.py`（第 581-582 行）、`fact_diff.py`（第 100-101 行）、`narrative/projection.py::__main__`。

### 4.4 `render_report` / `build_package` / `check_export_readiness`

| 入口 | 位置 | 现状 |
| --- | --- | --- |
| `render_report` | `renderers/document.py::render_report`（第 739 行）+ 自身 CLI | 无模式参数 |
| `build_package` | `package_builder::build_package`（第 65 行）、其 CLI、`runtime.py::_cli --package`、`demo.py`（第 45/54 行）、`scripts/run_showcase_demo.sh`（第 38-41 行）、`docs/DEMO_README.md`（第 142-145 行） | 无模式参数，BLOCK 不中止 |
| `check_export_readiness` | `export_gate.py`（第 167 行），唯一调用方是 `build_package` | 无模式参数 |

**结论：现在没有任何一条"正式交付"路径**——所有入口产出的都是同一种包，manifest 里没有可供人识别草稿/正式的字段。P0-08 需要改的入口是上述 6 处（含 demo 脚本与文档示例）。

## 5. 缺陷复现（P0-00 动作 4）

方法：在会话 scratchpad 中用只读 probe 脚本运行，**不修改样本、不写仓库、不引入失败测试**（按任务要求，失败测试与对应修复同批交付）。原始输出保存在会话 scratchpad `p0_00/probe_results.json`。

| Probe | 对应诊断 / 验收 ID | 输入 | 实测结果 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | D02 / N01 | `sec_11_conclusion.render({}, {}, set(), {})` | `render_status=full`，`validate_block` **0 错误**，正文为"综上所述，—的水土保持方案编制依据充分……符合 GB/T 50434-2018 的要求" | 已复现 |
| 1b | D02 / N01 | `sec_3_evaluation.render_earthwork_balance({}, {}, set())` | 全部数值为"—"，仍输出"项目无需外借土石方""可剥离表土—，全部用于后期绿化覆土""土石方平衡合理，弃方有明确去向，借方有可靠来源" | 已复现 |
| 2 | D03 / N04 | 仅给 `field.derived.target.weighted_comprehensive_target`，无任何效果数据 | 输出"各项指标可达到上述目标值要求""各项防治目标可以实现" | 已复现 |
| 3 | D05 / S01-S02 | `condition_engine._get_value` | 缺键→`0`；`{"value": None}`→`None`；明确 0→`0`。后者在比较运算中抛 `'>' not supported between NoneType and int`，被 `evaluate_obligation` 的 `except Exception` 吞成 `triggered=False` | 已复现（**注意**：计划说"缺值转 0"，实测是两条不同路径——缺键静默转 0、null 值绕道异常转 False，P0-02 需分别处理） |
| 4 | D05 / U01-U02 | 借方字段完全缺失 vs 明确填 0 | 两种输入都落进 `not_triggered`，无 UNKNOWN 通道 | 已复现 |
| 5 | D05 / U03 | DSL `... .value >> 0`（求值异常） | `triggered=False`，进入 `not_triggered`，异常只写进 `py_expr` 字符串 | 已复现 |
| 6 | D04 / U07 | 空项目、无 `ob.unavoidability.redline_conflict` | `sec.project_overview.sensitive_areas`、`sec.evaluation.site_selection` 被判 `not_applicable`——常规选址评价与敏感区说明被红线冲突义务一票否决 | 已复现 |
| 7 | D01 / Q01 | 惠南样本完整投影 | `full=35 skeleton=0 na=3`；其中 6 个父章节的一句话引言（24-46 字符）计入 FULL；正文 <100 字符的 FULL 块共 **15 个** | 已复现 |
| 8 | D10 / F01 | 同一样本，仅改项目名称 | `fact_snapshot_hash` **完全相同**（`f8c459d6…`）——因为它散列的是 `derived_fields` 而非 facts | 已复现 |
| 9 | D11 / F02 | `run_project(deepcopy(sample))` 前后深比较 | **输入被原地改写**，被改键=`field.fact.investment.measures_registry`（quota enrich 写回） | 已复现 |
| 10 | D12 | `_FACT_MAPPING` 中的 field id 与四个样本实际键比对 | 见下节 | 已复现 |

### 5.1 D12 别名缺口实测（四个样本）

`project_fact_sheet._FACT_MAPPING` 中以下 field id **在任何样本里都不存在**，对应 ProjectFactSheet 属性恒为 `None`：

| 映射中的 id | 样本实际使用的 id | 四样本命中情况 |
| --- | --- | --- |
| `field.fact.topsoil.strippable_volume` | `field.fact.topsoil.stripable_volume` | 0/4 命中，别名 3/4 存在 |
| `field.fact.topsoil.backfill_volume` | `field.fact.topsoil.fill` | 0/4 命中，别名 3/4 存在 |
| `field.fact.prediction.predicted_total_loss` | `field.fact.prediction.total_loss` | 0/4 命中，别名 3/4 存在 |
| `field.fact.project.compile_unit` | `field.fact.project.compiler` | 0/4 命中 |
| `field.fact.project.construction_unit` | `field.fact.project.builder` | 0/4 命中 |

另外 4 个 `field.derived.*` 映射项在样本 pre-stored derived 中不存在（由 runtime 计算注入，属正常）；`disposal_highrisk_v0` 另缺 10 个自然/预测类 facts（该样本本身是弃渣场专项夹具）。

**未确认事项**：`stripable`/`strippable` 是否真的同指"可剥离量"、`topsoil.fill` 是否等于"回覆量"、`prediction.total_loss` 是否与 `predicted_total_loss` 同口径（是否含现状流失）——**P0-04 前必须先向工程师确认语义，不得直接合并**。

## 6. 与计划的差异

| # | 计划表述 | 实测 | 影响 |
| --- | --- | --- | --- |
| Δ1 | D05"缺值转 0" | 缺键转 0；`{"value": None}` 返回 `None` 后进入比较运算（`None > 0` 抛 TypeError → 再被吞成 False） | P0-02 要处理两条路径，不能只改一处 |
| Δ2 | D09 提到 GeoPipeline 示意图 | 本机 matplotlib 可用，示意图会真实生成；pyshp/pyproj 缺失 | 附图会以"看起来正常"的 PNG 出现在包里，`DEMONSTRATION` 标注更紧迫 |
| Δ3 | D08 只提 policy 有 11 章 | 本轮另核实：`DisplayNumberingPolicy_v0.yaml` 把 `sec.conclusion` 登记为 `display_number: "11"`，且 `sec_11_conclusion.py` 的 `normative_basis` 直接写 `rule.template_2026.section_11`。**模板原件是否存在第 11 章本轮未核验**，不作结论 | P0-05 需先核验模板原件再决定迁移 |
| Δ4 | 计划未提 | 现有 74 个测试**零覆盖** narrative/条件/冻结/门禁 | A 批新增测试是净增覆盖，不存在"改旧测试凑绿"的空间 |
| Δ5 | 计划建议命令 `python3 -m cpswc.lint` | 必须带 `PYTHONPATH=src`（包未安装） | 已按 README 说明执行，非缺陷 |

## 7. 未做的事

- 未修改任何产品代码、registry、governance 文件、样本、`tests/baselines`、`output/`。
- 未引入失败测试（按 P0-00 要求，反例测试与修复同批提交）。
- 未安装任何依赖，未联网，未生成任何包或文档产物。
- 未对 `.claude/settings.local.json` 等配置内容做任何输出。

## 8. 审批状态

RFC-RP-001 v1.0 状态：**PROPOSED，本文件编制时尚无批准记录**。按 `01_RFC_SCOPE.md` 第 6 节，P0-01 起的实施需要项目负责人对范围与兼容性决定的书面批准。批准发生后记入 `DECISION_LOG.md`。
