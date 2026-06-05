// ===================================================================
// 页 6 正文预览与编辑（核心页 · 第二轮精修）
// 三模式（预览 / 编辑 / 审查）· A4 为中心 · 左右面板可折叠
// 结构化注脚 · 数文一致性 · 段落状态动态 · 审查状态摘要
// ===================================================================
const { SOURCE_REGISTRY: N_SRC, SOURCE_TYPE_LABELS: N_STL, SOURCE_TYPE_ICONS: N_STI, FOOTNOTE_TYPES: N_FT } = window.CPSWC;

const N_CHAPTERS = [
  { num:'1',  title:'综合说明', base:['已生成'] },
  { num:'2',  title:'项目概况', base:['已生成'] },
  { num:'3',  title:'项目水土保持评价', base:['已生成'] },
  { num:'4',  title:'表土保护', base:['已生成'] },
  { num:'5',  title:'水土流失预测', base:['已生成'] },
  { num:'6',  title:'防治责任范围', base:['已生成'] },
  { num:'7',  title:'水土保持措施', base:['已生成'], paras:['p71','p72'] },
  { num:'8',  title:'监测安排', base:['已生成'] },
  { num:'9',  title:'投资估算与效益分析', base:['已生成'], paras:['p91','p92'] },
  { num:'10', title:'实施保障', base:['骨架占位'] },
  { num:'11', title:'结论', base:['已生成'], paras:['p11'] },
];

const N_PARAS = {
  p71: { id:'p71', label:'7.1 防治措施总体布局', refMoney:null,
    sys:'本项目按"三区一线"思路布设水土保持措施，工程措施与植物措施相结合，临时措施贯穿施工全过程，形成完整的水土流失防治体系。',
    srcCount:{ fact:4, rule:1, calc:0, table:1 } },
  p72: { id:'p72', label:'7.2 水土流失防治目标', refMoney:null,
    sys:'根据项目建设内容、扰动范围及区域水土保持要求，本项目水土流失防治目标采用南方红壤区建设类项目防治标准。经系统按 GB/T 50434-2018 相关指标进行计算，本项目水土流失治理度、土壤流失控制比、渣土防护率、表土保护率、林草植被恢复率和林草覆盖率均已形成目标值。',
    srcCount:{ fact:5, rule:2, calc:1, table:1 } },
  p91: { id:'p91', label:'9.1 投资估算', refMoney:'6.00',
    sys:'经测算，本项目水土保持措施投资合计 6.00 万元，其中工程措施 1.20 万元、植物措施 1.02 万元、临时措施 1.34 万元、主体已列 2.44 万元。',
    srcCount:{ fact:6, rule:1, calc:1, table:2 } },
  p92: { id:'p92', label:'9.2 水土保持补偿费', refMoney:'4.248',
    sys:'根据项目占地面积、广东省水土保持补偿费征收规则及惠州市区域适配规则，系统计算本项目水土保持补偿费为 4.248 万元。该结果已同步至补偿费计算表、投资汇总表及交付包。',
    srcCount:{ fact:5, rule:2, calc:1, table:1 } },
  p11: { id:'p11', label:'11 结论', refMoney:null,
    sys:'本项目水土保持方案事实资料基本完整，防治责任范围、措施体系、投资估算及补偿费计算均已形成可追溯结果。当前不存在导出阻塞项，年度投资分配仍需后续补充完善。',
    srcCount:{ fact:7, rule:3, calc:2, table:3 } },
};
// 模拟人工修改后的 9.2 文本（金额 4.248 → 4.5，触发数文不一致）
const MANUAL_FEE_TEXT = '根据项目占地面积、广东省水土保持补偿费征收规则及惠州市区域适配规则，系统计算本项目水土保持补偿费为 4.5 万元。该结果已同步至补偿费计算表、投资汇总表及交付包。';

// AI 润色建议（仅润色语气，锁定数值/注脚/标准/项目名）
const POLISH_SUGGEST = {
  p92:'经系统依据项目占地面积、广东省水土保持补偿费征收规则及惠州市区域适配规则进行计算，本项目水土保持补偿费为 4.248 万元。该计算结果已同步至补偿费计算表、投资汇总表及交付包，相关数值保持一致。',
  p72:'本项目水土流失防治目标依据南方红壤区建设类项目防治标准确定。经系统按 GB/T 50434-2018 相关指标计算，水土流失治理度、土壤流失控制比、渣土防护率、表土保护率、林草植被恢复率及林草覆盖率均已形成明确目标值。',
  p91:'经测算，本项目水土保持措施投资合计 6.00 万元，其中工程措施 1.20 万元、植物措施 1.02 万元、临时措施 1.34 万元、主体已列 2.44 万元，构成完整投资体系。',
  p71:'本项目按"三区一线"思路系统布设水土保持措施，工程措施与植物措施相结合，临时措施贯穿施工全过程，形成完整的水土流失防治体系。',
  p11:'本项目水土保持方案事实资料基本完整，防治责任范围、措施体系、投资估算及补偿费计算均已形成可追溯结果；当前不存在导出阻塞项，年度投资分配仍需后续补充完善。',
};
const POLISH_BAD = '本项目水土保持补偿费约为 4.5 万元。';
const POLISH_LOCKED = [
  ['项目名称','世维华南供应链（二期）'],
  ['建设地点','广东省惠州市惠城区马安镇'],
  ['补偿费金额','4.248 万元'],
  ['标准依据','GB/T 50434-2018'],
  ['注脚编号','[2]'],
  ['计算器结果','compensation_fee = 4.248 万元'],
];
const POLISH_METHODS = ['更正式','更简洁','更符合技术报告语气','去除重复表达','增强审查说明','保持原意轻微优化'];

const STUB_PARAS = {
  '1':'本方案为世维华南供应链（二期）项目水土保持方案报告书，依据国家及广东省水土保持法律法规、技术标准编制，明确项目水土流失防治责任、目标、措施与投资。',
  '2':'项目位于广东省惠州市，为物流仓储类生产建设项目，总占地面积 3.54 hm²，其中永久占地 2.86 hm²、临时占地 0.68 hm²。',
  '3':'经评价，项目选址、占地、土石方平衡及主体工程设计基本符合水土保持要求，不涉及水土保持禁止性规定。',
  '4':'项目场地为已硬化用地，无表土剥离，按简化表土保护措施处理。',
  '5':'经预测，项目建设期及自然恢复期可能产生的水土流失总量为 128.6 t，主要集中于施工扰动期。',
  '6':'本项目水土流失防治责任范围为 3.54 hm²，与项目占地范围一致。',
  '8':'项目布设水土流失监测点 4 个，监测内容包括扰动面积、措施实施情况及水土流失量。',
  '10':'建立水土保持管理、技术、资金保障体系，落实水土保持"三同时"制度。',
};

