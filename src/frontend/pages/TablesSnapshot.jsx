// ===================================================================
// F-7 表格中心（快照模式专用，只读）
// ===================================================================
// 演示版列了 12 张表，其中 9 张标成 LIVE。后端真正实现了表投影的只有 8 张，
// 而且其中一张（投资估算总表）返回的是 RENDER_WITH_PLACEHOLDER —— 有结构没值。
//
// 这里只显示 payload.tables 里实际有的东西：
//   · 表格四态照搬后端的 render_policy，界面不做推断；
//   · placeholder 表如实显示为"结构已就位、数值缺失"，不画成一张填满的表；
//   · 演示版里那些后端根本没有的表（年度投资表、附件目录表、监测点位表…）
//     单列一栏「后端未实现」，而不是悄悄消失 —— 消失会让人以为不需要这些表。

const TS_POLICY = {
  render_with_values: { label: '有值', tone: 'bg-slate-50 text-slate-600 border-slate-200' },
  render_with_placeholder: { label: '结构占位·缺值', tone: 'bg-amber-50 text-amber-700 border-amber-200' },
  render_not_applicable: { label: '本项目不适用', tone: 'bg-slate-100 text-slate-500 border-slate-200' },
  skip_render: { label: '不渲染', tone: 'bg-slate-100 text-slate-500 border-slate-200' },
  PROJECTION_FAILED: { label: '投影失败', tone: 'bg-rose-50 text-rose-700 border-rose-200' },
};

// 演示版列过、后端却没有投影的表。列出来是为了让缺口可见。
const TS_NOT_IMPLEMENTED = [
  '年度投资表', '附件目录表', '监测点位表', '补偿费计算表', '防治措施投资表',
];

function tsFmt(v, fmt) {
  if (v === null || v === undefined || v === '') return '—';
  if (typeof v !== 'number') return String(v);
  if (fmt === 'int') return String(Math.round(v));
  if (fmt === '1f') return v.toFixed(1);
  if (fmt === '2f') return v.toFixed(2);
  return String(v);
}

