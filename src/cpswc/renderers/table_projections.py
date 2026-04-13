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
# Step 16: Investment Summary Tables
# ============================================================
# 对齐样稿: 表10.2-3 (报告表) / 附表1 (报告书)
# 行骨架: 五部分 + 预备费 + 补偿费 + 总投资
# v0: 仅补偿费行 live, 其余 "—"
# 空值三态: "—" = 未提供, "0.00" = 明确为零, "/" = 不适用

# 投资行骨架 (固定, 对齐样稿)
_INVESTMENT_ROWS = [
    ("part1", "一", "第一部分 工程措施"),
    ("part2", "二", "第二部分 植物措施"),
    ("part3", "三", "第三部分 监测措施"),
    ("part4", "四", "第四部分 临时措施"),
    ("part5", "五", "第五部分 独立费用"),
    ("subtotal_1_5", "I", "一至五部分合计"),
    ("reserve", "II", "基本预备费"),
    ("compensation", "III", "水土保持补偿费"),
    ("grand_total", "", "水土保持工程总投资 (I+II+III)"),
]

SPEC_INVESTMENT_TOTAL = TableSpec(
    table_id="art.table.investment.total_summary",
    title="水土保持工程总投资估算表",
    columns=[
        TableColumn(key="seq", header="序号", unit="", align="center", fmt="str"),
        TableColumn(key="name", header="工程或费用名称", unit="", align="left", fmt="str"),
        TableColumn(key="amount", header="金额", unit="万元", align="right", fmt="2f"),
    ],
    has_total_row=False,  # 总计行已内含在行骨架里
    footnote="",  # 脚注在 projection 里动态设置
    section_id="sec.investment.summary",
)


def _compute_independent_fees(snapshot: dict) -> dict:
    """计算独立费用各项及预备费, 供 total_summary 和 appendix_fees 共用.

    Returns dict with keys:
      base: 计费基数 (新增一至四部分合计, 万元) or None
      indep_total: 独立费用小计 (万元) or 0
      reserve: 预备费 (万元) or None
      items: dict[row_id → amount(万元) or None]
    """
    facts = snapshot.get("_original_facts") or {}
    summary = facts.get("field.fact.investment.measures_summary") or {}

    cats = ["工程措施", "植物措施", "监测措施", "临时措施"]
    parts = [summary[c].get("new", 0) or 0 for c in cats if c in summary]
    base = sum(parts) if parts else None

    items = {}
    indep_total = 0.0
    has_value = False

    for row_id, _seq, _name, rate_pct, _basis, fact_key in _INDEP_FEE_DEFS:
        amount = None
        if row_id == "tender":
            amount = 0.0
        elif rate_pct is not None and base is not None:
            amount = round(base * rate_pct, 2)
            has_value = True
        elif fact_key is not None:
            v = facts.get(fact_key)
            if isinstance(v, dict) and "value" in v:
                amount = round(float(v["value"]), 2)
                has_value = True
            elif isinstance(v, (int, float)):
                amount = round(float(v), 2)
                has_value = True
        if amount is not None:
            indep_total += amount
        items[row_id] = amount

    reserve = None
    if base is not None:
        reserve = round((base + indep_total) * 0.10, 2)
        has_value = True

    return {
        "base": base,
        "indep_total": round(indep_total, 2) if has_value else None,
        "reserve": reserve,
        "items": items,
        "has_value": has_value,
    }


def project_investment_total_summary(snapshot: dict) -> TableData:
    """投资估算总表: 行骨架固定, 从 measures_summary + 独立费用计算填充"""
    derived = snapshot.get("derived_fields") or {}
    facts = snapshot.get("_original_facts") or {}
    comp_fee = derived.get("field.derived.investment.compensation_fee_amount")
    summary = facts.get("field.fact.investment.measures_summary") or {}
    indep = _compute_independent_fees(snapshot)

    cat_map = {
        "part1": "工程措施",
        "part2": "植物措施",
        "part3": "监测措施",
        "part4": "临时措施",
    }

    rows = []
    subtotal_1_4 = 0.0
    subtotal_1_5 = None
    reserve_amount = None
    comp_amount = None
    for row_id, seq, name in _INVESTMENT_ROWS:
        amount = None
        cat = cat_map.get(row_id)
        if cat and cat in summary:
            amount = round(summary[cat]["total"], 2)
            subtotal_1_4 += amount
        elif row_id == "part5" and indep["indep_total"] is not None:
            amount = indep["indep_total"]
        elif row_id == "subtotal_1_5" and subtotal_1_4 > 0:
            indep_val = indep["indep_total"] or 0
            amount = round(subtotal_1_4 + indep_val, 2)
            subtotal_1_5 = amount
        elif row_id == "reserve" and indep["reserve"] is not None:
            amount = indep["reserve"]
            reserve_amount = amount
        elif row_id == "compensation" and comp_fee is not None:
            amount = comp_fee
            comp_amount = comp_fee
        elif row_id == "grand_total":
            parts = [v for v in [subtotal_1_5, reserve_amount, comp_amount]
                     if v is not None]
            if parts:
                amount = round(sum(parts), 2)
        rows.append({"seq": seq, "name": name, "amount": amount})

    live_items = []
    if indep["has_value"]:
        live_items.append(f"独立费用={indep['indep_total']:.2f}")
    if indep["reserve"] is not None:
        live_items.append(f"预备费={indep['reserve']:.2f}")
    if comp_fee is not None:
        live_items.append("补偿费")
    footnote = (
        f"live 数据: {', '.join(live_items) if live_items else '无'}。"
        f"'—' 表示数据未提供, 非计算错误。"
    )

    spec = TableSpec(
        table_id=SPEC_INVESTMENT_TOTAL.table_id,
        title=SPEC_INVESTMENT_TOTAL.title,
        columns=SPEC_INVESTMENT_TOTAL.columns,
        has_total_row=False,
        footnote=footnote,
        section_id=SPEC_INVESTMENT_TOTAL.section_id,
    )

    return TableData(
        spec=spec, rows=rows,
        render_policy=TableRenderPolicy.RENDER_WITH_PLACEHOLDER,
    )


# ============================================================
# 主体已列 / 方案新增 汇总表
# ============================================================

SPEC_INVESTMENT_SPLIT = TableSpec(
    table_id="art.table.investment.split_summary",
    title="水土保持投资分类汇总表 (主体已列 / 方案新增)",
    columns=[
        TableColumn(key="seq", header="序号", unit="", align="center", fmt="str"),
        TableColumn(key="name", header="费用项", unit="", align="left", fmt="str"),
        TableColumn(key="scheme_new", header="方案新增", unit="万元", align="right", fmt="2f"),
        TableColumn(key="existing", header="主体已有", unit="万元", align="right", fmt="2f"),
        TableColumn(key="total", header="总投资", unit="万元", align="right", fmt="2f"),
    ],
    has_total_row=False,
    footnote="",
    section_id="sec.investment.summary",
)


