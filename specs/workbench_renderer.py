#!/usr/bin/env python3
"""
workbench_renderer.py — CPSWC v0 Static HTML Workbench Renderer

Step 12B: 把 RuntimeSnapshot 渲染成单文件只读 HTML 工作台。

输入: RuntimeSnapshot (dict, 由 cpswc_runtime.run_project() 产出)
输出: 单文件 HTML (内嵌 CSS + 少量原生 JS)

设计边界:
  - 只读, 不做编辑/表单/提交
  - 单文件, 不依赖 CDN / 外部资源 / 网络
  - 模板内嵌在本文件中, 不建 templates/ 目录
  - 6 个视图块: Summary / Facts+Derived / Calculators / Obligations / Drill-down / Freeze

使用方式:
  from workbench_renderer import render_workbench
  html = render_workbench(snapshot_dict, frozen_dict=None, version_dict=None)
  Path("workbench.html").write_text(html)
"""

from __future__ import annotations

import json
from typing import Any

from jinja2 import BaseLoader, Environment

# ============================================================
# Jinja2 template (内嵌, 不独立文件)
# ============================================================

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CPSWC v0 Workbench — {{ project_name }}</title>
<style>
/* ---- Reset + Base ---- */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans SC",sans-serif;
  line-height:1.6;color:#1a1a2e;background:#f8f9fa;padding:1.5rem;max-width:1200px;margin:0 auto}
