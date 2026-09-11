import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fitNeuralProjection } from '../lib/neural-projection.ts';

const model = JSON.parse(readFileSync(new URL('../public/models/circuit-refined.json', import.meta.url), 'utf8'));
void test('all measured soma locations remain visible on narrow, tall and wide screens', () => {
  for (const [w, h] of [[220, 500], [300, 270], [500, 220], [190, 700]]) {
    const points = fitNeuralProjection(model.positions, w, h);
    assert.equal(points.filter(Boolean).length, 758);
    points.forEach((p, i) => {
      if (!model.positions[i]) { assert.equal(p, null); return; }
      assert.ok(p && p[0] >= 17.99 && p[0] <= w - 17.99 && p[1] >= 15.99 && p[1] <= h - 15.99);
    });
  }
});
void test('anatomical skeletons map to exactly their trained neuron IDs', () => {
  const anatomy = JSON.parse(readFileSync(new URL('../public/models/neural-anatomy.json', import.meta.url), 'utf8'));
  assert.equal(anatomy.cells.length, 96);
  for (const cell of anatomy.cells) {
    assert.equal(String(model.bodyIds[cell.neuron]), cell.bodyId);
    assert.ok(model.nodeClasses[cell.neuron].startsWith('vnc_'));
    assert.ok(cell.points.every((p: number[]) => p.length === 3 && p.every(Number.isFinite)));
    for (const [a, b] of cell.edges) assert.ok(a !== b && cell.points[a] && cell.points[b]);
  }
});
