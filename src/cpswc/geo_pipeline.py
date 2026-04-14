"""
geo_pipeline.py — CPSWC v0 GeoPipeline

宪法必做项 #8: "上传 shp → 面积/拐点/分县/叠加; 自动出 F-01 / F-04 / F-12"

v0 实现 (两层):
  3A — 模块 + 接口契约 + manifest + CRS 检查
  3B — 产出 3 个真实附图文件 (PNG, 非 GIS 精度但可交付)

v0 限制:
  - 不解析真实 shapefile (无 geopandas/fiona 依赖)
  - 从 facts 中的 approximate_center + county_breakdown 投影
  - 图件为示意图级别, 含: 项目红线框 + 分区标注 + 图例 + 比例尺 + 指北针 + CGCS2000 标注

v1 升级路径:
  - 真实 shp 上传 → geopandas 解析
  - 面积/拐点自动计算
  - 分县叠加 (县界 shp 底图)
  - 敏感图层叠加
  - 高精度制图 (投影坐标系, 格网)

产出:
  F-01: 项目地理位置图
  F-04: 水土流失防治责任范围图
  F-12: 取土场和弃渣场位置图
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ============================================================
# 数据类型
# ============================================================

@dataclass
class GeoInput:
    """从 facts 提取的地理输入"""
    project_name: str = ""
    center_lon: float = 0.0
    center_lat: float = 0.0
    crs: str = "CGCS2000"
    epsg: int = 4490
    total_area_hm2: float = 0.0
    permanent_area_hm2: float = 0.0
    temporary_area_hm2: float = 0.0
    county_list: list[str] = field(default_factory=list)
    county_breakdown: list[dict] = field(default_factory=list)
    disposal_sites: list[dict] = field(default_factory=list)
    has_borrow_site: bool = False


@dataclass
class GeoArtifact:
    """单个图件产出"""
    artifact_id: str      # art.figure.F_01_location 等
    file_path: Path
    format: str           # "png" | "pdf"
    title: str
    crs_note: str


@dataclass
class GeoPipelineResult:
    """GeoPipeline 完整产出"""
    artifacts: list[GeoArtifact]
    crs_check_passed: bool
    crs_note: str
    manifest: dict


# ============================================================
# 从 facts 提取 geo 输入
# ============================================================

def _extract_geo_input(facts: dict, project_name: str = "") -> GeoInput:
    """从 facts dict 提取 geo 相关字段"""
    geo_ref = facts.get("field.fact.location.redline_geometry_ref") or {}
    center = {}
    crs = "CGCS2000"
    epsg = 4490

    if isinstance(geo_ref, dict):
        center = geo_ref.get("approximate_center") or {}
        crs = geo_ref.get("crs", "CGCS2000")
        epsg = geo_ref.get("epsg", 4490)

    def _num(key: str) -> float:
        v = facts.get(key)
        if isinstance(v, dict) and "value" in v:
            return float(v["value"])
        if isinstance(v, (int, float)):
            return float(v)
        return 0.0

    county_raw = facts.get("field.fact.location.county_list") or []
    if isinstance(county_raw, str):
        county_raw = [county_raw]

    breakdown = facts.get("field.fact.land.county_breakdown") or []
    disposal = facts.get("field.fact.disposal_site.level_assessment") or []
    borrow_type = facts.get("field.fact.earthwork.borrow_source_type") or ""

    return GeoInput(
        project_name=project_name,
        center_lon=float(center.get("longitude", 0)),
        center_lat=float(center.get("latitude", 0)),
        crs=crs,
        epsg=epsg,
        total_area_hm2=_num("field.fact.land.total_area"),
        permanent_area_hm2=_num("field.fact.land.permanent_area"),
        temporary_area_hm2=_num("field.fact.land.temporary_area"),
        county_list=county_raw,
        county_breakdown=breakdown if isinstance(breakdown, list) else [],
        disposal_sites=disposal if isinstance(disposal, list) else [],
        has_borrow_site=bool(borrow_type and borrow_type != "外购"),
    )


# ============================================================
# CRS 检查
# ============================================================

def check_crs(geo_input: GeoInput) -> tuple[bool, str]:
    """检查坐标参考系是否为 CGCS2000 (EPSG:4490)"""
    if geo_input.crs == "CGCS2000" and geo_input.epsg == 4490:
        return True, "CGCS2000 (EPSG:4490) 合规"
    return False, (
        f"坐标参考系不合规: crs={geo_input.crs}, epsg={geo_input.epsg}. "
        f"要求 CGCS2000 (EPSG:4490)"
    )


# ============================================================
# 图件渲染 (matplotlib)
# ============================================================

def _estimate_bbox(center_lon: float, center_lat: float,
                   area_hm2: float) -> tuple[float, float, float, float]:
    """从中心点和面积估算 bounding box"""
    if area_hm2 <= 0:
        area_hm2 = 1.0
    # 粗估: 正方形边长 (km)
    side_km = math.sqrt(area_hm2 * 0.01)  # hm² → km²
    # 1° lat ≈ 111 km, 1° lon ≈ 111 * cos(lat) km
    d_lat = side_km / 111.0 * 3  # 放大 3 倍留边距
    d_lon = side_km / (111.0 * math.cos(math.radians(center_lat))) * 3

    return (center_lon - d_lon, center_lon + d_lon,
            center_lat - d_lat, center_lat + d_lat)


def _render_figure(
    geo: GeoInput,
    artifact_id: str,
    title: str,
    output_path: Path,
    *,
    show_zones: bool = False,
    show_disposal: bool = False,
) -> None:
    """用 matplotlib 渲染一张附图"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import matplotlib.font_manager as fm
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

    # 中文字体: 按优先级查找可用字体
    _CJK_CANDIDATES = ["Heiti TC", "PingFang SC", "STHeiti",
                        "Arial Unicode MS", "SimHei", "Noto Sans CJK SC"]
    _cjk_font = None
    for name in _CJK_CANDIDATES:
        matches = [f for f in fm.fontManager.ttflist if f.name == name]
        if matches:
            _cjk_font = name
            break
    if _cjk_font:
        matplotlib.rcParams["font.sans-serif"] = [_cjk_font, "DejaVu Sans"]
        matplotlib.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    lon0, lon1, lat0, lat1 = _estimate_bbox(
        geo.center_lon, geo.center_lat, geo.total_area_hm2)

    ax.set_xlim(lon0, lon1)
    ax.set_ylim(lat0, lat1)
    ax.set_aspect("equal")

    # 背景格网
    ax.grid(True, linestyle="--", alpha=0.3, color="#999999")

    # 项目红线 (用中心点 + 面积估算的矩形)
    side_km = math.sqrt(max(geo.total_area_hm2, 0.01) * 0.01)
    d_lat_r = side_km / 111.0 / 2
    d_lon_r = side_km / (111.0 * math.cos(math.radians(geo.center_lat))) / 2
    rect = patches.Rectangle(
        (geo.center_lon - d_lon_r, geo.center_lat - d_lat_r),
        d_lon_r * 2, d_lat_r * 2,
        linewidth=2, edgecolor="#CC0000", facecolor="#FFCCCC",
        alpha=0.3, label="项目红线范围",
    )
    ax.add_patch(rect)

    # 中心点标记
    ax.plot(geo.center_lon, geo.center_lat, "r*", markersize=12)
    ax.annotate(
        geo.project_name[:20] if geo.project_name else "项目中心",
        (geo.center_lon, geo.center_lat),
        textcoords="offset points", xytext=(10, 10),
        fontsize=8, color="#333333",
        fontfamily="sans-serif",
    )

    # 防治分区 (F-04)
    if show_zones and geo.county_breakdown:
        n = len(geo.county_breakdown)
        colors = ["#4472C4", "#ED7D31", "#A5A5A5", "#FFC000", "#5B9BD5"]
        for i, rec in enumerate(geo.county_breakdown):
            zone_name = rec.get("type", f"分区{i+1}")
            area_v = rec.get("area", {})
            area_str = (f"{area_v.get('value', '?')} {area_v.get('unit', '')}"
                        if isinstance(area_v, dict) else str(area_v))
            # 在红线范围内偏移显示
            offset_lat = d_lat_r * 0.6 - i * d_lat_r * 1.2 / max(n, 1)
            ax.annotate(
                f"● {zone_name}\n   {area_str}",
                (geo.center_lon - d_lon_r * 0.8,
                 geo.center_lat + offset_lat),
                fontsize=7, color=colors[i % len(colors)],
                fontfamily="sans-serif",
            )

    # 弃渣场标记 (F-12)
    if show_disposal and geo.disposal_sites:
        for i, site in enumerate(geo.disposal_sites):
            site_name = site.get("site_name") or site.get("site_id", f"D{i+1}")
            # 在红线外偏移
            s_lon = geo.center_lon + d_lon_r * (1.2 + i * 0.3)
            s_lat = geo.center_lat + d_lat_r * (0.5 - i * 0.5)
            ax.plot(s_lon, s_lat, "s", markersize=10, color="#996633")
            ax.annotate(
                f"▲ {site_name}",
                (s_lon, s_lat),
                textcoords="offset points", xytext=(8, 5),
                fontsize=7, color="#663300",
                fontfamily="sans-serif",
            )

    # 借土场标记
    if show_disposal and geo.has_borrow_site:
        b_lon = geo.center_lon - d_lon_r * 1.3
        b_lat = geo.center_lat - d_lat_r * 0.3
        ax.plot(b_lon, b_lat, "^", markersize=10, color="#336699")
        ax.annotate(
            "◆ 取土场",
            (b_lon, b_lat),
            textcoords="offset points", xytext=(8, 5),
            fontsize=7, color="#336699",
            fontfamily="sans-serif",
        )

    # 图例
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    # 指北针 (文字)
    ax.annotate(
        "N\n↑", xy=(0.95, 0.95), xycoords="axes fraction",
        fontsize=14, ha="center", va="top", fontweight="bold",
    )

    # 比例尺
    scale_km = side_km * 0.3
    scale_deg = scale_km / (111.0 * math.cos(math.radians(geo.center_lat)))
    sx = lon0 + (lon1 - lon0) * 0.05
    sy = lat0 + (lat1 - lat0) * 0.05
    ax.plot([sx, sx + scale_deg], [sy, sy], "k-", linewidth=2)
    ax.text(sx + scale_deg / 2, sy - (lat1 - lat0) * 0.02,
            f"{scale_km:.1f} km", ha="center", fontsize=7)

    # 坐标系标注
    ax.set_xlabel(f"经度 (°E) — {geo.crs} / EPSG:{geo.epsg}", fontsize=8)
    ax.set_ylabel("纬度 (°N)", fontsize=8)
    ax.set_title(title, fontsize=12, fontweight="bold",
                 fontfamily="sans-serif")

    # 县区标注
    if geo.county_list:
        county_text = "涉及: " + "、".join(geo.county_list)
        ax.text(0.02, 0.02, county_text, transform=ax.transAxes,
                fontsize=7, color="#666666", va="bottom",
                fontfamily="sans-serif")

    fig.tight_layout()
    fig.savefig(str(output_path), dpi=150, bbox_inches="tight")
    plt.close(fig)


