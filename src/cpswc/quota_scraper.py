"""
quota_scraper.py — 水土保持定额数据采集与入库

数据源: yanshou100.com 2025年版水土保持工程概算定额
  1. 工程定额: GET /quota/search (REST API, 分页, 需登录 cookie)
  2. 机械索引: GET /dinge/json/jx-dinge.json (静态 JSON, 需登录 cookie)
  3. 机械台班明细: GET /dinge/json/jx-dinge-details.json (静态 JSON, 需登录 cookie)

注意: 该站点所有接口都需要微信扫码登录后的 session cookie。
      直接用 Python urllib 请求会被重定向到登录页。

推荐采集流程 (浏览器辅助):
  1. 在 Chrome 中登录 yanshou100.com (微信扫码)
  2. 打开 /dinge/2025dinge.html
  3. 通过 Claude in Chrome 执行浏览器端 JS 分页拉取全量数据
  4. POST 到本地临时服务 → 保存为 data/quota_2025/raw/*_latest.json
  5. 运行: python -m cpswc.quota_scraper --ingest-only

入库: SQLite (后续可迁移到其他数据库)

用法:
  python -m cpswc.quota_scraper --ingest-only      # 从已有 JSON 入库 (主要用法)
  python -m cpswc.quota_scraper --stats             # 查看库统计
  python -m cpswc.quota_scraper                     # 全量采集+入库 (需 cookie, 见下)
  python -m cpswc.quota_scraper --scrape-only       # 仅采集到 JSON
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any

from cpswc.paths import PROJECT_ROOT

# ============================================================
# 常量
# ============================================================

BASE_URL = "https://www.yanshou100.com"
QUOTA_SEARCH_URL = f"{BASE_URL}/quota/search"
MACHINE_INDEX_URL = f"{BASE_URL}/dinge/json/jx-dinge.json"
MACHINE_DETAILS_URL = f"{BASE_URL}/dinge/json/jx-dinge-details.json"

DATA_DIR = PROJECT_ROOT / "data" / "quota_2025"
DB_PATH = DATA_DIR / "quota_2025.db"

PAGE_SIZE = 50  # 分页大小, 保守值
REQUEST_DELAY = 0.3  # 秒, 请求间隔 (礼貌爬取)

USER_AGENT = "CPSWC/0.5 quota-scraper (local-cache, non-commercial)"


# ============================================================
# HTTP 工具
# ============================================================

def _fetch_json(url: str) -> Any:
    """GET JSON with proper headers and error handling."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ============================================================
# 采集: 工程定额 (分页)
# ============================================================

def scrape_quotas() -> list[dict]:
    """
    分页拉取全量工程定额数据。
    返回完整的 quota 记录列表 (含 details)。
    """
    all_records: list[dict] = []
    page = 1
    total_count = None

    print(f"[采集] 工程定额 — 分页 size={PAGE_SIZE}")

    while True:
        params = urllib.parse.urlencode({
            "searchType": "name",
            "keyword": "",
            "page": page,
            "size": PAGE_SIZE,
            "quotaCode": "",
        })
        url = f"{QUOTA_SEARCH_URL}?{params}"
        data = _fetch_json(url)

        if total_count is None:
            total_count = data.get("count", 0)
            print(f"  总记录数: {total_count}")

        records = data.get("data") or []
        if not records:
            break

        all_records.extend(records)
        fetched = len(all_records)
        print(f"  page {page}: +{len(records)} (累计 {fetched}/{total_count})")

        if fetched >= total_count:
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    print(f"[采集] 工程定额完成: {len(all_records)} 条")
    return all_records


# ============================================================
# 采集: 机械定额 (静态 JSON)
# ============================================================

def scrape_machines() -> tuple[list[dict], list[dict]]:
    """
    拉取机械索引 + 台班费明细。
    返回 (machine_index, machine_details)。
    """
    print("[采集] 机械索引...")
    index = _fetch_json(MACHINE_INDEX_URL)
    print(f"  机械索引: {len(index)} ���")

    time.sleep(REQUEST_DELAY)

    print("[采集] 机械台���明细...")
    details = _fetch_json(MACHINE_DETAILS_URL)
    print(f"  台班明细: {len(details)} 条")

    return index, details


