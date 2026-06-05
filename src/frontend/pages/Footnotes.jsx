// ===================================================================
// 页 7 注脚与依据库
// ===================================================================
const FN_TYPES = [
  { id:'all', name:'全部', icon:'List' },
  { id:'标准依据', name:'标准依据', icon:'BookMarked' },
  { id:'事实来源', name:'事实来源', icon:'Database' },
  { id:'计算依据', name:'计算依据', icon:'Calculator' },
  { id:'审查意见', name:'审查意见', icon:'MessageSquareWarning' },
  { id:'人工说明', name:'人工说明', icon:'PenLine' },
  { id:'版本说明', name:'版本说明', icon:'GitCommitHorizontal' },
  { id:'图件来源', name:'图件来源', icon:'Map' },
];

const { SOURCE_TYPE_LABELS: FN_STL0, SOURCE_TYPE_ICONS: FN_STI0 } = window.CPSWC;
const FN_STL = { ...FN_STL0, figure:'图件' };
const FN_STI = { ...FN_STI0, figure:'Map' };

const FN_DB = [
  { id:'F-001', type:'事实来源', sourceType:'fact', sourceId:'land.total_area', sourceName:'总占地面积 = 3.54 hm²', expert:false, summary:'项目用地红线及建设单位提供资料。', field:'land.total_area', chapter:['2.1 项目概况','9.2 补偿费'], table:['防治责任范围表'], by:'李工 · 编制', time:'2026-06-01', export:true,
    full:'项目用地红线及建设单位提供资料。占地面积 3.54 hm² 经红线图核定，与不动产权属一致。', uses:['2.1 项目概况','9.2 补偿费','防治责任范围表'] },
  { id:'F-002', type:'标准依据', sourceType:'rule', sourceId:'GBT50434-2018', sourceName:'GB/T 50434-2018 表 4.0.2-5', expert:false, summary:'GB/T 50434-2018 表 4.0.2-5。', field:'—', chapter:['7.2 水土流失防治目标'], table:['六率分项目标表'], by:'系统', time:'2026-06-01', export:true,
    full:'依据 GB/T 50434-2018《生产建设项目水土流失防治标准》表 4.0.2-5，南方红壤区一级标准。', uses:['7.2 水土流失防治目标','六率目标计算器','六率分项目标表'] },
  { id:'F-003', type:'计算依据', sourceType:'calculator', sourceId:'calc.fee', sourceName:'补偿费计算器 → 4.248 万元', expert:false, summary:'水土保持补偿费计算器，输入占地面积 3.54 hm²，输出 4.248 万元。', field:'compensation_fee', chapter:['9.2 补偿费'], table:['补偿费计算表'], by:'系统', time:'2026-06-01', export:true,
    full:'水土保持补偿费计算器：输入占地面积 3.54 hm²（35400 m²）× 区域费率 1.20 元/m²，输出 4.248 万元。', uses:['9.2 补偿费','补偿费计算表','投资汇总表'] },
  { id:'F-004', type:'审查意见', sourceType:'rule', sourceId:'GB50433-2018', sourceName:'GB 50433-2018 7.1', expert:true, summary:'方案新增措施布局需经专家确认其针对性。', field:'measures.added', chapter:['7.1 措施布局'], table:['防治措施表'], by:'张工 · 审查', time:'2026-06-02', export:true,
    full:'审查意见：方案新增 6 条措施中，2 条边坡防护措施布局需结合现场地形进一步确认其针对性与合理性。', uses:['7.1 措施布局','防治措施表'] },
  { id:'F-005', type:'人工说明', sourceType:'manual', sourceId:'manual', sourceName:'编制人员补充说明', expert:false, summary:'临时占地于施工结束后及时恢复原地类。', field:'land.temporary_area', chapter:['6 防治责任范围'], table:['防治责任范围表'], by:'李工 · 编制', time:'2026-06-02', export:false,
    full:'人工补充说明：临时占地 0.68 hm² 于施工结束后及时清理并恢复原地类，纳入临时措施管理。', uses:['6 防治责任范围'] },
  { id:'F-006', type:'版本说明', sourceType:'fact', sourceId:'compensation.region_rate', sourceName:'区域费率 = 1.2', expert:true, summary:'区域费率由 1.0 调整为 1.2（惠州市适配规则）。', field:'compensation.region_rate', chapter:['9.2 补偿费'], table:['补偿费计算表'], by:'系统 · 规则更新', time:'2026-06-03', export:true,
    full:'版本说明：依据惠州市区域适配规则，水土保持补偿费区域费率由 1.0 调整为 1.2，补偿费由 3.840 万元更新为 4.248 万元。', uses:['9.2 补偿费','补偿费计算器','补偿费计算表'] },
  { id:'F-007', type:'图件来源', sourceType:'figure', sourceId:'FIG-002', sourceName:'水土流失防治责任范围图', expert:false, summary:'项目用地红线及建设单位提供资料。', field:'prevention.scope_area', chapter:['6 防治责任范围'], table:['防治责任范围表'], by:'李工 · 编制', time:'2026-06-03', export:true,
    full:'图件来源：项目用地红线、建设单位提供资料及系统防治责任范围装配结果。对应正文 图 6-1 水土流失防治责任范围图[4]。', uses:['6 防治责任范围','FIG-002 防治责任范围图'] },
];