function TsTable({ t }) {
  const cols = t.columns || [];
  const placeholder = t.render_policy === 'render_with_placeholder';
  if (!cols.length) {
    return <div className="text-[12.5px] text-rose-700">该表没有列定义，无法渲染。</div>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[12px] border-collapse">
        <thead>
          <tr className="bg-slate-100">
            {cols.map(c => (
              <th key={c.key} className="border border-slate-300 px-3 py-2 text-left font-medium text-slate-600 whitespace-nowrap">
                {c.header}{c.unit ? ` (${c.unit})` : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {(t.rows || []).map((r, i) => (
            <tr key={i} className={placeholder ? 'text-slate-500' : ''}>
              {cols.map(c => (
                <td key={c.key} className={`border border-slate-300 px-3 py-1.5 ${c.align === 'right' ? 'text-right tabular' : c.align === 'center' ? 'text-center' : ''}`}>
                  {tsFmt(r[c.key], c.fmt)}
                </td>
              ))}
            </tr>
          ))}
          {t.has_total_row && t.total_row && (
            <tr className="bg-slate-50 font-semibold">
              {cols.map(c => (
                <td key={c.key} className={`border border-slate-300 px-3 py-1.5 ${c.align === 'right' ? 'text-right tabular' : c.align === 'center' ? 'text-center' : ''}`}>
                  {tsFmt(t.total_row[c.key], c.fmt)}
                </td>
              ))}
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function TablesSnapshotPage() {
  const { PAYLOAD, PROJECT, SIX_RATES } = window.CPSWC;
  const tables = PAYLOAD.tables || [];
  const [active, setActive] = useState(tables[0] ? tables[0].table_id : '');
  const cur = tables.find(t => t.table_id === active) || tables[0] || null;
  const pol = cur ? (TS_POLICY[cur.render_policy] || TS_POLICY.skip_render) : null;
  const isSixRate = cur && cur.table_id === 'art.table.six_indicator_review';

  const valueCount = tables.filter(t => t.render_policy === 'render_with_values').length;
  const placeholderCount = tables.filter(t => t.render_policy === 'render_with_placeholder').length;

  return (
    <div>
      <PageHeader title="表格中心" sub="后端表投影的直出结果 · 四态照搬，不做推断" icon="Table2">
        <Chip tone="slate" icon="Table2">有值 {valueCount} 张</Chip>
        {placeholderCount > 0 && <Chip tone="amber" icon="LayoutTemplate">结构占位 {placeholderCount} 张</Chip>}
        <button disabled title="正式表格导出未实现"
          className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md border border-slate-200 bg-white text-slate-400 cursor-not-allowed">
          <Icon name="FileDown" size={14}/>导出正式表格（未实现）
        </button>
      </PageHeader>

      <div className="grid grid-cols-[260px_1fr_320px] h-[calc(100vh-56px-65px)] min-w-[1180px]">
        {/* 左：真实表清单 */}
        <aside className="border-r border-slate-200 bg-white overflow-y-auto">
          <div className="p-2.5">
            <div className="text-[10.5px] font-semibold text-slate-400 uppercase px-2 mb-1.5 tracking-wide">已实现的表投影</div>
            {tables.map(t => {
              const act = t.table_id === active;
              const p = TS_POLICY[t.render_policy] || TS_POLICY.skip_render;
              return (
                <button key={t.table_id} onClick={() => setActive(t.table_id)}
                  className={`w-full text-left px-2.5 py-2 rounded-md mb-0.5 transition-colors ${act ? 'bg-brand-50' : 'hover:bg-slate-50'}`}>
                  <div className={`text-[12.5px] ${act ? 'text-brand-700 font-medium' : 'text-slate-600'}`}>{t.title}</div>
                  <div className="mt-1 flex items-center gap-1.5 flex-wrap">
                    <span className={`text-[10px] px-1.5 py-px rounded border ${p.tone}`}>{p.label}</span>
                    <span className="text-[10px] text-slate-400">{(t.rows || []).length} 行</span>
                    {(t.warnings || []).length > 0 &&
                      <span className="text-[10px] text-amber-600">{t.warnings.length} 条提示</span>}
                  </div>
                </button>
              );
            })}

            <div className="text-[10.5px] font-semibold text-slate-400 uppercase px-2 mt-4 mb-1.5 tracking-wide">后端未实现</div>
            {TS_NOT_IMPLEMENTED.map(n => (
              <div key={n} className="px-2.5 py-2 rounded-md mb-0.5 opacity-60">
                <div className="text-[12.5px] text-slate-500 line-through decoration-slate-300">{n}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">没有表投影，本次不产出</div>
              </div>
            ))}
          </div>
        </aside>

        {/* 中：表预览 */}
        <section className="overflow-y-auto bg-[#dfe3ea] p-6">
          {!cur ? (
            <div className="bg-white rounded-lg border border-slate-200 p-8 text-[13px] text-slate-500">
              本次快照没有产出任何表格。
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <h2 className="text-[14px] font-semibold text-slate-700">{cur.title}</h2>
                  <span className={`text-[11px] px-2 py-0.5 rounded border ${pol.tone}`}>{pol.label}</span>
                </div>
                <span className="text-[11px] text-slate-500">快照结果，未经复核，不可直接用于报批</span>
              </div>

              {cur.render_policy === 'render_with_placeholder' && (
                <div className="mb-3 flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-[12px] text-amber-800">
                  <Icon name="LayoutTemplate" size={14} className="shrink-0 mt-0.5"/>
                  <span>
                    <b>结构已就位，数值缺失。</b>后端表投影返回 RENDER_WITH_PLACEHOLDER —— 行骨架是固定的，
                    缺的值以「—」显示。<b>不要把它当成一张已经算好的表。</b>
                  </span>
                </div>
              )}
              {cur.render_policy === 'PROJECTION_FAILED' && (
                <div className="mb-3 flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-[12px] text-rose-800">
                  <Icon name="OctagonX" size={14} className="shrink-0 mt-0.5"/>
                  <span><b>表投影执行失败。</b>本表没有任何可信内容。</span>
                </div>
              )}

              <div className="bg-white rounded-lg border border-slate-200 a4-shadow p-6">
                <div className="text-center mb-4">
                  <div className="text-[14px] font-semibold text-slate-800 font-serif">{cur.title}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{PROJECT.name}</div>
                </div>
                <TsTable t={cur}/>
                {cur.footnote && (
                  <div className="mt-3 text-[11px] text-slate-500 font-serif">注：{cur.footnote}</div>
                )}
              </div>

              {isSixRate && (
                <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-[12px] text-amber-800">
                  <b>「实现值」一列是候选值，不是已确认的效果。</b>
                  {SIX_RATES.map(r => r.result).filter((v, i, a) => a.indexOf(v) === i).join('；')}
                  —— 效果来源确认前，不构成达标判断。
                </div>
              )}
            </>
          )}
        </section>

        {/* 右：表来源与诊断 */}
        <aside className="border-l border-slate-200 bg-white overflow-y-auto">
          <div className="px-4 py-3 border-b border-slate-100">
            <div className="text-[12px] font-semibold text-slate-700 flex items-center gap-1.5">
              <Icon name="GitBranch" size={14} className="text-brand-600"/>表格来源与诊断
            </div>
          </div>
          {!cur ? null : (
            <div className="p-4 space-y-4">
              <div>
                <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">标识</div>
                <div className="space-y-1 text-[11px] font-mono text-slate-600 break-all">
                  <div className="bg-slate-50 border border-slate-100 rounded px-2 py-1">{cur.table_id}</div>
                  {cur.section_id
                    ? <div className="bg-slate-50 border border-slate-100 rounded px-2 py-1">嵌入 {cur.section_id}</div>
                    : <div className="text-slate-400 px-2">未登记嵌入章节</div>}
                </div>
              </div>

              <div>
                <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">
                  投影提示 · {(cur.warnings || []).length}
                </div>
                {(cur.warnings || []).length === 0 ? (
                  <div className="text-[11.5px] text-slate-500">
                    本表投影没有报出提示。注意：这只说明<b>投影内部的检查</b>没报警，
                    不等于表中数值已经复核。
                  </div>
                ) : (
                  <div className="space-y-1">
                    {cur.warnings.map((w, i) => (
                      <div key={i} className="text-[11.5px] px-2 py-1 rounded bg-amber-50 border border-amber-200 text-amber-800">{w}</div>
                    ))}
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-slate-100">
                <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">导出位置</div>
                <div className="text-[12px] text-slate-500">
                  正式表格导出<b>未实现</b>，本表目前只能在此查看。
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

Object.assign(window, { TablesSnapshotPage, TsTable });
