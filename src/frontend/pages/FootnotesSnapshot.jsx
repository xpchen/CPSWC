// ===================================================================
// F-10 注脚与依据库（快照模式专用，只读）
// ===================================================================
// 演示版这一页是一个能增删改的注脚编辑器。系统没有注脚功能，一条也存不下。
//
// 改成一件真能做、而且非做不可的事：**清点系统引用过的全部依据 ID**，
// 并显示每一条核到了什么程度。
//
// 三态一个都不许含糊（口径来自 RuleRegistry_v0，界面不做二次判定）：
//   已核原文   条文原文已从本地原件抽取并核对，可直接向审查人员出示
//   已定位     知道是哪部文件（可能到章/条），但没抓原文
//   未登记     系统不知道这个 ID 指向哪一条 —— 报告里那句"依据 XXX"是空壳
//
// **不给单一"依据覆盖率"百分比**：压成一个数会立刻抹掉最要紧的区别 ——
// "定位到文件了"和"条文核对过了"完全是两回事。

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

const FS_STATE = {
  VERIFIED_TEXT: ['已核原文', 'bg-slate-50 text-slate-700 border-slate-300'],
  DECLARED: ['已定位·未抓原文', 'bg-amber-50 text-amber-700 border-amber-200'],
  UNREGISTERED: ['未登记', 'bg-rose-50 text-rose-700 border-rose-200'],
};

function FsStateBadge({ r }) {
  const [label, tone] = FS_STATE[r.verification_status] || FS_STATE.UNREGISTERED;
  return <span className={`text-[10px] px-1.5 py-px rounded border whitespace-nowrap ${tone}`}>{label}</span>;
}

