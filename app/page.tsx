import { Circle, RectangleHorizontal, Triangle, Wind, LayoutTemplate, Activity, GitBranch, Gauge } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useDrawing } from '@/lib/use-drawing';
import { NeuralDisplay } from './neural-display';
import { CompositionEditor } from './composition-editor';
import { INITIAL_STUDY, MAX_SHAPES, constrainShape, type PlacedShape } from '@/lib/composition';

const SHAPES = ['rectangle', 'circle', 'triangle'] as const;
const ICONS = [RectangleHorizontal, Circle, Triangle];
function Screw({ position }: { position: string }) { return <span aria-hidden="true" className={`screw ${position}`}><i /></span>; }
function Screws() { return <>{['top-left', 'top-right', 'bottom-left', 'bottom-right'].map(p => <Screw key={p} position={p} />)}</>; }

export default function DesignerFly() {
  const { model, report, error, shape, phase, progress, host, live, ready, draw, wings, toggleWings, neuralSource, strokeCount, strokeIndex, isComposition, speed, cycleSpeed } = useDrawing();
  const [neuralMode, setNeuralMode] = useState<'activity' | 'anatomy'>('activity');
  const [arranging, setArranging] = useState(false), [study, setStudy] = useState<PlacedShape[]>(INITIAL_STUDY);
  const nextId = useRef(5);
  function chooseShape(kind: number) {
    if (!arranging) { void draw(kind); return; }
    if (study.length >= MAX_SHAPES) return;
    const id = nextId.current++;
    setStudy(s => [...s, constrainShape({ id, shape: kind, x: ((id % 3) - 1) * .18, y: ((id % 2) - .5) * .25, width: .55, height: .55 })]);
  }
  useEffect(() => {
    if (!arranging) return;
    const key = (e: KeyboardEvent) => { if (e.repeat || e.metaKey || e.ctrlKey || e.altKey) return; const i = ['1', '2', '3'].indexOf(e.key); if (i >= 0) { e.preventDefault(); e.stopImmediatePropagation(); chooseShape(i); } };
    window.addEventListener('keydown', key, true); return () => window.removeEventListener('keydown', key, true);
  });
  const compositionScores = report?.reports['composition-validation']?.scores;
  const expanded = report?.reports['active-motor'];
  const motorScores = expanded ? { trained_rmse: expanded.after_rmse, ablated_rmse: expanded.ablated_rmse } : isComposition ? compositionScores && { ...compositionScores, untrained_rmse: compositionScores.before_refinement_rmse } : report?.reports['motor-validation']?.scores;
  const busy = ['drawing', 'draw', 'approach', 'travel', 'lower', 'lift'].includes(phase);
  const monitoring = ready && (busy || wings);
  const status = error ? 'Connection interrupted' : !ready ? 'Preparing the studio' : arranging ? study.length >= MAX_SHAPES ? 'Eight shapes on this sheet' : 'Shape buttons add to the study' : phase === 'travel' ? `Moving to shape ${strokeIndex + 1}` : phase === 'lower' ? 'Pencil to paper' : phase === 'lift' ? 'Lifting the pencil' : phase === 'approach' ? 'Taking the pencil' : phase === 'drawing' || phase === 'draw' ? `Drawing ${SHAPES[shape!]}${strokeCount > 1 ? ` ${strokeIndex + 1}/${strokeCount}` : ''}` : phase === 'done' ? 'A little work of art' : 'Ready when you are';
  return (
    <main className="workbench">
      <div className="device-pair">
        <section className="instrument drawing-device" aria-label="Designer Fly drawing instrument">
          <Screws />
          <header className="faceplate"><div className="wordmark"><span className="brand-mark" aria-hidden="true"><i /><i /><i /></span><h1>designer fly<span className="brand-period">.</span></h1></div><div className="model-number"><strong>DF–01</strong></div></header>
          <div className="paper-surround">
            <section className="scene-view" aria-label={`Three-dimensional fruit fly controlling a physical stylus with one foreleg at a small artist pedestal. ${shape === null ? 'Blank canvas.' : `${isComposition ? `${strokeCount}-shape study` : SHAPES[shape]}, ${Math.round(progress * 100)} percent drawn.`}`}>
              <div ref={host} className="fly-scene" />
              <span className="view-corner corner-a" /><span className="view-corner corner-b" /><span className="view-corner corner-c" /><span className="view-corner corner-d" />
              <output className="scene-status" aria-label="Fly activity" aria-live="polite">{status}</output>
              <div className="scene-hint">Drag to rotate · Scroll to zoom</div>
              {!ready && <div className="scene-loading">{error || 'Preparing the little studio…'}</div>}
              {arranging && <CompositionEditor shapes={study} onChange={setStudy} onClose={() => setArranging(false)} onDraw={() => { setArranging(false); void draw(study[0].shape, study); }} />}
            </section>
            <div className="rail" aria-hidden="true"><div className="rail-ticks" /></div>
          </div>
          <div className="control-panel">
            <div className="utility-controls"><button className="hardware-key utility-key" aria-label="Arrange shapes" aria-pressed={arranging} disabled={!ready || busy} onClick={() => setArranging(a => !a)}><LayoutTemplate size={19} /><span>Arrange</span></button><button className="hardware-key utility-key wing-key" aria-label={wings ? 'Stop wings' : 'Flap wings'} aria-pressed={wings} onClick={toggleWings} disabled={!ready}><Wind size={20} /><span>Wings</span></button><button className="hardware-key utility-key speed-key" aria-label={`Simulation speed ${speed} times. Click to change.`} onClick={cycleSpeed} disabled={!ready} title="Advance more full physics steps per update"><Gauge size={19} /><span>{speed}× speed</span></button></div>
            <div className="shape-controls" aria-label="Choose a shape">{SHAPES.map((kind, i) => { const Icon = ICONS[i]; return <div className="key-module" key={kind}><button disabled={!ready || (arranging && study.length >= MAX_SHAPES)} className={`shape-key ${!arranging && shape === i ? 'selected' : ''}`} onClick={() => chooseShape(i)} aria-label={`${arranging ? 'Add' : 'Draw'} ${kind}`} aria-keyshortcuts={String(i + 1)} title={`${arranging ? 'Add' : 'Draw'} ${kind} (${i + 1})`}><span className="key-top"><Icon size={31} strokeWidth={1.7} /><span className="key-indicator" /></span></button><span className="key-caption" aria-hidden="true"><span>0{i + 1}</span>{kind}</span></div>; })}</div>
          </div>
          <footer className="device-footer" aria-hidden="true"><span className="footer-dots"><i /><i /><i /></span><span className="vent" /></footer>
        </section>
        <div className={`cable ${busy ? 'connected' : ''}`} aria-hidden="true"><i className="jack jack-left" /><svg viewBox="0 0 90 300" preserveAspectRatio="none"><path d="M0 70 C65 70 4 244 56 244 C85 244 70 136 90 136" /><path className="cable-highlight" d="M0 70 C65 70 4 244 56 244 C85 244 70 136 90 136" /></svg><i className="jack jack-right" /></div>
        <aside className="instrument neural-device" aria-label="Live neural circuit monitor">
          <Screws />
          <header className="neural-header"><h2>neural link<span>.</span></h2><span className="neural-model">NL–01</span></header>
          <div className="neural-screen"><div className="screen-top"><span>{neuralSource === 'motor' ? 'Drawing controller' : 'Wing rhythm'}</span><span className={`screen-live ${monitoring ? 'active' : ''}`}>{monitoring ? '● Live' : '● Paused'}</span></div>{model && <NeuralDisplay model={model} live={live} source={neuralSource} mode={neuralMode} />}
            <div className="screen-metrics">{model?.neurons.toLocaleString('en-US') || '…'} neurons · {model?.edges.toLocaleString('en-US') || '…'} connections</div>
            <div className="signal-row"><span>{isComposition ? 'Study' : 'Drawing'}</span><progress className="signal-track" aria-label={isComposition ? 'Study progress' : 'Drawing progress'} value={progress} max={1} /><span>{Math.round(progress * 100)}%</span></div>
          </div>
          <div className="neural-hardware"><button className="hardware-key mode-key" aria-pressed={neuralMode === 'activity'} onClick={() => setNeuralMode('activity')}><Activity size={19} /><span>Activity</span><i /></button><button className="hardware-key mode-key" aria-pressed={neuralMode === 'anatomy'} onClick={() => setNeuralMode('anatomy')}><GitBranch size={19} /><span>Anatomy</span><i /></button></div>
          <footer className="device-footer" aria-hidden="true"><span className="vent" /></footer>
        </aside>
      </div>
      <div className="bench-footer"><p>Pick a shape. Let the little artist take it from here.</p></div>
      <details className="experiment-notes"><summary>Inside the experiment <span>↗</span></summary><div className="notes-content compact-notes">
        <p><strong>How it works.</strong> A trained neural planner makes the shape path. Arrange specifies its position and size; a feedback network reads joint motion, pencil error and contact, then drives three physical foreleg joints in MuJoCo. Marks appear only when the tip touches the paper during a stroke.</p>
        <p><strong>What you’re seeing.</strong> The monitor shows a selected MaleCNS ventral nerve cord circuit. Activity colors show signed model values; rings show changes between samples (×8). Anatomy colors identify sensory, local-circuit and motor cells. Missing cell locations are never invented. The trace includes every neuron.</p>
        <p><strong>The limits.</strong> This is an embodied neural prototype: a fixed body, one controlled foreleg and an attached pencil. Wings are driven animation, without flight physics. Layouts are specified by you or a preset. It does not understand prompts or autonomously design interfaces; biological accuracy and an advantage over random wiring are unproven.</p>
        <p><strong>Speed.</strong> 1× / 2× / 4× runs more complete neural-and-physics steps per display update, keeping the timestep and every contact/ink sample. It accelerates simulation time, not the learned movement in physical time. Actual speed depends on your computer.</p>
        {motorScores && <p className="compact-evidence">Held-out command error: {motorScores.trained_rmse.toFixed(3)} trained · {motorScores.ablated_rmse.toFixed(3)} with connections removed.</p>}
        <p className="credits">Built by <a href="https://github.com/hckmstrrahul" target="_blank" rel="noreferrer">@hckmstrrahul</a> · <a href="https://github.com/hckmstrrahul/designerfly" target="_blank" rel="noreferrer">Code &amp; methods ↗</a><br />Data: <a href="https://male-cns.janelia.org/" target="_blank" rel="noreferrer">MaleCNS / FlyEM</a> (CC BY 4.0) · Anatomy: <a href="https://github.com/NeLy-EPFL/flygym" target="_blank" rel="noreferrer">NeuroMechFly / FlyGym</a> (Apache 2.0).</p>
      </div></details>
    </main>
  );
}
