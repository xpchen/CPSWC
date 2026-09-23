// ===================================================================
// CPSWC — App Shell（顶部栏 / 角色 / 左侧导航 / 路由）
// ===================================================================
const { PROJECT: P, ROLES: APP_ROLES, NAV: APP_NAV } = window.CPSWC;
const { DATA_MODE, IS_SNAPSHOT, PAYLOAD, PAYLOAD_PROBLEMS } = window.CPSWC;

// ---------- F-1B 全局数据模式条 ----------
// 用户必须一眼看出"这是真项目快照 / 这是演示数据 / 这份数据有问题"。
function DataModeBar() {
  if (DATA_MODE === 'DEMO') {
    return (
      <div className="h-7 shrink-0 flex items-center justify-center gap-2 text-[11.5px] font-medium
        text-amber-900 border-b border-amber-300"
        style={{background:'repeating-linear-gradient(45deg,#fde68a,#fde68a 10px,#fcd34d 10px,#fcd34d 20px)'}}>
        <Icon name="TriangleAlert" size={13}/>
        演示数据 — 本界面显示的全部数值均为示例，不来自任何真实项目
      </div>
    );
  }
  const h = PAYLOAD.hashes.generation_input_hash;
  return (
    <div className="h-7 shrink-0 flex items-center gap-3 px-3 text-[11.5px] bg-brand-950 text-brand-100 border-b border-brand-800">
      <span className="inline-flex items-center gap-1.5 font-medium"><Icon name="Camera" size={13}/>项目快照</span>
      <span className="text-brand-300">{PAYLOAD.project.name || '(项目名称未填)'}</span>
      <span className="text-brand-400">生成于 {new Date(PAYLOAD.generated_at).toLocaleString('zh-CN')}</span>
      <span className="ml-auto font-mono text-brand-400" title="generation_input_hash">{h.slice(0,16)}</span>
      <span className="text-brand-400">静态快照，非实时数据</span>
    </div>
  );
}

// ---------- F-1B 未接线页面提示 ----------
// 快照模式下, 尚未接到 payload 的页面必须自曝。否则用户看到顶栏是真项目,
// 就会默认整个界面都是这个项目的数据 —— 而页面里其实还是示例工程。
function UnwiredNotice({ pageKey }) {
  if (!IS_SNAPSHOT) return null;
  if ((window.CPSWC.WIRED_PAGES || []).includes(pageKey)) return null;
  return (
    <div className="mx-4 mt-3 rounded border border-amber-300 bg-amber-50 px-3 py-2
      text-[12px] text-amber-900 flex items-start gap-2">
      <Icon name="TriangleAlert" size={14} className="mt-0.5 shrink-0"/>
      <span>
        <b>本页尚未接入项目数据。</b>
        以下内容仍是示例工程的演示数据，与顶栏所示项目无关，不可作为该项目的依据。
      </span>
    </div>
  );
}