function FootnotesSnapshotPage() {
  const { PAYLOAD } = window.CPSWC;
  const refs = PAYLOAD.rule_refs || [];
  const cov = PAYLOAD.rule_coverage || {
    cited_total: refs.length, text_verified: 0, declared: 0,
    unregistered: refs.length, clause_located: 0, defects: [],
    unregistered_namespaces: [],
  };
  const [active, setActive] = useState(refs[0] ? refs[0].rule_id : '');
  const [kind, setKind] = useState('all');

  const shown = kind === 'all' ? refs
    : ['VERIFIED_TEXT', 'DECLARED', 'UNREGISTERED'].includes(kind)
      ? refs.filter(r => r.verification_status === kind)
      : refs.filter(r => r.cited_by.some(c => c.kind === kind));
  const cur = refs.find(r => r.rule_id === active) || null;

  const byKind = {};
  refs.forEach(r => r.cited_by.forEach(c => { byKind[c.kind] = (byKind[c.kind] || 0) + 1; }));

  return (
    <div>
      <PageHeader title="注脚与依据库" sub="依据清点 · 每条核到什么程度 · 引用方可追溯" icon="BookMarked">
        <Chip tone="slate" icon="Quote">依据 ID {cov.cited_total} 个</Chip>
        <Chip tone="slate" icon="ShieldCheck">已核原文 {cov.text_verified}</Chip>
        <Chip tone="amber" icon="FileSearch">已定位 {cov.declared}</Chip>
        <Chip tone={cov.unregistered ? 'rose' : 'slate'} icon="FileX2">未登记 {cov.unregistered}</Chip>
      </PageHeader>

      <div className="p-5 space-y-4 max-w-[1400px]">
        {/* **不给单一覆盖率百分比** —— 三档分开摆, 压成一个数会抹掉
            "定位到文件了"和"条文核对过了"的区别 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-200 rounded-lg overflow-hidden border border-slate-200">
          {[
            ['已核原文', cov.text_verified, '条文可直接向审查人员出示', 'text-slate-800'],
            ['已定位·未抓原文', cov.declared, '知道出自哪份文件，条文没抓', 'text-amber-700'],
            ['未登记', cov.unregistered, '不知道指向哪一条 —— 引用是空壳', 'text-rose-700'],
            ['已定位到条款', cov.clause_located, '其余只到文件级', 'text-slate-600'],
          ].map(([k, v, note, tone]) => (
            <div key={k} className="bg-white p-3.5">
              <div className="text-[11px] text-slate-400">{k}</div>
              <div className={`mt-0.5 text-[22px] font-bold tabular ${tone}`}>{v}</div>
              <div className="text-[11px] text-slate-400 mt-0.5 leading-snug">{note}</div>
            </div>
          ))}
        </div>

        {cov.unregistered > 0 && (
          <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-3 text-[12.5px] text-rose-900">
            <div className="font-semibold flex items-center gap-1.5">
              <Icon name="TriangleAlert" size={15}/>
              {cov.unregistered} 个依据 ID 未登记，系统不知道它们指向哪一条
            </div>
            <div className="mt-1 leading-snug">
              报告里对应的"依据 XXX"目前只是一个符号，<b>无法向审查人员出示条文</b>，
              也无法核对引用是否正确。
            </div>
            {(cov.unregistered_namespaces || []).map(ns => (
              <div key={ns.namespace} className="mt-2 rounded bg-white/70 border border-rose-200 px-2.5 py-2 text-[11.5px]">
                <span className="font-mono">{ns.namespace}.*</span> · {ns.count_at_registry_time} 个 ——
                {ns.reason}
                <div className="text-rose-700 mt-0.5">下一步：{ns.next_step}</div>
              </div>
            ))}
          </div>
        )}

        {(cov.defects || []).length > 0 && (
          <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-[12.5px] text-amber-900">
            <div className="font-semibold flex items-center gap-1.5">
              <Icon name="GitCompareArrows" size={15}/>
              {cov.defects.length} 条依据引用有缺陷
            </div>
            {cov.defects.map(d => (
              <div key={d.rule_id} className="mt-2 rounded bg-white/70 border border-amber-200 px-2.5 py-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11.5px]">{d.rule_id}</span>
                  <span className="text-[10px] px-1.5 py-px rounded border bg-amber-100 border-amber-300">{d.defect}</span>
                </div>
                <div className="text-[11.5px] mt-0.5 whitespace-pre-line leading-snug">{d.defect_note}</div>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-center gap-1.5 flex-wrap">
          {[['all', `全部 ${refs.length}`],
            ['VERIFIED_TEXT', `已核原文 ${cov.text_verified}`],
            ['DECLARED', `已定位 ${cov.declared}`],
            ['UNREGISTERED', `未登记 ${cov.unregistered}`],
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
            前四项按 ID 计数；按引用方筛选时同一依据被多处引用会重复计入
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
                    <FsStateBadge r={r}/>
                    {[...new Set(r.cited_by.map(c => c.kind))].map(k => <FsCitedBadge key={k} kind={k}/>)}
                    {r.defect && <span className="text-[10px] px-1.5 py-px rounded border bg-amber-50 text-amber-700 border-amber-200">{r.defect}</span>}
                  </div>
                  {r.document_number && (
                    <div className="mt-0.5 text-[11px] text-slate-500">
                      {r.document_number}{r.clause_ref ? ` · ${r.clause_ref}` : ''}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="依据详情" sub={cur ? cur.rule_id : '未选择'}>
            {!cur ? (
              <div className="p-4 text-[12px] text-slate-500">在左侧选一个依据 ID。</div>
            ) : (
              <div className="p-4 space-y-3">
                {!cur.registered ? (
                  <div className="rounded-md bg-rose-50 border border-rose-200 px-3 py-2 text-[12px] text-rose-800">
                    <b>未登记。</b>系统不知道这个 ID 指向哪部规范的哪一条。
                    报告里引用它的地方目前<b>拿不出条文</b>。
                  </div>
                ) : (
                  <>
                    <div className="rounded-md bg-slate-50 border border-slate-200 px-3 py-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <FsStateBadge r={cur}/>
                        {cur.authority_class && (
                          <span className="text-[10.5px] text-slate-500">{cur.authority_class}</span>
                        )}
                      </div>
                      <div className="text-[12.5px] text-slate-800 mt-1 leading-snug">{cur.document_title}</div>
                      <div className="text-[11.5px] text-slate-500 mt-0.5">{cur.document_number}</div>
                      {cur.issuing_authority && (
                        <div className="text-[11px] text-slate-400 mt-0.5">{cur.issuing_authority}</div>
                      )}
                      {cur.effective_from && (
                        <div className="text-[11px] text-slate-400">施行 {cur.effective_from}</div>
                      )}
                    </div>

                    <div>
                      <div className="text-[11.5px] font-semibold text-slate-500 mb-1">条款</div>
                      <div className="text-[12.5px] text-slate-700">
                        {cur.clause_ref || <span className="text-amber-700">未定位到具体条款，仅到文件级</span>}
                      </div>
                    </div>

                    <div>
                      <div className="text-[11.5px] font-semibold text-slate-500 mb-1">条文原文</div>
                      {cur.quoted_text ? (
                        <pre className="text-[12px] text-slate-700 bg-white border border-slate-200 rounded px-3 py-2 whitespace-pre-wrap font-serif leading-relaxed">
{cur.quoted_text}</pre>
                      ) : (
                        <div className="text-[12px] text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                          <b>未抓取。</b>本条只定位到文件{cur.clause_ref ? '与条款' : ''}，
                          原文尚未从原件抽取，<b>不能直接向审查人员出示</b>。
                        </div>
                      )}
                    </div>

                    {cur.defect && (
                      <div className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-[11.5px] text-amber-900">
                        <b>{cur.defect}</b>
                        <div className="mt-0.5 whitespace-pre-line leading-snug">{cur.defect_note}</div>
                      </div>
                    )}

                    {cur.source_file && (
                      <div className="text-[11px] text-slate-400 break-all">
                        出处：{cur.source_file}
                        {cur.source_locator ? ` · ${cur.source_locator}` : ''}
                      </div>
                    )}
                    {cur.verification_note && (
                      <div className="text-[11px] text-slate-500 whitespace-pre-line leading-snug border-t border-slate-100 pt-2">
                        {cur.verification_note}
                      </div>
                    )}
                  </>
                )}
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
          依据登记表见 <span className="font-mono">registries/RuleRegistry_v0.yaml</span>。
          「已核原文」表示条文已从本地原件抽取并核对；「已定位」只表示知道出自哪份文件。
          <b>本页不做任何合规判断</b>，只回答"这条依据核到什么程度"。
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
