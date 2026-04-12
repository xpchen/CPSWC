"""
table_projections.py — CPSWC P0 CAN_GENERATE 表格数据投影函数

每张表一个 project_*() 函数:
    输入: snapshot dict (含 _original_facts)
    输出: TableData

投影纪律:
  - 只从 snapshot._original_facts / derived_fields / triggered_obligations 取数
  - 不创造新信息, 不做规则判断
  - 缺值时标 None (由 render_data_table 显示为 "—")
"""
from __future__ import annotations
from typing import Any

from cpswc.renderers.table_protocol import TableColumn, TableSpec, TableData, TableRenderPolicy


# ============================================================
# Helper
# ============================================================

def _get(facts: dict, key: str) -> Any:
    """从 facts 取值, 处理 Quantity {value, unit}"""
    v = facts.get(key)
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


# ============================================================
# 1. art.table.total_land_occupation — 工程总占地表
# ============================================================

SPEC_TOTAL_LAND = TableSpec(
    table_id="art.table.total_land_occupation",
    title="工程总占地表",
    columns=[
        TableColumn(key="item", header="项目", unit="", align="left", fmt="str"),
        TableColumn(key="permanent", header="永久占地", unit="hm\u00b2", align="right", fmt="2f"),
        TableColumn(key="temporary", header="临时占地", unit="hm\u00b2", align="right", fmt="2f"),
        TableColumn(key="total", header="合计", unit="hm\u00b2", align="right", fmt="2f"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.land.permanent_area / temporary_area / total_area",
    section_id="sec.project_overview.land_occupation",
)


def project_total_land_occupation(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    perm = _get(facts, "field.fact.land.permanent_area")
    temp = _get(facts, "field.fact.land.temporary_area")
    total = _get(facts, "field.fact.land.total_area")

    row = {"item": "项目合计", "permanent": perm, "temporary": temp, "total": total}
    total_row = row.copy()  # v0 单行, 合计=数据行

    warnings = []
    if perm is None:
        warnings.append("field.fact.land.permanent_area 缺失")
    if temp is None:
        warnings.append("field.fact.land.temporary_area 缺失")

    policy = TableRenderPolicy.RENDER_WITH_VALUES
    if perm is None and temp is None:
        policy = TableRenderPolicy.RENDER_WITH_PLACEHOLDER
    return TableData(spec=SPEC_TOTAL_LAND, rows=[row], total_row=total_row,
                     render_policy=policy, warnings=warnings)


# ============================================================
# 2. art.table.earthwork_balance — 土石方 (不含表土) 平衡表
# ============================================================

SPEC_EARTHWORK = TableSpec(
    table_id="art.table.earthwork_balance",
    title="土石方 (不含表土) 平衡表",
    columns=[
        TableColumn(key="item", header="项目", unit="", align="left", fmt="str"),
        TableColumn(key="excavation", header="挖方", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="fill", header="填方", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="self_reuse", header="本项目利用", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="borrow", header="借方", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="spoil", header="弃方", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="comprehensive_reuse", header="综合利用", unit="万m\u00b3", align="right", fmt="2f"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.earthwork.*",
    section_id="sec.project_overview.earthwork_balance",
)


def project_earthwork_balance(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    row = {
        "item": "项目合计",
        "excavation": _get(facts, "field.fact.earthwork.excavation"),
        "fill": _get(facts, "field.fact.earthwork.fill"),
        "self_reuse": _get(facts, "field.fact.earthwork.self_reuse"),
        "borrow": _get(facts, "field.fact.earthwork.borrow"),
        "spoil": _get(facts, "field.fact.earthwork.spoil"),
        "comprehensive_reuse": _get(facts, "field.fact.earthwork.comprehensive_reuse"),
    }
    return TableData(spec=SPEC_EARTHWORK, rows=[row], total_row=row.copy(),
                     render_policy=TableRenderPolicy.RENDER_WITH_VALUES)


# ============================================================
# 3. art.table.land_occupation_by_county — 分县占地表
# ============================================================

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
    footnote="数据来源: field.fact.land.county_breakdown",
    section_id="sec.project_overview.land_occupation",
)


def project_land_occupation_by_county(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    breakdown = facts.get("field.fact.land.county_breakdown")
    if not isinstance(breakdown, list):
        return TableData(spec=SPEC_COUNTY_LAND, rows=[], total_row=None,
                         render_policy=TableRenderPolicy.SKIP_RENDER,
                         warnings=["field.fact.land.county_breakdown 缺失或非 list"])

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
# 4. art.table.topsoil_balance — 表土平衡表
# ============================================================

SPEC_TOPSOIL = TableSpec(
    table_id="art.table.topsoil_balance",
    title="表土平衡表",
    columns=[
        TableColumn(key="item", header="项目", unit="", align="left", fmt="str"),
        TableColumn(key="stripable_area", header="可剥离面积", unit="hm\u00b2", align="right", fmt="2f"),
        TableColumn(key="stripable_volume", header="可剥离量", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="reuse_volume", header="回覆量", unit="万m\u00b3", align="right", fmt="2f"),
        TableColumn(key="balance", header="平衡 (剥-覆)", unit="万m\u00b3", align="right", fmt="2f"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.topsoil.* (部分为 placeholder stub, 标 '—' 的待措施布设确认)",
    section_id="sec.topsoil.balance",
)


def project_topsoil_balance(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    s_area = _get(facts, "field.fact.topsoil.stripable_area")
    s_vol = _get(facts, "field.fact.topsoil.stripable_volume")
    # reuse_volume 是 placeholder stub, 可能缺
    r_vol = _get(facts, "field.fact.topsoil.fill")
    balance = None
    if s_vol is not None and r_vol is not None:
        balance = round(float(s_vol) - float(r_vol), 2)

    row = {
        "item": "项目合计",
        "stripable_area": s_area,
        "stripable_volume": s_vol,
        "reuse_volume": r_vol,
        "balance": balance,
    }
    warnings = []
    if r_vol is None:
        warnings.append("field.fact.topsoil.fill (回覆量) 为 placeholder stub, 待措施布设确认")

    policy = TableRenderPolicy.RENDER_WITH_PLACEHOLDER if warnings else TableRenderPolicy.RENDER_WITH_VALUES
    return TableData(spec=SPEC_TOPSOIL, rows=[row], total_row=row.copy(),
                     render_policy=policy, warnings=warnings)


# ============================================================
# 5. art.table.responsibility_range_by_admin_division — 防治责任范围统计表
# ============================================================

SPEC_RESP_RANGE = TableSpec(
    table_id="art.table.responsibility_range_by_admin_division",
    title="防治责任范围统计表",
    columns=[
        TableColumn(key="admin_area", header="行政区", unit="", align="left", fmt="str"),
        TableColumn(key="resp_area", header="责任范围面积", unit="hm\u00b2", align="right", fmt="2f"),
        TableColumn(key="ratio", header="占比", unit="%", align="right", fmt="1f"),
    ],
    has_total_row=True,
    footnote="数据来源: field.fact.land.county_breakdown + field.fact.prevention.responsibility_range_area",
    section_id="sec.soil_loss_prevention.responsibility_range_by_county",
)


def project_responsibility_range(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    breakdown = facts.get("field.fact.land.county_breakdown")
    total_resp = _get(facts, "field.fact.prevention.responsibility_range_area")

    if not isinstance(breakdown, list) or not breakdown:
        return TableData(spec=SPEC_RESP_RANGE, rows=[], total_row=None,
                         render_policy=TableRenderPolicy.SKIP_RENDER,
                         warnings=["county_breakdown 缺失"])

    # v0 近似: 用各县占地面积合计作为分县责任范围
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

    # 计算占比
    for row in rows:
        if row["resp_area"] is not None and grand_total > 0:
            row["ratio"] = round(float(row["resp_area"]) / grand_total * 100, 1)

    total_row = {"admin_area": "合计", "resp_area": grand_total, "ratio": 100.0}

    warnings = []
    if total_resp is not None and abs(float(total_resp) - grand_total) > 0.01:
        warnings.append(f"county_breakdown 合计 ({grand_total}) 与 responsibility_range_area ({total_resp}) 不一致")

    return TableData(spec=SPEC_RESP_RANGE, rows=rows, total_row=total_row,
                     render_policy=TableRenderPolicy.RENDER_WITH_VALUES,
                     warnings=warnings)


# ============================================================
# 6. art.table.spoil_summary — 弃渣场和临时堆土场设置汇总表
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
    has_total_row=False,  # 明细表不做合计
    footnote="弃渣场级别依据 GB 51018-2014 表 5.7.1; 临时堆土场不适用弃渣场分级",
    section_id="sec.disposal_site.site_selection",
)


def project_spoil_summary(snapshot: dict) -> TableData:
    facts = snapshot.get("_original_facts") or {}
    derived = snapshot.get("derived_fields") or {}

    disposal_facts = facts.get("field.fact.disposal_site.level_assessment") or []
    disposal_derived = derived.get("field.derived.disposal_site.level_assessment") or []
    temp_sites = facts.get("field.fact.construction.temp_topsoil_site") or []

    # Build derived level lookup
    level_by_id = {}
    for sd in disposal_derived:
        if isinstance(sd, dict):
            level_by_id[sd.get("site_id")] = sd.get("level", "—")

    rows = []

    # Disposal sites (弃渣场)
    for sf in disposal_facts:
        if not isinstance(sf, dict):
            continue
        sid = sf.get("site_id", "?")
        vol = sf.get("volume")
        if isinstance(vol, dict):
            vol = vol.get("value")
        ht = sf.get("max_height")
        if isinstance(ht, dict):
            ht = ht.get("value")
        rows.append({
            "site_id": sid,
            "name": sf.get("site_name", sid),
            "type": "弃渣场",
            "volume": vol,
            "max_height": ht,
            "level": level_by_id.get(sid, "—"),
        })

    # Temp topsoil sites (临时堆土场)
    for ts in temp_sites:
        if not isinstance(ts, dict):
            continue
        sid = ts.get("name_or_id", ts.get("site_id", "?"))
        vol = ts.get("storage_volume")
        if isinstance(vol, dict):
            vol = vol.get("value")
        rows.append({
            "site_id": sid,
            "name": sid,
            "type": ts.get("type", "临时堆土场"),
            "volume": vol,
            "max_height": None,  # 临时堆土场一般不记录最大高度
            "level": "不适用",   # 不适用弃渣场分级
        })

    policy = TableRenderPolicy.RENDER_WITH_VALUES if rows else TableRenderPolicy.RENDER_NOT_APPLICABLE
    return TableData(spec=SPEC_SPOIL_SUMMARY, rows=rows, render_policy=policy)


# ============================================================
# Registry: table_id → projection function
# ============================================================

TABLE_PROJECTIONS = {
    "art.table.total_land_occupation": project_total_land_occupation,
    "art.table.earthwork_balance": project_earthwork_balance,
    "art.table.land_occupation_by_county": project_land_occupation_by_county,
    "art.table.topsoil_balance": project_topsoil_balance,
    "art.table.responsibility_range_by_admin_division": project_responsibility_range,
    "art.table.spoil_summary": project_spoil_summary,
}
