import { useRef, useState, type KeyboardEvent, type PointerEvent } from 'react';
import { Play, Trash2, X, Square, RectangleHorizontal, Circle, Triangle, Type, Smile, MousePointer2, FilePlus2, Pencil, Undo2, Redo2 } from 'lucide-react';
import { constrainShape, UI_EXAMPLE, MAX_SHAPES, textStudy, type PlacedShape } from '@/lib/composition';
import { EMOJIS, emojiStudy } from '@/lib/emoji';
import { validText, MAX_TEXT_LENGTH, type PenPoint } from '@/lib/lettering';
import { selectionBounds, sameSelection, transformSelection, validStrokeBounds } from '@/lib/composition-groups';
import { freehandStroke } from '@/lib/freehand';

export type EditorMode = 'arrange' | 'text' | 'emoji';
export type EditorTool = 'arrange' | 'text' | 'emoji' | 'pen';
export function CompositionEditor({ mode, shapes, onChange: publish, onDraw, onClose, tool, onTool }: { mode: EditorMode; tool: EditorTool; onTool: (tool: EditorTool) => void; shapes: PlacedShape[]; onChange: (s: PlacedShape[]) => void; onDraw: (paths: PlacedShape[]) => void; onClose: () => void }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [histories,setHistories]=useState<Record<EditorMode,{past:PlacedShape[][];future:PlacedShape[][]}>>({arrange:{past:[],future:[]},text:{past:[],future:[]},emoji:{past:[],future:[]}});
  const history=histories[mode];
  const record=(before:PlacedShape[],after:PlacedShape[])=>{
    if(JSON.stringify(before)===JSON.stringify(after))return;
    setHistories(all=>({...all,[mode]:{past:[...all[mode].past,before].slice(-100),future:[]}}));
  };
  const onChange=(next:PlacedShape[])=>{record(shapes,next);publish(next);};
  const undo=()=>{
    const previous=history.past.at(-1);if(!previous)return;
    setHistories(all=>({...all,[mode]:{past:history.past.slice(0,-1),future:[shapes,...history.future]}}));
    publish(previous);if(!previous.some(s=>s.id===selected))setSelected(null);(svg.current?.closest('.paint-editor') as HTMLElement | null)?.focus();
  };
  const redo=()=>{
    const next=history.future[0];if(!next)return;
    setHistories(all=>({...all,[mode]:{past:[...history.past,shapes],future:history.future.slice(1)}}));
    publish(next);if(!next.some(s=>s.id===selected))setSelected(null);(svg.current?.closest('.paint-editor') as HTMLElement | null)?.focus();
  };
  const [draft,setDraft] = useState<PenPoint[]>([]);
  const pen = useRef<{pointer:number;points:PenPoint[]} | null>(null);
  const textOpen = tool === 'text';
  const addPaths = (paths: PlacedShape[], label: string) => {
    const id=Math.max(0,...shapes.map(s=>s.id))+1;
    const added=paths.map((s,i)=>validStrokeBounds({...s,id:id+i,groupId:id,groupLabel:label,x:s.x*.55,y:s.y*.55,width:s.width*.55,height:s.height*.55}));
    onChange([...shapes,...added]);setSelected(id);
  };
  const [emoji,setEmoji]=useState<string | null>(null);
  const [lettering, setLettering] = useState('HELLO\nWORLD');
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{ id: number; kind: 'move' | 'resize'; origin: [number, number]; shape: PlacedShape; shapes: PlacedShape[] } | null>(null);
  const point = (e: PointerEvent) => {
    const bounds = svg.current!.getBoundingClientRect();
    return [(e.clientX - bounds.left) / bounds.width * 2 - 1, (e.clientY - bounds.top) / bounds.height * 2 - 1] as [number, number];
  };
  const penDown = (e:PointerEvent<SVGSVGElement>) => {
    setSelected(null);
    if(tool!=='pen'||e.button!==0||pen.current||shapes.length>=MAX_SHAPES)return;
    e.preventDefault();e.currentTarget.setPointerCapture(e.pointerId);
    pen.current={pointer:e.pointerId,points:[point(e)]};setDraft(pen.current.points);
  };
  const penEnd = (e:PointerEvent<SVGSVGElement>,cancel=false) => {
    if(drag.current){
      if(cancel)publish(drag.current.shapes);else record(drag.current.shapes,shapes);
      drag.current=null;
    }
    if(!pen.current||pen.current.pointer!==e.pointerId)return;
    const raw=pen.current.points;pen.current=null;setDraft([]);
    if(cancel)return;
    const id=Math.max(0,...shapes.map(s=>s.id))+1;
    const stroke=freehandStroke([...raw,point(e)],id);
    if(stroke&&shapes.length<MAX_SHAPES)onChange([...shapes,stroke]);
  };
  const start = (e: PointerEvent<SVGGElement | SVGRectElement>, s: PlacedShape, kind: 'move' | 'resize') => {
    if(tool==='pen')return;
    e.preventDefault(); e.stopPropagation(); e.currentTarget.setPointerCapture(e.pointerId);
    (svg.current?.closest('.paint-editor') as HTMLElement | null)?.focus();setSelected(s.id); drag.current = { id: s.id, kind, origin: point(e), shape: s, shapes };
  };
  const move = (e: PointerEvent<SVGSVGElement>) => {
    if(pen.current){
      if(e.pointerId!==pen.current.pointer)return;
      const p=point(e);p[0]=Math.max(-.98,Math.min(.98,p[0]));p[1]=Math.max(-.98,Math.min(.98,p[1]));
      const points=pen.current.points,last=points.at(-1)!;
      if(Math.hypot(p[0]-last[0],p[1]-last[1])>.002){
        if(points.length>=4096)pen.current.points=points.filter((_,i)=>i%2===0);
        pen.current.points.push(p);setDraft([...pen.current.points]);
      }return;
    }
    if (!drag.current) return;
    const { kind, origin, shape } = drag.current, p = point(e), dx = p[0] - origin[0], dy = p[1] - origin[1];
    publish(transformSelection(drag.current.shapes, shape, dx, dy, kind==='resize'));
  };
  const palette = [
    { name: 'Rectangle', shape: 0, Icon: RectangleHorizontal, width: .65, height: .4 },
    { name: 'Square', shape: 0, Icon: Square, width: .48, height: .48, variant: 'square' as const },
    { name: 'Circle', shape: 1, Icon: Circle, width: .48, height: .48 },
    { name: 'Ellipse', shape: 1, Icon: Circle, width: .68, height: .38, variant: 'ellipse' as const },
    { name: 'Triangle', shape: 2, Icon: Triangle, width: .55, height: .55 },
  ];
  const changed = JSON.stringify(shapes)!==JSON.stringify(UI_EXAMPLE);
  const selectedShape = shapes.find(s => s.id === selected);
  const objects=shapes.filter((s,i)=>s.groupId===undefined || shapes.findIndex(item=>item.groupId===s.groupId)===i);
  const textPaths=validText(lettering)?textStudy(lettering):[];
  const emojiPaths=emoji?emojiStudy(emoji):[];
  const keyboard=(e:KeyboardEvent<HTMLDivElement>)=>{
    if(e.target instanceof HTMLElement && (e.target.matches('input,textarea,select')||e.target.isContentEditable))return;
    if(mode!=='arrange')return;
    const key=e.key.toLowerCase();
    if((e.metaKey||e.ctrlKey)&&!e.altKey&&(key==='z'||key==='y')){
      e.preventDefault();e.stopPropagation();if(key==='y'||e.shiftKey)redo();else undo();return;
    }
    if(tool!=='arrange'||!selectedShape||e.metaKey||e.ctrlKey||e.altKey)return;
    if(e.key==='Delete'||e.key==='Backspace'){
      e.preventDefault();e.stopPropagation();onChange(shapes.filter(s=>!sameSelection(s,selectedShape)));setSelected(null);return;
    }
    const step=e.shiftKey?.04:.01;
    const dx=e.key==='ArrowLeft'?-step:e.key==='ArrowRight'?step:0;
    const dy=e.key==='ArrowUp'?-step:e.key==='ArrowDown'?step:0;
    if(dx||dy){e.preventDefault();e.stopPropagation();onChange(transformSelection(shapes,selectedShape,dx,dy,false));}
  };
  const clearAll=()=>{onChange([]);setSelected(null);setLettering('');setEmoji(null);};
  // The studio application handles canvas shortcuts; native text inputs keep their own keyboard behavior.
  // oxlint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
  return <div className={`composition-editor paint-editor mode-${mode} tool-${tool}`} role="application" aria-label="Drawing studio" tabIndex={-1} onKeyDown={keyboard}>
    <div className="composition-heading"><div><span className="composition-kicker">S–01 / STUDIO</span><h2>{mode === 'text' ? 'Text' : mode === 'emoji' ? 'Emoji' : 'Draw UI'}<span>.</span></h2></div><div className="studio-header-actions">{mode==='arrange'&&<><button aria-label="Undo" title="Undo (⌘/Ctrl Z)" disabled={!history.past.length} onClick={undo}><Undo2 size={18}/></button><button aria-label="Redo" title="Redo (⌘/Ctrl Shift Z)" disabled={!history.future.length} onClick={redo}><Redo2 size={18}/></button></>}<button aria-label="New canvas" title="New canvas" onClick={()=>{onChange([]);setSelected(null);onTool(mode==='arrange'?(tool==='pen'?'pen':'arrange'):mode);}}><FilePlus2 size={18}/></button><button aria-label="Delete selected shape" title="Delete selected shape" disabled={!selectedShape} onClick={()=>{onChange(shapes.filter(s=>!selectedShape||!sameSelection(s,selectedShape)));setSelected(null);}}><Trash2 size={18}/></button>{mode==='arrange'&&changed&&<button className="clear-all" aria-label="Reset to UI example" title="Reset to UI example" onClick={()=>{onChange(UI_EXAMPLE.map(s=>({...s})));setSelected(null);onTool('arrange');}}>Reset</button>}<button className="clear-all" onClick={clearAll}>Clear all</button><button className="editor-close" onClick={onClose} aria-label="Close arrangement"><X size={18} /></button></div></div>
    {mode==='arrange'&&<aside className="paint-tools" aria-label="Drawing tools">
      <button className="studio-mode" aria-pressed={tool==='arrange'} onClick={()=>onTool('arrange')} title="Select and arrange"><MousePointer2 size={20}/><span>Select</span></button>
      <div className="tool-separator" />
      {palette.map(({ name, shape, Icon, width, height, variant }) => <button key={name} disabled={shapes.length >= MAX_SHAPES} aria-label={`Add ${name.toLowerCase()}`} title={`Add ${name.toLowerCase()}`} onClick={() => { const id = Math.max(0, ...shapes.map(s => s.id)) + 1; onChange([...shapes, constrainShape({ id, shape, width, height, variant, x: 0, y: 0 })]); setSelected(id); onTool('arrange'); }}><Icon size={20} strokeWidth={1.6} style={variant === 'ellipse' ? { transform: 'scaleY(.65)' } : undefined} /></button>)}
      <div className="tool-separator" />
      {([{id:'text',label:'Text',Icon:Type},{id:'emoji',label:'Emoji',Icon:Smile},{id:'pen',label:'Pen',Icon:Pencil}] as const).map(({id,label,Icon})=><button key={id} aria-label={`${label} tool`} title={label} aria-pressed={tool===id} onClick={()=>{setSelected(null);onTool(id);}}><Icon size={20}/></button>)}
    </aside>}
    <div className="paint-content">
    {textOpen && <div className="lettering-panel tool-panel">
      <label htmlFor="fly-lettering">Write with the fly<span>A name, a note, a little hello.</span></label>
      <textarea id="fly-lettering" value={lettering} maxLength={MAX_TEXT_LENGTH} rows={3} placeholder={'YOUR NAME\nGOES HERE'} onChange={e=>setLettering(e.target.value.toUpperCase())} spellCheck={false} />
      <div className="lettering-meta"><span>Enter for a new line · A–Z, 0–9</span><span>{lettering.length} / {MAX_TEXT_LENGTH}</span></div>
      {!validText(lettering) && <output>Use letters, numbers, spaces or . ! ? -</output>}
      {mode==='arrange'&&<button disabled={!lettering.trim()||!textPaths.length||shapes.length+textPaths.length>MAX_SHAPES} onClick={()=>addPaths(textPaths,'Text')}>Add text</button>}
      {mode==='text'&&<div className="text-preview" aria-label="Live lettering preview"><svg viewBox="-1 -1 2 2">{textPaths.map(s=><polyline key={s.id} points={s.points!.map(([x,y])=>`${s.x+x*s.width},${s.y+y*s.height}`).join(' ')}/>)}</svg></div>}
    </div>}
    {tool==='emoji'  && <div className="emoji-panel tool-panel"><div className="emoji-choices">{EMOJIS.map(e=><button key={e.id} disabled={(mode==='arrange'?shapes.length:0)+e.paths.length>MAX_SHAPES} aria-pressed={mode==='emoji'?emoji===e.id:undefined} onClick={()=>{if(mode==='arrange')addPaths(emojiStudy(e.id),e.label);else setEmoji(e.id);}}><svg viewBox="-1 -1 2 2" aria-hidden="true">{e.paths.map((path,i)=><polyline key={i} points={path.map(p=>p.join(',')).join(' ')}/>)}</svg><span>{e.label}</span></button>)}</div></div>}
    <div className="composition-workspace" hidden={mode!=='arrange'}>
    <svg ref={svg} className="composition-paper" viewBox="-1 -1 2 2" aria-label={tool==='pen'?'Freehand canvas. Drag to draw a stroke.':'Shape arrangement. Drag shapes to place them; drag the corner handle to resize.'} onPointerMove={move} onPointerUp={e=>penEnd(e)} onPointerCancel={e=>penEnd(e,true)} onLostPointerCapture={()=>{pen.current=null;setDraft([]);drag.current=null;}} onPointerDown={penDown}>
      <rect x={-.995} y={-.995} width={1.99} height={1.99} fill="#fffdf5" />
      {/* SVG groups cannot be replaced with HTML buttons. */}
      {/* oxlint-disable-next-line jsx-a11y/prefer-tag-over-role */}
      {objects.map(object => {const s=selectionBounds(shapes,object);const active=!!selectedShape&&sameSelection(object,selectedShape);return <g key={s.id} role="button" tabIndex={0} aria-label={`Select ${s.groupLabel || s.variant || ['rectangle', 'circle', 'triangle'][s.shape]} ${s.id}`} onFocus={() => setSelected(s.id)} onPointerDown={e => start(e, s, 'move')}>
        <rect x={s.x - s.width / 2 - .03} y={s.y - s.height / 2 - .03} width={s.width + .06} height={s.height + .06} fill="transparent" stroke={active ? '#df7648' : 'none'} strokeWidth={.006} vectorEffect="non-scaling-stroke" />
        {shapes.filter(item=>sameSelection(item,s)).map(item=><ShapeInk key={item.id} shape={item}/>)}
        {active && <rect className="resize-handle" x={s.x + s.width / 2 - .035} y={s.y + s.height / 2 - .035} width={.07} height={.07} onPointerDown={e => start(e, s, 'resize')} />}
      </g>;})}
      {draft.length>1&&<polyline className="pen-draft" points={draft.map(p=>p.join(',')).join(' ')}/>}
    </svg>
    </div>
    </div>
    <div className="composition-actions"><span className="paint-status">{mode==='text'?`${lettering.length} / ${MAX_TEXT_LENGTH} characters`:mode==='emoji'?(emoji?EMOJIS.find(e=>e.id===emoji)?.label:'Choose an emoji'):tool==='pen'?`Drag to draw · ${shapes.length}/${MAX_SHAPES}`:`${shapes.length} / ${MAX_SHAPES} strokes`}</span><button className="draw-study" disabled={mode==='text'?!lettering.trim()||!textPaths.length||textPaths.length>MAX_SHAPES:mode==='emoji'?!emoji:!shapes.length} onClick={()=>onDraw(mode==='text'?textPaths:mode==='emoji'?emojiPaths:shapes)}><Play size={15}/>Draw</button></div>
  </div>;
}

function ShapeInk({shape:s}:{shape:PlacedShape}) {
  return s.points ? <polyline points={s.points.map(([x,y])=>`${s.x+x*s.width},${s.y+y*s.height}`).join(' ')} /> : s.shape===0 ? <rect x={s.x-s.width/2} y={s.y-s.height/2} width={s.width} height={s.height}/> : s.shape===1 ? <ellipse cx={s.x} cy={s.y} rx={s.width/2} ry={s.height/2}/> : <polygon points={`${s.x},${s.y-s.height/2} ${s.x+s.width/2},${s.y+s.height/2} ${s.x-s.width/2},${s.y+s.height/2}`}/>;
}
