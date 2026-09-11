import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { infer, type CircuitModel } from '../lib/circuit.ts';
const model: CircuitModel = JSON.parse(readFileSync(new URL('../public/models/circuit-123.json', import.meta.url), 'utf8'));
const fixture = JSON.parse(readFileSync(new URL('../research/results/parity-123.json', import.meta.url), 'utf8'));

void test('browser sparse inference matches independently exported PyTorch coordinates and all neuron states', () => {
  for (let i = 0; i < fixture.shape.length; i++) {
    const result = infer(model, fixture.shape[i], fixture.phase[i]);
    result.point.forEach((value, j) => assert.ok(Math.abs(value - fixture.output[i][j]) < 0.00002, `coordinate ${i}/${j}`));
    result.state.forEach((value, j) => assert.ok(Math.abs(value - fixture.states[i][j]) < 0.00002, `neuron ${i}/${j}`));
  }
});

void test('removing measured connections removes task and clock influence at the motor output', () => {
  const outputs = [0, 1, 2].flatMap(shape => [.1, .3, .7].map(phase => infer(model, shape, phase, true).point));
  outputs.forEach(p => p.forEach((v, i) => assert.ok(Math.abs(v - outputs[0][i]) < 1e-6)));
  const trainedA = infer(model, 1, .1).point, trainedB = infer(model, 1, .6).point;
  assert.ok(Math.hypot(trainedA[0] - trainedB[0], trainedA[1] - trainedB[1]) > 1.8);
});

void test('all three training seeds pass held-out shape tests and edge ablation', () => {
  for (const seed of [123, 456, 789]) {
    const r = JSON.parse(readFileSync(new URL(`../research/results/training-${seed}.json`, import.meta.url), 'utf8'));
    assert.equal(r.passed, true); assert.equal(r.fixed_interfaces_and_topology_unchanged, true);
    assert.ok(r.after.rmse < .035); assert.ok(r.ablated.rmse > r.after.rmse * 10);
    assert.equal(r.graph.neurons, 1024); assert.equal(r.graph.edges, 42944);
  }
});
