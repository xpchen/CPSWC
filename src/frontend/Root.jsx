// ===================================================================
// CPSWC — Root 路由状态机（账户 / 工作空间 / 向导 / 工作台）
// ===================================================================
function Root() {
  const { DATA_MODE, IS_SNAPSHOT, PAYLOAD } = window.CPSWC;

  // payload 有问题 → 阻断, **绝不回落 mock** (F-1B)
  if (DATA_MODE === 'PAYLOAD_ERROR') return <window.PayloadErrorPage />;

  // 快照模式直接进工作台: 登录 / 工作空间 / 新建向导全是 mock 交互,
  // 让用户在快照模式下走那套流程等于让他以为系统有账户和项目管理能力。
  // 同时也就不存在"Workspace 选的项目与 payload 不是同一个"的问题了。
  const [view, setView] = useState(IS_SNAPSHOT ? 'workbench' : 'login');
  const [project, setProject] = useState(
    IS_SNAPSHOT ? { name: PAYLOAD.project.name, completeness: null, frozen: false } : null);

  const go = (v) => setView(v);
  const openProject = (p) => { setProject(p); setView('workbench'); };

  switch (view) {
    case 'login':
      return <window.LoginView onLogin={() => go('workspace')} onRegister={() => go('register')} onForgot={() => go('forgot')} />;
    case 'register':
      return <window.RegisterView onDone={() => go('workspace')} onBack={() => go('login')} />;
    case 'forgot':
      return <window.ForgotView onBack={() => go('login')} />;
    case 'workspace':
      return <window.WorkspaceView onOpen={openProject} onNew={() => go('wizard')} onAccount={() => go('account')} onLogout={() => go('login')} />;
    case 'account':
      return <window.AccountView onBack={() => go('workspace')} onLogout={() => go('login')} />;
    case 'wizard':
      return <window.NewProjectWizard onCancel={() => go('workspace')} onFinish={openProject} />;
    case 'workbench':
      return <window.Workbench project={project}
        onExit={() => { if (!IS_SNAPSHOT) go('workspace'); }}
        onAccount={() => { if (!IS_SNAPSHOT) go('account'); }}
        onLogout={() => { if (!IS_SNAPSHOT) go('login'); }} />;
    default:
      return <window.LoginView onLogin={() => go('workspace')} onRegister={() => go('register')} onForgot={() => go('forgot')} />;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(<Root />);