def project_investment_split_summary(snapshot: dict) -> TableData:
    """主体已列/方案新增汇总: 从 measures_summary + 独立费用计算填充"""
    derived = snapshot.get("derived_fields") or {}
    facts = snapshot.get("_original_facts") or {}
    comp_fee = derived.get("field.derived.investment.compensation_fee_amount")
    summary = facts.get("field.fact.investment.measures_summary") or {}
    indep = _compute_independent_fees(snapshot)

    cat_map = {"part1": "工程措施", "part2": "植物措施",
               "part3": "监测措施", "part4": "临时措施"}

    rows = []
    sum_new = 0.0
    sum_existing = 0.0
    sum_total = 0.0
    has_parts = False
    for row_id, seq, name in _INVESTMENT_ROWS:
        scheme_new = None
        existing = None
        total = None
        cat = cat_map.get(row_id)
        if cat and cat in summary:
            scheme_new = round(summary[cat]["new"], 2)
            existing = round(summary[cat]["existing"], 2)
            total = round(summary[cat]["total"], 2)
            sum_new += scheme_new
            sum_existing += existing
            sum_total += total
            has_parts = True
        elif row_id == "part5" and indep["indep_total"] is not None:
            scheme_new = indep["indep_total"]
            existing = 0
            total = indep["indep_total"]
            sum_new += scheme_new
            sum_total += total
            has_parts = True
        elif row_id == "subtotal_1_5" and has_parts:
            scheme_new = round(sum_new, 2)
            existing = round(sum_existing, 2)
            total = round(sum_total, 2)
        elif row_id == "reserve" and indep["reserve"] is not None:
            scheme_new = indep["reserve"]
            existing = 0
            total = indep["reserve"]
            sum_new += scheme_new
            sum_total += total
        elif row_id == "compensation" and comp_fee is not None:
            scheme_new = comp_fee
            existing = 0
            total = comp_fee
            sum_new += scheme_new
            sum_total += total
        elif row_id == "grand_total" and has_parts:
            scheme_new = round(sum_new, 2)
            existing = round(sum_existing, 2)
            total = round(sum_total, 2)
        rows.append({
            "seq": seq, "name": name,
            "scheme_new": scheme_new, "existing": existing, "total": total,
        })

    footnote = (
        "独立费用/预备费由公式计算 (全额计入方案新增)。"
        "主体已列/方案新增的拆分由设计院在录入工程量时标注。"
        "'—' 表示数据未提供。"
    )

    spec = TableSpec(
        table_id=SPEC_INVESTMENT_SPLIT.table_id,
        title=SPEC_INVESTMENT_SPLIT.title,
        columns=SPEC_INVESTMENT_SPLIT.columns,
        has_total_row=False,
        footnote=footnote,
        section_id=SPEC_INVESTMENT_SPLIT.section_id,
    )

    return TableData(
        spec=spec, rows=rows,
        render_policy=TableRenderPolicy.RENDER_WITH_PLACEHOLDER,
    )


# ============================================================
# Step 17: Investment Appendix Skeletons
# ============================================================
# 附表结构对齐样稿, 数据全 "—" (v0 无分项 facts)
# 目的: 验证 INVESTMENT_FACTS_BACKFILL_CONTRACT 的输出可落地性

SPEC_APPENDIX_TOTAL = TableSpec(
    table_id="art.table.investment.appendix_total",
    title="附表 1 水土保持工程投资估算总表",
    columns=[
        TableColumn(key="seq", header="序号", unit="", align="center", fmt="str"),
        TableColumn(key="name", header="工程或费用名称", unit="", align="left", fmt="str"),
        TableColumn(key="construction", header="建安工程费", unit="万元", align="right", fmt="2f"),
        TableColumn(key="plant", header="植物措施费", unit="万元", align="right", fmt="2f"),
        TableColumn(key="independent", header="独立费用", unit="万元", align="right", fmt="2f"),
        TableColumn(key="new_total", header="方案新增投资", unit="万元", align="right", fmt="2f"),
        TableColumn(key="existing", header="主体已有投资", unit="万元", align="right", fmt="2f"),
        TableColumn(key="grand_total", header="工程总投资", unit="万元", align="right", fmt="2f"),
    ],
    has_total_row=False,
    footnote="",
    section_id="",  # 附表, 不绑定正文 section
)

SPEC_APPENDIX_EXISTING = TableSpec(
    table_id="art.table.investment.appendix_existing",
    title="附表 3 主体工程已列水土保持措施投资",
    columns=[
        TableColumn(key="seq", header="序号", unit="", align="center", fmt="str"),
        TableColumn(key="name", header="措施名称", unit="", align="left", fmt="str"),
        TableColumn(key="unit", header="单位", unit="", align="center", fmt="str"),
        TableColumn(key="quantity", header="数量", unit="", align="right", fmt="2f"),
        TableColumn(key="unit_price", header="单价 (元)", unit="", align="right", fmt="2f"),
        TableColumn(key="amount", header="合价 (万元)", unit="", align="right", fmt="2f"),
    ],
    has_total_row=True,
    footnote="主体已列措施由设计院在录入时以 source_attribution='主体已列' 标注",
    section_id="",
)

SPEC_APPENDIX_FEES = TableSpec(
    table_id="art.table.investment.appendix_fees",
    title="附表 4 独立费用 / 预备费 / 专项费用估算表",
    columns=[
        TableColumn(key="seq", header="序号", unit="", align="center", fmt="str"),
        TableColumn(key="name", header="费用名称", unit="", align="left", fmt="str"),
        TableColumn(key="basis", header="计算依据", unit="", align="left", fmt="str"),
        TableColumn(key="rate", header="费率", unit="", align="center", fmt="str"),
        TableColumn(key="base", header="计费基数 (万元)", unit="", align="right", fmt="2f"),
        TableColumn(key="amount", header="费用 (万元)", unit="", align="right", fmt="2f"),
    ],
    has_total_row=False,
    footnote="",
    section_id="",
)

# 独立费用 7 子项定义
# row_id: (seq, name, rate_pct|None, basis_text, fact_key|None)
# rate_pct: 有百分比费率的行, 可从 base 计算
# fact_key: 无公式、需从 facts 读取金额的行
_INDEP_FEE_DEFS = [
    ("mgmt",    "1", "建设单位管理费",       0.03,  "(一至四部分)×3%",                   None),
    ("tender",  "2", "招标业务费",           None,  "不发生",                            None),
    ("consult", "3", "经济技术咨询费",       None,  "按实际计列",                        "field.fact.investment.fee_consulting"),
    ("supv",    "4", "工程建设监理费",       None,  "发改价格[2007]670号",               "field.fact.investment.fee_supervision"),
    ("cost_sv", "5", "工程造价咨询服务费",   None,  "粤价函[2011]724号",                 "field.fact.investment.fee_cost_consulting"),
    ("survey",  "6", "科研勘测设计费",       0.0108, "(一至四部分)×1.08%",               None),
    ("accept",  "7", "水土保持设施验收咨询费", None, "按市场价",                          "field.fact.investment.fee_acceptance"),
]


def project_appendix_total(snapshot: dict) -> TableData:
    """附表1: 多列版投资总表, 从 overlay + 独立费用计算填充"""
    derived = snapshot.get("derived_fields") or {}
    facts = snapshot.get("_original_facts") or {}
    comp_fee = derived.get("field.derived.investment.compensation_fee_amount")
    summary = facts.get("field.fact.investment.measures_summary") or {}
    indep = _compute_independent_fees(snapshot)

    cat_map = {"part1": "工程措施", "part2": "植物措施",
               "part3": "监测措施", "part4": "临时措施"}

    rows = []
    for row_id, seq, name in _INVESTMENT_ROWS:
        row = {"seq": seq, "name": name,
               "construction": None, "plant": None, "independent": None,
               "new_total": None, "existing": None, "grand_total": None}
        cat = cat_map.get(row_id)
        if cat and cat in summary:
            s = summary[cat]
            if cat in ("工程措施", "临时措施", "监测措施"):
                row["construction"] = round(s["total"], 2)
            elif cat == "植物措施":
                row["plant"] = round(s["total"], 2)
            row["new_total"] = round(s["new"], 2)
            row["existing"] = round(s["existing"], 2)
            row["grand_total"] = round(s["total"], 2)
        elif row_id == "part5" and indep["indep_total"] is not None:
            row["independent"] = indep["indep_total"]
            row["new_total"] = indep["indep_total"]
            row["existing"] = 0
            row["grand_total"] = indep["indep_total"]
        elif row_id == "reserve" and indep["reserve"] is not None:
            row["new_total"] = indep["reserve"]
            row["existing"] = 0
            row["grand_total"] = indep["reserve"]
        elif row_id == "compensation" and comp_fee is not None:
            row["new_total"] = comp_fee
            row["existing"] = 0
            row["grand_total"] = comp_fee
        rows.append(row)
    footnote = (
        "附表版投资估算总表 (对齐样稿附表1) | "
        "独立费用/预备费由公式计算, 补偿费由 cal.compensation.fee 计算"
    )
    spec = TableSpec(
        table_id=SPEC_APPENDIX_TOTAL.table_id,
        title=SPEC_APPENDIX_TOTAL.title,
        columns=SPEC_APPENDIX_TOTAL.columns,
        has_total_row=False, footnote=footnote, section_id="",
    )
    return TableData(spec=spec, rows=rows,
                     render_policy=TableRenderPolicy.RENDER_WITH_PLACEHOLDER)


