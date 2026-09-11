import test from 'node:test';
import assert from 'node:assert/strict';
import { activityTrace, recordActivity, type NeuralSample } from '../lib/neural-telemetry.ts';
const sample = (extra: Partial<NeuralSample> = {}): NeuralSample => ({ source: 'motor', time: 1, sequence: 1, run: 1, state: new Float32Array(1024).fill(-.25), ...extra });
void test('neural trace uses signed-rate magnitude and adds no samples when inference holds', () => {
  const trace = activityTrace(); recordActivity(trace, sample());
  for (let i = 0; i < 100; i++) recordActivity(trace, sample());
  assert.equal(trace.samples.length, 1); assert.equal(trace.samples[0].mean, .25);
  recordActivity(trace, sample({ time: 1.08, sequence: 2 }));
  assert.equal(trace.samples[1].time, 1.08); assert.equal(trace.samples[1].mean, .25);
});
void test('switching source or drawing clears unrelated trace history', () => {
  const trace = activityTrace(); recordActivity(trace, sample());
  recordActivity(trace, sample({ source: 'wing', sequence: 2, time: 40 }));
  assert.equal(trace.samples.length, 1); assert.equal(trace.source, 'wing');
  recordActivity(trace, sample({ run: 2, sequence: 3, time: .02 }));
  assert.equal(trace.samples.length, 1); assert.equal(trace.source, 'motor'); assert.equal(trace.samples[0].time, .02);
});
void test('invalid neural payloads never become displayed activity', () => {
  const trace = activityTrace();
  assert.equal(recordActivity(trace, sample({ state: new Float32Array(10) })), false);
  assert.equal(recordActivity(trace, sample({ state: new Float32Array(1024).fill(NaN) })), false);
  assert.equal(trace.samples.length, 0);
});
void test('switching back to a cached controller accepts its older sequence without duplicating samples', () => {
  const trace = activityTrace();
  recordActivity(trace, sample({ sequence: 20 }));
  recordActivity(trace, sample({ source: 'wing', sequence: 21 }));
  assert.equal(recordActivity(trace, sample({ sequence: 20 })), true);
  assert.equal(trace.source, 'motor');
  assert.equal(trace.samples.length, 1);
  assert.equal(recordActivity(trace, sample({ sequence: 20 })), false);
});
void test('expanded network telemetry includes every cell and rejects a mismatched graph', () => {
  const trace = activityTrace(), expanded = sample({ state: new Float32Array(2048).fill(.125) });
  assert.equal(recordActivity(trace, expanded), false);
  assert.equal(recordActivity(trace, expanded, 2048), true);
  assert.equal(trace.samples[0].mean, .125);
  assert.equal(recordActivity(trace, expanded, 2048), false);
});
