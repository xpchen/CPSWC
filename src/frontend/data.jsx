// ===================================================================
// CPSWC — 共享原语 + Mock 数据
// ===================================================================
const { useState, useEffect, useRef, useMemo, createElement } = React;

// ---------- Icon (lucide UMD) ----------
function camel(k){ return k.replace(/-([a-z])/g, (_,c)=>c.toUpperCase()); }
function renderIconChild(child, i) {
  if (!Array.isArray(child)) return null;
  const tag = child[0], attrs = child[1], kids = child[2];
  if (typeof tag !== 'string') return null;
  const props = { key: i };
  if (attrs && typeof attrs === 'object') for (const k in attrs) props[camel(k)] = attrs[k];
  const childEls = Array.isArray(kids) ? kids.map(renderIconChild) : undefined;
  return createElement(tag, props, childEls);
}
function Icon({ name, size = 16, className = "", strokeWidth = 2, style }) {
  const L = window.lucide || {};
  let node = (L.icons && L.icons[name]) || L[name] || null;
  if (!Array.isArray(node)) {
    return <svg width={size} height={size} viewBox="0 0 24 24" className={className} style={style}><rect x="4" y="4" width="16" height="16" rx="2" fill="none" stroke="currentColor" strokeWidth="2"/></svg>;
  }
  // Two possible shapes: array-of-tuples, OR a full ['svg', attrs, children] triple.
  let children = node;
  if (typeof node[0] === 'string') children = Array.isArray(node[2]) ? node[2] : [];
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
      {children.map(renderIconChild)}
    </svg>
  );
}

