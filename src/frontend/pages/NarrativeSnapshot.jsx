// ===================================================================
// F-5 正文预览（快照模式专用，只读）
// ===================================================================
// 为什么另起一个组件而不是改造演示版：演示版的正文页整页都围绕"编辑 / AI
// 润色 / 加注脚 / 模拟人工改金额"组织，这些能力一样也没实现。把真实正文塞
// 进那套壳里，用户会以为自己能改——改完还什么都没发生。
//
// 这里只做一件事：**按 2026 模板的章节顺序，把"已生成什么"和"缺什么"并排摆出来。**
//
//   · 有产出的小节 → 显示真实段落，并标出每段的断言类型与证据字段
//   · 没有产出的小节 → 显示醒目的缺口块，而不是悄悄跳过
//
// 跳过未实现的小节是最危险的做法：目录看起来是连续的，读者会默认它写完了。

const NS_STATUS_TONE = {
  full: ['已生成', 'text-slate-600'],
  partial: ['部分生成', 'text-amber-700'],
  skeleton: ['骨架占位', 'text-amber-700'],
  gap: ['未产出', 'text-rose-700'],
};

const NS_ASSERTION_LABEL = {
  FACT_RESTATEMENT: '事实复述',
  DERIVED_STATEMENT: '派生结论',
  PROJECT_JUDGMENT: '专业判断',
  REGULATORY_CITATION: '法规引用',
  GAP_DISCLOSURE: '缺口披露',
};

/** 把 requirements 按 2026 章节切段。display_number 为纯数字者开新章。 */
function nsChapters() {
  const { PAYLOAD } = window.CPSWC;
  const sections = {};
  (PAYLOAD.narrative || []).forEach(s => { sections[s.section_id] = s; });

  const chapters = [];
  let cur = null;
  (PAYLOAD.requirements || []).forEach(r => {
    if (/^\d+$/.test(r.display_number)) {
      cur = { num: r.display_number, title: r.title, items: [] };
      chapters.push(cur);
      if (!r.is_leaf) return;          // 章标题本身不是要求项
    }
    if (!cur) {
      cur = { num: '?', title: '未归章', items: [] };
      chapters.push(cur);
    }
    if (r.is_leaf) cur.items.push({ req: r, section: r.stable_id ? sections[r.stable_id] : null });
  });

  // 有产出但模板里没有对应要求的小节：单列一章，不藏起来
  const claimed = new Set();
  chapters.forEach(c => c.items.forEach(i => { if (i.section) claimed.add(i.section.section_id); }));
  const extra = (PAYLOAD.narrative || []).filter(s => !claimed.has(s.section_id));
  if (extra.length) {
    chapters.push({
      num: '附', title: '模板外产出',
      items: extra.map(s => ({ req: null, section: s })),
    });
  }
  return chapters;
}

function nsChapterStats(ch) {
  let withOutput = 0, unimplemented = 0;
  ch.items.forEach(i => {
    if (i.section) withOutput += 1;
    if (i.req && !i.req.implemented) unimplemented += 1;
  });
  return { total: ch.items.length, withOutput, unimplemented };
}

// ---------- 缺口块 ----------
function NsGapBlock({ req }) {
  return (
    <div className="my-4 rounded-md border-2 border-dashed border-rose-300 bg-rose-50/60 px-4 py-3">
      <div className="flex items-center gap-2 text-[12.5px] font-semibold text-rose-800">
        <Icon name="FileX2" size={15}/>
        {req.display_number ? `${req.display_number} ` : ''}{req.title}
      </div>
      <div className="mt-1 text-[12px] text-rose-700 leading-snug">
        本节<b>未实现</b>：系统尚未建立该内容要求与任何叙述模板的映射，本次快照没有产出任何文字。
        {req.condition_note && <span className="block mt-0.5 text-rose-600">适用条件：{req.condition_note}</span>}
      </div>
      <div className="mt-1 text-[11px] text-rose-500 font-mono">{req.id} · stable_id 未登记</div>
    </div>
  );
}

