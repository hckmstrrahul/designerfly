import { useEffect, useMemo, useRef, useState, type RefObject } from 'react';
import type { CircuitView } from '@/lib/circuit';
import type { LiveDrawing } from '@/lib/fly-scene';
import { activityTrace, recordActivity, type NeuralSource } from '@/lib/neural-telemetry';
import { activityColor, activityChange, CELL_COLORS } from '@/lib/neural-colors';
type Anatomy = { cells: { bodyId: string; neuron: number; points: number[][]; edges: [number, number][] }[] };
type Camera = { yaw: number; pitch: number; zoom: number; x: number; y: number };
const home = (): Camera => ({ yaw: .38, pitch: .12, zoom: 1, x: 0, y: 0 });

export function NeuralDisplay({ model, live, source, mode }: { model: CircuitView; live: RefObject<LiveDrawing>; source: NeuralSource; mode: 'activity' | 'anatomy' }) {
  const ref = useRef<HTMLCanvasElement>(null), camera = useRef(home());
  const [anatomyData, setAnatomy] = useState<Anatomy | null>(null), [anatomyError, setAnatomyError] = useState(false);
  const anatomy = useMemo(() => {
    if (!anatomyData) return null;
    const index = new Map(model.bodyIds.map((id, i) => [String(id), i]));
    return { cells: anatomyData.cells.filter(c => index.has(c.bodyId)).map(c => ({ ...c, neuron: index.get(c.bodyId)! })) };
  }, [anatomyData, model]);
  const historyRef = useRef(activityTrace());
  const feedback = useRef({ state: null as Float32Array | null, change: new Float32Array(model.neurons) });
  const anatomyPoints = useMemo(() => anatomy?.cells.flatMap(c => c.points) || [], [anatomy]);
  useEffect(() => {
    if (mode !== 'anatomy' || anatomy) return;
    const controller = new AbortController();
    fetch('/models/neural-anatomy.json', { signal: controller.signal }).then(r => { if (!r.ok) throw new Error('Anatomy unavailable'); return r.json(); }).then((data: Anatomy) => {
      if (!data.cells.every(c => model.bodyIds.includes(c.bodyId))) throw new Error('Anatomy identity mismatch');
      setAnatomy(data);
    }).catch(() => { if (!controller.signal.aborted) setAnatomyError(true); });
    return () => controller.abort();
  }, [mode, anatomy, model]);
  useEffect(() => {
    const canvas = ref.current!, pointers = new Map<number, { x: number; y: number }>();
    const down = (e: PointerEvent) => { canvas.setPointerCapture(e.pointerId); pointers.set(e.pointerId, { x: e.clientX, y: e.clientY }); };
    const move = (e: PointerEvent) => {
      const previous = pointers.get(e.pointerId); if (!previous) return;
      const dx = e.clientX - previous.x, dy = e.clientY - previous.y, other = [...pointers.entries()].find(([id]) => id !== e.pointerId)?.[1];
      if (other) {
        const before = Math.hypot(previous.x - other.x, previous.y - other.y), after = Math.hypot(e.clientX - other.x, e.clientY - other.y);
        camera.current.zoom = Math.max(.4, Math.min(5, camera.current.zoom * after / Math.max(1, before)));
        camera.current.x += dx / 2; camera.current.y += dy / 2;
      } else if (e.buttons === 2 || e.shiftKey) { camera.current.x += dx; camera.current.y += dy; }
      else { camera.current.yaw += dx * .008; camera.current.pitch = Math.max(-1.5, Math.min(1.5, camera.current.pitch + dy * .008)); }
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    };
    const up = (e: PointerEvent) => { pointers.delete(e.pointerId); };
    const wheel = (e: WheelEvent) => { e.preventDefault(); camera.current.zoom = Math.max(.4, Math.min(5, camera.current.zoom * Math.exp(-e.deltaY * .0015))); };
    const reset = () => { camera.current = home(); }, context = (e: Event) => e.preventDefault();
    const key = (e: KeyboardEvent) => {
      if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-', '0', 'Home'].includes(e.key)) return;
      e.preventDefault();
      if (e.key === 'Home' || e.key === '0') reset();
      else if (e.key === '+' || e.key === '=') camera.current.zoom = Math.min(5, camera.current.zoom * 1.1);
      else if (e.key === '-') camera.current.zoom = Math.max(.4, camera.current.zoom / 1.1);
      else if (e.shiftKey) { camera.current.x += e.key === 'ArrowLeft' ? -10 : e.key === 'ArrowRight' ? 10 : 0; camera.current.y += e.key === 'ArrowUp' ? -10 : e.key === 'ArrowDown' ? 10 : 0; }
      else { camera.current.yaw += e.key === 'ArrowLeft' ? -.1 : e.key === 'ArrowRight' ? .1 : 0; camera.current.pitch = Math.max(-1.5, Math.min(1.5, camera.current.pitch + (e.key === 'ArrowUp' ? -.1 : e.key === 'ArrowDown' ? .1 : 0))); }
    };
    canvas.addEventListener('pointerdown', down); canvas.addEventListener('pointermove', move); canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', up); canvas.addEventListener('lostpointercapture', up);
    canvas.addEventListener('wheel', wheel, { passive: false }); canvas.addEventListener('dblclick', reset); canvas.addEventListener('contextmenu', context); canvas.addEventListener('keydown', key);
    return () => { canvas.removeEventListener('pointerdown', down); canvas.removeEventListener('pointermove', move); canvas.removeEventListener('pointerup', up); canvas.removeEventListener('pointercancel', up); canvas.removeEventListener('lostpointercapture', up); canvas.removeEventListener('wheel', wheel); canvas.removeEventListener('dblclick', reset); canvas.removeEventListener('contextmenu', context); canvas.removeEventListener('keydown', key); };
  }, []);
  useEffect(() => {
    const canvas = ref.current!, ctx = canvas.getContext('2d')!;
    const positions = mode === 'anatomy' && anatomy ? anatomyPoints : model.positions;
    const bounds = [0, 1, 2].map(axis => {
      let lo = Infinity, hi = -Infinity;
      for (const p of positions) if (p) { lo = Math.min(lo, p[axis]); hi = Math.max(hi, p[axis]); }
      return { center: (lo + hi) / 2, range: Math.max(1, hi - lo) };
    });
    let animation = 0, cachedView = '';
    let projected: (number[] | null)[] = [], paths: { neuron: number; path: Path2D }[] = [];
    const trace = historyRef.current;
    const draw = () => {
      animation = requestAnimationFrame(draw);
      const w = canvas.clientWidth, h = canvas.clientHeight, dpr = Math.min(devicePixelRatio, 2), plotHeight = h - 82;
      if (!w || !h) return;
      if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
      const frame = live.current.frame;
      if (frame?.source && frame.time !== undefined && frame.sequence !== undefined) {
        const sameStream = trace.source === frame.source && trace.run === frame.run;
        if (recordActivity(trace, { ...frame, source: frame.source, time: frame.time, sequence: frame.sequence }, model.neurons)) {
          const previous = sameStream && feedback.current.state?.length === model.neurons ? feedback.current.state : null;
          feedback.current.change = Float32Array.from(frame.state, (v, i) => previous ? activityChange(v, previous[i]) : 0);
          feedback.current.state = frame.state;
        }
      }
      const state = feedback.current.state?.length === model.neurons ? feedback.current.state : null;
      canvas.dataset.sequence = String(trace.sequence); canvas.dataset.source = trace.source || 'none';
      canvas.dataset.meanRate = String(trace.samples.at(-1)?.mean ?? '');
      canvas.dataset.sampleTime = String(trace.samples.at(-1)?.time ?? '');
      const cam = camera.current, key = `${w}:${h}:${cam.yaw}:${cam.pitch}:${cam.zoom}:${cam.x}:${cam.y}`;
      canvas.dataset.view = key;
      if (key !== cachedView) {
        cachedView = key;
        const scale = Math.min((w - 36) / Math.hypot(bounds[0].range, bounds[1].range), (plotHeight - 30) / bounds[2].range) * cam.zoom;
        projected = positions.map(p => {
          if (!p) return null;
          const x = p[0] - bounds[0].center, y = p[1] - bounds[1].center, z = p[2] - bounds[2].center;
          const horizontal = x * Math.cos(cam.yaw) - y * Math.sin(cam.yaw), depth = x * Math.sin(cam.yaw) + y * Math.cos(cam.yaw);
          return [w / 2 + horizontal * scale + cam.x, plotHeight / 2 + (z * Math.cos(cam.pitch) - depth * Math.sin(cam.pitch)) * scale + cam.y];
        });
        if (mode === 'anatomy' && anatomy) {
          let offset = 0;
          paths = anatomy.cells.map(c => {
            const path = new Path2D();
            for (const [from, to] of c.edges) { const a = projected[offset + from]!, b = projected[offset + to]!; path.moveTo(a[0], a[1]); path.lineTo(b[0], b[1]); }
            offset += c.points.length; return { neuron: c.neuron, path };
          });
        }
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h);
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, w, plotHeight); ctx.clip();
      ctx.strokeStyle = '#aabc8c09'; ctx.lineWidth = 1;
      for (let x = 12; x < w; x += 24) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, plotHeight); ctx.stroke(); }
      for (let y = 12; y < plotHeight; y += 24) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
      if (mode === 'anatomy' && anatomy) {
        ctx.lineWidth = .7; ctx.globalAlpha = .62;
        for (const { neuron, path } of paths) { ctx.strokeStyle = CELL_COLORS[model.nodeClasses[neuron]] || '#9ea99f'; ctx.stroke(path); }
        ctx.globalAlpha = 1;
      } else if (mode === 'anatomy') {
        ctx.fillStyle = '#b3c39b'; ctx.font = '11px "Departure Mono", monospace'; ctx.fillText(anatomyError ? 'Anatomy unavailable' : 'Loading anatomy…', 18, plotHeight / 2);
      } else {
        ctx.lineWidth = .5;
        for (let e = 0; e < model.edges; e += Math.max(23, Math.ceil(model.edges / 1800))) {
          const a = projected[model.col[e]], b = projected[model.rows[e]]; if (!a || !b) continue;
          ctx.strokeStyle = '#a2bdba15'; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
        }
        projected.forEach((p, i) => {
          if (!p) return;
          const value = state?.[i] || 0, change = state ? feedback.current.change[i] : 0;
          ctx.fillStyle = state ? activityColor(value) : '#697e77';
          ctx.beginPath(); ctx.arc(p[0], p[1], 1.25 + Math.abs(value) * 1.5, 0, Math.PI * 2); ctx.fill();
          if (change > .005) { ctx.strokeStyle = `rgba(244,231,183,${Math.min(.9, change)})`; ctx.lineWidth = .8; ctx.beginPath(); ctx.arc(p[0], p[1], 2.4 + change * 4, 0, Math.PI * 2); ctx.stroke(); }
        });
      }
      ctx.restore();
      const history = trace.samples;
      const lo = Math.max(0, Math.min(...history.map(s => s.mean), 1) - .005), hi = Math.min(1, Math.max(...history.map(s => s.mean), 0) + .005);
      const start = history[0]?.time || 0, duration = Math.max(1, (history.at(-1)?.time || start) - start);
      ctx.strokeStyle = '#efbd79'; ctx.lineWidth = 1.25; ctx.beginPath();
      history.forEach((s, i) => { const x = 16 + (s.time - start) / duration * (w - 32), y = h - 24 - (s.mean - lo) / Math.max(.01, hi - lo) * 28; if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); }); ctx.stroke();
      ctx.fillStyle = '#b2c3b8'; ctx.font = '10px "Departure Mono", monospace'; ctx.fillText(history.length ? 'Mean strength · all neurons' : 'Choose a shape to see activity', 16, h - 7);
      if (history.length) { ctx.fillText(`${lo.toFixed(3)}–${hi.toFixed(3)}`, 16, h - 58); ctx.textAlign = 'right'; ctx.fillText(`${duration.toFixed(1)}s`, w - 16, h - 58); ctx.textAlign = 'left'; }
    };
    animation = requestAnimationFrame(draw); return () => cancelAnimationFrame(animation);
  }, [model, live, mode, anatomy, anatomyPoints, anatomyError]);
  return <>
    <div className="neural-view-label">{mode === 'activity' ? `Activity · ${model.positions.filter(Boolean).length} located cells` : `Anatomy · ${anatomy ? anatomy.cells.length : '…'} traced cells`}<span>Ventral nerve cord subset</span></div>
    {/* oxlint-disable-next-line jsx-a11y/prefer-tag-over-role */}
    <canvas ref={ref} className="neural-canvas" tabIndex={0} role="img" aria-label={`${source} ${mode} interactive 3D view. ${mode === 'activity' ? 'Computed signed rates: blue negative, gray zero, coral positive. Rings show change between received samples.' : 'Measured neuron skeletons: sensory cyan, local circuit purple, motor gold.'} Drag or arrow keys rotate; scroll or plus/minus zoom; Shift-drag or Shift-arrows pan; double-click or Home resets.`} />
    <div className="neural-legend">{mode === 'activity' ? <><div className="rate-legend"><span>−1</span><i /><span>+1</span></div><div className="legend-description"><span>Signed activity · center 0</span><span>◯ Change ×8</span></div></> : <div className="cell-legend">{[['vnc_sensory', 'Sensory'], ['vnc_intrinsic', 'Local circuit'], ['vnc_motor', 'Motor']].map(([type, label]) => <span key={type}><i style={{ background: CELL_COLORS[type] }} />{label}</span>)}</div>}</div>
    <div className="neural-gesture-hint" title="Right-drag or Shift-drag to pan. Double-click to reset. Touch: drag to rotate, pinch to zoom.">Drag to rotate · Scroll to zoom · Double-click resets</div>
  </>;
}
