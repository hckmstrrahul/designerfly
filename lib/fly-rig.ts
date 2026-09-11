import { Euler, Group, Quaternion } from 'three';

export type Rig = { rig: Record<string, { pos: [number, number, number]; quat: [number, number, number, number] }>; pose: { joint_angles: Record<string, number> } };
export function parentOf(name: string) {
  if (name === 'c_thorax') return null;
  if (name === 'c_head' || name === 'c_abdomen12' || /_(coxa|wing|haltere)$/.test(name)) return 'c_thorax';
  if (name === 'c_rostrum' || /_(eye|pedicel)$/.test(name)) return 'c_head';
  if (name === 'c_haustellum') return 'c_rostrum';
  if (name.startsWith('c_abdomen')) return name === 'c_abdomen3' ? 'c_abdomen12' : `c_abdomen${Number(name.slice(-1)) - 1}`;
  const [side, part] = name.split('_');
  const previous: Record<string, string> = { funiculus: 'pedicel', arista: 'funiculus', trochanterfemur: 'coxa', tibia: 'trochanterfemur', tarsus1: 'tibia', tarsus2: 'tarsus1', tarsus3: 'tarsus2', tarsus4: 'tarsus3', tarsus5: 'tarsus4' };
  return `${side}_${previous[part]}`;
}
export function createJointRig(data: Rig, root: Group) {
  const joints: Record<string, Group> = {};
  for (const [name, spec] of Object.entries(data.rig)) {
    const parent = parentOf(name), group = new Group(); group.name = name;
    group.position.fromArray(spec.pos); group.quaternion.set(spec.quat[1], spec.quat[2], spec.quat[3], spec.quat[0]).normalize();
    if (parent) {
      const prefix = `${parent.replace(/^r/, 'l')}-${name.replace(/^r/, 'l')}-`;
      const mirror = name.startsWith('r') ? -1 : 1, a = data.pose.joint_angles;
      group.quaternion.multiply(new Quaternion().setFromEuler(new Euler((a[`${prefix}roll`] || 0) * Math.PI / 180 * mirror, (a[`${prefix}pitch`] || 0) * Math.PI / 180, (a[`${prefix}yaw`] || 0) * Math.PI / 180 * mirror, 'ZYX')));
      joints[parent].add(group);
    } else root.add(group);
    joints[name] = group;
  }
  root.updateWorldMatrix(true, true);
  return joints;
}