// ---------- 状态标签 ----------
const STATUS_STYLES = {
  // 绿色
  'LIVE':        ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '已生成':       ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '通过':         ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '已满足':       ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '可下载':       ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  // 蓝色
  '系统生成':     ['bg-brand-50','text-brand-700','border-brand-200','#205394'],
  '已计算':       ['bg-brand-50','text-brand-700','border-brand-200','#205394'],
  '可生成':       ['bg-brand-50','text-brand-700','border-brand-200','#205394'],
  'CAN_GENERATE':['bg-brand-50','text-brand-700','border-brand-200','#205394'],
  // 橙色
  '人工编辑':     ['bg-orange-50','text-orange-700','border-orange-200','#ea7a25'],
  '待确认':       ['bg-orange-50','text-orange-700','border-orange-200','#ea7a25'],
  '专家确认':     ['bg-orange-50','text-orange-700','border-orange-200','#ea7a25'],
  // 黄色
  '待补充':       ['bg-amber-50','text-amber-700','border-amber-200','#d99a06'],
  '缺失':         ['bg-amber-50','text-amber-700','border-amber-200','#d99a06'],
  'SKELETON':    ['bg-amber-50','text-amber-700','border-amber-200','#d99a06'],
  '骨架占位':     ['bg-amber-50','text-amber-700','border-amber-200','#d99a06'],
  // 红色
  '阻塞':         ['bg-red-50','text-red-700','border-red-200','#dc2626'],
  'BLOCKED':     ['bg-red-50','text-red-700','border-red-200','#dc2626'],
  '风险':         ['bg-red-50','text-red-700','border-red-200','#dc2626'],
  '不一致':       ['bg-red-50','text-red-700','border-red-200','#dc2626'],
  // 灰色
  '不适用':       ['bg-slate-100','text-slate-500','border-slate-200','#94a3b8'],
  'NOT_APPLICABLE':['bg-slate-100','text-slate-500','border-slate-200','#94a3b8'],
  '未触发':       ['bg-slate-100','text-slate-500','border-slate-200','#94a3b8'],
  '未启用':       ['bg-slate-100','text-slate-500','border-slate-200','#94a3b8'],
  '未冻结':       ['bg-slate-100','text-slate-600','border-slate-300','#64748b'],
  '已冻结':       ['bg-brand-700','text-white','border-brand-700','#1b4178'],
  // 审查状态摘要
  '可接受':       ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '一致':         ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '可导出':       ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '已引用':       ['bg-brand-50','text-brand-700','border-brand-200','#205394'],
  '系统生成文本':  ['bg-brand-50','text-brand-700','border-brand-200','#205394'],
  '待复核':       ['bg-orange-50','text-orange-700','border-orange-200','#ea7a25'],
  '已人工编辑':    ['bg-orange-50','text-orange-700','border-orange-200','#ea7a25'],
  '需复核':       ['bg-orange-50','text-orange-700','border-orange-200','#ea7a25'],
  '需重新确认':    ['bg-orange-50','text-orange-700','border-orange-200','#ea7a25'],
  '缺失事实':     ['bg-amber-50','text-amber-700','border-amber-200','#d99a06'],
  '失效':         ['bg-slate-100','text-slate-500','border-slate-200','#94a3b8'],
  '新增':         ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '已完成':       ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '已选用':       ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '已上传':       ['bg-brand-50','text-brand-700','border-brand-200','#205394'],
  '待识别':       ['bg-amber-50','text-amber-700','border-amber-200','#d99a06'],
  '待审查':       ['bg-orange-50','text-orange-700','border-orange-200','#ea7a25'],
  '已匹配':       ['bg-emerald-50','text-emerald-700','border-emerald-200','#10b981'],
  '需确认':       ['bg-orange-50','text-orange-700','border-orange-200','#ea7a25'],
  '外部对照':     ['bg-violet-50','text-violet-700','border-violet-200','#7c5cd6'],
  'AI 润色':      ['bg-teal-50','text-teal-700','border-teal-200','#0c7f76'],
};
function StatusTag({ status, dot = false, className = "" }) {
  const s = STATUS_STYLES[status] || ['bg-slate-100','text-slate-600','border-slate-200','#64748b'];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border ${s[0]} ${s[1]} ${s[2]} ${className}`}>
      {dot && <span className="w-1.5 h-1.5 rounded-full" style={{ background: s[3] }}></span>}
      {status}
    </span>
  );
}

// ---------- 通用面板 ----------
function Panel({ title, sub, right, children, className = "", bodyClass = "" }) {
  return (
    <div className={`bg-white rounded-lg border border-slate-200 panel-shadow ${className}`}>
      {(title || right) && (
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-100">
          <div>
            {title && <div className="text-[13px] font-semibold text-slate-800">{title}</div>}
            {sub && <div className="text-[11px] text-slate-400 mt-0.5">{sub}</div>}
          </div>
          {right}
        </div>
      )}
      <div className={bodyClass}>{children}</div>
    </div>
  );
}

// ---------- 指标卡 ----------
function MetricCard({ label, value, unit, status, note, trend, accent = 'brand' }) {
  const accents = {
    brand: 'text-brand-700', emerald: 'text-emerald-600', amber: 'text-amber-600',
    orange: 'text-orange-600', red: 'text-red-600', slate: 'text-slate-700'
  };
  return (
    <div className="bg-white rounded-lg border border-slate-200 panel-shadow p-4 flex flex-col">
      <div className="flex items-start justify-between">
        <span className="text-[12px] text-slate-500">{label}</span>
        {status && <StatusTag status={status} dot />}
      </div>
      <div className="mt-2 flex items-baseline gap-1.5">
        <span className={`text-[30px] leading-none font-bold tabular ${accents[accent]}`}>{value}</span>
        {unit && <span className="text-[13px] text-slate-400">{unit}</span>}
        {trend && (
          <span className={`ml-auto inline-flex items-center gap-0.5 text-[11px] ${trend.up ? 'text-emerald-600' : 'text-slate-400'}`}>
            <Icon name={trend.up ? 'TrendingUp' : 'Minus'} size={13} />{trend.label}
          </span>
        )}
      </div>
      {note && <div className="mt-2 text-[11.5px] text-slate-400 leading-snug">{note}</div>}
    </div>
  );
}

// ---------- 小标签 / KV ----------
function Field({ k, v, mono }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1.5 border-b border-slate-50 last:border-0">
      <span className="text-[12px] text-slate-400 shrink-0">{k}</span>
      <span className={`text-[12.5px] text-slate-700 text-right ${mono ? 'font-mono tabular' : 'font-medium'}`}>{v}</span>
    </div>
  );
}
function Chip({ children, tone = 'slate', icon }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-600', brand: 'bg-brand-50 text-brand-700',
    emerald: 'bg-emerald-50 text-emerald-700', amber: 'bg-amber-50 text-amber-700',
    teal: 'bg-teal-50 text-teal-700',
  };
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono ${tones[tone]}`}>{icon && <Icon name={icon} size={11}/>}{children}</span>;
}

