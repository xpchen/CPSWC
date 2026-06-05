// ===================================================================
// 智能收资向导（顶栏全局大抽屉）
// AI 辅助层：识别资料 · 提取候选事实 · 提醒缺项 · 引导下一步
// ===================================================================
const { INTAKE_DOCS, INTAKE_CANDIDATES, INTAKE_MISSING, INTAKE_NEXT } = window.CPSWC;

function IntakeSection({ n, title, icon, sub, children, right }) {
  return (
    <section className="border-b border-slate-100 pb-5 mb-5 last:border-0">
      <div className="flex items-center gap-2.5 mb-3">
        <span className="w-6 h-6 rounded-md bg-brand-600 text-white grid place-items-center text-[11px] font-bold shrink-0">{n}</span>
        <Icon name={icon} size={16} className="text-brand-600"/>
        <div className="flex-1">
          <div className="text-[13.5px] font-semibold text-slate-800">{title}</div>
          {sub && <div className="text-[11px] text-slate-400">{sub}</div>}
        </div>
        {right}
      </div>
      {children}
    </section>
  );
}

function ConfBar({ v }) {
  const tone = v>=90 ? 'bg-emerald-500' : v>=80 ? 'bg-brand-500' : 'bg-amber-500';
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="w-12 h-1.5 rounded-full bg-slate-100 overflow-hidden"><span className={`block h-full ${tone}`} style={{width:v+'%'}}></span></span>
      <span className="tabular text-[11px] text-slate-500">{v}%</span>
    </span>
  );
}