def project_appendix_existing(snapshot: dict) -> TableData:
    """附表3: 主体已列措施投资 — 从 overlay 取 source_attribution='主体已列' 的条目"""
    facts = snapshot.get("_original_facts") or {}
    registry = facts.get("field.fact.investment.measures_registry") or []

    existing = [m for m in registry if m.get("source_attribution") == "主体已列"]

    if not existing:
        rows = [{"seq": "—", "name": "(待录入主体已列措施条目)",
                 "unit": "—", "quantity": None, "unit_price": None, "amount": None}]
        total_row = {"seq": "", "name": "合计", "unit": "", "quantity": None,
                     "unit_price": None, "amount": None}
        return TableData(spec=SPEC_APPENDIX_EXISTING, rows=rows, total_row=total_row,
                         render_policy=TableRenderPolicy.RENDER_WITH_PLACEHOLDER)

    rows = []
    total_amount = 0.0
    for i, m in enumerate(existing, 1):
        amt = m.get("amount_wan")
        if amt is not None:
            total_amount += float(amt)
        rows.append({
            "seq": str(i),
            "name": m.get("measure_name", "—"),
            "unit": m.get("unit", "—"),
            "quantity": m.get("quantity"),
            "unit_price": m.get("unit_price"),
            "amount": amt,
        })
    total_row = {"seq": "", "name": "合计", "unit": "", "quantity": None,
                 "unit_price": None, "amount": round(total_amount, 2)}
    return TableData(spec=SPEC_APPENDIX_EXISTING, rows=rows, total_row=total_row,
                     render_policy=TableRenderPolicy.RENDER_WITH_VALUES)


def project_appendix_fees(snapshot: dict) -> TableData:
    """附表4: 独立费用 / 预备费 / 补偿费估算表

    计算逻辑:
      base = 新增(工程措施 + 植物措施 + 监测措施 + 临时措施)
      建设管理费 = base × 3%
      科研勘测设计费 = base × 1.08%
      其余子项 = 从 facts 读取 (按实际/市场价, 无通用公式)
      预备费 = (一至五部分合计) × 10%
      补偿费 = 从 calculator derived
    """
    derived = snapshot.get("derived_fields") or {}
    indep = _compute_independent_fees(snapshot)
    base = indep["base"]
    has_any_value = indep["has_value"]

    rows = []
    indep_total = 0.0

    for row_id, seq, name, rate_pct, basis_text, _fact_key in _INDEP_FEE_DEFS:
        amount = indep["items"].get(row_id)
        rate_str = ""
        base_val = None

        if rate_pct is not None and base is not None:
            base_val = round(base, 2)
            rate_str = f"{rate_pct * 100:.0f}%" if rate_pct >= 0.01 else f"{rate_pct * 100:.2f}%"

        if amount is not None:
            indep_total += amount

        rows.append({
            "seq": seq, "name": name, "basis": basis_text,
            "rate": rate_str, "base": base_val, "amount": amount,
        })

    # 独立费用小计
    rows.append({
        "seq": "五", "name": "独立费用小计", "basis": "",
        "rate": "", "base": None,
        "amount": indep["indep_total"],
    })

    # 预备费
    reserve_base = round(base + indep_total, 2) if base is not None else None
    rows.append({
        "seq": "六", "name": "基本预备费", "basis": "(一至五)×10%",
        "rate": "10%", "base": reserve_base, "amount": indep["reserve"],
    })

    # 补偿费
    comp_fee = derived.get("field.derived.investment.compensation_fee_amount")
    if comp_fee is not None:
        has_any_value = True
    rows.append({
        "seq": "七", "name": "水土保持补偿费", "basis": "cal.compensation.fee",
        "rate": "", "base": None, "amount": comp_fee,
    })

    # 合计行
    grand_parts = [indep["indep_total"] or 0, indep["reserve"] or 0, comp_fee or 0]
    grand_total = round(sum(grand_parts), 2) if has_any_value else None
    rows.append({
        "seq": "", "name": "合  计", "basis": "",
        "rate": "", "base": None, "amount": grand_total,
    })

    # 动态脚注
    live = []
    if base is not None:
        live.append(f"计费基数={base:.2f}万元 (新增一至四部分)")
    if comp_fee is not None:
        live.append(f"补偿费={comp_fee:.2f}万元")
    footnote = (
        "费率依据: 建设管理费3% / 科研勘测设计费1.08% / 预备费10% | "
        + ("; ".join(live) if live else "measures_summary 未提供, 公式行留白")
    )

    spec = TableSpec(
        table_id=SPEC_APPENDIX_FEES.table_id,
        title=SPEC_APPENDIX_FEES.title,
        columns=SPEC_APPENDIX_FEES.columns,
        has_total_row=False,
        footnote=footnote,
        section_id="",
    )

    return TableData(
        spec=spec, rows=rows,
        render_policy=(TableRenderPolicy.RENDER_WITH_VALUES if has_any_value
                       else TableRenderPolicy.RENDER_WITH_PLACEHOLDER),
    )


# ============================================================
# 特性表 — art.table.spec_sheet (工程特性表)
# ============================================================
# 对齐样稿: 表 2.1-1 工程特性表
# 三部分: 一、项目基本情况  二、项目组成及占地  三、土石方平衡
# v0: 两列 key-value 表, 从 facts 直接投影

SPEC_SPEC_SHEET = TableSpec(
    table_id="art.table.spec_sheet",
    title="工程特性表",
    columns=[
        TableColumn(key="item", header="项目", unit="", align="left", fmt="str"),
        TableColumn(key="value", header="内容", unit="", align="left", fmt="str"),
    ],
    has_total_row=False,
    footnote="数据来源: facts 直接投影 (对齐样稿工程特性表)",
    section_id="sec.overview.spec_sheet_end",
)


def _fmt_q(facts: dict, key: str, suffix: str = "") -> str:
    """Format a Quantity fact as 'value unit' or '—'"""
    v = facts.get(key)
    if v is None:
        return "—"
    if isinstance(v, dict) and "value" in v:
        val = v["value"]
        unit = v.get("unit", "")
        return f"{val} {unit}".strip() + suffix
    if isinstance(v, list):
        return "、".join(str(x) for x in v) if v else "—"
    return str(v) if v else "—"