// ===================================================================
// MOCK DATA
// ===================================================================
const PROJECT = {
  name: '世维华南供应链（二期）',
  org: '广东世维供应链有限公司',
  code: 'GD-HZ-2026-SWBC-0211',
  location: '广东省惠州市',
  type: '物流仓储类生产建设项目',
  rulesets: ['GB 50433-2018', 'GB/T 50434-2018', '广东省区域规则', '惠州市适配规则'],
  rulesetVersion: '2026-06 candidate',
  scopeArea: 3.54,
  compensationFee: 4.248,
  soilLoss: 128.6,
  narrativeCoverage: 92,
  tableRate: 88,
  factCompleteness: 94,
  blockers: 0,
  expertPending: 2,
  phase: '方案编制 · 预生成',
  frozen: false,
  status: '可生成，需补充年度投资分配',
};

const ROLES = [
  { id: 'editor',   name: '编制人员', icon: 'PencilRuler', desc: '事实填报 · 正文编辑 · 表格生成 · 导出' },
  { id: 'reviewer', name: '审查专家', icon: 'ShieldCheck', desc: '规则审查 · 证据链 · 注脚依据 · 改动追踪' },
  { id: 'manager',  name: '项目负责人', icon: 'ClipboardList', desc: '总体进度 · 阻塞项 · 交付状态 · 版本冻结' },
];

const NAV = [
  { id: 'overview',  name: '项目总览', icon: 'LayoutDashboard' },
  { id: 'facts',     name: '事实填报', icon: 'Database' },
  { id: 'rules',     name: '规则审查', icon: 'Gavel' },
  { id: 'calc',      name: '计算器',  icon: 'Calculator' },
  { id: 'tables',    name: '表格中心', icon: 'Table2' },
  { id: 'maps',      name: '附图与地图', icon: 'Map' },
  { id: 'narrative', name: '正文预览与编辑', icon: 'FileText' },
  { id: 'footnotes', name: '注脚与依据库', icon: 'BookMarked' },
  { id: 'changes',   name: '改动追踪', icon: 'GitCompareArrows' },
  { id: 'history',   name: '历史与版本', icon: 'History' },
  { id: 'delivery',  name: '交付包',  icon: 'PackageCheck' },
];

const SIX_RATES = [
  { name: '水土流失治理度', target: '97%', actual: '97.6%', ok: true,  ref: 'GB/T 50434-2018 表4.0.2-5' },
  { name: '土壤流失控制比', target: '1.0', actual: '1.0',   ok: true,  ref: 'GB/T 50434-2018 表4.0.2-5' },
  { name: '渣土防护率',     target: '92%', actual: '95.0%', ok: true,  ref: 'GB/T 50434-2018 表4.0.2-5' },
  { name: '表土保护率',     target: '92%', actual: '94.0%', ok: true,  ref: 'GB/T 50434-2018 表4.0.2-5' },
  { name: '林草植被恢复率', target: '97%', actual: '97.2%', ok: true,  ref: 'GB/T 50434-2018 表4.0.2-5' },
  { name: '林草覆盖率',     target: '22%', actual: '23.1%', ok: true,  ref: 'GB/T 50434-2018 表4.0.2-5' },
];

const KEY_FACTS = [
  { id: 'land.total_area',     v: '3.54',  u: 'hm²',  src: '项目用地红线' },
  { id: 'land.permanent_area', v: '2.86',  u: 'hm²',  src: '项目用地红线' },
  { id: 'land.temporary_area', v: '0.68',  u: 'hm²',  src: '施工组织设计' },
  { id: 'earthwork.excavation',v: '12.50', u: '万m³', src: '土石方平衡' },
  { id: 'earthwork.fill',      v: '12.50', u: '万m³', src: '土石方平衡' },
  { id: 'earthwork.borrow',    v: '0',     u: '万m³', src: '土石方平衡' },
  { id: 'earthwork.spoil',     v: '0',     u: '万m³', src: '土石方平衡' },
  { id: 'topsoil.stripping',   v: '0',     u: '万m³', src: '表土剥离方案' },
  { id: 'compensation_fee',    v: '4.248', u: '万元', src: '补偿费计算器' },
];

