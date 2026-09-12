import { Wind, LayoutTemplate, Activity, FlaskConical, Scale, ArrowUpRight, Type, Smile, Camera } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useDrawing } from '@/lib/use-drawing';
import { DeviceCable } from './device-cable';
import { NeuralDisplay } from './neural-display';
import { CompositionEditor, type EditorMode, type EditorTool } from './composition-editor';
import { UI_EXAMPLE, MAX_SHAPES, constrainShape, type PlacedShape } from '@/lib/composition';

const SHAPES = ['rectangle', 'circle', 'triangle'] as const;
function Screw({ position }: { position: string }) { return <span aria-hidden="true" className={`screw ${position}`}><i /></span>; }
function Screws() { return <>{['top-left', 'top-right', 'bottom-left', 'bottom-right'].map(p => <Screw key={p} position={p} />)}</>; }

export default function DesignerFly() {
  const { model, report, error, shape, phase, progress, host, live, ready, draw, wings, toggleWings, neuralSource, selectNeuralSource, strokeCount, strokeIndex, isComposition, speed, cycleSpeed, cameraPreset, cycleCamera, contact } = useDrawing();
  const [arranging, setArranging] = useState(false);
  const [editorMode,setEditorMode] = useState<EditorMode>('arrange');
  const [canvases,setCanvases] = useState<Record<EditorMode,PlacedShape[]>>({arrange:UI_EXAMPLE,text:[],emoji:[]});
  const study=canvases[editorMode];
  const setStudy=(next:PlacedShape[] | ((current:PlacedShape[])=>PlacedShape[]))=>setCanvases(current=>({...current,[editorMode]:typeof next==='function'?next(current[editorMode]):next}));
  const [editorTool,setEditorTool] = useState<EditorTool>('arrange');
  function openEditor(mode:EditorMode){setEditorMode(mode);setEditorTool(mode);setArranging(true);}
  const nextId = useRef(5);
  const experimentDialog = useRef<HTMLDialogElement>(null);
  const stage = useRef<HTMLDivElement>(null), devices = useRef<HTMLDivElement>(null);
  const [deviceScale, setDeviceScale] = useState(1);
  const [stageHeight, setStageHeight] = useState<number>();
  useEffect(() => {
    const fit = () => {
      if (!stage.current || !devices.current) return;
      const bench = stage.current.parentElement!;
      const heading = bench.querySelector<HTMLElement>('.project-heading')!;
      const style = getComputedStyle(bench);
      const available = bench.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom) - heading.offsetHeight - parseFloat(style.rowGap);
      const scale = window.innerWidth <= 1000 ? 1 : Math.max(0, Math.min(1, stage.current.clientWidth / devices.current.offsetWidth, available / devices.current.offsetHeight));
      setDeviceScale(scale);
      setStageHeight(devices.current.offsetHeight * scale);
    };
    const observer = new ResizeObserver(fit);
    if (stage.current) {
      observer.observe(stage.current);
      observer.observe(stage.current.parentElement!);
      const heading = stage.current.parentElement!.querySelector('.project-heading');
      if (heading) observer.observe(heading);
    }
    if (devices.current) observer.observe(devices.current);
    fit(); return () => observer.disconnect();
  }, []);
  function chooseShape(kind: number) {
    if (!arranging) { void draw(kind); return; }
    if (study.length >= MAX_SHAPES) return;
    const id = Math.max(nextId.current, ...study.map(s => s.id + 1));
    nextId.current = id + 1;
    setStudy(s => [...s, constrainShape({ id, shape: kind, x: ((id % 3) - 1) * .18, y: ((id % 2) - .5) * .25, width: .55, height: .55 })]);
  }
  useEffect(() => {
    if (!arranging) return;
    const key = (e: KeyboardEvent) => { if (e.repeat || e.metaKey || e.ctrlKey || e.altKey || (e.target instanceof HTMLElement && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName))) return; const i = ['1', '2', '3'].indexOf(e.key); if (i >= 0) { e.preventDefault(); e.stopImmediatePropagation(); if(editorMode==='arrange' && (editorTool==='arrange'||editorTool==='pen')) chooseShape(i); } };
    window.addEventListener('keydown', key, true); return () => window.removeEventListener('keydown', key, true);
  });
  const compositionScores = report?.reports['composition-validation']?.scores;
  const expanded = report?.reports['active-motor'];
  const motorScores = expanded ? { trained_rmse: expanded.after_rmse, ablated_rmse: expanded.ablated_rmse } : isComposition ? compositionScores && { ...compositionScores, untrained_rmse: compositionScores.before_refinement_rmse } : report?.reports['motor-validation']?.scores;
  const busy = ['drawing', 'draw', 'approach', 'travel', 'lower', 'lift'].includes(phase);
  const monitoring = ready && (neuralSource === 'wing' ? wings : busy);
  const status = error ? 'Connection interrupted' : !ready ? 'Preparing the studio' : arranging ? study.length >= MAX_SHAPES ? 'This sheet is full' : 'Shape buttons add to the study' : phase === 'travel' ? `Moving to shape ${strokeIndex + 1}` : phase === 'lower' ? 'Pencil to paper' : phase === 'lift' ? 'Lifting the pencil' : phase === 'approach' ? 'Taking the pencil' : phase === 'drawing' || phase === 'draw' ? `Drawing ${isComposition ? 'stroke' : SHAPES[shape!]}${strokeCount > 1 ? ` ${strokeIndex + 1}/${strokeCount}` : ''}` : phase === 'done' ? 'A little work of art' : 'Ready when you are';
  return (
    <main className="workbench">
      <header className="project-heading">
        <h2>designerfly<span className="brand-period">.</span></h2>
        <p>A virtual fruit fly drawing with a trained neural controller.</p>
        <nav aria-label="About this project">
          <button onClick={() => experimentDialog.current?.showModal()}><FlaskConical aria-hidden="true" />About this experiment</button>
          <a href="https://github.com/hckmstrrahul/designerfly" target="_blank" rel="noreferrer"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .75a11.25 11.25 0 0 0-3.56 21.92c.56.1.77-.24.77-.54v-2.1c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 1.71 2.63 1.22 3.27.93.1-.73.4-1.22.71-1.5-2.5-.28-5.13-1.25-5.13-5.56 0-1.23.44-2.24 1.16-3.02-.12-.29-.5-1.43.11-2.98 0 0 .95-.3 3.09 1.15a10.77 10.77 0 0 1 5.62 0c2.15-1.45 3.09-1.15 3.09-1.15.61 1.55.23 2.69.11 2.98.72.78 1.16 1.79 1.16 3.02 0 4.32-2.63 5.28-5.14 5.56.4.35.76 1.03.76 2.09v3.09c0 .3.2.65.77.54A11.25 11.25 0 0 0 12 .75Z" /></svg>GitHub<ArrowUpRight aria-hidden="true" /></a>
          <a href="https://github.com/hckmstrrahul/designerfly/blob/main/LICENSE" target="_blank" rel="noreferrer"><Scale aria-hidden="true" />Open source · MIT<ArrowUpRight aria-hidden="true" /></a>
        </nav>
      </header>
      <div className="device-stage" ref={stage} style={{ height: stageHeight }}>
      <div className="device-pair" ref={devices} style={{ transform: `scale(${deviceScale})` }}>
        <section className="instrument drawing-device" aria-label="Designer Fly drawing instrument">
          <Screws />
          <header className="faceplate"><div className="wordmark"><h1>simulator<span className="brand-period">.</span></h1></div><div className="model-number"><strong>S–01</strong></div></header>
          <div className="paper-surround">
            <section className="scene-view" aria-label={`Three-dimensional fruit fly controlling a physical stylus with one foreleg at a small artist pedestal. ${shape === null ? 'Blank canvas.' : `${isComposition ? `${strokeCount}-shape study` : SHAPES[shape]}, ${Math.round(progress * 100)} percent drawn.`}`}>
              <div ref={host} className="fly-scene" />
              <span className="view-corner corner-a" /><span className="view-corner corner-b" /><span className="view-corner corner-c" /><span className="view-corner corner-d" />
              <output className="scene-status" aria-label="Fly activity" aria-live="polite">
                <svg className="fly-speaker" viewBox="0 0 32 32" fill="none" aria-hidden="true">
                  <g stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 15C4 2 2 18 13 20m5-5C28 2 30 18 19 20M13 23l-4 4m10-4 4 4M14 7l-2-3m6 3 2-3" />
                    <ellipse cx="16" cy="20" rx="3" ry="6" fill="currentColor" fillOpacity=".12" />
                    <circle cx="16" cy="10" r="3.5" />
                  </g>
                </svg>
                <span>{status}</span>
              </output>
              <div className="scene-hint">Drag to rotate · Scroll to zoom</div>
              {!ready && <div className="scene-loading">{error || 'Preparing the little studio…'}</div>}
              {arranging && <CompositionEditor mode={editorMode} tool={editorTool} onTool={setEditorTool} shapes={study} onChange={setStudy} onClose={() => setArranging(false)} onDraw={(paths) => { if(!paths.length)return; setStudy(paths); setArranging(false); void draw(paths[0].shape, paths); }} />}
            </section>
            <div className="rail" aria-hidden="true"><div className="rail-ticks" /></div>
          </div>
          <div className="control-panel">
            <div className="utility-controls">

              <div className="utility-module"><button className={`shape-key round-key ${wings ? 'selected' : ''}`} aria-label={wings ? 'Stop wings' : 'Flap wings'} aria-pressed={wings} onClick={toggleWings} disabled={!ready}><span className="key-top"><Wind size={26} strokeWidth={1.7} /><span className="key-indicator" /></span></button><span className="key-caption" aria-hidden="true">Wings</span></div>
              <div className="utility-module"><button className="shape-key round-key speed-key selected" aria-pressed={true} aria-label={`Simulation speed ${speed} times. Click to change.`} onClick={cycleSpeed} disabled={!ready} title="Advance more full physics steps per update"><span className="key-top"><span className="speed-value">{speed}×</span><span className="speed-leds" aria-hidden="true">{[1, 2, 4].map(level => <i key={level} className={speed >= level ? 'lit' : ''} />)}</span></span></button><span className="key-caption" aria-hidden="true">Speed</span></div>
              <div className="utility-module"><button className="shape-key round-key speed-key selected" aria-pressed={true} aria-label={`Camera view ${cameraPreset+1}: ${['Angled','Paper','Overhead'][cameraPreset]}. Click to change.`} title="Cycle angled, paper and overhead views" onClick={cycleCamera} disabled={!ready}><span className="key-top"><Camera size={25} strokeWidth={1.7}/><span className="speed-leds" aria-hidden="true">{[0,1,2].map(level=><i key={level} className={cameraPreset>=level?'lit':''}/>)}</span></span></button><span className="key-caption">Camera</span></div>
            </div>
            <div className="shape-controls" aria-label="Drawing modes"><div className="key-module"><button className={`shape-key ${arranging && editorMode==='arrange' ? 'selected' : ''}`} aria-label="Draw UI" aria-pressed={arranging&&editorMode==='arrange'} disabled={!ready || busy} onClick={() => {if(arranging&&editorMode==='arrange')setArranging(false);else openEditor('arrange');}}><span className="key-top"><LayoutTemplate size={25} strokeWidth={1.7} /><span className="key-indicator" /></span></button><span className="key-caption" aria-hidden="true">Draw UI</span></div>{([{tool:'text',label:'Text',Icon:Type},{tool:'emoji',label:'Emoji',Icon:Smile}] as const).map(({tool,label,Icon})=><div className="key-module" key={tool}><button className={`shape-key ${arranging&&editorMode===tool?'selected':''}`} aria-label={`Open ${label.toLowerCase()} mode`} aria-pressed={arranging&&editorMode===tool} disabled={!ready||busy} onClick={()=>openEditor(tool)}><span className="key-top"><Icon size={25} strokeWidth={1.7}/><span className="key-indicator"/></span></button><span className="key-caption">{label}</span></div>)}</div>
          </div>
          <footer className="device-footer" aria-hidden="true"><span className="footer-dots"><i /><i /><i /></span><span className="vent" /></footer>
        </section>
        <aside className="instrument neural-device activity-device" aria-label="Live neural circuit monitor">
          <Screws />
          <header className="neural-header"><h2>neural link<span>.</span></h2><span className="neural-model">NL–01</span></header>
          <div className="neural-screen"><div className="neural-screen-toolbar">
            <span title="Right-drag to pan · Double-click to reset">Drag to rotate · Scroll to zoom</span>
            <span className={`screen-live ${monitoring ? 'active' : ''}`}>{monitoring ? '● Live' : '● Paused'}</span>
          </div>
            <div className="screen-metrics" title="Selected controller totals. The scene displays neurons with measured locations; the trace includes all neurons."><span><strong>{model?.neurons.toLocaleString('en-US') || '…'}</strong> neurons</span><span><strong>{model?.edges.toLocaleString('en-US') || '…'}</strong> connections</span></div>
            {model && <NeuralDisplay model={model} live={live} source={neuralSource} mode="activity" />}
            <div className="controller-status" aria-label="Controller and stylus status"><span><small>Controller</small><b>{neuralSource === 'wing' ? 'Wing rhythm' : 'Foreleg motor'}</b></span><span><small>Stylus</small><b>{contact ? 'On paper' : 'Lifted'}</b></span></div>
            <div className="signal-row"><span>{isComposition ? 'Study' : 'Drawing'}</span><progress className="signal-track" aria-label={isComposition ? 'Study progress' : 'Drawing progress'} value={progress} max={1} /><span>{Math.round(progress * 100)}%</span></div>
          </div>
          <div className="neural-hardware" aria-label="Neural signal source"><button className="hardware-key mode-key" aria-pressed={neuralSource === 'motor'} title="Show drawing activity and stop wing flapping" onClick={() => { if (wings) toggleWings(); else selectNeuralSource('motor'); }}><Activity size={19} /><span>Drawing 01</span><i /></button><button className="hardware-key mode-key" aria-pressed={neuralSource === 'wing'} title="Start wing flapping and show its activity" onClick={() => { if (!wings) toggleWings(); else selectNeuralSource('wing'); }} disabled={!ready}><Wind size={19} /><span>Drawing 02</span><i /></button></div>
          <footer className="device-footer" aria-hidden="true"><span className="vent" /></footer>
        </aside>
        <div className="neural-companions">
        <aside className="instrument neural-device spectral-device" aria-label="Neural morphology colored by controller activity">
          <Screws />
          <header className="neural-header"><h2>neural spectrum<span>.</span></h2><span className="neural-model">NS–01</span></header>
          <div className="neural-screen">
            <div className="anatomy-caption spectrum-status"><span title="Right-drag to pan · Double-click to reset">Drag to rotate · Scroll to zoom</span><span>{monitoring ? '● Live' : '● Paused'}</span></div>
            {model && <NeuralDisplay model={model} live={live} source={neuralSource} mode="spectrum" />}
          </div>
          <footer className="device-footer" aria-hidden="true"><span className="vent" /></footer>
        </aside>
        </div>
        <DeviceCable />
      </div>
      </div>
      {/* Native modal handles backdrop dismissal and isolates simulation shortcuts. */}
      {/* oxlint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <dialog ref={experimentDialog} className="experiment-modal" aria-labelledby="experiment-title" onClick={event => { if (event.target === event.currentTarget) experimentDialog.current?.close(); }} onKeyDown={event => event.stopPropagation()}>
        <header><h2 id="experiment-title">About this experiment</h2><button aria-label="Close experiment details" onClick={() => experimentDialog.current?.close()}>×</button></header>
        <div className="experiment-content">
          <section><h3>From neurons to pencil</h3><p>A trained planner traces a shape. A feedback network uses joint motion, pencil error and contact to drive three foreleg joints in MuJoCo. Ink appears only when the pencil touches paper.</p></section>
          <section><h3>Reading the displays</h3><div className="display-explain">
            <div><h4>Neural Link</h4><p>A selected MaleCNS circuit: red and green show signed model activity; brightness shows strength. The graph averages activity magnitude across all controller neurons.</p></div>
            <div><h4>Neural Spectrum</h4><p>96 measured neuron skeletons. Color identifies each neuron; brightness follows its computed activity. Missing locations are omitted.</p></div>
          </div></section>
          <section><h3>What this prototype can do</h3><p>Draw shapes, rounded wireframes and short lettering with one controlled foreleg. Letter paths are supplied; the existing trained motor draws them. The body stays fixed; wing flapping is neural animation without flight physics. It cannot understand prompts or design interfaces on its own.</p><p className="experiment-caveat">These are model values, not recorded spikes or signals travelling along branches. This is a partial circuit, not a full brain. Biological accuracy and an advantage over random wiring remain unproven.</p></section>
          <section><h3>Faster simulation</h3><p>1×, 2× and 4× run more complete physics and neural steps per update, preserving the timestep and ink samples. Actual speed depends on your computer.</p></section>
          {motorScores && <section className="experiment-results"><h3>Held-out command error <span>Lower is better</span></h3><div><p><strong>{motorScores.trained_rmse.toFixed(3)}</strong><span>Trained controller</span></p><p><strong>{motorScores.ablated_rmse.toFixed(3)}</strong><span>Connections removed</span></p></div></section>}
          <section className="experiment-sources"><h3>Sources &amp; credits</h3><p><a href="https://male-cns.janelia.org/" target="_blank" rel="noreferrer">MaleCNS / FlyEM ↗</a><span>Neural data · CC BY 4.0</span></p><p><a href="https://github.com/NeLy-EPFL/flygym" target="_blank" rel="noreferrer">NeuroMechFly / FlyGym ↗</a><span>Fly anatomy · Apache 2.0</span></p><p className="experiment-author">Built by <a href="https://github.com/hckmstrrahul" target="_blank" rel="noreferrer">@hckmstrrahul</a><a href="https://github.com/hckmstrrahul/designerfly" target="_blank" rel="noreferrer">Code &amp; methods ↗</a></p></section>
        </div>
      </dialog>
    </main>
  );
}