// ---------- F-1B payload 错误阻断页 ----------
// **绝不回落 mock。** 半真半演示比完全没有数据更危险。
function PayloadErrorPage() {
  return (
    <div className="min-h-screen bg-slate-100 grid place-items-center p-8">
      <div className="max-w-2xl bg-white rounded-lg border border-rose-300 shadow-sm overflow-hidden">
        <div className="bg-rose-600 text-white px-5 py-3 flex items-center gap-2">
          <Icon name="OctagonAlert" size={18}/>
          <span className="font-semibold text-[15px]">数据包无法加载</span>
        </div>
        <div className="p-5 text-[13px] text-slate-700 space-y-3">
          <p>检测到项目数据包（payload），但它未通过校验。
             为避免把演示数据和真实数据混在一起显示，界面已停止加载。</p>
          <ul className="list-disc pl-5 space-y-1 text-rose-700">
            {PAYLOAD_PROBLEMS.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
          <p className="text-slate-500 text-[12px] pt-2 border-t border-slate-200">
            请用 <code className="font-mono bg-slate-100 px-1">python -m cpswc.frontend_payload &lt;项目.json&gt;</code>
            重新生成，并使用生成出来的整个目录，不要把新 payload 拷进旧的界面副本。
          </p>
        </div>
      </div>
    </div>
  );
}

function TopBar({ role, setRole, frozen, setFrozen, completeness, projectName, onExit, onAccount, onLogout, onIntake }) {
  const [roleOpen, setRoleOpen] = useState(false);
  const [acctOpen, setAcctOpen] = useState(false);
  const cur = APP_ROLES.find(r => r.id === role);
  const U = window.CPSWC.USER;
  return (
    <header className="h-14 shrink-0 bg-brand-900 text-white flex items-center pl-3 pr-3 gap-4 border-b border-brand-950 relative z-30">
      {/* 返回 + Logo + 名称 */}
      <div className="flex items-center gap-2.5">
        <button onClick={onExit} title="返回我的项目" className="w-8 h-8 rounded hover:bg-white/10 grid place-items-center text-brand-200 shrink-0"><Icon name="ArrowLeft" size={17}/></button>
        <button onClick={onExit} className="w-8 h-8 rounded bg-gradient-to-br from-teal-500 to-brand-500 grid place-items-center font-bold text-[13px] tracking-tight shadow-inner shrink-0">
          CP
        </button>
        <div className="leading-tight">
          <div className="text-[13px] font-semibold tracking-wide">CPSWC <span className="text-brand-200 font-normal hidden 2xl:inline">水土保持方案智能编制与审查平台</span></div>
          <div className="text-[11px] text-brand-300 flex items-center gap-1.5"><Icon name="FolderClosed" size={11}/>{projectName || P.name}</div>
        </div>
      </div>

      {/* 中部：阶段 / 规则集 / 冻结 / 完成度 */}
      <div className="hidden xl:flex items-center gap-5 ml-4 pl-5 border-l border-white/10 text-[11.5px]">
        <div className="flex flex-col">
          <span className="text-brand-300">当前阶段</span>
          <span className="text-brand-50 font-medium">{P.phase}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-brand-300">规则集版本</span>
          <span className="text-brand-50 font-medium font-mono">{P.rulesetVersion}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-brand-300">冻结状态</span>
          {IS_SNAPSHOT ? (
            /* 快照模式禁止本地假冻结 —— 原实现的"冻结"只改浏览器状态, 什么也没冻 */
            <span className="font-medium inline-flex items-center gap-1 text-brand-300" title="冻结能力未实现">
              <Icon name="Minus" size={11}/>未实现
            </span>
          ) : (
            <span className={`font-medium inline-flex items-center gap-1 ${frozen ? 'text-emerald-300' : 'text-amber-300'}`}>
              <Icon name={frozen ? 'Lock' : 'LockOpen'} size={11}/>{frozen ? '已冻结' : '未冻结'}
            </span>
          )}
        </div>
        <div className="flex flex-col min-w-[150px]">
          {/* **不显示单一完成度百分比。** 覆盖率必须四行分开看, 压成一个数就会
              重新制造"91% 接近完成"的错觉 */}
          <span className="text-brand-300">内容完成度</span>
          <span className="text-brand-50 font-medium text-[11px]">
            {IS_SNAPSHOT ? (P.coverageDisplay || '未判定') : `演示 ${completeness}%`}
          </span>
        </div>
      </div>

      {/* 右侧 */}
      <div className="ml-auto flex items-center gap-2">
        <button disabled={IS_SNAPSHOT}
          title={IS_SNAPSHOT ? '预览生成能力未实现' : ''}
          className={`hidden lg:inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1.5 rounded transition-colors
            ${IS_SNAPSHOT ? 'bg-white/5 text-brand-400 cursor-not-allowed' : 'bg-white/10 hover:bg-white/15'}`}>
          <Icon name="Eye" size={14}/>生成预览
        </button>
        <button onClick={() => { if (!IS_SNAPSHOT) setFrozen(f => !f); }}
          disabled={IS_SNAPSHOT}
          title={IS_SNAPSHOT ? '冻结能力未实现（原按钮只改浏览器本地状态）' : ''}
          className={`hidden lg:inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1.5 rounded transition-colors
            ${IS_SNAPSHOT ? 'bg-white/5 text-brand-400 cursor-not-allowed' : 'bg-white/10 hover:bg-white/15'}`}>
          <Icon name={frozen ? 'LockOpen' : 'Lock'} size={14}/>{IS_SNAPSHOT ? '冻结版本（未实现）' : (frozen ? '解冻' : '冻结版本')}
        </button>
        <button onClick={onIntake} className="inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1.5 rounded bg-white/10 hover:bg-white/15 transition-colors">
          <Icon name="Sparkles" size={14}/>智能收资向导
        </button>
        {/* P0-08 未实现: 没有草稿/正式之分。门禁 BLOCK 时更不能让它看起来可点。 */}
        <button disabled={IS_SNAPSHOT}
          title={IS_SNAPSHOT ? '正式发布能力未实现（P0-08）' : ''}
          className={`inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded transition-colors font-medium
            ${IS_SNAPSHOT ? 'bg-white/5 text-brand-400 cursor-not-allowed' : 'bg-teal-500 hover:bg-teal-600'}`}>
          <Icon name="Package" size={14}/>{IS_SNAPSHOT ? '导出交付包（未实现）' : '导出交付包'}
        </button>

        {/* 角色切换 */}
        <div className="relative ml-1">
          <button onClick={() => setRoleOpen(o => !o)}
            className="flex items-center gap-2 pl-2 pr-2.5 py-1 rounded bg-white/10 hover:bg-white/15 transition-colors">
            <span className="w-7 h-7 rounded-full bg-brand-700 grid place-items-center"><Icon name={cur.icon} size={15}/></span>
            <span className="text-left leading-tight">
              <span className="block text-[12px] font-medium">{cur.name}</span>
              <span className="block text-[10px] text-brand-300">切换角色</span>
            </span>
            <Icon name="ChevronDown" size={14} className="text-brand-300"/>
          </button>
          {roleOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setRoleOpen(false)}></div>
              <div className="absolute right-0 mt-1.5 w-64 bg-white rounded-lg shadow-xl border border-slate-200 p-1.5 z-20 text-slate-700">
                {APP_ROLES.map(r => (
                  <button key={r.id} onClick={() => { setRole(r.id); setRoleOpen(false); }}
                    className={`w-full flex items-start gap-2.5 p-2 rounded-md text-left transition-colors ${role === r.id ? 'bg-brand-50' : 'hover:bg-slate-50'}`}>
                    <span className={`w-8 h-8 rounded-md grid place-items-center shrink-0 ${role === r.id ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
                      <Icon name={r.icon} size={16}/>
                    </span>
                    <span className="leading-tight">
                      <span className="flex items-center gap-1.5 text-[13px] font-medium text-slate-800">{r.name}
                        {role === r.id && <Icon name="Check" size={13} className="text-brand-600"/>}</span>
                      <span className="block text-[11px] text-slate-400 mt-0.5">{r.desc}</span>
                    </span>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {/* 账户菜单 */}
        <div className="relative">
          <button onClick={() => setAcctOpen(o => !o)} className="flex items-center gap-1.5 pl-1 pr-1.5 py-1 rounded bg-white/10 hover:bg-white/15 transition-colors">
            <span className="w-7 h-7 rounded-full bg-teal-600 grid place-items-center text-[12px] font-semibold">{U.initials}</span>
            <Icon name="ChevronDown" size={14} className="text-brand-300"/>
          </button>
          {acctOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setAcctOpen(false)}></div>
              <div className="absolute right-0 mt-1.5 w-52 bg-white rounded-lg shadow-xl border border-slate-200 p-1.5 z-20 text-slate-700">
                <div className="px-2.5 py-2 border-b border-slate-100 mb-1">
                  <div className="text-[13px] font-medium text-slate-800">{U.fullName}</div>
                  <div className="text-[11px] text-slate-400">{U.email}</div>
                </div>
                <button onClick={() => { setAcctOpen(false); onExit && onExit(); }} className="w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-[12.5px] hover:bg-slate-50"><Icon name="LayoutGrid" size={15} className="text-slate-400"/>返回我的项目</button>
                <button onClick={() => { setAcctOpen(false); onAccount && onAccount(); }} className="w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-[12.5px] hover:bg-slate-50"><Icon name="UserCog" size={15} className="text-slate-400"/>个人中心 / 账户设置</button>
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

function SideNav({ page, setPage, role }) {
  // 不同角色高亮的导航
  const roleFocus = {
    editor:   ['facts','narrative','tables','delivery'],
    reviewer: ['rules','footnotes','changes'],
    manager:  ['overview','delivery','changes'],
  };
  const focus = roleFocus[role] || [];
  return (
    <nav className="w-56 shrink-0 bg-white border-r border-slate-200 flex flex-col">
      <div className="px-3 pt-3 pb-2">
        <div className="text-[10.5px] font-semibold text-slate-400 uppercase tracking-wider px-2 mb-1">工作台</div>
      </div>
      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {APP_NAV.map((n, i) => {
          const active = page === n.id;
          const hot = focus.includes(n.id);
          return (
            <button key={n.id} onClick={() => setPage(n.id)}
              className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-[13px] transition-colors group ${
                active ? 'bg-brand-600 text-white font-medium shadow-sm' : 'text-slate-600 hover:bg-slate-50'}`}>
              <span className={`w-5 text-center shrink-0 tabular text-[10px] ${active ? 'text-brand-200' : 'text-slate-300'}`}>{String(i+1).padStart(2,'0')}</span>
              <Icon name={n.icon} size={16} className={active ? 'text-white' : 'text-slate-400 group-hover:text-slate-500'}/>
              <span className="flex-1 text-left truncate">{n.name}</span>
              {hot && !active && <span className="w-1.5 h-1.5 rounded-full bg-teal-500" title="当前角色重点"></span>}
            </button>
          );
        })}
      </div>
      <div className="p-3 border-t border-slate-100">
        <div className="rounded-md bg-slate-50 border border-slate-200 p-2.5">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mb-1.5"><Icon name="Info" size={12}/>规则集</div>
          <div className="space-y-1">
            {P.rulesets.map(r => <div key={r} className="text-[10.5px] font-mono text-slate-500 truncate">{r}</div>)}
          </div>
        </div>
      </div>
    </nav>
  );
}