// ---------- 小节块 ----------
function NsSectionBlock({ item, active, onPick }) {
  const { req, section } = item;
  if (!section) return <NsGapBlock req={req}/>;

  const [label, tone] = NS_STATUS_TONE[section.render_status] || NS_STATUS_TONE.gap;
  const title = req
    ? `${req.display_number ? req.display_number + ' ' : ''}${req.title}`
    : `${section.display_number} ${section.title}`;
  const hasFindings = (section.finding_codes || []).length > 0
    || (section.block_warnings || []).length > 0;

  return (
    <div className={`my-4 -mx-3 px-3 py-2 rounded-md cursor-pointer transition-colors
      ${active ? 'bg-brand-50/70 ring-1 ring-brand-200' : 'hover:bg-slate-50'}`}
      onClick={() => onPick(section.section_id)}>
      <div className="flex items-baseline gap-2 flex-wrap">
        <h3 className="text-[16px] font-semibold text-slate-800 font-serif">{title}</h3>
        <span className={`text-[11px] ${tone}`}>{label}</span>
        {hasFindings && (
          <span className="text-[11px] text-amber-700 inline-flex items-center gap-0.5">
            <Icon name="TriangleAlert" size={11}/>有诊断
          </span>
        )}
        {section.applicability !== 'APPLICABLE' && (
          <span className="text-[11px] text-slate-500">适用性 {section.applicability}</span>
        )}
      </div>

      {(section.paragraphs || []).length === 0 ? (
        <p className="mt-1.5 text-[12.5px] text-amber-700">
          该小节已建立模板映射，但本次<b>没有产出任何段落</b>。
        </p>
      ) : (section.paragraphs || []).map(p => (
        <div key={p.paragraph_id} className="mt-2">
          <p className="text-[15px] leading-[2] text-slate-800 font-serif text-justify" style={{ textIndent: '2em' }}>
            {p.text}
          </p>
          <div className="mt-0.5 flex items-center gap-2 flex-wrap text-[10.5px] text-slate-400">
            <span className="px-1.5 py-px rounded bg-slate-100 border border-slate-200">
              {NS_ASSERTION_LABEL[p.assertion_class] || p.assertion_class || '未标注断言类型'}
            </span>
            <span>证据字段 {(p.evidence_refs || []).length}</span>
            <span>规则依据 {(p.source_rule_refs || []).length}</span>
            {(p.review_refs || []).length === 0 && p.assertion_class === 'PROJECT_JUDGMENT' && (
              <span className="text-amber-600">无复核记录</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------- 右栏：小节诊断 ----------
function NsInspector({ section }) {
  if (!section) {
    return (
      <div className="p-4 text-[12px] text-slate-500">
        在左侧正文中点选一个小节，这里显示它的模板、诊断与证据链。
      </div>
    );
  }
  const paras = section.paragraphs || [];
  const codes = section.finding_codes || [];
  const warns = section.block_warnings || [];
  return (
    <div className="p-4 space-y-4">
      <div>
        <div className="text-[12.5px] font-semibold text-slate-700">{section.display_number} {section.title}</div>
        <div className="mt-1.5 space-y-1 text-[11px] text-slate-500 font-mono break-all">
          <div>{section.section_id}</div>
          <div>{section.template_id}</div>
          <div>variant={section.variant_id} · role={section.content_role}</div>
        </div>
      </div>

      <div>
        <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">诊断</div>
        {codes.length === 0 && warns.length === 0 ? (
          <div className="text-[11.5px] text-slate-500">
            本小节没有诊断。注意：这只说明<b>已登记的检查</b>没有报出问题，
            不等于内容已经合格。
          </div>
        ) : (
          <div className="space-y-1">
            {codes.map((c, i) => (
              <div key={'c' + i} className="text-[11.5px] px-2 py-1 rounded bg-amber-50 border border-amber-200 text-amber-800 font-mono">{c}</div>
            ))}
            {warns.map((w, i) => (
              <div key={'w' + i} className="text-[11.5px] px-2 py-1 rounded bg-slate-50 border border-slate-200 text-slate-600">{w}</div>
            ))}
          </div>
        )}
      </div>

      <div>
        <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">段落证据链 · {paras.length} 段</div>
        <div className="space-y-2">
          {paras.map(p => (
            <div key={p.paragraph_id} className="rounded-md border border-slate-200 bg-white p-2">
              <div className="text-[10.5px] font-mono text-slate-400 break-all">{p.paragraph_id}</div>
              <div className="mt-1 text-[11px] text-slate-600">
                {NS_ASSERTION_LABEL[p.assertion_class] || p.assertion_class || '未标注'}
              </div>
              {(p.evidence_refs || []).length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {p.evidence_refs.map(r => (
                    <span key={r} className="text-[10px] px-1.5 py-px rounded bg-brand-50 text-brand-700 border border-brand-200 font-mono break-all">{r}</span>
                  ))}
                </div>
              )}
              {(p.source_rule_refs || []).length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {p.source_rule_refs.map(r => (
                    <span key={r} className="text-[10px] px-1.5 py-px rounded bg-slate-50 text-slate-500 border border-slate-200 font-mono break-all">{r}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------- 页面 ----------
function NarrativeSnapshotPage() {
  const { PAYLOAD, PROJECT, QUALITY } = window.CPSWC;
  const chapters = nsChapters();
  const [chapter, setChapter] = useState(chapters[0] ? chapters[0].num : '1');
  const [activeSec, setActiveSec] = useState('');

  const ch = chapters.find(c => c.num === chapter) || chapters[0];
  const sectionById = {};
  (PAYLOAD.narrative || []).forEach(s => { sectionById[s.section_id] = s; });
  const cur = sectionById[activeSec] || null;

  return (
    <div>
      <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-white sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <span className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 grid place-items-center"><Icon name="FileText" size={19}/></span>
          <div>
            <h1 className="text-[17px] font-semibold text-slate-800 leading-tight">正文预览</h1>
            <p className="text-[12px] text-slate-400">
              按 2026 模板章节顺序逐节对照：已产出的显示原文，未实现的显示缺口
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Chip tone="slate" icon="ListChecks">
            叶子要求 {QUALITY.applicable_leaf_count} · 有产出 {QUALITY.with_output_leaf_count} · 未实现 {QUALITY.unimplemented_leaf_count}
          </Chip>
          <button disabled title="正文编辑能力未实现"
            className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md border border-slate-200 bg-white text-slate-400 cursor-not-allowed">
            <Icon name="PencilLine" size={14}/>编辑正文（未实现）
          </button>
          <button disabled title="Word 导出能力未实现"
            className="inline-flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-md border border-slate-200 bg-white text-slate-400 cursor-not-allowed">
            <Icon name="FileDown" size={14}/>导出 Word（未实现）
          </button>
        </div>
      </div>

      <div className="grid grid-cols-[248px_1fr_340px] h-[calc(100vh-56px-58px)] min-w-[1100px]">
        {/* 左：2026 章节树 */}
        <aside className="border-r border-slate-200 bg-white overflow-y-auto">
          <div className="px-3 py-2 sticky top-0 bg-white border-b border-slate-100">
            <span className="text-[10.5px] font-semibold text-slate-400 uppercase tracking-wide">
              章节目录 · 办水保函〔2026〕232 号
            </span>
          </div>
          <div className="p-2">
            {chapters.map(c => {
              const act = chapter === c.num;
              const st = nsChapterStats(c);
              return (
                <button key={c.num} onClick={() => { setChapter(c.num); setActiveSec(''); }}
                  className={`w-full text-left px-2.5 py-2 rounded-md mb-0.5 transition-colors ${act ? 'bg-brand-50' : 'hover:bg-slate-50'}`}>
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono tabular ${act ? 'text-brand-500' : 'text-slate-300'}`}>
                      {/^\d+$/.test(c.num) ? String(c.num).padStart(2, '0') : c.num}
                    </span>
                    <span className={`flex-1 text-[12.5px] ${act ? 'text-brand-700 font-medium' : 'text-slate-600'}`}>{c.title}</span>
                  </div>
                  <div className="pl-6 mt-1 flex items-center gap-2 text-[10.5px]">
                    <span className="text-slate-400">有产出 {st.withOutput}/{st.total}</span>
                    {st.unimplemented > 0 &&
                      <span className="text-rose-600">未实现 {st.unimplemented}</span>}
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        {/* 中：A4 预览 */}
        <section className="overflow-y-auto bg-[#d9dde4] p-8">
          <div className="mx-auto bg-white a4-shadow relative" style={{ maxWidth: '860px', minHeight: '1000px', padding: '72px 80px' }}>
            <div className="absolute left-20 right-20 top-7 flex items-center justify-between text-[10.5px] text-slate-400 font-serif border-b border-slate-200 pb-1.5">
              <span>{PROJECT.name}</span>
              <span className="font-mono">{PAYLOAD.hashes.generation_input_hash.slice(0, 16)}</span>
            </div>

            <div className="text-center mb-2 mt-2">
              <h2 className="text-[24px] font-bold text-slate-900 font-serif tracking-wide">
                {/^\d+$/.test(ch.num) ? `第${ch.num}章　` : ''}{ch.title}
              </h2>
            </div>
            <div className="text-center mb-6 text-[11px] text-slate-400">
              本页为快照预览，不是可提交的报告正文；缺口以红框显示，未做任何省略。
            </div>

            {ch.items.length === 0 ? (
              <p className="text-[13px] text-slate-500">本章没有登记任何内容要求。</p>
            ) : ch.items.map((item, i) => (
              <NsSectionBlock key={(item.req && item.req.id) || item.section.section_id || i}
                item={item} active={!!item.section && item.section.section_id === activeSec}
                onPick={setActiveSec}/>
            ))}
          </div>
        </section>

        {/* 右：小节诊断 */}
        <aside className="border-l border-slate-200 bg-white overflow-y-auto">
          <div className="px-4 py-3 border-b border-slate-100 sticky top-0 bg-white">
            <div className="text-[12px] font-semibold text-slate-700 flex items-center gap-1.5">
              <Icon name="Microscope" size={14} className="text-brand-600"/>小节诊断
            </div>
          </div>
          <NsInspector section={cur}/>
        </aside>
      </div>
    </div>
  );
}

Object.assign(window, { NarrativeSnapshotPage, nsChapters, nsChapterStats });
