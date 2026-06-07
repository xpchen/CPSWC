// ===================================================================
// 页 2 事实填报
// ===================================================================
const FACT_CATS = [
  { id:'basic',     name:'项目基本信息', icon:'FileSpreadsheet', done:12, total:13 },
  { id:'content',   name:'建设内容',     icon:'Building2', done:5, total:6 },
  { id:'land',      name:'占地与土石方', icon:'Layers', done:7, total:7 },
  { id:'topsoil',   name:'表土剥离与回覆', icon:'Mountain', done:2, total:3 },
  { id:'scope',     name:'防治责任范围', icon:'SquareDashed', done:3, total:3 },
  { id:'sensitive', name:'敏感区逐项排查', icon:'ShieldAlert', done:12, total:12 }, // G-09
  { id:'predict',   name:'水土流失预测', icon:'TrendingDown', done:4, total:4 },
  { id:'disposal',  name:'弃方外运接收方', icon:'Truck', done:1, total:1 }, // G-06
  { id:'measure',   name:'防治措施体系', icon:'ShieldPlus', done:12, total:14 },
  { id:'invest',    name:'投资估算',     icon:'Coins', done:3, total:5 },
  { id:'monitor',   name:'监测与管理',   icon:'Activity', done:4, total:4 },
  { id:'attach',    name:'附件材料',     icon:'Paperclip', done:6, total:8 },
];

// Phase A 落地数据 (Step 53-A1/A2/A3 落地于 facts 层)
const SENSITIVE_AREAS_12  = window.CPSWC.SENSITIVE_AREAS_12  || [];
const ANALOG_PROJECTS     = window.CPSWC.ANALOG_PROJECTS     || [];
const DISPOSAL_RECEIVERS  = window.CPSWC.DISPOSAL_RECEIVERS  || [];

const FACT_FIELDS = {
  basic: [
    { name:'项目名称', id:'project.name', value:'世维华南供应链（二期）', unit:'', src:'立项批复', status:'已校验', impacts:true },
    { name:'建设单位', id:'project.org', value:'广东世维供应链有限公司', unit:'', src:'营业执照', status:'已校验', impacts:true },
    { name:'项目代码', id:'project.code', value:'待补充', unit:'', src:'投资项目代码', status:'缺失', missing:true, impacts:false },
    { name:'建设性质', id:'project.nature', value:'新建', unit:'', src:'立项批复', status:'已校验', impacts:false },
    { name:'项目类型', id:'project.type', value:'物流仓储类生产建设项目', unit:'', src:'可研报告', status:'已校验', impacts:true },
    { name:'建设地点', id:'project.location', value:'广东省惠州市惠城区马安镇', unit:'', src:'项目用地红线', status:'已校验', impacts:true, key:true },
    { name:'所在省份', id:'project.province', value:'广东省', unit:'', src:'用地红线', status:'已校验', impacts:true },
    { name:'所在城市', id:'project.city', value:'惠州市', unit:'', src:'用地红线', status:'已校验', impacts:true },
    { name:'所在区县', id:'project.district', value:'惠城区', unit:'', src:'用地红线', status:'已校验', impacts:false },
    { name:'开工时间', id:'project.start', value:'2026-07', unit:'', src:'建设计划', status:'已校验', impacts:false },
    { name:'完工时间', id:'project.end', value:'2027-06', unit:'', src:'建设计划', status:'已校验', impacts:false },
    { name:'报告编制单位', id:'project.editor_org', value:'广东某某水土保持技术有限公司', unit:'', src:'委托合同', status:'已校验', impacts:false },
    { name:'编制人员', id:'project.editor', value:'李工', unit:'', src:'委托合同', status:'已校验', impacts:false },
  ],
  land: [
    { name:'总占地面积', id:'land.total_area', value:'3.54', unit:'hm²', src:'项目用地红线', status:'已校验', impacts:true, key:true },
    { name:'永久占地', id:'land.permanent_area', value:'2.86', unit:'hm²', src:'用地红线', status:'已校验', impacts:true },
    { name:'临时占地', id:'land.temporary_area', value:'0.68', unit:'hm²', src:'施工组织设计', status:'已校验', impacts:true },
    { name:'挖方量', id:'earthwork.excavation', value:'12.50', unit:'万m³', src:'土石方平衡', status:'已校验', impacts:true },
    { name:'填方量', id:'earthwork.fill', value:'12.50', unit:'万m³', src:'土石方平衡', status:'已校验', impacts:true },
    { name:'借方量', id:'earthwork.borrow', value:'0', unit:'万m³', src:'土石方平衡', status:'已校验', impacts:false },
    { name:'余方量', id:'earthwork.spoil', value:'0', unit:'万m³', src:'土石方平衡', status:'已校验', impacts:true, key:true },
  ],
  measure: [
    { name:'工程措施（条）', id:'measures.engineering', value:'5', unit:'条', src:'措施登记表', status:'已校验', impacts:true },
    { name:'植物措施（条）', id:'measures.plant', value:'4', unit:'条', src:'措施登记表', status:'已校验', impacts:true },
    { name:'临时措施（条）', id:'measures.temporary', value:'3', unit:'条', src:'措施登记表', status:'已校验', impacts:true },
    { name:'主体已列措施', id:'measures.main_listed', value:'8', unit:'条', src:'主体设计', status:'已校验', impacts:true },
    { name:'方案新增措施', id:'measures.added', value:'6', unit:'条', src:'本方案', status:'待确认', impacts:true, key:true },
  ],
  invest: [
    { name:'工程措施投资', id:'investment.engineering', value:'1.20', unit:'万元', src:'投资估算', status:'已校验', impacts:true },
    { name:'植物措施投资', id:'investment.plant', value:'1.02', unit:'万元', src:'投资估算', status:'已校验', impacts:true },
    { name:'临时措施投资', id:'investment.temporary', value:'1.34', unit:'万元', src:'投资估算', status:'已校验', impacts:true },
    { name:'年度投资分配', id:'investment.annual_allocation', value:'—', unit:'万元', src:'待填报', status:'缺失', impacts:true, key:true, missing:true },
    { name:'独立费用', id:'investment.indirect', value:'1.50', unit:'万元', src:'投资估算', status:'已校验', impacts:false },
  ],
};
const FACT_FALLBACK = (cat) => ([
  { name:'示例字段 A', id:`${cat}.field_a`, value:'已填报', unit:'', src:'项目资料', status:'已校验', impacts:true },
  { name:'示例字段 B', id:`${cat}.field_b`, value:'已填报', unit:'', src:'项目资料', status:'已校验', impacts:false },
]);

