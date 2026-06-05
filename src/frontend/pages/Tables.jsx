// ===================================================================
// 页 5 表格中心
// ===================================================================
const TABLE_LIST = [
  { id:'scope', name:'防治责任范围表', status:'LIVE', cat:'占地' },
  { id:'predict', name:'水土流失预测表', status:'LIVE', cat:'预测' },
  { id:'sixrate', name:'六率分项目标表', status:'LIVE', cat:'目标' },
  { id:'measure', name:'防治措施投资表', status:'LIVE', cat:'措施' },
  { id:'fee', name:'补偿费计算表', status:'LIVE', cat:'投资' },
  { id:'annual', name:'年度投资表', status:'SKELETON', cat:'投资' },
  { id:'attach', name:'附件目录表', status:'CAN_GENERATE', cat:'附件' },
  { id:'spoil', name:'弃渣场级别表', status:'NOT_APPLICABLE', cat:'措施' },
  { id:'basic', name:'项目基本表', status:'LIVE', cat:'基本' },
  { id:'earth', name:'土石方平衡表', status:'LIVE', cat:'占地' },
  { id:'topsoil', name:'表土平衡表', status:'LIVE', cat:'占地' },
  { id:'monitor', name:'监测点位表', status:'LIVE', cat:'监测' },
];

const SIXRATE_ROWS = [
  ['水土流失治理度','97%','97.6%','达标','GB/T 50434-2018 表4.0.2-5'],
  ['土壤流失控制比','1.0','1.0','达标','GB/T 50434-2018 表4.0.2-5'],
  ['渣土防护率','92%','95.0%','达标','GB/T 50434-2018 表4.0.2-5'],
  ['表土保护率','92%','94.0%','达标','GB/T 50434-2018 表4.0.2-5'],
  ['林草植被恢复率','97%','97.2%','达标','GB/T 50434-2018 表4.0.2-5'],
  ['林草覆盖率','22%','23.1%','达标','GB/T 50434-2018 表4.0.2-5'],
];
const MEASURE_ROWS = [
  ['工程措施','排水沟','2.44','1.20','3.64','measures_registry'],
  ['植物措施','撒播草籽','0.50','0.52','1.02','measures_registry'],
  ['临时措施','临时覆盖','0.50','0.84','1.34','measures_registry'],
];

const TABLE_SOURCE = {
  sixrate: { facts:['prevention.scope_area = 3.54 hm²','region.type = 南方红壤区'], calc:['六率目标计算器'], rules:['GB/T 50434-2018 表4.0.2-5'], narrative:['7.2 水土流失防治目标'], export:'formal_tables_v0.docx · 附表 5' },
  measure: { facts:['measures.engineering = 5','measures.plant = 4','measures.temporary = 3'], calc:['防治措施投资汇总计算器'], rules:['GB 50433-2018 8.1'], narrative:['7.3 措施投资','9.1 投资估算'], export:'formal_tables_v0.docx · 附表 8' },
};

