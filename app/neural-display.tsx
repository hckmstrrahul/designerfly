import { useEffect, useMemo, useRef, useState, type RefObject } from 'react';
import type { CircuitView } from '@/lib/circuit';
import type { LiveDrawing } from '@/lib/fly-scene';
import { activityTrace, recordActivity, type NeuralSource } from '@/lib/neural-telemetry';
import { activityColor, activityChange, CELL_COLORS } from '@/lib/neural-colors';
type Anatomy = { cells: { bodyId: string; neuron: number; points: number[][]; edges: [number, number][] }[] };
type Camera = { yaw: number; pitch: number; zoom: number; x: number; y: number };
const home = (mode: 'activity' | 'anatomy' | 'spectrum'): Camera => ({ yaw: mode === 'spectrum' ? 0 : .38, pitch: mode === 'spectrum' ? 0 : .12, zoom: mode === 'activity' ? 1.16 * .8 * 1.1 : mode === 'spectrum' ? .96 : 1, x: 0, y: 0 });

export function NeuralDisplay({ model, live, source, mode }: { model: CircuitView; live: RefObject<LiveDrawing>; source: NeuralSource; mode: 'activity' | 'anatomy' | 'spectrum' }) {
  const traceRef = useRef<HTMLCanvasElement>(null);
  const ref = useRef<HTMLCanvasElement>(null), camera = useRef(home(mode));
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
    if (mode === 'activity' || anatomy) return;
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
        camera.current.zoom = Math.max(.15, Math.min(12, camera.current.zoom * Math.pow(after / Math.max(1, before), 2.5)));
        camera.current.x += dx / 2; camera.current.y += dy / 2;
      } else if (e.buttons === 2 || e.shiftKey) { camera.current.x += dx; camera.current.y += dy; }
      else { camera.current.yaw += dx * .008; camera.current.pitch = Math.max(-1.5, Math.min(1.5, camera.current.pitch + dy * .008)); }
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    };
    const up = (e: PointerEvent) => { pointers.delete(e.pointerId); };
    const wheel = (e: WheelEvent) => {
      e.preventDefault();
      const pixels = e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? canvas.clientHeight : 1);
      camera.current.zoom = Math.max(.15, Math.min(12, camera.current.zoom * Math.exp(-pixels * .0045 * (e.ctrlKey ? 3 : 1))));
    };
    const reset = () => { camera.current = home(mode); }, context = (e: Event) => e.preventDefault();
    const key = (e: KeyboardEvent) => {
      if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-', '0', 'Home'].includes(e.key)) return;
      e.preventDefault();
      if (e.key === 'Home' || e.key === '0') reset();
      else if (e.key === '+' || e.key === '=') camera.current.zoom = Math.min(12, camera.current.zoom * 1.25);
      else if (e.key === '-') camera.current.zoom = Math.max(.15, camera.current.zoom / 1.25);
      else if (e.shiftKey) { camera.current.x += e.key === 'ArrowLeft' ? -10 : e.key === 'ArrowRight' ? 10 : 0; camera.current.y += e.key === 'ArrowUp' ? -10 : e.key === 'ArrowDown' ? 10 : 0; }
      else { camera.current.yaw += e.key === 'ArrowLeft' ? -.1 : e.key === 'ArrowRight' ? .1 : 0; camera.current.pitch = Math.max(-1.5, Math.min(1.5, camera.current.pitch + (e.key === 'ArrowUp' ? -.1 : e.key === 'ArrowDown' ? .1 : 0))); }
    };
    canvas.addEventListener('pointerdown', down); canvas.addEventListener('pointermove', move); canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', up); canvas.addEventListener('lostpointercapture', up);
    canvas.addEventListener('wheel', wheel, { passive: false }); canvas.addEventListener('dblclick', reset); canvas.addEventListener('contextmenu', context); canvas.addEventListener('keydown', key);
    return () => { canvas.removeEventListener('pointerdown', down); canvas.removeEventListener('pointermove', move); canvas.removeEventListener('pointerup', up); canvas.removeEventListener('pointercancel', up); canvas.removeEventListener('lostpointercapture', up); canvas.removeEventListener('wheel', wheel); canvas.removeEventListener('dblclick', reset); canvas.removeEventListener('contextmenu', context); canvas.removeEventListener('keydown', key); };
  }, [mode]);
  useEffect(() => {
    const canvas = ref.current!, ctx = canvas.getContext('2d')!;
    const positions = mode !== 'activity' && anatomy ? anatomyPoints : model.positions;
    const bounds = [0, 1, 2].map(axis => {
      let lo = Infinity, hi = -Infinity;
      for (const p of positions) if (p) { lo = Math.min(lo, p[axis]); hi = Math.max(hi, p[axis]); }
      return { center: (lo + hi) / 2, range: Math.max(1, hi - lo) };
    });
    let animation = 0, cachedView = '';
    // Reuse small feathered sprites instead of blurring thousands of dots per frame.
    const glows = new Map<number, HTMLCanvasElement>();
    const glowSprite = (value: number) => {
      const key = Math.sign(value);
      let sprite = glows.get(key);
      if (!sprite) {
        sprite = document.createElement('canvas'); sprite.width = sprite.height = 48;
        const brush = sprite.getContext('2d')!, color = activityColor(key);
        const gradient = brush.createRadialGradient(24, 24, 0, 24, 24, 24);
        gradient.addColorStop(0, color.replace('rgb(', 'rgba(').replace(')', ',.8)'));
        gradient.addColorStop(.18, color.replace('rgb(', 'rgba(').replace(')', ',.45)'));
        gradient.addColorStop(.48, color.replace('rgb(', 'rgba(').replace(')', ',.12)'));
        gradient.addColorStop(1, color.replace('rgb(', 'rgba(').replace(')', ',0)'));
        brush.fillStyle = gradient; brush.fillRect(0, 0, 48, 48); glows.set(key, sprite);
      }
      return sprite;
    };
    let projected: (number[] | null)[] = [], paths: { neuron: number; path: Path2D }[] = [];
    const trace = historyRef.current;
    const draw = () => {
      animation = requestAnimationFrame(draw);
      const w = canvas.clientWidth, h = canvas.clientHeight, dpr = Math.min(devicePixelRatio, 2), plotHeight = h;
      if (!w || !h) return;
      if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
      const frame = live.current.frame;
      if (mode !== 'anatomy' && frame?.source === source && frame.time !== undefined && frame.sequence !== undefined) {
        const sameStream = trace.source === frame.source && trace.run === frame.run;
        if (recordActivity(trace, { ...frame, source: frame.source, time: frame.time, sequence: frame.sequence }, model.neurons)) {
          const previous = sameStream && feedback.current.state?.length === model.neurons ? feedback.current.state : null;
          feedback.current.change = Float32Array.from(frame.state, (v, i) => previous ? activityChange(v, previous[i]) : 0);
          feedback.current.state = frame.state;
        }
      }
      const state = trace.source === source && frame && feedback.current.state?.length === model.neurons ? feedback.current.state : null;
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
        if (mode !== 'activity' && anatomy) {
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
      if (mode !== 'activity' && anatomy) {
        ctx.lineWidth = .7; ctx.globalAlpha = .62;
        for (const { neuron, path } of paths) {
          if (mode === 'spectrum') {
            const strength = Math.sqrt(Math.min(1, Math.abs(state?.[neuron] || 0)));
            const hue = Number(model.bodyIds[neuron].slice(-9)) * 137.508 % 360;
            ctx.strokeStyle = `hsl(${hue}, 82%, 68%)`;
            ctx.globalAlpha = strength * .12; ctx.lineWidth = 2.8; ctx.stroke(path);
            ctx.globalAlpha = .16 + strength * .8; ctx.lineWidth = .55 + strength * .65; ctx.stroke(path);
          } else { ctx.strokeStyle = CELL_COLORS[model.nodeClasses[neuron]] || '#9ea99f'; ctx.stroke(path); }
        }
        ctx.globalAlpha = 1;
      } else if (mode !== 'activity') {
        ctx.fillStyle = '#b3c39b'; ctx.font = '11px "Departure Mono", monospace'; ctx.fillText(anatomyError ? 'Anatomy unavailable' : 'Loading anatomy…', 18, plotHeight / 2);
      } else {
        ctx.lineWidth = .5;
        for (let e = 0; e < model.edges; e += Math.max(23, Math.ceil(model.edges / 1800))) {
          const a = projected[model.col[e]], b = projected[model.rows[e]]; if (!a || !b) continue;
          ctx.strokeStyle = '#a2bdba09'; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
        }
        // Anatomy stays visible even when the controller is quiet or has no sample yet.
        // This neutral base is separate from the data-driven color and glow layers.
        ctx.globalAlpha = .20;
        ctx.fillStyle = '#c1d2a4';
        ctx.beginPath();
        for (const p of projected) {
          if (!p) continue;
          ctx.moveTo(p[0] + 1.35, p[1]);
          ctx.arc(p[0], p[1], 1.35, 0, Math.PI * 2);
        }
        ctx.fill(); ctx.globalAlpha = 1;
        projected.forEach((p, i) => {
          if (!p) return;
          const value = state?.[i] || 0, change = state ? feedback.current.change[i] : 0;
          const strength = Math.sqrt(Math.abs(value)), changing = Math.sqrt(change);
          const glow = Math.min(.6, strength * .35 + changing * .4);
          if (glow > .035) {
            const radius = 3 + strength * 3 + changing * 3;
            ctx.globalAlpha = glow;
            ctx.drawImage(glowSprite(value), p[0] - radius, p[1] - radius, radius * 2, radius * 2);
          }
          ctx.globalAlpha = Math.min(1, strength + changing * .25);
          ctx.fillStyle = activityColor(value);
          ctx.beginPath(); ctx.arc(p[0], p[1], 1.35 + strength * 1.1, 0, Math.PI * 2); ctx.fill();
          ctx.globalAlpha = 1;
        });
      }
      ctx.restore();
      if (mode !== 'activity') return;
      const traceCanvas = traceRef.current;
      if (!traceCanvas) return;
      const tw = traceCanvas.clientWidth, th = traceCanvas.clientHeight;
      if (!tw || !th) return;
      if (traceCanvas.width !== Math.round(tw * dpr) || traceCanvas.height !== Math.round(th * dpr)) { traceCanvas.width = Math.round(tw * dpr); traceCanvas.height = Math.round(th * dpr); }
      const traceCtx = traceCanvas.getContext('2d')!;
      traceCtx.setTransform(dpr, 0, 0, dpr, 0, 0); traceCtx.clearRect(0, 0, tw, th);
      const history = trace.source === source && frame ? trace.samples : [];
      const lo = Math.max(0, Math.min(...history.map(s => s.mean), 1) - .005), hi = Math.min(1, Math.max(...history.map(s => s.mean), 0) + .005);
      const start = history[0]?.time || 0, duration = Math.max(1, (history.at(-1)?.time || start) - start);
      traceCtx.font = '9px "Departure Mono", monospace'; traceCtx.fillStyle = '#929b96';
      traceCtx.fillText(history.length ? `${lo.toFixed(3)}–${hi.toFixed(3)}` : 'No samples yet', 16, 32);
      traceCtx.textAlign = 'right'; traceCtx.fillText(history.length ? `${duration.toFixed(1)}s` : '—', tw - 16, 32); traceCtx.textAlign = 'left';
      const baseline = th - 14, amplitude = Math.max(12, th - 56);
      traceCtx.strokeStyle = history.length ? '#efbd79' : '#555b58'; traceCtx.lineWidth = 1.25; traceCtx.beginPath();
      if (!history.length) { traceCtx.moveTo(16, baseline - amplitude / 2); traceCtx.lineTo(tw - 16, baseline - amplitude / 2); }
      history.forEach((sample, i) => {
        const x = 16 + (sample.time - start) / duration * (tw - 32), y = baseline - (sample.mean - lo) / Math.max(.01, hi - lo) * amplitude;
        if (i === 0) traceCtx.moveTo(x, y); else traceCtx.lineTo(x, y);
        if (history.length === 1) { traceCtx.moveTo(x - 1, y); traceCtx.lineTo(x + 1, y); }
      }); traceCtx.stroke();

    };
    animation = requestAnimationFrame(draw); return () => cancelAnimationFrame(animation);
  }, [model, live, source, mode, anatomy, anatomyPoints, anatomyError]);
  return <>
    {/* oxlint-disable-next-line jsx-a11y/prefer-tag-over-role */}
    <canvas ref={ref} className="neural-canvas" tabIndex={0} role="img" aria-label={`${source} ${mode} interactive 3D view. ${mode === 'activity' ? 'Computed signed rates: red negative, dark green zero, green positive. Soft glow shows activity strength and changes between received samples.' : mode === 'spectrum' ? 'Measured 3D skeletons: rainbow hue identifies each neuron, brightness shows its computed rate magnitude. No branch signal propagation is modeled.' : 'Measured neuron skeletons: sensory cyan, local circuit purple, motor gold.'} Drag or arrow keys rotate; scroll or plus/minus zoom; Shift-drag or Shift-arrows pan; double-click or Home resets.`} />
    {mode === 'activity' && <canvas ref={traceRef} className="neural-trace" aria-label="Mean absolute activity across all controller neurons" />}
    <div className="neural-legend">{mode === 'activity' ? <><div className="rate-legend-title" title="This scale maps each neuron’s signed model value to color; it is separate from the average activity graph.">Neuron color scale</div><div className="rate-legend"><span>−1</span><i /><span>+1</span></div></> : mode === 'spectrum' ? <div className="spectrum-legend"><div title="Each hue identifies one of the 96 measured neurons"><span className="spectrum-swatches" aria-hidden="true">{['#ff718a','#da7aff','#77aaff','#70e7bb','#e3e87a'].map(color => <i key={color} style={{ background: color }} />)}</span><span>Neuron identity</span></div><div title="Brightness follows the neuron’s actual computed activity magnitude"><span className="strength-swatches" aria-hidden="true">{[.2,.4,.6,.8,1].map(opacity => <i key={opacity} style={{ opacity }} />)}</span><span>Activity strength</span></div></div> : <div className="cell-legend">{[['vnc_sensory', 'Sensory'], ['vnc_intrinsic', 'Local circuit'], ['vnc_motor', 'Motor']].map(([type, label]) => <span key={type}><i style={{ background: CELL_COLORS[type] }} />{label}</span>)}</div>}</div>
  </>;
}
