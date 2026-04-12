# CPSWC v0 Demo Baseline

**生产建设项目水土保持方案智能编制与审查平台 — v0 演示基线**

Tag: `v0-demo-baseline` | 日期: 2026-04-13

---

## 产品定位

CPSWC 是一个**确定性水土保持方案生产引擎**，不是 AI 写作工具。

核心锚点：
1. **确定性生产内核** — facts → rules → calculators → narrative + tables，全链路可复现
2. **可追溯闭环** — 每段文字标注 evidence_refs + source_rule_refs，改一个 fact 可追溯影响链
3. **收成产品** — 输出完整 submission package（docx + snapshot + manifest + workbench）
4. **改得动、查得清、数一致** — 三处引用同一数据源，改一处全联动

---

## v0 覆盖率

### Narrative Blocks (38 sections)

| 样本 | FULL | SKELETON | N/A | 有效覆盖率 |
|---|---|---|---|---|
| 惠州住宅 (合成) | 31 | 7 | 0 | 82% |
| 世维物流 (真实) | 26 | 6 | 6 | 81% |
| 惠南智谷 (真实) | 29 | 6 | 3 | 83% |

### FULL Chapters (确定性生成)

| # | 章节 | 模板数 | 状态 |
|---|---|---|---|
| 1 | 综合说明 | 3 | 概述 + 基本信息 + 特性表 |
| 2 | 项目概况 | 6 | 占地 + 土石方 + 进度 + 敏感区(条件) + 气候 + 区划 |
| 3 | 水土保持评价 | 3 | 总评 + 选址(条件) + 土石方评价 |
| 4 | 表土资源 | 2 | 剥离 + 平衡 (零值自然退化) |
| 5 | 弃渣处置 | 2 | 来源流向 + 选址论证 (条件, 含 no_site variant) |
| 6 | 水土流失分析 | 2 | 现状 + 预测 |
| 7 | 防治措施 | 4 | 责任范围 + 目标(单级/多级) + 设计水平年 + 效益分析 |
| 9 | 投资估算 | 2 | 汇总 + 补偿费 |
| 11 | 结论 | 1 | 全局收束 (含弃渣场高风险差异) |

### SKELETON Chapters (v1 规划)

| 章节 | 缺失原因 |
|---|---|
| 7.x 施工进度 | 需要横道图数据 facts |
| 8 监测 (×4) | 需要监测方法/频率/点位专业内容 |
| 10 管理 | 需要管理制度程式化文本 |

### Table Projections (13 tables)

| 表 | 说明 |
|---|---|
| 工程占地统计表 | 分项目组成×占地性质 |
| 土石方平衡表 | 挖/填/调入/调出/借方/弃方 |
| 分县占地统计 | 按行政区分 |
| 表土平衡表 | 剥离/回覆/剩余 |
| 防治责任范围表 | 按行政区×分区 |
| 弃渣场汇总表 | 级别评定(条件) |
| 六项指标复核表 | 目标值 vs 达标 |
| 投资估算总表 (S1) | 五类措施 + 补偿费 |
| 投资分项表 (S2) | 方案新增/已有/合计 |
| 附表: 总表/已有/独立费 | 投资明细 (×3) |
| 工程特性表 | 4 部分 key-value 汇总 |

---

## 三套验证样本

### 1. 惠州住宅 (huizhou_housing_v0.json) — 合成
- 用途: 全功能覆盖测试
- 特点: 多防治分区(惠阳+大亚湾), 面积加权六率, 有弃渣场, 有敏感区, 有临时占地
- 覆盖: 31 FULL / 7 SKELETON / 0 N/A

### 2. 世维物流 (shiwei_logistics_v0.json) — 真实
- 来源: 参考样稿 02 (报告书, 世维华南供应链枢纽项目二期)
- 特点: 无表土(零值早退), 无弃渣场(N/A), 无敏感区(N/A), 无临时占地, 单行政区
- 覆盖: 26 FULL / 6 SKELETON / 6 N/A
- 发现: 样稿补偿费 0.0468 万元为笔误，正确值 0.468 万元

### 3. 惠南智谷 (huinan_zhigu_v0.json) — 真实
- 来源: 参考样稿 01 (报告表, 惠南智谷创业创新中心项目)
- 特点: 小项目(0.78hm²), 有微量表土(0.01万m³), 有弃方(0.40万m³), 有临时占地, 有项目代码
- 覆盖: 29 FULL / 6 SKELETON / 3 N/A

---

## 技术架构

```
sample.json (facts)
  → runtime.py (rule engine → obligations/artifacts/assurances)
  → calculator_engine.py (compensation fee / weighted target / disposal level)
  → narrative/projection.py (25 render functions → NarrativeBlocks)
  → renderers/
      ├── document.py (→ narrative_skeleton_v0.docx)
      ├── table_projections.py (13 tables → formal_tables_v0.docx)
      ├── workbench.py (→ workbench.html)
      └── package_builder.py (→ submission package with SHA256 manifest)
```

### 核心模块 (15 files)

| 模块 | 职责 |
|---|---|
| `runtime.py` | Rule engine: facts → obligations/artifacts/assurances |
| `calculator_engine.py` | 3 calculators: compensation fee, weighted target, disposal level |
| `narrative/contract.py` | NarrativeBlock/Paragraph/TemplateSpec 数据契约 |
| `narrative/projection.py` | 投影引擎: snapshot → list[NarrativeBlock] |
| `narrative/templates/` | 19 模板文件, 25 render 函数 |
| `renderers/document.py` | DOCX 渲染 (recursive section tree + table embedding) |
| `renderers/table_projections.py` | 13 表投影函数 |
| `renderers/table_protocol.py` | 通用表格协议 (TableSpec/TableData/render_data_table) |
| `renderers/workbench.py` | 6-panel HTML 工作台 |
| `renderers/package_builder.py` | Submission package (12 files + SHA256 manifest) |
| `investment_loader.py` | 措施投资 CSV 导入 |
| `lint.py` | 静态校验 (facts/obligations/artifacts naming) |
| `validator.py` | NarrativeBlock 运行时校验 |
| `quota_scraper.py` | 2025 版水保定额采集 |
| `quota_connector.py` | 定额 DB → 措施单价连接器 |

---

## 运行方式

```bash
# 安装依赖
pip install python-docx pyyaml

# 运行 narrative 投影 (查看 blocks)
PYTHONPATH=src python3 -m cpswc.narrative.projection samples/huinan_zhigu_v0.json

# 生成完整 submission package
PYTHONPATH=src python3 -c "
import json
from cpswc.renderers.package_builder import build_package
with open('samples/huinan_zhigu_v0.json') as f:
    data = json.load(f)
build_package(data, 'output/huinan_v0')
"

# 输出位置
# output/huinan_v0/rendered/narrative_skeleton_v0.docx  — 正文报告
# output/huinan_v0/rendered/formal_tables_v0.docx       — 正式表格
# output/huinan_v0/workbench.html                        — 可视化工作台
# output/huinan_v0/PACKAGE_MANIFEST.json                 — SHA256 校验清单
```

---

## v1 路线图

| 优先级 | 方向 | 内容 |
|---|---|---|
| P0 | 项目录入 MVP | facts 填充工作台, 缺失字段清单, 校验反馈 |
| P0 | Fact Diff | 改一个 fact → 追溯影响链 (章节/表/计算/义务) |
| P1 | 监测章节 | monitoring facts + 4 模板 |
| P1 | 施工进度 | construction_schedule facts + 横道图 |
| P2 | 管理章节 | management 程式化文本 |
| P2 | 多规则集 | 2018 GB vs 2026 模板 自动适配 |
