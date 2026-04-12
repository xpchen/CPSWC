"""
table_projections.py — CPSWC P0/Step 15 表格数据投影函数

Step 15 样稿对位修正:
  M1: 工程占地 → 项目组成×地类×占地性质 矩阵 (对齐样稿 表4.3-1 / 表2.3-1)
  M2: 表土平衡 → 序号/项目组成/开挖/回填/调入来源/调出去向 (对齐样稿 表4.4-1)
  M3: 土石方平衡 → 序号/项目组成/挖/填/调入/调出/借方来源/弃方去向 (对齐样稿 表4.4-2 / 表2.4-1)
  M4: 防治责任范围统计 → 降级为条件附表, 正文位置留给防治分区表 (v1 补 facts)
  N2: 新增六项指标复核表 (对齐样稿 表10.3-5 / 表7.2-3)

投影纪律:
  - 只从 snapshot._original_facts / derived_fields 取数
  - 列结构对齐样稿, 行数不足时出"项目合计"单行, 不伪造分项
  - 缺值标 None → render_data_table 显示 "—"
"""
from __future__ import annotations
from typing import Any

from cpswc.renderers.table_protocol import TableColumn, TableSpec, TableData, TableRenderPolicy


def _get(facts: dict, key: str) -> Any:
    v = facts.get(key)
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


# ============================================================
# M1. art.table.total_land_occupation — 工程占地情况统计表
# ============================================================
# 对齐样稿: 表4.3-1 (报告表) / 表2.3-1 (报告书)
# 列: 项目组成 / 占地面积 / 占地类型 / 占地性质(永久/临时)
# v0: county_breakdown 提供分项数据, 汇总行从 land.* facts 取

