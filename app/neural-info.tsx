import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

export function NeuralInfo({ onClose }: { onClose: () => void }) {
  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => { const previous = document.activeElement; panel.current?.focus(); return () => { if (previous instanceof HTMLElement) previous.focus(); }; }, []);
  return <div ref={panel} className="neural-info" role="region" aria-label="About the neural displays" tabIndex={-1} onKeyDown={e => { if(e.key==='Escape') {e.stopPropagation();onClose();} }}>
    <header><span>NL–01 / FIELD GUIDE</span><button aria-label="Close neural display information" onClick={onClose}><X size={16}/></button></header>
    <h3>Two ways to move.</h3>
    <div className="neural-info-modes">
      <section><div className="neural-info-label">01 / MOTOR <b>DEFAULT</b></div>
        <svg viewBox="0 0 200 44" aria-hidden="true"><path d="M0 30 C20 30 20 12 40 12 S60 30 80 30 S100 12 120 12 S140 30 160 30 S180 12 200 12"/></svg>
        <h4>Smooth signals.</h4><p>Trained to guide the leg steadily. Best for clean drawings.</p></section>
      <section><div className="neural-info-label">02 / SPIKES <b>EXPERIMENT</b></div>
        <svg viewBox="0 0 200 44" aria-hidden="true"><path d="M0 32 H20 V8 H23 V32 H45 V8 H48 V32 H57 V8 H60 V32 H100 V8 H103 V32 H130 V8 H133 V32 H143 V8 H146 V32 H177 V8 H180 V32 H200"/></svg>
        <h4>Neurons that fire.</h4><p>Uses brief neural pulses. Still less precise: lines can wobble.</p></section>
    </div>
    <div className="neural-info-flow" aria-label="Drawing path goes through the controller to the leg, which returns feedback"><span>YOUR PATH</span><i>→</i><span>CONTROLLER</span><i>⇄</i><span>LEG + PENCIL</span></div>
    <section className="neural-info-reading"><span className="neural-info-label">READ THE DISPLAYS</span>
      <p><strong>NL–01 · Activity</strong> Dots show model neurons. The graph shows average activity. Motor: red/green = negative/positive signal. Spikes: brighter green = more firing.</p>
      <p><strong>NS–01 · Structure</strong> Real, selected neuron shapes. Each color identifies a neuron; brightness follows its activity.</p>
    </section>
    <footer>Wings show their rhythm in Motor. These are simulated signals, not live brain recordings.</footer>
  </div>;
}