function Workbench({ project, onExit, onAccount, onLogout }) {
  const [page, setPage] = useState('overview');
  const [role, setRole] = useState('editor');
  const [frozen, setFrozen] = useState(!!(project && project.frozen));
  const [intakeOpen, setIntakeOpen] = useState(false);

  const ctx = { role, frozen, setFrozen, setPage };
  // 供浏览器级验收 (以及将来的深链) 按 NAV id 跳页。
  useEffect(() => { window.__cpswcGo = setPage; }, []);
  // 任何页面都可以请求打开收资抽屉 (Overview 的"待甲方补充"指路用)
  useEffect(() => {
    const open = () => setIntakeOpen(true);
    window.addEventListener('cpswc:open-intake', open);
    return () => window.removeEventListener('cpswc:open-intake', open);
  }, []);
  const PAGES = {
    overview:  window.OverviewPage,
    facts:     window.FactsPage,
    rules:     window.RulesPage,
    calc:      window.CalculatorsPage,
    tables:    IS_SNAPSHOT ? window.TablesSnapshotPage : window.TablesPage,
    maps:      window.MapsPage,
    // 快照模式用只读版: 演示版整页围绕编辑/润色/注脚组织, 而这些一样没实现
    narrative: IS_SNAPSHOT ? window.NarrativeSnapshotPage : window.NarrativePage,
    footnotes: window.FootnotesPage,
    changes:   window.ChangeTrackingPage,
    history:   window.HistoryPage,
    delivery:  window.DeliveryPage,
  };
  const RawPage = PAGES[page] || (() => <div className="p-8 text-slate-400">页面建设中…</div>);
  const PageComp = (props) => (
    <>
      <UnwiredNotice pageKey={page} />
      <RawPage {...props} />
    </>
  );
  const completeness = project ? project.completeness : (IS_SNAPSHOT ? null : 91);

  return (
    <div className="h-full flex flex-col">
      <DataModeBar />
      <TopBar role={role} setRole={setRole} frozen={frozen} setFrozen={setFrozen} completeness={completeness}
        projectName={project && project.name} onExit={onExit} onAccount={onAccount} onLogout={onLogout}
        onIntake={() => setIntakeOpen(true)} />
      <div className="flex-1 flex min-h-0">
        <SideNav page={page} setPage={setPage} role={role} />
        <main className="flex-1 min-w-0 overflow-auto bg-[#eef1f5]">
          <PageComp {...ctx} />
        </main>
      </div>
      <window.IntakeWizard open={intakeOpen} onClose={() => setIntakeOpen(false)} onNavigate={setPage} />
    </div>
  );
}

window.Workbench = Workbench;

Object.assign(window, { Workbench, PayloadErrorPage, DataModeBar, UnwiredNotice });
