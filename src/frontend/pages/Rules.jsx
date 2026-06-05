// ===================================================================
// 页 3 规则审查
// ===================================================================
const OBLIGATIONS = [
  { id:'OB-001', name:'表土保护措施判断', cond:'存在表土剥离或占用耕地 / 园地', status:'已满足', risk:'低', ref:['GB 50433-2018'], evidence:'topsoil.stripping', expert:false,
    chain:{ fact:'topsoil.stripping = 0 万 m³（场地为已硬化用地）', rule:'当无表土剥离且不占用耕园地时，按简化表土保护措施处理。', std:['GB 50433-2018 6.2'], result:'表土保护章节标记为 LIVE（简化）。', pos:['第 4 章 表土保护','第 7 章 水土保持措施'] } },
  { id:'OB-002', name:'弃渣场专项说明', cond:'余方量 > 0 或存在永久 / 临时弃渣场', status:'不适用', risk:'—', ref:['GB 51018-2014'], evidence:'earthwork.spoil = 0', expert:false,
    chain:{ fact:'earthwork.spoil = 0 万 m³（挖填平衡，无余方）', rule:'当余方量为 0 时，不触发弃渣场专项章节与级别鉴定。', std:['GB 50433-2018','GB 51018-2014'], result:'弃渣场章节标记为 NOT_APPLICABLE。', pos:['第 5 章 水土流失预测','第 7 章 水土保持措施','交付包 review_trace.html'] } },
  { id:'OB-003', name:'补偿费计算明细', cond:'征占地行为成立', status:'已满足', risk:'低', ref:['广东省水土保持补偿费规则'], evidence:'land.total_area', expert:false,
    chain:{ fact:'land.total_area = 3.54 hm² · project.location = 广东省惠州市', rule:'按占地面积 × 区域费率计征水土保持补偿费，惠州市适用区域系数 1.2。', std:['广东省水土保持补偿费征收使用管理办法','惠州市适配规则'], result:'补偿费 = 4.248 万元，写入补偿费计算表。', pos:['第 9 章 投资估算','附表 6 补偿费计算表'] } },
  { id:'OB-004', name:'防治措施布局专家确认', cond:'方案新增措施或措施布局调整', status:'专家确认', risk:'中', ref:['GB 50433-2018'], evidence:'prevention.measures_layout', expert:true,
    chain:{ fact:'measures.added = 6 条（其中 2 条布局需复核）', rule:'方案新增措施布局应经专家确认其针对性与合理性后方可定稿。', std:['GB 50433-2018 7.1'], result:'措施布局标记为待专家确认（2 条）。', pos:['第 7 章 水土保持措施','附表 8 防治措施表'] } },
  { id:'OB-005', name:'年度投资分配', cond:'建设期跨年度', status:'待补充', risk:'中', ref:['投资估算章节要求'], evidence:'investment.annual_allocation', expert:false,
    chain:{ fact:'investment.annual_allocation = 缺失（建设期 2026-08 ~ 2027-12）', rule:'建设期跨年度时应提供年度投资分配，支撑年度投资表生成。', std:['GB 50433-2018 8.2'], result:'年度投资表标记为 SKELETON，待补充事实。', pos:['第 9 章 投资估算','附表 7 年度投资表'] } },
  { id:'OB-006', name:'监测点位布设', cond:'防治责任范围 ≥ 1 hm²', status:'已满足', risk:'低', ref:['GB/T 51240-2018'], evidence:'monitor.points', expert:false,
    chain:{ fact:'monitor.points = 4 个 · 防治责任范围 3.54 hm²', rule:'防治责任范围 ≥ 1 hm² 应布设水土流失监测点。', std:['GB/T 51240-2018'], result:'监测点位表标记为 LIVE。', pos:['第 8 章 监测安排','附表 9 监测点位表'] } },
];

const FILTERS = ['全部','已满足','待补充','专家确认','不适用','阻塞'];