SPEC_TOTAL_LAND = TableSpec(
    table_id="art.table.total_land_occupation",
    title="工程占地情况统计表",
    columns=[
        TableColumn(key="component", header="项目组成", unit="", align="left", fmt="str"),
        TableColumn(key="area", header="占地面积", unit="hm\u00b2", align="right", fmt="2f"),
        TableColumn(key="land_type", header="占地类型", unit="", align="center", fmt="str"),
        TableColumn(key="permanent", header="永久占地", unit="hm\u00b2", align="right", fmt="2f"),
        TableColumn(key="temporary", header="临时占地", unit="hm\u00b2", align="right", fmt="2f"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.land.county_breakdown / permanent_area / temporary_area (对齐样稿工程占地情况统计表)",
    section_id="sec.project_overview.land_occupation",
)


def project_total_land_occupation(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    breakdown = facts.get("field.fact.land.county_breakdown")
    perm_total = _get(facts, "field.fact.land.permanent_area")
    temp_total = _get(facts, "field.fact.land.temporary_area")

    rows = []
    if isinstance(breakdown, list) and breakdown:
        for rec in breakdown:
            area = rec.get("area")
            if isinstance(area, dict):
                area = area.get("value")
            nature = rec.get("nature", "")
            rows.append({
                "component": rec.get("county", "") + " " + rec.get("type", ""),
                "area": area,
                "land_type": rec.get("type", "—"),
                "permanent": area if nature == "永久" else None,
                "temporary": area if nature == "临时" else None,
            })
    else:
        # 无分项数据时, 出 1 行汇总
        total = _get(facts, "field.fact.land.total_area")
        rows.append({
            "component": "项目合计",
            "area": total,
            "land_type": "—",
            "permanent": perm_total,
            "temporary": temp_total,
        })

    total_area = _get(facts, "field.fact.land.total_area")
    total_row = {
        "component": "合计",
        "area": total_area,
        "land_type": "",
        "permanent": perm_total,
        "temporary": temp_total,
    }

    policy = TableRenderPolicy.RENDER_WITH_VALUES if rows else TableRenderPolicy.RENDER_WITH_PLACEHOLDER
    return TableData(spec=SPEC_TOTAL_LAND, rows=rows, total_row=total_row,
                     render_policy=policy)


# ============================================================
# M3. art.table.earthwork_balance — 一般土石方平衡表
# ============================================================
# 对齐样稿: 表4.4-2 (报告表) / 表2.4-1 (报告书)
# 列: 序号 / 项目组成 / 挖方 / 填方 / 调入(数量+来源) / 调出(数量+去向) / 借方(数量+来源) / 弃方(数量+去向)
# v0: 只有汇总级, 列对齐但只出 1 行"项目合计"; v1 补分项后扩成多行

SPEC_EARTHWORK = TableSpec(
    table_id="art.table.earthwork_balance",
    title="一般土石方 (不含表土) 平衡表",
    columns=[
        TableColumn(key="seq", header="序号", unit="", align="center", fmt="str"),
        TableColumn(key="component", header="项目组成", unit="", align="left", fmt="str"),
        TableColumn(key="excavation", header="挖方", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="fill", header="填方", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="transfer_in", header="调入", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="transfer_in_source", header="调入来源", unit="", align="left", fmt="str"),
        TableColumn(key="transfer_out", header="调出", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="transfer_out_dest", header="调出去向", unit="", align="left", fmt="str"),
        TableColumn(key="borrow", header="借方", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="spoil", header="弃方", unit="万m\u00b3", align="right", fmt="2f"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.earthwork.* | 单位: 万m\u00b3 (自然方) | v0 为项目合计级, v1 补分项",
    section_id="sec.project_overview.earthwork_balance",
)


def project_earthwork_balance(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    exc = _get(facts, "field.fact.earthwork.excavation")
    fill = _get(facts, "field.fact.earthwork.fill")
    borrow = _get(facts, "field.fact.earthwork.borrow")
    spoil = _get(facts, "field.fact.earthwork.spoil")
    self_reuse = _get(facts, "field.fact.earthwork.self_reuse")
    comp_reuse = _get(facts, "field.fact.earthwork.comprehensive_reuse")

    # v0 单行合计
    row = {
        "seq": "",
        "component": "项目合计",
        "excavation": exc,
        "fill": fill,
        "transfer_in": self_reuse,  # 本项目利用=调入
        "transfer_in_source": "本项目" if self_reuse else "",
        "transfer_out": comp_reuse,
        "transfer_out_dest": "综合利用" if comp_reuse and float(comp_reuse or 0) > 0 else "",
        "borrow": borrow,
        "spoil": spoil,
    }
    return TableData(spec=SPEC_EARTHWORK, rows=[row], total_row=row.copy(),
                     render_policy=TableRenderPolicy.RENDER_WITH_VALUES)


# ============================================================
# M2. art.table.topsoil_balance — 表土平衡表
# ============================================================
# 对齐样稿: 表4.4-1 (报告表)
# 列: 序号 / 项目组成 / 开挖 / 回填 / 调入(数量+来源) / 调出(数量+去向)
# v0: 合计级, 列对齐样稿

SPEC_TOPSOIL = TableSpec(
    table_id="art.table.topsoil_balance",
    title="表土平衡表",
    columns=[
        TableColumn(key="seq", header="序号", unit="", align="center", fmt="str"),
        TableColumn(key="component", header="项目组成", unit="", align="left", fmt="str"),
        TableColumn(key="excavation", header="开挖 (剥离)", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="fill", header="回填 (覆土)", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="transfer_in", header="调入", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="transfer_in_source", header="来源", unit="", align="left", fmt="str"),
        TableColumn(key="transfer_out", header="调出", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="transfer_out_dest", header="去向", unit="", align="left", fmt="str"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.topsoil.* | 部分为 placeholder stub, '—' 表示待措施布设确认",
    section_id="sec.topsoil.balance",
)


def project_topsoil_balance(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    s_vol = _get(facts, "field.fact.topsoil.stripable_volume")
    r_vol = _get(facts, "field.fact.topsoil.fill")

    row = {
        "seq": "",
        "component": "项目合计",
        "excavation": s_vol,
        "fill": r_vol,
        "transfer_in": r_vol,  # 回覆量=调入
        "transfer_in_source": "本项目剥离" if r_vol else "",
        "transfer_out": None,
        "transfer_out_dest": "",
    }
    warnings = []
    if r_vol is None:
        warnings.append("topsoil.fill (回覆量) 为 placeholder stub")
    policy = TableRenderPolicy.RENDER_WITH_PLACEHOLDER if warnings else TableRenderPolicy.RENDER_WITH_VALUES
    return TableData(spec=SPEC_TOPSOIL, rows=[row], total_row=row.copy(),
                     render_policy=policy, warnings=warnings)


# ============================================================
# 3 (unchanged). art.table.land_occupation_by_county — 分县占地表
# ============================================================
# 保留为条件表, 不在正文默认位置出现

SPEC_COUNTY_LAND = TableSpec(
    table_id="art.table.land_occupation_by_county",
    title="分县 (区) 占地表",
    columns=[
        TableColumn(key="county", header="县 (区)", unit="", align="left", fmt="str"),
        TableColumn(key="nature", header="占地性质", unit="", align="center", fmt="str"),
        TableColumn(key="type", header="占地类型", unit="", align="center", fmt="str"),
        TableColumn(key="area", header="面积", unit="hm\u00b2", align="right", fmt="2f"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.land.county_breakdown | 条件性附表, 跨行政区项目适用",
    section_id="",  # M4: 不绑定正文 section, 降级为条件附表
)


def project_land_occupation_by_county(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    breakdown = facts.get("field.fact.land.county_breakdown")
    if not isinstance(breakdown, list) or not breakdown:
        return TableData(spec=SPEC_COUNTY_LAND, rows=[], total_row=None,
                         render_policy=TableRenderPolicy.SKIP_RENDER,
                         warnings=["county_breakdown 缺失"])
    rows = []
    total_area = 0.0
    for rec in breakdown:
        area_val = rec.get("area")
        if isinstance(area_val, dict):
            area_val = area_val.get("value")
        rows.append({
            "county": rec.get("county", "—"),
            "nature": rec.get("nature", "—"),
            "type": rec.get("type", "—"),
            "area": area_val,
        })
        if area_val is not None:
            total_area += float(area_val)
    total_row = {"county": "合计", "nature": "", "type": "", "area": total_area}
    return TableData(spec=SPEC_COUNTY_LAND, rows=rows, total_row=total_row,
                     render_policy=TableRenderPolicy.RENDER_WITH_VALUES)


# ============================================================
# M4. art.table.responsibility_range_by_admin_division
# ============================================================
# 降级为条件附表: section_id 清空, 不再绑定正文 7.1.1
# 正文位置留给未来的 "防治分区面积表" (N1, v1 补 facts)

SPEC_RESP_RANGE = TableSpec(
    table_id="art.table.responsibility_range_by_admin_division",
    title="防治责任范围按行政区统计表",
    columns=[
        TableColumn(key="admin_area", header="行政区", unit="", align="left", fmt="str"),
        TableColumn(key="resp_area", header="责任范围面积", unit="hm\u00b2", align="right", fmt="2f"),
        TableColumn(key="ratio", header="占比", unit="%", align="right", fmt="1f"),
    ],
    has_total_row=True,
    footnote="条件性附表: 仅跨行政区项目适用 | 数据来源: field.fact.land.county_breakdown",
    section_id="",  # M4: 降级, 不绑定正文 section
)


def project_responsibility_range(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    breakdown = facts.get("field.fact.land.county_breakdown")
    if not isinstance(breakdown, list) or not breakdown:
        return TableData(spec=SPEC_RESP_RANGE, rows=[], total_row=None,
                         render_policy=TableRenderPolicy.SKIP_RENDER,
                         warnings=["county_breakdown 缺失"])
    rows = []
    grand_total = 0.0
    for rec in breakdown:
        area_val = rec.get("area")
        if isinstance(area_val, dict):
            area_val = area_val.get("value")
        county = rec.get("county", "—")
        if area_val is not None:
            grand_total += float(area_val)
        rows.append({"admin_area": county, "resp_area": area_val, "ratio": None})
    for row in rows:
        if row["resp_area"] is not None and grand_total > 0:
            row["ratio"] = round(float(row["resp_area"]) / grand_total * 100, 1)
    total_row = {"admin_area": "合计", "resp_area": grand_total, "ratio": 100.0}
    return TableData(spec=SPEC_RESP_RANGE, rows=rows, total_row=total_row,
                     render_policy=TableRenderPolicy.RENDER_WITH_VALUES)


# ============================================================
# 5 (unchanged). art.table.spoil_summary
# ============================================================

SPEC_SPOIL_SUMMARY = TableSpec(
    table_id="art.table.spoil_summary",
    title="弃渣场和临时堆土场设置汇总表",
    columns=[
        TableColumn(key="site_id", header="编号", unit="", align="center", fmt="str"),
        TableColumn(key="name", header="名称", unit="", align="left", fmt="str"),
        TableColumn(key="type", header="类型", unit="", align="center", fmt="str"),
        TableColumn(key="volume", header="容量/堆渣量", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="max_height", header="最大高度", unit="m", align="right", fmt="1f"),
        TableColumn(key="level", header="级别", unit="", align="center", fmt="str"),
    ],
    has_total_row=False,
    footnote="弃渣场级别依据 GB 51018-2014 表 5.7.1; 临时堆土场不适用弃渣场分级",
    section_id="sec.disposal_site.site_selection",
)


def project_spoil_summary(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    derived = snapshot.get("derived_fields") or {}
    disposal_facts = facts.get("field.fact.disposal_site.level_assessment") or []
    disposal_derived = derived.get("field.derived.disposal_site.level_assessment") or []
    temp_sites = facts.get("field.fact.construction.temp_topsoil_site") or []

    level_by_id = {}
    for sd in disposal_derived:
        if isinstance(sd, dict):
            level_by_id[sd.get("site_id")] = sd.get("level", "—")

    rows = []
    for sf in disposal_facts:
        if not isinstance(sf, dict):
            continue
        sid = sf.get("site_id", "?")
        vol = sf.get("volume")
        if isinstance(vol, dict): vol = vol.get("value")
        ht = sf.get("max_height")
        if isinstance(ht, dict): ht = ht.get("value")
        rows.append({
            "site_id": sid, "name": sf.get("site_name", sid), "type": "弃渣场",
            "volume": vol, "max_height": ht, "level": level_by_id.get(sid, "—"),
        })
    for ts in temp_sites:
        if not isinstance(ts, dict): continue
        sid = ts.get("name_or_id", ts.get("site_id", "?"))
        vol = ts.get("storage_volume")
        if isinstance(vol, dict): vol = vol.get("value")
        rows.append({
            "site_id": sid, "name": sid,
            "type": ts.get("type", "临时堆土场"),
            "volume": vol, "max_height": None, "level": "不适用",
        })
    policy = TableRenderPolicy.RENDER_WITH_VALUES if rows else TableRenderPolicy.RENDER_NOT_APPLICABLE
    return TableData(spec=SPEC_SPOIL_SUMMARY, rows=rows, render_policy=policy)


# ============================================================
# N2. art.table.six_indicator_review — 六项指标完成情况复核表
# ============================================================
# 对齐样稿: 表10.3-5 (报告表) / 表7.2-3 (报告书)
# 列: 指标项目 / 计算公式 / 目标值 / 实现值 / 达标判定
# 数据来源: field.derived.target.* (目标值 + 实际值)

SPEC_SIX_INDICATOR = TableSpec(
    table_id="art.table.six_indicator_review",
    title="水保方案六项指标完成情况复核",
    columns=[
        TableColumn(key="indicator", header="防治指标", unit="", align="left", fmt="str"),
        TableColumn(key="formula", header="计算公式", unit="", align="left", fmt="str"),
        TableColumn(key="target", header="目标值", unit="", align="right", fmt="str"),
        TableColumn(key="actual", header="实现值", unit="", align="right", fmt="str"),
        TableColumn(key="result", header="达标判定", unit="", align="center", fmt="str"),
    ],
    has_total_row=False,
    footnote="目标值来源: cal.target.weighted_comprehensive / GB/T 50434-2018 | 实现值来源: field.derived.target.*",
    section_id="sec.soil_loss_prevention.benefit_analysis",
)

_INDICATOR_META = [
    ("control_degree", "水土流失治理度 (%)",
     "治理达标面积 / 水土流失总面积"),
    ("soil_loss_control_ratio", "土壤流失控制比",
     "容许土壤流失量 / 治理后年均土壤流失量"),
    ("spoil_protection_rate", "渣土防护率 (%)",
     "实际挡护的弃渣量 / 弃渣总量"),
    ("topsoil_protection_rate", "表土保护率 (%)",
     "保护的表土量 / 可剥离表土总量"),
    ("vegetation_restoration_rate", "林草植被恢复率 (%)",
     "林草植被面积 / 可恢复面积"),
    ("vegetation_coverage_rate", "林草覆盖率 (%)",
     "林草植被面积 / 责任范围总面积"),
]


def project_six_indicator_review(snapshot: dict) -> TableData:
    derived = snapshot.get("derived_fields") or {}
    facts = snapshot.get("_original_facts") or {}

    # 目标值: 从加权综合目标取 (多等级) 或从直接查表取 (单等级)
    wt = derived.get("field.derived.target.weighted_comprehensive_target") or {}

    # 实际值: 从 field.derived.target.* 各指标取
    actual_map = {}
    for key, _, _ in _INDICATOR_META:
        actual_field = derived.get(f"field.derived.target.{key}")
        if isinstance(actual_field, dict):
            actual_map[key] = actual_field.get("value")
            # 也可能有 actual_derived 子字段
            if actual_field.get("actual_derived") is not None:
                actual_map[key] = actual_field["actual_derived"]
        elif actual_field is not None:
            actual_map[key] = actual_field

    rows = []
    for key, label, formula in _INDICATOR_META:
        target_val = wt.get(key) if isinstance(wt, dict) else None
        actual_val = actual_map.get(key)

        # 格式化
        if key == "soil_loss_control_ratio":
            t_str = str(target_val) if target_val is not None else "—"
            a_str = str(actual_val) if actual_val is not None else "—"
        else:
            t_str = f"{target_val}" if target_val is not None else "—"
            a_str = f"{actual_val}" if actual_val is not None else "—"

        # 达标判定
        if target_val is not None and actual_val is not None:
            try:
                if key == "soil_loss_control_ratio":
                    # 控制比: 实际值 >= 目标值 即达标
                    result = "达标" if float(actual_val) >= float(target_val) else "未达标"
                else:
                    # 百分比: 实际值 >= 目标值 即达标
                    result = "达标" if float(actual_val) >= float(target_val) else "未达标"
            except (ValueError, TypeError):
                result = "—"
        else:
            result = "—"

        rows.append({
            "indicator": label,
            "formula": formula,
            "target": t_str,
            "actual": a_str,
            "result": result,
        })

    policy = TableRenderPolicy.RENDER_WITH_VALUES if any(
        r["target"] != "—" for r in rows
    ) else TableRenderPolicy.RENDER_WITH_PLACEHOLDER

    return TableData(spec=SPEC_SIX_INDICATOR, rows=rows, render_policy=policy)


# ============================================================
# Registry
# ============================================================

TABLE_PROJECTIONS = {
    "art.table.total_land_occupation": project_total_land_occupation,
    "art.table.earthwork_balance": project_earthwork_balance,
    "art.table.land_occupation_by_county": project_land_occupation_by_county,
    "art.table.topsoil_balance": project_topsoil_balance,
    "art.table.responsibility_range_by_admin_division": project_responsibility_range,
    "art.table.spoil_summary": project_spoil_summary,
    "art.table.six_indicator_review": project_six_indicator_review,  # N2
}