const RECENT_CHANGES = [
  { field: 'land.total_area', before: '3.20', after: '3.54', unit: 'hm²', by: '李工 · 编制', time: '今天 09:42', impact: '1 个计算器 · 3 张表格 · 5 个正文段落' },
  { field: 'measures.layout', before: '12 条', after: '14 条', unit: '', by: '李工 · 编制', time: '昨天 16:20', impact: '1 张表格 · 2 个正文段落 · 待专家确认' },
  { field: 'compensation.region_rate', before: '1.0', after: '1.2', unit: '', by: '系统 · 规则更新', time: '昨天 10:05', impact: '1 个计算器 · 2 张表格 · 1 个正文段落' },
];

const TODOS = [
  { tone: 'amber', text: '年度投资分配未填写，年度投资表为 SKELETON', tag: '待补充' },
  { tone: 'orange', text: '部分防治措施布局需要专家确认（2 条）', tag: '专家确认' },
  { tone: 'brand', text: '附件目录可生成但未最终确认', tag: 'CAN_GENERATE' },
  { tone: 'emerald', text: '当前无导出阻塞项', tag: '通过' },
];

// ===================================================================
// 账户 / 工作空间 层 MOCK DATA
// ===================================================================
const USER = {
  name: '李工', fullName: '李文涛', initials: '李',
  email: 'liwentao@gd-swbc.com', phone: '138 **** 6021',
  org: '广东××水土保持咨询有限公司', title: '水保方案编制工程师',
  joined: '2025-11', lastLogin: '2026-06-04 08:51',
};

const PROJECTS = [
  { id:'p-swbc2', name:'世维华南供应链（二期）', code:'GD-HZ-2026-SWBC-0211', location:'广东省惠州市', type:'物流仓储',
    role:'编制人员', stage:'方案编制 · 预生成', completeness:91, status:'可生成', frozen:false, blockers:0, expert:2,
    version:'v0.6-preview', updated:'今天 09:43', members:4, primary:true },
  { id:'p-glport', name:'广利港区集装箱堆场扩建', code:'GD-GZ-2026-GLPT-0188', location:'广东省广州市', type:'港口码头',
    role:'审查专家', stage:'专家审查中', completeness:78, status:'待确认', frozen:false, blockers:1, expert:5,
    version:'v0.4', updated:'昨天 17:20', members:6 },
  { id:'p-pvbase', name:'河源东源山地光伏基地', code:'GD-HY-2026-PVBS-0142', location:'广东省河源市', type:'光伏发电',
    role:'编制人员', stage:'事实填报', completeness:46, status:'缺失', frozen:false, blockers:3, expert:0,
    version:'v0.2', updated:'2026-06-01', members:3 },
  { id:'p-roadk1', name:'惠大高速 K1 标段改扩建', code:'GD-HZ-2025-RDK1-0097', location:'广东省惠州市', type:'公路工程',
    role:'项目负责人', stage:'已交付', completeness:100, status:'已冻结', frozen:true, blockers:0, expert:0,
    version:'v1.0', updated:'2026-05-22', members:8 },
  { id:'p-wwtp', name:'潮州凤泉污水处理厂', code:'GD-CZ-2026-WWTP-0205', location:'广东省潮州市', type:'市政环保',
    role:'编制人员', stage:'方案编制', completeness:63, status:'待确认', frozen:false, blockers:0, expert:1,
    version:'v0.3', updated:'2026-05-30', members:5 },
];

