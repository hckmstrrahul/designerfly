import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Group, Vector3 } from 'three';
import { createJointRig } from '../lib/fly-rig.ts';
import { applyPhysicalPose } from '../lib/fly-pose.ts';

void test('segmented foot retains its lengths and wraps outside the pencil shaft', () => {
  const rig = JSON.parse(readFileSync(new URL('../public/models/fly/rig.json', import.meta.url), 'utf8'));
  const frames = JSON.parse(readFileSync(new URL('../research/results/pose-check.json', import.meta.url), 'utf8'));
  const root = new Group(); root.rotation.x = -Math.PI / 2; root.position.x = -.3;
  const joints = createJointRig(rig, root), stylus = new Group();
  for (const frame of frames) {
    stylus.position.set(frame.tip[0], frame.tip[2], -frame.tip[1]);
    applyPhysicalPose(joints, stylus, frame);
    for (let i = 1; i <= 4; i++) {
      const a = stylus.worldToLocal(joints[`rf_tarsus${i}`].getWorldPosition(new Vector3()));
      const next = joints[`rf_tarsus${i + 1}`], b = stylus.worldToLocal(next.getWorldPosition(new Vector3()));
      assert.ok(Math.abs(a.distanceTo(b) - next.position.length()) < 1e-7);
      for (let t = 0; t <= 1; t += .05) {
        const p = a.clone().lerp(b, t);
        if (p.y >= .12 && p.y <= .625) assert.ok(Math.hypot(p.x, p.z) > .033, 'foot centerline must clear the shaft and cap');
      }
    }
  }
});
