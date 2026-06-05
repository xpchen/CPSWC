// ===================================================================
// 页 9 交付包
// ===================================================================
const CHECKS = [
  { k:'事实完整性', s:'通过', d:'关键事实满足生成要求（94%）' },
  { k:'规则审查', s:'通过', d:'无阻塞项' },
  { k:'计算器状态', s:'通过', d:'4 / 5 已计算，1 项未触发' },
  { k:'表格状态', s:'待确认', d:'年度投资表为 SKELETON' },
  { k:'正文状态', s:'通过', d:'覆盖率 92%，主要章节已生成' },
  { k:'注脚状态', s:'通过', d:'6 条依据，导出标记完整' },
  { k:'附件状态', s:'待确认', d:'附件目录可生成但未最终确认' },
  { k:'数文一致性', s:'通过', d:'计算值与表格一致' },
  { k:'图件状态', s:'待确认', d:'措施布局图仍为待补充，不阻塞预览导出，建议报批前完成' },
  { k:'人工编辑风险', s:'通过', d:'无人工覆盖风险，正文与计算器一致' },
  { k:'交付文件完整性', s:'通过', d:'14 个交付文件就绪（含图件）' },
];

const FILES = [
  { name:'narrative_skeleton_v0.docx', type:'正文 Word', s:'可下载', time:'09:43', src:'正文引擎', manual:false },
  { name:'formal_tables_v0.docx', type:'正式表格', s:'可下载', time:'09:43', src:'表格中心', manual:false },
  { name:'submission_package.json', type:'交付清单', s:'可下载', time:'09:43', src:'交付引擎', manual:false },
  { name:'workbench.html', type:'HTML 工作台', s:'可下载', time:'09:43', src:'工作台', manual:false },
  { name:'review_trace.html', type:'审查追踪', s:'可下载', time:'09:43', src:'规则引擎', manual:false },
  { name:'evidence_chain.json', type:'证据链', s:'可下载', time:'09:43', src:'改动追踪', manual:false },
  { name:'footnote_registry.json', type:'注脚清单', s:'可下载', time:'09:43', src:'依据库', manual:false },
  { name:'fact_snapshot.json', type:'事实快照', s:'可下载', time:'09:43', src:'事实库', manual:false },
  { name:'figures_manifest.json', type:'图件清单', s:'可下载', time:'09:43', src:'附图与地图', manual:false },
  { name:'maps_export.zip', type:'地图导出包', s:'可下载', time:'09:43', src:'附图与地图', manual:false },
  { name:'location_map.png', type:'区位图', s:'可下载', time:'09:43', src:'FIG-001', manual:false },
  { name:'prevention_scope_map.png', type:'责任范围图', s:'可下载', time:'09:43', src:'FIG-002', manual:false },
  { name:'monitoring_points_map.png', type:'监测点位图', s:'可下载', time:'09:43', src:'FIG-004', manual:false },
];