const PROJECT_VERSIONS = [
  { v:'v0.6-preview', date:'2026-06-04 09:43', by:'李工 · 编制', tag:'当前', current:true,
    summary:'更新占地面积 3.20→3.54 hm²，补偿费重算为 4.248 万元，正文 9.2 人工编辑。', changes:8 },
  { v:'v0.5', date:'2026-06-03 10:05', by:'系统 · 规则更新', tag:'已生成',
    summary:'区域费率 1.0→1.2（惠州市适配规则），补偿费 3.540→4.248 万元。', changes:5 },
  { v:'v0.4', date:'2026-06-02 16:20', by:'李工 · 编制', tag:'已生成',
    summary:'新增 2 条防治措施布局，措施投资 5.16→6.00 万元，触发专家确认。', changes:6 },
  { v:'v0.3', date:'2026-06-01 14:10', by:'张工 · 审查', tag:'已审查',
    summary:'专家审查表土保护与弃渣场判定，OB-002 标记不适用。', changes:4 },
  { v:'v0.2', date:'2026-05-29 11:30', by:'李工 · 编制', tag:'已生成',
    summary:'录入土石方平衡与防治责任范围，生成六率目标表骨架。', changes:7 },
  { v:'v0.1', date:'2026-05-28 09:00', by:'李工 · 编制', tag:'初始',
    summary:'创建项目，导入基本信息与规则集，生成报告骨架。', changes:3 },
];

const OP_LOG = [
  { action:'人工编辑正文', target:'9.2 水土保持补偿费', detail:'金额 4.248 → 4.5 万元', time:'今天 10:12', risk:true, icon:'Pencil' },
  { action:'添加注脚', target:'9.2 水土保持补偿费', detail:'[2] 计算依据', time:'今天 09:55', icon:'Asterisk' },
  { action:'模拟修改事实', target:'land.total_area', detail:'3.20 → 3.54 hm²', time:'今天 09:42', icon:'Database' },
  { action:'专家确认', target:'OB-004 措施布局', detail:'确认通过（张工）', time:'昨天 16:40', icon:'UserCheck' },
  { action:'生成预览', target:'交付包 v0.5', detail:'8 个文件就绪', time:'昨天 10:08', icon:'Eye' },
  { action:'切换角色', target:'编制人员 → 审查专家', detail:'—', time:'昨天 09:30', icon:'Repeat' },
  { action:'导出 Word', target:'narrative_skeleton_v0.docx', detail:'含人工编辑', time:'2026-06-02 17:02', icon:'FileText' },
];

const RULESET_OPTIONS = [
  { id:'gb50433', name:'GB 50433-2018', desc:'生产建设项目水土保持技术标准', required:true },
  { id:'gb50434', name:'GB/T 50434-2018', desc:'生产建设项目水土流失防治标准', required:true },
  { id:'gd_region', name:'广东省区域规则', desc:'广东省水土保持补偿费征收使用管理办法', required:false },
  { id:'hz_adapt', name:'惠州市适配规则', desc:'惠州市区域系数与措施适配规则', required:false },
  { id:'gb51018', name:'GB 51018-2014', desc:'水土保持工程设计规范（弃渣场）', required:false },
  { id:'gb51240', name:'GB/T 51240-2018', desc:'生产建设项目水土保持监测与评价标准', required:false },
];

const PROJECT_TYPES = ['物流仓储','港口码头','光伏发电','公路工程','市政环保','房屋建筑','矿山采选','水利工程','输变电','油气管道'];

