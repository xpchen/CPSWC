// ===================================================================
// CPSWC — Root 路由状态机（账户 / 工作空间 / 向导 / 工作台）
// ===================================================================
function Root() {
  const [view, setView] = useState('login'); // login | register | forgot | workspace | account | wizard | workbench
  const [project, setProject] = useState(null);

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
      return <window.Workbench project={project} onExit={() => go('workspace')} onAccount={() => go('account')} onLogout={() => go('login')} />;
    default:
      return <window.LoginView onLogin={() => go('workspace')} onRegister={() => go('register')} onForgot={() => go('forgot')} />;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(<Root />);