function DeliveryPage({ frozen, setFrozen }) {
  const [generated, setGenerated] = useState(false);
  const [manualRisk, setManualRisk] = useState(false); // 演示：正文金额被人工改写
  const [activeFile, setActiveFile] = useState('narrative_skeleton_v0.docx');
  const checks = CHECKS.map(c => (manualRisk && c.k==='人工编辑风险')
    ? { ...c, s:'风险', d:'存在 1 处需复核（9.2 补偿费金额 4.5 万元与计算器 4.248 万元不一致）' } : c);
  const files = FILES.map(f => (manualRisk && f.name==='narrative_skeleton_v0.docx') ? { ...f, manual:true } : f);
  const cur = files.find(f=>f.name===activeFile);
  const passN = checks.filter(c=>c.s==='通过').length;
  const warnN = checks.filter(c=>c.s==='待确认').length;
  const riskN = checks.filter(c=>c.s==='风险').length;

  const ACTIONS = [
    { label:'生成预览', icon:'Eye', primary:true, onClick:()=>setGenerated(true) },
    { label:frozen?'解除冻结':'冻结版本', icon:frozen?'LockOpen':'Lock', onClick:()=>setFrozen(f=>!f) },
    { label:'导出 Word', icon:'FileText' },
    { label:'导出正式表格', icon:'Table2' },
    { label:'导出审查包', icon:'ShieldCheck' },
    { label:'查看证据链', icon:'Workflow' },
    { label:'查看注脚清单', icon:'BookMarked' },
  ];

  return (
    <div>
      <PageHeader title="交付包" sub="面向交付 · 导出前检查、文件清单与证据链 — 输出完整 submission package" icon="PackageCheck">
        <StatusTag status={frozen?'已冻结':'未冻结'} dot/>
      </PageHeader>

      <div className="grid grid-cols-[1fr_280px] gap-4 p-5">
        <div className="space-y-4">
          {/* 交付包状态 */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-px bg-slate-200 rounded-lg overflow-hidden border border-slate-200">
            {[
              ['当前版本','v0.6-preview','GitBranch'],
              ['冻结状态',frozen?'已冻结':'未冻结','Lock'],
              ['规则集版本','2026-06 candidate','BookOpen'],
              ['生成状态',generated?'已生成':'可生成','Sparkles'],
              ['是否可提交','可提交（非阻塞）','Send'],
              ['最近生成', generated?'刚刚':'09:43','Clock'],
            ].map(([k,v,icon]) => (
              <div key={k} className="bg-white p-3">
                <div className="flex items-center gap-1.5 text-[10.5px] text-slate-400"><Icon name={icon} size={11}/>{k}</div>
                <div className={`mt-1 text-[12.5px] font-medium ${k==='冻结状态'&&frozen?'text-emerald-600':'text-slate-700'}`}>{v}</div>
              </div>
            ))}
          </div>

          {/* 导出前检查 */}
          <Panel title="导出前检查" sub={`${passN} / ${checks.length} 项通过`} right={
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 text-[11px]">
                <span className="text-emerald-600">通过 {passN}</span>
                <span className="text-orange-600">待确认 {warnN}</span>
                {riskN>0 && <span className="text-red-600">风险 {riskN}</span>}
              </div>
              <button onClick={()=>setManualRisk(r=>!r)} className={`inline-flex items-center gap-1.5 text-[11.5px] px-2.5 py-1 rounded-md border whitespace-nowrap transition-colors ${manualRisk?'bg-orange-500 border-orange-500 text-white':'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'}`}>
                <Icon name="Wand2" size={13}/>{manualRisk?'恢复默认':'模拟正文金额被人工改写'}
              </button>
            </div>
          }>
            <div className="divide-y divide-slate-50">
              {checks.map(c => (
                <div key={c.k} className="flex items-center gap-3 px-4 py-2.5">
                  <Icon name={c.s==='通过'?'CircleCheck':c.s==='风险'?'CircleAlert':'Clock'} size={16}
                    className={c.s==='通过'?'text-emerald-500':c.s==='风险'?'text-red-500':'text-orange-500'}/>
                  <span className="text-[13px] text-slate-700 w-32 shrink-0">{c.k}</span>
                  <span className="text-[12px] text-slate-400 flex-1">{c.d}</span>
                  <StatusTag status={c.s} dot/>
                </div>
              ))}
            </div>
          </Panel>

          {/* 人工编辑风险提示（仅演示后） */}
          {manualRisk ? (
            <div className="flex items-start gap-2.5 px-4 py-3 rounded-lg bg-orange-50 border border-orange-200 text-[12.5px] text-orange-800">
              <Icon name="TriangleAlert" size={16} className="text-orange-500 shrink-0 mt-0.5"/>
              <span>导出前提示：第 <b>9.2 补偿费</b> 段落存在人工编辑（金额 4.5 万元）与计算器结果（4.248 万元）不一致，建议复核后再冻结导出。</span>
            </div>
          ) : (
            <div className="flex items-center gap-2.5 px-4 py-3 rounded-lg bg-emerald-50 border border-emerald-200 text-[12.5px] text-emerald-800">
              <Icon name="ShieldCheck" size={16} className="text-emerald-600 shrink-0"/>
              <span>数文一致性检查通过：正文、表格与计算器结果一致，当前无人工覆盖风险。</span>
            </div>
          )}

          {/* 文件清单 */}
          <Panel title="文件清单" sub="14 个交付文件（含图件）">
            <table className="w-full text-[12.5px]">
              <thead>
                <tr className="text-[11px] text-slate-400 border-b border-slate-100">
                  <th className="text-left font-medium px-4 py-2">文件</th>
                  <th className="text-left font-medium px-2 py-2">类型</th>
                  <th className="text-left font-medium px-2 py-2">状态</th>
                  <th className="text-left font-medium px-2 py-2">来源</th>
                  <th className="text-left font-medium px-2 py-2">人工编辑</th>
                  <th className="px-2 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {files.map(f => {
                  const act = activeFile===f.name;
                  return (
                    <tr key={f.name} onClick={()=>setActiveFile(f.name)} className={`border-b border-slate-50 cursor-pointer transition-colors ${act?'bg-brand-50/70':'hover:bg-slate-50'}`}>
                      <td className="px-4 py-2.5 font-mono text-[11.5px] text-slate-700 flex items-center gap-1.5">
                        <Icon name={f.name.endsWith('.docx')?'FileText':f.name.endsWith('.html')?'Code':f.name.endsWith('.png')?'FileImage':f.name.endsWith('.zip')?'FileArchive':'Braces'} size={13} className="text-slate-400"/>{f.name}
                      </td>
                      <td className="px-2 py-2.5 text-slate-500">{f.type}</td>
                      <td className="px-2 py-2.5"><StatusTag status={f.s} dot/></td>
                      <td className="px-2 py-2.5 text-slate-400">{f.src}</td>
                      <td className="px-2 py-2.5">{f.manual ? <Chip tone="amber" icon="PenLine">含</Chip> : <span className="text-slate-300">—</span>}</td>
                      <td className="px-2 py-2.5 text-right"><Icon name="Download" size={14} className={act?'text-brand-500':'text-slate-300'}/></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>
        </div>

        {/* 右：操作 + 文件详情 */}
        <div className="space-y-4 self-start sticky top-[81px]">
          <Panel title="交付操作">
            <div className="p-3 space-y-2">
              {ACTIONS.map(a => (
                <button key={a.label} onClick={a.onClick}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-[12.5px] transition-colors ${
                    a.primary ? 'bg-brand-600 text-white hover:bg-brand-700' : 'border border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
                  <Icon name={a.icon} size={15}/>{a.label}
                </button>
              ))}
            </div>
          </Panel>

          {generated && (
            <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-[12px] text-emerald-700">
              <Icon name="CircleCheck" size={15}/>预览已生成 · 8 个文件就绪
            </div>
          )}

          <Panel title="文件详情" sub={cur.name}>
            <div className="p-4 space-y-1.5">
              <Field k="文件类型" v={cur.type} />
              <Field k="生成状态" v={cur.s} />
              <Field k="更新时间" v={`今天 ${cur.time}`} />
              <Field k="来源" v={cur.src} />
              <div className="flex items-center justify-between py-1.5">
                <span className="text-[12px] text-slate-400">包含人工编辑</span>
                {cur.manual ? <Chip tone="amber" icon="PenLine">是</Chip> : <span className="text-[12px] text-slate-500">否</span>}
              </div>
              <button className="mt-2 w-full inline-flex items-center justify-center gap-1.5 text-[12px] py-1.5 rounded-md bg-teal-600 text-white hover:bg-teal-700">
                <Icon name="Download" size={14}/>下载文件
              </button>
              {cur.manual && (
                <div className="mt-2 text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1.5 flex items-start gap-1.5">
                  <Icon name="Info" size={12} className="shrink-0 mt-0.5"/>该文件包含人工编辑内容，导出前请确认数文一致性。
                </div>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

window.DeliveryPage = DeliveryPage;
