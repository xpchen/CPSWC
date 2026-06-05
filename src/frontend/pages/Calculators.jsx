// ===================================================================
// 页 4 计算器
// ===================================================================
const CALCULATORS = [
  { id:'fee', name:'水土保持补偿费计算器', icon:'Coins', status:'已计算', complete:100,
    inputs:[ {k:'占地面积', v:'3.54 hm²', f:'land.total_area'}, {k:'区域费率', v:'1.20 元/m²', f:'compensation.region_rate'}, {k:'项目类型', v:'物流仓储', f:'project.type'} ],
    output:'4.248', unit:'万元', std:['广东省水土保持补偿费征收使用管理办法','惠州市适配规则'],
    formula:'补偿费 = 占地面积(m²) × 区域费率 × 类型系数 = 35400 × 1.20 = 42480 元 ≈ 4.248 万元',
    tables:['补偿费计算表','投资汇总表'], narrative:['9.2 水土保持补偿费'], time:'今天 09:42' },
  { id:'sixrate', name:'六率目标计算器', icon:'Target', status:'已计算', complete:100,
    inputs:[ {k:'防治区', v:'南方红壤区', f:'region.type'}, {k:'标准等级', v:'一级', f:'standard.level'}, {k:'区域类型', v:'建设类项目', f:'project.category'} ],
    output:'6 项', unit:'目标值', std:['GB/T 50434-2018 表 4.0.2-5'],
    formula:'按区域 + 等级查表取基准值，结合项目特征修正，输出六项防治目标。',
    tables:['六率分项目标表'], narrative:['7.2 水土流失防治目标'], time:'今天 09:42' },
  { id:'spoil', name:'弃渣场级别计算器', icon:'Mountain', status:'未触发', complete:0,
    inputs:[ {k:'弃渣量', v:'0 万 m³', f:'earthwork.spoil'}, {k:'堆高', v:'—', f:'spoil.height'}, {k:'场地条件', v:'—', f:'spoil.site'} ],
    output:'不适用', unit:'', std:['GB 51018-2014'],
    formula:'当弃渣量为 0 时不触发级别鉴定，章节标记为 NOT_APPLICABLE。',
    tables:['弃渣场级别表'], narrative:['5.2 弃渣场','7.4 弃渣防护'], time:'—' },
  { id:'predict', name:'水土流失预测计算器', icon:'TrendingDown', status:'已计算', complete:100,
    inputs:[ {k:'扰动面积', v:'3.54 hm²', f:'prevention.scope_area'}, {k:'侵蚀模数', v:'1200 t/(km²·a)', f:'predict.erosion'}, {k:'预测时段', v:'1.4 a', f:'predict.period'} ],
    output:'128.6', unit:'t', std:['GB 50433-2018'],
    formula:'预测流失量 = Σ(面积 × 侵蚀模数 × 时段 × 系数) = 128.6 t',
    tables:['水土流失预测表'], narrative:['5.1 流失量预测'], time:'今天 09:43' },
  { id:'invest', name:'防治措施投资汇总计算器', icon:'Wallet', status:'已计算', complete:100,
    inputs:[ {k:'工程措施', v:'1.20 万元', f:'investment.engineering'}, {k:'植物措施', v:'1.02 万元', f:'investment.plant'}, {k:'临时措施', v:'1.34 万元', f:'investment.temporary'}, {k:'主体已列', v:'2.44 万元', f:'investment.main'} ],
    output:'6.00', unit:'万元', std:['GB 50433-2018 8.1'],
    formula:'措施投资合计 = 工程 + 植物 + 临时 + 主体已列 = 1.20 + 1.02 + 1.34 + 2.44 = 6.00 万元',
    tables:['防治措施投资表','投资估算表'], narrative:['9.1 投资估算'], time:'今天 09:43' },
];

