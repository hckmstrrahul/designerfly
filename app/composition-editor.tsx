import { useRef, useState, type PointerEvent } from 'react';
import { Play, Trash2, X } from 'lucide-react';
import { constrainShape, SEARCH_FEED, type PlacedShape } from '@/lib/composition';

export function CompositionEditor({ shapes, onChange, onDraw, onClose }: { shapes: PlacedShape[]; onChange: (s: PlacedShape[]) => void; onDraw: () => void; onClose: () => void }) {
  const [selected, setSelected] = useState<number | null>(null);
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
  return <div className="composition-editor">
    <div className="composition-heading"><span>Arrange a study</span><div className="composition-presets"><button onClick={() => { onChange(SEARCH_FEED.map(s => ({ ...s }))); setSelected(null); }}>Search / feed</button><button onClick={onClose} aria-label="Close arrangement"><X size={16} /></button></div></div>
    <svg ref={svg} className="composition-paper" viewBox="-1 -1 2 2" aria-label="Shape arrangement. Drag shapes to place them; drag the corner handle to resize." onPointerMove={move} onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }} onPointerDown={() => setSelected(null)}>
      <rect x={-.995} y={-.995} width={1.99} height={1.99} fill="#fffdf5" />
      {/* SVG groups cannot be replaced with HTML buttons. */}
      {/* oxlint-disable-next-line jsx-a11y/prefer-tag-over-role */}
      {shapes.map(s => <g key={s.id} role="button" tabIndex={0} aria-label={`Select ${['rectangle', 'circle', 'triangle'][s.shape]} ${s.id}`} onFocus={() => setSelected(s.id)} onPointerDown={e => start(e, s, 'move')} onKeyDown={e => {
        if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); onChange(shapes.filter(item => item.id !== s.id)); return; }
        const dx = e.key === 'ArrowLeft' ? -.04 : e.key === 'ArrowRight' ? .04 : 0, dy = e.key === 'ArrowUp' ? -.04 : e.key === 'ArrowDown' ? .04 : 0;
        if (dx || dy) { e.preventDefault(); onChange(shapes.map(item => item.id === s.id ? constrainShape(e.shiftKey ? { ...s, width: s.width + dx, height: s.height + dy } : { ...s, x: s.x + dx, y: s.y + dy }) : item)); }
      }}>
        <rect x={s.x - s.width / 2 - .03} y={s.y - s.height / 2 - .03} width={s.width + .06} height={s.height + .06} fill="transparent" stroke={selected === s.id ? '#df7648' : 'none'} strokeWidth={.006} strokeDasharray=".025 .025" />
        {s.shape === 0 ? <rect x={s.x - s.width / 2} y={s.y - s.height / 2} width={s.width} height={s.height} /> : s.shape === 1 ? <ellipse cx={s.x} cy={s.y} rx={s.width / 2} ry={s.height / 2} /> : <polygon points={`${s.x},${s.y - s.height / 2} ${s.x + s.width / 2},${s.y + s.height / 2} ${s.x - s.width / 2},${s.y + s.height / 2}`} />}
        {selected === s.id && <rect className="resize-handle" x={s.x + s.width / 2 - .035} y={s.y + s.height / 2 - .035} width={.07} height={.07} onPointerDown={e => start(e, s, 'resize')} />}
      </g>)}
    </svg>
    <div className="composition-actions"><button aria-label="Delete selected shape" disabled={selected === null} onClick={() => { onChange(shapes.filter(s => s.id !== selected)); setSelected(null); }}><Trash2 size={15} /></button><span>Drag to place · corner to resize</span><button className="draw-study" disabled={!shapes.length} onClick={onDraw}><Play size={13} />Draw {shapes.length || ''}</button></div>
  </div>;
}