function RulesPage() {
  const [filter, setFilter] = useState('全部');
  const [active, setActive] = useState('OB-002');
  const [confirmed, setConfirmed] = useState({});
  const [stdOpen, setStdOpen] = useState(true);

  const list = OBLIGATIONS.filter(o => filter === '全部' || o.status === filter);
  const cur = OBLIGATIONS.find(o => o.id === active) || OBLIGATIONS[0];
  const counts = FILTERS.reduce((a,f) => { a[f] = f==='全部' ? OBLIGATIONS.length : OBLIGATIONS.filter(o=>o.status===f).length; return a; }, {});

  return (
    <div>
      <PageHeader title="规则审查" sub="规则可追踪 · 义务可审查 — 每条结论可追溯到事实、规则与标准依据" icon="Gavel">
        <Chip tone="brand" icon="ShieldCheck">无阻塞</Chip>
        <Chip tone="amber" icon="UserCheck">专家确认 2 项</Chip>
      </PageHeader>

      <div className="p-5 space-y-4">
        {/* 规则集状态 */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-px bg-slate-200 rounded-lg overflow-hidden border border-slate-200">
          {[
            { k:'当前规则集', v:'GB 50433-2018 等 4 项', icon:'BookOpen' },
            { k:'适用区域', v:'广东省惠州市', icon:'MapPin' },
            { k:'规则锁定', v:'候选规则集 · 冻结后锁定', icon:'LockOpen' },
            { k:'审查状态', v:'无阻塞', icon:'CircleCheck', ok:true },
            { k:'专家确认', v:'2 项待处理', icon:'UserCheck', warn:true },
          ].map(c => (
            <div key={c.k} className="bg-white p-3.5">
              <div className="flex items-center gap-1.5 text-[11px] text-slate-400"><Icon name={c.icon} size={12}/>{c.k}</div>
              <div className={`mt-1 text-[13px] font-medium ${c.ok?'text-emerald-600':c.warn?'text-orange-600':'text-slate-700'}`}>{c.v}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-[1fr_360px] gap-4">
          {/* 义务表 */}
          <Panel title="义务触发列表" sub={`共 ${OBLIGATIONS.length} 条义务`} right={
            <div className="flex items-center gap-1">
              {FILTERS.map(f => (
                <button key={f} onClick={()=>setFilter(f)}
                  className={`text-[11.5px] px-2 py-1 rounded transition-colors ${filter===f ? 'bg-brand-600 text-white' : 'text-slate-500 hover:bg-slate-100'}`}>
                  {f}<span className="ml-1 opacity-60 tabular">{counts[f]}</span>
                </button>
              ))}
            </div>
          }>
            <table className="w-full text-[12.5px]">
              <thead>
                <tr className="text-[11px] text-slate-400 border-b border-slate-100">
                  <th className="text-left font-medium px-4 py-2">义务</th>
                  <th className="text-left font-medium px-2 py-2">触发条件</th>
                  <th className="text-left font-medium px-2 py-2">状态</th>
                  <th className="text-left font-medium px-2 py-2">风险</th>
                  <th className="text-left font-medium px-2 py-2">证据字段</th>
                  <th className="px-2 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {list.map(o => {
                  const act = active === o.id;
                  const isConfirmed = confirmed[o.id];
                  return (
                    <tr key={o.id} onClick={()=>setActive(o.id)}
                      className={`border-b border-slate-50 last:border-0 cursor-pointer transition-colors ${act ? 'bg-brand-50/70' : 'hover:bg-slate-50'}`}>
                      <td className="px-4 py-2.5">
                        <div className="font-mono text-[11px] text-slate-400">{o.id}</div>
                        <div className="text-slate-800 font-medium">{o.name}</div>
                      </td>
                      <td className="px-2 py-2.5 text-slate-500 max-w-[160px]">{o.cond}</td>
                      <td className="px-2 py-2.5"><StatusTag status={isConfirmed ? '已满足' : o.status} dot /></td>
                      <td className="px-2 py-2.5">
                        <span className={`text-[11px] ${o.risk==='中'?'text-orange-500':o.risk==='低'?'text-emerald-600':'text-slate-300'}`}>{o.risk}</span>
                      </td>
                      <td className="px-2 py-2.5"><span className="font-mono text-[11px] text-slate-500">{o.evidence}</span></td>
                      <td className="px-2 py-2.5 text-right"><Icon name="ChevronRight" size={14} className={act?'text-brand-500':'text-slate-300'}/></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>

          {/* 证据链 */}
          <Panel title="证据链详情" sub={cur.id + ' · ' + cur.name} right={<StatusTag status={confirmed[cur.id]?'已满足':cur.status} dot/>}>
            <div className="p-4 space-y-3.5">
              {[
                { n:'1', t:'来源事实', icon:'Database', body:cur.chain.fact, mono:true },
                { n:'2', t:'判断规则', icon:'Gavel', body:cur.chain.rule },
                { n:'4', t:'生成结果', icon:'CircleCheck', body:cur.chain.result },
              ].map((s,i,arr) => (
                <div key={s.n} className="relative pl-7">
                  <span className="absolute left-0 top-0 w-5 h-5 rounded-full bg-brand-600 text-white grid place-items-center text-[10px] font-bold">{s.n}</span>
                  {i<arr.length && <span className="absolute left-[9px] top-5 bottom-[-14px] w-px bg-slate-200"></span>}
                  <div className="text-[11.5px] font-semibold text-slate-500 flex items-center gap-1.5"><Icon name={s.icon} size={12}/>{s.t}</div>
                  <div className={`mt-1 text-[12.5px] text-slate-700 leading-relaxed ${s.mono?'font-mono tabular bg-slate-50 rounded px-2 py-1.5':''}`}>{s.body}</div>
                </div>
              ))}

              {/* 标准依据（可展开） */}
              <div className="relative pl-7">
                <span className="absolute left-0 top-0 w-5 h-5 rounded-full bg-amber-500 text-white grid place-items-center text-[10px] font-bold">3</span>
                <span className="absolute left-[9px] top-5 bottom-[-14px] w-px bg-slate-200"></span>
                <button onClick={()=>setStdOpen(o=>!o)} className="text-[11.5px] font-semibold text-slate-500 flex items-center gap-1.5">
                  <Icon name="BookMarked" size={12}/>标准依据<Icon name={stdOpen?'ChevronUp':'ChevronDown'} size={12}/>
                </button>
                {stdOpen && (
                  <div className="mt-1.5 space-y-1">
                    {cur.chain.std.map(s => (
                      <div key={s} className="flex items-center gap-1.5 text-[12px] text-amber-700 bg-amber-50 border border-amber-100 rounded px-2 py-1">
                        <Icon name="FileBadge" size={12}/>{s}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 影响报告位置 */}
              <div className="relative pl-7">
                <span className="absolute left-0 top-0 w-5 h-5 rounded-full bg-teal-500 text-white grid place-items-center text-[10px] font-bold">5</span>
                <div className="text-[11.5px] font-semibold text-slate-500 flex items-center gap-1.5"><Icon name="MapPin" size={12}/>影响报告位置</div>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {cur.chain.pos.map(p => <Chip key={p} tone="teal">{p}</Chip>)}
                </div>
              </div>

              {/* 专家确认 */}
              {cur.expert && (
                <div className="mt-1 p-3 rounded-lg bg-orange-50 border border-orange-200">
                  {confirmed[cur.id] ? (
                    <div className="flex items-center gap-2 text-[12.5px] text-emerald-700">
                      <Icon name="CircleCheck" size={16} className="text-emerald-600"/>
                      <span>已由 <b>张工 · 审查专家</b> 确认 · {new Date().toLocaleDateString('zh-CN')}</span>
                    </div>
                  ) : (
                    <>
                      <div className="text-[12px] text-orange-800 mb-2 flex items-center gap-1.5"><Icon name="UserCheck" size={14}/>本义务需要专家确认后方可定稿</div>
                      <button onClick={()=>setConfirmed(c=>({...c,[cur.id]:true}))}
                        className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md bg-orange-500 text-white hover:bg-orange-600 transition-colors">
                        <Icon name="Check" size={14}/>确认通过
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

window.RulesPage = RulesPage;
