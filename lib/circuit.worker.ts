import { infer, type CircuitModel } from './circuit';
let model: CircuitModel | null = null;
self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'load') {
      const response = await fetch('/models/circuit-123.json');
      if (!response.ok) throw new Error('Neural model could not be loaded');
      model = await response.json();
      self.postMessage({ type: 'ready', model });
    } else if (model && data.type === 'infer') {
      const result = infer(model, data.shape, data.phase);
      self.postMessage({ type: 'frame', ...result, phase: data.phase, run: data.run }, { transfer: [result.state.buffer] });
    }
  } catch (error) { self.postMessage({ type: 'error', message: String(error) }); }
};
