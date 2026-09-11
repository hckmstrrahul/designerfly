import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Group, Vector3, Euler } from 'three';
import { solveCCD } from '../lib/kinematics.ts';

void test('foreleg segments retain their physical lengths through 10,000 drawing frames', () => {
  const rig = JSON.parse(readFileSync(new URL('../public/models/fly/rig.json', import.meta.url), 'utf8'));
  const root = new Group(); root.rotation.x = -Math.PI / 2; root.position.set(-.3, 0, 0);
  const thorax = new Group(); thorax.position.fromArray(rig.rig.c_thorax.pos); root.add(thorax);
  let parent = thorax, parentName = 'c_thorax'; const joints: Group[] = [];
  for (const part of ['coxa', 'trochanterfemur', 'tibia', 'tarsus1', 'tarsus2', 'tarsus3']) {
    const name = `rf_${part}`, group = new Group(); group.position.fromArray(rig.rig[name].pos);
    const prefix = `${parentName.replace(/^r/, 'l')}-${name.replace(/^r/, 'l')}-`, angles = rig.pose.joint_angles;
    group.quaternion.setFromEuler(new Euler(-(angles[prefix + 'roll'] || 0) * Math.PI / 180, (angles[prefix + 'pitch'] || 0) * Math.PI / 180, -(angles[prefix + 'yaw'] || 0) * Math.PI / 180, 'ZYX'));
    parent.add(group); parent = group; parentName = name; joints.push(group);
  }
  const end = joints.at(-1)!, chain = joints.slice(0, -1), p = new Vector3(), q = new Vector3();
  let worstError = 0;
  for (let frame = 0; frame < 10000; frame++) {
    const phase = frame / 300 * Math.PI * 2;
    const target = new Vector3(1.35 + Math.sin(phase) * .4, 1.25, Math.cos(phase) * .45);
    solveCCD(chain, end, target);
    if (frame > 20) worstError = Math.max(worstError, end.getWorldPosition(p).distanceTo(target));
    for (const joint of joints) {
      assert.ok(Math.abs(joint.quaternion.length() - 1) < 1e-10);
      joint.getWorldPosition(p); joint.parent!.getWorldPosition(q);
      assert.ok(Math.abs(p.distanceTo(q) - joint.position.length()) < 1e-8, 'segment geometry must not stretch');
    }
  }
  assert.ok(worstError < .04, `grip error ${worstError}`);
});
