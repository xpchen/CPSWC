// ===================================================================
// F-12 未实现页（快照模式专用）
// ===================================================================
// 改动追踪与历史版本在后端**完全没有对应产出**：快照是一次生成的静态结果，
// 系统不记录任何字段的修改历史，也不保存版本。
//
// 演示版这两页展示的是另一个项目的伪造改动日志和版本树。即便顶上压一条
// 「本页尚未接入项目数据」的提示条，下面那一屏具体到人名、时间、金额的记录
// 仍然会被当成真的 —— 提示条压不住一屏看起来很具体的假数据。
//
// 所以快照模式下不显示它们，代之以：这件事没做、为什么没做、当前能替代它的是什么。

function NiFeature({ icon, title, children }) {
  return (
    <div className="flex items-start gap-3 py-2.5">
      <span className="w-7 h-7 rounded-md bg-slate-100 text-slate-400 grid place-items-center shrink-0">
        <Icon name={icon} size={15}/>
      </span>
      <div className="min-w-0">
        <div className="text-[12.5px] font-medium text-slate-700">{title}</div>
        <div className="text-[12px] text-slate-500 leading-snug mt-0.5">{children}</div>
      </div>
    </div>
  );
}

function NotImplementedPage({ title, sub, icon, missing, instead, onNavigate }) {
  const { PAYLOAD } = window.CPSWC;
  return (
    <div>
      <PageHeader title={title} sub={sub} icon={icon}>
        <Chip tone="amber" icon="Minus">未实现</Chip>
      </PageHeader>

      <div className="p-6 max-w-[860px] space-y-4">
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3">
          <div className="text-[13px] font-semibold text-amber-900 flex items-center gap-1.5">
            <Icon name="TriangleAlert" size={15}/>该功能尚未实现，本页不显示任何内容
          </div>
          <div className="mt-1 text-[12.5px] text-amber-800 leading-snug">
            系统后端没有产出与本页对应的数据。这里<b>刻意不显示示例内容</b> ——
            一屏具体到人名、时间、金额的演示记录会被当成真的，
            一条提示条压不住它。
          </div>
        </div>

        <Panel title="缺的是什么">
          <div className="px-4 py-2 divide-y divide-slate-50">
            {missing.map(m => (
              <NiFeature key={m.title} icon={m.icon} title={m.title}>{m.desc}</NiFeature>
            ))}
          </div>
        </Panel>

        <Panel title="当前可以替代的做法">
          <div className="px-4 py-3 space-y-2">
            {instead.map(i => (
              <div key={i.text} className="flex items-start gap-2 text-[12.5px] text-slate-600">
                <Icon name="ArrowRight" size={14} className="text-brand-500 shrink-0 mt-0.5"/>
                <span>
                  {i.text}
                  {i.page && (
                    <button onClick={() => onNavigate && onNavigate(i.page)}
                      className="ml-1 text-brand-600 hover:underline">{i.pageLabel}</button>
                  )}
                </span>
              </div>
            ))}
          </div>
        </Panel>

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-[12px] text-slate-500">
          本次快照的输入指纹是
          <span className="font-mono text-slate-700 mx-1">{PAYLOAD.hashes.generation_input_hash.slice(0, 16)}</span>。
          输入变了指纹就会变 —— 这是目前<b>唯一</b>能用来区分两次生成结果的东西，
          但它只能告诉你"不一样了"，不能告诉你"哪里不一样"。
        </div>
      </div>
    </div>
  );
}

function ChangeTrackingSnapshotPage({ setPage }) {
  return (
    <NotImplementedPage
      title="改动追踪" sub="字段变更及其影响范围" icon="GitCompareArrows"
      onNavigate={setPage}
      missing={[
        { icon: 'History', title: '字段修改历史',
          desc: '系统不记录任何字段何时被谁改成什么。快照是一次生成的静态结果，没有"改动"这个概念。' },
        { icon: 'GitBranch', title: '改动影响传播',
          desc: '改一个字段会波及哪些章节、表格与计算结果 —— 这个推导没有实现。字段与章节的静态对应关系倒是有登记。' },
        { icon: 'PenLine', title: '人工编辑痕迹',
          desc: '正文不支持编辑，因此也没有"人工改过哪里"可追踪。' },
      ]}
      instead={[
        { text: '字段与章节／图件的静态对应关系可在事实填报页的「影响预览」查看（取自登记表，不是改动推导）。',
          page: 'facts', pageLabel: '事实填报' },
        { text: '两次生成是否用了同一份输入，可比对 generation_input_hash。' },
      ]}
    />
  );
}

function HistorySnapshotPage({ setPage }) {
  return (
    <NotImplementedPage
      title="历史与版本" sub="版本记录与回溯" icon="History"
      onNavigate={setPage}
      missing={[
        { icon: 'Save', title: '版本保存',
          desc: '系统不保存版本。每次生成都是一次性的静态快照，生成完就结束了。' },
        { icon: 'Lock', title: '冻结',
          desc: '「冻结版本」没有实现。演示版里的冻结只改浏览器本地状态，什么也没冻住。' },
        { icon: 'GitCompare', title: '版本对比与回溯',
          desc: '没有版本，自然也没有对比和回滚。' },
      ]}
      instead={[
        { text: '每次生成的产物按 项目编码 / generation_input_hash 分目录落盘，互不覆盖 —— 旧快照不会被新的冲掉。' },
        { text: '当前快照的门禁与内容缺口见交付包页。', page: 'delivery', pageLabel: '交付包' },
      ]}
    />
  );
}

Object.assign(window, {
  NotImplementedPage, ChangeTrackingSnapshotPage, HistorySnapshotPage,
});
