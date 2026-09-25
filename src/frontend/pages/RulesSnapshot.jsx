// ===================================================================
// F-8 规则审查（快照模式专用，只读）
// ===================================================================
// 演示版这一页顶上挂着「无阻塞」chip 和「审查状态：无阻塞」，而本次快照的真实
// 门禁是 BLOCK。这里改成逐条摆事实：
//
//   · 每条义务的**判定表达式**、判定结果、依据规则 ID、需要的附件与保证事项
//   · triggered 是三值：是 / 否 / **未知**。未知不折成"否" ——
//     "条件算不出来"和"条件不成立"是两回事，把前者当后者就是悄悄放过一条义务
//   · 门禁结论照搬 verdict，不出具"通过"
//
// 这一页不判断合规与否。它只回答："系统检查了什么、依据是什么、结果是什么。"

const RS_TRI = {
  true: { label: '已触发', tone: 'bg-brand-50 text-brand-700 border-brand-200', dot: 'bg-brand-500' },
  false: { label: '未触发', tone: 'bg-slate-50 text-slate-500 border-slate-200', dot: 'bg-slate-300' },
  unknown: { label: '判定未知', tone: 'bg-amber-50 text-amber-800 border-amber-300', dot: 'bg-amber-500' },
};

function rsTri(o) {
  if (o.triggered === true) return RS_TRI.true;
  if (o.triggered === false) return RS_TRI.false;
  return RS_TRI.unknown;
}

const RS_TABS = [
  { id: 'obligations', name: '义务判定', icon: 'Gavel' },
  { id: 'gate', name: '导出门禁', icon: 'ShieldAlert' },
  { id: 'artifacts', name: '需附文件', icon: 'Paperclip' },
];

