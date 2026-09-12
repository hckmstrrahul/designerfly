import { useRef, useState, type PointerEvent } from 'react';
import { Play, Trash2, X, Square, RectangleHorizontal, Circle, Triangle, LayoutTemplate, Type } from 'lucide-react';
import { constrainShape, UI_EXAMPLE, MAX_SHAPES, textStudy, type PlacedShape } from '@/lib/composition';
import { validText } from '@/lib/lettering';

export function CompositionEditor({ shapes, onChange, onDraw, onClose }: { shapes: PlacedShape[]; onChange: (s: PlacedShape[]) => void; onDraw: () => void; onClose: () => void }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [textOpen, setTextOpen] = useState(false);
  const [lettering, setLettering] = useState('HELLO\nWORLD');
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{ id: number; kind: 'move' | 'resize'; origin: [number, number]; shape: PlacedShape } | null>(null);
  const point = (e: PointerEvent) => {
    const bounds = svg.current!.getBoundingClientRect();
    return [(e.clientX - bounds.left) / bounds.width * 2 - 1, (e.clientY - bounds.top) / bounds.height * 2 - 1] as [number, number];
  };
  const start = (e: PointerEvent<SVGGElement | SVGRectElement>, s: PlacedShape, kind: 'move' | 'resize') => {
    e.preventDefault(); e.stopPropagation(); e.currentTarget.setPointerCapture(e.pointerId);
    setSelected(s.id); drag.current = { id: s.id, kind, origin: point(e), shape: s };
  };
  const move = (e: PointerEvent<SVGSVGElement>) => {
    if (!drag.current) return;
    const { id, kind, origin, shape } = drag.current, p = point(e), dx = p[0] - origin[0], dy = p[1] - origin[1];
    const next = kind === 'move' ? { ...shape, x: shape.x + dx, y: shape.y + dy } : { ...shape, width: shape.width + dx * 2, height: shape.height + dy * 2 };
    onChange(shapes.map(s => s.id === id ? constrainShape(next) : s));
  };
  const palette = [
    { name: 'Rectangle', shape: 0, Icon: RectangleHorizontal, width: .65, height: .4 },
    { name: 'Square', shape: 0, Icon: Square, width: .48, height: .48, variant: 'square' as const },
    { name: 'Circle', shape: 1, Icon: Circle, width: .48, height: .48 },
    { name: 'Ellipse', shape: 1, Icon: Circle, width: .68, height: .38, variant: 'ellipse' as const },
    { name: 'Triangle', shape: 2, Icon: Triangle, width: .55, height: .55 },
  ];
  const selectedShape = shapes.find(s => s.id === selected);
  return <div className={`composition-editor${textOpen ? ' lettering-open' : ''}`}>
    <div className="composition-heading"><div><span className="composition-kicker">COMPOSITION</span><h2>Arrange a study<span>.</span></h2></div><button className="editor-close" onClick={onClose} aria-label="Close arrangement"><X size={18} /></button></div>
    <div className="composition-toolbar" aria-label="Add a shape">{palette.map(({ name, shape, Icon, width, height, variant }) => <button key={name} disabled={shapes.length >= MAX_SHAPES} title={`Add ${name.toLowerCase()}`} onClick={() => { const id = Math.max(0, ...shapes.map(s => s.id)) + 1; onChange([...shapes, constrainShape({ id, shape, width, height, variant, x: 0, y: 0 })]); setSelected(id); }}><Icon size={20} strokeWidth={1.6} style={variant === 'ellipse' ? { transform: 'scaleY(.65)' } : undefined} /><span>{name}</span></button>)}<span className="composition-count">{shapes.length}<span> / {MAX_SHAPES}</span></span></div>
    {textOpen && <div className="lettering-panel">
      <label htmlFor="fly-lettering">Write with the fly<span>A name, a note, a little hello.</span></label>
      <textarea id="fly-lettering" value={lettering} maxLength={20} rows={3} placeholder={'YOUR NAME\nGOES HERE'} onChange={e=>setLettering(e.target.value)} spellCheck={false} />
      <div className="lettering-meta"><span>Enter for a new line · A–Z, 0–9</span><span>{lettering.length} / 20</span></div>
      {!validText(lettering) && <output>Use letters, numbers, spaces or . ! ? -</output>}
    </div>}
    <div className="composition-workspace">
    <svg ref={svg} className="composition-paper" viewBox="-1 -1 2 2" aria-label="Shape arrangement. Drag shapes to place them; drag the corner handle to resize." onPointerMove={move} onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }} onPointerDown={() => setSelected(null)}>
      <rect x={-.995} y={-.995} width={1.99} height={1.99} fill="#fffdf5" />
      {/* SVG groups cannot be replaced with HTML buttons. */}
      {/* oxlint-disable-next-line jsx-a11y/prefer-tag-over-role */}
      {shapes.map(s => <g key={s.id} role="button" tabIndex={0} aria-label={`Select ${s.variant || ['rectangle', 'circle', 'triangle'][s.shape]} ${s.id}`} onFocus={() => setSelected(s.id)} onPointerDown={e => start(e, s, 'move')} onKeyDown={e => {
        if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); onChange(shapes.filter(item => item.id !== s.id)); return; }
        const dx = e.key === 'ArrowLeft' ? -.04 : e.key === 'ArrowRight' ? .04 : 0, dy = e.key === 'ArrowUp' ? -.04 : e.key === 'ArrowDown' ? .04 : 0;
        if (dx || dy) { e.preventDefault(); onChange(shapes.map(item => item.id === s.id ? constrainShape(e.shiftKey ? { ...s, width: s.width + dx, height: s.height + dy } : { ...s, x: s.x + dx, y: s.y + dy }) : item)); }
      }}>
        <rect x={s.x - s.width / 2 - .03} y={s.y - s.height / 2 - .03} width={s.width + .06} height={s.height + .06} fill="transparent" stroke={selected === s.id ? '#df7648' : 'none'} strokeWidth={.006} vectorEffect="non-scaling-stroke" />
        {s.points ? <polyline points={s.points.map(([x,y])=>`${s.x+x*s.width},${s.y+y*s.height}`).join(' ')} /> : s.shape === 0 ? <rect x={s.x - s.width / 2} y={s.y - s.height / 2} width={s.width} height={s.height} /> : s.shape === 1 ? <ellipse cx={s.x} cy={s.y} rx={s.width / 2} ry={s.height / 2} /> : <polygon points={`${s.x},${s.y - s.height / 2} ${s.x + s.width / 2},${s.y + s.height / 2} ${s.x - s.width / 2},${s.y + s.height / 2}`} />}
        {selected === s.id && <rect className="resize-handle" x={s.x + s.width / 2 - .035} y={s.y + s.height / 2 - .035} width={.07} height={.07} onPointerDown={e => start(e, s, 'resize')} />}
      </g>)}
    </svg>
    </div>
    <div className="composition-actions"><div className="composition-secondary">
      {!textOpen && <button className="editor-delete" aria-label="Delete selected shape" disabled={!selectedShape} onClick={() => { onChange(shapes.filter(s => s.id !== selected)); setSelected(null); }}><Trash2 size={16} /></button>}
      <button onClick={() => { onChange(UI_EXAMPLE.map(s => ({ ...s }))); setSelected(null); setTextOpen(false); }}><LayoutTemplate size={16} /><span>UI Example</span></button>
      <button aria-pressed={textOpen} onClick={()=>setTextOpen(!textOpen)}><Type size={16} />Text</button>
    </div><button className="draw-study" disabled={textOpen ? !lettering.trim() || !validText(lettering) : !shapes.length} onClick={()=>{if(textOpen){onChange(textStudy(lettering));setSelected(null);setTextOpen(false);}else onDraw();}}><Play size={15} />{textOpen ? 'Preview lettering' : 'Draw study'}</button></div>
    {!textOpen && <p className="composition-help">Drag to move · Corner to resize · Supplied paths, neural motor</p>}

  </div>;
}
