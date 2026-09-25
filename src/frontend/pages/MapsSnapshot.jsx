// ===================================================================
// F-11 附图与地图（快照模式专用，只读）
// ===================================================================
// 演示版是一个能"生成图件"的地图中心，标着「已生成 / 可生成」。
// 实际情况：ArtifactRegistry 登记了 14 张图件的要求，每张都写了 renderer 类名，
// 但 `src/cpswc/renderers/` 里**一个图件渲染器都没有实现**。
//
// 登记表写了 renderer 名字 ≠ 那个渲染器存在。所以这一页做两件事：
//   1. 把本项目需要哪 14 张图、每张要画什么、数据从哪来，完整列出来；
//   2. 如实说明它们**一张也生成不了**，系统也不能接收上传的图件。
//
// 这份清单本身是有用的 —— 它是交给制图的人的任务单。

function MapsSnapshotPage() {
  const { PAYLOAD } = window.CPSWC;
  const figs = PAYLOAD.figures || [];
  const [active, setActive] = useState(figs[0] ? figs[0].artifact_id : '');
  const cur = figs.find(f => f.artifact_id === active) || figs[0] || null;

  const required = figs.filter(f => f.required_for_this_project);
  const renderable = figs.filter(f => f.renderer_implemented);

  return (
    <div>
      <PageHeader title="附图与地图" sub="本项目需要的图件清单 · 生成能力现状" icon="Map">
        <Chip tone="slate" icon="Map">本项目需要 {required.length} 张</Chip>
        <Chip tone={renderable.length ? 'slate' : 'amber'} icon="TriangleAlert">
          可生成 {renderable.length} 张
        </Chip>
      </PageHeader>

      <div className="p-5 space-y-4 max-w-[1400px]">
        {renderable.length === 0 && (
          <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-[12.5px] text-amber-900">
            <div className="font-semibold flex items-center gap-1.5">
              <Icon name="TriangleAlert" size={15}/>图件生成能力尚未实现：{figs.length} 张图，一张也生成不了
            </div>
            <div className="mt-1 leading-snug">
              登记表为每张图写了 renderer 类名，但<b>这些渲染器没有一个有代码实现</b>。
              系统同样<b>不能接收上传的图件</b>，因此无法判断哪些图已经由人工画好。
              下面这份清单的用处是当<b>制图任务单</b>：需要哪些图、每张画什么、数据取自哪些字段。
            </div>
          </div>
        )}

        <div className="grid grid-cols-[1fr_420px] gap-4 items-start">
          <Panel title="图件清单" sub={`${figs.length} 张 · 本项目需要的排在前面`}>
            <div className="divide-y divide-slate-50 max-h-[calc(100vh-300px)] overflow-y-auto">
              {figs.map(f => (
                <button key={f.artifact_id} onClick={() => setActive(f.artifact_id)}
                  className={`w-full text-left px-4 py-2.5 transition-colors ${f.artifact_id === active ? 'bg-brand-50/70' : 'hover:bg-slate-50'}`}>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[12.5px] text-slate-700">{f.canonical_name}</span>
                    {f.required_for_this_project
                      ? <span className="text-[10px] px-1.5 py-px rounded border bg-brand-50 text-brand-700 border-brand-200">本项目需要</span>
                      : <span className="text-[10px] px-1.5 py-px rounded border bg-slate-50 text-slate-500 border-slate-200">本项目未触发</span>}
                    <span className={`text-[10px] px-1.5 py-px rounded border ml-auto whitespace-nowrap
                      ${f.renderer_implemented
                        ? 'bg-slate-50 text-slate-600 border-slate-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'}`}>
                      {f.renderer_implemented ? '可生成' : '无法生成'}
                    </span>
                  </div>
                  <div className="mt-0.5 text-[10.5px] font-mono text-slate-400 break-all">{f.artifact_id}</div>
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="图件要求" sub={cur ? cur.canonical_name : '未选择'}>
            {!cur ? (
              <div className="p-4 text-[12px] text-slate-500">在左侧选一张图。</div>
            ) : (
              <div className="p-4 space-y-3">
                <div>
                  <div className="text-[11.5px] font-semibold text-slate-500 mb-1">画什么</div>
                  <div className="text-[12.5px] text-slate-700">
                    {cur.content_spec || <span className="text-slate-400">登记表未写内容要求</span>}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-px bg-slate-100 rounded-lg overflow-hidden border border-slate-100">
                  {[
                    ['要求级别', cur.requirement === 'always' ? '必需' : cur.requirement === 'conditional' ? '条件必需' : cur.requirement || '未登记'],
                    ['本项目', cur.required_for_this_project ? '需要' : '未触发'],
                    ['输出格式', (cur.output_formats || []).join(' / ') || '未登记'],
                    ['所在章节', (cur.chapter_ref || '未登记').replace(/^sec\./, '')],
                  ].map(([k, v]) => (
                    <div key={k} className="bg-white p-2.5">
                      <div className="text-[11px] text-slate-400">{k}</div>
                      <div className="text-[12.5px] text-slate-800 mt-0.5 break-all">{v}</div>
                    </div>
                  ))}
                </div>

                <div className={`rounded-md px-3 py-2 text-[11.5px] border
                  ${cur.renderer_implemented
                    ? 'bg-slate-50 border-slate-200 text-slate-600'
                    : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
                  渲染器 <span className="font-mono">{cur.renderer || '未登记'}</span>
                  {cur.renderer_implemented
                    ? ' —— 已实现'
                    : <> —— <b>没有代码实现</b>，这张图系统画不出来，也无法接收人工上传的版本</>}
                </div>

                <div>
                  <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5">
                    数据来源 · {(cur.data_source_refs || []).length}
                  </div>
                  <div className="space-y-1">
                    {(cur.data_source_refs || []).map(r => {
                      const isField = r.startsWith('field.');
                      const f = isField ? window.CPSWC.fact(r) : null;
                      const missing = isField && (!f || f.state !== 'PRESENT');
                      return (
                        <div key={r} className={`text-[11px] rounded px-2 py-1.5 border
                          ${missing ? 'bg-amber-50 border-amber-200 text-amber-800' : 'bg-white border-slate-200 text-slate-600'}`}>
                          <span className="font-mono break-all">{r}</span>
                          {isField && (
                            <div className="font-sans text-[10.5px] mt-0.5">
                              {f ? window.CPSWC.factText(r) : '该字段未登记'}
                            </div>
                          )}
                          {!isField && (
                            <div className="font-sans text-[10.5px] text-slate-400 mt-0.5">
                              引擎依赖，非事实字段
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { MapsSnapshotPage });