h1{font-size:1.5rem;margin-bottom:.5rem}
h2{font-size:1.15rem;color:#16213e;border-bottom:2px solid #0f3460;padding-bottom:.3rem;margin:1.5rem 0 .8rem}
h3{font-size:1rem;color:#333;margin:.8rem 0 .4rem}

/* ---- Card ---- */
.card{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:1rem 1.2rem;margin-bottom:1rem;
  box-shadow:0 1px 3px rgba(0,0,0,.06)}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:600}
.badge-ok{background:#d4edda;color:#155724}
.badge-err{background:#f8d7da;color:#721c24}
.badge-info{background:#cce5ff;color:#004085}
.badge-warn{background:#fff3cd;color:#856404}
.badge-critical{background:#e2e3f5;color:#383d6e}
.badge-muted{background:#eee;color:#666}

/* ---- Tabs ---- */
.tabs{display:flex;gap:0;border-bottom:2px solid #0f3460;margin-bottom:1rem}
.tab{padding:.5rem 1rem;cursor:pointer;border:1px solid transparent;border-bottom:none;
  border-radius:6px 6px 0 0;font-size:.9rem;color:#555;background:#f0f0f0}
.tab.active{color:#0f3460;background:#fff;border-color:#0f3460 #0f3460 #fff;font-weight:600}
.tab-content{display:none}
.tab-content.active{display:block}

/* ---- Table ---- */
table{width:100%;border-collapse:collapse;font-size:.85rem;margin:.5rem 0}
th,td{text-align:left;padding:.4rem .6rem;border-bottom:1px solid #eee}
th{background:#f5f5f5;font-weight:600;color:#333;position:sticky;top:0}
tr:hover td{background:#f9f9fe}
td.mono{font-family:"SF Mono",Consolas,"Liberation Mono",monospace;font-size:.8rem;word-break:break-all}

/* ---- Details/Summary (drill-down) ---- */
details{margin:.3rem 0}
details>summary{cursor:pointer;padding:.3rem .5rem;border-radius:4px;font-size:.85rem}
details>summary:hover{background:#f0f4ff}
details>.detail-body{padding:.5rem .8rem;background:#fafbff;border-left:3px solid #0f3460;
  margin:.3rem 0 .3rem 1rem;font-size:.83rem}

/* ---- Search ---- */
.search-box{width:100%;padding:.4rem .6rem;border:1px solid #ccc;border-radius:4px;
  font-size:.85rem;margin-bottom:.6rem}

/* ---- Utilities ---- */
.flex-row{display:flex;gap:1rem;flex-wrap:wrap}
.flex-col{flex:1;min-width:300px}
.text-muted{color:#888;font-size:.8rem}
.text-green{color:#28a745}
.text-red{color:#dc3545}
.mt-1{margin-top:.5rem}
.kv-grid{display:grid;grid-template-columns:max-content 1fr;gap:.2rem .8rem;font-size:.85rem}
.kv-grid dt{color:#555;font-weight:600}
.kv-grid dd{color:#1a1a2e}
.scroll-y{max-height:500px;overflow-y:auto}
</style>
</head>
<body>

<!-- ====== HEADER ====== -->
<h1>CPSWC v0 Workbench</h1>
<p class="text-muted">
  Snapshot: <code>{{ snapshot_id }}</code> &middot;
  {{ timestamp }} &middot;
  Ruleset: {{ ruleset }}
</p>

<!-- ====== TABS ====== -->
<div class="tabs" id="main-tabs">
  <div class="tab active" data-tab="summary">Summary</div>
  <div class="tab" data-tab="facts">Facts / Derived</div>
  <div class="tab" data-tab="calculators">Calculators</div>
  <div class="tab" data-tab="obligations">Obligations</div>
  <div class="tab" data-tab="drilldown">Rule Drill-down</div>
  <div class="tab" data-tab="freeze">Freeze / Version</div>
</div>

<!-- ====== 1. SUMMARY ====== -->
<div class="tab-content active" id="tab-summary">
  <div class="card">
    <h2>Project Summary</h2>
    <dl class="kv-grid">
      <dt>Project</dt><dd>{{ project_name }}</dd>
      <dt>Code</dt><dd>{{ project_code }}</dd>
      <dt>Industry</dt><dd>{{ industry }}</dd>
      <dt>Species</dt><dd>{{ species }}</dd>
      <dt>Ruleset</dt><dd>{{ ruleset }}</dd>
      <dt>Lifecycle</dt><dd>{{ lifecycle }}</dd>
    </dl>
  </div>
  <div class="flex-row">
    <div class="card flex-col">
      <h3>Registries</h3>
      <p>{{ registries_loaded | join(', ') }}</p>
    </div>
    <div class="card flex-col">
      <h3>Counts</h3>
      <dl class="kv-grid">
        <dt>Facts</dt><dd>{{ facts_count }}</dd>
        <dt>Derived</dt><dd>{{ derived_count }}</dd>
        <dt>Calculators</dt><dd>{{ calc_count }}</dd>
        <dt>Obligations triggered</dt><dd>{{ triggered_count }}</dd>
        <dt>Artifacts required</dt><dd>{{ artifacts_count }}</dd>
        <dt>Assurances required</dt><dd>{{ assurances_count }}</dd>
      </dl>
    </div>
  </div>
</div>

<!-- ====== 2. FACTS / DERIVED ====== -->
<div class="tab-content" id="tab-facts">
  <div class="card">
    <h2>Facts ({{ facts | length }})</h2>
    <input type="text" class="search-box" placeholder="Search facts..." onkeyup="filterTable(this,'facts-table')">
    <div class="scroll-y">
    <table id="facts-table">
      <thead><tr><th>Field ID</th><th>Value</th></tr></thead>
      <tbody>
      {% for fid, fval in facts %}
      <tr><td class="mono">{{ fid }}</td><td class="mono">{{ fval | truncate(120) }}</td></tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
  </div>
  <div class="card">
    <h2>Derived Fields ({{ derived | length }})</h2>
    <div class="scroll-y">
    <table>
      <thead><tr><th>Field ID</th><th>Value</th><th>Source Calculator</th></tr></thead>
      <tbody>
      {% for d in derived %}
      <tr>
        <td class="mono">{{ d.field_id }}</td>
        <td class="mono">{{ d.value_str | truncate(200) }}</td>
        <td><span class="badge badge-info">{{ d.calculator_id }}</span></td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
  </div>
</div>

<!-- ====== 3. CALCULATORS ====== -->
<div class="tab-content" id="tab-calculators">
  <div class="card">
    <h2>Live Calculators ({{ calc_results | length }})</h2>
    {% for cr in calc_results %}
    <details>
      <summary>
        {% if cr.status == 'ok' %}<span class="badge badge-ok">OK</span>{% else %}<span class="badge badge-err">ERR</span>{% endif %}
        <strong>{{ cr.calculator_id }}</strong>
        &rarr; {{ cr.output_field_id }}
      </summary>
      <div class="detail-body">
        <dl class="kv-grid">
          <dt>Status</dt><dd>{{ cr.status }}</dd>
          <dt>Output</dt><dd class="mono">{{ cr.value_str | truncate(300) }}</dd>
          <dt>Unit</dt><dd>{{ cr.unit }}</dd>
          {% if cr.error_message %}<dt>Error</dt><dd class="text-red">{{ cr.error_message }}</dd>{% endif %}
        </dl>
      </div>
    </details>
    {% endfor %}
  </div>
</div>

<!-- ====== 4. OBLIGATIONS / ARTIFACTS / ASSURANCES ====== -->
<div class="tab-content" id="tab-obligations">
  <div class="flex-row">
    <div class="card flex-col">
      <h2>Triggered ({{ triggered | length }})</h2>
      {% for ob in triggered %}
      <div style="padding:2px 0"><span class="badge badge-ok">+</span> <code>{{ ob }}</code></div>
      {% endfor %}
    </div>
    <div class="card flex-col">
      <h2>Not Triggered ({{ not_triggered | length }})</h2>
      {% for ob in not_triggered %}
      <div style="padding:2px 0"><span class="badge badge-muted">&ndash;</span> <code>{{ ob }}</code></div>
      {% endfor %}
    </div>
  </div>
  <div class="card">
    <h2>Required Artifacts ({{ artifacts | length }})</h2>
    <div class="scroll-y">
    <table>
      <thead><tr><th>#</th><th>Artifact ID</th></tr></thead>
      <tbody>
      {% for a in artifacts %}
      <tr><td>{{ loop.index }}</td><td class="mono">{{ a }}</td></tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
  </div>
  <div class="card">
    <h2>Required Assurances ({{ assurances | length }})</h2>
    {% for a in assurances %}
    <div style="padding:2px 0"><span class="badge badge-info">AS</span> <code>{{ a }}</code></div>
    {% endfor %}
  </div>
</div>

<!-- ====== 5. RULE DRILL-DOWN ====== -->
<div class="tab-content" id="tab-drilldown">
  <div class="card">
    <h2>Obligation Drill-down</h2>
    <input type="text" class="search-box" placeholder="Search obligations..." onkeyup="filterDetails(this,'ob-drilldown')">
    <div id="ob-drilldown" class="scroll-y">
    {% for ob in obligation_details %}
    <details>
      <summary>
        {% if ob.triggered %}<span class="badge badge-ok">TRIG</span>{% else %}<span class="badge badge-muted">OFF</span>{% endif %}
        <code>{{ ob.obligation_id }}</code>
        <span class="text-muted">{{ ob.mode }}</span>
      </summary>
      <div class="detail-body">
        <dl class="kv-grid">
          <dt>Trigger mode</dt><dd>{{ ob.mode }}</dd>
          <dt>DSL expr</dt><dd class="mono">{{ ob.py_expr | truncate(300) }}</dd>
          {% if ob.source_rule_id %}<dt>source_rule_id</dt><dd class="mono">{{ ob.source_rule_id }}</dd>{% endif %}
          {% if ob.normative_basis_refs %}<dt>normative_basis_refs</dt><dd class="mono">{{ ob.normative_basis_refs | join(', ') }}</dd>{% endif %}
          {% if ob.evidence_anchor_refs %}<dt>evidence_anchor_refs</dt><dd class="mono">{{ ob.evidence_anchor_refs | join(', ') }}</dd>{% endif %}
          {% if ob.authority_class %}<dt>authority / rank</dt><dd>{{ ob.authority_class }} ({{ ob.precedence_rank }})</dd>{% endif %}
          {% if ob.required_artifact_refs %}<dt>required_artifacts</dt><dd class="mono">{{ ob.required_artifact_refs | join(', ') }}</dd>{% endif %}
          {% if ob.required_assurance_refs %}<dt>required_assurances</dt><dd class="mono">{{ ob.required_assurance_refs | join(', ') }}</dd>{% endif %}
        </dl>
      </div>
    </details>
    {% endfor %}
    </div>
  </div>
  <div class="card">
    <h2>Calculator Drill-down</h2>
    {% for cd in calculator_drilldown %}
    <details>
      <summary>
        <span class="badge badge-critical">CAL</span>
        <code>{{ cd.calculator_id }}</code>
        <span class="text-muted">{{ cd.authority_class }} (rank {{ cd.precedence_rank }})</span>
      </summary>
      <div class="detail-body">
        <dl class="kv-grid">
          <dt>normative_basis_refs</dt><dd class="mono">{{ cd.normative_basis_refs | join(', ') }}</dd>
          <dt>evidence_anchor_refs</dt><dd class="mono">{{ cd.evidence_anchor_refs | join(', ') }}</dd>
          <dt>authority_class</dt><dd>{{ cd.authority_class }}</dd>
          <dt>precedence_rank</dt><dd>{{ cd.precedence_rank }}</dd>
          <dt>protection_level</dt><dd>{{ cd.protection_level }}</dd>
          <dt>inputs</dt><dd class="mono">{{ cd.input_refs | join(', ') }}</dd>
          <dt>outputs</dt><dd class="mono">{{ cd.output_refs | join(', ') }}</dd>
        </dl>
      </div>
    </details>
    {% endfor %}
  </div>
</div>

<!-- ====== 6. FREEZE / VERSION ====== -->
<div class="tab-content" id="tab-freeze">
  {% if frozen %}
  <div class="card">
    <h2>FrozenSubmissionInput</h2>
    <dl class="kv-grid">
      <dt>content_hash</dt><dd class="mono">{{ frozen.content_hash }}</dd>
      <dt>fact_snapshot_hash</dt><dd class="mono">{{ frozen.fact_snapshot_hash }}</dd>
      <dt>frozen_at</dt><dd>{{ frozen.frozen_at }}</dd>
    </dl>
    <h3 class="mt-1">Manifests</h3>
    <dl class="kv-grid">
      <dt>Artifacts</dt><dd>{{ frozen.artifact_manifest | length }} items</dd>
      <dt>Assurances</dt><dd>{{ frozen.assurance_manifest | length }} items</dd>
      <dt>Calculators</dt><dd>{{ frozen.calculator_manifest | join(', ') }}</dd>
      <dt>Obligations</dt><dd>{{ frozen.obligation_manifest | length }} items</dd>
    </dl>
  </div>
  {% endif %}
  {% if version %}
  <div class="card">
    <h2>SubmissionPackageVersion</h2>
    <dl class="kv-grid">
      <dt>version_id</dt><dd class="mono">{{ version.version_id }}</dd>
      <dt>frozen_input_hash</dt><dd class="mono">{{ version.frozen_input_hash }}</dd>
      <dt>timestamp</dt><dd>{{ version.timestamp }}</dd>
      {% if version.previous_version_id %}<dt>previous</dt><dd class="mono">{{ version.previous_version_id }}</dd>{% endif %}
    </dl>
  </div>
  {% endif %}
  {% if not frozen and not version %}
  <div class="card"><p class="text-muted">Use <code>--freeze --version</code> to generate frozen snapshot and version.</p></div>
  {% endif %}
</div>

<!-- ====== JS ====== -->
<script>
// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
  });
});

// Table search
function filterTable(input, tableId) {
  const q = input.value.toLowerCase();
  const rows = document.getElementById(tableId).querySelectorAll('tbody tr');
  rows.forEach(r => { r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none'; });
}

// Details search
function filterDetails(input, containerId) {
  const q = input.value.toLowerCase();
  const items = document.getElementById(containerId).querySelectorAll('details');
  items.forEach(d => { d.style.display = d.textContent.toLowerCase().includes(q) ? '' : 'none'; });
}
</script>

<footer style="margin-top:2rem;padding-top:1rem;border-top:1px solid #ddd;font-size:.75rem;color:#999;text-align:center">
  CPSWC v0 Workbench Shell (Step 12B) &middot; Generated {{ timestamp }} &middot; Read-only internal tool
</footer>
</body>
</html>"""


# ============================================================
# Template context builder
# ============================================================

def _val_str(v: Any) -> str:
    """把各种值类型转成简短可读字符串"""
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def _build_context(
    snapshot: dict,
    frozen: dict | None = None,
    version: dict | None = None,
    registries: dict | None = None,
) -> dict:
    """从 RuntimeSnapshot dict 构建 Jinja2 模板上下文"""
    summary = snapshot.get("project_input_summary") or {}
    manifest = snapshot.get("manifest") or {}

    # Facts as sorted list of (field_id, value_str)
    # We need the original project_input to get facts — but snapshot only has facts_count.
    # So we also accept the original facts dict via an extra key "_original_facts"
    original_facts = snapshot.get("_original_facts") or {}
    facts_list = sorted(
        (fid, _val_str(fval)) for fid, fval in original_facts.items()
    )

    # Derived fields
    derived_fields = snapshot.get("derived_fields") or {}
    calc_results = snapshot.get("calculator_results") or []
    calc_id_by_output = {}
    for cr in calc_results:
        if cr.get("output_field_id"):
            calc_id_by_output[cr["output_field_id"]] = cr.get("calculator_id", "")

    derived_list = [
        {
            "field_id": fid,
            "value_str": _val_str(fval),
            "calculator_id": calc_id_by_output.get(fid, "?"),
        }
        for fid, fval in sorted(derived_fields.items())
    ]

    # Calculator results with value_str
    calc_results_display = []
    for cr in calc_results:
        calc_results_display.append({
            **cr,
            "value_str": _val_str(cr.get("value")),
        })

    # Obligation details with drill-down info from registries
    obligation_details = []
    ob_reg = {}
    if registries:
        ob_reg = (registries.get("obligations") or {}).get("obligations") or {}
    for od in (snapshot.get("obligation_details") or []):
        ob_def = ob_reg.get(od.get("obligation_id")) or {}
        obligation_details.append({
            "obligation_id": od.get("obligation_id"),
            "triggered": od.get("triggered"),
            "mode": od.get("mode"),
            "py_expr": od.get("py_expr", ""),
            "source_rule_id": ob_def.get("source_rule_id"),
            "normative_basis_refs": ob_def.get("normative_basis_refs") or [],
            "evidence_anchor_refs": ob_def.get("evidence_anchor_refs") or [],
            "authority_class": ob_def.get("authority_class"),
            "precedence_rank": ob_def.get("precedence_rank"),
            "required_artifact_refs": ob_def.get("required_artifact_refs") or [],
            "required_assurance_refs": ob_def.get("required_assurance_refs") or [],
        })

    # Calculator drill-down from registries
    calculator_drilldown = []
    if registries:
        cal_reg = (registries.get("calculators") or {}).get("calculators") or {}
        for cid, cdef in cal_reg.items():
            if not isinstance(cdef, dict) or cdef.get("status") != "live":
                continue
            calculator_drilldown.append({
                "calculator_id": cid,
                "normative_basis_refs": cdef.get("normative_basis_refs") or [],
                "evidence_anchor_refs": cdef.get("evidence_anchor_refs") or [],
                "authority_class": cdef.get("authority_class", ""),
                "precedence_rank": cdef.get("precedence_rank", ""),
                "protection_level": cdef.get("protection_level", ""),
                "input_refs": [i.get("ref", "") for i in (cdef.get("inputs") or [])],
                "output_refs": [o.get("ref", "") for o in (cdef.get("outputs") or [])],
            })

    return {
        # Summary
        "project_name": summary.get("name", "Unknown"),
        "project_code": summary.get("code", ""),
        "industry": summary.get("industry", ""),
        "species": summary.get("species", ""),
        "ruleset": snapshot.get("ruleset", ""),
        "lifecycle": snapshot.get("lifecycle", ""),
        "snapshot_id": snapshot.get("snapshot_id", ""),
        "timestamp": snapshot.get("timestamp", ""),
        "registries_loaded": manifest.get("registries_loaded") or [],
        "facts_count": snapshot.get("facts_count", 0),
        "derived_count": len(derived_fields),
        "calc_count": len(calc_results),
        "triggered_count": len(snapshot.get("triggered_obligations") or []),
        "artifacts_count": len(snapshot.get("required_artifacts") or []),
        "assurances_count": len(snapshot.get("required_assurances") or []),
        # Facts / Derived
        "facts": facts_list,
        "derived": derived_list,
        # Calculators
        "calc_results": calc_results_display,
        # Obligations
        "triggered": snapshot.get("triggered_obligations") or [],
        "not_triggered": snapshot.get("not_triggered_obligations") or [],
        "obligation_details": obligation_details,
        # Artifacts / Assurances
        "artifacts": snapshot.get("required_artifacts") or [],
        "assurances": snapshot.get("required_assurances") or [],
        # Calculator drill-down
        "calculator_drilldown": calculator_drilldown,
        # Freeze / Version
        "frozen": frozen,
        "version": version,
    }


# ============================================================
# Public API
# ============================================================

def render_workbench(
    snapshot: dict,
    frozen: dict | None = None,
    version: dict | None = None,
    registries: dict | None = None,
) -> str:
    """
    把 RuntimeSnapshot dict 渲染成单文件 HTML。

    参数:
        snapshot: RuntimeSnapshot 的 dict 形式 (含 _original_facts 键)
        frozen: FrozenSubmissionInput 的 dict 形式 (可选)
        version: SubmissionPackageVersion 的 dict 形式 (可选)
        registries: 全部 v0 registries (可选, 用于 Rule Drill-down)

    返回:
        完整 HTML 字符串
    """
    env = Environment(loader=BaseLoader(), autoescape=True)
    template = env.from_string(_TEMPLATE)
    ctx = _build_context(snapshot, frozen, version, registries)
    return template.render(**ctx)


# ============================================================
# CLI (独立使用)
# ============================================================
def _cli() -> int:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="CPSWC v0 Workbench HTML Renderer")
    parser.add_argument("snapshot_json",
                        help="RuntimeSnapshot JSON 文件路径")
    parser.add_argument("-o", "--output", default="workbench.html",
                        help="输出 HTML 文件路径 (默认 workbench.html)")
    args = parser.parse_args()

    with open(args.snapshot_json, encoding="utf-8") as f:
        snapshot = json.load(f)

    html = render_workbench(snapshot)
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Workbench HTML written to: {args.output}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
