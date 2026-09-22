// ===================================================================
// F-2 真实收资清单（待甲方提供资料清单）
//
// 数据来自后端 intake_issues（cpswc/intake_issues.py）。界面**不做二次判断**：
// 分类、严重度、影响范围全部照搬后端结论；后端解析不出影响范围时，
// 如实显示"影响范围尚未建立"，不得用"可能影响全部章节"之类的话填充。
//
// 演示模式下不产出收资清单 —— 收资清单是对甲方的正式索要依据，
// 用 mock 生成一份等于凭空向客户要东西。
// ===================================================================
const SEV_STYLE = {
  BLOCK: ['border-rose-200 bg-rose-50', 'bg-rose-600', '阻断'],
  WARN: ['border-amber-200 bg-amber-50', 'bg-amber-500', '提醒'],
  INFO: ['border-slate-200 bg-white', 'bg-slate-400', '提示'],
};

function IntakeIssueCard({ issue }) {
  const [box, dot, sevCn] = SEV_STYLE[issue.severity] || SEV_STYLE.INFO;
  const impactRefs = [].concat(
    issue.affected_section_refs || [], issue.affected_artifact_refs || [],
    issue.affected_projection_refs || []);
  return (
    <div className={`rounded-md border p-2.5 ${box}`}>
      <div className="flex items-start gap-2">
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 mt-1.5 ${dot}`}/>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10.5px] font-semibold px-1.5 py-0.5 rounded bg-white/70 border border-slate-200 text-slate-600">{issue.category_label}</span>
            <span className="text-[10.5px] text-slate-500">{sevCn}</span>
            <span className="font-mono text-[10px] text-slate-400">{issue.source_code}</span>
            <span className="font-mono text-[10px] text-slate-300 ml-auto">{issue.issue_id}</span>
          </div>
          {(issue.field_names || []).length > 0 && (
            <div className="text-[12px] text-slate-700 mt-1">{issue.field_names.join('、')}</div>
          )}
          <div className="text-[11.5px] text-slate-600 mt-1 break-words">{issue.message}</div>
          {issue.remediation && (
            <div className="text-[11px] text-brand-600 mt-1">建议：{issue.remediation}</div>
          )}
          <div className="text-[11px] text-slate-400 mt-1">
            {issue.impact_known ? `影响：${impactRefs.join('、')}` : '影响范围尚未建立'}
          </div>
        </div>
      </div>
    </div>
  );
}

// 导出清单。硬性要求：水印 + 项目名 + 生成时间 + generation_input_hash + 分级，
// 外加"影响范围未建立"的说明 —— 这份东西会被发给甲方，不能看着像正式附件。
function exportIntakeList() {
  const { INTAKE_ISSUES, INTAKE_SUMMARY, PROJECT, PAYLOAD } = window.CPSWC;
  const hash = (PAYLOAD && PAYLOAD.hashes && PAYLOAD.hashes.generation_input_hash) || '(未知)';
  const gen = (PAYLOAD && PAYLOAD.generated_at) || '(未知)';
  const s = INTAKE_SUMMARY || { total: 0, by_severity: {}, impact_unknown_count: 0 };
  const esc = (v) => String(v == null ? '' : v)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const rows = INTAKE_ISSUES.map((i, n) => {
    const impact = [].concat(i.affected_section_refs || [], i.affected_artifact_refs || [],
      i.affected_projection_refs || []).join('、');
    const sev = i.severity === 'BLOCK' ? '阻断' : i.severity === 'WARN' ? '提醒' : '提示';
    return `<tr><td>${n + 1}</td><td>${esc(sev)}</td><td>${esc(i.category_label)}</td>`
      + `<td>${esc((i.field_names || []).join('、'))}</td><td>${esc(i.message)}</td>`
      + `<td>${esc(i.remediation)}</td>`
      + `<td>${i.impact_known ? esc(impact) : '影响范围尚未建立'}</td></tr>`;
  }).join('');

  const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>待甲方提供资料清单 — ${esc(PROJECT.name)}</title>
<style>
 body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:32px;color:#1e293b}
 .wm{position:fixed;inset:0;pointer-events:none;z-index:0}
 .wm span{position:absolute;top:42%;left:50%;transform:translate(-50%,-50%) rotate(-24deg);
   font-size:52px;font-weight:800;color:rgba(220,38,38,.12);white-space:nowrap}
 .c{position:relative;z-index:1}
 h1{font-size:19px;margin:0 0 4px}
 .notice{border:1px solid #fecaca;background:#fef2f2;color:#991b1b;padding:9px 12px;
   border-radius:6px;font-size:12.5px;margin:12px 0}
 dl{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:12px;margin:12px 0}
 dt{color:#64748b} dd{margin:0;font-family:ui-monospace,Menlo,monospace;word-break:break-all}
 table{border-collapse:collapse;width:100%;font-size:11.5px;margin-top:10px}
 th,td{border:1px solid #cbd5e1;padding:5px 7px;vertical-align:top;text-align:left}
 th{background:#f1f5f9} tfoot td{background:#f8fafc;color:#64748b}
</style></head><body>
<div class="wm"><span>工作草稿 · 非正式报告附件</span></div>
<div class="c">
<h1>待甲方提供资料清单</h1>
<div class="notice"><b>工作草稿，非正式报告附件。</b>
 本清单由系统按本次生成快照自动导出，反映截至生成时刻系统发现的数据缺口；
 不构成水土保持方案报告的任何正式组成部分，也不代表方案已通过任何审查。</div>
<dl>
 <dt>项目名称</dt><dd>${esc(PROJECT.name)}</dd>
 <dt>项目编码</dt><dd>${esc(PROJECT.code)}</dd>
 <dt>生成时间</dt><dd>${esc(gen)}</dd>
 <dt>generation_input_hash</dt><dd>${esc(hash)}</dd>
 <dt>条目统计</dt><dd>共 ${s.total} 项：阻断 ${s.by_severity.BLOCK || 0} · 提醒 ${s.by_severity.WARN || 0} · 提示 ${s.by_severity.INFO || 0}</dd>
 <dt>影响范围未建立</dt><dd>${s.impact_unknown_count} 项</dd>
</dl>
<p style="font-size:11.5px;color:#64748b">
 「阻断」= 缺此项无法通过导出前检查；「提醒」= 不阻断导出但会削弱依据。
 标注「影响范围尚未建立」的条目，表示系统尚未登记该数据与章节／图件的对应关系，
 <b>不代表它不影响任何章节</b>。</p>
<table><thead><tr><th>#</th><th>分级</th><th>分类</th><th>涉及数据</th><th>问题</th><th>建议</th><th>影响范围</th></tr></thead>
<tbody>${rows}</tbody>
<tfoot><tr><td colspan="7">本清单随输入变化而变化；甲方补充资料后需重新生成，hash 会随之改变。</td></tr></tfoot>
</table></div></body></html>`;

  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([html], { type: 'text/html;charset=utf-8' }));
  a.download = `待甲方提供资料清单_${PROJECT.code || 'project'}_${String(hash).slice(0, 8)}.html`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}