const SOURCE_DETAIL = {
  facts:['land.total_area = 3.54 hm²','project.location = 广东省惠州市','earthwork.spoil = 0 万 m³','compensation.region_rate = 1.2','land.permanent_area = 2.86 hm²'],
  rules:['GB 50433-2018','GB/T 50434-2018','惠州市区域适配规则'],
  calc:['compensation_fee = 4.248 万元','weighted_target = 已计算','prediction.soil_loss = 128.6 t'],
  tables:['防治责任范围表','六率分项目标表','补偿费计算表'],
  pos:{ chapter:'第 9 章 投资估算与效益分析', table:'附表 6', file:'narrative_skeleton_v0.docx' },
};

// ---------- 工具：数文一致性检测 ----------
function moneyMismatch(p, edits) {
  if (!p || !p.refMoney) return null;
  const txt = edits[p.id];
  if (txt == null) return null;
  const m = txt.match(/([0-9]+(?:\.[0-9]+)?)\s*万元/);
  if (m && m[1] !== p.refMoney) return { found:m[1], expect:p.refMoney };
  return null;
}
// ---------- 工具：段落派生状态 ----------
function paraState(p, edits, footnotes) {
  const edited = edits[p.id] != null;
  const fns = footnotes[p.id] || [];
  const mismatch = moneyMismatch(p, edits);
  return { edited, fns, hasFootnote: fns.length>0, mismatch, risk: !!mismatch };
}
// ---------- 工具：章节动态状态标签 ----------
function chapterStatus(ch, edits, footnotes) {
  if (!ch.paras) return ch.base;
  const tags = [...ch.base];
  let edited=false, foot=false, risk=false;
  ch.paras.forEach(id => { const s = paraState(N_PARAS[id], edits, footnotes);
    edited = edited||s.edited; foot = foot||s.hasFootnote; risk = risk||s.risk; });
  if (edited) tags.push('人工编辑');
  if (foot) tags.push('有注脚');
  if (risk) tags.push('风险');
  return tags;
}

// ===================================================================
// 工具栏（分组：模式 / 显示 / 编辑操作 / 导出）
// ===================================================================
function ModeSwitch({ mode, setMode }) {
  const items = [['preview','预览','Eye'],['edit','编辑','PencilLine'],['review','审查','ShieldCheck']];
  return (
    <div className="flex rounded-md border border-slate-300 overflow-hidden shrink-0">
      {items.map(([id,label,icon]) => (
        <button key={id} onClick={()=>setMode(id)}
          className={`inline-flex items-center gap-1.5 text-[13px] px-3 py-1.5 whitespace-nowrap border-l first:border-l-0 border-slate-300 transition-colors ${mode===id?'bg-brand-600 text-white':'bg-white text-slate-600 hover:bg-slate-50'}`}>
          <Icon name={icon} size={14}/>{label}
        </button>
      ))}
    </div>
  );
}
function ToggleBtn({ icon, label, on, onClick, disabled }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className={`inline-flex items-center gap-1.5 text-[13px] px-2.5 py-1.5 rounded-md border whitespace-nowrap transition-colors ${
        disabled ? 'border-slate-200 text-slate-300 cursor-not-allowed' : on ? 'bg-brand-50 border-brand-300 text-brand-700' : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'}`}>
      <Icon name={icon} size={14}/>{label}
    </button>
  );
}
function ActionBtn({ icon, label, onClick, tone='default', disabled }) {
  const tones = {
    default:'bg-white border-slate-300 text-slate-600 hover:bg-slate-50',
    warn:'bg-orange-500 border-orange-500 text-white hover:bg-orange-600',
    ghost:'bg-white border-slate-300 text-slate-600 hover:bg-red-50 hover:text-red-600 hover:border-red-200',
    teal:'bg-teal-600 border-teal-600 text-white hover:bg-teal-700',
  };
  return (
    <button onClick={onClick} disabled={disabled}
      className={`inline-flex items-center gap-1.5 text-[13px] px-3 py-1.5 rounded-md border whitespace-nowrap transition-colors ${disabled?'bg-slate-100 border-slate-200 text-slate-300 cursor-not-allowed':tones[tone]}`}>
      <Icon name={icon} size={14}/>{label}
    </button>
  );
}
function ToolGroup({ label, children }) {
  return (
    <div className="flex items-center gap-1.5 shrink-0">
      <span className="text-[10.5px] text-slate-400 uppercase tracking-wide mr-0.5 hidden 2xl:inline">{label}</span>
      {children}
    </div>
  );
}
const ToolDivider = () => <div className="w-px h-6 bg-slate-200 shrink-0"></div>;

// ===================================================================
// 折叠侧栏轨
// ===================================================================
function CollapsedRail({ label, icon, side, onExpand }) {
  return (
    <div className={`bg-white ${side==='left'?'border-r':'border-l'} border-slate-200 flex flex-col items-center pt-3 gap-3`}>
      <button onClick={onExpand} className="w-7 h-7 rounded-md hover:bg-slate-100 grid place-items-center text-slate-500" title="展开">
        <Icon name={side==='left'?'PanelLeftOpen':'PanelRightOpen'} size={17}/>
      </button>
      <div className="flex items-center gap-1.5 text-slate-400" style={{ writingMode:'vertical-rl' }}>
        <Icon name={icon} size={13}/><span className="text-[11px]">{label}</span>
      </div>
    </div>
  );
}

