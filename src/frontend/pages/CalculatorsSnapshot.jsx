// ===================================================================
// F-9 计算器（快照模式专用，只读）
// ===================================================================
// 演示版写着「4 / 5 已计算，1 项未触发」。后端登记表里其实只有 3 个计算器，
// 本次全部执行了。这里只显示真实执行结果 + 登记元数据：
//
//   · status 照搬（ok / error / …），错误必须显示错误原文，不能空着过去
//   · 输入字段的**当前取值状态**一并显示 —— 输入是 placeholder stub 的话，
//     输出再精确也只是把假设算了一遍
//   · normative_basis_refs 显示出来，并标明这些依据 ID 没有登记条文原文

const CS_STATUS = {
  ok: { label: '已执行', tone: 'bg-slate-50 text-slate-600 border-slate-200' },
  error: { label: '执行失败', tone: 'bg-rose-50 text-rose-700 border-rose-200' },
  skipped: { label: '未执行', tone: 'bg-slate-100 text-slate-500 border-slate-200' },
};

function csFmtValue(v) {
  if (v === null || v === undefined) return '（无输出）';
  if (Array.isArray(v)) return v.length ? `${v.length} 条记录` : '空清单·未核实';
  if (typeof v === 'object') return '结构化记录';
  return String(v);
}