const FIELD_IMPACTS = {
  'land.total_area': {
    calc:['补偿费计算器','防治目标计算器'],
    tables:['防治责任范围表','补偿费计算表','投资汇总表'],
    narrative:['2.1 项目概况','7.2 防治目标','9.2 补偿费'],
    rules:['补偿费义务 OB-003','责任范围完整性检查'],
    delivery:['formal_tables_v0.docx','narrative_skeleton_v0.docx'],
  },
  'earthwork.spoil': {
    calc:['弃渣场级别计算器','水土流失预测计算器'],
    tables:['土石方平衡表','弃渣场级别表'],
    narrative:['5.2 弃渣场','7.4 弃渣防护'],
    rules:['弃渣场专项 OB-002'],
    delivery:['formal_tables_v0.docx'],
  },
  'investment.annual_allocation': {
    calc:['投资汇总计算器'],
    tables:['年度投资表','投资估算表'],
    narrative:['9.1 投资估算','9.3 进度安排'],
    rules:['年度投资分配 OB-005'],
    delivery:['formal_tables_v0.docx'],
  },
};
const DEFAULT_IMPACT = { calc:['补偿费计算器'], tables:['防治责任范围表'], narrative:['2.1 项目概况'], rules:['责任范围完整性检查'], delivery:['narrative_skeleton_v0.docx'] };

// project.location 专属影响链（演示重点）
FIELD_IMPACTS['project.location'] = {
  rules:['广东省区域规则','惠州市适配规则','区域规则集选择','区域标准等级判断'],
  calc:['补偿费计算器','六率目标计算器','区域标准等级判断'],
  tables:['项目基本情况表','防治责任范围表','补偿费计算表'],
  narrative:['1.1 综合说明','2.1 项目概况','7.2 水土流失防治目标','9.2 水土保持补偿费'],
  delivery:['narrative_skeleton_v0.docx','formal_tables_v0.docx','submission_package.json','fact_snapshot.json'],
};

function FieldRow({ f, active, onClick, simulated }) {
  return (
    <button onClick={onClick}
      className={`w-full text-left rounded-lg border p-3 transition-all ${active ? 'border-brand-400 bg-brand-50/60 ring-1 ring-brand-200' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[13px] font-medium text-slate-800">{f.name}</span>
          {f.key && <span className="text-[10px] px-1.5 py-px rounded bg-teal-50 text-teal-600 border border-teal-200">关键</span>}
          {simulated && <StatusTag status="人工编辑" />}
        </div>
        <StatusTag status={f.missing ? '缺失' : f.status} dot />
      </div>
      <div className="mt-2 flex items-center gap-3 text-[11.5px]">
        <Chip tone="slate" icon="Hash">{f.id}</Chip>
        <span className="font-mono tabular text-slate-700 font-semibold">{simulated ? '3.54' : f.value}{f.unit && ` ${f.unit}`}</span>
      </div>
      <div className="mt-1.5 flex items-center justify-between text-[11px] text-slate-400">
        <span className="inline-flex items-center gap-1"><Icon name="FileInput" size={11}/>来源：{f.src}</span>
        {f.impacts && <span className="inline-flex items-center gap-1 text-brand-500"><Icon name="GitBranch" size={11}/>影响报告</span>}
      </div>
      {f.excel && (
        <div className="mt-1.5 pt-1.5 border-t border-slate-100 flex items-center gap-2 flex-wrap text-[10.5px] text-emerald-600">
          <Icon name="FileSpreadsheet" size={11}/>来源文件：项目基础资料与投资估算.xlsx
          <span className="text-slate-400">· {f.excel} · 导入于刚刚</span>
          {f.extDiff && <span className="text-violet-600">· 外部对照 {f.extDiff}，未覆盖计算值</span>}
        </div>
      )}
    </button>
  );
}

function ImpactGroup({ icon, title, items, tone='brand', onPick }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-[11.5px] font-semibold text-slate-500 mb-1.5"><Icon name={icon} size={13} className={`text-${tone}-500`}/>{title}<span className="text-slate-300 font-normal">· {items.length}</span></div>
      <div className="space-y-1">
        {items.map(it => (
          <div key={it} className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-slate-50 border border-slate-100 text-[12px] text-slate-600 hover:bg-slate-100 transition-colors">
            <span className="w-1 h-1 rounded-full bg-slate-300"></span>{it}
          </div>
        ))}
      </div>
    </div>
  );
}

// ===================================================================
// Excel 事实导入（右侧大抽屉）
// ===================================================================
const EXCEL_SHEETS = window.CPSWC.EXCEL_SHEETS;

function ExcelImportDrawer({ onClose, onImported }) {
  const sheetNames = Object.keys(EXCEL_SHEETS);
  const [sheet, setSheet] = useState(sheetNames[0]);
  const [stage, setStage] = useState('map'); // map | preview | done
  const rows = EXCEL_SHEETS[sheet];

  const previewFields = ['project.name','project.org','project.location','land.total_area','land.permanent_area','land.temporary_area','earthwork.excavation','earthwork.fill','earthwork.spoil','investment.measures_total'];

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-slate-900/40" onClick={onClose}></div>
      <aside className="absolute right-0 top-0 bottom-0 w-full max-w-[760px] bg-[#f4f6f9] shadow-2xl flex flex-col">
        <header className="shrink-0 bg-brand-900 text-white px-5 py-3.5 flex items-start gap-3">
          <span className="w-9 h-9 rounded-lg bg-white/10 grid place-items-center mt-0.5"><Icon name="FileSpreadsheet" size={19}/></span>
          <div className="flex-1">
            <div className="text-[15px] font-semibold">Excel 事实收集</div>
            <div className="text-[11.5px] text-brand-200 mt-0.5">将 Excel 中的项目资料、占地与土石方、投资估算、防治措施等内容映射为 CPSWC 事实字段，确认后写入事实层。</div>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-md hover:bg-white/10 grid place-items-center"><Icon name="X" size={18}/></button>
        </header>

        <div className="px-5 py-2 bg-violet-50 border-b border-violet-100 text-[11px] text-violet-700 flex items-center gap-1.5">
          <Icon name="ShieldCheck" size={13}/>Excel 补偿费 4.25 万元仅作为外部对照值，不覆盖计算器结果 compensation_fee = 4.248 万元。
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {/* 1. 上传区域 */}
          <div className="rounded-lg border border-slate-200 bg-white p-3.5 mb-4">
            <div className="flex items-center gap-3">
              <span className="w-10 h-10 rounded-md bg-emerald-50 grid place-items-center text-emerald-600 shrink-0"><Icon name="FileSpreadsheet" size={20}/></span>
              <div className="flex-1">
                <div className="text-[13px] font-medium text-slate-800">项目基础资料与投资估算.xlsx</div>
                <div className="text-[11px] text-slate-400">支持 .xlsx / .xls / .csv</div>
              </div>
              <StatusTag status="已生成" dot/>
            </div>
            <div className="mt-3 grid grid-cols-5 gap-px bg-slate-100 rounded-md overflow-hidden text-center">
              {[['Sheet 数量','4'],['识别字段','18'],['自动匹配','15'],['需确认','3'],['冲突','1']].map(([k,v]) => (
                <div key={k} className="bg-white py-2"><div className="text-[18px] font-bold text-slate-800 tabular">{v}</div><div className="text-[10px] text-slate-400">{k}</div></div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-[1fr_300px] gap-4">
            {/* 左：Sheet 识别 + 映射 */}
            <div>
              <div className="flex items-center gap-1 mb-2 border-b border-slate-200">
                {sheetNames.map(s => (
                  <button key={s} onClick={()=>setSheet(s)} className={`text-[12px] px-3 py-2 transition-colors ${sheet===s?'text-brand-600 border-b-2 border-brand-600 font-medium':'text-slate-500 hover:text-slate-700'}`}>{s}</button>
                ))}
              </div>
              <div className="rounded-lg border border-slate-200 bg-white overflow-hidden overflow-x-auto">
                <table className="w-full text-[11.5px]">
                  <thead><tr className="text-[10.5px] text-slate-400 border-b border-slate-100 bg-slate-50">
                    <th className="text-left font-medium px-2.5 py-2">Excel 列 / 值</th><th className="text-left font-medium px-2 py-2">CPSWC 字段</th>
                    <th className="text-left font-medium px-2 py-2">单位</th><th className="text-left font-medium px-2 py-2">置信</th><th className="text-left font-medium px-2 py-2">状态</th>
                  </tr></thead>
                  <tbody>
                    {rows.map((r,i) => (
                      <tr key={i} className="border-b border-slate-50 last:border-0">
                        <td className="px-2.5 py-2"><div className="text-slate-700">{r[0]}</div><div className="font-mono text-[10px] text-slate-400">{r[1]}</div></td>
                        <td className="px-2 py-2 font-mono text-[10.5px] text-brand-700">{r[2]}</td>
                        <td className="px-2 py-2 text-slate-500">{r[3]}</td>
                        <td className="px-2 py-2 tabular text-slate-500">{r[4]?r[4]+'%':'—'}</td>
                        <td className="px-2 py-2"><StatusTag status={r[5]==='已匹配'?'已匹配':r[5]==='需确认'?'需确认':r[5]==='外部对照'?'外部对照':'缺失'} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 右：映射摘要 + 校验 */}
            <div className="space-y-3">
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="text-[12px] font-semibold text-slate-700 mb-2">将导入</div>
                <div className="space-y-1 text-[11.5px]">
                  {[['项目基本信息','7 项'],['占地与土石方','5 项'],['投资估算','3 项'],['防治措施','3 项']].map(([k,v]) => (
                    <div key={k} className="flex items-center justify-between"><span className="text-slate-500">{k}</span><span className="text-slate-700 font-medium">{v}</span></div>
                  ))}
                </div>
                <div className="mt-2 pt-2 border-t border-slate-100 text-[11px] text-slate-500">需人工确认：</div>
                <div className="mt-1 space-y-0.5 font-mono text-[10.5px] text-orange-600">
                  <div>investment.measures_total</div><div>investment.annual_allocation</div><div>attachments.redline_map</div>
                </div>
              </div>
              <div className="rounded-lg border border-violet-200 bg-violet-50 p-3 text-[11.5px] text-violet-800">
                <div className="font-semibold mb-1 flex items-center gap-1.5"><Icon name="GitCompareArrows" size={13}/>冲突提示</div>
                Excel 补偿费 4.25 万元，系统计算值 4.248 万元，差异 0.002 万元。建议作为外部对照值保存，不覆盖系统计算值。
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="text-[12px] font-semibold text-slate-700 mb-2">导入前校验</div>
                <div className="space-y-1">
                  {[['字段映射完整性','通过'],['单位识别','通过'],['必填字段','待补充'],['数值冲突','需确认'],['覆盖已有事实','否'],['影响地图图件','是 · 3 张']].map(([k,v]) => (
                    <div key={k} className="flex items-center justify-between text-[11.5px]"><span className="text-slate-500">{k}</span><StatusTag status={v==='通过'?'通过':v==='待补充'?'待补充':v==='需确认'?'需确认':v==='否'?'不适用':'已生成'} /></div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border border-teal-200 bg-teal-50 p-3 text-[11.5px] text-teal-800">
                <div className="font-semibold mb-1 flex items-center gap-1.5"><Icon name="Map" size={13}/>影响地图图件：3 张</div>
                project.location / land.total_area / prevention.scope_area / monitoring.points 将影响 项目地理位置图、防治责任范围图、监测点位布设图。
              </div>
            </div>
          </div>

          {/* 事实变更预览 */}
          {stage==='preview' && (
            <div className="mt-4 rounded-lg border border-brand-200 bg-white p-3.5">
              <div className="text-[12.5px] font-semibold text-slate-700 mb-2 flex items-center gap-1.5"><Icon name="ListChecks" size={14} className="text-brand-600"/>将新增 / 更新事实（{previewFields.length}）</div>
              <div className="flex flex-wrap gap-1.5">{previewFields.map(f=><span key={f} className="font-mono text-[11px] px-2 py-0.5 rounded bg-brand-50 text-brand-700 border border-brand-100">{f}</span>)}</div>
            </div>
          )}

          {/* 导入结果 */}
          {stage==='done' && (
            <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3.5">
              <div className="flex items-center gap-2 text-[13px] font-semibold text-emerald-800 mb-1.5"><Icon name="CircleCheck" size={16} className="text-emerald-600"/>导入成功</div>
              <div className="text-[12px] text-emerald-700 space-y-0.5">
                <div>已导入 15 个事实字段，其中 12 项自动通过，3 项需人工确认。</div>
                <div>事实来源已记录为：项目基础资料与投资估算.xlsx。</div>
                <div>影响图件：3 张（项目地理位置图、防治责任范围图、监测点位布设图）。</div>
              </div>
            </div>
          )}
        </div>

        {/* 底部操作 */}
        <footer className="shrink-0 px-5 py-3 border-t border-slate-200 bg-white flex items-center justify-end gap-2">
          {stage==='done' ? (
            <button onClick={onImported} className="text-[13px] px-4 py-2 rounded-md bg-brand-600 text-white hover:bg-brand-700">完成并返回事实填报</button>
          ) : (
            <>
              <button onClick={onClose} className="text-[13px] px-3.5 py-2 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50">取消</button>
              <button className="text-[13px] px-3.5 py-2 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50">仅保存映射</button>
              <button onClick={()=>setStage('preview')} className="text-[13px] px-3.5 py-2 rounded-md border border-brand-300 text-brand-700 hover:bg-brand-50">预览事实变更</button>
              <button onClick={()=>setStage('done')} className="text-[13px] px-4 py-2 rounded-md bg-brand-600 text-white hover:bg-brand-700 inline-flex items-center gap-1.5"><Icon name="Check" size={14}/>确认导入</button>
            </>
          )}
        </footer>
      </aside>
    </div>
  );
}

function FactsPage() {
  const [cat, setCat] = useState('basic');
  const [active, setActive] = useState('project.location');
  const [simulated, setSimulated] = useState(false);   // land 演示
  const [codeFilled, setCodeFilled] = useState(false); // 补齐项目代码
  const [locChanged, setLocChanged] = useState(false); // 模拟修改建设地点
  const [saved, setSaved] = useState(false);           // 保存并校验
  const [excelOpen, setExcelOpen] = useState(false);
  const [imported, setImported] = useState(false);     // Excel 导入完成

  // 派生字段值（基本信息受演示状态影响）
  let fields = FACT_FIELDS[cat] || FACT_FALLBACK(cat);
  if (cat === 'basic') fields = fields.map(f => {
    if (f.id === 'project.code') return { ...f, value: codeFilled ? '2405-441302-04-01-865321' : '待补充', status: codeFilled ? '已校验' : '缺失', missing: !codeFilled };
    if (f.id === 'project.location') return { ...f, value: locChanged ? '广东省深圳市龙岗区' : '广东省惠州市惠城区马安镇' };
    if (f.id === 'project.city') return { ...f, value: locChanged ? '深圳市' : '惠州市' };
    if (f.id === 'project.district') return { ...f, value: locChanged ? '龙岗区' : '惠城区' };
    if (f.id === 'project.province') return { ...f, value: locChanged ? '广东省' : '广东省' };
    return f;
  });
  const activeField = fields.find(f => f.id === active) || fields[0];
  const impact = FIELD_IMPACTS[active] || DEFAULT_IMPACT;
  const isBasic = cat === 'basic';

  // 导入后注入 Excel 来源追溯
  const EXCEL_SRC = {
    'project.name':'Sheet1 A2','project.org':'Sheet1 B2','project.location':'Sheet1 B5',
    'land.total_area':'占地与土石方 / B6','land.permanent_area':'占地与土石方 / B7','land.temporary_area':'占地与土石方 / B8',
    'earthwork.excavation':'土石方 / C5','earthwork.fill':'土石方 / D5','earthwork.spoil':'土石方 / E8',
    'investment.measures_total':'投资估算 / D12',
  };
  if (imported) fields = fields.map(f => {
    if (f.id==='external.compensation_fee') return { ...f, excel:'投资估算 / D12', extDiff:'4.25 万元（系统 4.248）' };
    if (EXCEL_SRC[f.id]) return { ...f, excel: EXCEL_SRC[f.id] };
    return f;
  });

  useEffect(() => { if (!fields.find(f=>f.id===active)) setActive(fields[0].id); }, [cat]);

  const curCat = FACT_CATS.find(c => c.id === cat);

  return (
    <div>
      <PageHeader title="事实填报" sub="事实驱动 · 录入项目事实，系统据此生成审查、计算、表格与正文" icon="Database">
        <button onClick={()=>setExcelOpen(true)} className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 whitespace-nowrap"><Icon name="FileSpreadsheet" size={14} className="text-emerald-600"/>Excel 导入事实</button>
        <Chip tone="emerald" icon="CircleCheck">事实完整度 94%</Chip>
      </PageHeader>
      {excelOpen && <ExcelImportDrawer onClose={()=>setExcelOpen(false)} onImported={()=>{ setImported(true); setExcelOpen(false); }} />}

      <div className="grid grid-cols-[230px_1fr_320px] gap-0 h-[calc(100vh-56px-65px)] min-w-[1180px]">
        {/* 左：分类树 */}
        <aside className="border-r border-slate-200 bg-white overflow-y-auto">
          <div className="p-2.5">
            <div className="text-[10.5px] font-semibold text-slate-400 uppercase px-2 mb-1.5 tracking-wide">事实分类</div>
            {FACT_CATS.map(c => {
              const act = cat === c.id;
              const full = c.done === c.total;
              return (
                <button key={c.id} onClick={()=>setCat(c.id)}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md mb-0.5 transition-colors ${act ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-50'}`}>
                  <Icon name={c.icon} size={15} className={act ? 'text-brand-600' : 'text-slate-400'}/>
                  <span className="flex-1 text-left text-[12.5px]">{c.name}</span>
                  <span className={`text-[10px] font-mono tabular px-1.5 py-px rounded ${full ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>{c.done}/{c.total}</span>
                </button>
              );
            })}
          </div>
        </aside>

        {/* 中：表单 */}
        <section className="overflow-y-auto bg-[#eef1f5] p-5">
          {imported && (
            <div className="mb-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3.5 py-2.5">
              <div className="flex items-center gap-2 text-[12.5px] text-emerald-800">
                <Icon name="FileSpreadsheet" size={15} className="text-emerald-600"/>
                <span className="font-semibold">最近导入：</span>项目基础资料与投资估算.xlsx
                <span className="ml-auto text-[11px] text-emerald-600">导入人：李工 · 刚刚</span>
              </div>
              <div className="mt-1 flex items-center gap-4 text-[11.5px] text-emerald-700 pl-7">
                <span>导入字段：15</span><span>自动通过：12</span><span>需确认：3</span><span>影响图件：3 张</span>
              </div>
            </div>
          )}
          <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
            <div className="flex items-center gap-2 text-[13px] font-semibold text-slate-700">
              <Icon name={curCat.icon} size={16} className="text-brand-600"/>{curCat.name}
              <span className="text-[11px] font-normal text-slate-400">共 {fields.length} 个字段</span>
            </div>
            {isBasic ? (
              <div className="flex items-center gap-1.5 flex-wrap">
                <button onClick={()=>{ setActive('project.code'); setCodeFilled(true); }} disabled={codeFilled}
                  className={`inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1.5 rounded-md whitespace-nowrap transition-colors ${codeFilled?'bg-slate-100 text-slate-400 cursor-default':'bg-brand-600 text-white hover:bg-brand-700'}`}>
                  <Icon name="ClipboardCheck" size={14}/>补齐项目代码
                </button>
                <button onClick={()=>{ setActive('project.location'); setLocChanged(true); }} disabled={locChanged}
                  className={`inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1.5 rounded-md whitespace-nowrap transition-colors ${locChanged?'bg-slate-100 text-slate-400 cursor-default':'bg-orange-500 text-white hover:bg-orange-600'}`}>
                  <Icon name="MapPinned" size={14}/>模拟修改建设地点
                </button>
                <button onClick={()=>setSaved(true)}
                  className="inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1.5 rounded-md bg-teal-600 text-white hover:bg-teal-700 whitespace-nowrap transition-colors">
                  <Icon name="Save" size={14}/>保存并校验事实
                </button>
              </div>
            ) : (
              <button onClick={()=>{ setActive('land.total_area'); setCat('land'); setSimulated(true); }}
                className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md bg-orange-500 text-white hover:bg-orange-600 transition-colors whitespace-nowrap">
                <Icon name="Wand2" size={14}/>模拟修改 land.total_area
              </button>
            )}
          </div>

          {/* 演示反馈框 */}
          {isBasic && codeFilled && (
            <div className="mb-3 flex items-start gap-2.5 p-3 rounded-lg bg-brand-50 border border-brand-200 text-[12.5px] text-brand-800">
              <Icon name="CircleCheck" size={16} className="text-brand-600 shrink-0 mt-0.5"/>
              <span><b>项目代码已补齐：</b>2405-441302-04-01-865321。项目基本情况表、报告封面信息和交付包 metadata 已更新。</span>
            </div>
          )}
          {isBasic && locChanged && (
            <div className="mb-3 p-3 rounded-lg bg-orange-50 border border-orange-200 text-[12.5px] text-orange-800">
              <div className="flex items-start gap-2.5">
                <Icon name="TriangleAlert" size={16} className="text-orange-500 shrink-0 mt-0.5"/>
                <div className="flex-1">
                  <b>区域发生变化，规则集需要重新确认。</b>建设地点由「广东省惠州市惠城区马安镇」变更为「广东省深圳市龙岗区」。
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {['广东省区域规则','惠州市适配规则 → 深圳市区域规则待确认','补偿费计算器','六率目标计算器','项目基本情况表','补偿费计算表','2.1 项目概况','7.2 水土流失防治目标','9.2 水土保持补偿费','交付包 metadata'].map(t=>(
                      <span key={t} className="text-[11px] px-2 py-0.5 rounded bg-white border border-orange-200 text-orange-700">{t}</span>
                    ))}
                  </div>
                  <button onClick={()=>setLocChanged(false)} className="mt-2 underline text-orange-600">撤销</button>
                </div>
              </div>
            </div>
          )}
          {isBasic && saved && (
            <div className="mb-3 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-[12.5px] text-emerald-800">
              <div className="flex items-center gap-2 mb-1.5 font-semibold"><Icon name="ShieldCheck" size={15}/>保存并校验完成</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {['项目基本信息校验通过','区域规则集识别完成','正文 2.1 项目概况已生成','项目基本情况表状态变为 LIVE','交付包 fact_snapshot.json 已更新'].map(t=>(
                  <div key={t} className="flex items-center gap-1.5"><Icon name="Check" size={13} className="text-emerald-600"/>{t}</div>
                ))}
              </div>
            </div>
          )}

          {/* Phase A · G-09 敏感区逐项排查 */}
          {cat === 'sensitive' && (
            <Panel title="敏感区 12 类逐项排查"
              sub="源 · SensitiveAreaTypeRegistry_v0 · 命中清单回写 field.fact.natural.other_sensitive_areas"
              right={<Chip tone="emerald" icon="ShieldCheck">命中 0 / 12</Chip>}>
              <div className="overflow-x-auto">
                <table className="w-full text-[12px]">
                  <thead className="bg-slate-50 text-[10.5px] text-slate-500">
                    <tr>
                      <th className="text-left font-medium px-3 py-2 w-10">#</th>
                      <th className="text-left font-medium px-3 py-2">类型</th>
                      <th className="text-left font-medium px-3 py-2">code</th>
                      <th className="text-left font-medium px-3 py-2">审批主体</th>
                      <th className="text-left font-medium px-3 py-2">排查结论</th>
                      <th className="text-left font-medium px-3 py-2 w-16">状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {SENSITIVE_AREAS_12.map((s, i) => (
                      <tr key={s.code} className="border-t border-slate-100">
                        <td className="px-3 py-2 text-slate-400 tabular">{i+1}</td>
                        <td className="px-3 py-2 text-slate-800 font-medium">{s.name}</td>
                        <td className="px-3 py-2 font-mono text-[10.5px] text-brand-700">{s.code}</td>
                        <td className="px-3 py-2 text-slate-500">{s.authority}</td>
                        <td className="px-3 py-2 text-slate-600">{s.conclusion}</td>
                        <td className="px-3 py-2"><StatusTag status={s.hit ? '已命中' : '不适用'} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          )}

          {/* Phase A · G-06 弃方外运接收方实名 */}
          {cat === 'disposal' && (
            <Panel title="弃方外运接收方实名 + 批复挂钩"
              sub="源 · field.fact.disposal.external_receivers · narrative §5.disposal v2"
              right={<Chip tone="emerald" icon="ShieldCheck">已批复</Chip>}>
              <div className="p-4 space-y-3">
                {DISPOSAL_RECEIVERS.map((r, i) => (
                  <div key={i} className="rounded-lg border border-slate-200 bg-white p-3.5">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-[13px] font-semibold text-slate-800">{r.receiver_project_name}</div>
                      <StatusTag status={r.receiver_swc_status} dot />
                    </div>
                    <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-[11.5px]">
                      <Field k="接收方位置" v={r.receiver_location} />
                      <Field k="运距" v={`${r.distance_km} km`} mono />
                      <Field k="运输路线" v={r.transport_route} />
                      <Field k="接收量" v={`${r.volume_received.value} ${r.volume_received.unit}`} mono />
                      <Field k="时间窗口" v={r.timing_window} />
                      <Field k="接收方水保批复" v={r.receiver_swc_approval_id} />
                    </div>
                    <div className="mt-2.5 pt-2.5 border-t border-slate-100 space-y-1 text-[11px] text-slate-500">
                      <div className="flex items-start gap-1.5"><Icon name="Paperclip" size={12} className="mt-0.5 text-slate-400"/><span>批复证明：{r.receiver_swc_approval_attachment}</span></div>
                      <div className="flex items-start gap-1.5"><Icon name="Network" size={12} className="mt-0.5 text-slate-400"/><span>权属关系：{r.ownership_relation_statement}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {/* Phase A · 普通分类的字段行 */}
          {cat !== 'sensitive' && cat !== 'disposal' && (
            <div className="space-y-2.5">
              {fields.map(f => (
                <FieldRow key={f.id} f={f} active={active===f.id} onClick={()=>setActive(f.id)} simulated={simulated && f.id==='land.total_area'} />
              ))}
            </div>
          )}

          {/* Phase A · G-11 类比工程实名 (附在水土流失预测末尾) */}
          {cat === 'predict' && ANALOG_PROJECTS.length > 0 && (
            <div className="mt-4">
              <Panel title="类比工程实名 + 6 维可比性"
                sub="源 · AnalogProjectRegistry_v0 · narrative §7.4.3 表 7.4-3"
                right={<Chip tone="brand" icon="Link2">field.fact.prediction.analog_project_ref</Chip>}>
                <div className="p-4 space-y-3">
                  {ANALOG_PROJECTS.map(ap => (
                    <div key={ap.id} className="rounded-lg border border-slate-200 bg-white p-3.5">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <div className="text-[13px] font-semibold text-slate-800">{ap.name}</div>
                          <div className="text-[11px] text-slate-400 mt-0.5">{ap.project_type} · {ap.location}</div>
                        </div>
                        <Chip tone="emerald" icon="ShieldCheck">{ap.audit_status.includes('已用于') ? '审批已采纳' : '可比'}</Chip>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-[11.5px]">
                          <thead className="text-[10.5px] text-slate-400">
                            <tr><th className="text-left font-medium px-2 py-1.5 w-16">维度</th>
                                <th className="text-left font-medium px-2 py-1.5">本项目</th>
                                <th className="text-left font-medium px-2 py-1.5">类比工程</th>
                                <th className="text-left font-medium px-2 py-1.5 w-20">结论</th></tr>
                          </thead>
                          <tbody>
                            {ap.comparability.map(c => (
                              <tr key={c.dim} className="border-t border-slate-100">
                                <td className="px-2 py-1.5 text-slate-600">{c.dim}</td>
                                <td className="px-2 py-1.5 text-slate-700">{c.self}</td>
                                <td className="px-2 py-1.5 text-slate-700">{c.analog}</td>
                                <td className="px-2 py-1.5"><StatusTag status={c.ok ? '一致' : '不一致'} /></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="mt-2.5 pt-2.5 border-t border-slate-100 text-[11px] text-slate-500 flex items-start gap-1.5">
                        <Icon name="Quote" size={12} className="mt-0.5 text-slate-400"/>
                        <span>引用：{ap.citation_source}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
            </div>
          )}
          {simulated && !isBasic && (
            <div className="mt-4 flex items-start gap-2.5 p-3.5 rounded-lg bg-orange-50 border border-orange-200 text-[12.5px] text-orange-800">
              <Icon name="Zap" size={16} className="text-orange-500 shrink-0 mt-0.5"/>
              <div>
                <b>land.total_area 已模拟修改：3.20 → 3.54 hm²。</b> 系统检测到该修改影响
                <b> 1 个计算器 · 3 张表格 · 5 个正文段落 · 2 项规则</b>。请前往「改动追踪」查看完整证据链。
                <button onClick={()=>setSimulated(false)} className="ml-2 underline text-orange-600">撤销模拟</button>
              </div>
            </div>
          )}
        </section>

        {/* 右：影响预览 */}
        <aside className="border-l border-slate-200 bg-white overflow-y-auto">
          <div className="px-4 py-3 border-b border-slate-100 sticky top-0 bg-white">
            <div className="text-[12px] font-semibold text-slate-700 flex items-center gap-1.5"><Icon name="Radar" size={14} className="text-brand-600"/>影响预览
              {active==='project.location' && <span className="ml-1 text-[10px] px-1.5 py-px rounded bg-orange-50 text-orange-600 border border-orange-200">区域驱动</span>}
            </div>
            <div className="mt-1.5 flex items-center gap-2 flex-wrap">
              <Chip tone="brand" icon="Hash">{activeField.id}</Chip>
              <span className="font-mono tabular text-[12px] font-semibold text-slate-700">{activeField.value}{activeField.unit}</span>
            </div>
          </div>
          <div className="p-4 space-y-4">
            {active==='project.location' && locChanged && (
              <div className="flex items-start gap-2 text-[11.5px] text-orange-700 bg-orange-50 border border-orange-200 rounded-md px-2.5 py-2">
                <Icon name="TriangleAlert" size={13} className="shrink-0 mt-0.5"/>区域已变更，下列规则集、计算器与表格均需重新确认。
              </div>
            )}
            <ImpactGroup icon="Gavel" title="影响规则" items={impact.rules} tone="amber" />
            <ImpactGroup icon="Calculator" title="影响计算器" items={impact.calc} />
            <ImpactGroup icon="Table2" title="影响表格" items={impact.tables} tone="teal" />
            <ImpactGroup icon="FileText" title="影响正文" items={impact.narrative} tone="brand" />
            <ImpactGroup icon="Package" title="影响交付包" items={impact.delivery} />
          </div>
        </aside>
      </div>
    </div>
  );
}

window.FactsPage = FactsPage;