// 结构化注脚：来源登记表（关联来源类型 → 候选来源）
const SOURCE_REGISTRY = {
  fact: [
    { id:'land.total_area', name:'总占地面积 = 3.54 hm²' },
    { id:'land.permanent_area', name:'永久占地 = 2.86 hm²' },
    { id:'land.temporary_area', name:'临时占地 = 0.68 hm²' },
    { id:'earthwork.spoil', name:'余方量 = 0 万 m³' },
    { id:'topsoil.stripping', name:'表土剥离 = 0 万 m³' },
    { id:'project.location', name:'建设地点 = 广东省惠州市' },
    { id:'compensation.region_rate', name:'区域费率 = 1.2' },
  ],
  rule: [
    { id:'GB50433-2018', name:'GB 50433-2018 技术标准' },
    { id:'GBT50434-2018', name:'GB/T 50434-2018 表 4.0.2-5' },
    { id:'GD-comp-rule', name:'广东省水土保持补偿费征收规则' },
    { id:'HZ-adapt', name:'惠州市区域适配规则' },
    { id:'GB51018-2014', name:'GB 51018-2014 弃渣场' },
  ],
  calculator: [
    { id:'calc.fee', name:'补偿费计算器 → 4.248 万元' },
    { id:'calc.sixrate', name:'六率目标计算器 → 已计算' },
    { id:'calc.predict', name:'水土流失预测计算器 → 128.6 t' },
    { id:'calc.invest', name:'防治措施投资汇总计算器 → 6.00 万元' },
  ],
  table: [
    { id:'tbl.scope', name:'防治责任范围表' },
    { id:'tbl.sixrate', name:'六率分项目标表' },
    { id:'tbl.fee', name:'补偿费计算表' },
    { id:'tbl.measure', name:'防治措施投资表' },
  ],
  narrative: [
    { id:'n.2.1', name:'2.1 项目概况' },
    { id:'n.7.2', name:'7.2 水土流失防治目标' },
    { id:'n.9.2', name:'9.2 水土保持补偿费' },
    { id:'n.11', name:'11 结论' },
  ],
  attachment: [
    { id:'att.redline', name:'项目用地红线图' },
    { id:'att.earthbalance', name:'土石方平衡图' },
    { id:'att.contract', name:'委托合同' },
  ],
  manual: [],
};
const SOURCE_TYPE_LABELS = { fact:'事实', rule:'规则', calculator:'计算器', table:'表格', narrative:'正文', attachment:'附件', manual:'人工' };
const SOURCE_TYPE_ICONS = { fact:'Database', rule:'Gavel', calculator:'Calculator', table:'Table2', narrative:'FileText', attachment:'Paperclip', manual:'PenLine' };
const FOOTNOTE_TYPES = ['标准依据','事实来源','计算依据','审查意见','人工说明','版本说明','图件来源'];

// ===================================================================
// 第四轮：智能收资 / Excel 导入 / 附图与地图 MOCK DATA
// ===================================================================
const INTAKE_DOCS = [
  { id:'d1', name:'项目基础资料与投资估算.xlsx', kind:'Excel', icon:'FileSpreadsheet', time:'今天 09:20', status:'已识别',
    facts:15, pending:3, figures:0, conflict:1, action:'excel', note:'15 个候选事实，3 个待确认字段' },
  { id:'d2', name:'项目红线图.pdf', kind:'PDF 图件', icon:'FileText', time:'今天 09:22', status:'已识别',
    facts:0, pending:1, figures:1, conflict:0, action:'maps', note:'1 个图件附件，1 个责任范围候选来源' },
  { id:'d3', name:'总平面布置图.png', kind:'图片', icon:'Image', time:'今天 09:24', status:'已识别',
    facts:0, pending:0, figures:1, conflict:0, action:'figure', note:'1 个外部图件附件' },
  { id:'d4', name:'监测点位表.xlsx', kind:'Excel', icon:'FileSpreadsheet', time:'今天 09:25', status:'待识别',
    facts:0, pending:1, figures:0, conflict:0, action:'excel', note:'尚未确认字段映射' },
];

