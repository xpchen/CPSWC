// ===================================================================
// 工作空间：项目列表（我的项目） + 个人中心
// ===================================================================
const { USER: WS_USER, PROJECTS: WS_PROJECTS, OP_LOG: WS_OPLOG } = window.CPSWC;

function WorkspaceTopBar({ onAccount, onLogout, onHome, active }) {
  const [menu, setMenu] = useState(false);
  return (
    <header className="h-14 shrink-0 bg-brand-900 text-white flex items-center px-4 gap-4 relative z-30">
      <button onClick={onHome} className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded bg-gradient-to-br from-teal-500 to-brand-500 grid place-items-center font-bold text-[13px]">CP</div>
        <div className="leading-tight text-left">
          <div className="text-[13px] font-semibold tracking-wide">CPSWC</div>
          <div className="text-[10px] text-brand-300">水土保持方案智能编制与审查平台</div>
        </div>
      </button>
      <nav className="hidden md:flex items-center gap-1 ml-4">
        {[['workspace','我的项目','LayoutGrid'],['account','个人中心','UserCog']].map(([id,label,icon]) => (
          <button key={id} onClick={id==='account'?onAccount:onHome}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12.5px] transition-colors ${active===id?'bg-white/15 text-white':'text-brand-200 hover:bg-white/10'}`}>
            <Icon name={icon} size={14}/>{label}
          </button>
        ))}
      </nav>
      <div className="ml-auto flex items-center gap-2">
        <button className="w-8 h-8 rounded-md hover:bg-white/10 grid place-items-center text-brand-200"><Icon name="Bell" size={16}/></button>
        <div className="relative">
          <button onClick={()=>setMenu(m=>!m)} className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-md hover:bg-white/10">
            <span className="w-7 h-7 rounded-full bg-teal-600 grid place-items-center text-[12px] font-semibold">{WS_USER.initials}</span>
            <span className="text-[12.5px]">{WS_USER.name}</span>
            <Icon name="ChevronDown" size={14} className="text-brand-300"/>
          </button>
          {menu && (
            <>
              <div className="fixed inset-0 z-10" onClick={()=>setMenu(false)}></div>
              <div className="absolute right-0 mt-1.5 w-52 bg-white rounded-lg shadow-xl border border-slate-200 p-1.5 z-20 text-slate-700">
                <div className="px-2.5 py-2 border-b border-slate-100 mb-1">
                  <div className="text-[13px] font-medium text-slate-800">{WS_USER.fullName}</div>
                  <div className="text-[11px] text-slate-400">{WS_USER.email}</div>
                </div>
                <button onClick={()=>{setMenu(false);onAccount();}} className="w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-[12.5px] hover:bg-slate-50"><Icon name="UserCog" size={15} className="text-slate-400"/>个人中心 / 账户设置</button>
                <button className="w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-[12.5px] hover:bg-slate-50"><Icon name="HelpCircle" size={15} className="text-slate-400"/>帮助与标准库</button>
                <div className="h-px bg-slate-100 my-1"></div>
                <button onClick={onLogout} className="w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-[12.5px] hover:bg-red-50 text-red-600"><Icon name="LogOut" size={15}/>退出登录</button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

function ProjectCard({ p, onOpen }) {
  const pct = p.completeness;
  return (
    <button onClick={()=>onOpen(p)} className="text-left bg-white rounded-lg border border-slate-200 panel-shadow hover:border-brand-300 hover:shadow-md transition-all p-4 flex flex-col group">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <StatusTag status={p.frozen?'已冻结':p.status} dot/>
          {p.primary && <span className="text-[10px] px-1.5 py-px rounded bg-teal-50 text-teal-600 border border-teal-200">主项目</span>}
        </div>
        <Icon name="ArrowUpRight" size={16} className="text-slate-300 group-hover:text-brand-500 transition-colors"/>
      </div>
      <h3 className="mt-2.5 text-[15px] font-semibold text-slate-800 leading-snug">{p.name}</h3>
      <div className="mt-1 text-[11px] font-mono text-slate-400">{p.code}</div>
      <div className="mt-2.5 flex items-center gap-3 text-[11.5px] text-slate-500">
        <span className="inline-flex items-center gap-1"><Icon name="MapPin" size={12} className="text-slate-400"/>{p.location}</span>
        <span className="inline-flex items-center gap-1"><Icon name="Tag" size={12} className="text-slate-400"/>{p.type}</span>
      </div>
      {/* 进度 */}
      <div className="mt-3">
        <div className="flex items-center justify-between text-[10.5px] text-slate-400 mb-1"><span>完成度</span><span className="tabular font-medium text-slate-600">{pct}%</span></div>
        <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden"><div className={`h-full ${pct===100?'bg-emerald-500':pct>=70?'bg-brand-500':'bg-amber-500'}`} style={{width:pct+'%'}}></div></div>
      </div>
      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
        <span className="inline-flex items-center gap-1"><Icon name="UserCheck" size={12}/>我的角色：<b className="text-slate-600 font-medium">{p.role}</b></span>
        <span className="font-mono">{p.version}</span>
      </div>
      <div className="mt-1.5 flex items-center justify-between text-[10.5px] text-slate-400">
        <span className="inline-flex items-center gap-1"><Icon name="Users" size={11}/>{p.members} 名成员</span>
        <span>{p.blockers>0 && <span className="text-red-500 mr-2">阻塞 {p.blockers}</span>}更新于 {p.updated}</span>
      </div>
    </button>
  );
}

function WorkspaceView({ onOpen, onNew, onAccount, onLogout }) {
  const [filter, setFilter] = useState('全部');
  const [q, setQ] = useState('');
  const [intakeOpen, setIntakeOpen] = useState(false);
  const FILTERS = ['全部','进行中','已交付','我编制','我审查'];
  let list = WS_PROJECTS.filter(p => {
    if (filter==='进行中') return !p.frozen;
    if (filter==='已交付') return p.frozen;
    if (filter==='我编制') return p.role==='编制人员';
    if (filter==='我审查') return p.role==='审查专家';
    return true;
  });
  if (q.trim()) list = list.filter(p => (p.name+p.code+p.location).includes(q.trim()));

  const stats = [
    { k:'项目总数', v:WS_PROJECTS.length, icon:'FolderKanban', tone:'text-brand-700' },
    { k:'进行中', v:WS_PROJECTS.filter(p=>!p.frozen).length, icon:'Loader', tone:'text-amber-600' },
    { k:'已交付', v:WS_PROJECTS.filter(p=>p.frozen).length, icon:'PackageCheck', tone:'text-emerald-600' },
    { k:'待我处理', v:WS_PROJECTS.reduce((a,p)=>a+p.expert,0), icon:'BellRing', tone:'text-orange-600' },
  ];

  return (
    <div className="h-full flex flex-col">
      <WorkspaceTopBar onAccount={onAccount} onLogout={onLogout} onHome={()=>{}} active="workspace" />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[1200px] mx-auto p-6">
          {/* 头部 */}
          <div className="flex items-end justify-between flex-wrap gap-3">
            <div>
              <h1 className="text-[22px] font-bold text-slate-800">我的项目</h1>
              <p className="text-[13px] text-slate-400 mt-1">欢迎回来，{WS_USER.name}。您参与与创建的水土保持方案项目都在这里。</p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={()=>setIntakeOpen(true)} className="inline-flex items-center gap-2 h-10 px-4 rounded-md bg-gradient-to-r from-teal-500 to-brand-600 text-white text-[13.5px] font-medium hover:opacity-90 transition-opacity shadow-sm">
                <Icon name="Sparkles" size={16}/>智能向导新建
              </button>
              <button onClick={onNew} className="inline-flex items-center gap-2 h-10 px-4 rounded-md bg-white border border-slate-200 text-slate-700 text-[13.5px] font-medium hover:bg-slate-50 transition-colors">
                <Icon name="Plus" size={16}/>手动新建
              </button>
            </div>
          </div>

          {/* 统计 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
            {stats.map(s => (
              <div key={s.k} className="bg-white rounded-lg border border-slate-200 panel-shadow p-4 flex items-center gap-3">
                <span className="w-10 h-10 rounded-lg bg-slate-50 grid place-items-center text-slate-400"><Icon name={s.icon} size={19}/></span>
                <div><div className={`text-[24px] font-bold tabular leading-none ${s.tone}`}>{s.v}</div><div className="text-[11.5px] text-slate-400 mt-1">{s.k}</div></div>
              </div>
            ))}
          </div>

          {/* 工具条 */}
          <div className="flex items-center justify-between gap-3 mt-6 flex-wrap">
            <div className="flex items-center gap-1 bg-white rounded-md border border-slate-200 p-0.5">
              {FILTERS.map(f => (
                <button key={f} onClick={()=>setFilter(f)} className={`text-[12.5px] px-3 py-1.5 rounded transition-colors ${filter===f?'bg-brand-600 text-white':'text-slate-500 hover:bg-slate-50'}`}>{f}</button>
              ))}
            </div>
            <div className="relative">
              <Icon name="Search" size={15} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400"/>
              <input value={q} onChange={e=>setQ(e.target.value)} placeholder="搜索项目名称 / 编号 / 地点"
                className="h-9 w-64 rounded-md border border-slate-200 bg-white text-[12.5px] pl-8 pr-3 focus:outline-none focus:ring-2 focus:ring-brand-300"/>
            </div>
          </div>

          {/* 卡片网格 */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-4">
            {/* 智能向导新建占位卡（推荐） */}
            <button onClick={()=>setIntakeOpen(true)} className="rounded-lg border-2 border-dashed border-teal-300 hover:border-teal-500 bg-gradient-to-br from-teal-50/40 to-brand-50/30 hover:from-teal-50 hover:to-brand-50 transition-colors p-4 flex flex-col items-center justify-center min-h-[210px] text-slate-500 hover:text-brand-700 group relative">
              <span className="absolute top-2 right-2 px-1.5 py-0.5 rounded text-[10px] font-medium bg-teal-500 text-white">推荐</span>
              <span className="w-12 h-12 rounded-full bg-gradient-to-br from-teal-100 to-brand-100 group-hover:from-teal-200 group-hover:to-brand-200 grid place-items-center transition-colors text-teal-600"><Icon name="Sparkles" size={24}/></span>
              <span className="mt-3 text-[13.5px] font-medium">智能向导新建</span>
              <span className="mt-1 text-[11.5px] text-center">上传红线图/施工图/PDF<br/>AI 识别 · 提取候选事实 · 引导补齐</span>
            </button>
            {/* 手动新建占位卡 */}
            <button onClick={onNew} className="rounded-lg border-2 border-dashed border-slate-300 hover:border-brand-400 hover:bg-brand-50/30 transition-colors p-4 flex flex-col items-center justify-center min-h-[210px] text-slate-400 hover:text-brand-600 group">
              <span className="w-12 h-12 rounded-full bg-slate-100 group-hover:bg-brand-100 grid place-items-center transition-colors"><Icon name="Plus" size={24}/></span>
              <span className="mt-3 text-[13.5px] font-medium">手动新建项目</span>
              <span className="mt-1 text-[11.5px]">逐项填写事实 → 选规则集 → 生成骨架</span>
            </button>
            {list.map(p => <ProjectCard key={p.id} p={p} onOpen={onOpen} />)}
          </div>
          {list.length===0 && <div className="text-center text-slate-400 text-[13px] py-10">没有匹配的项目</div>}
        </div>
      </main>
      {window.IntakeWizard && <window.IntakeWizard open={intakeOpen} onClose={()=>setIntakeOpen(false)} onNavigate={()=>{ setIntakeOpen(false); onNew && onNew(); }} />}
    </div>
  );
}

function AccountView({ onBack, onLogout }) {
  const [tab, setTab] = useState('profile');
  const u = WS_USER;
  return (
    <div className="h-full flex flex-col">
      <WorkspaceTopBar onAccount={()=>{}} onLogout={onLogout} onHome={onBack} active="account" />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[1000px] mx-auto p-6">
          <button onClick={onBack} className="text-[12.5px] text-slate-400 hover:text-slate-600 inline-flex items-center gap-1 mb-4"><Icon name="ArrowLeft" size={14}/>返回我的项目</button>
          {/* 头卡 */}
          <div className="bg-white rounded-lg border border-slate-200 panel-shadow p-5 flex items-center gap-4">
            <span className="w-16 h-16 rounded-full bg-gradient-to-br from-teal-500 to-brand-600 grid place-items-center text-white text-[24px] font-bold">{u.initials}</span>
            <div className="flex-1">
              <div className="text-[18px] font-bold text-slate-800">{u.fullName}</div>
              <div className="text-[12.5px] text-slate-400">{u.title} · {u.org}</div>
              <div className="mt-1.5 flex items-center gap-3 text-[11.5px] text-slate-400">
                <span className="inline-flex items-center gap-1"><Icon name="Mail" size={12}/>{u.email}</span>
                <span className="inline-flex items-center gap-1"><Icon name="Clock" size={12}/>上次登录 {u.lastLogin}</span>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="mt-5 flex gap-1 border-b border-slate-200">
            {[['profile','账户信息','User'],['security','安全设置','ShieldCheck'],['log','我的操作记录','History']].map(([id,label,icon]) => (
              <button key={id} onClick={()=>setTab(id)} className={`flex items-center gap-1.5 px-4 py-2.5 text-[13px] transition-colors ${tab===id?'text-brand-600 border-b-2 border-brand-600 font-medium':'text-slate-500 hover:text-slate-700'}`}><Icon name={icon} size={14}/>{label}</button>
            ))}
          </div>

          <div className="mt-5">
            {tab==='profile' && (
              <Panel title="账户信息" sub="基本资料（演示环境，修改不会持久化）">
                <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[['姓名',u.fullName,'User'],['机构邮箱',u.email,'Mail'],['手机号',u.phone,'Phone'],['所属单位',u.org,'Building2'],['职务',u.title,'Briefcase'],['加入时间',u.joined,'CalendarDays']].map(([k,v,icon]) => (
                    <label key={k} className="block">
                      <span className="text-[12px] text-slate-500">{k}</span>
                      <div className="mt-1 relative">
                        <Icon name={icon} size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/>
                        <input defaultValue={v} className="w-full h-9 rounded-md border border-slate-300 text-[13px] pl-9 pr-3 focus:outline-none focus:ring-2 focus:ring-brand-300"/>
                      </div>
                    </label>
                  ))}
                  <div className="md:col-span-2"><button className="h-9 px-4 rounded-md bg-brand-600 text-white text-[13px] hover:bg-brand-700">保存修改</button></div>
                </div>
              </Panel>
            )}
            {tab==='security' && (
              <Panel title="安全设置">
                <div className="divide-y divide-slate-100">
                  {[['登录密码','上次修改于 2026-05-10','修改密码'],['两步验证','未开启，建议开启以提升安全','去开启'],['登录设备','当前 2 台设备已登录','管理设备']].map(([k,d,btn]) => (
                    <div key={k} className="flex items-center justify-between px-5 py-3.5">
                      <div><div className="text-[13.5px] text-slate-700 font-medium">{k}</div><div className="text-[12px] text-slate-400 mt-0.5">{d}</div></div>
                      <button className="text-[12.5px] px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50">{btn}</button>
                    </div>
                  ))}
                </div>
              </Panel>
            )}
            {tab==='log' && (
              <Panel title="我的操作记录" sub="跨项目的全部动作（最近）">
                <div className="divide-y divide-slate-100">
                  {WS_OPLOG.map((o,i) => (
                    <div key={i} className="flex items-center gap-3 px-5 py-3">
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
      </main>
    </div>
  );
}

Object.assign(window, { WorkspaceView, AccountView });