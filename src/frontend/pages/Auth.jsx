// ===================================================================
// 账户层：登录 / 注册 / 找回密码
// ===================================================================
const { USER: AUTH_USER } = window.CPSWC;

function AuthShell({ children }) {
  return (
    <div className="h-full flex bg-[#eef1f5]">
      {/* 左：品牌深蓝面板 */}
      <div className="hidden lg:flex w-[44%] max-w-[620px] flex-col justify-between bg-brand-900 text-white p-12 relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.07]" style={{ backgroundImage:'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize:'40px 40px' }}></div>
        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-teal-500 to-brand-500 grid place-items-center font-bold text-[16px]">CP</div>
            <div>
              <div className="text-[15px] font-semibold tracking-wide">CPSWC</div>
              <div className="text-[11px] text-brand-300">水土保持方案智能编制与审查平台</div>
            </div>
          </div>
        </div>
        <div className="relative">
          <h1 className="text-[30px] font-bold leading-snug">事实驱动 · 规则可追踪<br/>数文一致 · 面向交付</h1>
          <p className="mt-4 text-[13.5px] text-brand-200 leading-relaxed max-w-[420px]">
            生产建设项目水土保持方案的确定性生产与审查平台。从项目事实到交付包，全链路可追溯、可审查、可复核。
          </p>
          <div className="mt-8 space-y-3">
            {[['ShieldCheck','规则审查与义务触发可追踪到标准依据'],['Calculator','专业确定性计算器，非 AI 猜测'],['FileText','正式报告预览 + 段落级编辑 + 来源链'],['GitCompareArrows','一次事实修改，全链路影响一目了然']].map(([i,t]) => (
              <div key={t} className="flex items-center gap-3 text-[13px] text-brand-100">
                <span className="w-8 h-8 rounded-md bg-white/10 grid place-items-center shrink-0"><Icon name={i} size={16}/></span>{t}
              </div>
            ))}
          </div>
        </div>
        <div className="relative text-[11px] text-brand-400">© 2026 CPSWC · 依据 GB 50433-2018 / GB/T 50434-2018 等标准</div>
      </div>

      {/* 右：表单 */}
      <div className="flex-1 flex items-center justify-center p-6 overflow-y-auto">
        <div className="w-full max-w-[400px]">{children}</div>
      </div>
    </div>
  );
}

function TextInput({ icon, label, type='text', value, onChange, placeholder, right }) {
  return (
    <label className="block">
      <span className="text-[12.5px] font-medium text-slate-600">{label}</span>
      <div className="mt-1.5 relative">
        {icon && <Icon name={icon} size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/>}
        <input type={type} value={value} onChange={onChange} placeholder={placeholder}
          className={`w-full h-10 rounded-md border border-slate-300 bg-white text-[13.5px] text-slate-800 ${icon?'pl-9':'pl-3'} pr-3 focus:outline-none focus:ring-2 focus:ring-brand-300 focus:border-brand-400 transition-shadow`} />
        {right}
      </div>
    </label>
  );
}

function LoginView({ onLogin, onRegister, onForgot }) {
  const [email, setEmail] = useState('liwentao@gd-swbc.com');
  const [pwd, setPwd] = useState('demo-pass');
  const [show, setShow] = useState(false);
  const [remember, setRemember] = useState(true);
  return (
    <AuthShell>
      <div className="lg:hidden flex items-center gap-2.5 mb-8">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-teal-500 to-brand-500 grid place-items-center font-bold text-white">CP</div>
        <div className="text-[14px] font-semibold text-slate-800">CPSWC 水土保持方案平台</div>
      </div>
      <h2 className="text-[22px] font-bold text-slate-800">登录工作台</h2>
      <p className="text-[13px] text-slate-400 mt-1">使用机构账户登录，进入您的项目工作空间</p>

      <form className="mt-7 space-y-4" onSubmit={(e)=>{e.preventDefault();onLogin();}}>
        <TextInput icon="Mail" label="账户邮箱" value={email} onChange={e=>setEmail(e.target.value)} placeholder="name@org.com" />
        <TextInput icon="Lock" label="登录密码" type={show?'text':'password'} value={pwd} onChange={e=>setPwd(e.target.value)} placeholder="请输入密码"
          right={<button type="button" onClick={()=>setShow(s=>!s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"><Icon name={show?'EyeOff':'Eye'} size={16}/></button>} />
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-1.5 text-[12.5px] text-slate-500 cursor-pointer">
            <input type="checkbox" checked={remember} onChange={e=>setRemember(e.target.checked)} className="accent-brand-600"/>记住此设备
          </label>
          <button type="button" onClick={onForgot} className="text-[12.5px] text-brand-600 hover:underline">忘记密码？</button>
        </div>
        <button type="submit" className="w-full h-10 rounded-md bg-brand-600 text-white text-[14px] font-medium hover:bg-brand-700 transition-colors flex items-center justify-center gap-2">
          <Icon name="LogIn" size={16}/>登录
        </button>
      </form>

      <div className="mt-5 flex items-center gap-3 text-[11px] text-slate-300"><div className="flex-1 h-px bg-slate-200"></div>或<div className="flex-1 h-px bg-slate-200"></div></div>
      <button onClick={onRegister} className="mt-5 w-full h-10 rounded-md border border-slate-300 bg-white text-[13.5px] text-slate-600 hover:bg-slate-50 transition-colors flex items-center justify-center gap-2">
        <Icon name="UserPlus" size={16}/>注册新账户
      </button>
      <div className="mt-6 flex items-start gap-2 text-[11.5px] text-slate-400 bg-slate-100 rounded-md px-3 py-2">
        <Icon name="Info" size={13} className="shrink-0 mt-0.5"/>演示环境：已预填演示账户，直接点「登录」即可进入。
      </div>
    </AuthShell>
  );
}

function RegisterView({ onDone, onBack }) {
  const [step, setStep] = useState(1);
  const [f, setF] = useState({ name:'', email:'', org:'', role:'编制人员', pwd:'', pwd2:'', agree:false });
  const up = (k,v)=>setF(s=>({...s,[k]:v}));
  const roleOk = ['编制人员','审查专家','项目负责人'];
  return (
    <AuthShell>
      <button onClick={onBack} className="text-[12.5px] text-slate-400 hover:text-slate-600 inline-flex items-center gap-1 mb-5"><Icon name="ArrowLeft" size={14}/>返回登录</button>
      <h2 className="text-[22px] font-bold text-slate-800">注册新账户</h2>
      <p className="text-[13px] text-slate-400 mt-1">创建机构账户以使用水土保持方案工作台</p>

      {/* 步骤指示 */}
      <div className="mt-5 flex items-center gap-2">
        {[1,2].map(s => (
          <React.Fragment key={s}>
            <span className={`w-6 h-6 rounded-full grid place-items-center text-[11px] font-bold ${step>=s?'bg-brand-600 text-white':'bg-slate-200 text-slate-400'}`}>{s}</span>
            {s===1 && <span className={`flex-1 h-px ${step>1?'bg-brand-600':'bg-slate-200'}`}></span>}
          </React.Fragment>
        ))}
        <span className="text-[11.5px] text-slate-400 ml-2">{step===1?'账户信息':'设置密码'}</span>
      </div>

      {step===1 ? (
        <div className="mt-6 space-y-4">
          <TextInput icon="User" label="姓名" value={f.name} onChange={e=>up('name',e.target.value)} placeholder="如：李文涛" />
          <TextInput icon="Mail" label="机构邮箱" value={f.email} onChange={e=>up('email',e.target.value)} placeholder="name@org.com" />
          <TextInput icon="Building2" label="所属单位" value={f.org} onChange={e=>up('org',e.target.value)} placeholder="如：广东××水保咨询有限公司" />
          <label className="block">
            <span className="text-[12.5px] font-medium text-slate-600">默认角色</span>
            <div className="mt-1.5 grid grid-cols-3 gap-2">
              {roleOk.map(r => (
                <button key={r} onClick={()=>up('role',r)} className={`h-9 rounded-md border text-[12.5px] transition-colors ${f.role===r?'border-brand-500 bg-brand-50 text-brand-700':'border-slate-300 text-slate-500 hover:bg-slate-50'}`}>{r}</button>
              ))}
            </div>
            <span className="text-[11px] text-slate-400 mt-1.5 block">登录后仍可在顶部自由切换角色</span>
          </label>
          <button onClick={()=>setStep(2)} className="w-full h-10 rounded-md bg-brand-600 text-white text-[14px] font-medium hover:bg-brand-700 transition-colors">下一步</button>
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          <TextInput icon="Lock" label="设置密码" type="password" value={f.pwd} onChange={e=>up('pwd',e.target.value)} placeholder="至少 8 位，含字母与数字" />
          <TextInput icon="Lock" label="确认密码" type="password" value={f.pwd2} onChange={e=>up('pwd2',e.target.value)} placeholder="再次输入密码" />
          <label className="flex items-start gap-2 text-[12px] text-slate-500 cursor-pointer">
            <input type="checkbox" checked={f.agree} onChange={e=>up('agree',e.target.checked)} className="accent-brand-600 mt-0.5"/>
            <span>我已阅读并同意《平台服务协议》与《数据安全与保密条款》</span>
          </label>
          <div className="flex gap-2">
            <button onClick={()=>setStep(1)} className="h-10 px-4 rounded-md border border-slate-300 text-[13.5px] text-slate-600 hover:bg-slate-50">上一步</button>
            <button onClick={onDone} className="flex-1 h-10 rounded-md bg-brand-600 text-white text-[14px] font-medium hover:bg-brand-700 transition-colors flex items-center justify-center gap-2">
              <Icon name="UserCheck" size={16}/>完成注册并登录
            </button>
          </div>
        </div>
      )}
    </AuthShell>
  );
}

function ForgotView({ onBack }) {
  const [sent, setSent] = useState(false);
  const [email, setEmail] = useState('');
  return (
    <AuthShell>
      <button onClick={onBack} className="text-[12.5px] text-slate-400 hover:text-slate-600 inline-flex items-center gap-1 mb-5"><Icon name="ArrowLeft" size={14}/>返回登录</button>
      {!sent ? (
        <>
          <h2 className="text-[22px] font-bold text-slate-800">找回密码</h2>
          <p className="text-[13px] text-slate-400 mt-1">输入注册邮箱，我们将发送密码重置链接</p>
          <form className="mt-7 space-y-4" onSubmit={(e)=>{e.preventDefault();setSent(true);}}>
            <TextInput icon="Mail" label="注册邮箱" value={email} onChange={e=>setEmail(e.target.value)} placeholder="name@org.com" />
            <button type="submit" className="w-full h-10 rounded-md bg-brand-600 text-white text-[14px] font-medium hover:bg-brand-700 transition-colors flex items-center justify-center gap-2">
              <Icon name="Send" size={15}/>发送重置链接
            </button>
          </form>
        </>
      ) : (
        <div className="text-center py-6">
          <div className="w-14 h-14 rounded-full bg-emerald-50 text-emerald-600 grid place-items-center mx-auto"><Icon name="MailCheck" size={26}/></div>
          <h2 className="text-[19px] font-bold text-slate-800 mt-4">重置链接已发送</h2>
          <p className="text-[13px] text-slate-400 mt-2 leading-relaxed">我们已向 <b className="text-slate-600">{email||'您的邮箱'}</b> 发送密码重置链接，请在 30 分钟内完成重置。</p>
          <button onClick={onBack} className="mt-6 w-full h-10 rounded-md bg-brand-600 text-white text-[14px] font-medium hover:bg-brand-700">返回登录</button>
        </div>
      )}
    </AuthShell>
  );
}

Object.assign(window, { LoginView, RegisterView, ForgotView });