function CsInputRow({ ref_ }) {
  const F = window.CPSWC;
  const f = F.fact(ref_);
  const present = !!f && f.state === 'PRESENT';
  const demo = present && /placeholder|stub/i.test(f.note || '');
  const empty = present && !!f.is_empty_container;
  // 空容器和 placeholder 是同一类问题: 输出只是把一个未经核实的前提算了一遍
  const weak = demo || empty;
  return (
    <div className="flex items-start gap-2 px-2 py-1.5 rounded border bg-white border-slate-100">
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 mt-1.5 ${present ? (weak ? 'bg-amber-500' : 'bg-slate-400') : 'bg-rose-500'}`}/>
      <div className="min-w-0 flex-1">
        <div className="text-[11px] font-mono text-slate-500 break-all">{ref_}</div>
        <div className="text-[12px] text-slate-700">
          {f ? (f.canonical_name || ref_) : '该字段未登记'}
          <span className="ml-1.5 text-slate-500">{F.factText(ref_)}</span>
        </div>
        {demo && (
          <div className="text-[11px] text-amber-700 mt-0.5">
            该输入带演示/默认假设标记 —— 输出只是把这个假设算了一遍
          </div>
        )}
        {empty && !demo && (
          <div className="text-[11px] text-amber-700 mt-0.5">
            该输入是空清单，且未经核实 —— 输出只是把"没有记录"算了一遍，
            不构成"本项目不涉及"的证据
          </div>
        )}
      </div>
    </div>
  );
}

function CalculatorsSnapshotPage() {
  const { PAYLOAD } = window.CPSWC;
  const calcs = PAYLOAD.calculators || [];
  const [active, setActive] = useState(calcs[0] ? calcs[0].calculator_id : '');
  const cur = calcs.find(c => c.calculator_id === active) || calcs[0] || null;

  const okN = calcs.filter(c => c.status === 'ok').length;
  const errN = calcs.filter(c => c.status !== 'ok').length;

  return (
    <div>
      <PageHeader title="计算器" sub="本次实际执行的计算器 · 输入取值状态与依据同屏可见" icon="Calculator">
        <Chip tone="slate" icon="Calculator">已执行 {okN}</Chip>
        {errN > 0 && <Chip tone="amber" icon="TriangleAlert">失败 {errN}</Chip>}
      </PageHeader>

      {calcs.length === 0 ? (
        <div className="p-6 text-[13px] text-slate-500">本次快照没有执行任何计算器。</div>
      ) : (
        <div className="grid grid-cols-[280px_1fr] h-[calc(100vh-56px-65px)] min-w-[980px]">
          <aside className="border-r border-slate-200 bg-white overflow-y-auto">
            <div className="p-2.5">
              <div className="text-[10.5px] font-semibold text-slate-400 uppercase px-2 mb-1.5 tracking-wide">已执行</div>
              {calcs.map(c => {
                const act = c.calculator_id === active;
                const st = CS_STATUS[c.status] || CS_STATUS.skipped;
                return (
                  <button key={c.calculator_id} onClick={() => setActive(c.calculator_id)}
                    className={`w-full text-left px-2.5 py-2 rounded-md mb-0.5 transition-colors ${act ? 'bg-brand-50' : 'hover:bg-slate-50'}`}>
                    <div className={`text-[12.5px] ${act ? 'text-brand-700 font-medium' : 'text-slate-600'}`}>{c.canonical_name}</div>
                    <div className="mt-1 flex items-center gap-1.5 flex-wrap">
                      <span className={`text-[10px] px-1.5 py-px rounded border ${st.tone}`}>{st.label}</span>
                      {c.protection_level && <span className="text-[10px] text-slate-400">{c.protection_level}</span>}
                    </div>
                  </button>
                );
              })}
              <div className="mt-3 px-2 text-[11px] text-slate-400 leading-snug">
                登记表里共 {calcs.length} 个计算器，本次全部执行。
                这一页<b>只显示真正跑过的</b>。
              </div>
            </div>
          </aside>

          <section className="overflow-y-auto bg-[#eef1f5] p-5 space-y-4">
            {!cur ? null : (
              <>
                <Panel title={cur.canonical_name} sub={cur.calculator_id}>
                  <div className="p-4 space-y-3">
                    {cur.purpose && (
                      <div className="text-[12.5px] text-slate-600 whitespace-pre-line leading-relaxed">{cur.purpose}</div>
                    )}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-100 rounded-lg overflow-hidden border border-slate-100">
                      {[
                        ['输出字段', cur.output_field_id.replace(/^field\./, '')],
                        ['输出值', csFmtValue(cur.value) + (cur.unit && typeof cur.value !== 'object' ? ' ' + cur.unit : '')],
                        ['执行状态', (CS_STATUS[cur.status] || CS_STATUS.skipped).label],
                        ['来源已核验', cur.provenance_verified ? '是' : '否'],
                      ].map(([k, v]) => (
                        <div key={k} className="bg-white p-3">
                          <div className="text-[11px] text-slate-400">{k}</div>
                          <div className="mt-0.5 text-[13px] text-slate-800 font-medium break-all">{v}</div>
                        </div>
                      ))}
                    </div>

                    {cur.status !== 'ok' && (
                      <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-[12px] text-rose-800">
                        <b>执行失败。</b>{cur.error_message || '（登记表未给出错误原文）'}
                        <div className="mt-1 text-rose-700">
                          该计算器没有产出任何可用结果，依赖它的章节与表格同样没有依据。
                        </div>
                      </div>
                    )}

                    <div className="rounded-md bg-slate-50 border border-slate-200 px-3 py-2 text-[11.5px] text-slate-600">
                      执行成功<b>不等于结果可信</b>：计算器只保证按公式算对，
                      输入是否属实、口径是否正确都不在它的判断范围内。
                    </div>
                  </div>
                </Panel>

                <Panel title="输入字段" sub={`${cur.input_refs.length} 项 · 当前取值与状态`}>
                  <div className="p-3 space-y-1.5">
                    {cur.input_refs.length === 0
                      ? <div className="text-[12px] text-slate-500">登记表未声明输入字段。</div>
                      : cur.input_refs.map(r => <CsInputRow key={r} ref_={r}/>)}
                  </div>
                </Panel>

                {cur.formula && (
                  <Panel title="公式">
                    <pre className="m-3 p-3 text-[11.5px] font-mono text-slate-700 bg-slate-50 border border-slate-200 rounded whitespace-pre-wrap break-all">
                      {cur.formula}
                    </pre>
                  </Panel>
                )}

                <Panel title="规范依据" sub={`${cur.normative_basis_refs.length} 项`}>
                  <div className="p-3 space-y-1.5">
                    {cur.normative_basis_refs.length === 0
                      ? <div className="text-[12px] text-slate-500">登记表未声明规范依据。</div>
                      : cur.normative_basis_refs.map(r => (
                        <div key={r} className="text-[11px] font-mono break-all rounded px-2 py-1.5 bg-white border border-slate-200 text-slate-600">
                          {r}
                          <div className="font-sans text-[10.5px] text-slate-400 mt-0.5">
                            该依据 ID 没有登记标题或条文原文
                          </div>
                        </div>
                      ))}
                  </div>
                </Panel>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { CalculatorsSnapshotPage });
