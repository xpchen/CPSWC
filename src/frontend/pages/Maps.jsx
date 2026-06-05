// ===================================================================
// 页 6.5 附图与地图中心
// 统一管理区位图 / 责任范围图 / 措施布局图 / 监测点位图 / 典型图 / 外部图纸
// 模拟地图装配（schematic basemap），纳入插图、依据链与交付包
// ===================================================================
const { FIGURE_CATS, FIGURES, FIGURE_TEMPLATES } = window.CPSWC;

// ---------- 模拟底图（schematic，不接入真实地图 API） ----------
function MapPreview({ kind, title, num }) {
  // 颜色：浅灰道路 / 蓝水系 / 淡绿绿地 / 红线 / 责任范围
  return (
    <div className="bg-white">
      <div className="text-center mb-2">
        <div className="text-[13.5px] font-semibold text-slate-800 font-serif">{num}　{title}</div>
      </div>
      <div className="relative border border-slate-300 bg-[#f3f5f2]" style={{ aspectRatio:'4/3' }}>
        <svg viewBox="0 0 400 300" className="w-full h-full">
          {/* 绿地 */}
          <rect x="0" y="0" width="400" height="300" fill="#eef3ea"/>
          <rect x="30" y="40" width="120" height="90" fill="#e3ecdd"/>
          <rect x="250" y="180" width="120" height="80" fill="#e3ecdd"/>
          {/* 水系 */}
          <path d="M0,250 C80,235 140,265 210,250 C280,235 340,260 400,248 L400,300 L0,300 Z" fill="#cfe0ef"/>
          <path d="M0,250 C80,235 140,265 210,250 C280,235 340,260 400,248" fill="none" stroke="#9cc0e0" strokeWidth="1.5"/>
          {/* 道路 */}
          <rect x="0" y="150" width="400" height="14" fill="#e7e7e3"/>
          <rect x="190" y="0" width="14" height="300" fill="#e7e7e3"/>
          <line x1="0" y1="157" x2="400" y2="157" stroke="#c9c9c2" strokeWidth="1" strokeDasharray="8 6"/>
          <line x1="197" y1="0" x2="197" y2="300" stroke="#c9c9c2" strokeWidth="1" strokeDasharray="8 6"/>
          {/* 行政区边界 */}
          <rect x="8" y="8" width="384" height="284" fill="none" stroke="#b6b6ad" strokeWidth="1" strokeDasharray="2 4"/>

          {/* 项目红线（所有图都显示） */}
          <polygon points="120,90 290,80 300,210 135,225" fill="rgba(217,90,60,0.06)" stroke="#d24b2c" strokeWidth="2"/>

          {kind==='loc' && (
            <>
              <circle cx="210" cy="150" r="9" fill="#205394" stroke="#fff" strokeWidth="2"/>
              <text x="222" y="146" fontSize="11" fill="#205394" fontWeight="bold">项目位置</text>
              <text x="222" y="160" fontSize="9" fill="#64748b">惠州市惠城区马安镇</text>
            </>
          )}
          {kind==='scope' && (
            <>
              <polygon points="120,90 290,80 300,210 135,225" fill="rgba(15,155,142,0.18)" stroke="#0c7f76" strokeWidth="1.5" strokeDasharray="6 3"/>
              <text x="150" y="160" fontSize="11" fill="#0b665f" fontWeight="bold">防治责任范围 3.54 hm²</text>
            </>
          )}
          {kind==='measure' && (
            <>
              <rect x="130" y="92" width="80" height="60" fill="rgba(32,83,148,0.12)" stroke="#205394" strokeWidth="1"/>
              <rect x="215" y="92" width="75" height="55" fill="rgba(217,154,6,0.12)" stroke="#d99a06" strokeWidth="1"/>
              <rect x="135" y="160" width="160" height="55" fill="rgba(15,155,142,0.12)" stroke="#0c7f76" strokeWidth="1"/>
              <text x="138" y="106" fontSize="8.5" fill="#205394">建构筑物区</text>
              <text x="220" y="106" fontSize="8.5" fill="#a06d05">道路广场区</text>
              <text x="140" y="174" fontSize="8.5" fill="#0b665f">绿化区 / 临时施工区</text>
            </>
          )}
          {kind==='monitor' && (
            <>
              {[['M1',160,110,'沉沙池出口'],['M2',265,130,'施工出入口'],['M3',200,195,'绿化区']].map(([id,x,y,t]) => (
                <g key={id}>
                  <circle cx={x} cy={y} r="6" fill="#d24b2c" stroke="#fff" strokeWidth="1.5"/>
                  <text x={x+9} y={y-2} fontSize="10" fill="#b04127" fontWeight="bold">{id}</text>
                  <text x={x+9} y={y+9} fontSize="8" fill="#64748b">{t}</text>
                </g>
              ))}
            </>
          )}

          {/* 指北针 */}
          <g transform="translate(366,30)">
            <polygon points="0,-14 5,6 0,1 -5,6" fill="#334155"/>
            <text x="-3" y="-18" fontSize="10" fill="#334155" fontWeight="bold">N</text>
          </g>
          {/* 比例尺 */}
          <g transform="translate(20,278)">
            <rect x="0" y="0" width="30" height="4" fill="#334155"/>
            <rect x="30" y="0" width="30" height="4" fill="#fff" stroke="#334155" strokeWidth="0.5"/>
            <text x="0" y="-3" fontSize="8" fill="#475569">0      100m</text>
          </g>
        </svg>
      </div>
      {/* 图签 */}
      <div className="grid grid-cols-4 border border-t-0 border-slate-300 text-[9.5px] text-slate-500">
        <div className="px-2 py-1 border-r border-slate-200">图名：{title}</div>
        <div className="px-2 py-1 border-r border-slate-200">图号：{num.replace('图 ','')}</div>
        <div className="px-2 py-1 border-r border-slate-200">编制：广东某某水保技术</div>
        <div className="px-2 py-1">日期：2026-06</div>
      </div>
    </div>
  );
}