const INTAKE_CANDIDATES = [
  { fid:'project.name', cn:'项目名称', val:'世维华南供应链（二期）', unit:'', file:'项目基础资料与投资估算.xlsx', loc:'Sheet1 A2', conf:98, status:'待确认' },
  { fid:'project.org', cn:'建设单位', val:'广东世维供应链有限公司', unit:'', file:'项目基础资料与投资估算.xlsx', loc:'Sheet1 B2', conf:96, status:'待确认' },
  { fid:'project.location', cn:'建设地点', val:'广东省惠州市惠城区马安镇', unit:'', file:'项目基础资料与投资估算.xlsx', loc:'Sheet1 B5', conf:95, status:'待确认' },
  { fid:'land.total_area', cn:'总占地面积', val:'3.54', unit:'hm²', file:'项目基础资料与投资估算.xlsx', loc:'占地与土石方 B6', conf:99, status:'待确认' },
  { fid:'earthwork.spoil', cn:'余方量', val:'0', unit:'万 m³', file:'项目基础资料与投资估算.xlsx', loc:'土石方 Sheet E8', conf:92, status:'待确认' },
  { fid:'prevention.scope_area', cn:'防治责任范围面积', val:'3.54', unit:'hm²', file:'项目红线图.pdf', loc:'图件辅助识别', conf:72, status:'待人工确认' },
  { fid:'external.compensation_fee', cn:'补偿费外部对照值', val:'4.25', unit:'万元', file:'项目基础资料与投资估算.xlsx', loc:'投资估算 Sheet D12', conf:88, status:'外部对照', note:'与系统计算值 4.248 存在差异，不覆盖计算器结果' },
];

const INTAKE_MISSING = {
  facts:[
    { id:'project.code', cn:'项目代码', impact:'报告封面、项目基本情况表、交付包 metadata', block:false, advice:'手工填写或上传立项资料' },
    { id:'investment.annual_allocation', cn:'年度投资分配', impact:'年度投资表、交付包完整性', block:false, advice:'上传投资年度分配 Excel，或手动填写' },
  ],
  figures:[
    { id:'措施布局图资料', cn:'措施布局图资料', impact:'水土保持措施总体布局图', block:false, advice:'上传总平图、措施布置图或 CAD 图纸' },
    { id:'监测点位资料', cn:'监测点位资料', impact:'监测点位布设图、监测章节', block:false, advice:'上传监测点位表或手工录入' },
    { id:'红线边界可编辑版本', cn:'红线边界可编辑版本', impact:'防治责任范围图自动装配', block:false, advice:'上传 CAD / SHP / GeoJSON / KML' },
  ],
};

const INTAKE_NEXT = [
  '建议先确认 12 个高置信度候选事实字段，提升项目基本信息、占地与土石方完整度。',
  '建议上传项目代码或立项资料，以完善报告封面和交付包 metadata。',
  '建议将"项目红线图.pdf"登记到附图与地图中心，用于防治责任范围图和图件来源依据。',
  '年度投资分配尚未提供，年度投资表仍将保持 SKELETON。',
  '若要继续完善报告插图，建议生成"水土流失防治责任范围图"。',
  '若要完善监测章节，建议上传监测点位表。',
];

// Excel 导入：Sheet → 字段映射
const EXCEL_SHEETS = {
  '项目基本信息':[
    ['项目名称','世维华南供应链（二期）','project.name','—',98,'已匹配'],
    ['建设单位','广东世维供应链有限公司','project.org','—',96,'已匹配'],
    ['建设地点','广东省惠州市惠城区马安镇','project.location','—',95,'已匹配'],
  ],
  '占地与土石方':[
    ['总占地面积','3.54','land.total_area','hm²',99,'已匹配'],
    ['永久占地','2.86','land.permanent_area','hm²',96,'已匹配'],
    ['临时占地','0.68','land.temporary_area','hm²',95,'已匹配'],
    ['挖方量','12.50','earthwork.excavation','万 m³',94,'已匹配'],
    ['填方量','12.50','earthwork.fill','万 m³',94,'已匹配'],
    ['余方量','0','earthwork.spoil','万 m³',92,'已匹配'],
  ],
  '防治措施':[
    ['工程措施投资','3.64','investment.engineering','万元',90,'已匹配'],
    ['植物措施投资','1.02','investment.plant','万元',90,'已匹配'],
    ['临时措施投资','1.34','investment.temporary','万元',90,'已匹配'],
  ],
  '投资估算':[
    ['水土保持措施投资','6.00','investment.measures_total','万元',88,'需确认'],
    ['补偿费','4.25','external.compensation_fee','万元',88,'外部对照'],
    ['年度投资','空','investment.annual_allocation','万元',0,'缺失'],
  ],
};