function StatusDotList({ list, active, setActive }) {
  const cats = [...new Set(list.map(t=>t.cat))];
  return (
    <div className="p-2">
      {cats.map(cat => (
        <div key={cat} className="mb-2">
          <div className="text-[10.5px] font-semibold text-slate-400 px-2 py-1 uppercase tracking-wide">{cat}</div>
          {list.filter(t=>t.cat===cat).map(t => {
            const act = active===t.id;
            const can = t.status==='LIVE'||t.status==='CAN_GENERATE'||t.status==='SKELETON';
            return (
              <button key={t.id} onClick={()=>can && setActive(t.id)} disabled={!can}
                className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md mb-0.5 text-left transition-colors ${
                  act ? 'bg-brand-50' : can ? 'hover:bg-slate-50' : 'opacity-50 cursor-not-allowed'}`}>
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  t.status==='LIVE'?'bg-emerald-500':t.status==='CAN_GENERATE'?'bg-brand-500':t.status==='SKELETON'?'bg-amber-500':'bg-slate-300'}`}></span>
                <span className={`flex-1 text-[12.5px] ${act?'text-brand-700 font-medium':'text-slate-600'}`}>{t.name}</span>
                <StatusTag status={t.status} />
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}

function FormalTable({ id, highlight }) {
  if (id === 'sixrate') {
    return (
      <table className="w-full text-[12.5px] border-collapse">
        <thead>
          <tr className="bg-slate-100 text-slate-600">
            {['指标','目标值','实际预测值','达标状态','依据'].map((h,i) => <th key={i} className="border border-slate-300 px-3 py-2 font-semibold text-left">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {SIXRATE_ROWS.map((r,ri) => (
            <tr key={ri} className="hover:bg-brand-50/30">
              {r.map((c,ci) => (
                <td key={ci} className={`border border-slate-300 px-3 py-2 ${ci===0?'font-medium text-slate-700':ci>=1&&ci<=2?'tabular text-center':'text-slate-500'} ${highlight==='actual'&&ci===2?'bg-amber-100 ring-1 ring-amber-300':''}`}>
                  {ci===3 ? <StatusTag status="通过" /> : ci===4 ? <span className="text-[11px] text-slate-400">{c}</span> : c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  // measure
  return (
    <table className="w-full text-[12.5px] border-collapse">
      <thead>
        <tr className="bg-slate-100 text-slate-600">
          {['措施类型','措施名称','主体已列','方案新增','金额（万元）','来源'].map((h,i)=><th key={i} className="border border-slate-300 px-3 py-2 font-semibold text-left">{h}</th>)}
        </tr>
      </thead>
      <tbody>
        {MEASURE_ROWS.map((r,ri) => (
          <tr key={ri} className="hover:bg-brand-50/30">
            {r.map((c,ci) => (
              <td key={ci} className={`border border-slate-300 px-3 py-2 ${ci<=1?'text-slate-700':ci>=2&&ci<=4?'tabular text-center':''} ${ci===5?'text-[11px] text-slate-400 font-mono':''} ${highlight==='amount'&&ci===4?'bg-amber-100 ring-1 ring-amber-300':''}`}>{c}</td>
            ))}
          </tr>
        ))}
        <tr className="bg-slate-50 font-semibold">
          <td className="border border-slate-300 px-3 py-2" colSpan={2}>合计</td>
          <td className="border border-slate-300 px-3 py-2 tabular text-center">3.44</td>
          <td className="border border-slate-300 px-3 py-2 tabular text-center">2.56</td>
          <td className="border border-slate-300 px-3 py-2 tabular text-center text-brand-700">6.00</td>
          <td className="border border-slate-300 px-3 py-2"></td>
        </tr>
      </tbody>
    </table>
  );
}

function TablesPage() {
  const [active, setActive] = useState('sixrate');
  const [highlight, setHighlight] = useState(null);
  const cur = TABLE_LIST.find(t=>t.id===active);
  const isSkeleton = cur.status === 'SKELETON';
  const src = TABLE_SOURCE[active] || TABLE_SOURCE.sixrate;

  return (
    <div>
      <PageHeader title="表格中心" sub="正式表格生成 · LIVE / 可生成 / 骨架 / 不适用 — 数表同源、可追溯" icon="Table2">
        <Chip tone="emerald" icon="CircleCheck">9 张 LIVE</Chip>
        <Chip tone="amber" icon="LayoutTemplate">1 张 SKELETON</Chip>
      </PageHeader>

      <div className="grid grid-cols-[250px_1fr_300px] h-[calc(100vh-56px-65px)] min-w-[1180px]">
        {/* 左：清单 */}
        <aside className="border-r border-slate-200 bg-white overflow-y-auto">
          <StatusDotList list={TABLE_LIST} active={active} setActive={setActive} />
        </aside>

        {/* 中：预览 */}
        <section className="overflow-y-auto bg-[#dfe3ea] p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <h2 className="text-[14px] font-semibold text-slate-700">{cur.name}</h2>
              <StatusTag status={cur.status} dot/>
            </div>
            <button className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-50 text-slate-600">
              <Icon name="FileDown" size={14}/>插入正文位置
            </button>
          </div>

          {isSkeleton ? (
            <div className="bg-white rounded-lg border border-slate-200 a4-shadow p-8">
              <div className="flex items-center gap-2 text-amber-600 mb-4"><Icon name="LayoutTemplate" size={18}/><span className="font-semibold text-[14px]">骨架占位表（SKELETON）</span></div>
              <p className="text-[12.5px] text-slate-500 mb-4">该表缺少关键事实，暂以骨架占位。补齐以下字段后即可生成 LIVE 表格：</p>
              <div className="space-y-2">
                {['investment.annual_allocation（年度投资分配）','schedule.annual_plan（年度进度计划）'].map(f => (
                  <div key={f} className="flex items-center gap-2 px-3 py-2 rounded-md bg-amber-50 border border-amber-200 text-[12.5px] text-amber-800">
                    <Icon name="CircleAlert" size={14}/>缺失字段：<span className="font-mono">{f}</span>
                  </div>
                ))}
              </div>
              <table className="w-full text-[12px] border-collapse mt-5 opacity-40">
                <thead><tr className="bg-slate-100">{['年度','工程措施','植物措施','临时措施','合计'].map(h=><th key={h} className="border border-slate-300 px-3 py-2 text-left">{h}</th>)}</tr></thead>
                <tbody>{[0,1].map(r=><tr key={r}>{[0,1,2,3,4].map(c=><td key={c} className="border border-slate-300 px-3 py-3"><div className="h-2 bg-slate-200 rounded"></div></td>)}</tr>)}</tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-slate-200 a4-shadow p-6">
              <div className="text-center mb-4">
                <div className="text-[14px] font-semibold text-slate-800 font-serif">附表 {active==='sixrate'?'5':'8'}　{cur.name}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">世维华南供应链（二期）　水土保持方案</div>
              </div>
              <FormalTable id={active} highlight={highlight} />
              <div className="mt-3 text-[11px] text-slate-400 flex items-center gap-1.5"><Icon name="Info" size={12}/>表中数值由计算器输出，与正文、补偿费、六率目标保持一致。</div>
            </div>
          )}
        </section>

        {/* 右：来源 */}
        <aside className="border-l border-slate-200 bg-white overflow-y-auto">
          <div className="px-4 py-3 border-b border-slate-100"><div className="text-[12px] font-semibold text-slate-700 flex items-center gap-1.5"><Icon name="GitBranch" size={14} className="text-brand-600"/>表格来源</div></div>
          <div className="p-4 space-y-4">
            <div>
              <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="Database" size={12}/>来源事实</div>
              <div className="space-y-1">{src.facts.map(f=><div key={f} className="font-mono text-[11px] text-slate-600 bg-slate-50 border border-slate-100 rounded px-2 py-1">{f}</div>)}</div>
            </div>
            <div>
              <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="Calculator" size={12}/>计算器</div>
              <div className="flex flex-wrap gap-1">{src.calc.map(c=><Chip key={c} tone="brand">{c}</Chip>)}</div>
            </div>
            <div>
              <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="BookMarked" size={12}/>规则依据</div>
              <div className="space-y-1">{src.rules.map(r=><div key={r} className="text-[11.5px] text-amber-700 bg-amber-50 border border-amber-100 rounded px-2 py-1">{r}</div>)}</div>
            </div>
            <div>
              <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="FileText" size={12}/>关联正文</div>
              <div className="flex flex-wrap gap-1">{src.narrative.map(n=><Chip key={n} tone="teal">{n}</Chip>)}</div>
            </div>
            <div className="pt-2 border-t border-slate-100">
              <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="Package" size={12}/>导出位置</div>
              <div className="text-[12px] text-slate-600 font-mono">{src.export}</div>
            </div>

            {/* 高亮单元格交互 */}
            <div className="pt-2 border-t border-slate-100">
              <div className="text-[11px] text-slate-400 mb-1.5">点击来源字段，高亮表中对应单元格：</div>
              <div className="flex flex-wrap gap-1.5">
                {active==='sixrate' && <button onClick={()=>setHighlight(h=>h==='actual'?null:'actual')} className={`text-[11.5px] px-2.5 py-1 rounded border ${highlight==='actual'?'bg-amber-100 border-amber-300 text-amber-700':'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}>高亮「实际预测值」列</button>}
                {active==='measure' && <button onClick={()=>setHighlight(h=>h==='amount'?null:'amount')} className={`text-[11.5px] px-2.5 py-1 rounded border ${highlight==='amount'?'bg-amber-100 border-amber-300 text-amber-700':'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}>高亮「金额」列</button>}
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

window.TablesPage = TablesPage;