# ============================================================
# 保存 JSON 快照 (中间产物)
# ============================================================

def save_json_snapshot(
    quotas: list[dict],
    machine_index: list[dict],
    machine_details: list[dict],
) -> None:
    """保存原始 JSON 快照到 data/quota_2025/raw/"""
    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    ts = time.strftime("%Y%m%d_%H%M%S")

    (raw_dir / f"quotas_{ts}.json").write_text(
        json.dumps(quotas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (raw_dir / f"machine_index_{ts}.json").write_text(
        json.dumps(machine_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (raw_dir / f"machine_details_{ts}.json").write_text(
        json.dumps(machine_details, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 同时写一份 latest (覆盖)
    (raw_dir / "quotas_latest.json").write_text(
        json.dumps(quotas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (raw_dir / "machine_index_latest.json").write_text(
        json.dumps(machine_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (raw_dir / "machine_details_latest.json").write_text(
        json.dumps(machine_details, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[快照] 已保存到 {raw_dir}/ (timestamped + latest)")


def load_json_snapshot() -> tuple[list[dict], list[dict], list[dict]]:
    """从 latest 快照加载."""
    raw_dir = DATA_DIR / "raw"
    quotas = json.loads((raw_dir / "quotas_latest.json").read_text(encoding="utf-8"))
    mi = json.loads((raw_dir / "machine_index_latest.json").read_text(encoding="utf-8"))
    md = json.loads((raw_dir / "machine_details_latest.json").read_text(encoding="utf-8"))
    return quotas, mi, md


# ============================================================
# SQLite Schema
# ============================================================

SCHEMA_SQL = """
-- 工程定额主表
CREATE TABLE IF NOT EXISTS quotas (
    code          TEXT PRIMARY KEY,   -- 定额编码 (如 "0309")
    title         TEXT NOT NULL,      -- 定额名称
    subtitle      TEXT DEFAULT '',
    unit          TEXT NOT NULL,      -- 计量单位 (如 "100m³砌体方")
    content       TEXT DEFAULT '',    -- 工作内容
    scope         TEXT DEFAULT '',
    remark        TEXT DEFAULT '',
    page          TEXT DEFAULT '',    -- 原书页码
    chapter       TEXT NOT NULL       -- 章节编号 (前2位)
);

-- 工程定额子项 (工料机明细)
CREATE TABLE IF NOT EXISTS quota_details (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    quota_code    TEXT NOT NULL,      -- → quotas.code
    detail_code   TEXT NOT NULL,      -- ��项编号 (如 "03027")
    spec_name     TEXT NOT NULL,      -- 规格名称 (如 "人工", "块（片）石")
    spec_value    TEXT NOT NULL,      -- 规格值 (如 "863.9")
    spec_unit     TEXT DEFAULT '',    -- 单位 (如 "工时", "m³")
    type_name     TEXT NOT NULL,      -- 分类: 人工/材料/机械/其他
    jx_id         TEXT DEFAULT '',    -- 关联机械 ID (如 "jx69")
    FOREIGN KEY (quota_code) REFERENCES quotas(code)
);

-- 机械索引
CREATE TABLE IF NOT EXISTS machines (
    jx_id         TEXT PRIMARY KEY,   -- 机械 ID (��� "jx69")
    dimension_name TEXT DEFAULT '',   -- 英文标识
    name          TEXT NOT NULL,      -- 中文名称 (如 "搅拌机 0.4m³")
    quota_code    TEXT DEFAULT ''     -- 关联定额编号
);

-- 机械台班费明细
CREATE TABLE IF NOT EXISTS machine_details (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    jx_id         TEXT NOT NULL,      -- → machines.jx_id
    quota_code    TEXT DEFAULT '',    -- 定额编号
    spec_id       TEXT NOT NULL,      -- 规格标识 (depreciation_expense 等)
    spec_name     TEXT NOT NULL,      -- 中文名称 (折旧费 等)
    spec_value    TEXT NOT NULL,      -- 值
    spec_unit     TEXT DEFAULT '',    -- 单位
    name          TEXT DEFAULT '',    -- 机械名称 (冗余, 方便查询)
    chapter_no    TEXT DEFAULT '',    -- 章节序号
    chapter_name  TEXT DEFAULT '',    -- 章���名称
    page          TEXT DEFAULT '',    -- 页码
    FOREIGN KEY (jx_id) REFERENCES machines(jx_id)
);

-- 元数��
CREATE TABLE IF NOT EXISTS scrape_meta (
    key           TEXT PRIMARY KEY,
    value         TEXT NOT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_qd_quota_code ON quota_details(quota_code);
CREATE INDEX IF NOT EXISTS idx_qd_type_name ON quota_details(type_name);
CREATE INDEX IF NOT EXISTS idx_qd_detail_code ON quota_details(detail_code);
CREATE INDEX IF NOT EXISTS idx_md_jx_id ON machine_details(jx_id);
CREATE INDEX IF NOT EXISTS idx_md_spec_id ON machine_details(spec_id);
"""


# ============================================================
# 入库
# ============================================================

def create_db() -> sqlite3.Connection:
    """创建/重建数据库."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[入库] 已删除旧库: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA_SQL)
    print(f"[入库] 数据库已创建: {DB_PATH}")
    return conn


def ingest_quotas(conn: sqlite3.Connection, quotas: list[dict]) -> tuple[int, int]:
    """导入工程定额 + 子项, 返回 (quota_count, detail_count)."""
    quota_count = 0
    detail_count = 0

    for q in quotas:
        code = q.get("code", "")
        chapter = code[:2] if len(code) >= 2 else ""

        conn.execute(
            "INSERT OR REPLACE INTO quotas (code, title, subtitle, unit, content, scope, remark, page, chapter) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (code, q.get("title", ""), q.get("subtitle", ""),
             q.get("unit", ""), q.get("content", ""), q.get("scope", ""),
             q.get("remark", ""), q.get("page", ""), chapter),
        )
        quota_count += 1

        for det in (q.get("details") or []):
            detail_code = det.get("code", "")
            for spec in (det.get("specList") or []):
                conn.execute(
                    "INSERT INTO quota_details "
                    "(quota_code, detail_code, spec_name, spec_value, spec_unit, type_name, jx_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (code, detail_code,
                     spec.get("specName") or "", spec.get("specValue") or "",
                     spec.get("specUnit") or "", spec.get("typeName") or "",
                     spec.get("jxId") or ""),
                )
                detail_count += 1

    conn.commit()
    return quota_count, detail_count


def ingest_machines(
    conn: sqlite3.Connection,
    index: list[dict],
    details: list[dict],
) -> tuple[int, int]:
    """导入机械索引 + 台班明细, 返回 (index_count, detail_count)."""
    index_count = 0
    for m in index:
        conn.execute(
            "INSERT OR REPLACE INTO machines (jx_id, dimension_name, name, quota_code) "
            "VALUES (?, ?, ?, ?)",
            (m.get("jx_id", ""), m.get("dimension_name", ""),
             m.get("含义", ""), m.get("定额编号", "")),
        )
        index_count += 1

    detail_count = 0
    for d in details:
        conn.execute(
            "INSERT INTO machine_details "
            "(jx_id, quota_code, spec_id, spec_name, spec_value, spec_unit, "
            " name, chapter_no, chapter_name, page) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (d.get("jx-id", ""), d.get("定额编号", ""),
             d.get("规格标识", ""), d.get("规格名称", ""),
             d.get("规格值", ""), d.get("规格值单位", ""),
             d.get("名称", ""), d.get("章节序号", ""),
             d.get("章节名称", ""), d.get("页码", "")),
        )
        detail_count += 1

    conn.commit()
    return index_count, detail_count


def write_meta(conn: sqlite3.Connection, quotas: list, machines: list, details: list):
    """写入采集元数据."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    meta = {
        "scrape_timestamp": ts,
        "source": "yanshou100.com/dinge/2025dinge.html",
        "edition": "2025年版《水土保持工程概算定��》",
        "quota_count": str(len(quotas)),
        "machine_index_count": str(len(machines)),
        "machine_detail_count": str(len(details)),
    }
    for k, v in meta.items():
        conn.execute(
            "INSERT OR REPLACE INTO scrape_meta (key, value) VALUES (?, ?)",
            (k, v),
        )
    conn.commit()


# ============================================================
# 统计
# ============================================================

def print_stats():
    """打印数据库统计."""
    if not DB_PATH.exists():
        print(f"数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))

    print("=" * 60)
    print(" 水土保持定额数据库统计")
    print("=" * 60)

    # 元数据
    for key, val in conn.execute("SELECT key, value FROM scrape_meta ORDER BY key"):
        print(f"  {key}: {val}")
    print()

    # 各表记录数
    tables = ["quotas", "quota_details", "machines", "machine_details"]
    for t in tables:
        (cnt,) = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()
        print(f"  {t}: {cnt} 条")
    print()

    # 各章节分布
    print("  章节分布 (quotas):")
    for ch, cnt in conn.execute(
        "SELECT chapter, COUNT(*) FROM quotas GROUP BY chapter ORDER BY chapter"
    ):
        (title,) = conn.execute(
            "SELECT title FROM quotas WHERE chapter=? LIMIT 1", (ch,)
        ).fetchone()
        print(f"    第{int(ch):>2d}章: {cnt:>3d} 条  (首条: {title})")
    print()

    # 子项类型分布
    print("  子��类型分布 (quota_details):")
    for tn, cnt in conn.execute(
        "SELECT type_name, COUNT(*) FROM quota_details GROUP BY type_name ORDER BY COUNT(*) DESC"
    ):
        print(f"    {tn or 'null':8s}: {cnt:>5d}")
    print()

    # 机械台班费规格分布
    print("  机械规格分布 (machine_details):")
    for sid, cnt in conn.execute(
        "SELECT spec_id, COUNT(*) FROM machine_details GROUP BY spec_id ORDER BY COUNT(*) DESC"
    ):
        print(f"    {sid:40s}: {cnt:>4d}")

    print("=" * 60)
    conn.close()


# ============================================================
# Main
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="水土保持定额数据采集与入库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--scrape-only", action="store_true",
                        help="仅采集到 JSON, 不入库")
    parser.add_argument("--ingest-only", action="store_true",
                        help="从已有 JSON 快照入库 (不重新采集)")
    parser.add_argument("--stats", action="store_true",
                        help="显示数据库统计")
    args = parser.parse_args()

    if args.stats:
        print_stats()
        return 0

    # --- 采集 ---
    if args.ingest_only:
        print("[模式] 从已有快照入库")
        try:
            quotas, machine_index, machine_details = load_json_snapshot()
            print(f"  加载: {len(quotas)} quotas, {len(machine_index)} machines, "
                  f"{len(machine_details)} machine details")
        except FileNotFoundError as e:
            print(f"ERROR: 快照不存在: {e}", file=sys.stderr)
            return 1
    else:
        print("[模式] 全量采集")
        print()
        quotas = scrape_quotas()
        print()
        machine_index, machine_details = scrape_machines()
        print()
        save_json_snapshot(quotas, machine_index, machine_details)
        print()

    if args.scrape_only:
        print("[完成] 仅采集, 跳过入库")
        return 0

    # --- 入库 ---
    conn = create_db()

    qc, qdc = ingest_quotas(conn, quotas)
    print(f"[入库] 工程定额: {qc} 条主记录, {qdc} 条子项")

    mic, mdc = ingest_machines(conn, machine_index, machine_details)
    print(f"[入库] 机械定额: {mic} 条索引, {mdc} 条台班明细")

    write_meta(conn, quotas, machine_index, machine_details)
    conn.close()

    print()
    print_stats()
    return 0


if __name__ == "__main__":
    sys.exit(main())
