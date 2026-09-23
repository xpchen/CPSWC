// ===================================================================
// 共享：页面头 + 页 1 项目总览
// ===================================================================
const { PROJECT: OP, SIX_RATES: OSR, RECENT_CHANGES: ORC, TODOS: OTD } = window.CPSWC;

function PageHeader({ title, sub, icon, children }) {
  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-white/60 backdrop-blur sticky top-0 z-20">
      <div className="flex items-center gap-3">
        {icon && <span className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 grid place-items-center"><Icon name={icon} size={19}/></span>}
        <div>
          <h1 className="text-[17px] font-semibold text-slate-800 leading-tight">{title}</h1>
          {sub && <p className="text-[12px] text-slate-400 mt-0.5">{sub}</p>}
        </div>
      </div>
      <div className="flex items-center gap-2">{children}</div>
    </div>
  );
}
window.PageHeader = PageHeader;

// 角色重点提示条
function RoleBanner({ role }) {
  const map = {
    editor:   { icon:'PencilRuler', tone:'bg-brand-50 border-brand-200 text-brand-700', text:'编制视图 · 重点关注：待补充字段与正文/表格生成进度。' },
    reviewer: { icon:'ShieldCheck', tone:'bg-orange-50 border-orange-200 text-orange-700', text:'审查视图 · 重点关注：规则触发与标准依据、数文一致性风险。' },
    manager:  { icon:'ClipboardList', tone:'bg-teal-50 border-teal-200 text-teal-700', text:'负责人视图 · 重点关注：内容覆盖率、导出门禁与待甲方补充资料。' },
  };
  const m = map[role] || map.editor;
  return (
    <div className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg border text-[12.5px] ${m.tone}`}>
      <Icon name={m.icon} size={16} className="shrink-0"/>
      <span className="leading-snug">{m.text}</span>
    </div>
  );
}

function RateBar({ r }) {
  // 快照模式下 actual 往往是"99.47（候选·待确认，源自 actual_derived）"这类文案 ——
  // **不画进度条、不上绿色**: 一根绿条就等于宣布达标, 而效果来源尚未确认。
  if (window.CPSWC.IS_SNAPSHOT) {
    return (
      <div className="py-2 border-b border-slate-50 last:border-0">
        <div className="text-[12px] text-slate-600">{r.name}</div>
        <div className="mt-1 grid grid-cols-3 gap-2 text-[11.5px]">
          <div><span className="text-slate-400">目标 </span><b className="text-slate-700 tabular">{r.target}</b></div>
          <div className="col-span-2">
            <span className="text-slate-400">实现值 </span>
            <b className="text-slate-700">{r.actual}</b>
          </div>
        </div>
        <div className="mt-0.5 text-[11px] text-amber-700">{r.result}</div>
      </div>
    );
  }
  const pct = parseFloat(r.actual);
  const tgt = parseFloat(r.target);
  const isPct = r.actual.includes('%');
  const w = isPct ? pct : Math.min(100, pct * 90);
  return (
    <div className="py-2">
      <div className="flex items-center justify-between text-[12px] mb-1">
        <span className="text-slate-600">{r.name}</span>
        <span className="tabular text-slate-400">目标 <b className="text-slate-600">{r.target}</b> · 预测 <b className="text-emerald-600">{r.actual}</b></span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 overflow-hidden relative">
        <div className="h-full rounded-full bg-emerald-500/80" style={{ width: w + '%' }}></div>
        {isPct && <div className="absolute top-0 h-full w-px bg-slate-400" style={{ left: tgt + '%' }} title="目标线"></div>}
      </div>
    </div>
  );
}

const { IS_SNAPSHOT } = window.CPSWC;

// ===================================================================
// F-3 快照模式首屏 —— 全部数字来自 payload
// ===================================================================
// 原 hero 写死了另一个项目名与"无导出阻塞""2 项专家确认"。这里改接真结论,
// 并且**只报事实、不下判断**: 覆盖率四项分开列, 门禁照搬 verdict,
// 收资按严重度分档 —— 不出现任何"已达标 / 可交付"之类的合成结论。
function SnapshotHero({ setPage }) {
  const { QUALITY: q, GATE: g, INTAKE_SUMMARY: s, PROJECT: pr, PAYLOAD: pl } = window.CPSWC;
  const verdict = (g && g.verdict) || '未知';
  const gateTone = verdict === 'BLOCK' ? 'bg-rose-500/20 text-rose-200 border-rose-400/40'
    : verdict === 'WARN' ? 'bg-amber-500/20 text-amber-100 border-amber-400/40'
    : 'bg-white/10 text-brand-100 border-white/20';
  const cells = [
    ['内容要求（叶）', q.applicable_leaf_count, '项'],
    ['确认完成', q.complete_leaf_count, '项'],
    ['未实现', q.unimplemented_leaf_count, '项'],
    ['已建立映射', q.mapped_leaf_count, '项'],
    ['本次有产出', q.with_output_leaf_count, '项'],
    ['待甲方补充', (s && s.total) || 0, '项'],
  ];
  return (
    <div className="rounded-xl overflow-hidden border border-brand-800 bg-brand-900 text-white relative">
      <div className="absolute inset-0 opacity-[0.06]" style={{ backgroundImage:'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize:'34px 34px' }}></div>
      <div className="relative px-6 py-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2.5">
            <span className="w-9 h-9 rounded-lg bg-white/10 grid place-items-center"><Icon name="Gauge" size={20}/></span>
            <div>
              <div className="text-[16px] font-semibold tracking-wide">当前项目生产状态总览</div>
              <div className="text-[12px] text-brand-300">
                {pr.name} · 静态快照 · {pl.hashes.generation_input_hash.slice(0, 16)}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1 rounded-md border whitespace-nowrap ${gateTone}`}>
              <Icon name={verdict === 'BLOCK' ? 'OctagonX' : 'ShieldQuestion'} size={14}/>
              导出门禁 {verdict}{g ? `（阻断 ${g.block_count} · 提醒 ${g.warn_count}）` : ''}
            </span>
            <span className="inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1 rounded-md bg-white/10 text-brand-100 border border-white/20 whitespace-nowrap">
              <Icon name="FileClock" size={14}/>正式导出未实现
            </span>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-3 md:grid-cols-6 gap-px bg-white/10 rounded-lg overflow-hidden">
          {cells.map(([k, v, u]) => (
            <div key={k} className="bg-brand-900 px-3 py-3">
              <div className="text-[11px] text-brand-300">{k}</div>
              <div className="mt-0.5 flex items-baseline gap-1">
                <span className="text-[22px] font-bold tabular">{v}</span>
                <span className="text-[11px] text-brand-300">{u}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-3 text-[11.5px] text-brand-200 leading-snug">
          「确认完成」为 0 不是显示故障：没有任何一项内容要求走完确认。
          「已建立映射」只说明有那么多项被标为 implemented，<b>不证明它们都有合格产出</b>。
          <button onClick={() => setPage('delivery')} className="ml-1 underline hover:text-white">查看门禁明细</button>
        </div>
      </div>
    </div>
  );
}

// 四状态卡的快照版。**没有一个状态是"通过"** —— 这份快照里确实没有通过的东西。
function snapshotCards() {
  const { QUALITY: q, GATE: g, INTAKE_SUMMARY: s, PAYLOAD: pl } = window.CPSWC;
  const missing = pl.facts.filter(f => f.state !== 'PRESENT').length;
  return [
    { label:'事实字段', value:String(pl.facts.length - missing), unit:`/${pl.facts.length}`,
      status: missing ? '待确认' : '待确认', accent:'brand',
      note: missing ? `${missing} 项未取到值` : '登记字段均有取值，未经复核' },
    { label:'内容要求', value:String(q.complete_leaf_count), unit:`/${q.applicable_leaf_count}`,
      status:'待确认', accent:'amber',
      note:`确认完成 ${q.complete_leaf_count}；未实现 ${q.unimplemented_leaf_count}` },
    { label:'正文块', value:String(q.rendered_block_count), unit:'块',
      status:'待确认', accent:'brand',
      note:'有文字不等于满足内容要求，须逐项对照' },
    { label:'导出门禁', value:(g && g.verdict) || '未知', unit:'',
      status:(g && g.verdict === 'BLOCK') ? '风险' : '待确认', accent:'amber',
      note:`待甲方补充 ${(s && s.total) || 0} 项；正式导出未实现` },
  ];
}

// 资料收集六格的快照版。没有后端支撑的两格如实写"未实现", 不填 0 ——
// 0 会被读成"已查过, 确实没有", 而事实是根本没查。
function intakeCells() {
  const { PAYLOAD: pl, INTAKE_SUMMARY: s } = window.CPSWC;
  const present = pl.facts.filter(f => f.state === 'PRESENT').length;
  const missing = pl.facts.length - present;
  const sev = (s && s.by_severity) || {};
  return [
    ['已上传资料','未实现','','FolderOpen','text-slate-400'],
    ['有取值事实',String(present),'项','Database','text-slate-800'],
    ['未取到值',String(missing),'项','CircleHelp','text-amber-600'],
    ['待甲方补充·阻断',String(sev.BLOCK || 0),'项','PackageSearch','text-rose-600'],
    ['待甲方补充·提醒',String(sev.WARN || 0),'项','PackageSearch','text-amber-600'],
    ['图件登记','未实现','','Map','text-slate-400'],
  ];
}

// 关键指标的快照版。每格都是**具名登记字段**的当前取值,
// 取不到就显示状态说法 (未填报 / 数据非法…), 不补默认数。
function snapshotKpis() {
  const F = window.CPSWC;
  const cell = (k, id, opts) => {
    const f = F.fact(id);
    const present = !!f && f.state === 'PRESENT';
    return {
      k, v: F.factText(id, Object.assign({ unit: false }, opts || {})),
      u: present && f.unit ? f.unit : '',
      tone: present ? 'text-slate-800' : 'text-amber-600',
      small: !present,
    };
  };
  return [
    cell('水土保持补偿费', 'field.derived.investment.compensation_fee_amount'),
    cell('防治责任范围', 'field.fact.prevention.responsibility_range_area'),
    cell('预测土壤流失总量', 'field.fact.prediction.total_loss'),
    cell('新增土壤流失量', 'field.fact.prediction.new_loss'),
    cell('土石方弃方量', 'field.fact.earthwork.spoil'),
    cell('弃渣场级别', 'field.derived.disposal_site.level_assessment'),
  ];
}

function OverviewPage({ role, setPage }) {
  const cards = [
    { label:'事实完整度', value:'94', unit:'%', status:'通过', accent:'emerald', note:'关键事实已满足生成要求' },
    { label:'表格生成率', value:'88', unit:'%', status:'待确认', accent:'amber', note:'年度投资表仍为骨架（SKELETON）' },
    { label:'正文覆盖率', value:'92', unit:'%', status:'可生成', accent:'brand', note:'主要章节已生成，可预览' },
    { label:'导出状态',   value:'可生成', unit:'', status:'通过', accent:'emerald', note:'无阻塞项，存在 2 项专家确认' },
  ];
  return (
    <div>
      <PageHeader title="项目总览" sub="项目状态 · 完成度 · 阻塞项 · 关键结果 · 最近修改" icon="LayoutDashboard">
        <button className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-600"><Icon name="RefreshCw" size={14}/>重新计算</button>
        <button onClick={()=>setPage('delivery')} className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700"><Icon name="Package" size={14}/>前往交付</button>
      </PageHeader>

      <div className="p-6 space-y-5 max-w-[1400px]">
        {/* 当前项目生产状态总览（演示冲击区）
            快照模式下整块隐藏: 这里写死了另一个项目的名字, 以及"无导出阻塞"
            "2 项专家确认"等肯定结论 —— 与真实门禁 (BLOCK) 相反。
            在 Overview 正式接线 (F-3) 之前, 宁可不显示, 也不显示假的。 */}
        {IS_SNAPSHOT ? <SnapshotHero setPage={setPage} /> : (
        <div className="rounded-xl overflow-hidden border border-brand-800 bg-brand-900 text-white relative">
          <div className="absolute inset-0 opacity-[0.06]" style={{ backgroundImage:'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize:'34px 34px' }}></div>
          <div className="relative px-6 py-5">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2.5">
                <span className="w-9 h-9 rounded-lg bg-white/10 grid place-items-center"><Icon name="Gauge" size={20}/></span>
                <div>
                  <div className="text-[16px] font-semibold tracking-wide">当前项目生产状态总览</div>
                  <div className="text-[12px] text-brand-300">世维华南供应链（二期）· 事实驱动 · 规则可追踪 · 数文一致</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1 rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 whitespace-nowrap"><Icon name="ShieldCheck" size={14}/>无导出阻塞</span>
                <span className="inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1 rounded-md bg-orange-500/15 text-orange-200 border border-orange-500/30 whitespace-nowrap"><Icon name="UserCheck" size={14}/>2 项专家确认</span>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-3 md:grid-cols-6 gap-px bg-white/10 rounded-lg overflow-hidden">
              {[
                ['正文段落','32','FileText'],['报告表格','23','Table2'],['计算结果','6','Calculator'],
                ['审查义务','12','Gavel'],['依据注脚','18','BookMarked'],['交付包','1','Package'],
              ].map(([k,v,icon]) => (
                <div key={k} className="bg-brand-900/60 px-3 py-3 text-center">
                  <Icon name={icon} size={15} className="text-brand-300 mx-auto mb-1.5"/>
                  <div className="text-[26px] font-bold tabular leading-none text-white">{v}</div>
                  <div className="text-[11px] text-brand-300 mt-1.5">{k}</div>
                </div>
              ))}
            </div>

            <div className="mt-4 flex items-start gap-2.5">
              <div className="flex-1 flex items-center gap-2 text-[12.5px] text-brand-100 bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5">
                <Icon name="Link2" size={16} className="text-teal-300 shrink-0"/>
                所有正文、表格、计算结果和审查结论均可追溯到<b className="text-white">项目事实</b>、<b className="text-white">规则依据</b>和<b className="text-white">计算器结果</b>。
              </div>
              <div className="hidden lg:flex items-center gap-2 shrink-0">
                {[['可追溯','GitBranch'],['数文一致','Equal'],['可导出','PackageCheck']].map(([t,i]) => (
                  <span key={t} className="inline-flex items-center gap-1.5 text-[12px] px-3 py-2.5 rounded-lg bg-teal-500/15 text-teal-200 border border-teal-500/30"><Icon name={i} size={14}/>{t}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
        )}

        <RoleBanner role={role} />

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {(IS_SNAPSHOT ? snapshotCards() : cards).map(c => <MetricCard key={c.label} {...c} />)}
        </div>

        {/* 资料收集状态 */}
        <Panel title="资料收集状态" sub="智能收资向导汇总" right={<button onClick={()=>setPage('facts')} className="text-[11.5px] text-brand-600 hover:underline inline-flex items-center gap-1">事实填报<Icon name="ArrowRight" size={12}/></button>}>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-px bg-slate-100">
            {(IS_SNAPSHOT ? intakeCells() : [
              ['已上传资料','4','份','FolderOpen','text-brand-700'],
              ['已确认事实','42','项','Database','text-emerald-600'],
              ['候选待确认','7','项','CircleHelp','text-orange-600'],
              ['缺失资料','5','项','PackageSearch','text-amber-600'],
              ['已登记图件','6','张','Map','text-teal-600'],
              ['可生成图件','3','张','MapPlus','text-brand-600'],
            ]).map(([k,v,u,icon,tone]) => (
              <div key={k} className="bg-white p-3.5">
                <div className="flex items-center gap-1.5 text-[11px] text-slate-400"><Icon name={icon} size={12}/>{k}</div>
                <div className="mt-1 flex items-baseline gap-1"><span className={`text-[22px] font-bold tabular ${tone}`}>{v}</span><span className="text-[11px] text-slate-400">{u}</span></div>
              </div>
            ))}
          </div>
          <div className="px-4 py-2.5 text-[12px] text-slate-500 border-t border-slate-100 flex items-start gap-1.5">
            <Icon name="Info" size={13} className="text-slate-400 shrink-0 mt-0.5"/>
            {IS_SNAPSHOT ? (
              <span>
                资料上传与图件识别尚未接入后端，相应计数显示为「未实现」。
                「待甲方补充」逐条清单见
                <button onClick={()=>window.dispatchEvent(new CustomEvent('cpswc:open-intake'))}
                  className="text-brand-600 hover:underline mx-0.5">智能收资向导</button>
                第 4 节。
              </span>
            ) : '当前项目资料已覆盖项目基本信息、占地与土石方、投资估算和部分图件来源；年度投资分配、措施布局图和监测点位资料仍需补充。'}
          </div>
        </Panel>

        {/* 概况 + 关键指标 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Panel title="项目概况" sub="基础事实快照" right={<button onClick={()=>setPage('facts')} className="text-[11.5px] text-brand-600 hover:underline inline-flex items-center gap-1">查看事实<Icon name="ArrowRight" size={12}/></button>}>
            <div className="px-4 py-2">
              <Field k="项目名称" v={OP.name} />
              <Field k="项目编码" v={OP.code} mono />
              <Field k="建设单位" v={OP.org} />
              <Field k="建设性质" v={IS_SNAPSHOT ? OP.nature : OP.type} />
              <Field k="所在区域" v={OP.location} />
              <Field k="防治责任范围" v={IS_SNAPSHOT ? OP.scopeArea : `${OP.scopeArea} hm²`} mono />
              <Field k="规则集" v={OP.rulesets.slice(0,2).join(' / ')} />
              <div className="flex items-center justify-between pt-2 mt-1">
                <span className="text-[12px] text-slate-400">当前状态</span>
                {/* 快照模式不给"可生成" —— 门禁是 BLOCK 时它就是谎话 */}
                {IS_SNAPSHOT
                  ? <span className="text-[12px] text-slate-500">静态快照 · 未复核</span>
                  : <StatusTag status="可生成" dot />}
              </div>
            </div>
          </Panel>

          <Panel title="关键指标" sub="计算器与规则输出">
            <div className="grid grid-cols-2 gap-px bg-slate-100">
              {(IS_SNAPSHOT ? snapshotKpis() : [
                { k:'水土保持补偿费', v:'4.248', u:'万元', tone:'text-brand-700' },
                { k:'防治责任范围', v:'3.54', u:'hm²', tone:'text-slate-800' },
                { k:'预测土壤流失量', v:'128.6', u:'t', tone:'text-slate-800' },
                { k:'是否涉及弃渣场', v:'否', u:'', tone:'text-slate-500' },
                { k:'是否跨行政区', v:'否', u:'', tone:'text-slate-500' },
                { k:'需要专家确认', v:'2', u:'项', tone:'text-orange-600' },
              ]).map(m => (
                <div key={m.k} className="bg-white p-3.5">
                  <div className="text-[11.5px] text-slate-400">{m.k}</div>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className={`${m.small ? 'text-[13px] font-medium' : 'text-[22px] font-bold tabular'} ${m.tone}`}>{m.v}</span>
                    <span className="text-[11px] text-slate-400">{m.u}</span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* 六率 + 待办 */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          <Panel className="lg:col-span-3" title="六率目标概览" sub="GB/T 50434-2018 防治目标"
            right={IS_SNAPSHOT
              ? <span className="text-[11px] text-amber-700">实现值来源待确认</span>
              : <StatusTag status="已计算" dot/>}>
            <div className="px-4 py-1.5">
              {OSR.map(r => <RateBar key={r.name} r={r} />)}
            </div>
          </Panel>

          <Panel className="lg:col-span-2" title="风险 / 待办"
            sub={IS_SNAPSHOT ? `本次快照阻断级诊断 ${OTD.length} 条（最多列 8 条）` : '非阻塞提示 4 项'} right={<button onClick={()=>setPage('rules')} className="text-[11.5px] text-brand-600 hover:underline">规则审查</button>}>
            <div className="p-3 space-y-2">
              {IS_SNAPSHOT && OTD.length === 0 && (
                <div className="text-[12px] text-slate-500 p-2">
                  本次快照没有阻断级诊断。注意：这只说明<b>已登记的检查</b>没有报出阻断，
                  不等于内容已经合格 —— 未实现的内容要求不会在此出现。
                </div>
              )}
              {OTD.map((t,i) => (
                <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-md border border-slate-100 bg-slate-50/50">
                  <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                    t.tone==='emerald'?'bg-emerald-500':t.tone==='amber'?'bg-amber-500':t.tone==='orange'?'bg-orange-500':'bg-brand-500'}`}></span>
                  <span className="text-[12.5px] text-slate-600 leading-snug flex-1">{t.text}</span>
                  <StatusTag status={t.tag} />
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* 最近修改 */}
        <Panel title="最近修改记录" sub={IS_SNAPSHOT ? '未实现' : '字段变更及其影响范围'} right={<button onClick={()=>setPage('changes')} className="text-[11.5px] text-brand-600 hover:underline inline-flex items-center gap-1">改动追踪<Icon name="ArrowRight" size={12}/></button>}>
          {IS_SNAPSHOT ? (
            <div className="px-4 py-4 text-[12px] text-slate-500">
              改动追踪尚未接入后端。快照是一次生成的静态结果，系统<b>没有记录</b>
              任何字段的修改历史，这里不显示任何条目 —— 空白表示未实现，不表示没有改动过。
            </div>
          ) : (
          <table className="w-full text-[12.5px]">
            <thead>
              <tr className="text-[11px] text-slate-400 border-b border-slate-100">
                <th className="text-left font-medium px-4 py-2">修改字段</th>
                <th className="text-left font-medium px-2 py-2">修改前</th>
                <th className="text-left font-medium px-2 py-2">修改后</th>
                <th className="text-left font-medium px-2 py-2">修改人</th>
                <th className="text-left font-medium px-2 py-2">时间</th>
                <th className="text-left font-medium px-4 py-2">影响范围</th>
              </tr>
            </thead>
            <tbody>
              {ORC.map((c,i) => (
                <tr key={i} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                  <td className="px-4 py-2.5"><Chip tone="brand">{c.field}</Chip></td>
                  <td className="px-2 py-2.5 font-mono text-slate-400 tabular">{c.before} {c.unit}</td>
                  <td className="px-2 py-2.5 font-mono text-slate-800 tabular">→ {c.after} {c.unit}</td>
                  <td className="px-2 py-2.5 text-slate-500">{c.by}</td>
                  <td className="px-2 py-2.5 text-slate-400">{c.time}</td>
                  <td className="px-4 py-2.5 text-slate-500">{c.impact}</td>
                </tr>
              ))}
            </tbody>
          </table>
          )}
        </Panel>
      </div>
    </div>
  );
}

window.OverviewPage = OverviewPage;
