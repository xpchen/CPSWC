// ===================================================================
// 新建项目向导：基本信息 → 选规则集 → 录关键事实 → 生成骨架
// ===================================================================
const { RULESET_OPTIONS: WZ_RULES, PROJECT_TYPES: WZ_TYPES } = window.CPSWC;

const WZ_STEPS = [
  { n:1, name:'基本信息', icon:'FileText', desc:'项目名称、单位、地点、类型' },
  { n:2, name:'选规则集', icon:'BookMarked', desc:'适用标准与区域规则' },
  { n:3, name:'录关键事实', icon:'Database', desc:'占地、土石方等核心事实' },
  { n:4, name:'生成骨架', icon:'Sparkles', desc:'生成报告与表格骨架' },
];

function WzField({ label, children, hint }) {
  return (
    <label className="block">
      <span className="text-[12.5px] font-medium text-slate-600">{label}</span>
      <div className="mt-1.5">{children}</div>
      {hint && <span className="text-[11px] text-slate-400 mt-1 block">{hint}</span>}
    </label>
  );
}
const wzInput = "w-full h-10 rounded-md border border-slate-300 bg-white text-[13.5px] text-slate-800 px-3 focus:outline-none focus:ring-2 focus:ring-brand-300 focus:border-brand-400";

function NewProjectWizard({ onCancel, onFinish }) {
  const [step, setStep] = useState(1);
  const [gen, setGen] = useState(0); // 0 idle, 1 generating, 2 done
  const [f, setF] = useState({
    name:'', org:'', location:'广东省', type:'物流仓储', start:'', end:'',
    rules:['gb50433','gb50434','gd_region'],
    facts:{ total:'', perm:'', temp:'', exc:'', fill:'', spoil:'' },
  });
  const up = (k,v)=>setF(s=>({...s,[k]:v}));
  const upFact = (k,v)=>setF(s=>({...s,facts:{...s.facts,[k]:v}}));
  const toggleRule = (id) => {
    const r = WZ_RULES.find(x=>x.id===id);
    if (r.required) return;
    setF(s=>({...s,rules: s.rules.includes(id)?s.rules.filter(x=>x!==id):[...s.rules,id]}));
  };

  const canNext = step===1 ? f.name.trim() : true;

  const runGenerate = () => {
    setGen(1);
    setTimeout(()=>setGen(2), 1700);
  };

  const finish = () => {
    onFinish({
      id:'p-new', name:f.name||'未命名项目', code:'GD-NEW-2026-XXXX-0000', location:f.location, type:f.type,
      role:'编制人员', stage:'方案编制 · 骨架已生成', completeness:38, status:'缺失', frozen:false, blockers:2, expert:0,
      version:'v0.1', updated:'刚刚', members:1, isNew:true,
    });
  };

  return (
    <div className="h-full flex flex-col bg-[#eef1f5]">
      {/* 顶栏 */}
      <header className="h-14 shrink-0 bg-white border-b border-slate-200 flex items-center px-5 gap-3">
        <div className="w-8 h-8 rounded bg-gradient-to-br from-teal-500 to-brand-500 grid place-items-center font-bold text-[12px] text-white">CP</div>
        <div className="text-[14px] font-semibold text-slate-800">新建水土保持方案项目</div>
        <button onClick={onCancel} className="ml-auto text-[12.5px] text-slate-400 hover:text-slate-600 inline-flex items-center gap-1"><Icon name="X" size={15}/>取消</button>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-[860px] mx-auto p-6">
          {/* 步骤条 */}
          <div className="flex items-center justify-between mb-6">
            {WZ_STEPS.map((s,i) => (
              <React.Fragment key={s.n}>
                <div className="flex items-center gap-2.5">
                  <span className={`w-9 h-9 rounded-full grid place-items-center shrink-0 transition-colors ${step>s.n?'bg-emerald-500 text-white':step===s.n?'bg-brand-600 text-white':'bg-white border border-slate-300 text-slate-400'}`}>
                    {step>s.n ? <Icon name="Check" size={17}/> : <Icon name={s.icon} size={16}/>}
                  </span>
                  <div className="hidden sm:block">
                    <div className={`text-[12.5px] font-medium ${step>=s.n?'text-slate-800':'text-slate-400'}`}>{s.name}</div>
                    <div className="text-[10.5px] text-slate-400">{s.desc}</div>
                  </div>
                </div>
                {i<WZ_STEPS.length-1 && <div className={`flex-1 h-px mx-3 ${step>s.n?'bg-emerald-400':'bg-slate-200'}`}></div>}
              </React.Fragment>
            ))}
          </div>

          <div className="bg-white rounded-lg border border-slate-200 panel-shadow p-6 min-h-[380px]">
            {/* Step 1 */}
            {step===1 && (
              <div className="space-y-5">
                <div><h2 className="text-[16px] font-semibold text-slate-800">项目基本信息</h2><p className="text-[12.5px] text-slate-400 mt-0.5">这些信息将作为报告封面与第 2 章项目概况的事实来源。</p></div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2"><WzField label="项目名称" hint="例如：世维华南供应链（二期）"><input value={f.name} onChange={e=>up('name',e.target.value)} placeholder="请输入项目全称" className={wzInput}/></WzField></div>
                  <WzField label="建设单位"><input value={f.org} onChange={e=>up('org',e.target.value)} placeholder="如：广东××供应链有限公司" className={wzInput}/></WzField>
                  <WzField label="建设地点"><input value={f.location} onChange={e=>up('location',e.target.value)} className={wzInput}/></WzField>
                  <WzField label="项目类型"><select value={f.type} onChange={e=>up('type',e.target.value)} className={wzInput}>{WZ_TYPES.map(t=><option key={t}>{t}</option>)}</select></WzField>
                  <div className="grid grid-cols-2 gap-3">
                    <WzField label="开工时间"><input value={f.start} onChange={e=>up('start',e.target.value)} placeholder="2026-08" className={wzInput}/></WzField>
                    <WzField label="完工时间"><input value={f.end} onChange={e=>up('end',e.target.value)} placeholder="2027-12" className={wzInput}/></WzField>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2 */}
            {step===2 && (
              <div className="space-y-5">
                <div><h2 className="text-[16px] font-semibold text-slate-800">选择适用规则集</h2><p className="text-[12.5px] text-slate-400 mt-0.5">规则集决定义务触发、计算器与审查逻辑。冻结版本后规则集将锁定。</p></div>
                <div className="space-y-2.5">
                  {WZ_RULES.map(r => {
                    const on = f.rules.includes(r.id);
                    return (
                      <button key={r.id} onClick={()=>toggleRule(r.id)} disabled={r.required}
                        className={`w-full flex items-center gap-3 p-3.5 rounded-lg border text-left transition-colors ${on?'border-brand-400 bg-brand-50/50':'border-slate-200 hover:bg-slate-50'} ${r.required?'cursor-default':''}`}>
                        <span className={`w-5 h-5 rounded grid place-items-center shrink-0 ${on?'bg-brand-600 text-white':'border border-slate-300'}`}>{on && <Icon name="Check" size={13}/>}</span>
                        <div className="flex-1">
                          <div className="flex items-center gap-2"><span className="font-mono text-[13px] font-semibold text-slate-800">{r.name}</span>{r.required && <span className="text-[10px] px-1.5 py-px rounded bg-slate-100 text-slate-500">必选</span>}</div>
                          <div className="text-[12px] text-slate-400 mt-0.5">{r.desc}</div>
                        </div>
                      </button>
                    );
                  })}
                </div>
                <div className="flex items-start gap-2 text-[11.5px] text-slate-400 bg-slate-50 rounded-md px-3 py-2"><Icon name="Info" size={13} className="shrink-0 mt-0.5"/>已选 {f.rules.length} 项。区域规则按建设地点「{f.location}」自动推荐。</div>
              </div>
            )}

            {/* Step 3 */}
            {step===3 && (
              <div className="space-y-5">
                <div><h2 className="text-[16px] font-semibold text-slate-800">录入关键事实</h2><p className="text-[12.5px] text-slate-400 mt-0.5">关键事实驱动计算器与表格。此处可先填核心项，其余可进入工作台后补充。</p></div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[['total','总占地面积','hm²','land.total_area'],['perm','永久占地','hm²','land.permanent_area'],['temp','临时占地','hm²','land.temporary_area'],['exc','挖方量','万m³','earthwork.excavation'],['fill','填方量','万m³','earthwork.fill'],['spoil','余方量','万m³','earthwork.spoil']].map(([k,label,unit,fid]) => (
                    <WzField key={k} label={label} hint={fid}>
                      <div className="relative">
                        <input value={f.facts[k]} onChange={e=>upFact(k,e.target.value)} placeholder="0.00" className={wzInput+' pr-12 font-mono tabular'}/>
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[11.5px] text-slate-400">{unit}</span>
                      </div>
                    </WzField>
                  ))}
                </div>
                <div className="flex items-start gap-2 text-[11.5px] text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2"><Icon name="TriangleAlert" size={13} className="shrink-0 mt-0.5"/>未填写的关键事实将在工作台中标记为「缺失」，对应表格生成为 SKELETON。</div>
              </div>
            )}

            {/* Step 4 */}
            {step===4 && (
              <div className="min-h-[320px] flex flex-col items-center justify-center text-center">
                {gen===0 && (
                  <>
                    <div className="w-16 h-16 rounded-full bg-brand-50 text-brand-600 grid place-items-center"><Icon name="Sparkles" size={30}/></div>
                    <h2 className="text-[17px] font-semibold text-slate-800 mt-4">准备生成报告骨架</h2>
                    <p className="text-[13px] text-slate-400 mt-2 max-w-[440px] leading-relaxed">系统将依据已录入的事实与所选规则集，生成报告章节骨架、正式表格骨架、义务清单与初始证据链。</p>
                    <div className="mt-5 grid grid-cols-2 gap-2.5 text-left w-full max-w-[440px]">
                      {[['项目名称',f.name||'未命名项目'],['项目类型',f.type],['规则集',f.rules.length+' 项'],['关键事实',Object.values(f.facts).filter(Boolean).length+' / 6 项']].map(([k,v]) => (
                        <div key={k} className="rounded-md bg-slate-50 border border-slate-100 px-3 py-2"><div className="text-[11px] text-slate-400">{k}</div><div className="text-[13px] text-slate-700 font-medium truncate">{v}</div></div>
                      ))}
                    </div>
                    <button onClick={runGenerate} className="mt-6 h-10 px-6 rounded-md bg-brand-600 text-white text-[14px] font-medium hover:bg-brand-700 inline-flex items-center gap-2"><Icon name="Sparkles" size={16}/>生成骨架</button>
                  </>
                )}
                {gen===1 && (
                  <>
                    <div className="w-16 h-16 rounded-full border-4 border-brand-100 border-t-brand-600 animate-spin"></div>
                    <h2 className="text-[16px] font-semibold text-slate-800 mt-5">正在生成…</h2>
                    <div className="mt-3 space-y-1.5 text-[12.5px] text-slate-500">
                      {['解析事实与规则集','生成 11 章报告骨架','生成 12 张正式表格骨架','建立义务清单与证据链'].map(t => (
                        <div key={t} className="flex items-center gap-2"><Icon name="Loader" size={13} className="text-brand-500 animate-spin"/>{t}</div>
                      ))}
                    </div>
                  </>
                )}
                {gen===2 && (
                  <>
                    <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 grid place-items-center"><Icon name="CircleCheck" size={32}/></div>
                    <h2 className="text-[17px] font-semibold text-slate-800 mt-4">骨架已生成</h2>
                    <p className="text-[13px] text-slate-400 mt-2 max-w-[420px]">已创建项目「{f.name||'未命名项目'}」，初始版本 v0.1。现在进入工作台继续填报事实、生成正文与表格。</p>
                    <div className="mt-4 flex items-center gap-4 text-[12px] text-slate-500">
                      <span className="inline-flex items-center gap-1"><Icon name="FileText" size={13} className="text-brand-500"/>11 章骨架</span>
                      <span className="inline-flex items-center gap-1"><Icon name="Table2" size={13} className="text-brand-500"/>12 表骨架</span>
                      <span className="inline-flex items-center gap-1"><Icon name="Gavel" size={13} className="text-brand-500"/>6 项义务</span>
                    </div>
                    <button onClick={finish} className="mt-6 h-10 px-6 rounded-md bg-teal-600 text-white text-[14px] font-medium hover:bg-teal-700 inline-flex items-center gap-2"><Icon name="ArrowRight" size={16}/>进入工作台</button>
                  </>
                )}
              </div>
            )}
          </div>

          {/* 底部导航 */}
          {!(step===4) && (
            <div className="flex items-center justify-between mt-5">
              <button onClick={()=> step===1?onCancel():setStep(step-1)} className="h-10 px-4 rounded-md border border-slate-300 bg-white text-[13.5px] text-slate-600 hover:bg-slate-50 inline-flex items-center gap-1.5"><Icon name="ArrowLeft" size={15}/>{step===1?'取消':'上一步'}</button>
              <div className="text-[12px] text-slate-400">第 {step} / 4 步</div>
              <button onClick={()=>canNext && setStep(step+1)} disabled={!canNext} className={`h-10 px-5 rounded-md text-[13.5px] font-medium inline-flex items-center gap-1.5 ${canNext?'bg-brand-600 text-white hover:bg-brand-700':'bg-slate-200 text-slate-400 cursor-not-allowed'}`}>下一步<Icon name="ArrowRight" size={15}/></button>
            </div>
          )}
          {step===4 && gen!==1 && (
            <div className="flex items-center justify-start mt-5">
              <button onClick={()=>{setStep(3);setGen(0);}} className="h-10 px-4 rounded-md border border-slate-300 bg-white text-[13.5px] text-slate-600 hover:bg-slate-50 inline-flex items-center gap-1.5"><Icon name="ArrowLeft" size={15}/>上一步</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

window.NewProjectWizard = NewProjectWizard;