function IntakeWizard({ open, onClose, onNavigate }) {
  const [docs, setDocs] = useState(INTAKE_DOCS);
  const [uploading, setUploading] = useState(false);
  const [uploadDone, setUploadDone] = useState(false);
  const [confirmedCount, setConfirmedCount] = useState(0);
  const [cands, setCands] = useState(INTAKE_CANDIDATES.map(c => ({ ...c })));
  const scanSteps = ['正在识别资料内容……','正在判断资料类型……','正在提取候选事实……','正在分析缺失资料……','识别完成。'];
  const [scanIdx, setScanIdx] = useState(0);

  const runUpload = () => {
    setUploading(true); setUploadDone(false); setScanIdx(0);
    let i = 0;
    const t = setInterval(() => { i++; setScanIdx(i); if (i >= scanSteps.length-1) { clearInterval(t); setUploading(false); setUploadDone(true); } }, 520);
  };

  const confirmOne = (fid) => setCands(cs => cs.map(c => c.fid===fid ? { ...c, status:'已确认' } : c));
  const confirmAll = () => {
    setCands(cs => cs.map(c => c.status==='待确认' ? { ...c, status:'已确认' } : c));
    setConfirmedCount(12);
  };

  const go = (page) => { onClose(); onNavigate(page); };

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-slate-900/40" onClick={onClose}></div>
      <aside className="absolute right-0 top-0 bottom-0 w-full max-w-[680px] bg-[#f4f6f9] shadow-2xl flex flex-col animate-[slidein_.2s_ease]">
        <style>{`@keyframes slidein{from{transform:translateX(24px);opacity:.6}to{transform:translateX(0);opacity:1}}`}</style>
        {/* 头部 */}
        <header className="shrink-0 bg-brand-900 text-white px-5 py-3.5 flex items-start gap-3">
          <span className="w-9 h-9 rounded-lg bg-white/10 grid place-items-center mt-0.5"><Icon name="Sparkles" size={19}/></span>
          <div className="flex-1">
            <div className="text-[15px] font-semibold">智能收资向导</div>
            <div className="text-[11.5px] text-brand-200 leading-snug mt-0.5">上传 Excel、图片、红线图、地图、图纸、PDF、Word 等资料，AI 帮助识别已有信息、提取候选事实、分析缺失项，并引导逐步补齐。</div>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-md hover:bg-white/10 grid place-items-center"><Icon name="X" size={18}/></button>
        </header>

        {/* AI 辅助声明 */}
        <div className="shrink-0 px-5 py-2 bg-amber-50 border-b border-amber-100 text-[11px] text-amber-700 flex items-center gap-1.5">
          <Icon name="Info" size={13}/>AI 仅辅助识别与引导，不直接决定最终事实、不覆盖计算器结果，所有候选事实需人工确认后写入。
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-5">
          {/* 上传按钮 */}
          <div className="flex items-center justify-between mb-5">
            <div className="text-[12px] text-slate-500">已收集 {docs.length} 份资料 · {cands.filter(c=>c.status==='已确认').length} 项已确认</div>
            <button onClick={runUpload} disabled={uploading}
              className="inline-flex items-center gap-1.5 text-[12.5px] px-3.5 py-2 rounded-md bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-60">
              <Icon name="Upload" size={15}/>上传资料
            </button>
          </div>

          {/* 上传识别流程 */}
          {(uploading || uploadDone) && (
            <div className="mb-5 rounded-lg border border-brand-200 bg-white p-4">
              {uploading ? (
                <div className="space-y-1.5">
                  {scanSteps.slice(0, scanIdx+1).map((s,i) => (
                    <div key={s} className={`flex items-center gap-2 text-[12.5px] ${i===scanIdx?'text-brand-700 font-medium':'text-slate-400'}`}>
                      <Icon name={i<scanIdx?'CircleCheck':'Loader'} size={14} className={i<scanIdx?'text-emerald-500':'text-brand-500 animate-spin'}/>{s}
                    </div>
                  ))}
                </div>
              ) : (
                <div>
                  <div className="flex items-center gap-2 text-[13px] font-semibold text-slate-700 mb-2"><Icon name="CircleCheck" size={16} className="text-emerald-500"/>已识别资料：项目基础资料与投资估算.xlsx</div>
                  <div className="grid grid-cols-2 gap-2 text-[12px]">
                    {[['事实类信息','15 项','text-brand-700'],['图件类资料','0 项','text-slate-500'],['待人工确认','3 项','text-orange-600'],['发现冲突','1 项','text-red-600']].map(([k,v,c]) => (
                      <div key={k} className="flex items-center justify-between px-2.5 py-1.5 rounded bg-slate-50 border border-slate-100"><span className="text-slate-500">{k}</span><span className={`font-medium ${c}`}>{v}</span></div>
                    ))}
                  </div>
                  <div className="mt-2 text-[11px] text-slate-400">支持 .xlsx / .xls / .csv / .docx / .pdf / .png / .jpg / .dwg / .dxf / .zip</div>
                </div>
              )}
            </div>
          )}

          {/* 1. 已上传资料 */}
          <IntakeSection n="1" title="已上传资料" icon="FolderOpen" sub={`${docs.length} 份`}>
            <div className="space-y-2">
              {docs.map(d => (
                <div key={d.id} className="rounded-lg border border-slate-200 bg-white p-3">
                  <div className="flex items-start gap-2.5">
                    <span className="w-9 h-9 rounded-md bg-slate-50 grid place-items-center text-slate-500 shrink-0"><Icon name={d.icon} size={17}/></span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] font-medium text-slate-800 truncate">{d.name}</span>
                        <StatusTag status={d.status==='已识别'?'已生成':'待识别'} />
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{d.kind} · 上传于 {d.time}</div>
                      <div className="text-[11.5px] text-slate-500 mt-1">{d.note}</div>
                      <div className="mt-2 flex items-center gap-2 flex-wrap">
                        {d.facts>0 && <Chip tone="brand" icon="Database">{d.facts} 候选事实</Chip>}
                        {d.figures>0 && <Chip tone="teal" icon="Map">{d.figures} 图件</Chip>}
                        {d.pending>0 && <Chip tone="amber" icon="CircleHelp">{d.pending} 待确认</Chip>}
                        {d.conflict>0 && <Chip tone="slate" icon="TriangleAlert">{d.conflict} 冲突</Chip>}
                      </div>
                      <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                        {d.action==='excel' && <button onClick={()=>go('facts')} className="text-[11.5px] px-2 py-1 rounded border border-slate-200 text-brand-600 hover:bg-brand-50 inline-flex items-center gap-1"><Icon name="ArrowRight" size={12}/>进入 Excel 导入</button>}
                        {(d.action==='maps'||d.action==='figure') && <button onClick={()=>go('maps')} className="text-[11.5px] px-2 py-1 rounded border border-slate-200 text-teal-600 hover:bg-teal-50 inline-flex items-center gap-1"><Icon name="Map" size={12}/>登记为图件</button>}
                        <button className="text-[11.5px] px-2 py-1 rounded border border-slate-200 text-slate-500 hover:bg-slate-50">查看识别结果</button>
                        <button className="text-[11.5px] px-2 py-1 rounded border border-slate-200 text-slate-400 hover:bg-slate-50">忽略</button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </IntakeSection>

          {/* 2. AI 识别结果 */}
          <IntakeSection n="2" title="AI 识别结果" icon="ScanSearch" sub="按类别归类">
            <div className="grid grid-cols-1 gap-2.5">
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="text-[12px] font-semibold text-slate-600 mb-1.5 flex items-center gap-1.5"><Icon name="Database" size={13} className="text-brand-500"/>事实类信息</div>
                <div className="flex flex-wrap gap-1.5">
                  {['项目名称','建设单位','建设地点','总占地面积 3.54 hm²','永久占地 2.86','临时占地 0.68','挖方 12.50','填方 12.50','余方 0','措施投资 6.00 万元'].map(t=><span key={t} className="text-[11px] px-2 py-0.5 rounded bg-slate-50 border border-slate-100 text-slate-600">{t}</span>)}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <div className="text-[12px] font-semibold text-slate-600 mb-1.5 flex items-center gap-1.5"><Icon name="Map" size={13} className="text-teal-500"/>图件类信息</div>
                  <div className="space-y-1 text-[11.5px] text-slate-500">{['项目红线图','总平面布置图','可生成项目地理位置图','可生成防治责任范围图'].map(t=><div key={t} className="flex items-center gap-1.5"><span className="w-1 h-1 rounded-full bg-teal-400"></span>{t}</div>)}</div>
                </div>
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <div className="text-[12px] font-semibold text-slate-600 mb-1.5 flex items-center gap-1.5"><Icon name="Paperclip" size={13} className="text-slate-400"/>附件类信息</div>
                  <div className="space-y-1 text-[11.5px] text-slate-500">{['建设单位说明资料','总平面布置图附件','红线图附件'].map(t=><div key={t} className="flex items-center gap-1.5"><span className="w-1 h-1 rounded-full bg-slate-300"></span>{t}</div>)}</div>
                </div>
              </div>
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                <div className="text-[12px] font-semibold text-amber-700 mb-1.5 flex items-center gap-1.5"><Icon name="CircleHelp" size={13}/>待人工判断信息</div>
                <div className="space-y-1 text-[11.5px] text-amber-800">
                  <div>prevention.scope_area：可从红线图辅助确认，当前置信度 72%</div>
                  <div>monitoring.points：等待监测点位表映射确认</div>
                  <div>investment.annual_allocation：未识别</div>
                </div>
              </div>
            </div>
          </IntakeSection>

          {/* 3. 候选事实待确认 */}
          <IntakeSection n="3" title="候选事实待确认" icon="ListChecks" sub={`${cands.filter(c=>c.status!=='已确认'&&c.status!=='外部对照').length} 项待确认`}
            right={<button onClick={confirmAll} className="text-[11.5px] px-2.5 py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700 inline-flex items-center gap-1 whitespace-nowrap"><Icon name="CheckCheck" size={13}/>确认写入事实层</button>}>
            {confirmedCount>0 && (
              <div className="mb-2.5 flex items-start gap-2 p-2.5 rounded-md bg-emerald-50 border border-emerald-200 text-[12px] text-emerald-800">
                <Icon name="CircleCheck" size={15} className="text-emerald-600 shrink-0 mt-0.5"/>
                <span>已确认 {confirmedCount} 个候选事实。事实来源已记录，相关字段将在事实填报页显示来源文件和来源位置。</span>
              </div>
            )}
            <div className="rounded-lg border border-slate-200 bg-white overflow-hidden overflow-x-auto">
              <table className="w-full text-[11.5px]">
                <thead><tr className="text-[10.5px] text-slate-400 border-b border-slate-100 bg-slate-50">
                  <th className="text-left font-medium px-2.5 py-2">字段 / 名称</th><th className="text-left font-medium px-2 py-2">候选值</th>
                  <th className="text-left font-medium px-2 py-2">来源</th><th className="text-left font-medium px-2 py-2">置信度</th>
                  <th className="text-left font-medium px-2 py-2">状态</th><th className="px-2 py-2"></th>
                </tr></thead>
                <tbody>
                  {cands.map(c => (
                    <tr key={c.fid} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                      <td className="px-2.5 py-2"><div className="font-mono text-[10.5px] text-slate-400">{c.fid}</div><div className="text-slate-700">{c.cn}</div></td>
                      <td className="px-2 py-2 font-mono tabular text-slate-700">{c.val}{c.unit&&<span className="text-slate-400"> {c.unit}</span>}</td>
                      <td className="px-2 py-2 text-slate-400"><div className="truncate max-w-[120px]">{c.file}</div><div className="text-[10px]">{c.loc}</div></td>
                      <td className="px-2 py-2"><ConfBar v={c.conf}/></td>
                      <td className="px-2 py-2"><StatusTag status={c.status==='已确认'?'通过':c.status==='外部对照'?'外部对照':c.status==='待人工确认'?'待复核':'待确认'} /></td>
                      <td className="px-2 py-2 text-right">{c.status!=='已确认' && c.status!=='外部对照' && <button onClick={()=>confirmOne(c.fid)} className="text-[11px] px-2 py-0.5 rounded bg-brand-50 text-brand-600 hover:bg-brand-100 whitespace-nowrap">确认</button>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-2 flex items-start gap-1.5 text-[11px] text-violet-700 bg-violet-50 border border-violet-200 rounded-md px-2.5 py-2">
              <Icon name="GitCompareArrows" size={13} className="shrink-0 mt-0.5"/>external.compensation_fee（4.25 万元）与系统计算值 4.248 万元存在差异，作为<b>外部对照值</b>保存，不覆盖计算器结果。
            </div>
          </IntakeSection>

          {/* 4. 当前缺失资料 */}
          <IntakeSection n="4" title="当前缺失资料" icon="PackageSearch" sub="非阻塞，建议补齐">
            <div className="space-y-3">
              <div>
                <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">缺失事实</div>
                <div className="space-y-1.5">{INTAKE_MISSING.facts.map(m => (
                  <div key={m.id} className="rounded-md border border-slate-200 bg-white p-2.5">
                    <div className="flex items-center gap-2"><span className="font-mono text-[11px] text-slate-500">{m.id}</span><span className="text-[12px] text-slate-700">{m.cn}</span><StatusTag status="待补充" className="ml-auto"/></div>
                    <div className="text-[11px] text-slate-400 mt-1">影响：{m.impact}</div>
                    <div className="text-[11px] text-brand-600 mt-0.5">建议：{m.advice}</div>
                  </div>
                ))}</div>
              </div>
              <div>
                <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">缺失图件</div>
                <div className="space-y-1.5">{INTAKE_MISSING.figures.map(m => (
                  <div key={m.id} className="rounded-md border border-slate-200 bg-white p-2.5">
                    <div className="flex items-center gap-2"><Icon name="Map" size={13} className="text-teal-500"/><span className="text-[12px] text-slate-700">{m.cn}</span><StatusTag status="待补充" className="ml-auto"/></div>
                    <div className="text-[11px] text-slate-400 mt-1">影响：{m.impact}</div>
                    <div className="text-[11px] text-brand-600 mt-0.5">建议：{m.advice}</div>
                  </div>
                ))}</div>
              </div>
            </div>
          </IntakeSection>

          {/* 5. 下一步建议 */}
          <IntakeSection n="5" title="下一步建议" icon="Compass">
            <ol className="space-y-1.5">
              {INTAKE_NEXT.map((t,i) => (
                <li key={i} className="flex items-start gap-2 text-[12px] text-slate-600"><span className="w-4 h-4 rounded-full bg-brand-100 text-brand-700 grid place-items-center text-[9px] font-bold shrink-0 mt-0.5">{i+1}</span>{t}</li>
              ))}
            </ol>
            <div className="mt-3 rounded-md bg-teal-50 border border-teal-200 p-2.5">
              <div className="text-[11.5px] font-semibold text-teal-700 mb-1.5 flex items-center gap-1.5"><Icon name="Map" size={13}/>建议补充 4 类图件</div>
              <div className="grid grid-cols-2 gap-1.5 text-[11.5px]">
                {[['项目地理位置图','已生成'],['防治责任范围图','可生成'],['措施布局图','待补充'],['监测点位图','已生成']].map(([n,s]) => (
                  <div key={n} className="flex items-center justify-between px-2 py-1 rounded bg-white border border-teal-100"><span className="text-slate-600">{n}</span><StatusTag status={s==='已生成'||s==='已完成'?'已生成':s==='可生成'?'可生成':'待补充'}/></div>
                ))}
              </div>
              <button onClick={()=>go('maps')} className="mt-2 text-[11.5px] text-teal-700 hover:underline inline-flex items-center gap-1">进入附图与地图中心，生成防治责任范围图<Icon name="ArrowRight" size={12}/></button>
            </div>
          </IntakeSection>

          {/* 6. 快捷操作 */}
          <IntakeSection n="6" title="快捷操作" icon="Zap">
            <div className="grid grid-cols-2 gap-2">
              {[['继续上传资料','Upload',runUpload],['打开 Excel 导入','FileSpreadsheet',()=>go('facts')],['打开附图与地图中心','Map',()=>go('maps')],['确认候选事实','CheckCheck',confirmAll],['查看导出前检查','PackageCheck',()=>go('delivery')],['打开正文编辑','FileText',()=>go('narrative')],['查看改动追踪','GitCompareArrows',()=>go('changes')]].map(([label,icon,fn]) => (
                <button key={label} onClick={fn} className="flex items-center gap-2 px-3 py-2 rounded-md border border-slate-200 bg-white text-[12px] text-slate-600 hover:bg-slate-50 hover:border-brand-300 transition-colors">
                  <Icon name={icon} size={14} className="text-brand-500"/>{label}
                </button>
              ))}
            </div>
          </IntakeSection>
        </div>
      </aside>
    </div>
  );
}

window.IntakeWizard = IntakeWizard;
