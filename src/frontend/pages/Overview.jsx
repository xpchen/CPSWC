// ===================================================================
// 共享：页面头 + 页 1 项目总览
// ===================================================================
const { PROJECT: OP, SIX_RATES: OSR, RECENT_CHANGES: ORC, TODOS: OTD } = window.CPSWC;

function PageHeader({ title, sub, icon, children }) {
  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-white/60 backdrop-blur sticky top-0 z-20">
      <div className="flex items-center gap-3">
        {icon && <span className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 grid place-items-center"><Icon name={icon} size={19}/></span>}
        <div>
          <h1 className="text-[17px] font-semibold text-slate-800 leading-tight">{title}</h1>
          {sub && <p className="text-[12px] text-slate-400 mt-0.5">{sub}</p>}
        </div>
      </div>
      <div className="flex items-center gap-2">{children}</div>
    </div>
  );
}
window.PageHeader = PageHeader;

// 角色重点提示条
function RoleBanner({ role }) {
  const map = {
    editor:   { icon:'PencilRuler', tone:'bg-brand-50 border-brand-200 text-brand-700', text:'编制视图 · 重点关注：待补充字段（年度投资分配）与正文/表格生成进度。' },
    reviewer: { icon:'ShieldCheck', tone:'bg-orange-50 border-orange-200 text-orange-700', text:'审查视图 · 重点关注：2 项专家确认、规则触发与标准依据、数文一致性风险。' },
    manager:  { icon:'ClipboardList', tone:'bg-teal-50 border-teal-200 text-teal-700', text:'负责人视图 · 重点关注：总体完成度 91%、0 阻塞项、交付包未冻结。' },
  };
  const m = map[role] || map.editor;
  return (
    <div className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg border text-[12.5px] ${m.tone}`}>
      <Icon name={m.icon} size={16} className="shrink-0"/>
      <span className="leading-snug">{m.text}</span>
    </div>
  );
}

function RateBar({ r }) {
  const pct = parseFloat(r.actual);
  const tgt = parseFloat(r.target);
  const isPct = r.actual.includes('%');
  const w = isPct ? pct : Math.min(100, pct * 90);
  return (
    <div className="py-2">
      <div className="flex items-center justify-between text-[12px] mb-1">
        <span className="text-slate-600">{r.name}</span>
        <span className="tabular text-slate-400">目标 <b className="text-slate-600">{r.target}</b> · 预测 <b className="text-emerald-600">{r.actual}</b></span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 overflow-hidden relative">
        <div className="h-full rounded-full bg-emerald-500/80" style={{ width: w + '%' }}></div>
        {isPct && <div className="absolute top-0 h-full w-px bg-slate-400" style={{ left: tgt + '%' }} title="目标线"></div>}
      </div>
    </div>
  );
}

function OverviewPage({ role, setPage }) {
  const cards = [
    { label:'事实完整度', value:'94', unit:'%', status:'通过', accent:'emerald', note:'关键事实已满足生成要求' },
    { label:'表格生成率', value:'88', unit:'%', status:'待确认', accent:'amber', note:'年度投资表仍为骨架（SKELETON）' },
    { label:'正文覆盖率', value:'92', unit:'%', status:'可生成', accent:'brand', note:'主要章节已生成，可预览' },
    { label:'导出状态',   value:'可生成', unit:'', status:'通过', accent:'emerald', note:'无阻塞项，存在 2 项专家确认' },
  ];
  return (
    <div>
      <PageHeader title="项目总览" sub="项目状态 · 完成度 · 阻塞项 · 关键结果 · 最近修改" icon="LayoutDashboard">
        <button className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-600"><Icon name="RefreshCw" size={14}/>重新计算</button>
        <button onClick={()=>setPage('delivery')} className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700"><Icon name="Package" size={14}/>前往交付</button>
      </PageHeader>

      <div className="p-6 space-y-5 max-w-[1400px]">
        {/* 当前项目生产状态总览（演示冲击区） */}
        <div className="rounded-xl overflow-hidden border border-brand-800 bg-brand-900 text-white relative">
          <div className="absolute inset-0 opacity-[0.06]" style={{ backgroundImage:'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize:'34px 34px' }}></div>
          <div className="relative px-6 py-5">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2.5">
                <span className="w-9 h-9 rounded-lg bg-white/10 grid place-items-center"><Icon name="Gauge" size={20}/></span>
                <div>
                  <div className="text-[16px] font-semibold tracking-wide">当前项目生产状态总览</div>
                  <div className="text-[12px] text-brand-300">世维华南供应链（二期）· 事实驱动 · 规则可追踪 · 数文一致</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1 rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 whitespace-nowrap"><Icon name="ShieldCheck" size={14}/>无导出阻塞</span>
                <span className="inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1 rounded-md bg-orange-500/15 text-orange-200 border border-orange-500/30 whitespace-nowrap"><Icon name="UserCheck" size={14}/>2 项专家确认</span>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-3 md:grid-cols-6 gap-px bg-white/10 rounded-lg overflow-hidden">
              {[
                ['正文段落','32','FileText'],['报告表格','23','Table2'],['计算结果','6','Calculator'],
                ['审查义务','12','Gavel'],['依据注脚','18','BookMarked'],['交付包','1','Package'],
              ].map(([k,v,icon]) => (
                <div key={k} className="bg-brand-900/60 px-3 py-3 text-center">
                  <Icon name={icon} size={15} className="text-brand-300 mx-auto mb-1.5"/>
                  <div className="text-[26px] font-bold tabular leading-none text-white">{v}</div>
                  <div className="text-[11px] text-brand-300 mt-1.5">{k}</div>
                </div>
              ))}
            </div>

            <div className="mt-4 flex items-start gap-2.5">
              <div className="flex-1 flex items-center gap-2 text-[12.5px] text-brand-100 bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5">
                <Icon name="Link2" size={16} className="text-teal-300 shrink-0"/>
                所有正文、表格、计算结果和审查结论均可追溯到<b className="text-white">项目事实</b>、<b className="text-white">规则依据</b>和<b className="text-white">计算器结果</b>。
              </div>
              <div className="hidden lg:flex items-center gap-2 shrink-0">
                {[['可追溯','GitBranch'],['数文一致','Equal'],['可导出','PackageCheck']].map(([t,i]) => (
                  <span key={t} className="inline-flex items-center gap-1.5 text-[12px] px-3 py-2.5 rounded-lg bg-teal-500/15 text-teal-200 border border-teal-500/30"><Icon name={i} size={14}/>{t}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <RoleBanner role={role} />

        {/* 四状态卡 */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map(c => <MetricCard key={c.label} {...c} />)}
        </div>

        {/* 资料收集状态 */}
        <Panel title="资料收集状态" sub="智能收资向导汇总" right={<button onClick={()=>setPage('facts')} className="text-[11.5px] text-brand-600 hover:underline inline-flex items-center gap-1">事实填报<Icon name="ArrowRight" size={12}/></button>}>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-px bg-slate-100">
            {[
              ['已上传资料','4','份','FolderOpen','text-brand-700'],
              ['已确认事实','42','项','Database','text-emerald-600'],
              ['候选待确认','7','项','CircleHelp','text-orange-600'],
              ['缺失资料','5','项','PackageSearch','text-amber-600'],
              ['已登记图件','6','张','Map','text-teal-600'],
              ['可生成图件','3','张','MapPlus','text-brand-600'],
            ].map(([k,v,u,icon,tone]) => (
              <div key={k} className="bg-white p-3.5">
                <div className="flex items-center gap-1.5 text-[11px] text-slate-400"><Icon name={icon} size={12}/>{k}</div>
                <div className="mt-1 flex items-baseline gap-1"><span className={`text-[22px] font-bold tabular ${tone}`}>{v}</span><span className="text-[11px] text-slate-400">{u}</span></div>
              </div>
            ))}
          </div>
          <div className="px-4 py-2.5 text-[12px] text-slate-500 border-t border-slate-100 flex items-start gap-1.5">
            <Icon name="Info" size={13} className="text-slate-400 shrink-0 mt-0.5"/>当前项目资料已覆盖项目基本信息、占地与土石方、投资估算和部分图件来源；年度投资分配、措施布局图和监测点位资料仍需补充。
          </div>
        </Panel>

        {/* 概况 + 关键指标 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Panel title="项目概况" sub="基础事实快照" right={<button onClick={()=>setPage('facts')} className="text-[11.5px] text-brand-600 hover:underline inline-flex items-center gap-1">查看事实<Icon name="ArrowRight" size={12}/></button>}>
            <div className="px-4 py-2">
              <Field k="项目名称" v={OP.name} />
              <Field k="建设单位" v={OP.org} />
              <Field k="项目类型" v={OP.type} />
              <Field k="所在区域" v={OP.location} />
              <Field k="防治责任范围" v={`${OP.scopeArea} hm²`} mono />
              <Field k="规则集" v={OP.rulesets.slice(0,2).join(' / ')} />
              <div className="flex items-center justify-between pt-2 mt-1">
                <span className="text-[12px] text-slate-400">当前状态</span>
                <StatusTag status="可生成" dot />
              </div>
            </div>
          </Panel>

          <Panel title="关键指标" sub="计算器与规则输出">
            <div className="grid grid-cols-2 gap-px bg-slate-100">
              {[
                { k:'水土保持补偿费', v:'4.248', u:'万元', tone:'text-brand-700' },
                { k:'防治责任范围', v:'3.54', u:'hm²', tone:'text-slate-800' },
                { k:'预测土壤流失量', v:'128.6', u:'t', tone:'text-slate-800' },
                { k:'是否涉及弃渣场', v:'否', u:'', tone:'text-slate-500' },
                { k:'是否跨行政区', v:'否', u:'', tone:'text-slate-500' },
                { k:'需要专家确认', v:'2', u:'项', tone:'text-orange-600' },
              ].map(m => (
                <div key={m.k} className="bg-white p-3.5">
                  <div className="text-[11.5px] text-slate-400">{m.k}</div>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className={`text-[22px] font-bold tabular ${m.tone}`}>{m.v}</span>
                    <span className="text-[11px] text-slate-400">{m.u}</span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* 六率 + 待办 */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          <Panel className="lg:col-span-3" title="六率目标概览" sub="GB/T 50434-2018 防治目标" right={<StatusTag status="已计算" dot/>}>
            <div className="px-4 py-1.5">
              {OSR.map(r => <RateBar key={r.name} r={r} />)}
            </div>
          </Panel>

          <Panel className="lg:col-span-2" title="风险 / 待办" sub="非阻塞提示 4 项" right={<button onClick={()=>setPage('rules')} className="text-[11.5px] text-brand-600 hover:underline">规则审查</button>}>
            <div className="p-3 space-y-2">
              {OTD.map((t,i) => (
                <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-md border border-slate-100 bg-slate-50/50">
                  <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                    t.tone==='emerald'?'bg-emerald-500':t.tone==='amber'?'bg-amber-500':t.tone==='orange'?'bg-orange-500':'bg-brand-500'}`}></span>
                  <span className="text-[12.5px] text-slate-600 leading-snug flex-1">{t.text}</span>
                  <StatusTag status={t.tag} />
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* 最近修改 */}
        <Panel title="最近修改记录" sub="字段变更及其影响范围" right={<button onClick={()=>setPage('changes')} className="text-[11.5px] text-brand-600 hover:underline inline-flex items-center gap-1">改动追踪<Icon name="ArrowRight" size={12}/></button>}>
          <table className="w-full text-[12.5px]">
            <thead>
              <tr className="text-[11px] text-slate-400 border-b border-slate-100">
                <th className="text-left font-medium px-4 py-2">修改字段</th>
                <th className="text-left font-medium px-2 py-2">修改前</th>
                <th className="text-left font-medium px-2 py-2">修改后</th>
                <th className="text-left font-medium px-2 py-2">修改人</th>
                <th className="text-left font-medium px-2 py-2">时间</th>
                <th className="text-left font-medium px-4 py-2">影响范围</th>
              </tr>
            </thead>
            <tbody>
              {ORC.map((c,i) => (
                <tr key={i} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                  <td className="px-4 py-2.5"><Chip tone="brand">{c.field}</Chip></td>
                  <td className="px-2 py-2.5 font-mono text-slate-400 tabular">{c.before} {c.unit}</td>
                  <td className="px-2 py-2.5 font-mono text-slate-800 tabular">→ {c.after} {c.unit}</td>
                  <td className="px-2 py-2.5 text-slate-500">{c.by}</td>
                  <td className="px-2 py-2.5 text-slate-400">{c.time}</td>
                  <td className="px-4 py-2.5 text-slate-500">{c.impact}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>
    </div>
  );
}

window.OverviewPage = OverviewPage;