function RsObligationCard({ o, active, onPick }) {
  const tri = rsTri(o);
  return (
    <button onClick={() => onPick(o.obligation_id)}
      className={`w-full text-left rounded-lg border p-3 transition-all
        ${active ? 'border-brand-400 bg-brand-50/60 ring-1 ring-brand-200' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
      <div className="flex items-start justify-between gap-2">
        <span className="text-[12.5px] text-slate-700 leading-snug flex-1">
          {o.human || <span className="text-slate-400">（登记表未写人类可读说明）</span>}
        </span>
        <span className={`shrink-0 text-[10.5px] px-1.5 py-0.5 rounded border whitespace-nowrap ${tri.tone}`}>
          {tri.label}
        </span>
      </div>
      <div className="mt-1.5 flex items-center gap-2 flex-wrap text-[10.5px] text-slate-400">
        <span className="font-mono break-all">{o.obligation_id}</span>
        {o.protection_level && <span>{o.protection_level}</span>}
        {o.requirement_type && <span>{o.requirement_type}</span>}
        {o.missing_field_refs.length > 0 &&
          <span className="text-amber-600">缺 {o.missing_field_refs.length} 个输入</span>}
      </div>
    </button>
  );
}

function RsInspector({ o }) {
  if (!o) {
    return <div className="p-4 text-[12px] text-slate-500">在左侧选一条义务，这里显示它的判定依据与影响。</div>;
  }
  const tri = rsTri(o);
  const Row = ({ k, children }) => (
    <div>
      <div className="text-[11.5px] font-semibold text-slate-500 mb-1">{k}</div>
      {children}
    </div>
  );
  const refList = (arr, tone) => arr.length ? (
    <div className="space-y-1">
      {arr.map(r => (
        <div key={r} className={`text-[11px] font-mono break-all rounded px-2 py-1 border ${tone}`}>{r}</div>
      ))}
    </div>
  ) : <div className="text-[11.5px] text-slate-400">无</div>;

  return (
    <div className="p-4 space-y-4">
      <div>
        <span className={`text-[11px] px-2 py-0.5 rounded border ${tri.tone}`}>{tri.label}</span>
        <div className="mt-1.5 text-[12.5px] text-slate-700 leading-snug">
          {o.human || '（登记表未写人类可读说明）'}
        </div>
        <div className="mt-1 text-[11px] font-mono text-slate-400 break-all">{o.obligation_id}</div>
      </div>

      <Row k="判定表达式">
        <pre className="text-[11px] font-mono text-slate-600 bg-slate-50 border border-slate-200 rounded px-2 py-1.5 whitespace-pre-wrap break-all">
          {o.expression || '（无条件，mode=' + o.mode + '）'}
        </pre>
        <div className="mt-1 text-[11px] text-slate-400">
          判定状态 {o.evaluation_status} · 适用性 {o.applicability || '未登记'}
        </div>
      </Row>

      {o.triggered === null && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-2.5 py-2 text-[11.5px] text-amber-900">
          <b>判定结果未知。</b>条件算不出来，<b>不等于条件不成立</b> ——
          这条义务可能适用，系统没有把它当作"未触发"放过去。
          {o.diagnostic_message && <div className="mt-1 text-amber-700">{o.diagnostic_message}</div>}
        </div>
      )}
      {o.missing_field_refs.length > 0 && (
        <Row k={`判定所缺输入 · ${o.missing_field_refs.length}`}>
          {refList(o.missing_field_refs, 'bg-amber-50 border-amber-200 text-amber-800')}
        </Row>
      )}

      <Row k="依据规则">
        {o.source_rule_id ? (
          <div className="text-[11px] font-mono break-all rounded px-2 py-1 border bg-slate-50 border-slate-200 text-slate-600">
            {o.source_rule_id}
            <div className="mt-0.5 font-sans text-slate-400">该依据 ID 没有登记标题或条文原文</div>
          </div>
        ) : <div className="text-[11.5px] text-slate-400">未登记</div>}
      </Row>

      <Row k={`需附文件 · ${o.required_artifact_refs.length}`}>
        {refList(o.required_artifact_refs, 'bg-teal-50 border-teal-100 text-teal-700')}
      </Row>
      <Row k={`需保证事项 · ${o.required_assurance_refs.length}`}>
        {refList(o.required_assurance_refs, 'bg-brand-50 border-brand-100 text-brand-700')}
      </Row>
      <Row k={`判定依赖字段 · ${o.depends_on_field_refs.length}`}>
        {refList(o.depends_on_field_refs, 'bg-slate-50 border-slate-100 text-slate-600')}
      </Row>

      {o.v0_scope_note && (
        <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500">
          v0 范围说明：{o.v0_scope_note}
        </div>
      )}
    </div>
  );
}

function RulesSnapshotPage() {
  const { PAYLOAD, GATE } = window.CPSWC;
  const obs = PAYLOAD.obligations_detail || [];
  const [tab, setTab] = useState('obligations');
  const [active, setActive] = useState(obs[0] ? obs[0].obligation_id : '');
  const cur = obs.find(o => o.obligation_id === active) || null;

  const yes = obs.filter(o => o.triggered === true).length;
  const no = obs.filter(o => o.triggered === false).length;
  const unk = obs.filter(o => o.triggered === null).length;
  const findings = (GATE && GATE.findings) || [];

  return (
    <div>
      <PageHeader title="规则审查" sub="义务逐条判定 · 判定表达式与依据可见 · 门禁结论照搬，不出具通过" icon="Gavel">
        <Chip tone="brand" icon="Gavel">已触发 {yes}</Chip>
        <Chip tone="slate" icon="Minus">未触发 {no}</Chip>
        {unk > 0 && <Chip tone="amber" icon="CircleHelp">判定未知 {unk}</Chip>}
      </PageHeader>

      <div className="px-6 pt-3 flex items-center gap-1.5 border-b border-slate-200 bg-white">
        {RS_TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`inline-flex items-center gap-1.5 text-[12.5px] px-3 py-2 rounded-t-md border-b-2 transition-colors
              ${tab === t.id ? 'border-brand-600 text-brand-700 font-medium' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
            <Icon name={t.icon} size={14}/>{t.name}
          </button>
        ))}
      </div>

      {tab === 'obligations' && (
        <div className="grid grid-cols-[1fr_360px] h-[calc(100vh-56px-65px-41px)] min-w-[980px]">
          <section className="overflow-y-auto bg-[#eef1f5] p-5 space-y-2">
            <div className="text-[11.5px] text-slate-500 mb-1">
              共 {obs.length} 条义务。已触发的排在前面；
              <b>「判定未知」单独成类，不并入未触发</b>。
            </div>
            {obs.map(o => (
              <RsObligationCard key={o.obligation_id} o={o}
                active={o.obligation_id === active} onPick={setActive}/>
            ))}
          </section>
          <aside className="border-l border-slate-200 bg-white overflow-y-auto">
            <div className="px-4 py-3 border-b border-slate-100 sticky top-0 bg-white">
              <div className="text-[12px] font-semibold text-slate-700 flex items-center gap-1.5">
                <Icon name="Microscope" size={14} className="text-brand-600"/>判定详情
              </div>
            </div>
            <RsInspector o={cur}/>
          </aside>
        </div>
      )}

      {tab === 'gate' && (
        <div className="p-5 space-y-3 max-w-[1100px]">
          <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
            <div className="text-[13px] font-semibold text-slate-700">
              门禁结论 {(GATE && GATE.verdict) || '未知'}
            </div>
            <div className="mt-1 text-[12px] text-slate-500">
              报出 {findings.length} 条（阻断 {(GATE && GATE.block_count) || 0} ·
              提醒 {(GATE && GATE.warn_count) || 0}）。
              <b>门禁只报问题，不出具「通过」结论</b> —— 没被拦下不等于合格。
            </div>
          </div>
          {findings.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-[12px] text-slate-500">
              门禁未报出问题。这只说明<b>已登记的门禁规则</b>没有拦下什么。
            </div>
          ) : findings.map((f, i) => {
            const block = (f.action || f.severity) === 'BLOCK';
            const msg = f.message || '';
            return (
              <div key={i} className={`rounded-lg border px-4 py-3 ${block ? 'border-rose-200 bg-rose-50' : 'border-amber-200 bg-amber-50'}`}>
                <div className="flex items-center gap-2">
                  <span className={`text-[10.5px] px-1.5 py-0.5 rounded border font-mono
                    ${block ? 'bg-white border-rose-200 text-rose-700' : 'bg-white border-amber-200 text-amber-700'}`}>
                    {f.rule_id || f.code || '未命名规则'}
                  </span>
                  <span className={`text-[11px] ${block ? 'text-rose-700' : 'text-amber-700'}`}>
                    {block ? '阻断' : '提醒'}
                  </span>
                  {f.target_ref && <span className="text-[10.5px] font-mono text-slate-400 break-all ml-auto">{f.target_ref}</span>}
                </div>
                <div className="mt-1.5 text-[12px] text-slate-700 break-all" title={msg}>
                  {msg.length > 400 ? msg.slice(0, 400) + '…（悬停查看完整原文）' : msg}
                </div>
                {f.remediation && <div className="mt-1 text-[11.5px] text-slate-500">处理建议：{f.remediation}</div>}
              </div>
            );
          })}
        </div>
      )}

      {tab === 'artifacts' && (
        <div className="p-5 grid grid-cols-1 lg:grid-cols-2 gap-4 max-w-[1300px]">
          <Panel title="本项目需要的附件 / 图件"
            sub={`${(PAYLOAD.required_artifacts || []).length} 项，由已触发义务与模板要求推导`}>
            <div className="p-3 grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {(PAYLOAD.required_artifacts || []).map(a => (
                <div key={a} className="text-[11px] font-mono break-all rounded px-2 py-1 bg-slate-50 border border-slate-100 text-slate-600">{a}</div>
              ))}
            </div>
            <div className="px-4 py-2.5 border-t border-slate-100 text-[11.5px] text-slate-500">
              这是<b>需要什么</b>的清单，不是<b>已经有什么</b>。
              系统没有接收附件的能力，无法核对其中任何一项是否已提供。
            </div>
          </Panel>

          <Panel title="需要的保证事项"
            sub={`${(PAYLOAD.required_assurances || []).length} 项`}>
            <div className="p-3 space-y-1.5">
              {(PAYLOAD.required_assurances || []).map(a => (
                <div key={a} className="text-[11.5px] font-mono break-all rounded px-2 py-1.5 bg-amber-50 border border-amber-200 text-amber-800">
                  {a}
                  <div className="font-sans text-[10.5px] text-amber-600 mt-0.5">未提供 —— 已在门禁中报出</div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { RulesSnapshotPage, rsTri });