def project_spec_sheet(snapshot: dict) -> TableData:
    """工程特性表: 三部分 key-value 投影"""
    facts = snapshot.get("_original_facts") or {}
    derived = snapshot.get("derived_fields") or {}
    rows: list[dict] = []

    def _add(item: str, value: str):
        rows.append({"item": item, "value": value})

    def _section(title: str):
        rows.append({"item": title, "value": ""})

    # ── 一、项目基本情况 ──
    _section("一、项目基本情况")
    _add("项目名称", _fmt_q(facts, "field.fact.project.name"))
    code = facts.get("field.fact.project.code")
    if code:
        _add("项目代码", str(code))
    _add("建设单位", _fmt_q(facts, "field.fact.project.builder"))
    _add("编制单位", _fmt_q(facts, "field.fact.project.compiler"))
    _add("行业类别", _fmt_q(facts, "field.fact.project.industry_category"))
    _add("建设性质", _fmt_q(facts, "field.fact.project.nature"))

    # 位置
    province = _fmt_q(facts, "field.fact.location.province_list")
    prefecture = _fmt_q(facts, "field.fact.location.prefecture_list")
    county = _fmt_q(facts, "field.fact.location.county_list")
    _add("涉及省（市、区）", province)
    _add("涉及地市", prefecture)
    _add("涉及县", county)
    _add("流域管理机构", _fmt_q(facts, "field.fact.location.river_basin_agency"))

    # 投资
    _add("总投资", _fmt_q(facts, "field.fact.investment.total_investment"))
    _add("土建投资", _fmt_q(facts, "field.fact.investment.civil_investment"))

    # 工期
    start = _fmt_q(facts, "field.fact.schedule.start_time")
    end = _fmt_q(facts, "field.fact.schedule.end_time")
    _add("动工时间", start)
    _add("完工时间", end)
    _add("设计水平年", _fmt_q(facts, "field.fact.schedule.design_horizon_year"))

    # 占地
    _add("总占地面积", _fmt_q(facts, "field.fact.land.total_area"))
    _add("永久占地", _fmt_q(facts, "field.fact.land.permanent_area"))
    _add("临时占地", _fmt_q(facts, "field.fact.land.temporary_area"))

    # ── 二、项目组成及占地情况 ──
    breakdown = facts.get("field.fact.land.county_breakdown")
    if isinstance(breakdown, list) and breakdown:
        _section("二、项目组成及占地情况")
        for rec in breakdown:
            comp = rec.get("type", "—")
            area = rec.get("area", {})
            area_str = f"{area.get('value', '—')} {area.get('unit', '')}".strip() if isinstance(area, dict) else str(area)
            nature = rec.get("nature", "")
            _add(comp, f"{area_str}（{nature}）" if nature else area_str)

    # ── 三、土石方平衡 ──
    _section("三、土石方平衡")
    _add("挖方量", _fmt_q(facts, "field.fact.earthwork.excavation"))
    _add("填方量", _fmt_q(facts, "field.fact.earthwork.fill"))
    _add("借方量", _fmt_q(facts, "field.fact.earthwork.borrow"))
    _add("弃方量", _fmt_q(facts, "field.fact.earthwork.spoil"))

    # ── 四、水土保持相关 ──
    _section("四、水土保持相关")
    _add("侵蚀类型", _fmt_q(facts, "field.fact.natural.soil_erosion_type"))
    _add("侵蚀强度", _fmt_q(facts, "field.fact.natural.soil_erosion_intensity"))
    _add("原地貌侵蚀模数", _fmt_q(facts, "field.fact.natural.original_erosion_modulus"))
    _add("容许土壤流失量", _fmt_q(facts, "field.fact.natural.allowable_loss"))
    _add("水土保持区划", _fmt_q(facts, "field.fact.natural.water_soil_zoning"))
    level = _fmt_q(facts, "field.fact.prevention.control_standard_level")
    if level != "—":
        _add("防治标准等级", level)
    _add("可剥离表土量", _fmt_q(facts, "field.fact.topsoil.stripable_volume"))

    # 水保投资 (derived)
    comp_fee = derived.get("field.derived.investment.compensation_fee_amount")
    if comp_fee is not None:
        _add("水土保持补偿费", f"{comp_fee} 万元")

    return TableData(
        spec=SPEC_SPEC_SHEET,
        rows=rows,
        total_row=None,
        render_policy=TableRenderPolicy.RENDER_WITH_VALUES,
    )


# ============================================================
# Step 31A-1: 防治目标表 (Prevention Target Table)
# ============================================================
# 对齐样稿: 01:T8-1 / 02:1.5-1
# 列: 防治指标 / 等级标准值 / 加权目标值 / 说明
# 数据来源: cal.target.weighted_comprehensive 已算出六率目标

SPEC_PREVENTION_TARGET = TableSpec(
    table_id="art.table.prevention_target",
    title="水土流失防治目标表",
    columns=[
        TableColumn(key="indicator", header="防治指标", unit="", align="left", fmt="str"),
        TableColumn(key="unit", header="单位", unit="", align="center", fmt="str"),
        TableColumn(key="target_value", header="目标值", unit="", align="right", fmt="str"),
        TableColumn(key="basis", header="取值依据", unit="", align="left", fmt="str"),
    ],
    has_total_row=False,
    footnote="目标值来源: cal.target.weighted_comprehensive / GB/T 50434-2018",
    section_id="sec.soil_loss_prevention.targets",
)

_TARGET_INDICATOR_LABELS = [
    ("control_degree", "水土流失治理度", "%"),
    ("soil_loss_control_ratio", "土壤流失控制比", "—"),
    ("spoil_protection_rate", "渣土防护率", "%"),
    ("topsoil_protection_rate", "表土保护率", "%"),
    ("vegetation_restoration_rate", "林草植被恢复率", "%"),
    ("vegetation_coverage_rate", "林草覆盖率", "%"),
]

# GB/T 50434-2018 南方红壤区 (same as CalculatorRegistry_v0.yaml reference_data)
# Used as fallback when weighted calculator didn't run (single-level without breakdown)
_GBT50434_SOUTH_RED = {
    "一级": {"control_degree": 98, "soil_loss_control_ratio": 0.9, "spoil_protection_rate": 97,
             "topsoil_protection_rate": 92, "vegetation_restoration_rate": 98, "vegetation_coverage_rate": 25},
    "二级": {"control_degree": 95, "soil_loss_control_ratio": 0.85, "spoil_protection_rate": 95,
             "topsoil_protection_rate": 87, "vegetation_restoration_rate": 97, "vegetation_coverage_rate": 22},
    "三级": {"control_degree": 90, "soil_loss_control_ratio": 0.8, "spoil_protection_rate": 92,
             "topsoil_protection_rate": 82, "vegetation_restoration_rate": 95, "vegetation_coverage_rate": 19},
}


def project_prevention_target(snapshot: dict) -> TableData:
    derived = snapshot.get("derived_fields") or {}
    facts = snapshot.get("_original_facts") or {}

    wt = derived.get("field.derived.target.weighted_comprehensive_target") or {}
    level = facts.get("field.fact.prevention.control_standard_level")
    zoning = facts.get("field.fact.natural.water_soil_zoning") or "—"

    # Fallback: single-level direct lookup when weighted calc didn't run
    if not wt and level and level in _GBT50434_SOUTH_RED:
        wt = _GBT50434_SOUTH_RED[level]

    # Determine basis text
    breakdown = facts.get("field.fact.prevention.control_standard_level_breakdown")
    if isinstance(breakdown, list) and len(breakdown) > 1:
        basis = f"GB/T 50434-2018 {zoning} 面积加权"
    elif level:
        basis = f"GB/T 50434-2018 {zoning} {level}"
    else:
        basis = "GB/T 50434-2018"

    rows = []
    for key, label, unit in _TARGET_INDICATOR_LABELS:
        val = wt.get(key) if isinstance(wt, dict) else None
        if val is not None:
            val_str = str(val)
        else:
            val_str = "—"
        rows.append({
            "indicator": label,
            "unit": unit,
            "target_value": val_str,
            "basis": basis,
        })

    policy = TableRenderPolicy.RENDER_WITH_VALUES if any(
        r["target_value"] != "—" for r in rows
    ) else TableRenderPolicy.RENDER_WITH_PLACEHOLDER

    return TableData(spec=SPEC_PREVENTION_TARGET, rows=rows, render_policy=policy)


