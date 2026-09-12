export interface CircuitModel {
  neurons: number; edges: number; features: number; steps: number;
  crow: number[]; col: number[]; rows: number[]; values: number[];
  leak: number[]; bias: number[]; sensory: number[]; motor: number[];
  projection: number[]; decoder: number[]; bodyIds: string[];
  positions: ([number, number, number] | null)[]; nodeClasses: string[];
  report: { before: { rmse: number }; after: { rmse: number }; ablated: { rmse: number }; seconds: number; seed: number };
}

export type CircuitView = Pick<CircuitModel, 'neurons' | 'edges' | 'steps' | 'bodyIds' | 'positions' | 'nodeClasses' | 'rows' | 'col'>;

/** Same sparse rate network as research/train.py. No path geometry at inference. */
export function infer(model: CircuitModel, shape: number, phase: number, ablated = false) {
  const features = new Float32Array(16);
  features[shape] = 1;
  for (let k = 1; k <= 6; k++) {
    features[3 + (k - 1) * 2] = Math.sin(2 * Math.PI * k * phase);
    features[4 + (k - 1) * 2] = Math.cos(2 * Math.PI * k * phase);
  }
  features[15] = 1;
  const drive = new Float32Array(model.neurons);
  model.sensory.forEach((cell, i) => {
    for (let j = 0; j < 16; j++) drive[cell] += features[j] * model.projection[i * 16 + j];
  });
  let state = new Float32Array(model.neurons);
  let next = new Float32Array(model.neurons);
  for (let step = 0; step < model.steps; step++) {
    for (let n = 0; n < model.neurons; n++) {
      let recurrent = 0;
      if (!ablated) for (let e = model.crow[n]; e < model.crow[n + 1]; e++) recurrent += model.values[e] * state[model.col[e]];
      next[n] = (1 - model.leak[n]) * state[n] + model.leak[n] * Math.tanh(recurrent + drive[n] + model.bias[n]);
    }
    [state, next] = [next, state];
  }
  const point: [number, number] = [0, 0];
  model.motor.forEach((cell, i) => { point[0] += state[cell] * model.decoder[i * 2]; point[1] += state[cell] * model.decoder[i * 2 + 1]; });
  return { point, state };
}

export interface NeuralFrame { point: [number, number]; state: Float32Array; phase: number; run: number; source?: 'motor' | 'wing' | 'spiking'; time?: number; sequence?: number; }
