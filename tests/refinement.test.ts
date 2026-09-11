import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { infer } from '../lib/circuit.ts';
const read = (path: string) => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
void test('refined shape inference matches PyTorch, including all displayed states', () => {
  const model = read('../public/models/circuit-refined.json'), fixture = read('../research/results/parity-refined.json');
  fixture.shape.forEach((shape: number, i: number) => {
    const result = infer(model, shape, fixture.phase[i]);
    result.point.forEach((v, j) => assert.ok(Math.abs(v - fixture.output[i][j]) < 2e-5));
    result.state.forEach((v, j) => assert.ok(Math.abs(v - fixture.states[i][j]) < 2e-5));
  });
});
void test('rectangle held-out straightness and corners improve without snapping the output', () => {
  const r = read('../research/results/refinement.json');
  assert.equal(r.passed, true);
  assert.ok(r.after.rectangle.max_edge_deviation < r.before.rectangle.max_edge_deviation * .2);
  assert.ok(r.after.rectangle.max_corner_error < .01);
  for (const shape of ['rectangle', 'circle', 'triangle']) assert.ok(r.after[shape].rmse < .005);
});
void test('independent motor validation preserves measured graph interfaces and needs its connections', () => {
  const r = read('../research/results/motor-validation.json');
  assert.equal(r.fixed_interfaces, true); assert.equal(r.sparse_pytorch_parity, true);
  assert.ok(r.scores.trained_rmse < r.scores.untrained_rmse * .25);
  assert.ok(r.scores.ablated_rmse > r.scores.trained_rmse * 5);
});
void test('all three physical shapes pass tracking, contact and disturbance-recovery checks', () => {
  const r = read('../research/results/embodied-validation.json');
  assert.equal(r.passed, true); assert.equal(r.teacher_at_inference, false);
  for (const shape of ['rectangle', 'circle', 'triangle']) {
    const normal = r.results.find((v: { shape: string; condition: string }) => v.shape === shape && v.condition === 'normal');
    assert.ok(normal.rmse < .035); assert.ok(normal.contact_fraction > .95);
    const perturbed = r.results.find((v: { shape: string; condition: string }) => v.shape === shape && v.condition === 'perturbed');
    assert.ok(perturbed.recovery_error < .05);
    for (const condition of ['feedback_removed', 'core_removed']) {
      const ablated = r.results.find((v: { shape: string; condition: string }) => v.shape === shape && v.condition === condition);
      assert.ok(ablated.rmse > normal.rmse * 10);
    }
  }
});
