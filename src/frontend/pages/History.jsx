// ===================================================================
// 页 10 历史与版本（版本时间线 + 操作日志 · 项目内）
// ===================================================================
const { PROJECT_VERSIONS: H_VERSIONS, OP_LOG: H_OPLOG } = window.CPSWC;

const VERSION_DIFF = {
  'v0.5':{ items:[['补偿费','3.540 万元','4.248 万元'],['区域费率','1.0','1.2'],['正文 9.2','系统生成','—'],['六率目标表','LIVE','LIVE']] },
  'v0.4':{ items:[['措施数量','12 条','14 条'],['措施投资','5.16 万元','6.00 万元'],['OB-004','已满足','专家确认'],['防治措施表','LIVE','LIVE']] },
  'v0.3':{ items:[['OB-002 弃渣场','待判定','不适用'],['表土保护','骨架','LIVE'],['弃渣场级别表','SKELETON','NOT_APPLICABLE']] },
  'v0.2':{ items:[['防治责任范围','—','3.20 hm²'],['六率目标表','—','SKELETON'],['土石方平衡表','—','LIVE']] },
  'v0.1':{ items:[['项目','—','已创建'],['报告骨架','—','11 章'],['规则集','—','3 项']] },
  'v0.6-preview':{ items:[['占地面积','3.20 hm²','3.54 hm²'],['补偿费','3.840 万元','4.248 万元'],['正文 9.2','系统生成','人工编辑'],['预测流失量','116.2 t','128.6 t']] },
};