function CalcCard({ c, active, onClick }) {
  const ok = c.status === '已计算';
  return (
    <button onClick={onClick}
      className={`text-left rounded-lg border p-4 transition-all ${active ? 'border-brand-400 ring-1 ring-brand-200 bg-brand-50/40' : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'}`}>
      <div className="flex items-start justify-between">
        <span className={`w-9 h-9 rounded-lg grid place-items-center ${ok?'bg-brand-50 text-brand-600':'bg-slate-100 text-slate-400'}`}><Icon name={c.icon} size={18}/></span>
        <StatusTag status={c.status} dot/>
      </div>
      <div className="mt-3 text-[13.5px] font-semibold text-slate-800 leading-snug">{c.name}</div>
      <div className="mt-2 flex items-baseline gap-1">
        <span className={`text-[24px] font-bold tabular ${ok?'text-brand-700':'text-slate-400'}`}>{c.output}</span>
        <span className="text-[12px] text-slate-400">{c.unit}</span>
      </div>
      {/* 输入完整度 */}
      <div className="mt-3">
        <div className="flex items-center justify-between text-[10.5px] text-slate-400 mb-1"><span>输入完整度</span><span className="tabular">{c.complete}%</span></div>
        <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
          <div className={`h-full ${ok?'bg-emerald-500':'bg-slate-300'}`} style={{width:c.complete+'%'}}></div>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-3 text-[10.5px] text-slate-400 pt-2.5 border-t border-slate-100">
        <span className="inline-flex items-center gap-1"><Icon name="Table2" size={11}/>{c.tables.length} 表</span>
        <span className="inline-flex items-center gap-1"><Icon name="FileText" size={11}/>{c.narrative.length} 段</span>
        <span className="inline-flex items-center gap-1 ml-auto"><Icon name="BookMarked" size={11}/>{c.std.length} 依据</span>
      </div>
    </button>
  );
}

function CalculatorsPage() {
  const [active, setActive] = useState('fee');
  const cur = CALCULATORS.find(c => c.id === active);
  const ok = cur.status === '已计算';
  return (
    <div>
      <PageHeader title="计算器" sub="专业确定性计算 · 非 AI 猜测 — 输入事实，按标准公式输出可追溯结果" icon="Calculator">
        <Chip tone="emerald" icon="CircleCheck">4 / 5 已计算</Chip>
      </PageHeader>

      <div className="grid grid-cols-[1fr_360px] gap-4 p-5">
        {/* 卡片网格 */}
        <div className="grid grid-cols-2 xl:grid-cols-3 gap-4 content-start">
          {CALCULATORS.map(c => <CalcCard key={c.id} c={c} active={active===c.id} onClick={()=>setActive(c.id)} />)}
        </div>

        {/* 右侧详情 */}
        <Panel className="self-start sticky top-[81px]" title="计算详情" sub={cur.name} right={<StatusTag status={cur.status} dot/>}>
          <div className="p-4 space-y-4">
            {/* 输出 */}
            <div className={`rounded-lg p-4 text-center ${ok?'bg-brand-50 border border-brand-100':'bg-slate-50 border border-slate-200'}`}>
              <div className="text-[11px] text-slate-400 mb-1">计算输出</div>
              <div className="flex items-baseline justify-center gap-1.5">
                <span className={`text-[34px] font-bold tabular ${ok?'text-brand-700':'text-slate-400'}`}>{cur.output}</span>
                <span className="text-[14px] text-slate-400">{cur.unit}</span>
              </div>
              <div className="mt-1 text-[11px] text-slate-400 inline-flex items-center gap-1"><Icon name="Clock" size={11}/>最近计算：{cur.time}</div>
            </div>

            {/* 输入字段 */}
            <div>
              <div className="text-[11.5px] font-semibold text-slate-500 mb-2 flex items-center gap-1.5"><Icon name="FileInput" size={13}/>输入字段</div>
              <div className="space-y-1">
                {cur.inputs.map(i => (
                  <div key={i.f} className="flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-md bg-slate-50 border border-slate-100">
                    <span className="text-[12px] text-slate-500">{i.k}</span>
                    <span className="flex items-center gap-2">
                      <span className="font-mono tabular text-[12px] font-semibold text-slate-700">{i.v}</span>
                      <Chip tone="slate">{i.f}</Chip>
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 公式 */}
            <div>
              <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="Sigma" size={13}/>计算公式说明</div>
              <div className="text-[12px] text-slate-600 leading-relaxed font-mono bg-slate-900 text-slate-100 rounded-md p-3">{cur.formula}</div>
            </div>

            {/* 标准依据 */}
            <div>
              <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="BookMarked" size={13}/>引用标准</div>
              <div className="space-y-1">
                {cur.std.map(s => <div key={s} className="flex items-center gap-1.5 text-[12px] text-amber-700 bg-amber-50 border border-amber-100 rounded px-2 py-1"><Icon name="FileBadge" size={12}/>{s}</div>)}
              </div>
            </div>

            {/* 关联 */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div>
                <div className="text-[11px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="Table2" size={12}/>关联表格</div>
                <div className="flex flex-wrap gap-1">{cur.tables.map(t=><Chip key={t} tone="teal">{t}</Chip>)}</div>
              </div>
              <div>
                <div className="text-[11px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="FileText" size={12}/>关联正文</div>
                <div className="flex flex-wrap gap-1">{cur.narrative.map(t=><Chip key={t} tone="brand">{t}</Chip>)}</div>
              </div>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}

window.CalculatorsPage = CalculatorsPage;
