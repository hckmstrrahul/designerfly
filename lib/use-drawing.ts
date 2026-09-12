import { useEffect, useRef, useState } from 'react';
import type { CircuitModel, CircuitView, NeuralFrame } from './circuit';
import { createFlyScene, type LiveDrawing } from './fly-scene';
import { physics, type PhysicsFrame, type PhysicsReport } from './physics';
import { drawingStroke, type PlacedShape } from './composition';
import { CAMERA_PRESETS, CAMERA_STORAGE_KEY, savedCameraPreset } from './camera-presets';
import { stepsAtSpeed } from './simulation-clock';
import { PlaybackBuffer } from './playback-buffer';

export function useDrawing() {
  const [model, setModel] = useState<CircuitModel | null>(null), [report, setReport] = useState<PhysicsReport | null>(null);
  const [motorModel, setMotorModel] = useState<CircuitView | null>(null);
  const [sceneReady, setSceneReady] = useState(false), [error, setError] = useState('');
  const [neuralSource, setNeuralSource] = useState<'motor' | 'wing' | 'spiking'>('motor');
  const [controller,setController]=useState<'trained'|'spiking'>('trained');
  const controllerRef=useRef<'trained'|'spiking'>('trained');
  const selectedSource = useRef<'motor' | 'wing' | 'spiking'>('motor');
  const motorFrame = useRef<NeuralFrame | null>(null), wingFrame = useRef<NeuralFrame | null>(null);
  const [shape, setShape] = useState<number | null>(null), [phase, setPhase] = useState('loading');
  const [progress, setProgress] = useState(0), [completed, setCompleted] = useState(0), [wings, setWings] = useState(false), [contact, setContact] = useState(false);
  const host = useRef<HTMLDivElement>(null);
  const [cameraPreset,setCameraPreset] = useState(savedCameraPreset);
  const live = useRef<LiveDrawing>({ frame: null, drawing: false, run: 0, physical: null, ink: [], wings: false, wing: 0, resetView: 0, cameraPreset });
  const session = useRef(''), active = useRef(false), alive = useRef(false), selection = useRef<(i: number) => void>(() => {});
  const sequence = useRef(0);
  const [speed, setSpeed] = useState(1), speedRef = useRef(1);
  const [strokeCount, setStrokeCount] = useState(1), [strokeIndex, setStrokeIndex] = useState(0);
  const [isComposition, setIsComposition] = useState(false);
  const ready = !!model && !!report && sceneReady && !error && phase!=='resetting';
  const publishNeuralFrame = () => { live.current.frame = selectedSource.current === 'wing' ? wingFrame.current : motorFrame.current; };
  const selectNeuralSource = (source: 'motor' | 'wing' | 'spiking') => { selectedSource.current = source; setNeuralSource(source); publishNeuralFrame(); };
  async function resetSimulation() {
    const run = ++live.current.run;
    active.current = false; live.current.drawing = false; live.current.ink.length = 0;
    live.current.wings = false; live.current.wing = 0; live.current.resetView++;
    motorFrame.current = null; wingFrame.current = null; selectNeuralSource(controllerRef.current==='spiking'?'spiking':'motor');
    setWings(false); setShape(null); setProgress(0); setContact(false); setPhase('resetting');
    setIsComposition(false); setStrokeCount(1); setStrokeIndex(0);
    const old = session.current; session.current = '';
    try {
      if (old) await physics(`/session/${old}`, undefined, 'DELETE');
      const initial = await physics<{ session: string; frame: PhysicsFrame }>('/session', { shape: 0, controller:controllerRef.current });
      if (!alive.current || run !== live.current.run) { void physics(`/session/${initial.session}`, undefined, 'DELETE').catch(() => {}); return; }
      session.current = initial.session; live.current.physical = initial.frame; setPhase('ready');
    } catch { if (alive.current && run === live.current.run) setError('Physics disconnected. Run npm run physics and reload.'); }
  }
  async function draw(i: number, composition?: PlacedShape[]) {
    if (!ready) return;
    if (!composition && shape === i && !isComposition) { await resetSimulation(); return; }
    const run = ++live.current.run; active.current = false; live.current.ink.length = 0; live.current.drawing = false;
    motorFrame.current = null;
    if (!live.current.wings) selectNeuralSource(controllerRef.current==='spiking'?'spiking':'motor');
    else publishNeuralFrame();
    const old = session.current; session.current = '';
    setShape(i); setPhase('approach'); setProgress(0); setContact(false);
    setStrokeCount(composition?.length || 1); setStrokeIndex(0);
    setIsComposition(!!composition);
    try {
      if (old) await physics(`/session/${old}`, undefined, 'DELETE');
      const next = await physics<{ session: string; frame: PhysicsFrame }>(composition ? '/composition' : '/session', composition ? { controller:controllerRef.current, strokes: composition.map(drawingStroke).map(({ shape, x, y, width, height, points }) => ({ shape, x, y, width, height, points })) } : { shape: i, controller:controllerRef.current });
      if (!alive.current || run !== live.current.run) { void physics(`/session/${next.session}`, undefined, 'DELETE').catch(() => {}); return; }
      session.current = next.session; live.current.physical = next.frame; active.current = true;
    } catch { if (alive.current && run === live.current.run) setError('Physics disconnected. Run npm run physics and reload.'); }
  }
  useEffect(() => { selection.current = draw; });
  useEffect(() => {
    let mounted = true; let dispose: (() => void) | undefined;
    try { dispose = createFlyScene(host.current!, live.current, () => { if (mounted) setSceneReady(true); }, e => { if (mounted) setError(e); }); } catch (e) { queueMicrotask(() => { if (mounted) setError(String(e)); }); }
    return () => { mounted = false; dispose?.(); };
  }, []);
  useEffect(() => {
    alive.current = true; let disposed = false, timer = 0;
    type Sample = { duration: number; frames: PhysicsFrame[]; state: number[]; wing: number; wing_state: number[] | null; sample_time: number; neural_source: 'motor' | 'spiking'; wing_time: number; wing_phase: number };
    const buffer = new PlaybackBuffer<Sample>();
    let bufferKey = '', pending: object | null = null, requestedWingTime = 0, lastTick = performance.now(), started = false, exhausted = false;
    Promise.all([fetch('/models/circuit-refined.json').then(r => { if (!r.ok) throw new Error('Model unavailable'); return r.json(); }), physics<PhysicsReport>('/health')]).then(async ([network, health]) => {
      if (disposed) return;
      setModel(network);
      if (health.motor_model) {
        const response = await fetch(health.motor_model); if (!response.ok) throw new Error('Motor graph unavailable');
        const graph = await response.json(); if (disposed) return; setMotorModel(graph);
      }
      const initial = await physics<{ session: string; frame: PhysicsFrame }>('/session', { shape: 0, controller:controllerRef.current });
      if (disposed) { void physics(`/session/${initial.session}`, undefined, 'DELETE').catch(() => {}); return; }
      session.current = initial.session; live.current.physical = initial.frame; setReport(health); setPhase('ready');
    }).catch(() => { if (!disposed) setError(location.hostname==='localhost'||location.hostname==='127.0.0.1'?'Start the local physics service with npm run physics, then reload.':'The drawing service is currently unavailable. Please try again shortly.'); });
    const tick = () => {
      const now = performance.now(), elapsed = Math.min(.08, (now - lastTick) / 1000);
      lastTick = now;
      const run = live.current.run;
      const drawing = active.current && !!session.current;
      const key = `${run}:${drawing ? session.current : `wing:${live.current.wings}`}`;
      if (key !== bufferKey) { bufferKey = key; buffer.clear(); pending = null; started = false; exhausted = false; }
      if (!document.hidden && (drawing || live.current.wings)) {
        // Prefetch independently of playback; only one request per run is in flight.
        if (!pending && !exhausted && buffer.seconds < .6 * speedRef.current) {
          const token = {}; pending = token;
          const steps = stepsAtSpeed(speedRef.current), count = started ? 20 : 4; started = true;
          const wingStart = requestedWingTime;
          requestedWingTime += count * steps * .02;
          void physics<{ samples: Sample[] }>('/playback', { session: drawing ? session.current : null, steps, count, wings: live.current.wings, wing_time: wingStart }).then(result => {
            if (!disposed && run === live.current.run && key === bufferKey) {
              buffer.push(result.samples);
              exhausted = !!result.samples.at(-1)?.frames.at(-1)?.done;
            }
          }).catch(() => {
            if (!disposed && run === live.current.run && key === bufferKey) {
              active.current = false; live.current.drawing = false;
              setError('The drawing service disconnected. Please reload and try again.');
            }
          }).finally(() => { if (pending === token) pending = null; });
        }
        for (const result of buffer.take(elapsed * speedRef.current)) {
          const f = result.frames.at(-1);
          if (drawing && f) {
            live.current.physical = f; live.current.ink.push(...result.frames);
            motorFrame.current = { point: f.point as [number, number], state: new Float32Array(result.state), phase: f.phase || 0, run, source: result.neural_source, time: result.sample_time, sequence: ++sequence.current };
            live.current.drawing = !!f.drawing; setContact(f.contact); setProgress(f.phase || 0);
            setPhase(f.done ? 'done' : f.stage ? f.stage : f.time < 1.2 ? 'approach' : 'drawing');
            if (f.shape !== undefined) setShape(f.shape);
            if (f.stroke_index !== undefined) setStrokeIndex(f.stroke_index);
            if (f.done) { active.current = false; live.current.drawing = false; setCompleted(n => n + 1); }
          }
          if (live.current.wings && result.wing_state) {
            live.current.wing = result.wing;
            wingFrame.current = { point: [0, 0], state: new Float32Array(result.wing_state), phase: result.wing_phase, run, source: 'wing', time: result.wing_time, sequence: ++sequence.current };
          }
          publishNeuralFrame();
        }
      }
      if (!disposed) timer = window.setTimeout(tick, 16);
    };
    timer = window.setTimeout(tick, 40);
    const keydown = (e: KeyboardEvent) => {
      if (e.repeat || e.metaKey || e.ctrlKey || e.altKey || (e.target instanceof HTMLElement && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName))) return;
      const i = ['1', '2', '3'].indexOf(e.key); if (i >= 0) { e.preventDefault(); selection.current(i); }
    };
    window.addEventListener('keydown', keydown);
    return () => { disposed = true; alive.current = false; clearTimeout(timer); window.removeEventListener('keydown', keydown); active.current = false; const id = session.current; session.current = ''; if (id) void physics(`/session/${id}`, undefined, 'DELETE').catch(() => {}); };
  }, []);
  function toggleWings() {
    live.current.wings = !live.current.wings; setWings(live.current.wings);
    if (live.current.wings) wingFrame.current = null;
    selectNeuralSource(live.current.wings ? 'wing' : controllerRef.current==='spiking'?'spiking':'motor');
  }
  async function selectController(next:'trained'|'spiking') {
    if(active.current || !ready || (next==='spiking' && !report?.spiking?.available))return;
    controllerRef.current=next;setController(next);
    await resetSimulation();
  }
  function resetView() { live.current.resetView++; }
  function cycleCamera() {
    const next=(live.current.cameraPreset+1)%CAMERA_PRESETS.length;
    live.current.cameraPreset=next;live.current.resetView++;setCameraPreset(next);
    try{localStorage.setItem(CAMERA_STORAGE_KEY,String(next));}catch{/* Storage can be unavailable in private sessions. */}
  }
  function cycleSpeed() { speedRef.current = speedRef.current === 1 ? 3 : speedRef.current === 3 ? 6 : 1; setSpeed(speedRef.current); }
  return { controller, selectController, model: neuralSource !== 'wing' && motorModel ? motorModel : model, report, error, shape, phase, progress, completed, host, live, ready, draw, wings, toggleWings, contact, resetView, neuralSource, selectNeuralSource, strokeCount, strokeIndex, isComposition, speed, cycleSpeed, cameraPreset, cycleCamera };
}