function FootnotesPage() {
  const [type, setType] = useState('all');
  const [active, setActive] = useState('F-003');
  const list = FN_DB.filter(f => type==='all' || f.type===type);
  const cur = FN_DB.find(f=>f.id===active) || list[0];
  const counts = FN_TYPES.reduce((a,t)=>{ a[t.id]= t.id==='all'?FN_DB.length:FN_DB.filter(f=>f.type===t.id).length; return a; },{});

  return (
    <div>
      <PageHeader title="注脚与依据库" sub="统一管理标准依据、事实来源、计算来源、审查意见与人工说明" icon="BookMarked">
        <button className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700"><Icon name="Plus" size={14}/>新增依据</button>
      </PageHeader>

      <div className="grid grid-cols-[200px_1fr_340px] h-[calc(100vh-56px-65px)] min-w-[1180px]">
        {/* 左：类型筛选 */}
        <aside className="border-r border-slate-200 bg-white overflow-y-auto p-2">
          <div className="text-[10.5px] font-semibold text-slate-400 uppercase px-2 py-1.5 tracking-wide">依据类型</div>
          {FN_TYPES.map(t => {
            const act = type===t.id;
            return (
              <button key={t.id} onClick={()=>setType(t.id)}
                className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md mb-0.5 transition-colors ${act?'bg-brand-50 text-brand-700':'text-slate-600 hover:bg-slate-50'}`}>
                <Icon name={t.icon} size={15} className={act?'text-brand-600':'text-slate-400'}/>
                <span className="flex-1 text-left text-[12.5px]">{t.name}</span>
                <span className="text-[10px] font-mono tabular text-slate-400">{counts[t.id]}</span>
              </button>
            );
          })}
        </aside>

        {/* 中：列表 */}
        <section className="overflow-y-auto bg-[#eef1f5] p-4">
          <table className="w-full text-[12px] bg-white rounded-lg border border-slate-200 overflow-hidden">
            <thead>
              <tr className="text-[11px] text-slate-400 border-b border-slate-100 bg-slate-50">
                <th className="text-left font-medium px-3 py-2">编号</th>
                <th className="text-left font-medium px-2 py-2">类型</th>
                <th className="text-left font-medium px-2 py-2">内容摘要</th>
                <th className="text-left font-medium px-2 py-2">关联来源类型</th>
                <th className="text-left font-medium px-2 py-2">专家确认</th>
                <th className="text-left font-medium px-2 py-2">创建人</th>
                <th className="text-left font-medium px-2 py-2">导出</th>
              </tr>
            </thead>
            <tbody>
              {list.map(f => {
                const act = active===f.id;
                return (
                  <tr key={f.id} onClick={()=>setActive(f.id)} className={`border-b border-slate-50 cursor-pointer transition-colors ${act?'bg-brand-50/70':'hover:bg-slate-50'}`}>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-slate-500">{f.id}</td>
                    <td className="px-2 py-2.5"><Chip tone="amber">{f.type}</Chip></td>
                    <td className="px-2 py-2.5 text-slate-700 max-w-[230px] truncate">{f.summary}</td>
                    <td className="px-2 py-2.5"><span className="inline-flex items-center gap-1 text-[11px] text-slate-500"><Icon name={FN_STI[f.sourceType]} size={12} className="text-slate-400"/>{FN_STL[f.sourceType]} · {f.sourceId}</span></td>
                    <td className="px-2 py-2.5">{f.expert ? <StatusTag status="专家确认"/> : <span className="text-slate-300">—</span>}</td>
                    <td className="px-2 py-2.5 text-slate-500">{f.by}</td>
                    <td className="px-2 py-2.5">{f.export ? <Icon name="Check" size={14} className="text-emerald-500"/> : <Icon name="Minus" size={14} className="text-slate-300"/>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>

        {/* 右：详情 */}
        <aside className="border-l border-slate-200 bg-white overflow-y-auto">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <span className="font-mono text-[13px] font-semibold text-slate-700">{cur.id}</span>
            <Chip tone="amber">{cur.type}</Chip>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <div className="text-[11px] font-semibold text-slate-400 mb-1.5">注脚完整内容</div>
              <div className="text-[13px] text-slate-700 leading-relaxed bg-slate-50 rounded-md p-3 border border-slate-100 font-serif">{cur.full}</div>
            </div>
            <div>
              <div className="text-[11px] font-semibold text-slate-400 mb-1.5">关联来源（结构化）</div>
              <div className="rounded-md border border-slate-200 overflow-hidden mb-2">
                <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 border-b border-slate-100">
                  <Icon name={FN_STI[cur.sourceType]} size={14} className="text-brand-600"/>
                  <span className="text-[12px] font-medium text-slate-700">{FN_STL[cur.sourceType]}</span>
                  <span className="ml-auto font-mono text-[11px] text-slate-500">{cur.sourceId}</span>
                </div>
                <div className="px-3 py-2 text-[12px] text-slate-600">{cur.sourceName}</div>
              </div>
              <div className="space-y-1.5">
                <Field k="关联字段" v={cur.field} mono />
                <Field k="关联章节" v={cur.chapter.join('、')} />
                <Field k="关联表格" v={cur.table.join('、')} />
              </div>
            </div>
            <div>
              <div className="text-[11px] font-semibold text-slate-400 mb-1.5 flex items-center gap-1.5"><Icon name="Link2" size={12}/>使用位置 · {cur.uses.length}</div>
              <div className="flex flex-wrap gap-1.5">{cur.uses.map(u=><Chip key={u} tone="teal">{u}</Chip>)}</div>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
              <Field k="创建人" v={cur.by} />
              <Field k="创建时间" v={cur.time} />
            </div>
            <div className="flex items-center justify-between px-3 py-2 rounded-md bg-slate-50 border border-slate-100">
              <span className="text-[12px] text-slate-500">导出 Word</span>
              <StatusTag status={cur.export?'通过':'不适用'} dot/>
            </div>
            <div className="flex items-center justify-between px-3 py-2 rounded-md bg-slate-50 border border-slate-100">
              <span className="text-[12px] text-slate-500">是否需专家确认</span>
              {cur.expert ? <StatusTag status="专家确认" dot/> : <span className="text-[12px] text-slate-400">否</span>}
            </div>
            <div className="flex gap-2 pt-1">
              <button className="flex-1 text-[12px] py-1.5 rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 inline-flex items-center justify-center gap-1.5"><Icon name="Link" size={13}/>绑定到段落</button>
              <button className="flex-1 text-[12px] py-1.5 rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 inline-flex items-center justify-center gap-1.5"><Icon name="Pencil" size={13}/>编辑</button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

window.FootnotesPage = FootnotesPage;