// ===================================================================
// 段落块
// ===================================================================
function ParaBlock({ p, mode, active, st, flags, draft, onClick, onEdit, onChange, onCommit, onPolish }) {
  const chrome = mode !== 'preview';
  const canEdit = mode === 'edit';
  const editing = canEdit && active === p.id && draft != null;
  const text = (st.edited || st.polished) ? st.editText : p.sys;

  return (
    <div onClick={onClick}
      className={`group relative rounded-md px-4 py-2.5 -mx-3 transition-all ${chrome?'cursor-pointer':''} ${
        active && chrome ? 'ring-1 ring-brand-300 bg-brand-50/20' : chrome ? 'hover:bg-slate-50/70' : ''} ${
        st.risk ? 'border-l-4 border-red-400 bg-red-50/30' : st.edited && chrome ? 'border-l-4 border-orange-300' : ''}`}>
      {/* 状态条（仅 chrome 模式） */}
      {chrome && (
        <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
          {st.edited ? <StatusTag status="人工编辑" /> : st.polished ? <StatusTag status="AI 润色" /> : <StatusTag status="系统生成" />}
          {st.polished && <span className="text-[10px] text-teal-600">/ 人工确认</span>}
          {st.hasFootnote && <Chip tone="amber" icon="Asterisk">{st.fns.length} 注脚</Chip>}
          {st.risk && <StatusTag status="风险" dot />}
          <span className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
            {canEdit && !editing && <button onClick={(e)=>{e.stopPropagation();onPolish();}} className="text-[11.5px] px-2 py-0.5 rounded bg-teal-50 border border-teal-200 text-teal-700 hover:bg-teal-100 inline-flex items-center gap-1 whitespace-nowrap"><Icon name="Sparkles" size={11}/>AI 润色</button>}
            {canEdit && !editing && <button onClick={(e)=>{e.stopPropagation();onEdit();}} className="text-[11.5px] px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-500 hover:text-brand-600 inline-flex items-center gap-1 whitespace-nowrap"><Icon name="Pencil" size={11}/>编辑段落</button>}
          </span>
        </div>
      )}

      {/* 数文一致性提示（编辑且引用计算值时） */}
      {editing && p.refMoney && (
        <div className="mb-2 flex items-start gap-1.5 text-[11.5px] text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1.5">
          <Icon name="TriangleAlert" size={12} className="shrink-0 mt-0.5"/>当前段落引用了系统计算值（{p.refMoney} 万元）。若手动修改数值，可能破坏正文、表格与计算器的一致性。
        </div>
      )}

      {/* 正文 */}
      {editing ? (
        <div onClick={(e)=>e.stopPropagation()}>
          <textarea autoFocus value={draft} onChange={(e)=>onChange(e.target.value)}
            className="w-full min-h-[120px] text-[15px] leading-[2] text-slate-800 font-serif p-3 rounded-md border border-brand-300 focus:outline-none focus:ring-2 focus:ring-brand-200 resize-y" />
          <div className="mt-2 flex items-center gap-2">
            <button onClick={onCommit} className="text-[12.5px] px-3 py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700 inline-flex items-center gap-1.5"><Icon name="Check" size={14}/>保存段落</button>
            <button onClick={()=>onChange(null)} className="text-[12.5px] px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50">取消</button>
          </div>
        </div>
      ) : (
        <p className="text-[15px] leading-[2] text-slate-800 font-serif text-justify" style={{textIndent:'2em'}}>
          {flags.diff && (st.edited || st.polished) ? (
            <>
              <span className="diff-del">{p.sys}</span>{' '}
              <span className="diff-add">{text}</span>
            </>
          ) : text}
          {flags.footnote && st.fns.map(f => <sup key={f.n} className="text-brand-600 font-medium font-sans ml-0.5">[{f.n}]</sup>)}
        </p>
      )}

      {/* 来源摘要（chrome + 显示来源） */}
      {chrome && flags.source && !editing && (
        <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-slate-400 flex-wrap">
          <Icon name="GitBranch" size={12}/>
          来源 <b className="text-slate-500">{p.srcCount.fact}</b> 事实 · <b className="text-slate-500">{p.srcCount.rule}</b> 规则 · <b className="text-slate-500">{p.srcCount.calc}</b> 计算器 · <b className="text-slate-500">{p.srcCount.table}</b> 表格
        </div>
      )}
    </div>
  );
}

