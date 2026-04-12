# CPSWC Real Project Intake Specification

**版本**: v0 MVP | **日期**: 2026-04-13

---

## 1. 概述

本文档定义真实项目资料进入 CPSWC 系统的标准流程和数据规范。

**目标用户**: 水保方案编制人员、项目业主资料员
**输入**: 项目基础资料（纸质/电子）
**输出**: `facts.json` — 可直接驱动 CPSWC 管线生成报告

---

## 2. 字段总览

CPSWC v0 共消费 **46 个事实字段**，分为 4 个录入包。

### 必填 / 推荐 / 可选 标记说明

| 标记 | 含义 | 缺失后果 |
|---|---|---|
| **必填** | 缺失则管线无法产出有意义的报告 | 多个章节退化为 SKELETON |
| **推荐** | 缺失则特定章节/表退化 | 对应章节显示占位符 "—" |
| **可选** | 条件性字段，不涉及则留空 | 对应章节自动 N/A |

---

## 3. 录入包 A: 项目基本信息

| 字段 | 类型 | 必填 | 示例 | 影响范围 |
|---|---|---|---|---|
| project.name | string | **必填** | "世维华南供应链枢纽项目（二期）" | 全文标题、特性表、结论 |
| project.code | string | 可选 | "2108-441305-04-01-552966" | 1.1 项目代码括号 |
| project.industry_category | string | **必填** | "仓储物流" / "工业" | 1.1 行业类别 |
| project.nature | string | **必填** | "新建" / "改扩建" | 1.1 建设性质 |
| project.builder | string | 推荐 | "惠州市世维仓储物流有限公司" | 特性表 |
| project.compiler | string | 推荐 | "惠州恒江工程咨询有限公司" | 特性表 |
| location.province_list | list[str] | **必填** | ["广东省"] | 全文定位、补偿费 |
| location.prefecture_list | list[str] | **必填** | ["惠州市"] | 全文定位 |
| location.county_list | list[str] | 推荐 | ["仲恺高新技术产业开发区"] | 特性表、分县表 |
| location.river_basin_agency | string | 可选 | "东江流域管理局" | 特性表 |
| investment.total_investment | Quantity | **必填** | {"value": 10769.00, "unit": "万元"} | 1.1、特性表、综述 |
| investment.civil_investment | Quantity | **必填** | {"value": 6580.51, "unit": "万元"} | 1.1、特性表 |
| schedule.start_time | string | **必填** | "2021-12" | 1.1、进度、特性表 |
| schedule.end_time | string | **必填** | "2023-08" | 1.1、进度、设计水平年 |
| schedule.design_horizon_year | int | 推荐 | 2024 | 7.3 设计水平年 |

---

## 4. 录入包 B: 占地 / 土石方 / 表土

| 字段 | 类型 | 必填 | 示例 | 影响范围 |
|---|---|---|---|---|
| land.total_area | Quantity | **必填** | {"value": 7.08, "unit": "hm²"} | 占地表、防治范围、补偿费 |
| land.permanent_area | Quantity | **必填** | {"value": 7.08, "unit": "hm²"} | 占地表、补偿费 |
| land.temporary_area | Quantity | **必填** | {"value": 0.0, "unit": "hm²"} | 占地表、补偿费 |
| land.county_breakdown | list[obj] | 推荐 | 见下方格式 | 占地表、防治分区、特性表 |
| earthwork.excavation | Quantity | **必填** | {"value": 1.08, "unit": "万m³"} | ch3 评价、土石方表 |
| earthwork.fill | Quantity | **必填** | {"value": 1.51, "unit": "万m³"} | ch3 评价、土石方表 |
| earthwork.self_reuse | Quantity | 推荐 | {"value": 1.08, "unit": "万m³"} | ch3 利用率 |
| earthwork.comprehensive_reuse | Quantity | 推荐 | {"value": 0.0, "unit": "万m³"} | ch3 综合利用 |
| earthwork.spoil | Quantity | **必填** | {"value": 0.0, "unit": "万m³"} | ch5 弃渣触发、特性表 |
| earthwork.borrow | Quantity | 推荐 | {"value": 0.43, "unit": "万m³"} | ch3 借方 |
| earthwork.borrow_source_type | string | 可选 | "外购" | ch3 借方来源 |
| topsoil.stripable_area | Quantity | 推荐 | {"value": 0.0, "unit": "hm²"} | ch4 剥离 |
| topsoil.stripable_volume | Quantity | 推荐 | {"value": 0.0, "unit": "万m³"} | ch4 剥离、特性表 |
| topsoil.excavation | Quantity | 推荐 | {"value": 0.0, "unit": "万m³"} | ch4 平衡 |
| topsoil.fill | Quantity | 推荐 | {"value": 0.0, "unit": "万m³"} | ch4 平衡 |