# ============================================================
# Step 31A-2: 监测点位布设表 (Monitoring Point Layout Table)
# ============================================================
# 对齐样稿: 01:T9-1 / 02:6.4-1
# 列: 序号 / 防治分区 / 监测内容 / 监测方法 / 频次(施工期) / 频次(恢复期)
# 数据来源: county_breakdown zones + _MONITORING_MATRIX (sec_8_2 同源)

SPEC_MONITORING_POINTS = TableSpec(
    table_id="art.table.monitoring_points",
    title="水土保持监测点位布设表",
    columns=[
        TableColumn(key="seq", header="序号", unit="", align="center", fmt="str"),
        TableColumn(key="zone", header="防治分区", unit="", align="left", fmt="str"),
        TableColumn(key="content", header="监测内容", unit="", align="left", fmt="str"),
        TableColumn(key="method", header="监测方法", unit="", align="left", fmt="str"),
        TableColumn(key="freq_construction", header="施工期频次", unit="", align="center", fmt="str"),
        TableColumn(key="freq_recovery", header="恢复期频次", unit="", align="center", fmt="str"),
    ],
    has_total_row=False,
    footnote="数据来源: field.fact.land.county_breakdown + 标准监测矩阵",
    section_id="sec.monitoring.point_layout",
)

# Monitoring matrix (same source as sec_8_2_monitoring_content.py)
_MONITORING_MATRIX_TABLE: list[tuple[str, str, str, str, str]] = [
    ("主体", "扰动面积、地表径流、水土流失状况", "现场量测、定点照相", "月1次", "季1次"),
    ("建筑", "扰动面积、地表径流、水土流失状况", "现场量测、定点照相", "月1次", "季1次"),
    ("道路", "边坡稳定、排水设施完好性", "现场巡查、定点照相", "月1次", "季1次"),
    ("广场", "地表径流、硬化完好性", "现场巡查", "月1次", "—"),
    ("绿化", "植被恢复、覆盖度", "样方调查、定点照相", "—", "季1次"),
    ("景观", "植被恢复、覆盖度", "样方调查、定点照相", "—", "季1次"),
    ("临时堆土", "堆体稳定、拦挡完好性、苫盖情况", "现场巡查", "月2次", "—"),
    ("施工生产", "场地排水、临时覆盖", "现场巡查", "月1次", "—"),
    ("弃渣", "堆渣稳定性、拦挡完好性", "现场量测、位移观测", "月2次", "季1次"),
]

_DEFAULT_MONITORING_TABLE = ("扰动面积、水土流失状况", "现场量测、定点照相", "月1次", "季1次")


def _match_zone_table(zone_type: str) -> tuple[str, str, str, str]:
    for keyword, content, method, freq_c, freq_r in _MONITORING_MATRIX_TABLE:
        if keyword in zone_type:
            return content, method, freq_c, freq_r
    return _DEFAULT_MONITORING_TABLE