// ===================================================================
// 右侧：审查状态摘要
// ===================================================================
function ReviewSummary({ p, st }) {
  const status = st.mismatch ? '不一致' : st.edited ? '待复核' : '可接受';
  const rows = [
    ['事实完整性', '通过'],
    ['规则依据', p.srcCount.rule>0 ? '已引用' : '缺失事实'],
    ['计算结果', st.mismatch ? '不一致' : '一致'],
    ['表格一致性', st.mismatch ? '待复核' : '一致'],
    ['人工修改状态', st.edited ? '已人工编辑' : '系统生成文本'],
    ['注脚状态', st.hasFootnote ? `${st.fns.length} 条` : '无'],
    ['导出状态', st.mismatch ? '待复核' : '可导出'],
  ];
  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden mb-4">
      <div className={`px-3 py-2.5 flex items-center justify-between ${st.mismatch?'bg-red-50':st.edited?'bg-orange-50':'bg-emerald-50'}`}>
        <span className="text-[12px] font-semibold text-slate-700 flex items-center gap-1.5"><Icon name="ClipboardCheck" size={14}/>当前段落审查状态</span>
        <StatusTag status={status} dot />
      </div>
      <div className="divide-y divide-slate-50">
        {rows.map(([k,v]) => (
          <div key={k} className="flex items-center justify-between px-3 py-2">
            <span className="text-[12px] text-slate-500">{k}</span>
            <StatusTag status={v} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ===================================================================
// 右侧：结构化注脚表单
// ===================================================================
function FootnoteForm({ onAdd }) {
  const [form, setForm] = useState({ type:'标准依据', sourceType:'rule', sourceId:'', sourceName:'', content:'', export:true, expert:false });
  const up = (k,v)=>setForm(f=>({...f,[k]:v}));
  const opts = N_SRC[form.sourceType] || [];
  const isManual = form.sourceType === 'manual';

  const submit = () => {
    if (!form.content.trim()) return;
    const src = opts.find(o=>o.id===form.sourceId);
    onAdd({
      type: form.type, sourceType: form.sourceType,
      sourceId: isManual ? 'manual' : (form.sourceId || (opts[0] && opts[0].id) || '—'),
      sourceName: isManual ? (form.sourceName || '人工说明') : (src ? src.name : (opts[0] && opts[0].name) || '—'),
      content: form.content, export: form.export, expert: form.expert,
    });
    setForm({ type:'标准依据', sourceType:'rule', sourceId:'', sourceName:'', content:'', export:true, expert:false });
  };

  const sel = "w-full text-[12.5px] rounded-md border border-slate-300 px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-brand-300";
  return (
    <div className="rounded-lg border border-brand-200 bg-brand-50/30 p-3 space-y-2.5">
      <div className="text-[12.5px] font-semibold text-slate-700 flex items-center gap-1.5"><Icon name="Plus" size={14}/>新增结构化注脚</div>
      <div className="grid grid-cols-2 gap-2">
        <label className="block"><span className="text-[11px] text-slate-500">注脚类型</span>
          <select value={form.type} onChange={e=>up('type',e.target.value)} className={sel}>{N_FT.map(t=><option key={t}>{t}</option>)}</select>
        </label>
        <label className="block"><span className="text-[11px] text-slate-500">关联来源类型</span>
          <select value={form.sourceType} onChange={e=>{up('sourceType',e.target.value);up('sourceId','');}} className={sel}>
            {Object.keys(N_STL).map(k=><option key={k} value={k}>{N_STL[k]} · {k}</option>)}
          </select>
        </label>
      </div>
      <label className="block"><span className="text-[11px] text-slate-500">关联来源</span>
        {isManual ? (
          <input value={form.sourceName} onChange={e=>up('sourceName',e.target.value)} placeholder="人工说明来源（自由填写）" className={sel}/>
        ) : (
          <select value={form.sourceId} onChange={e=>up('sourceId',e.target.value)} className={sel}>
            <option value="">选择来源 ID…</option>
            {opts.map(o=><option key={o.id} value={o.id}>{o.id} · {o.name}</option>)}
          </select>
        )}
      </label>
      <label className="block"><span className="text-[11px] text-slate-500">注脚内容</span>
        <textarea value={form.content} onChange={e=>up('content',e.target.value)} placeholder="注脚正文…" className={sel+' min-h-[56px] resize-y'}/>
      </label>
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-1.5 text-[11.5px] text-slate-600"><input type="checkbox" checked={form.export} onChange={e=>up('export',e.target.checked)} className="accent-brand-600"/>导出 Word</label>
        <label className="flex items-center gap-1.5 text-[11.5px] text-slate-600"><input type="checkbox" checked={form.expert} onChange={e=>up('expert',e.target.checked)} className="accent-orange-500"/>需专家确认</label>
      </div>
      <button onClick={submit} className="w-full text-[12.5px] py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700">保存注脚</button>
    </div>
  );
}

function FootnoteCard({ f, onDel }) {
  return (
    <div className="rounded-md border border-slate-200 p-2.5">
      <div className="flex items-center justify-between mb-1.5">
        <span className="flex items-center gap-1.5"><span className="text-brand-600 font-bold text-[12.5px]">[{f.n}]</span><Chip tone="amber">{f.type}</Chip></span>
        <button onClick={onDel} className="text-slate-300 hover:text-red-500"><Icon name="Trash2" size={13}/></button>
      </div>
      <div className="text-[12.5px] text-slate-600 leading-snug mb-2">{f.content}</div>
      <div className="space-y-1 text-[11px]">
        <div className="flex items-center gap-1.5 text-slate-500"><Icon name={N_STI[f.sourceType]||'Link'} size={11} className="text-slate-400"/>{N_STL[f.sourceType]}：<span className="font-mono">{f.sourceId}</span></div>
        <div className="text-slate-400 pl-4">{f.sourceName}</div>
      </div>
      <div className="mt-2 flex items-center gap-2 flex-wrap">
        {f.export ? <Chip tone="emerald" icon="Check">导出 Word</Chip> : <Chip tone="slate">不导出</Chip>}
        {f.expert && <StatusTag status="专家确认" />}
      </div>
    </div>
  );
}

// ===================================================================
// AI 润色 Tab
// ===================================================================
function PolishTab({ pid, mode, polished, onAdopt, onRevert }) {
  const [method, setMethod] = useState('更符合技术报告语气');
  const [bad, setBad] = useState(false);
  const orig = N_PARAS[pid] ? N_PARAS[pid].sys : '';
  const suggest = POLISH_SUGGEST[pid] || orig;

  if (mode === 'review') {
    return (
      <div className="space-y-3">
        <div className="text-[12px] text-slate-500 bg-slate-50 rounded-md px-3 py-2 flex items-center gap-1.5"><Icon name="Info" size={13}/>审查模式仅可查看润色记录，不允许直接润色。</div>
        {polished ? (
          <div className="rounded-md border border-teal-200 bg-teal-50 p-2.5 text-[12px] text-teal-800"><div className="flex items-center gap-1.5 font-medium mb-1"><Icon name="Sparkles" size={13}/>已采用 AI 润色</div>该段落已采用 AI 润色建议，未修改事实、数值与注脚，数文一致性通过。</div>
        ) : <div className="text-[12px] text-slate-400 text-center py-4">该段落暂无润色记录</div>}
      </div>
    );
  }
  if (mode !== 'edit') {
    return <div className="text-[12px] text-slate-400 bg-slate-50 rounded-md px-3 py-2 flex items-center gap-1.5"><Icon name="Info" size={12}/>切换到「编辑」模式可使用 AI 润色。</div>;
  }

  return (
    <div className="space-y-3.5">
      <div className="flex items-center gap-1.5 text-[12px] text-teal-700 bg-teal-50 border border-teal-200 rounded-md px-2.5 py-1.5">
        <Icon name="Sparkles" size={14}/>AI 仅辅助润色语气表达，不修改事实、数值、注脚与标准依据。
      </div>

      {/* 1. 润色方式 */}
      <div>
        <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">润色方式</div>
        <div className="flex flex-wrap gap-1.5">
          {POLISH_METHODS.map(m => (
            <button key={m} onClick={()=>setMethod(m)} className={`text-[11.5px] px-2 py-1 rounded border transition-colors ${method===m?'bg-brand-600 text-white border-brand-600':'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}>{m}</button>
          ))}
        </div>
      </div>

      {/* 2. 锁定内容 */}
      <div className="rounded-md border border-amber-200 bg-amber-50 p-2.5">
        <div className="text-[11.5px] font-semibold text-amber-700 mb-1.5 flex items-center gap-1.5"><Icon name="Lock" size={12}/>系统已锁定，AI 润色不得修改</div>
        <div className="space-y-1">
          {POLISH_LOCKED.map(([k,v]) => (
            <div key={k} className="flex items-center justify-between text-[11px]"><span className="text-amber-700">{k}</span><span className="font-mono text-amber-800">{v}</span></div>
          ))}
        </div>
      </div>

      {/* 3. 原文 */}
      <div>
        <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">原文</div>
        <div className="text-[12.5px] text-slate-600 leading-relaxed bg-slate-50 rounded-md p-2.5 border border-slate-100 font-serif">{orig}</div>
      </div>

      {/* 4. AI 润色建议 */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11.5px] font-semibold text-slate-500">AI 润色建议</span>
          <button onClick={()=>setBad(b=>!b)} className={`text-[11px] px-2 py-0.5 rounded border ${bad?'bg-red-500 text-white border-red-500':'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'}`}>模拟错误润色</button>
        </div>
        <div className={`text-[12.5px] leading-relaxed rounded-md p-2.5 border font-serif ${bad?'bg-red-50 border-red-200 text-slate-700':'bg-teal-50/50 border-teal-100 text-slate-700'}`}>
          {bad ? POLISH_BAD : suggest}
        </div>
      </div>

      {/* 错误润色拦截 */}
      {bad && (
        <div className="rounded-md border border-red-300 bg-red-50 p-2.5">
          <div className="flex items-center gap-1.5 text-[12px] font-semibold text-red-700 mb-1"><Icon name="ShieldX" size={14}/>该润色建议已被拦截</div>
          <div className="text-[11.5px] text-red-700">原因：补偿费金额从 <b>4.248 万元</b> 变为 <b>4.5 万元</b>，修改了系统计算值。该建议不可直接采用。</div>
        </div>
      )}

      {/* 5. 差异对比 */}
      {!bad && (
        <div>
          <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">差异对比</div>
          <div className="text-[12px] leading-relaxed rounded-md p-2.5 border border-slate-100 font-serif">
            <span className="diff-del">{orig.slice(0,14)}</span><span className="diff-add">{suggest.slice(0,16)}</span>
            <span className="text-slate-600">…数值 <b className="bg-white px-1 rounded">4.248 万元</b>、注脚 <b className="bg-white px-1 rounded">[2]</b>、标准 <b className="bg-white px-1 rounded">GB/T 50434-2018</b> 保持不变。</span>
          </div>
        </div>
      )}

      {/* 6. 安全检查 */}
      <div>
        <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">安全检查</div>
        <div className="space-y-1">
          {[['数值是否被修改', bad],['注脚编号是否被修改', false],['标准依据是否被修改', false],['项目名称是否被修改', false],['结论状态是否被修改', false]].map(([k,changed]) => (
            <div key={k} className="flex items-center justify-between px-2.5 py-1.5 rounded bg-slate-50 border border-slate-100 text-[11.5px]">
              <span className="text-slate-600">{k}</span>
              <span className={`inline-flex items-center gap-1 ${changed?'text-red-600':'text-emerald-600'}`}><Icon name={changed?'CircleAlert':'CircleCheck'} size={13}/>{changed?'已修改':'未修改'}</span>
            </div>
          ))}
          <div className={`mt-1 rounded px-2.5 py-1.5 text-[11.5px] flex items-center gap-1.5 ${bad?'bg-red-50 text-red-700 border border-red-200':'bg-emerald-50 text-emerald-700 border border-emerald-200'}`}>
            <Icon name={bad?'ShieldX':'ShieldCheck'} size={14}/>状态：{bad?'拦截 · 不可采用':'通过'}
          </div>
        </div>
      </div>

      {/* 7. 操作 */}
      <div className="flex items-center gap-2 pt-1">
        {polished ? (
          <button onClick={onRevert} className="flex-1 text-[12px] py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 inline-flex items-center justify-center gap-1.5"><Icon name="RotateCcw" size={13}/>恢复系统生成</button>
        ) : (
          <button onClick={()=>!bad && onAdopt()} disabled={bad} className={`flex-1 text-[12px] py-1.5 rounded-md inline-flex items-center justify-center gap-1.5 ${bad?'bg-slate-200 text-slate-400 cursor-not-allowed':'bg-teal-600 text-white hover:bg-teal-700'}`}><Icon name="Check" size={13}/>采用润色</button>
        )}
        <button className="text-[12px] px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50">重新生成</button>
      </div>
      {polished && <div className="text-[11px] text-teal-600 flex items-center gap-1"><Icon name="CircleCheck" size={12}/>已采用 · 段落状态：AI 润色 / 人工确认 · 数文一致性通过</div>}
    </div>
  );
}

// ===================================================================
// 主页面
// ===================================================================
function NarrativePage() {
  const [mode, setMode] = useState('edit'); // preview | edit | review
  const [chapter, setChapter] = useState('9');
  const [active, setActive] = useState('p92');
  const [flags, setFlags] = useState({ source:true, footnote:true, diff:false });
  const [leftCol, setLeftCol] = useState(false);
  const [rightCol, setRightCol] = useState(false);
  const [edits, setEdits] = useState({});            // 默认空 → 数文一致（4.248）
  const [polished, setPolished] = useState({});       // 采用 AI 润色的段落文本
  const [draft, setDraft] = useState(null);
  const [feeSimulated, setFeeSimulated] = useState(false);
  const [tab, setTab] = useState('source');
  const [footnotes, setFootnotes] = useState({
    p92:[{ n:1, type:'计算依据', sourceType:'calculator', sourceId:'calc.fee', sourceName:'补偿费计算器 → 4.248 万元', content:'计算来源：水土保持补偿费计算器，输入占地面积 3.54 hm²，输出 4.248 万元。', export:true, expert:false }],
    p72:[{ n:2, type:'标准依据', sourceType:'rule', sourceId:'GBT50434-2018', sourceName:'GB/T 50434-2018 表 4.0.2-5', content:'依据：GB/T 50434-2018 表 4.0.2-5（南方红壤区一级标准）。', export:true, expert:false }],
  });
  const [records, setRecords] = useState([
    { by:'系统', time:'今天 09:42', type:'添加注脚', before:'—', after:'[1] 计算依据 · 补偿费计算器', risk:false },
    { by:'系统', time:'今天 09:40', type:'系统生成', before:'—', after:'生成 9.2 补偿费段落', risk:false },
  ]);

  // 预览模式：关闭来源/痕迹标记（保留注脚 = 正式报告效果）
  const effFlags = mode==='preview' ? { source:false, footnote:true, diff:false } : flags;

  const ch = N_CHAPTERS.find(c=>c.num===chapter);
  const paras = (ch.paras || []).map(id => N_PARAS[id]);

  // 派生：附带 editText 的段落状态
  const stateOf = (p) => {
    const base = paraState(p, edits, footnotes);
    const polishedText = polished[p.id];
    return { ...base, editText: polishedText != null ? polishedText : edits[p.id], polished: polishedText != null && edits[p.id]==null };
  };
  const curPara = N_PARAS[active];
  const curState = curPara ? stateOf(curPara) : null;

  const toggle = (k) => setFlags(f=>({...f,[k]:!f[k]}));
  const log = (rec) => setRecords(r=>[{ by:'李工 · 编制', time:'刚刚', ...rec }, ...r]);

  const startEdit = (id) => { setActive(id); setDraft(edits[id] ?? N_PARAS[id].sys); };
  const commitEdit = () => {
    if (draft != null && active) {
      setEdits(e=>({...e,[active]:draft}));
      const mm = moneyMismatch(N_PARAS[active], {[active]:draft});
      log({ type:'人工编辑', before:N_PARAS[active].sys.slice(0,16)+'…', after:draft.slice(0,16)+'…', risk:!!mm });
    }
    setDraft(null);
  };
  const restore = () => {
    if (active && edits[active]!=null) {
      setEdits(e=>{ const n={...e}; delete n[active]; return n; });
      if (active==='p92') setFeeSimulated(false);
      log({ type:'恢复系统生成文本', before:'人工文本', after:'系统原文', risk:false });
    }
    setDraft(null);
  };
  const simulateFee = () => {
    setChapter('9'); setActive('p92'); setMode('edit');
    setEdits(e=>({...e, p92: MANUAL_FEE_TEXT}));
    setFeeSimulated(true);
    log({ type:'人工编辑', before:'…补偿费为 4.248 万元…', after:'…补偿费为 4.5 万元…', risk:true });
  };

  const addFootnote = (data) => {
    const all = Object.values(footnotes).flat();
    const nextN = (all.length ? Math.max(...all.map(f=>f.n)) : 0) + 1; // max+1，删除后不重复
    setFootnotes(fn=>({...fn,[active]:[...(fn[active]||[]),{ n:nextN, ...data }]}));
    log({ type:'添加注脚', before:'—', after:`[${nextN}] ${data.type} · ${N_STL[data.sourceType]}`, risk:false });
  };
  const delFootnote = (n) => {
    setFootnotes(fn=>({...fn,[active]:(fn[active]||[]).filter(f=>f.n!==n)}));
    log({ type:'删除注脚', before:`[${n}]`, after:'—', risk:false });
  };

  const allFns = Object.entries(footnotes).flatMap(([pid,arr])=>arr.map(f=>({...f,pid}))).sort((a,b)=>a.n-b.n);

  // AI 润色
  const openPolish = (id) => { setActive(id); setTab('polish'); };
  const adoptPolish = () => {
    if (active && POLISH_SUGGEST[active]) {
      setPolished(p=>({...p,[active]:POLISH_SUGGEST[active]}));
      log({ type:'AI 润色', before:'系统生成文本', after:'采用 AI 润色建议，未修改事实、数值和注脚', risk:false });
    }
  };
  const revertPolish = () => {
    if (active) { setPolished(p=>{ const n={...p}; delete n[active]; return n; });
      log({ type:'恢复系统生成文本', before:'AI 润色文本', after:'系统原文', risk:false }); }
  };

  // 网格列宽（折叠）
  const gridCols = `${leftCol?'46px':'224px'} 1fr ${rightCol?'46px':'352px'}`;

  return (
    <div>
      {/* 头部（精简） */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-white sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <span className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 grid place-items-center"><Icon name="FileText" size={19}/></span>
          <div>
            <h1 className="text-[17px] font-semibold text-slate-800 leading-tight">正文预览与编辑</h1>
            <p className="text-[12px] text-slate-400">正式报告预览 · 段落级编辑 · 来源链 · 结构化注脚 · 数文一致性</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {feeSimulated && <Chip tone="amber" icon="TriangleAlert">检测到数文不一致</Chip>}
          <ModeSwitch mode={mode} setMode={setMode} />
        </div>
      </div>

      {/* 工具栏（分组） */}
      <div className="flex items-center gap-3 px-6 py-2 border-b border-slate-200 bg-slate-50/80 overflow-x-auto">
        <ToolGroup label="显示">
          <ToggleBtn icon="GitBranch" label="来源" on={flags.source} onClick={()=>toggle('source')} disabled={mode==='preview'} />
          <ToggleBtn icon="Asterisk" label="注脚" on={flags.footnote} onClick={()=>toggle('footnote')} disabled={mode==='preview'} />
          <ToggleBtn icon="History" label="修改痕迹" on={flags.diff} onClick={()=>toggle('diff')} disabled={mode==='preview'} />
        </ToolGroup>
        <ToolDivider />
        <ToolGroup label="编辑操作">
          <ActionBtn icon="Wand2" label="模拟人工修改金额" tone="warn" onClick={simulateFee} disabled={mode!=='edit'||feeSimulated} />
          <ActionBtn icon="RotateCcw" label="恢复系统生成" tone="ghost" onClick={restore} disabled={mode!=='edit'} />
        </ToolGroup>
        <div className="ml-auto"></div>
        <ToolGroup label="导出">
          <ActionBtn icon="Save" label="保存修改" />
          <ActionBtn icon="FileText" label="导出 Word" tone="teal" />
        </ToolGroup>
      </div>

      <div className="grid h-[calc(100vh-56px-58px-49px)] min-w-[980px]" style={{ gridTemplateColumns: gridCols }}>
        {/* 左：章节树（可折叠） */}
        {leftCol ? (
          <CollapsedRail label="章节目录" icon="ListTree" side="left" onExpand={()=>setLeftCol(false)} />
        ) : (
          <aside className="border-r border-slate-200 bg-white overflow-y-auto">
            <div className="flex items-center justify-between px-3 py-2 sticky top-0 bg-white border-b border-slate-100">
              <span className="text-[10.5px] font-semibold text-slate-400 uppercase tracking-wide">章节目录</span>
              <button onClick={()=>setLeftCol(true)} className="w-6 h-6 rounded hover:bg-slate-100 grid place-items-center text-slate-400" title="折叠"><Icon name="PanelLeftClose" size={15}/></button>
            </div>
            <div className="p-2">
              {N_CHAPTERS.map(c => {
                const act = chapter===c.num;
                const tags = chapterStatus(c, edits, footnotes);
                return (
                  <button key={c.num} onClick={()=>{ setChapter(c.num); if(c.paras) setActive(c.paras[c.paras.length-1]); }}
                    className={`w-full text-left px-2.5 py-2 rounded-md mb-0.5 transition-colors ${act?'bg-brand-50':'hover:bg-slate-50'}`}>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-mono tabular ${act?'text-brand-500':'text-slate-300'}`}>{c.num.padStart(2,'0')}</span>
                      <span className={`flex-1 text-[12.5px] ${act?'text-brand-700 font-medium':'text-slate-600'}`}>{c.title}</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1 pl-6">{tags.map((s,i) => <StatusTag key={s+i} status={s} />)}</div>
                  </button>
                );
              })}
            </div>
          </aside>
        )}

        {/* 中：A4 预览（视觉中心） */}
        <section className="overflow-y-auto bg-[#d9dde4] p-8">
          <div className="mx-auto bg-white a4-shadow relative" style={{ maxWidth:'860px', minHeight:'1000px', padding:'72px 80px' }}>
            {/* 运行页眉 */}
            <div className="absolute left-20 right-20 top-7 flex items-center justify-between text-[10.5px] text-slate-400 font-serif border-b border-slate-200 pb-1.5">
              <span>世维华南供应链（二期）水土保持方案报告书</span><span>GD-HZ-2026-SWBC-0211</span>
            </div>
            {/* 章标题 */}
            <div className="text-center mb-7">
              <h2 className="text-[24px] font-bold text-slate-900 font-serif tracking-wide">第{['','一','二','三','四','五','六','七','八','九','十','十一'][parseInt(chapter)]}章　{ch.title}</h2>
            </div>

            <div className="space-y-2">
              {paras.length > 0 ? paras.map(p => {
                const st = stateOf(p);
                return (
                  <div key={p.id}>
                    <h3 className="text-[16px] font-semibold text-slate-800 font-serif mt-5 mb-1.5">{p.label}</h3>
                    <ParaBlock p={p} mode={mode} active={active===p.id} st={st} flags={effFlags}
                      draft={active===p.id?draft:null}
                      onClick={()=>{ if(mode!=='preview') setActive(p.id); }}
                      onEdit={()=>startEdit(p.id)} onChange={setDraft} onCommit={commitEdit} onPolish={()=>openPolish(p.id)} />
                    {st.mismatch && mode!=='preview' && (
                      <div className="ml-1 mt-1 mb-2 flex items-start gap-2 text-[12.5px] text-orange-800 bg-orange-50 border border-orange-200 rounded-md px-3 py-2">
                        <Icon name="TriangleAlert" size={15} className="text-orange-500 shrink-0 mt-0.5"/>
                        <span>检测到人工文本中的金额与计算器结果不一致。计算器结果为 <b className="tabular">{st.mismatch.expect} 万元</b>，人工文本为 <b className="tabular">{st.mismatch.found} 万元</b>。
                        <button onClick={restore} className="ml-1 underline text-orange-600">恢复系统值</button></span>
                      </div>
                    )}
                  </div>
                );
              }) : (
                <p className="text-[15px] leading-[2] text-slate-800 font-serif text-justify" style={{textIndent:'2em'}}>
                  {STUB_PARAS[chapter] || '本章节内容由系统根据项目事实生成。'}
                  {ch.base.includes('骨架占位') && mode!=='preview' && <span className="ml-2 inline-block align-middle"><StatusTag status="骨架占位"/></span>}
                </p>
              )}

              {chapter==='9' && (
                <div className="my-6 rounded-md border-2 border-dashed border-slate-300 bg-slate-50 p-4 text-center">
                  <Icon name="Table2" size={20} className="text-slate-300 mx-auto"/>
                  <div className="text-[12px] text-slate-400 mt-1 font-serif">［此处插入　附表 6　补偿费计算表　］</div>
                </div>
              )}

              {chapter==='6' && (
                <div className="my-6 rounded-md border border-slate-300 bg-slate-50/60 overflow-hidden">
                  <div className="flex">
                    <div className="w-28 shrink-0 bg-white border-r border-slate-200 grid place-items-center p-2">
                      <svg viewBox="0 0 100 75" className="w-full"><rect width="100" height="75" fill="#eef3ea"/><polygon points="28,18 74,15 78,58 32,62" fill="rgba(15,155,142,0.18)" stroke="#0c7f76" strokeWidth="1.5"/><polygon points="28,18 74,15 78,58 32,62" fill="none" stroke="#d24b2c" strokeWidth="1.2"/></svg>
                    </div>
                    <div className="flex-1 p-3">
                      <div className="text-[13px] font-semibold text-slate-700 font-serif">图 6-1　水土流失防治责任范围图{effFlags.footnote && <sup className="text-brand-600 font-sans ml-0.5">[4]</sup>}</div>
                      <div className="text-[11.5px] text-slate-500 mt-1">图注：项目用地红线、建设单位提供资料及系统防治责任范围装配结果。</div>
                      <div className="mt-2 flex items-center gap-2 flex-wrap">
                        <Chip tone="teal" icon="Map">FIG-002</Chip>
                        <span className="text-[11px] text-slate-400">来源：红线边界 + 底图装配</span>
                        {mode!=='preview' && <StatusTag status="可生成" dot/>}
                        {mode!=='preview' && <Chip tone="emerald" icon="Check">进入交付包</Chip>}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 注脚区（正式报告效果） */}
            {effFlags.footnote && (chapter==='9'||chapter==='7') && allFns.filter(f=>paras.find(p=>p.id===f.pid)).length>0 && (
              <div className="mt-10 pt-3 border-t border-slate-300">
                {allFns.filter(f=>paras.find(p=>p.id===f.pid)).map(f => (
                  <div key={f.n} className="text-[11.5px] text-slate-500 leading-relaxed flex gap-1.5 font-serif mb-0.5">
                    <span className="text-brand-600 font-medium shrink-0">[{f.n}]</span>
                    <span>{f.content}<span className="text-slate-400">（{f.type} · {f.sourceName}）</span></span>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-12 pt-3 text-center text-[11px] text-slate-300 font-serif">— 第 {parseInt(chapter)+8} 页 · 共 32 页 —</div>
          </div>
        </section>

        {/* 右：面板（可折叠） */}
        {rightCol ? (
          <CollapsedRail label="来源 / 注脚 / 审查" icon="PanelRight" side="right" onExpand={()=>setRightCol(false)} />
        ) : (
          <aside className="border-l border-slate-200 bg-white overflow-y-auto flex flex-col">
            <div className="flex items-center justify-between px-3 py-2 border-b border-slate-100 sticky top-0 bg-white z-10">
              <span className="text-[10.5px] font-semibold text-slate-400 uppercase tracking-wide">段落信息面板</span>
              <button onClick={()=>setRightCol(true)} className="w-6 h-6 rounded hover:bg-slate-100 grid place-items-center text-slate-400" title="折叠"><Icon name="PanelRightClose" size={15}/></button>
            </div>
            <div className="grid grid-cols-5 border-b border-slate-200 sticky top-[37px] bg-white z-10">
              {[['source','来源','GitBranch'],['footnote','注脚','Asterisk'],['polish','润色','Sparkles'],['record','记录','History'],['consistency','一致','ShieldAlert']].map(([id,label,icon]) => (
                <button key={id} onClick={()=>setTab(id)}
                  className={`flex flex-col items-center gap-0.5 py-2.5 text-[11px] transition-colors ${tab===id?'text-brand-600 border-b-2 border-brand-600 bg-brand-50/40':'text-slate-400 hover:text-slate-600'}`}>
                  <Icon name={icon} size={14}/>{label}
                </button>
              ))}
            </div>

            <div className="p-3.5 flex-1">
              <div className="mb-3 flex items-center gap-2 text-[11px] text-slate-400">
                <Icon name="MousePointerClick" size={12}/>当前段落：<span className="font-mono text-slate-600">{curPara?.label || '未选择'}</span>
              </div>

              {curPara && curState && (
                <>
                  {tab==='source' && (
                    <div>
                      <ReviewSummary p={curPara} st={curState} />
                      <div className="space-y-3.5">
                        {[['事实字段','Database',SOURCE_DETAIL.facts,'slate'],['规则依据','Gavel',SOURCE_DETAIL.rules,'amber'],['计算器结果','Calculator',SOURCE_DETAIL.calc,'brand'],['关联表格','Table2',SOURCE_DETAIL.tables,'teal']].map(([t,icon,items,tone]) => (
                          <div key={t}>
                            <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name={icon} size={12}/>{t}</div>
                            <div className="space-y-1">{items.map(i=><div key={i} className={`text-[11.5px] rounded px-2 py-1 border ${tone==='slate'?'font-mono text-slate-600 bg-slate-50 border-slate-100':tone==='amber'?'text-amber-700 bg-amber-50 border-amber-100':tone==='teal'?'text-teal-700 bg-teal-50 border-teal-100':'text-brand-700 bg-brand-50 border-brand-100'}`}>{i}</div>)}</div>
                          </div>
                        ))}
                        <div className="pt-2 border-t border-slate-100">
                          <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="MapPin" size={12}/>交付位置</div>
                          <div className="text-[11.5px] text-slate-500 space-y-0.5">
                            <div>正文章节：{SOURCE_DETAIL.pos.chapter}</div>
                            <div>表格位置：{SOURCE_DETAIL.pos.table}</div>
                            <div>导出文件：<span className="font-mono">{SOURCE_DETAIL.pos.file}</span></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {tab==='footnote' && (
                    <div className="space-y-3">
                      <div className="space-y-2">
                        {(footnotes[active]||[]).map(f => <FootnoteCard key={f.n} f={f} onDel={()=>delFootnote(f.n)} />)}
                        {(footnotes[active]||[]).length===0 && <div className="text-[12px] text-slate-400 text-center py-3">本段落暂无注脚</div>}
                      </div>
                      {mode==='edit' ? <FootnoteForm onAdd={addFootnote} /> : <div className="text-[11.5px] text-slate-400 bg-slate-50 rounded-md px-3 py-2 flex items-center gap-1.5"><Icon name="Info" size={12}/>切换到「编辑」模式可新增注脚。</div>}
                    </div>
                  )}

                  {tab==='polish' && (
                    <PolishTab pid={active} mode={mode} polished={polished[active]!=null}
                      onAdopt={adoptPolish} onRevert={revertPolish} />
                  )}

                  {tab==='record' && (
                    <div className="space-y-2">
                      {records.map((r,i) => (
                        <div key={i} className="rounded-md border border-slate-200 p-2.5">
                          <div className="flex items-center justify-between mb-1.5">
                            <Chip tone={r.type==='人工编辑'?'amber':r.type==='恢复系统生成文本'?'brand':'slate'}>{r.type}</Chip>
                            {r.risk && <StatusTag status="风险"/>}
                          </div>
                          <div className="text-[11.5px] space-y-0.5">
                            <div className="text-slate-400">前：<span className="text-slate-500">{r.before}</span></div>
                            <div className="text-slate-400">后：<span className="text-slate-700">{r.after}</span></div>
                          </div>
                          <div className="mt-1.5 text-[10.5px] text-slate-400 flex items-center gap-2"><Icon name="User" size={11}/>{r.by}<span>·</span>{r.time}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {tab==='consistency' && (
                    <div className="space-y-2">
                      <ReviewSummary p={curPara} st={curState} />
                      <div className={`rounded-md px-3 py-2.5 text-[12px] flex items-center gap-2 ${curState.mismatch?'bg-red-50 border border-red-200 text-red-700':'bg-emerald-50 border border-emerald-200 text-emerald-700'}`}>
                        <Icon name={curState.mismatch?'ShieldAlert':'ShieldCheck'} size={15}/>
                        风险等级：<b>{curState.mismatch?'高 · 数文不一致':'低 · 一致'}</b>
                      </div>
                      {curState.edited && (
                        <div className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-[11.5px] text-amber-800 flex items-start gap-1.5">
                          <Icon name="Info" size={13} className="shrink-0 mt-0.5"/>该段落已被人工修改。后续事实变更可能导致系统生成内容与人工修改内容不一致，系统建议重新审阅。
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

window.NarrativePage = NarrativePage;