# ============================================================
# Public API
# ============================================================

def generate_figures(
    facts: dict,
    output_dir: str | Path,
    *,
    project_name: str = "",
) -> GeoPipelineResult:
    """
    GeoPipeline_v0 主入口: 从 facts 生成 3 张附图。

    产出:
      F-01: 项目地理位置图 (PNG)
      F-04: 水土流失防治责任范围图 (PNG)
      F-12: 取土场和弃渣场位置图 (PNG, 如有弃渣场/取土场)

    返回:
      GeoPipelineResult (含 artifacts, crs_check, manifest)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    geo = _extract_geo_input(facts, project_name)
    crs_ok, crs_note = check_crs(geo)

    artifacts: list[GeoArtifact] = []

    # 无坐标则无法出图
    if geo.center_lon == 0 and geo.center_lat == 0:
        return GeoPipelineResult(
            artifacts=[],
            crs_check_passed=crs_ok,
            crs_note="无中心坐标, 无法生成附图",
            manifest={"status": "no_coordinates", "artifacts": []},
        )

    # F-01: 项目地理位置图
    f01_path = output_dir / "F_01_location.png"
    _render_figure(geo, "art.figure.F_01_location",
                   f"{geo.project_name} — 项目地理位置图", f01_path)
    artifacts.append(GeoArtifact(
        artifact_id="art.figure.F_01_location",
        file_path=f01_path, format="png",
        title="项目地理位置图", crs_note=crs_note,
    ))

    # F-04: 防治责任范围图
    f04_path = output_dir / "F_04_responsibility_range.png"
    _render_figure(geo, "art.figure.F_04_responsibility_range",
                   f"{geo.project_name} — 水土流失防治责任范围图", f04_path,
                   show_zones=True)
    artifacts.append(GeoArtifact(
        artifact_id="art.figure.F_04_responsibility_range",
        file_path=f04_path, format="png",
        title="水土流失防治责任范围图", crs_note=crs_note,
    ))

    # F-12: 取土场和弃渣场位置图
    f12_path = output_dir / "F_12_borrow_disposal.png"
    _render_figure(geo, "art.figure.F_12_borrow_and_disposal_location",
                   f"{geo.project_name} — 取土场和弃渣场位置图", f12_path,
                   show_disposal=True)
    artifacts.append(GeoArtifact(
        artifact_id="art.figure.F_12_borrow_and_disposal_location",
        file_path=f12_path, format="png",
        title="取土场和弃渣场位置图", crs_note=crs_note,
    ))

    manifest = {
        "status": "generated",
        "crs": geo.crs,
        "epsg": geo.epsg,
        "crs_check_passed": crs_ok,
        "center": {"longitude": geo.center_lon, "latitude": geo.center_lat},
        "artifacts": [
            {"id": a.artifact_id, "path": str(a.file_path), "format": a.format}
            for a in artifacts
        ],
    }

    return GeoPipelineResult(
        artifacts=artifacts,
        crs_check_passed=crs_ok,
        crs_note=crs_note,
        manifest=manifest,
    )
