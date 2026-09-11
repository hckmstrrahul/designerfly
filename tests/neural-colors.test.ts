import test from 'node:test';
import assert from 'node:assert/strict';
import { activityColor, activityChange } from '../lib/neural-colors.ts';
void test('signed rate colors preserve opposite states instead of merging their magnitudes', () => {
  assert.notEqual(activityColor(-.5), activityColor(.5));
  assert.equal(activityColor(0), 'rgb(143,165,158)');
  assert.equal(activityColor(-1), 'rgb(99,175,249)');
  assert.equal(activityColor(1), 'rgb(255,139,103)');
  assert.equal(activityColor(2), activityColor(1));
});
void test('activity change responds to sign reversals, holds at zero for equal samples, and has fixed gain', () => {
  assert.equal(activityChange(.03, .03), 0);
  assert.equal(activityChange(.03, -.03), .48);
  assert.equal(activityChange(.5, -.5), 1);
});
