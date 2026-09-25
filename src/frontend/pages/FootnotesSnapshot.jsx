// ===================================================================
// F-10 注脚与依据库（快照模式专用，只读）
// ===================================================================
// 演示版这一页是一个能增删改的注脚编辑器。系统没有注脚功能，一条也存不下。
//
// 改成一件真能做、而且非做不可的事：**清点系统引用过的全部依据 ID**。
//
// 清点结果不好看，但它是真的：系统在义务、计算器、保证事项和正文里引用了
// 几十个 `rule.*` 依据 ID，而**这些 ID 在任何注册表里都没有登记标题或条文原文**。
// 也就是说，报告里每一句"依据 XXX"目前都指向一个空壳。
//
// 这正是该让人看见的东西 —— 它决定了正文的引用现在能不能当真。

function FsCitedBadge({ kind }) {
  const map = {
    obligation: ['义务', 'bg-brand-50 text-brand-700 border-brand-200'],
    calculator: ['计算器', 'bg-teal-50 text-teal-700 border-teal-200'],
    assurance: ['保证事项', 'bg-amber-50 text-amber-700 border-amber-200'],
    narrative: ['正文', 'bg-slate-50 text-slate-600 border-slate-200'],
  };
  const [label, tone] = map[kind] || [kind, 'bg-slate-50 text-slate-600 border-slate-200'];
  return <span className={`text-[10px] px-1.5 py-px rounded border ${tone}`}>{label}</span>;
}

function FootnotesSnapshotPage() {
  const { PAYLOAD } = window.CPSWC;
  const refs = PAYLOAD.rule_refs || [];
  const [active, setActive] = useState(refs[0] ? refs[0].rule_id : '');
  const [kind, setKind] = useState('all');

  const shown = kind === 'all'
    ? refs
    : refs.filter(r => r.cited_by.some(c => c.kind === kind));
  const cur = refs.find(r => r.rule_id === active) || null;

  const registered = refs.filter(r => r.title_registered).length;
  const byKind = {};
  refs.forEach(r => r.cited_by.forEach(c => { byKind[c.kind] = (byKind[c.kind] || 0) + 1; }));

  return (
    <div>
      <PageHeader title="注脚与依据库" sub="系统引用过的依据清点 · 引用方可追溯" icon="BookMarked">
        <Chip tone="slate" icon="Quote">依据 ID {refs.length} 个</Chip>
        <Chip tone={registered === refs.length ? 'slate' : 'amber'} icon="TriangleAlert">
          已登记标题 {registered} / {refs.length}
        </Chip>
      </PageHeader>

      <div className="p-5 space-y-4 max-w-[1400px]">
        {registered < refs.length && (
          <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-[12.5px] text-amber-900">
            <div className="font-semibold flex items-center gap-1.5">
              <Icon name="TriangleAlert" size={15}/>
              {refs.length - registered} 个依据 ID 没有登记标题或条文原文
            </div>
            <div className="mt-1 leading-snug">
              系统在义务判定、计算器和正文里引用了这些 ID，但<b>没有任何注册表记录它们指向哪部规范的哪一条</b>。
              这意味着报告里的"依据 XXX"目前只是一个符号，<b>无法向审查人员出示条文</b>，
              也无法核对引用是否正确。注脚功能（编号、插入正文、导出）同样<b>未实现</b>。
            </div>
          </div>
        )}

        <div className="flex items-center gap-1.5 flex-wrap">
          {[['all', `全部 ${refs.length}`],
            ['obligation', `义务 ${byKind.obligation || 0}`],
            ['calculator', `计算器 ${byKind.calculator || 0}`],
            ['assurance', `保证事项 ${byKind.assurance || 0}`],
            ['narrative', `正文 ${byKind.narrative || 0}`]].map(([k, label]) => (
            <button key={k} onClick={() => setKind(k)}
              className={`text-[11.5px] px-2.5 py-1 rounded-md border transition-colors
                ${kind === k ? 'bg-brand-600 text-white border-brand-600' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
              {label}
            </button>
          ))}
          <span className="text-[11px] text-slate-400 ml-1">
            计数按「引用次数」统计，同一依据被多处引用会重复计入
          </span>
        </div>

        <div className="grid grid-cols-[1fr_400px] gap-4 items-start">
          <Panel title="依据引用清点" sub={`${shown.length} 个 ID · 按引用次数排序`}>
            <div className="divide-y divide-slate-50 max-h-[calc(100vh-330px)] overflow-y-auto">
              {shown.map(r => (
                <button key={r.rule_id} onClick={() => setActive(r.rule_id)}
                  className={`w-full text-left px-4 py-2.5 transition-colors ${r.rule_id === active ? 'bg-brand-50/70' : 'hover:bg-slate-50'}`}>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[12px] font-mono text-slate-700 break-all">{r.rule_id}</span>
                    <span className="text-[11px] text-slate-400 ml-auto whitespace-nowrap">被引用 {r.citation_count} 次</span>
                  </div>
                  <div className="mt-1 flex items-center gap-1.5 flex-wrap">
                    {[...new Set(r.cited_by.map(c => c.kind))].map(k => <FsCitedBadge key={k} kind={k}/>)}
                    {!r.title_registered && <span className="text-[10.5px] text-amber-600">无标题登记</span>}
                  </div>
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="引用方" sub={cur ? cur.rule_id : '未选择'}>
            {!cur ? (
              <div className="p-4 text-[12px] text-slate-500">在左侧选一个依据 ID。</div>
            ) : (
              <div className="p-4 space-y-3">
                <div className="rounded-md bg-slate-50 border border-slate-200 px-3 py-2">
                  <div className="text-[11.5px] text-slate-500">标题 / 条文</div>
                  <div className="text-[12.5px] text-amber-700 mt-0.5">
                    {cur.title_registered ? cur.title : '未登记 —— 系统不知道这个 ID 指向哪部规范的哪一条'}
                  </div>
                </div>
                <div>
                  <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">
                    引用位置 · {cur.citation_count}
                  </div>
                  <div className="space-y-1 max-h-[calc(100vh-460px)] overflow-y-auto">
                    {cur.cited_by.map((c, i) => (
                      <div key={i} className="flex items-start gap-2 px-2 py-1.5 rounded border border-slate-100 bg-white">
                        <FsCitedBadge kind={c.kind}/>
                        <span className="text-[11px] font-mono text-slate-600 break-all flex-1">{c.ref}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </Panel>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-[12px] text-slate-500">
          <b>这一页不是注脚编辑器。</b>系统目前没有注脚能力：不能编号、不能插入正文、
          不能随报告导出，也没有存储。演示版里的那套增删改界面对应的功能一项也不存在，
          所以在快照模式下不再提供。
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { FootnotesSnapshotPage });