def project_monitoring_points(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    breakdown = facts.get("field.fact.land.county_breakdown") or []

    rows = []
    if isinstance(breakdown, list) and breakdown:
        for i, zone in enumerate(breakdown):
            zone_type = zone.get("type", f"分区{i+1}")
            content, method, freq_c, freq_r = _match_zone_table(zone_type)
            rows.append({
                "seq": str(i + 1),
                "zone": zone_type,
                "content": content,
                "method": method,
                "freq_construction": freq_c,
                "freq_recovery": freq_r,
            })
    else:
        rows.append({
            "seq": "1",
            "zone": "项目区",
            "content": "扰动面积、水土流失状况",
            "method": "现场量测、定点照相",
            "freq_construction": "月1次",
            "freq_recovery": "季1次",
        })

    policy = TableRenderPolicy.RENDER_WITH_VALUES
    return TableData(spec=SPEC_MONITORING_POINTS, rows=rows, render_policy=policy)


# ============================================================
# Step 31A-3: 补偿费明细表 (Compensation Fee Detail Table)
# ============================================================
# 对齐样稿: 01:T10-2 / 02:7.1-1
# 列: 占地类型 / 面积(hm²) / 面积(m²) / 费率(元/m²) / 金额(元) / 金额(万元)
# 数据来源: cal.compensation.fee 的 intermediate 已有全部中间值

SPEC_COMPENSATION_DETAIL = TableSpec(
    table_id="art.table.compensation_fee_detail",
    title="水土保持补偿费计费表",
    columns=[
        TableColumn(key="item", header="计费项目", unit="", align="left", fmt="str"),
        TableColumn(key="area_hm2", header="面积", unit="hm²", align="right", fmt="4f"),
        TableColumn(key="area_m2", header="面积", unit="m²", align="right", fmt="0f"),
        TableColumn(key="rate", header="费率", unit="元/m²", align="right", fmt="2f"),
        TableColumn(key="amount_yuan", header="金额", unit="元", align="right", fmt="2f"),
        TableColumn(key="amount_wan", header="金额", unit="万元", align="right", fmt="4f"),
    ],
    has_total_row=True,
    footnote="计算依据: 粤发改价格〔2021〕231号 / cal.compensation.fee",
    section_id="sec.investment_estimation.compensation_fee",
)


def project_compensation_fee_detail(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    derived = snapshot.get("derived_fields") or {}

    # Reconstruct from facts (same inputs as cal.compensation.fee)
    permanent_hm2 = _get(facts, "field.fact.land.permanent_area") or 0
    temporary_hm2 = _get(facts, "field.fact.land.temporary_area") or 0
    rate_fact = facts.get("field.fact.regulatory.compensation_fee_rate")
    rate = _get(facts, "field.fact.regulatory.compensation_fee_rate") or 0
    total_amount_wan = derived.get("field.derived.investment.compensation_fee_amount") or 0
    total_amount_yuan = total_amount_wan * 10000

    rows = []

    # Row 1: permanent land
    perm_m2 = permanent_hm2 * 10000
    perm_yuan = perm_m2 * rate
    perm_wan = round(perm_yuan / 10000, 4)
    rows.append({
        "item": "永久占地",
        "area_hm2": permanent_hm2,
        "area_m2": perm_m2,
        "rate": rate,
        "amount_yuan": perm_yuan,
        "amount_wan": perm_wan,
    })

    # Row 2: temporary land (only if > 0)
    if temporary_hm2 > 0:
        temp_m2 = temporary_hm2 * 10000
        temp_yuan = temp_m2 * rate
        temp_wan = round(temp_yuan / 10000, 4)
        rows.append({
            "item": "临时占地",
            "area_hm2": temporary_hm2,
            "area_m2": temp_m2,
            "rate": rate,
            "amount_yuan": temp_yuan,
            "amount_wan": temp_wan,
        })

    # Total row
    total_hm2 = permanent_hm2 + temporary_hm2
    total_m2 = total_hm2 * 10000
    total_row = {
        "item": "合计",
        "area_hm2": total_hm2,
        "area_m2": total_m2,
        "rate": rate,
        "amount_yuan": total_amount_yuan,
        "amount_wan": total_amount_wan,
    }

    policy = TableRenderPolicy.RENDER_WITH_VALUES if rate > 0 else TableRenderPolicy.RENDER_WITH_PLACEHOLDER

    return TableData(
        spec=SPEC_COMPENSATION_DETAIL,
        rows=rows,
        total_row=total_row,
        render_policy=policy,
    )


# ============================================================
# Step 31B: Prediction Tables (4 tables)
# ============================================================

# ---- 31B-1: 预测范围及时段表 ----
SPEC_PREDICTION_SCOPE = TableSpec(
    table_id="art.table.prediction.scope_period",
    title="水土流失预测范围及预测时段表",
    columns=[
        TableColumn(key="zone_type", header="预测单元", unit="", align="left", fmt="str"),
        TableColumn(key="area_hm2", header="面积", unit="hm²", align="right", fmt="2f"),
        TableColumn(key="construction_months", header="施工期", unit="月", align="right", fmt="str"),
        TableColumn(key="recovery_months", header="自然恢复期", unit="月", align="right", fmt="str"),
    ],
    has_total_row=True,
    footnote="数据来源: derive_prediction_units + derive_phases",
    section_id="sec.soil_loss_analysis.prediction_result",
)


def project_prediction_scope(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    from cpswc.prediction_engine import compute_prediction
    result = compute_prediction(facts)

    # Deduplicate zones (each zone has 2 rows: construction + recovery)
    zone_map: dict[str, dict] = {}
    for r in result.zone_results:
        key = r.zone_id
        if key not in zone_map:
            zone_map[key] = {
                "zone_type": r.zone_type,
                "area_hm2": r.area_hm2,
                "construction_months": "",
                "recovery_months": "",
            }
        if r.period == "施工期":
            zone_map[key]["construction_months"] = str(r.months)
        elif r.period == "自然恢复期":
            zone_map[key]["recovery_months"] = str(r.months)

    rows = list(zone_map.values())

    total_area = sum(r["area_hm2"] for r in rows)
    # All zones share same phase durations
    c_months = rows[0]["construction_months"] if rows else ""
    r_months = rows[0]["recovery_months"] if rows else ""
    total_row = {
        "zone_type": "合计",
        "area_hm2": total_area,
        "construction_months": c_months,
        "recovery_months": r_months,
    }

    return TableData(
        spec=SPEC_PREDICTION_SCOPE,
        rows=rows,
        total_row=total_row,
        render_policy=TableRenderPolicy.RENDER_WITH_VALUES,
    )


# ---- 31B-2: 侵蚀模数取值表 ----
SPEC_EROSION_MODULUS = TableSpec(
    table_id="art.table.prediction.erosion_modulus",
    title="土壤侵蚀模数取值表",
    columns=[
        TableColumn(key="zone_type", header="预测单元", unit="", align="left", fmt="str"),
        TableColumn(key="background", header="背景侵蚀模数", unit="t/(km²·a)", align="right", fmt="0f"),
        TableColumn(key="construction", header="施工期扰动模数", unit="t/(km²·a)", align="right", fmt="0f"),
        TableColumn(key="recovery", header="恢复期扰动模数", unit="t/(km²·a)", align="right", fmt="0f"),
        TableColumn(key="source", header="取值来源", unit="", align="left", fmt="str"),
    ],
    has_total_row=False,
    footnote="背景模数: field.fact.natural.original_erosion_modulus | 扰动模数: 标准矩阵或项目覆盖",
    section_id="sec.soil_loss_analysis.prediction_result",
)


def project_erosion_modulus(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    from cpswc.prediction_engine import (
        derive_prediction_units, resolve_disturbed_modulus, _get_val,
    )

    units = derive_prediction_units(facts)
    bg = _get_val(facts, "field.fact.natural.original_erosion_modulus")

    rows = []
    for unit in units:
        mod = resolve_disturbed_modulus(unit.zone_type, unit.zone_id, facts)
        rows.append({
            "zone_type": unit.zone_type,
            "background": bg,
            "construction": mod.construction,
            "recovery": mod.recovery,
            "source": mod.source_note,
        })

    return TableData(
        spec=SPEC_EROSION_MODULUS,
        rows=rows,
        render_policy=TableRenderPolicy.RENDER_WITH_VALUES,
    )


# ---- 31B-3: 预测成果表 ----
SPEC_PREDICTION_RESULT = TableSpec(
    table_id="art.table.prediction.result",
    title="水土流失预测成果表",
    columns=[
        TableColumn(key="zone_type", header="预测单元", unit="", align="left", fmt="str"),
        TableColumn(key="period", header="预测时段", unit="", align="center", fmt="str"),
        TableColumn(key="area_hm2", header="面积", unit="hm²", align="right", fmt="2f"),
        TableColumn(key="months", header="时段", unit="月", align="right", fmt="str"),
        TableColumn(key="disturbed_modulus", header="扰动模数", unit="t/(km²·a)", align="right", fmt="0f"),
        TableColumn(key="background_modulus", header="背景模数", unit="t/(km²·a)", align="right", fmt="0f"),
        TableColumn(key="disturbed_loss_t", header="流失量", unit="t", align="right", fmt="2f"),
        TableColumn(key="new_loss_t", header="新增流失量", unit="t", align="right", fmt="2f"),
    ],
    has_total_row=True,
    footnote="公式: loss = area_hm2/100 × modulus × months/12 | 新增 = 扰动流失 - 背景流失",
    section_id="sec.soil_loss_analysis.prediction_result",
)


def project_prediction_result(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    from cpswc.prediction_engine import compute_prediction
    result = compute_prediction(facts)

    rows = []
    for r in result.zone_results:
        rows.append({
            "zone_type": r.zone_type,
            "period": r.period,
            "area_hm2": r.area_hm2,
            "months": str(r.months),
            "disturbed_modulus": r.disturbed_modulus,
            "background_modulus": r.background_modulus,
            "disturbed_loss_t": r.disturbed_loss_t,
            "new_loss_t": r.new_loss_t,
        })

    total_row = {
        "zone_type": "合计",
        "period": "",
        "area_hm2": result.total_area_hm2,
        "months": "",
        "disturbed_modulus": None,
        "background_modulus": None,
        "disturbed_loss_t": result.total_loss_t,
        "new_loss_t": result.total_new_loss_t,
    }

    return TableData(
        spec=SPEC_PREDICTION_RESULT,
        rows=rows,
        total_row=total_row,
        render_policy=TableRenderPolicy.RENDER_WITH_VALUES,
    )


# ---- 31B-4: 预测汇总表 ----
SPEC_PREDICTION_SUMMARY = TableSpec(
    table_id="art.table.prediction.summary",
    title="水土流失预测汇总表",
    columns=[
        TableColumn(key="period", header="预测时段", unit="", align="left", fmt="str"),
        TableColumn(key="area_hm2", header="扰动面积", unit="hm²", align="right", fmt="2f"),
        TableColumn(key="disturbed_loss_t", header="流失总量", unit="t", align="right", fmt="2f"),
        TableColumn(key="background_loss_t", header="背景流失量", unit="t", align="right", fmt="2f"),
        TableColumn(key="new_loss_t", header="新增流失量", unit="t", align="right", fmt="2f"),
    ],
    has_total_row=True,
    footnote="汇总自预测成果表",
    section_id="sec.soil_loss_analysis.prediction_result",
)


def project_prediction_summary(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    from cpswc.prediction_engine import compute_prediction
    result = compute_prediction(facts)

    rows = []
    for period in ("施工期", "自然恢复期"):
        s = result.summary_by_period.get(period)
        if s:
            rows.append({
                "period": period,
                "area_hm2": round(s["area_hm2"], 2),
                "disturbed_loss_t": round(s["disturbed_loss_t"], 2),
                "background_loss_t": round(s["background_loss_t"], 2),
                "new_loss_t": round(s["new_loss_t"], 2),
            })

    total_row = {
        "period": "合计",
        "area_hm2": result.total_area_hm2,
        "disturbed_loss_t": result.total_loss_t,
        "background_loss_t": result.total_background_loss_t,
        "new_loss_t": result.total_new_loss_t,
    }

    return TableData(
        spec=SPEC_PREDICTION_SUMMARY,
        rows=rows,
        total_row=total_row,
        render_policy=TableRenderPolicy.RENDER_WITH_VALUES,
    )


# ============================================================
# Registry
# ============================================================

# ============================================================
# Step 32+: 六率分项达标表 (Six-Indicator Zone Breakdown Table)
# ============================================================
# 按防治分区展开六率目标值, 多等级项目含面积权重和加权合计行。
# 数据来源: control_standard_level_breakdown (facts) +
#           weighted_comprehensive_target (derived) +
#           GB/T 50434-2018 目标查表

SPEC_SIX_INDICATOR_BREAKDOWN = TableSpec(
    table_id="art.table.six_indicator_breakdown",
    title="水土流失防治目标分区取值表",
    columns=[
        TableColumn(key="zone", header="防治分区", unit="", align="left", fmt="str"),
        TableColumn(key="level", header="防治标准等级", unit="", align="center", fmt="str"),
        TableColumn(key="area", header="面积", unit="hm²", align="right", fmt=".2f"),
        TableColumn(key="weight", header="权重", unit="%", align="right", fmt="str"),
        TableColumn(key="control_degree", header="治理度", unit="%", align="right", fmt="str"),
        TableColumn(key="soil_loss_control_ratio", header="流失控制比", unit="", align="right", fmt="str"),
        TableColumn(key="spoil_protection_rate", header="渣土防护率", unit="%", align="right", fmt="str"),
        TableColumn(key="topsoil_protection_rate", header="表土保护率", unit="%", align="right", fmt="str"),
        TableColumn(key="vegetation_restoration_rate", header="植被恢复率", unit="%", align="right", fmt="str"),
        TableColumn(key="vegetation_coverage_rate", header="覆盖率", unit="%", align="right", fmt="str"),
    ],
    has_total_row=False,
    footnote="目标值来源: GB/T 50434-2018 表 4.0.2-5 | 加权方法: 面积加权 (cal.target.weighted_comprehensive)",
    section_id="sec.soil_loss_prevention.targets",
)


def project_six_indicator_breakdown(snapshot: dict) -> TableData:
    """按防治分区展开六率目标, 单等级→1 行, 多等级→分区行 + 加权合计行"""
    facts = snapshot.get("_original_facts") or {}
    derived = snapshot.get("derived_fields") or {}

    breakdown = facts.get("field.fact.prevention.control_standard_level_breakdown")
    level_single = facts.get("field.fact.prevention.control_standard_level")
    wt = derived.get("field.derived.target.weighted_comprehensive_target") or {}

    ind_keys = [
        "control_degree", "soil_loss_control_ratio", "spoil_protection_rate",
        "topsoil_protection_rate", "vegetation_restoration_rate", "vegetation_coverage_rate",
    ]

    def _fmt(val):
        return str(val) if val is not None else "—"

    rows = []

    if isinstance(breakdown, list) and len(breakdown) > 0:
        total_area = sum(
            (z.get("area", {}).get("value", 0) if isinstance(z.get("area"), dict)
             else z.get("area", 0))
            for z in breakdown
        )

        for zone in breakdown:
            name = zone.get("zone_name") or zone.get("zone_id", "—")
            level = zone.get("standard_level", "—")
            area_raw = zone.get("area")
            area = area_raw.get("value", 0) if isinstance(area_raw, dict) else (area_raw or 0)
            w = (area / total_area * 100) if total_area > 0 else 0

            # Look up standard targets for this level
            level_targets = _GBT50434_SOUTH_RED.get(level, {})

            row = {
                "zone": name,
                "level": level,
                "area": area,
                "weight": f"{w:.1f}",
            }
            for k in ind_keys:
                row[k] = _fmt(level_targets.get(k))
            rows.append(row)

        # Weighted total row (only for multi-zone)
        if len(breakdown) > 1 and wt:
            total_row = {
                "zone": "加权目标值",
                "level": "—",
                "area": total_area,
                "weight": "100.0",
            }
            for k in ind_keys:
                total_row[k] = _fmt(wt.get(k))
            rows.append(total_row)

    elif level_single and level_single in _GBT50434_SOUTH_RED:
        # Single level fallback: no breakdown list, just one row
        if not wt:
            wt = _GBT50434_SOUTH_RED[level_single]
        resp_area = facts.get("field.fact.prevention.responsibility_range_area")
        area = (resp_area.get("value", 0) if isinstance(resp_area, dict)
                else (resp_area or 0))
        row = {
            "zone": "全项目",
            "level": level_single,
            "area": area,
            "weight": "100.0",
        }
        for k in ind_keys:
            row[k] = _fmt(wt.get(k))
        rows.append(row)

    policy = (TableRenderPolicy.RENDER_WITH_VALUES if rows
              else TableRenderPolicy.RENDER_WITH_PLACEHOLDER)

    return TableData(
        spec=SPEC_SIX_INDICATOR_BREAKDOWN, rows=rows, render_policy=policy)


# ============================================================
# Step 34: 措施工程量汇总表 (Measures Engineering Quantity Table)
# ============================================================
# 按防治分区和措施类别展开, 从 measures_registry 过滤。
# 分"方案新增"和"主体已列"两张表, 共享同一 section_id。

SPEC_MEASURES_NEW = TableSpec(
    table_id="art.table.measures_quantity_new",
    title="新增水土保持措施工程量及投资汇总表",
    columns=[
        TableColumn(key="category", header="措施类别", unit="", align="left", fmt="str"),
        TableColumn(key="zone", header="防治分区", unit="", align="left", fmt="str"),
        TableColumn(key="measure", header="措施名称", unit="", align="left", fmt="str"),
        TableColumn(key="unit", header="单位", unit="", align="center", fmt="str"),
        TableColumn(key="quantity", header="工程量", unit="", align="right", fmt="str"),
        TableColumn(key="amount", header="投资", unit="万元", align="right", fmt="str"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.investment.measures_registry (source_attribution=方案新增)",
    section_id="sec.soil_loss_prevention.construction_schedule",
)

SPEC_MEASURES_EXISTING = TableSpec(
    table_id="art.table.measures_quantity_existing",
    title="主体工程已列水土保持措施工程量及投资汇总表",
    columns=[
        TableColumn(key="category", header="措施类别", unit="", align="left", fmt="str"),
        TableColumn(key="zone", header="防治分区", unit="", align="left", fmt="str"),
        TableColumn(key="measure", header="措施名称", unit="", align="left", fmt="str"),
        TableColumn(key="unit", header="单位", unit="", align="center", fmt="str"),
        TableColumn(key="quantity", header="工程量", unit="", align="right", fmt="str"),
        TableColumn(key="amount", header="投资", unit="万元", align="right", fmt="str"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.investment.measures_registry (source_attribution=主体已列)",
    section_id="sec.soil_loss_prevention.construction_schedule",
)

# Fee category ordering
_CATEGORY_ORDER = ["工程措施", "植物措施", "临时措施", "监测措施"]


def _build_measures_table(snapshot: dict, spec: TableSpec,
                          attribution_filter: str) -> TableData:
    """Build measures quantity table filtered by source_attribution."""
    facts = snapshot.get("_original_facts") or {}
    registry = facts.get("field.fact.investment.measures_registry") or []

    filtered = [m for m in registry
                if m.get("source_attribution") == attribution_filter]

    if not filtered:
        return TableData(spec=spec, rows=[],
                         render_policy=TableRenderPolicy.RENDER_WITH_PLACEHOLDER)

    # Sort: by category order, then zone, then measure name
    def sort_key(m):
        cat = m.get("fee_category", "")
        idx = _CATEGORY_ORDER.index(cat) if cat in _CATEGORY_ORDER else 99
        return (idx, m.get("prevention_zone", ""), m.get("measure_name", ""))

    filtered.sort(key=sort_key)

    rows = []
    total_amount = 0.0
    prev_cat = None
    for m in filtered:
        cat = m.get("fee_category", "—")
        amt = m.get("amount_wan", 0) or 0
        total_amount += amt

        rows.append({
            "category": cat if cat != prev_cat else "",  # merge same category
            "zone": m.get("prevention_zone", "—"),
            "measure": m.get("measure_name", "—"),
            "unit": m.get("unit", "—"),
            "quantity": str(m.get("quantity", "—")),
            "amount": f"{amt:.2f}" if amt else "—",
        })
        prev_cat = cat

    # Total row
    rows.append({
        "category": "合  计",
        "zone": "",
        "measure": "",
        "unit": "",
        "quantity": "",
        "amount": f"{total_amount:.2f}",
    })

    return TableData(spec=spec, rows=rows,
                     render_policy=TableRenderPolicy.RENDER_WITH_VALUES)


def project_measures_quantity_new(snapshot: dict) -> TableData:
    return _build_measures_table(snapshot, SPEC_MEASURES_NEW, "方案新增")


def project_measures_quantity_existing(snapshot: dict) -> TableData:
    return _build_measures_table(snapshot, SPEC_MEASURES_EXISTING, "主体已列")


# ============================================================
# Step 35: 新增水土保持措施分年度投资估算表
# ============================================================
# Contract (A-only):
#   - 只覆盖方案新增, 不含主体已列
#   - 唯一正式来源: investment.annual_allocation
#   - 没有 annual_allocation → placeholder, 不做均匀分摊猜测
#   - 年列由 annual_allocation 的 key 决定, 最后一列固定"合计"
#   - 事实不足时宁可留白, 不把猜测伪装成正式结论

# 固定 8 行 (费用类别)
_ANNUAL_ROWS = [
    ("一", "工程措施"),
    ("二", "植物措施"),
    ("三", "监测措施"),
    ("四", "临时措施"),
    ("五", "独立费用"),
    ("六", "预备费"),
    ("七", "补偿费"),
    ("八", "新增总投资"),
]


def project_annual_investment(snapshot: dict) -> TableData:
    """分年度投资估算表: A-only, 无 annual_allocation 即 placeholder"""
    facts = snapshot.get("_original_facts") or {}

    alloc = facts.get("field.fact.investment.annual_allocation")

    if not alloc or not isinstance(alloc, dict):
        # 无显式年度分配 → placeholder
        # 尝试从 schedule 推算年列用于 spec 展示
        start_str = facts.get("field.fact.schedule.start_time") or ""
        end_str = facts.get("field.fact.schedule.end_time") or ""
        try:
            start_year = int(start_str[:4])
            end_year = int(end_str[:4])
            if end_year < start_year:
                end_year = start_year
            years = list(range(start_year, end_year + 1))
        except (ValueError, IndexError):
            years = []
        spec = _make_annual_spec(years)
        return TableData(spec=spec, rows=[],
                         render_policy=TableRenderPolicy.RENDER_WITH_PLACEHOLDER)

    # Strategy A: read from explicit annual_allocation
    # Year list from allocation keys, sorted
    years = sorted(int(k) for k in alloc.keys() if str(k).isdigit())
    if not years:
        spec = _make_annual_spec([])
        return TableData(spec=spec, rows=[],
                         render_policy=TableRenderPolicy.RENDER_WITH_PLACEHOLDER)

    # Build rows
    rows = []
    for seq, label in _ANNUAL_ROWS:
        row = {"seq": seq, "name": label}
        row_total = 0.0

        for y in years:
            y_alloc = alloc.get(str(y)) or alloc.get(y) or {}
            if label == "新增总投资":
                # Sum all categories for this year
                amt = sum(
                    float((alloc.get(str(y)) or alloc.get(y) or {}).get(cat, 0))
                    for _, cat in _ANNUAL_ROWS if cat != "新增总投资"
                )
            else:
                amt = float(y_alloc.get(label, 0))
            row[f"y_{y}"] = f"{amt:.2f}" if amt else "—"
            row_total += amt

        row["total"] = f"{row_total:.2f}" if row_total else "—"
        rows.append(row)

    spec = _make_annual_spec(years)
    return TableData(spec=spec, rows=rows,
                     render_policy=TableRenderPolicy.RENDER_WITH_VALUES)


def _make_annual_spec(years: list[int]) -> TableSpec:
    """Dynamically build TableSpec with year columns."""
    cols = [
        TableColumn(key="seq", header="序号", unit="", align="center", fmt="str"),
        TableColumn(key="name", header="工程或费用名称", unit="", align="left", fmt="str"),
    ]
    for y in years:
        cols.append(TableColumn(
            key=f"y_{y}", header=f"{y} 年", unit="万元", align="right", fmt="str"))
    cols.append(TableColumn(
        key="total", header="合计", unit="万元", align="right", fmt="str"))

    return TableSpec(
        table_id="art.table.investment.annual_breakdown",
        title="新增水土保持措施分年度投资估算表",
        columns=cols,
        has_total_row=False,
        footnote="数据来源: field.fact.investment.annual_allocation (显式分配) | 仅含方案新增部分",
        section_id="sec.investment.summary",
    )


TABLE_PROJECTIONS = {
    "art.table.total_land_occupation": project_total_land_occupation,
    "art.table.earthwork_balance": project_earthwork_balance,
    "art.table.land_occupation_by_county": project_land_occupation_by_county,
    "art.table.topsoil_balance": project_topsoil_balance,
    "art.table.responsibility_range_by_admin_division": project_responsibility_range,
    "art.table.spoil_summary": project_spoil_summary,
    "art.table.six_indicator_review": project_six_indicator_review,
    "art.table.investment.total_summary": project_investment_total_summary,  # Step 16
    "art.table.investment.split_summary": project_investment_split_summary,  # Step 16
    "art.table.investment.appendix_total": project_appendix_total,  # Step 17
    "art.table.investment.appendix_existing": project_appendix_existing,  # Step 17
    "art.table.investment.appendix_fees": project_appendix_fees,  # Step 17
    "art.table.spec_sheet": project_spec_sheet,  # Step 24
    "art.table.prevention_target": project_prevention_target,  # Step 31A
    "art.table.monitoring_points": project_monitoring_points,  # Step 31A
    "art.table.compensation_fee_detail": project_compensation_fee_detail,  # Step 31A
    "art.table.prediction.scope_period": project_prediction_scope,  # Step 31B
    "art.table.prediction.erosion_modulus": project_erosion_modulus,  # Step 31B
    "art.table.prediction.result": project_prediction_result,  # Step 31B
    "art.table.prediction.summary": project_prediction_summary,  # Step 31B
    "art.table.six_indicator_breakdown": project_six_indicator_breakdown,  # Step 32+
    "art.table.measures_quantity_new": project_measures_quantity_new,  # Step 34
    "art.table.measures_quantity_existing": project_measures_quantity_existing,  # Step 34
    "art.table.investment.annual_breakdown": project_annual_investment,  # Step 35
}
