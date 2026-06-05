// ===================================================================
// 页 8 改动追踪（Diff Workbench）
// ===================================================================
const CHANGE_RECORDS = [
  { id:'c1', title:'land.total_area 由 3.20 → 3.54 hm²', by:'李工 · 编制', time:'今天 09:42', risk:'中',
    overview:{ facts:1, calc:2, oblig:3, tables:4, figures:2, narrative:8, footnotes:2, delivery:2 },
    facts:[['land.total_area','3.20 hm²','3.54 hm²'],['land.permanent_area','2.60 hm²','2.86 hm²']],
    calcs:[['水土保持补偿费','3.840 万元','4.248 万元'],['水土流失预测','116.2 t','128.6 t']],
    obligs:[{t:'OB-003 补偿费计算明细',c:'状态变化',d:'重新计算 → 已满足'},{t:'OB-001 表土保护',c:'无变化',d:'保持 已满足'},{t:'OB-007 占地复核',c:'新增义务',d:'占地超 3.5 hm² 触发复核'}],
    tables:[['补偿费计算表','占地面积','3.20','3.54'],['防治责任范围表','合计','3.20','3.54'],['投资汇总表','补偿费','3.840','4.248'],['水土流失预测表','预测总量','116.2','128.6']],
    figures:[{t:'FIG-002 防治责任范围图',c:'需重新生成',d:'红线面积变化，责任范围图需重新装配'},{t:'FIG-001 项目地理位置图',c:'无变化',d:'区域未变，无需更新'},{t:'FIG-004 监测点位图',c:'建议复核',d:'范围变化建议复核点位布设'}],
    narrative:[
      { ch:'2.1 项目概况', del:'总占地面积 3.20 hm²', add:'总占地面积 3.54 hm²' },
      { ch:'9.2 补偿费', del:'补偿费为 3.840 万元', add:'补偿费为 4.248 万元', manual:true },
      { ch:'5.1 流失量预测', del:'流失总量 116.2 t', add:'流失总量 128.6 t' },
    ],
    footnotes:[{t:'F-003 计算依据',c:'需重新确认',d:'计算器输出 3.840 → 4.248，注脚需重新确认'},{t:'F-001 事实来源',c:'新增',d:'占地红线更新，新增来源说明'},{t:'F-002 标准依据',c:'待复核',d:'来源字段 land.total_area 变化，需复核'},{t:'F-008 版本说明',c:'失效',d:'旧补偿费 3.840 万元说明已失效'}],
  },
  { id:'c2', title:'earthwork.spoil 由 0 → 5.00 万 m³', by:'李工 · 编制', time:'昨天 14:10', risk:'高',
    overview:{ facts:1, calc:1, oblig:3, tables:2, figures:3, narrative:3, footnotes:1, delivery:2 },
    facts:[['earthwork.spoil','0 万 m³','5.00 万 m³']],
    calcs:[['弃渣场级别计算器','不适用','待运行（预估 3 级）']],
    obligs:[
      {t:'弃渣场专项说明',c:'新增义务',d:'余方量>0，触发弃渣场专项章节'},
      {t:'弃渣场级别判定',c:'新增义务',d:'需运行弃渣场级别计算器'},
      {t:'弃渣场防护措施说明',c:'新增义务',d:'需补充拦挡 / 排水 / 覆盖措施'},
    ],
    tables:[['弃渣场级别判定表','级别','—','待判定'],['弃渣场防护措施表','措施','—','新增']],
    figures:[{t:'弃渣场位置图',c:'新增',d:'余方量>0，新增弃渣场位置图'},{t:'弃渣场防护措施图',c:'新增',d:'新增弃渣场防护措施图'},{t:'FIG-003 措施布局图',c:'需重新生成',d:'新增弃渣场，措施布局图需更新'}],
    narrative:[
      { ch:'5.x 弃渣场水土流失预测说明', del:'—', add:'新增弃渣场水土流失预测说明段落。' },
      { ch:'7.x 弃渣场防护措施', del:'—', add:'新增弃渣场拦挡、排水及覆盖措施段落。' },
      { ch:'11 结论风险提示', del:'—', add:'新增弃渣场相关风险提示。' },
    ],
    footnotes:[{t:'F-007 标准依据',c:'新增',d:'GB 51018-2014 弃渣场级别判定依据'}],
    delivery:['narrative_skeleton_v0.docx 需重新生成','formal_tables_v0.docx 需重新生成','review_trace.html 新增 3 条义务记录'],
    headline:'一个事实变化已触发 3 条审查义务、2 张表格、3 个正文段落和 2 个交付文件更新。',
    chain:[
      { t:'事实字段', icon:'Database', v:'earthwork.spoil = 5.00 万 m³' },
      { t:'规则判断', icon:'Gavel', v:'余方量大于 0，触发弃渣场相关审查义务' },
      { t:'专业计算器', icon:'Calculator', v:'弃渣场级别计算器待运行' },
      { t:'正式表格', icon:'Table2', v:'新增弃渣场级别判定表' },
      { t:'地图图件', icon:'Map', v:'新增弃渣场位置图' },
      { t:'正文章节', icon:'FileText', v:'新增弃渣场专项说明段落' },
      { t:'注脚依据', icon:'Asterisk', v:'需补充弃渣场设计资料来源' },
      { t:'交付包', icon:'Package', v:'review_trace.html 新增义务记录' },
    ],
  },
  { id:'c3', title:'compensation.region_rate 由 1.0 → 1.2', by:'系统 · 规则更新', time:'昨天 10:05', risk:'低',
    overview:{ facts:1, calc:1, oblig:1, tables:2, figures:1, narrative:1, footnotes:1, delivery:1 },
    facts:[['compensation.region_rate','1.0','1.2']],
    calcs:[['水土保持补偿费','3.540 万元','4.248 万元']],
    obligs:[{t:'OB-003 补偿费计算明细',c:'重新计算',d:'区域费率更新'}],
    tables:[['补偿费计算表','区域费率','1.0','1.2'],['投资汇总表','补偿费','3.540','4.248']],
    figures:[{t:'项目地理位置图',c:'建议复核',d:'区域规则图件注脚需复核'}],
    narrative:[{ ch:'9.2 补偿费', del:'补偿费为 3.540 万元', add:'补偿费为 4.248 万元', manual:true }],
    footnotes:[{t:'F-006 版本说明',c:'新增',d:'费率调整记录'}],
  },
  { id:'c4', title:'prevention.measures_layout 新增 2 条措施布局', by:'李工 · 编制', time:'2026-06-02', risk:'中',
    overview:{ facts:1, calc:1, oblig:1, tables:1, narrative:2, footnotes:1, delivery:1 },
    facts:[['measures.added','4 条','6 条']],
    calcs:[['防治措施投资汇总','5.16 万元','6.00 万元']],
    obligs:[{t:'OB-004 措施布局专家确认',c:'状态变化',d:'触发专家确认（2 条）'}],
    tables:[['防治措施投资表','合计','5.16','6.00']],
    narrative:[{ ch:'7.1 措施布局', del:'共布设措施 12 条', add:'共布设措施 14 条' },{ ch:'9.1 投资估算', del:'措施投资 5.16 万元', add:'措施投资 6.00 万元' }],
    footnotes:[{t:'F-004 审查意见',c:'新增',d:'布局针对性确认'}],
  },
];