### county_breakdown 格式

```json
[
  {"county": "仲恺高新区", "type": "建筑物区", "area": {"value": 4.15, "unit": "hm²"}, "nature": "永久"},
  {"county": "仲恺高新区", "type": "景观绿化区", "area": {"value": 1.42, "unit": "hm²"}, "nature": "永久"}
]
```

---

## 5. 录入包 C: 自然条件 / 侵蚀预测

| 字段 | 类型 | 必填 | 示例 | 影响范围 |
|---|---|---|---|---|
| natural.climate_type | string | 推荐 | "南亚热带季风气候" | ch2 气候 |
| natural.landform_type | string | 推荐 | "冲积平原" | ch2 气候、特性表 |
| natural.soil_erosion_type | string | 推荐 | "水力侵蚀" | ch6 现状、特性表 |
| natural.soil_erosion_intensity | string | 推荐 | "微度" | ch6 现状 |
| natural.original_erosion_modulus | Quantity | 推荐 | {"value": 500, "unit": "t/(km²·a)"} | ch6 现状、特性表 |
| natural.allowable_loss | Quantity | 推荐 | {"value": 500, "unit": "t/(km²·a)"} | ch6 现状、特性表 |
| natural.water_soil_zoning | string | **必填** | "南方红壤区" | ch7 目标值计算、ch2 区划 |
| natural.key_prevention_treatment_areas | list | 可选 | [] | ch2 区划 (空=不涉及) |
| natural.other_sensitive_areas | list | 可选 | [] | ch2 敏感区 (空=不涉及) |
| prediction.total_loss | Quantity | 推荐 | {"value": 285, "unit": "t"} | ch6 预测、ch7 效益 |
| prediction.new_loss | Quantity | 推荐 | {"value": 248, "unit": "t"} | ch6 预测、ch7 效益、综述 |
| prediction.reducible_loss | Quantity | 推荐 | {"value": 248, "unit": "t"} | ch7 效益 |

---

## 6. 录入包 D: 防治标准 / 弃渣 / 法规

| 字段 | 类型 | 必填 | 示例 | 影响范围 |
|---|---|---|---|---|
| prevention.control_standard_level | string | 推荐 | "一级" | ch7 目标、ch11 结论 |
| prevention.control_standard_level_breakdown | list | 可选 | 见下方 | ch7 多级加权 |
| disposal_site.level_assessment | list | 可选 | [] | ch5、ch11 高风险段 |
| disposal_site.failure_analysis_required | bool | 可选 | false | ch5 稳定性 |
| regulatory.compensation_fee_rate | obj | 推荐 | {"value": 0.6, "unit": "元/m²", "source": "粤发改价格〔2021〕231号"} | ch9 补偿费 |

### control_standard_level_breakdown 格式（多分区时）

```json
[
  {"zone_id": "Z1", "zone_name": "主体住宅区", "standard_level": "一级", "area": {"value": 7.9, "unit": "hm²"}},
  {"zone_id": "Z2", "zone_name": "配套用地", "standard_level": "二级", "area": {"value": 1.6, "unit": "hm²"}}
]
```

---

## 7. Quantity 类型规范

所有带单位的数值统一用 Quantity 对象：

```json
{"value": 7.08, "unit": "hm²", "precision": 0.01}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| value | number | 是 | 数值 |
| unit | string | 是 | 单位 (hm², 万m³, 万元, t, t/(km²·a)) |
| precision | number | 否 | 精度 (默认 0.01) |

---

## 8. 投资/措施扩展包（v0 可选）

以下字段在 v0 中由 CSV 导入或 quota connector 生成，一般不需要手工录入：

| 字段 | 说明 |
|---|---|
| investment.measures_registry | 措施清单 (由 investment_loader.py 从 CSV 导入) |
| investment.measures_summary | 措施费汇总 (由 runtime 从 registry 聚合) |

如手工提供 measures_summary，格式为：

```json
{
  "工程措施": {"new": 0.0, "existing": 3.64, "total": 3.64},
  "植物措施": {"new": 0.0, "existing": 1.02, "total": 1.02},
  "临时措施": {"new": 0.0, "existing": 1.34, "total": 1.34}
}
```

---

## 9. 完整录入流程

```
1. 收集项目资料 (参照 project_intake_checklist.md)
2. 填写 project_intake_minimal.yaml
3. 运行 intake_validator.py → 获得缺失清单 + 影响报告
4. 补齐缺失字段
5. 转换为 facts.json
6. 运行 CPSWC pipeline → 获得 submission package
```