function HistoryPage() {
  const [tab, setTab] = useState('versions');
  const [active, setActive] = useState('v0.5');
  const [compare, setCompare] = useState(false);
  const [rolledBack, setRolledBack] = useState(null);
  const cur = H_VERSIONS.find(v=>v.v===active);
  const diff = VERSION_DIFF[active] || { items:[] };

  return (
    <div>
      <PageHeader title="历史与版本" sub="版本快照时间线 · 可对比 / 回滚 · 项目操作日志" icon="History">
        <Chip tone="brand" icon="GitBranch">当前 v0.6-preview</Chip>
      </PageHeader>

      <div className="p-5">
        {/* Tabs */}
        <div className="flex gap-1 border-b border-slate-200 mb-4">
          {[['versions','版本快照','GitCommitHorizontal'],['log','操作日志','ScrollText']].map(([id,label,icon]) => (
            <button key={id} onClick={()=>setTab(id)} className={`flex items-center gap-1.5 px-4 py-2.5 text-[13px] transition-colors ${tab===id?'text-brand-600 border-b-2 border-brand-600 font-medium':'text-slate-500 hover:text-slate-700'}`}><Icon name={icon} size={14}/>{label}</button>
          ))}
        </div>

        {tab==='versions' && (
          <div className="grid grid-cols-[340px_1fr] gap-4">
            {/* 时间线 */}
            <div className="bg-white rounded-lg border border-slate-200 panel-shadow p-4">
              <div className="text-[12px] font-semibold text-slate-500 mb-3 flex items-center gap-1.5"><Icon name="GitCommitHorizontal" size={14}/>版本时间线</div>
              <div className="relative pl-1">
                {H_VERSIONS.map((v,i) => {
                  const act = active===v.v;
                  return (
                    <button key={v.v} onClick={()=>{setActive(v.v);setCompare(false);}} className="w-full text-left relative pl-7 pb-4 last:pb-0 group">
                      {i<H_VERSIONS.length-1 && <span className="absolute left-[9px] top-5 bottom-0 w-px bg-slate-200"></span>}
                      <span className={`absolute left-0 top-1 w-[19px] h-[19px] rounded-full grid place-items-center ${v.current?'bg-brand-600':act?'bg-brand-100 ring-2 ring-brand-400':'bg-white border-2 border-slate-300'}`}>
                        {v.current && <span className="w-2 h-2 rounded-full bg-white"></span>}
                      </span>
                      <div className={`rounded-md border p-2.5 transition-colors ${act?'border-brand-300 bg-brand-50/50':'border-transparent group-hover:bg-slate-50'}`}>
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-[13px] font-semibold text-slate-800">{v.v}</span>
                          <StatusTag status={v.current?'系统生成':v.tag==='已审查'?'专家确认':'已生成'} />
                        </div>
                        <div className="text-[11.5px] text-slate-500 mt-1 line-clamp-2 leading-snug">{v.summary}</div>
                        <div className="text-[10.5px] text-slate-400 mt-1 flex items-center gap-2"><Icon name="User" size={10}/>{v.by} · {v.date.slice(5)}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 详情 / 对比 */}
            <div className="space-y-4">
              <Panel title={`${cur.v} 版本详情`} sub={cur.date + ' · ' + cur.by} right={
                <div className="flex items-center gap-2">
                  <button onClick={()=>setCompare(c=>!c)} className={`text-[12px] px-3 py-1.5 rounded-md border inline-flex items-center gap-1.5 ${compare?'bg-brand-600 text-white border-brand-600':'border-slate-200 text-slate-600 hover:bg-slate-50'}`}><Icon name="GitCompareArrows" size={14}/>与当前对比</button>
                  {!cur.current && <button onClick={()=>setRolledBack(cur.v)} className="text-[12px] px-3 py-1.5 rounded-md border border-orange-300 text-orange-600 hover:bg-orange-50 inline-flex items-center gap-1.5"><Icon name="RotateCcw" size={14}/>回滚到此版本</button>}
                </div>
              }>
                <div className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <StatusTag status={cur.current?'系统生成':'已生成'} dot/>
                    <Chip tone="slate" icon="GitBranch">{cur.changes} 处变更</Chip>
                  </div>
                  <p className="text-[13px] text-slate-600 leading-relaxed">{cur.summary}</p>
                </div>
              </Panel>

              {compare && (
                <Panel title={`版本对比`} sub={`${cur.v} → v0.6-preview（当前）`}>
                  <table className="w-full text-[12.5px]">
                    <thead><tr className="text-[11px] text-slate-400 border-b border-slate-100"><th className="text-left font-medium px-4 py-2">项目</th><th className="text-left font-medium px-2 py-2">{cur.v}</th><th className="text-left font-medium px-2 py-2">当前</th></tr></thead>
                    <tbody>
                      {diff.items.map((d,i) => (
                        <tr key={i} className="border-b border-slate-50 last:border-0">
                          <td className="px-4 py-2.5 text-slate-700">{d[0]}</td>
                          <td className="px-2 py-2.5 font-mono tabular"><span className="diff-del px-1">{d[1]}</span></td>
                          <td className="px-2 py-2.5 font-mono tabular"><span className="diff-add px-1">{d[2]}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Panel>
              )}

              {rolledBack && (
                <div className="flex items-start gap-2.5 px-4 py-3 rounded-lg bg-orange-50 border border-orange-200 text-[12.5px] text-orange-800">
                  <Icon name="TriangleAlert" size={16} className="text-orange-500 shrink-0 mt-0.5"/>
                  <span>已创建回滚预览：将当前版本回滚至 <b>{rolledBack}</b>。回滚会生成一个新版本（不会丢失历史），人工编辑段落需重新审阅。
                  <button onClick={()=>setRolledBack(null)} className="ml-1 underline text-orange-600">取消</button>
                  <button className="ml-2 underline text-orange-700 font-medium">确认回滚</button></span>
                </div>
              )}
            </div>
          </div>
        )}

        {tab==='log' && (
          <Panel title="项目操作日志" sub="本项目内的全部动作（最近）">
            <div className="divide-y divide-slate-100">
              {H_OPLOG.map((o,i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50/60">
                  <span className="w-8 h-8 rounded-md bg-slate-50 grid place-items-center text-slate-400 shrink-0"><Icon name={o.icon} size={15}/></span>
                  <div className="flex-1 min-w-0">
                    <div className="text-[13px] text-slate-700"><b className="font-medium">{o.action}</b> · <span className="text-slate-500">{o.target}</span></div>
                    <div className="text-[11.5px] text-slate-400">{o.detail}</div>
                  </div>
                  {o.risk && <StatusTag status="风险"/>}
                  <span className="text-[11px] text-slate-400 shrink-0">{o.time}</span>
                </div>
              ))}
            </div>
          </Panel>
        )}
      </div>
    </div>
  );
}

window.HistoryPage = HistoryPage;