const TABS = [
  { id:'facts', name:'事实变化', icon:'Database' },
  { id:'calcs', name:'计算结果变化', icon:'Calculator' },
  { id:'obligs', name:'义务变化', icon:'Gavel' },
  { id:'tables', name:'表格变化', icon:'Table2' },
  { id:'figures', name:'图件变化', icon:'Map' },
  { id:'narrative', name:'正文变化', icon:'FileText' },
  { id:'footnotes', name:'注脚变化', icon:'Asterisk' },
  { id:'chain', name:'证据链', icon:'Workflow' },
];

const CHAIN_STEPS = [
  { t:'事实字段', icon:'Database', v:'land.total_area' },
  { t:'规则', icon:'Gavel', v:'OB-003 补偿费义务' },
  { t:'计算器', icon:'Calculator', v:'补偿费计算器' },
  { t:'表格', icon:'Table2', v:'补偿费计算表' },
  { t:'地图图件', icon:'Map', v:'FIG-002 责任范围图' },
  { t:'正文', icon:'FileText', v:'9.2 补偿费' },
  { t:'注脚', icon:'Asterisk', v:'F-003' },
  { t:'交付包', icon:'Package', v:'formal_tables_v0.docx' },
];

function ChangeTrackingPage() {
  const [recId, setRecId] = useState('c1');
  const [tab, setTab] = useState('facts');
  const [expanded, setExpanded] = useState(0);
  const rec = CHANGE_RECORDS.find(r=>r.id===recId);
  const ov = rec.overview;
  const chainSteps = rec.chain || CHAIN_STEPS;
  const node = chainSteps[Math.min(expanded, chainSteps.length-1)] || chainSteps[0];

  return (
    <div>
      <PageHeader title="改动追踪" sub="改得动、查得清 — 一次事实修改，全链路影响一目了然" icon="GitCompareArrows">
        <Chip tone={rec.risk==='高'?'amber':'brand'} icon="TriangleAlert">风险等级：{rec.risk}</Chip>
      </PageHeader>

      <div className="p-5 space-y-4">
        {/* 演示爆点：大按钮 */}
        <div className="rounded-xl border border-brand-700 bg-brand-900 text-white p-4 flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2.5 flex-1 min-w-[240px]">
            <span className="w-10 h-10 rounded-lg bg-white/10 grid place-items-center"><Icon name="Zap" size={20} className="text-teal-300"/></span>
            <div>
              <div className="text-[14px] font-semibold">改动追踪演示</div>
              <div className="text-[12px] text-brand-300">点击右侧按钮，查看一个事实变化如何沿全链路传导。</div>
            </div>
          </div>
          <button onClick={()=>{ setRecId('c2'); setTab('facts'); setExpanded(0); }}
            className={`inline-flex items-center gap-2 text-[14px] px-5 py-2.5 rounded-lg font-medium whitespace-nowrap transition-colors ${recId==='c2'?'bg-teal-500 text-white':'bg-white text-brand-800 hover:bg-brand-50'}`}>
            <Icon name="Play" size={16}/>演示：余方量 0 → 5 万 m³
          </button>
        </div>

        {/* 冲击提示 */}
        {rec.headline && (
          <div className="rounded-lg border border-orange-300 bg-orange-50 px-4 py-3">
            <div className="flex items-start gap-2.5">
              <Icon name="Megaphone" size={18} className="text-orange-500 shrink-0 mt-0.5"/>
              <div className="flex-1">
                <div className="text-[14px] font-semibold text-orange-800">{rec.headline}</div>
                {rec.delivery && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {rec.delivery.map(d=><span key={d} className="text-[11px] px-2 py-0.5 rounded bg-white border border-orange-200 text-orange-700 font-mono">{d}</span>)}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 选择修改记录 */}
        <div>
          <div className="text-[11.5px] font-semibold text-slate-400 mb-2 flex items-center gap-1.5"><Icon name="GitCommitHorizontal" size={13}/>选择一次事实修改记录</div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {CHANGE_RECORDS.map(r => {
              const act = recId===r.id;
              return (
                <button key={r.id} onClick={()=>setRecId(r.id)}
                  className={`text-left rounded-lg border p-3 transition-all ${act?'border-brand-400 ring-1 ring-brand-200 bg-brand-50/40':'border-slate-200 bg-white hover:border-slate-300'}`}>
                  <div className="flex items-center justify-between mb-1.5">
                    <Chip tone="brand">{r.facts[0][0]}</Chip>
                    <span className={`text-[10px] px-1.5 py-px rounded ${r.risk==='高'?'bg-red-50 text-red-600':r.risk==='中'?'bg-orange-50 text-orange-600':'bg-emerald-50 text-emerald-600'}`}>{r.risk}风险</span>
                  </div>
                  <div className="text-[12px] text-slate-700 font-medium leading-snug">{r.title}</div>
                  <div className="mt-1.5 text-[10.5px] text-slate-400 flex items-center gap-1.5"><Icon name="User" size={10}/>{r.by} · {r.time}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 影响总览 */}
        <div className="grid grid-cols-4 md:grid-cols-8 gap-px bg-slate-200 rounded-lg overflow-hidden border border-slate-200">
          {[['影响事实',ov.facts,'Database'],['计算器',ov.calc,'Calculator'],['义务',ov.oblig,'Gavel'],['表格',ov.tables,'Table2'],['图件',ov.figures||0,'Map'],['正文章节',ov.narrative,'FileText'],['注脚',ov.footnotes,'Asterisk'],['交付文件',ov.delivery,'Package']].map(([k,v,icon]) => (
            <div key={k} className="bg-white p-3 text-center">
              <Icon name={icon} size={15} className="text-brand-500 mx-auto mb-1"/>
              <div className="text-[22px] font-bold text-slate-800 tabular leading-none">{v}</div>
              <div className="text-[10.5px] text-slate-400 mt-1">{k}</div>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <Panel>
          <div className="flex border-b border-slate-200 overflow-x-auto">
            {TABS.map(t => (
              <button key={t.id} onClick={()=>setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-[12.5px] whitespace-nowrap transition-colors ${tab===t.id?'text-brand-600 border-b-2 border-brand-600 bg-brand-50/40 font-medium':'text-slate-500 hover:text-slate-700'}`}>
                <Icon name={t.icon} size={14}/>{t.name}
              </button>
            ))}
          </div>

          <div className="p-4">
            {tab==='facts' && (
              <table className="w-full text-[12.5px]">
                <thead><tr className="text-[11px] text-slate-400 border-b border-slate-100"><th className="text-left font-medium py-2 px-2">字段</th><th className="text-left font-medium py-2 px-2">修改前</th><th className="text-left font-medium py-2 px-2">修改后</th></tr></thead>
                <tbody>{rec.facts.map((f,i)=>(<tr key={i} className="border-b border-slate-50"><td className="py-2.5 px-2"><Chip tone="brand">{f[0]}</Chip></td><td className="py-2.5 px-2 font-mono tabular"><span className="diff-del px-1">{f[1]}</span></td><td className="py-2.5 px-2 font-mono tabular"><span className="diff-add px-1">{f[2]}</span></td></tr>))}</tbody>
              </table>
            )}

            {tab==='calcs' && (
              <div className="space-y-2">{rec.calcs.map((c,i)=>(
                <div key={i} className="flex items-center justify-between px-3 py-2.5 rounded-md border border-slate-100 bg-slate-50">
                  <span className="text-[12.5px] text-slate-700 flex items-center gap-1.5"><Icon name="Calculator" size={13} className="text-brand-500"/>{c[0]}</span>
                  <span className="font-mono tabular text-[12.5px]"><span className="text-slate-400">{c[1]}</span><Icon name="ArrowRight" size={12} className="inline mx-2 text-slate-300"/><span className="text-brand-700 font-semibold">{c[2]}</span></span>
                </div>
              ))}</div>
            )}

            {tab==='obligs' && (
              <div className="space-y-2">{rec.obligs.map((o,i)=>(
                <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-md border border-slate-100">
                  <span className="text-[12.5px] text-slate-700 flex-1">{o.t}</span>
                  <Chip tone={o.c.includes('新增')?'emerald':o.c.includes('无')?'slate':'amber'}>{o.c}</Chip>
                  <span className="text-[11.5px] text-slate-400">{o.d}</span>
                </div>
              ))}</div>
            )}

            {tab==='tables' && (
              <table className="w-full text-[12.5px]">
                <thead><tr className="text-[11px] text-slate-400 border-b border-slate-100"><th className="text-left font-medium py-2 px-2">表格</th><th className="text-left font-medium py-2 px-2">单元格</th><th className="text-left font-medium py-2 px-2">原值</th><th className="text-left font-medium py-2 px-2">新值</th></tr></thead>
                <tbody>{rec.tables.map((t,i)=>(<tr key={i} className="border-b border-slate-50"><td className="py-2.5 px-2 text-slate-700">{t[0]}</td><td className="py-2.5 px-2 text-slate-500">{t[1]}</td><td className="py-2.5 px-2 font-mono tabular text-slate-400">{t[2]}</td><td className="py-2.5 px-2 font-mono tabular"><span className="diff-chg px-1">{t[3]}</span></td></tr>))}</tbody>
              </table>
            )}

            {tab==='figures' && (
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 pb-1">图件变化图例：
                  <StatusTag status="新增"/><StatusTag status="需重新确认"/><StatusTag status="不适用"/>
                </div>
                {(rec.figures||[]).map((f,i)=>{
                  const tone = f.c==='新增'?'新增':f.c==='无变化'?'不适用':'需重新确认';
                  return (
                    <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-md border border-slate-100">
                      <Icon name="Map" size={13} className="text-teal-500"/>
                      <span className="text-[12.5px] text-slate-700 flex-1">{f.t}</span>
                      <StatusTag status={tone} dot/>
                      <span className="text-[11.5px] text-slate-400 max-w-[220px] text-right">{f.d}</span>
                    </div>
                  );
                })}
                {(!rec.figures||rec.figures.length===0) && <div className="text-[12px] text-slate-400 text-center py-4">本次变更不影响图件</div>}
              </div>
            )}

            {tab==='narrative' && (
              <div className="space-y-3">
                {rec.narrative.some(n=>n.manual) && (
                  <div className="flex items-start gap-2 px-3 py-2.5 rounded-md bg-orange-50 border border-orange-200 text-[12.5px] text-orange-800">
                    <Icon name="UserX" size={15} className="text-orange-500 shrink-0 mt-0.5"/>
                    <span><b>人工编辑覆盖风险：</b>本次事实变化影响的段落中，存在已被人工覆盖的内容。系统已重算但<b>不会自动覆盖人工修改</b>，请逐段重新审阅。</span>
                  </div>
                )}
                {rec.narrative.map((n,i)=>(
                <div key={i} className={`rounded-md border overflow-hidden ${n.manual?'border-orange-200':'border-slate-100'}`}>
                  <div className={`flex items-center justify-between px-3 py-1.5 border-b ${n.manual?'bg-orange-50/60 border-orange-100':'bg-slate-50 border-slate-100'}`}>
                    <span className="text-[12px] font-medium text-slate-600">{n.ch}</span>
                    {n.manual && <StatusTag status="人工编辑"/>}
                  </div>
                  <div className="p-3 space-y-1 text-[13px] font-serif leading-relaxed">
                    {n.del!=='—' && <div><span className="diff-del px-1">{n.del}</span></div>}
                    <div><span className="diff-add px-1">{n.add}</span></div>
                    {n.manual && <div className="text-[11px] text-orange-600 flex items-center gap-1 mt-1 font-sans"><Icon name="TriangleAlert" size={12}/>该段落已人工覆盖，系统建议重新审阅。</div>}
                  </div>
                </div>
              ))}</div>
            )}

            {tab==='footnotes' && (
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 pb-1">图例：
                  <StatusTag status="新增"/><StatusTag status="失效"/><StatusTag status="需重新确认"/><StatusTag status="待复核"/>
                </div>
                {rec.footnotes.map((f,i)=>{
                  const tone = f.c==='新增'?'新增':f.c==='失效'?'失效':f.c==='需重新确认'?'需重新确认':'待复核';
                  return (
                    <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-md border border-slate-100">
                      <Icon name="Asterisk" size={13} className="text-amber-500"/>
                      <span className="text-[12.5px] text-slate-700 flex-1">{f.t}</span>
                      <StatusTag status={tone} dot/>
                      <span className="text-[11.5px] text-slate-400 max-w-[200px] text-right">{f.d}</span>
                    </div>
                  );
                })}
              </div>
            )}

            {tab==='chain' && (
              <div className="py-4">
                <div className="flex items-center justify-between gap-1 overflow-x-auto pb-2">
                  {chainSteps.map((s,i) => (
                    <React.Fragment key={s.t}>
                      <button onClick={()=>setExpanded(i)} className={`shrink-0 flex flex-col items-center gap-1.5 px-3 py-2.5 rounded-lg border transition-all ${expanded===i?'border-brand-400 bg-brand-50 ring-1 ring-brand-200':'border-slate-200 bg-white hover:border-slate-300'}`}>
                        <span className={`w-9 h-9 rounded-full grid place-items-center ${expanded===i?'bg-brand-600 text-white':'bg-slate-100 text-slate-500'}`}><Icon name={s.icon} size={17}/></span>
                        <span className="text-[10.5px] text-slate-400">{s.t}</span>
                        <span className="text-[11px] font-mono text-slate-600 max-w-[96px] truncate">{s.v}</span>
                      </button>
                      {i<chainSteps.length-1 && <Icon name="ChevronRight" size={16} className="text-slate-300 shrink-0"/>}
                    </React.Fragment>
                  ))}
                </div>
                <div className="mt-4 rounded-lg bg-slate-50 border border-slate-200 p-4">
                  <div className="flex items-center gap-2 text-[13px] font-semibold text-slate-700 mb-1.5">
                    <Icon name={node.icon} size={15} className="text-brand-600"/>{node.t}：<span className="font-mono">{node.v}</span>
                  </div>
                  <p className="text-[12.5px] text-slate-500 leading-relaxed">
                    {rec.facts[0][0]} 的修改沿证据链传导至此节点。该节点的输出已重新生成并与上下游保持一致，相关变更已记录至改动日志与交付包追踪文件 <span className="font-mono">evidence_chain.json</span>。
                  </p>
                  {node.v==='F-003' && (
                    <div className="mt-3 rounded-md bg-white border border-slate-200 p-3 space-y-1.5">
                      <div className="flex items-center gap-2 text-[12px]"><span className="text-brand-600 font-bold">[1]</span><Chip tone="amber">计算依据</Chip><span className="text-slate-400 ml-auto font-mono text-[11px]">F-003</span></div>
                      <div className="text-[12px] text-slate-600">计算来源：水土保持补偿费计算器，输出 4.248 万元。</div>
                      <div className="grid grid-cols-2 gap-2 pt-1">
                        <div className="text-[11px]"><span className="text-slate-400">关联来源类型：</span><span className="text-slate-600">calculator</span></div>
                        <div className="text-[11px]"><span className="text-slate-400">关联来源 ID：</span><span className="font-mono text-slate-600">calc.fee</span></div>
                      </div>
                      <div className="flex items-center gap-2 pt-1.5 border-t border-slate-100"><span className="text-[11px] text-slate-400">注脚状态：</span><StatusTag status="需重新确认" dot/><span className="text-[11px] text-slate-400">计算器输出由 3.840 变为 4.248，注脚需重新确认</span></div>
                    </div>
                  )}
                  {node.t==='地图图件' && (
                    <div className="mt-3 rounded-md bg-white border border-slate-200 p-3 space-y-1.5">
                      <div className="flex items-center gap-2 text-[12px]"><Icon name="Map" size={13} className="text-teal-500"/><span className="font-medium text-slate-700">{node.v}</span><span className="text-slate-400 ml-auto font-mono text-[11px]">FIG-002</span></div>
                      <div className="text-[12px] text-slate-600">红线边界与防治责任范围事实变化，地图图件需重新装配并复核图签与图注。</div>
                      <div className="flex items-center gap-2 pt-1.5 border-t border-slate-100"><span className="text-[11px] text-slate-400">图件状态：</span><StatusTag status="可生成" dot/><span className="text-[11px] text-slate-400">待重新生成后进入交付包</span></div>
                    </div>
                  )}
                  {node.t==='注脚依据' && (
                    <div className="mt-3 rounded-md bg-white border border-slate-200 p-3 space-y-1.5">
                      <div className="flex items-center gap-2 text-[12px]"><Chip tone="amber">标准依据</Chip><span className="text-slate-400 ml-auto font-mono text-[11px]">F-007（待补充）</span></div>
                      <div className="text-[12px] text-slate-600">需补充弃渣场设计资料来源（GB 51018-2014 弃渣场级别判定依据）。</div>
                      <div className="flex items-center gap-2 pt-1.5 border-t border-slate-100"><span className="text-[11px] text-slate-400">注脚状态：</span><StatusTag status="缺失事实" dot/><span className="text-[11px] text-slate-400">弃渣场设计资料尚未录入</span></div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}

window.ChangeTrackingPage = ChangeTrackingPage;