// 按分类分组后的完整清单面板。
function IntakeIssueList() {
  const { INTAKE_ISSUES, INTAKE_SUMMARY, IS_SNAPSHOT } = window.CPSWC;

  if (!IS_SNAPSHOT) {
    return (
      <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-[11.5px] text-slate-500">
        演示模式不产出收资清单。收资清单是向甲方索要资料的依据，
        必须基于真实项目快照生成。
      </div>
    );
  }
  if (!INTAKE_ISSUES.length) {
    return (
      <div className="rounded-md border border-slate-200 bg-white p-3 text-[11.5px] text-slate-500">
        本次快照未产出收资条目。注意：这只说明系统<b>已登记的检查项</b>没有发现缺口，
        不等于资料齐全 —— 未实现的内容要求不会在此出现。
      </div>
    );
  }

  const s = INTAKE_SUMMARY || { by_severity: {}, impact_unknown_count: 0 };
  const groups = [];
  INTAKE_ISSUES.forEach((i) => {
    let g = groups.find((x) => x.key === i.category);
    if (!g) { g = { key: i.category, label: i.category_label, items: [] }; groups.push(g); }
    g.items.push(i);
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap text-[11.5px]">
        <span className="px-2 py-1 rounded bg-rose-50 border border-rose-200 text-rose-700">
          阻断 {s.by_severity.BLOCK || 0}
        </span>
        <span className="px-2 py-1 rounded bg-amber-50 border border-amber-200 text-amber-700">
          提醒 {s.by_severity.WARN || 0}
        </span>
        <span className="px-2 py-1 rounded bg-slate-50 border border-slate-200 text-slate-600">
          提示 {s.by_severity.INFO || 0}
        </span>
        {s.impact_unknown_count > 0 && (
          <span className="px-2 py-1 rounded bg-slate-50 border border-slate-200 text-slate-500">
            影响范围尚未建立 {s.impact_unknown_count}
          </span>
        )}
        <button onClick={exportIntakeList}
          className="ml-auto text-[11.5px] px-2.5 py-1.5 rounded-md bg-brand-600 text-white
            hover:bg-brand-700 inline-flex items-center gap-1 whitespace-nowrap">
          <Icon name="Download" size={13}/>导出待甲方提供资料清单
        </button>
      </div>
      <div className="text-[11px] text-slate-400">
        导出件带「工作草稿，非正式报告附件」水印，并附项目名、生成时间与
        generation_input_hash；甲方补充资料后需重新生成。
      </div>
      {groups.map((g) => (
        <div key={g.key}>
          <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">
            {g.label}（{g.items.length}）
          </div>
          <div className="space-y-1.5">
            {g.items.map((i) => <IntakeIssueCard key={i.issue_id} issue={i}/>)}
          </div>
        </div>
      ))}
    </div>
  );
}

Object.assign(window, { IntakeIssueCard, IntakeIssueList, exportIntakeList });
