#!/usr/bin/env python3
"""
diff_workbench.py — CPSWC v0 Step 28: Review Workbench MVP

把 fact_diff.FactDiffReport 渲染成单文件只读 HTML 工作台。
五个视图: 影响摘要 / Facts / Calculators / Obligations / Narrative+Tables

用法:
  python -m cpswc.renderers.diff_workbench samples/shiwei_logistics_v0.json \\
    --patch '{"facts":{"field.fact.land.total_area":{"value":10.0,"unit":"hm²"}}}' \\
    -o diff_workbench.html
"""

from __future__ import annotations

import json
from typing import Any

from jinja2 import BaseLoader, Environment


# ============================================================
# Jinja2 template
# ============================================================

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CPSWC Diff Workbench — {{ patch_description }}</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans SC",sans-serif;
  line-height:1.6;color:#1a1a2e;background:#f8f9fa;padding:1.5rem;max-width:1200px;margin:0 auto}
h1{font-size:1.5rem;margin-bottom:.3rem}
h2{font-size:1.15rem;color:#16213e;border-bottom:2px solid #0f3460;padding-bottom:.3rem;margin:1.2rem 0 .6rem}
h3{font-size:1rem;color:#333;margin:.8rem 0 .4rem}

.card{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:1rem 1.2rem;margin-bottom:1rem;
  box-shadow:0 1px 3px rgba(0,0,0,.06)}

.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:600}
.badge-changed{background:#fff3cd;color:#856404}
.badge-added{background:#d4edda;color:#155724}
.badge-removed{background:#f8d7da;color:#721c24}
.badge-triggered{background:#d4edda;color:#155724}
.badge-untriggered{background:#f8d7da;color:#721c24}
.badge-full{background:#d4edda;color:#155724}
.badge-skeleton{background:#fff3cd;color:#856404}
.badge-na{background:#eee;color:#666}
.badge-info{background:#cce5ff;color:#004085}
.badge-muted{background:#eee;color:#666}

/* Tabs */
.tabs{display:flex;gap:0;border-bottom:2px solid #0f3460;margin-bottom:1rem;flex-wrap:wrap}
.tab{padding:.5rem 1rem;cursor:pointer;border:1px solid transparent;border-bottom:none;
  border-radius:6px 6px 0 0;font-size:.9rem;color:#555;background:#f0f0f0;white-space:nowrap}
.tab.active{color:#0f3460;background:#fff;border-color:#0f3460 #0f3460 #fff;font-weight:600}
.tab .count{font-size:.7rem;background:#0f3460;color:#fff;border-radius:10px;
  padding:1px 6px;margin-left:4px;vertical-align:middle}
.tab .count-zero{background:#ccc;color:#666}
.tab-content{display:none}
.tab-content.active{display:block}

/* Table */
table{width:100%;border-collapse:collapse;font-size:.85rem;margin:.5rem 0}
th,td{text-align:left;padding:.4rem .6rem;border-bottom:1px solid #eee}
th{background:#f5f5f5;font-weight:600;color:#333;position:sticky;top:0}
tr:hover td{background:#f9f9fe}
td.mono{font-family:"SF Mono",Consolas,"Liberation Mono",monospace;font-size:.8rem;word-break:break-all}

/* Diff cells */
.val-before{color:#dc3545;text-decoration:line-through;font-size:.8rem}
.val-after{color:#28a745;font-weight:600}
.val-arrow{color:#888;margin:0 .3rem;font-size:.75rem}

/* Impact summary cards */
.impact-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.8rem;margin:.8rem 0}
.impact-card{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:.8rem 1rem;text-align:center;
  transition:transform .1s}
.impact-card:hover{transform:translateY(-2px);box-shadow:0 2px 6px rgba(0,0,0,.1)}
.impact-card .number{font-size:2rem;font-weight:700;color:#0f3460}
.impact-card .number.zero{color:#ccc}
.impact-card .label{font-size:.8rem;color:#666;margin-top:.2rem}

/* Evidence chain */
.chain{background:#fafbff;border:1px solid #d0d7e8;border-radius:6px;padding:.8rem 1rem;margin:.5rem 0;
  font-size:.85rem}
.chain-arrow{color:#0f3460;font-weight:700;margin:0 .5rem}
.chain-node{display:inline-block;background:#e8ecf4;padding:2px 8px;border-radius:4px;margin:2px;font-size:.8rem}
.chain-node.highlight{background:#0f3460;color:#fff}

/* Section diff */
.section-diff{border-left:3px solid #0f3460;padding:.5rem .8rem;margin:.5rem 0;background:#fafbff;font-size:.83rem}
.diff-line{margin:.2rem 0;font-family:"SF Mono",Consolas,monospace;font-size:.8rem;line-height:1.5;
  white-space:pre-wrap;word-break:break-all}
.diff-line.removed{color:#dc3545;background:#ffeef0}
.diff-line.added{color:#28a745;background:#e6ffec}

/* Details */
details{margin:.3rem 0}
details>summary{cursor:pointer;padding:.3rem .5rem;border-radius:4px;font-size:.85rem}
details>summary:hover{background:#f0f4ff}
details>.detail-body{padding:.5rem .8rem;background:#fafbff;border-left:3px solid #0f3460;
  margin:.3rem 0 .3rem 1rem;font-size:.83rem}

/* Utility */
.text-muted{color:#888;font-size:.8rem}
.text-green{color:#28a745}
.text-red{color:#dc3545}
.mt-1{margin-top:.5rem}
.flex-row{display:flex;gap:1rem;flex-wrap:wrap}
.flex-col{flex:1;min-width:280px}
.kv-grid{display:grid;grid-template-columns:max-content 1fr;gap:.2rem .8rem;font-size:.85rem}
.kv-grid dt{color:#555;font-weight:600}
.kv-grid dd{color:#1a1a2e}
</style>
</head>
<body>

<!-- ====== HEADER ====== -->
<h1>CPSWC Diff Workbench</h1>
<p class="text-muted">{{ patch_description }}</p>

<!-- ====== TABS ====== -->
<div class="tabs" id="main-tabs">
  <div class="tab active" data-tab="summary">影响摘要</div>
  <div class="tab" data-tab="facts">Facts
    <span class="count {% if total_facts == 0 %}count-zero{% endif %}">{{ total_facts }}</span>
  </div>
  <div class="tab" data-tab="derived">Calculators
    <span class="count {% if total_derived == 0 %}count-zero{% endif %}">{{ total_derived }}</span>
  </div>
  <div class="tab" data-tab="obligations">Obligations
    <span class="count {% if total_obligations == 0 %}count-zero{% endif %}">{{ total_obligations }}</span>
  </div>
  <div class="tab" data-tab="narrative">Narrative
    <span class="count {% if total_sections == 0 %}count-zero{% endif %}">{{ total_sections }}</span>
  </div>
  <div class="tab" data-tab="tables">Tables
    <span class="count {% if total_tables == 0 %}count-zero{% endif %}">{{ total_tables }}</span>
  </div>
  <div class="tab" data-tab="chain">证据链</div>
</div>

<!-- ====== 1. IMPACT SUMMARY ====== -->
<div class="tab-content active" id="tab-summary">
  <div class="card">
    <h2>变更影响总览</h2>
    <div class="impact-grid">
      <div class="impact-card">
        <div class="number {% if total_facts == 0 %}zero{% endif %}">{{ total_facts }}</div>
        <div class="label">Facts 变更</div>
      </div>
      <div class="impact-card">
        <div class="number {% if total_derived == 0 %}zero{% endif %}">{{ total_derived }}</div>
        <div class="label">Calculators 变更</div>
      </div>
      <div class="impact-card">
        <div class="number {% if total_obligations == 0 %}zero{% endif %}">{{ total_obligations }}</div>
        <div class="label">Obligations 变更</div>
      </div>
      <div class="impact-card">
        <div class="number {% if total_sections == 0 %}zero{% endif %}">{{ total_sections }}</div>
        <div class="label">Narrative 变更</div>
      </div>
      <div class="impact-card">
        <div class="number {% if total_tables == 0 %}zero{% endif %}">{{ total_tables }}</div>
        <div class="label">Tables 变更</div>
      </div>
    </div>
  </div>

  <!-- Quick facts summary -->
  {% if fact_changes %}
  <div class="card">
    <h3>输入变更</h3>
    {% for fc in fact_changes %}
    <div style="margin:.3rem 0;font-size:.85rem">
      <code>{{ fc.field_id }}</code>:
      <span class="val-before">{{ fc.before_fmt }}</span>
      <span class="val-arrow">&rarr;</span>
      <span class="val-after">{{ fc.after_fmt }}</span>
      <span class="badge badge-{{ fc.change_type }}">{{ fc.change_type }}</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- Quick obligation changes -->
  {% if obligation_changes %}
  <div class="card">
    <h3>Obligation 触发状态变更</h3>
    {% for oc in obligation_changes %}
    <div style="margin:.3rem 0;font-size:.85rem">
      {% if oc.change_type == 'newly_triggered' %}
        <span class="badge badge-triggered">+ 新触发</span>
      {% else %}
        <span class="badge badge-untriggered">- 不再触发</span>
      {% endif %}
      <code>{{ oc.obligation_id }}</code>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- Quick narrative impact -->
  {% if narrative_changes %}
  <div class="card">
    <h3>受影响章节</h3>
    {% for nc in narrative_changes %}
    <div style="margin:.3rem 0;font-size:.85rem">
      {% if nc.change_type == 'both' or nc.change_type == 'status_changed' %}
        <span class="badge badge-{{ nc.after_status }}">{{ nc.before_status }} &rarr; {{ nc.after_status }}</span>
      {% else %}
        <span class="badge badge-changed">text</span>
      {% endif %}
      {{ nc.title }} <span class="text-muted">({{ nc.section_id }})</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}
</div>

<!-- ====== 2. FACTS ====== -->
<div class="tab-content" id="tab-facts">
  <div class="card">
    <h2>Facts 变更明细 ({{ fact_changes | length }})</h2>
    {% if fact_changes %}
    <table>
      <thead><tr><th>Field ID</th><th>Before</th><th>After</th><th>Type</th></tr></thead>
      <tbody>
      {% for fc in fact_changes %}
      <tr>
        <td class="mono">{{ fc.field_id }}</td>
        <td class="mono val-before">{{ fc.before_fmt }}</td>
        <td class="mono val-after">{{ fc.after_fmt }}</td>
        <td><span class="badge badge-{{ fc.change_type }}">{{ fc.change_type }}</span></td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p class="text-muted">无 facts 变更</p>
    {% endif %}
  </div>
</div>

<!-- ====== 3. CALCULATORS / DERIVED ====== -->
<div class="tab-content" id="tab-derived">
  <div class="card">
    <h2>Calculator 产出变更 ({{ derived_changes | length }})</h2>
    {% if derived_changes %}
    <table>
      <thead><tr><th>Derived Field</th><th>Before</th><th>After</th><th>Type</th></tr></thead>
      <tbody>
      {% for dc in derived_changes %}
      <tr>
        <td class="mono">{{ dc.field_id }}</td>
        <td class="mono val-before">{{ dc.before_fmt }}</td>
        <td class="mono val-after">{{ dc.after_fmt }}</td>
        <td><span class="badge badge-{{ dc.change_type }}">{{ dc.change_type }}</span></td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p class="text-muted">Calculator 产出无变更 — 本次修改的 fact 未被任何 calculator 消费</p>
    {% endif %}
  </div>
</div>

<!-- ====== 4. OBLIGATIONS ====== -->
<div class="tab-content" id="tab-obligations">
  <div class="card">
    <h2>Obligation 触发状态变更 ({{ obligation_changes | length }})</h2>
    {% if obligation_changes %}
    <table>
      <thead><tr><th>Obligation ID</th><th>Before</th><th>After</th><th>变更</th></tr></thead>
      <tbody>
      {% for oc in obligation_changes %}
      <tr>
        <td class="mono">{{ oc.obligation_id }}</td>
        <td>{% if oc.before %}triggered{% else %}not triggered{% endif %}</td>
        <td>{% if oc.after %}triggered{% else %}not triggered{% endif %}</td>
        <td>
          {% if oc.change_type == 'newly_triggered' %}
            <span class="badge badge-triggered">+ 新触发</span>
          {% else %}
            <span class="badge badge-untriggered">- 不再触发</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p class="text-muted">Obligation 触发状态无变更</p>
    {% endif %}
  </div>
</div>

<!-- ====== 5. NARRATIVE ====== -->
<div class="tab-content" id="tab-narrative">
  <div class="card">
    <h2>Narrative 变更 ({{ narrative_changes | length }})</h2>
    {% if narrative_changes %}
    {% for nc in narrative_changes %}
    <details {% if loop.index <= 5 %}open{% endif %}>
      <summary>
        {% if nc.change_type == 'both' or nc.change_type == 'status_changed' %}
          <span class="badge badge-{{ nc.after_status }}">{{ nc.before_status }} &rarr; {{ nc.after_status }}</span>
        {% elif nc.change_type == 'text_changed' %}
          <span class="badge badge-changed">text changed</span>
        {% else %}
          <span class="badge badge-muted">{{ nc.change_type }}</span>
        {% endif %}
        <strong>{{ nc.title }}</strong>
        <span class="text-muted">{{ nc.section_id }}</span>
      </summary>
      <div class="detail-body">
        {% if nc.diff_lines %}
          {% for dl in nc.diff_lines %}
            <div class="diff-line {{ dl.type }}">{{ dl.prefix }} {{ dl.text }}</div>
          {% endfor %}
        {% elif nc.text_diff_summary %}
          <pre style="white-space:pre-wrap;font-size:.8rem">{{ nc.text_diff_summary }}</pre>
        {% else %}
          <p class="text-muted">Status changed: {{ nc.before_status }} &rarr; {{ nc.after_status }}</p>
        {% endif %}
      </div>
    </details>
    {% endfor %}
    {% else %}
    <p class="text-muted">Narrative 无变更</p>
    {% endif %}
  </div>
</div>

<!-- ====== 6. TABLES ====== -->
<div class="tab-content" id="tab-tables">
  <div class="card">
    <h2>Table 变更 ({{ table_changes | length }})</h2>
    {% if table_changes %}
    <table>
      <thead><tr><th>Table ID</th><th>Changed Cells</th></tr></thead>
      <tbody>
      {% for tc in table_changes %}
      <tr>
        <td class="mono">{{ tc.table_id }}</td>
        <td>{{ tc.cell_changes }} cells</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p class="text-muted">Table 数据无变更</p>
    {% endif %}
  </div>
</div>

<!-- ====== 7. EVIDENCE CHAIN ====== -->
<div class="tab-content" id="tab-chain">
  <div class="card">
    <h2>影响链: Fact &rarr; Calculator &rarr; Obligation &rarr; Narrative / Table</h2>
    <p class="text-muted" style="margin-bottom:.8rem">
      改一个 fact，哪些环节被波及？以下展示完整的数据流向。
    </p>

    <!-- Input facts -->
    <h3>1. 输入变更 (Facts)</h3>
    <div class="chain">
      {% for fc in fact_changes %}
        <span class="chain-node highlight">{{ fc.field_id_short }}</span>
      {% endfor %}
      {% if not fact_changes %}<span class="text-muted">无</span>{% endif %}
    </div>

    <!-- Arrow -->
    {% if derived_changes %}
    <div style="text-align:center;margin:.5rem 0"><span class="chain-arrow">&darr;</span></div>
    <h3>2. Calculator 产出变更</h3>
    <div class="chain">
      {% for dc in derived_changes %}
        <span class="chain-node">{{ dc.field_id_short }}</span>
      {% endfor %}
    </div>
    {% endif %}

    <!-- Arrow -->
    {% if obligation_changes %}
    <div style="text-align:center;margin:.5rem 0"><span class="chain-arrow">&darr;</span></div>
    <h3>{% if derived_changes %}3{% else %}2{% endif %}. Obligation 触发变更</h3>
    <div class="chain">
      {% for oc in obligation_changes %}
        <span class="chain-node {% if oc.change_type == 'newly_triggered' %}highlight{% endif %}">
          {% if oc.change_type == 'newly_triggered' %}+{% else %}-{% endif %} {{ oc.obligation_id_short }}
        </span>
      {% endfor %}
    </div>
    {% endif %}

    <!-- Arrow -->
    {% if narrative_changes or table_changes %}
    <div style="text-align:center;margin:.5rem 0"><span class="chain-arrow">&darr;</span></div>
    <h3>{% if derived_changes and obligation_changes %}4{% elif derived_changes or obligation_changes %}3{% else %}2{% endif %}. 输出变更</h3>
    <div class="flex-row">
      {% if narrative_changes %}
      <div class="flex-col">
        <h3 style="font-size:.9rem">Narrative ({{ narrative_changes | length }} sections)</h3>
        <div class="chain">
          {% for nc in narrative_changes %}
            <span class="chain-node">{{ nc.section_id }}</span>
          {% endfor %}
        </div>
      </div>
      {% endif %}
      {% if table_changes %}
      <div class="flex-col">
        <h3 style="font-size:.9rem">Tables ({{ table_changes | length }})</h3>
        <div class="chain">
          {% for tc in table_changes %}
            <span class="chain-node">{{ tc.table_id }}</span>
          {% endfor %}
        </div>
      </div>
      {% endif %}
    </div>
    {% endif %}
  </div>

  <!-- Traceability statement -->
  <div class="card">
    <h3>可追溯性声明</h3>
    <p style="font-size:.85rem">
      本次变更共涉及 <strong>{{ total_facts }}</strong> 项 fact 输入修改，
      导致 <strong>{{ total_derived }}</strong> 个 calculator 产出变化，
      <strong>{{ total_obligations }}</strong> 条 obligation 触发状态改变，
      <strong>{{ total_sections }}</strong> 个正文章节受影响，
      <strong>{{ total_tables }}</strong> 张表格数据发生变化。
    </p>
    <p style="font-size:.85rem;margin-top:.5rem">
      所有变化均由 CPSWC 管线自动传播 — 无人工干预、无遗漏。
      每一处变更都可沿 Fact &rarr; Calculator &rarr; Obligation &rarr; Narrative/Table 链路追溯。
    </p>
  </div>
</div>

<!-- ====== TAB JS ====== -->
<script>
document.querySelectorAll('.tab').forEach(function(tab){
  tab.addEventListener('click',function(){
    var target=this.dataset.tab;
    document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active')});
    document.querySelectorAll('.tab-content').forEach(function(c){c.classList.remove('active')});
    this.classList.add('active');
    document.getElementById('tab-'+target).classList.add('active');
  });
});
</script>

</body>
</html>"""


# ============================================================
# Context builder
# ============================================================

def _fmt_value(v: Any) -> str:
    """Format a fact value for display."""
    if v is None:
        return "\u2014"
    if isinstance(v, dict) and "value" in v:
        return f"{v['value']} {v.get('unit', '')}"
    if isinstance(v, list):
        return json.dumps(v, ensure_ascii=False)[:120]
    return str(v)


def _short_id(field_id: str) -> str:
    """Shorten a field ID for chain display."""
    # field.fact.land.total_area → land.total_area
    parts = field_id.split(".")
    if len(parts) > 2 and parts[0] == "field":
        return ".".join(parts[2:])
    return field_id


def _build_diff_lines(summary: str, before_text: str, after_text: str) -> list[dict]:
    """Build line-by-line diff for narrative changes."""
    if not before_text and not after_text:
        return []

    bl = before_text.split("\n") if before_text else []
    al = after_text.split("\n") if after_text else []

    lines = []
    max_len = max(len(bl), len(al))
    for i in range(max_len):
        bline = bl[i] if i < len(bl) else ""
        aline = al[i] if i < len(al) else ""
        if bline == aline:
            continue
        if bline:
            lines.append({"type": "removed", "prefix": "-", "text": bline[:200]})
        if aline:
            lines.append({"type": "added", "prefix": "+", "text": aline[:200]})
    return lines


def _build_context(report) -> dict:
    """Build Jinja2 template context from FactDiffReport."""
    from cpswc.fact_diff import FactDiffReport

    fact_changes = []
    for fc in report.fact_changes:
        fact_changes.append({
            "field_id": fc.field_id,
            "field_id_short": _short_id(fc.field_id),
            "before_fmt": _fmt_value(fc.before),
            "after_fmt": _fmt_value(fc.after),
            "change_type": fc.change_type,
        })

    derived_changes = []
    for dc in report.derived_changes:
        derived_changes.append({
            "field_id": dc.field_id,
            "field_id_short": _short_id(dc.field_id),
            "before_fmt": _fmt_value(dc.before),
            "after_fmt": _fmt_value(dc.after),
            "change_type": dc.change_type,
        })

    obligation_changes = []
    for oc in report.obligation_changes:
        obligation_changes.append({
            "obligation_id": oc.obligation_id,
            "obligation_id_short": oc.obligation_id.replace("ob.", ""),
            "before": oc.before_triggered,
            "after": oc.after_triggered,
            "change_type": oc.change_type,
        })

    narrative_changes = []
    for nc in report.narrative_changes:
        narrative_changes.append({
            "section_id": nc.section_id,
            "title": nc.title,
            "change_type": nc.change_type,
            "before_status": nc.before_status,
            "after_status": nc.after_status,
            "text_diff_summary": nc.text_diff_summary,
            "diff_lines": [],  # will be populated below if we have full text
        })

    table_changes = []
    for tc in report.table_changes:
        table_changes.append({
            "table_id": tc.table_id,
            "cell_changes": tc.cell_changes,
        })

    return {
        "patch_description": report.patch_description,
        "total_facts": report.total_facts_changed,
        "total_derived": report.total_derived_changed,
        "total_obligations": report.total_obligations_changed,
        "total_sections": report.total_sections_changed,
        "total_tables": report.total_tables_changed,
        "fact_changes": fact_changes,
        "derived_changes": derived_changes,
        "obligation_changes": obligation_changes,
        "narrative_changes": narrative_changes,
        "table_changes": table_changes,
    }


# ============================================================
# Enhanced diff with full narrative text
# ============================================================

def compute_diff_with_text(before_input: dict, after_input: dict,
                           patch_description: str = "") -> tuple:
    """Run diff and also capture narrative block texts for line-level diff."""
    from cpswc.fact_diff import compute_diff, _run_pipeline

    report = compute_diff(before_input, after_input, patch_description)

    # Re-run to get block texts (compute_diff already ran pipelines,
    # but we need the block objects for text extraction)
    _, _, before_blocks = _run_pipeline(before_input)
    _, _, after_blocks = _run_pipeline(after_input)

    before_map = {b.section_id: b for b in before_blocks}
    after_map = {b.section_id: b for b in after_blocks}

    # Build text-level diff lines for each narrative change
    text_diffs = {}
    for nc in report.narrative_changes:
        bb = before_map.get(nc.section_id)
        ab = after_map.get(nc.section_id)

        def _block_text(block):
            if not block or not block.paragraphs:
                return ""
            return "\n".join(p.text for p in block.paragraphs)

        bt = _block_text(bb)
        at = _block_text(ab)
        text_diffs[nc.section_id] = _build_diff_lines(nc.text_diff_summary, bt, at)

    return report, text_diffs


# ============================================================
# Public API
# ============================================================

def render_diff_workbench(report, text_diffs: dict | None = None) -> str:
    """
    Render a FactDiffReport as single-file HTML workbench.

    Args:
        report: FactDiffReport from fact_diff.compute_diff()
        text_diffs: optional {section_id: [diff_lines]} for narrative detail

    Returns:
        Complete HTML string
    """
    env = Environment(loader=BaseLoader(), autoescape=True)
    template = env.from_string(_TEMPLATE)
    ctx = _build_context(report)

    # Inject text-level diffs into narrative changes
    if text_diffs:
        for nc in ctx["narrative_changes"]:
            nc["diff_lines"] = text_diffs.get(nc["section_id"], [])

    return template.render(**ctx)


# ============================================================
# CLI
# ============================================================

def _cli() -> int:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="CPSWC Diff Workbench — 事实变更影响可视化",
    )
    parser.add_argument("before", help="原始 sample JSON 文件")
    parser.add_argument("after", nargs="?", help="修改后 sample JSON")
    parser.add_argument("--patch", help='JSON patch: {"facts":{"field.X":new_val}}')
    parser.add_argument("-o", "--output", default="diff_workbench.html",
                        help="输出 HTML 文件路径 (默认 diff_workbench.html)")
    args = parser.parse_args()

    before_path = Path(args.before)
    if not before_path.exists():
        print(f"ERROR: {before_path} not found", file=__import__('sys').stderr)
        return 2

    with before_path.open(encoding="utf-8") as f:
        before_input = json.load(f)

    if args.after:
        after_path = Path(args.after)
        if not after_path.exists():
            print(f"ERROR: {after_path} not found", file=__import__('sys').stderr)
            return 2
        with after_path.open(encoding="utf-8") as f:
            after_input = json.load(f)
        desc = f"{before_path.name} \u2192 {after_path.name}"
    elif args.patch:
        from cpswc.fact_diff import apply_patch
        patch = json.loads(args.patch)
        after_input = apply_patch(before_input, patch)
        changed_keys = list((patch.get("facts") or {}).keys())
        desc = f"patch: {', '.join(changed_keys)}"
    else:
        print("ERROR: \u9700\u8981\u63d0\u4f9b after \u6587\u4ef6\u6216 --patch \u53c2\u6570",
              file=__import__('sys').stderr)
        return 2

    report, text_diffs = compute_diff_with_text(before_input, after_input, desc)
    html = render_diff_workbench(report, text_diffs)
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Diff Workbench HTML written to: {args.output}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
