export type NeuralSource = 'motor' | 'wing' | 'spiking';
export interface NeuralSample { source: NeuralSource; time: number; sequence: number; run: number; state: Float32Array }
export interface ActivityTrace { source: NeuralSource | null; run: number; sequence: number; samples: { time: number; mean: number }[] }
export function activityTrace(): ActivityTrace { return { source: null, run: -1, sequence: -1, samples: [] }; }
/** At most one plotted value per neural observation; no render-clock samples. */
export function recordActivity(trace: ActivityTrace, sample: NeuralSample, neurons = 1024) {
  const differentStream = trace.source !== sample.source || trace.run !== sample.run;
  if (!differentStream && sample.sequence <= trace.sequence) return false;
  if (sample.state.length !== neurons || !Number.isFinite(sample.time) || sample.state.some(v => !Number.isFinite(v))) return false;
  if (differentStream) trace.samples = [];
  trace.source = sample.source; trace.run = sample.run; trace.sequence = sample.sequence;
  const mean = sample.state.reduce((sum, v) => sum + Math.abs(v), 0) / sample.state.length;
  trace.samples.push({ time: sample.time, mean });
  while (trace.samples.length > 200 || (trace.samples.length > 1 && trace.samples[0].time < sample.time - 8)) trace.samples.shift();
  return true;
}