function MapLegend({ kind }) {
  const items = [
    ['项目红线','#d24b2c','line'],
    ['防治责任范围','#0c7f76','fill'],
    ...(kind==='measure'?[['防治分区','#205394','fill']]:[]),
    ...(kind==='monitor'?[['监测点位','#d24b2c','dot']]:[]),
    ['临时措施','#d99a06','fill'],
  ];
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-3 px-1">
      {items.map(([t,c,shape]) => (
        <span key={t} className="inline-flex items-center gap-1.5 text-[11px] text-slate-500">
          {shape==='line' && <span className="w-4 h-0.5" style={{background:c}}></span>}
          {shape==='fill' && <span className="w-3.5 h-3" style={{background:c,opacity:.3,border:`1px solid ${c}`}}></span>}
          {shape==='dot' && <span className="w-2.5 h-2.5 rounded-full" style={{background:c}}></span>}
          {t}
        </span>
      ))}
    </div>
  );
}

// ---------- 弹窗 ----------
function Modal({ title, icon, onClose, children, footer }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
      <div className="absolute inset-0 bg-slate-900/40" onClick={onClose}></div>
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-[520px] max-h-[88vh] flex flex-col">
        <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-slate-100">
          <Icon name={icon} size={18} className="text-brand-600"/>
          <span className="text-[14.5px] font-semibold text-slate-800">{title}</span>
          <button onClick={onClose} className="ml-auto w-7 h-7 rounded hover:bg-slate-100 grid place-items-center text-slate-400"><Icon name="X" size={16}/></button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
        {footer && <div className="px-5 py-3 border-t border-slate-100 flex items-center justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}

const mInput = "w-full h-9 rounded-md border border-slate-300 text-[13px] px-3 focus:outline-none focus:ring-2 focus:ring-brand-300";

function MapsPage({ setPage }) {
  const [cat, setCat] = useState('all');
  const [activeId, setActiveId] = useState('FIG-002');
  const [modal, setModal] = useState(null); // upload | newmap | insert
  const [toast, setToast] = useState(null);
  const [insertedCh, setInsertedCh] = useState(null);
  const [newGen, setNewGen] = useState(false);

  const list = FIGURES.filter(f => cat==='all' || f.cat===cat);
  const cur = FIGURES.find(f=>f.id===activeId) || list[0];
  const isMap = cur && cur.map;

  const flash = (msg) => { setToast(msg); setTimeout(()=>setToast(null), 4000); };

  const ToolBtn = ({ icon, label, onClick, primary }) => (
    <button onClick={onClick} className={`inline-flex items-center gap-1.5 text-[12px] px-2.5 py-1.5 rounded-md whitespace-nowrap transition-colors ${primary?'bg-brand-600 text-white hover:bg-brand-700':'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'}`}>
      <Icon name={icon} size={14}/>{label}
    </button>
  );

  return (
    <div>
      <PageHeader title="附图与地图中心" sub="区位图 · 责任范围图 · 措施布局图 · 监测点位图 · 典型图 · 外部图纸 — 纳入插图、依据链与交付包" icon="Map">
        <Chip tone="teal" icon="Map">6 图件</Chip>
      </PageHeader>

      {/* 工具栏 */}
      <div className="flex items-center gap-1.5 px-5 py-2 border-b border-slate-200 bg-slate-50/80 overflow-x-auto">
        <ToolBtn icon="Upload" label="上传图件" onClick={()=>setModal('upload')} primary/>
        <ToolBtn icon="MapPlus" label="新建地图" onClick={()=>{setModal('newmap');setNewGen(false);}}/>
        <ToolBtn icon="LayoutTemplate" label="选择图件模板" onClick={()=>{setModal('newmap');setNewGen(false);}}/>
        <div className="w-px h-6 bg-slate-200 mx-0.5"></div>
        <ToolBtn icon="FileInput" label="插入正文" onClick={()=>setModal('insert')}/>
        <ToolBtn icon="ImageDown" label="导出 PNG" onClick={()=>flash('已导出 '+cur.id+'.png')}/>
        <ToolBtn icon="FileDown" label="导出 PDF" onClick={()=>flash('已导出 '+cur.id+'.pdf')}/>
        <ToolBtn icon="GitBranch" label="查看依赖链" onClick={()=>flash('依赖链：'+cur.facts.join('、'))}/>
      </div>

      {/* toast */}
      {toast && (
        <div className="fixed top-20 right-6 z-40 px-4 py-2.5 rounded-lg bg-slate-800 text-white text-[12.5px] shadow-lg flex items-center gap-2">
          <Icon name="CircleCheck" size={15} className="text-emerald-400"/>{toast}
        </div>
      )}

      <div className="grid grid-cols-[230px_1fr_320px] h-[calc(100vh-56px-65px-49px)] min-w-[1180px]">
        {/* 左：分类 */}
        <aside className="border-r border-slate-200 bg-white overflow-y-auto p-2">
          <button onClick={()=>setCat('all')} className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md mb-0.5 ${cat==='all'?'bg-brand-50 text-brand-700':'text-slate-600 hover:bg-slate-50'}`}>
            <Icon name="LayoutGrid" size={15} className={cat==='all'?'text-brand-600':'text-slate-400'}/><span className="flex-1 text-left text-[12.5px]">全部图件</span>
            <span className="text-[10px] font-mono text-slate-400">{FIGURES.length}</span>
          </button>
          <div className="text-[10.5px] font-semibold text-slate-400 uppercase px-2 py-1.5 tracking-wide">图件分类</div>
          {FIGURE_CATS.map(c => {
            const act = cat===c.id;
            const tone = c.status==='已完成'||c.status==='已生成'||c.status==='已上传'||c.status==='已选用'?'emerald':c.status==='可生成'?'brand':c.status==='待补充'?'amber':'slate';
            return (
              <button key={c.id} onClick={()=>setCat(c.id)} className={`w-full px-2.5 py-2 rounded-md mb-0.5 text-left transition-colors ${act?'bg-brand-50':'hover:bg-slate-50'}`}>
                <div className="flex items-center gap-2">
                  <span className={`flex-1 text-[12px] ${act?'text-brand-700 font-medium':'text-slate-600'}`}>{c.name}</span>
                  <span className="text-[10px] font-mono tabular text-slate-400">{c.done}/{c.total}</span>
                </div>
                <div className="mt-1"><StatusTag status={c.status==='已完成'?'已生成':c.status} /></div>
              </button>
            );
          })}
        </aside>

        {/* 中：图件列表 + 地图预览 */}
        <section className="overflow-y-auto bg-[#dfe3ea] p-5">
          {/* 列表 */}
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden mb-4">
            <table className="w-full text-[12px]">
              <thead><tr className="text-[10.5px] text-slate-400 border-b border-slate-100 bg-slate-50">
                <th className="text-left font-medium px-3 py-2">编号 / 名称</th><th className="text-left font-medium px-2 py-2">类型</th>
                <th className="text-left font-medium px-2 py-2">来源</th><th className="text-left font-medium px-2 py-2">关联章节</th>
                <th className="text-left font-medium px-2 py-2">状态</th><th className="text-left font-medium px-2 py-2">交付包</th>
              </tr></thead>
              <tbody>
                {list.map(f => {
                  const act = activeId===f.id;
                  return (
                    <tr key={f.id} onClick={()=>setActiveId(f.id)} className={`border-b border-slate-50 last:border-0 cursor-pointer transition-colors ${act?'bg-brand-50/70':'hover:bg-slate-50'}`}>
                      <td className="px-3 py-2.5"><div className="font-mono text-[10.5px] text-slate-400">{f.id}</div><div className="text-slate-800 font-medium">{f.name}</div></td>
                      <td className="px-2 py-2.5 text-slate-500">{f.type}</td>
                      <td className="px-2 py-2.5 text-slate-400 max-w-[120px]">{f.source}</td>
                      <td className="px-2 py-2.5 text-slate-500">{f.chapter}</td>
                      <td className="px-2 py-2.5"><StatusTag status={f.status} dot/></td>
                      <td className="px-2 py-2.5">{f.exp?<Icon name="Check" size={14} className="text-emerald-500"/>:<Icon name="Minus" size={14} className="text-slate-300"/>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* 地图预览 */}
          {cur && (
            <div className="bg-white rounded-lg border border-slate-200 a4-shadow p-5">
              {isMap ? (
                <>
                  <MapPreview kind={cur.map} title={cur.name} num={'图 '+({loc:'2-1',scope:'6-1',measure:'7-1',monitor:'8-1'}[cur.map]||'X-1')} />
                  <MapLegend kind={cur.map} />
                  <div className="mt-3 text-[11px] text-slate-400 flex items-center gap-1.5"><Icon name="Info" size={12}/>模拟地图装配预览（schematic），用于表达图层与要素能力，不接入真实地图 API。</div>
                </>
              ) : (
                <div className="text-center py-12">
                  <div className="w-16 h-16 rounded-lg bg-slate-100 grid place-items-center mx-auto text-slate-400"><Icon name={cur.type==='典型图'?'PencilRuler':'FileImage'} size={28}/></div>
                  <div className="text-[13.5px] font-medium text-slate-700 mt-3">{cur.name}</div>
                  <div className="text-[12px] text-slate-400 mt-1">{cur.type} · {cur.source}</div>
                  <div className="mt-3 inline-block px-3 py-1.5 rounded bg-slate-50 border border-slate-200 text-[11.5px] text-slate-500">{cur.type==='外部图纸'?'外部图纸附件，待审查后纳入插图':'典型图库选用，自动纳入措施章节'}</div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* 右：详情 */}
        <aside className="border-l border-slate-200 bg-white overflow-y-auto">
          {cur && (
            <>
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <span className="font-mono text-[13px] font-semibold text-slate-700">{cur.id}</span>
                <StatusTag status={cur.status} dot/>
              </div>
              <div className="p-4 space-y-4">
                {insertedCh===cur.id && (
                  <div className="flex items-start gap-2 p-2.5 rounded-md bg-emerald-50 border border-emerald-200 text-[11.5px] text-emerald-800">
                    <Icon name="CircleCheck" size={14} className="text-emerald-600 shrink-0 mt-0.5"/>已插入正文，正文预览页将显示图件占位。
                  </div>
                )}
                <div className="space-y-1.5">
                  <Field k="图件名称" v={cur.name} />
                  <Field k="图件类型" v={cur.type} />
                  <Field k="来源类型" v={cur.source} />
                  <Field k="生成方式" v={cur.gen} />
                  <Field k="关联章节" v={cur.chapter} />
                </div>
                {cur.facts.length>0 && (
                  <div>
                    <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="Database" size={12}/>关联事实</div>
                    <div className="space-y-1">{cur.facts.map(f=><div key={f} className="font-mono text-[11px] text-slate-600 bg-slate-50 border border-slate-100 rounded px-2 py-1">{f}</div>)}</div>
                  </div>
                )}
                {cur.tables.length>0 && (
                  <div>
                    <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="Table2" size={12}/>关联表格</div>
                    <div className="flex flex-wrap gap-1">{cur.tables.map(t=><Chip key={t} tone="teal">{t}</Chip>)}</div>
                  </div>
                )}
                {cur.notes.length>0 && (
                  <div>
                    <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="Asterisk" size={12}/>关联注脚</div>
                    <div className="space-y-1">{cur.notes.map(n=><div key={n} className="text-[11.5px] text-amber-700 bg-amber-50 border border-amber-100 rounded px-2 py-1">{n}</div>)}</div>
                  </div>
                )}
                <div>
                  <div className="text-[11.5px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5"><Icon name="FileOutput" size={12}/>导出格式</div>
                  <div className="flex flex-wrap gap-1">{['PNG','PDF','Word 插图'].map(t=><Chip key={t} tone="slate">{t}</Chip>)}</div>
                </div>
                <div className="rounded-md border border-slate-200 overflow-hidden">
                  <div className="px-3 py-2 bg-slate-50 text-[11.5px] font-semibold text-slate-600 flex items-center gap-1.5"><Icon name="ClipboardCheck" size={13}/>审查状态</div>
                  <div className="px-3 py-2 text-[12px] text-slate-600">{cur.review}</div>
                </div>
                <div className="flex items-center justify-between px-3 py-2 rounded-md bg-slate-50 border border-slate-100">
                  <span className="text-[12px] text-slate-500">是否进入交付包</span>
                  <StatusTag status={cur.exp?'通过':'不适用'} dot/>
                </div>
                <div className="flex gap-2 pt-1">
                  <button onClick={()=>setModal('insert')} className="flex-1 text-[12px] py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700 inline-flex items-center justify-center gap-1.5"><Icon name="FileInput" size={13}/>插入正文</button>
                  <button onClick={()=>flash('已导出 '+cur.id+'.png')} className="text-[12px] px-3 py-1.5 rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50"><Icon name="Download" size={13}/></button>
                </div>
              </div>
            </>
          )}
        </aside>
      </div>

      {/* 上传图件弹窗 */}
      {modal==='upload' && (
        <Modal title="上传图件" icon="Upload" onClose={()=>setModal(null)}
          footer={<>
            <button onClick={()=>setModal(null)} className="text-[13px] px-3.5 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50">取消</button>
            <button onClick={()=>{setModal(null);flash('已上传 3 个图件：其中 2 个已绑定章节，1 个待选择插入位置。');}} className="text-[13px] px-3.5 py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700">确认上传</button>
          </>}>
          <div className="space-y-3.5">
            <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-5 text-center">
              <Icon name="UploadCloud" size={26} className="text-slate-400 mx-auto"/>
              <div className="text-[12.5px] text-slate-500 mt-1.5">拖拽文件到此处，或点击选择</div>
              <div className="text-[11px] text-slate-400 mt-0.5">支持 .pdf / .dwg / .dxf / .png / .jpg</div>
            </div>
            <div className="space-y-1.5">
              <div className="text-[11.5px] text-slate-500">已选择文件：</div>
              {['总平面布置图.pdf','项目红线图.dwg','排水沟典型图.png'].map(f=>(
                <div key={f} className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-slate-50 border border-slate-100 text-[12px] text-slate-600"><Icon name="File" size={13} className="text-slate-400"/>{f}</div>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="block"><span className="text-[11.5px] text-slate-500">图件名称</span><input className={mInput} defaultValue="总平面布置图"/></label>
              <label className="block"><span className="text-[11.5px] text-slate-500">图件类型</span><select className={mInput}><option>外部图纸</option><option>地图</option><option>典型图</option></select></label>
              <label className="block"><span className="text-[11.5px] text-slate-500">关联章节</span><select className={mInput}><option>2.1 项目概况</option><option>6 防治责任范围</option><option>7 水土保持措施</option></select></label>
              <label className="block"><span className="text-[11.5px] text-slate-500">是否进入交付包</span><select className={mInput}><option>是</option><option>否</option></select></label>
            </div>
            <label className="block"><span className="text-[11.5px] text-slate-500">图注内容</span><input className={mInput} placeholder="图件来源说明 / 图注…"/></label>
          </div>
        </Modal>
      )}

      {/* 新建地图弹窗 */}
      {modal==='newmap' && (
        <Modal title="新建地图图件" icon="MapPlus" onClose={()=>setModal(null)}
          footer={newGen ? (
            <><button onClick={()=>setModal(null)} className="text-[13px] px-3.5 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50">关闭</button>
            <button onClick={()=>{setModal('insert');}} className="text-[13px] px-3.5 py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700">插入第 6 章正文</button></>
          ) : (
            <><button onClick={()=>setModal(null)} className="text-[13px] px-3.5 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50">取消</button>
            <button onClick={()=>setNewGen(true)} className="text-[13px] px-3.5 py-1.5 rounded-md bg-brand-600 text-white hover:bg-brand-700 inline-flex items-center gap-1.5"><Icon name="Sparkles" size={14}/>生成预览</button></>
          )}>
          {newGen ? (
            <div className="text-center py-3">
              <div className="border border-slate-300 rounded-lg overflow-hidden"><MapPreview kind="scope" title="水土流失防治责任范围图" num="图 6-1"/></div>
              <div className="mt-3 inline-flex items-center gap-1.5 text-[12.5px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md px-3 py-1.5"><Icon name="CircleCheck" size={15}/>已生成地图预览 · 图件状态：已生成 · 可插入正文第 6 章</div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <label className="block"><span className="text-[11.5px] text-slate-500">图件名称</span><input className={mInput} defaultValue="水土流失防治责任范围图"/></label>
                <label className="block"><span className="text-[11.5px] text-slate-500">图件类型</span><select className={mInput}><option>地图</option></select></label>
                <label className="block"><span className="text-[11.5px] text-slate-500">关联章节</span><select className={mInput}><option>6 防治责任范围</option></select></label>
                <label className="block"><span className="text-[11.5px] text-slate-500">地图模板</span><select className={mInput}>{FIGURE_TEMPLATES.map(t=><option key={t}>{t}</option>)}</select></label>
              </div>
              <div>
                <div className="text-[11.5px] text-slate-500 mb-1.5">图层与要素</div>
                <div className="grid grid-cols-2 gap-1.5">
                  {[['底图',true],['项目边界',true],['防治分区',true],['监测点位',false],['图例',true],['比例尺',true],['指北针',true]].map(([t,on]) => (
                    <label key={t} className="flex items-center gap-1.5 text-[12px] text-slate-600 px-2 py-1 rounded bg-slate-50 border border-slate-100"><input type="checkbox" defaultChecked={on} className="accent-brand-600"/>{t}</label>
                  ))}
                </div>
              </div>
              <label className="block"><span className="text-[11.5px] text-slate-500">导出格式</span><select className={mInput}><option>PNG + PDF + Word 插图</option><option>仅 PNG</option></select></label>
            </div>
          )}
        </Modal>
      )}

      {/* 插入正文弹窗 */}
      {modal==='insert' && (
        <Modal title="插入正文" icon="FileInput" onClose={()=>setModal(null)}>
          <div className="text-[12.5px] text-slate-500 mb-3">选择插入位置（{cur.id} {cur.name}）：</div>
          <div className="space-y-1.5">
            {['2.1 项目概况','6 防治责任范围','7 水土保持措施','8 监测安排','附图目录'].map((ch,i) => (
              <button key={ch} onClick={()=>{ setInsertedCh(cur.id); setModal(null); flash(`图件 ${cur.id} 已插入第 ${ch}。正文预览将显示图件占位。`); }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md border text-left transition-colors ${i===1?'border-brand-300 bg-brand-50/50':'border-slate-200 hover:bg-slate-50'}`}>
                <span className="text-[13px] text-slate-700">{ch}</span>
                <Icon name="ArrowRight" size={14} className="text-slate-400"/>
              </button>
            ))}
          </div>
        </Modal>
      )}
    </div>
  );
}

window.MapsPage = MapsPage;