// 附图与地图
const FIGURE_CATS = [
  { id:'loc', name:'区位与位置图', done:1, total:1, status:'已完成' },
  { id:'scope', name:'防治责任范围图', done:1, total:1, status:'可生成' },
  { id:'zone', name:'防治分区图', done:0, total:1, status:'待补充' },
  { id:'measure', name:'水土保持措施布局图', done:0, total:1, status:'待补充' },
  { id:'monitor', name:'监测点位布设图', done:1, total:1, status:'已生成' },
  { id:'spoil', name:'弃渣场 / 取土场图', done:0, total:0, status:'不适用' },
  { id:'layout', name:'施工总布置图', done:1, total:1, status:'已上传' },
  { id:'typical', name:'典型措施图', done:1, total:1, status:'已选用' },
  { id:'external', name:'外部附件图纸', done:3, total:3, status:'已上传' },
];

const FIGURES = [
  { id:'FIG-001', name:'项目地理位置图', type:'地图', cat:'loc', source:'系统装配', chapter:'2.1 项目概况', status:'已生成', updated:'今天 09:40', exp:true, map:'loc',
    gen:'区域底图 + 项目位置点', facts:['project.location = 广东省惠州市惠城区马安镇'], tables:['项目基本情况表'], notes:[], review:'可接受' },
  { id:'FIG-002', name:'水土流失防治责任范围图', type:'地图', cat:'scope', source:'红线边界 + 底图装配', chapter:'6 防治责任范围', status:'可生成', updated:'今天 09:41', exp:true, map:'scope',
    gen:'红线边界 + 防治责任范围事实 + 地图模板', facts:['land.total_area = 3.54 hm²','prevention.scope_area = 3.54 hm²','project.location = 广东省惠州市惠城区马安镇'], tables:['防治责任范围表','项目基本情况表'], notes:['[4] 项目用地红线及建设单位提供资料'], review:'可接受，需确认红线来源文件' },
  { id:'FIG-003', name:'水土保持措施总体布局图', type:'地图', cat:'measure', source:'防治分区 + 措施点位', chapter:'7 水土保持措施', status:'待补充', updated:'—', exp:false, map:'measure',
    gen:'防治分区 + 措施点位（资料缺失）', facts:['measures.layout = 待补充'], tables:['防治措施表'], notes:[], review:'缺少措施布局资料' },
  { id:'FIG-004', name:'监测点位布设图', type:'地图', cat:'monitor', source:'监测点位事实', chapter:'8 监测安排', status:'已生成', updated:'今天 09:42', exp:true, map:'monitor',
    gen:'监测点位事实 + 底图', facts:['monitor.points = 4 个'], tables:['监测点位表'], notes:[], review:'可接受' },
  { id:'FIG-005', name:'排水沟典型图', type:'典型图', cat:'typical', source:'典型图库', chapter:'7 水土保持措施', status:'已选用', updated:'今天 09:30', exp:true, map:null,
    gen:'典型图库选用', facts:[], tables:['防治措施表'], notes:[], review:'可接受' },
  { id:'FIG-006', name:'总平面布置图', type:'外部图纸', cat:'external', source:'上传附件', chapter:'2.1 项目概况', status:'待审查', updated:'今天 09:24', exp:true, map:null,
    gen:'上传附件（总平面布置图.png）', facts:[], tables:[], notes:[], review:'待审查' },
];

const FIGURE_TEMPLATES = ['项目地理位置图模板','防治责任范围图模板','防治措施布局图模板','监测点位图模板','弃渣场位置图模板'];

window.CPSWC = { PROJECT, ROLES, NAV, SIX_RATES, KEY_FACTS, RECENT_CHANGES, TODOS,
  USER, PROJECTS, PROJECT_VERSIONS, OP_LOG, RULESET_OPTIONS, PROJECT_TYPES,
  SOURCE_REGISTRY, SOURCE_TYPE_LABELS, SOURCE_TYPE_ICONS, FOOTNOTE_TYPES,
  INTAKE_DOCS, INTAKE_CANDIDATES, INTAKE_MISSING, INTAKE_NEXT, EXCEL_SHEETS,
  FIGURE_CATS, FIGURES, FIGURE_TEMPLATES };
Object.assign(window, { Icon, StatusTag, Panel, MetricCard, Field, Chip });
