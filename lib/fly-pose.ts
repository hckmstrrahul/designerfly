import { Group, Quaternion, Vector3 } from 'three';
import type { PhysicsFrame } from './physics';

const nativeToWorld = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), -Math.PI / 2);
const meshToBody = new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), -Math.PI / 2);

export function applyPhysicalPose(joints: Record<string, Group>, stylus: Group, frame: PhysicsFrame) {
  for (const [body, jointName] of [['femur', 'rf_trochanterfemur'], ['tibia', 'rf_tibia']]) {
    const pose = frame.bodies[body], joint = joints[jointName]; if (!pose || !joint) continue;
    const [w, x, y, z] = pose.quaternion;
    const worldQ = nativeToWorld.clone().multiply(new Quaternion(x, y, z, w)).multiply(meshToBody);
    const worldP = new Vector3().fromArray(pose.position).applyQuaternion(nativeToWorld);
    joint.position.copy(joint.parent!.worldToLocal(worldP));
    joint.quaternion.copy(joint.parent!.getWorldQuaternion(new Quaternion()).invert()).multiply(worldQ).normalize();
    joint.updateWorldMatrix(false, true);
  }
  const pose = frame.bodies.tibia;
  if (pose) {
    const [w, x, y, z] = pose.quaternion;
    const axis = new Vector3(-1, 0, 0).applyQuaternion(new Quaternion(x, y, z, w)).applyQuaternion(nativeToWorld);
    stylus.quaternion.setFromUnitVectors(new Vector3(0, 1, 0), axis);
  }
  gripStylus(joints, stylus);
}

export function aimJoint(joint: Group, childOffset: Vector3, direction: Vector3) {
  joint.quaternion.copy(joint.parent!.getWorldQuaternion(new Quaternion()).invert())
    .multiply(new Quaternion().setFromUnitVectors(childOffset.clone().normalize(), direction.clone().normalize()));
  joint.updateWorldMatrix(false, true);
}

/** Fixed-length two-bone stance. The pole keeps the knee on the outside of the body. */
export function plantLeg(joints: Record<string, Group>, side: string) {
  const sign = side.startsWith('l') ? -1 : 1;
  const front = side[1] === 'f';
  const coxa = joints[`${side}_coxa`], femur = joints[`${side}_trochanterfemur`];
  const tibia = joints[`${side}_tibia`], ankle = joints[`${side}_tarsus1`];
  // Front support leg exits laterally below the head before bending toward
  // the floor. Its elbow must never reach across the body's midline.
  aimJoint(coxa, femur.position, new Vector3(front ? -.025 : -.07, front ? -.16 : -.22, sign * (front ? .44 : .32)));
  const a = femur.getWorldPosition(new Vector3());
  const c = front ? new Vector3(.47, .05, sign * 1.22) : new Vector3(side[1] === 'm' ? -.35 : -1.25, .05, sign * 1.16);
  const l1 = tibia.position.length(), l2 = ankle.position.length();
  const axis = c.clone().sub(a); const d = Math.min(axis.length(), l1 + l2 - .001); axis.normalize();
  const along = (l1 * l1 - l2 * l2 + d * d) / (2 * d);
  const pole = new Vector3(front ? .55 : -.4, .15, sign);
  pole.addScaledVector(axis, -pole.dot(axis)).normalize();
  const b = a.clone().addScaledVector(axis, along).addScaledVector(pole, Math.sqrt(Math.max(0, l1 * l1 - along * along)));
  aimJoint(femur, tibia.position, b.clone().sub(a));
  aimJoint(tibia, ankle.position, c.clone().sub(b));
  aimJoint(ankle, joints[`${side}_tarsus2`].position, new Vector3(.65, -.015, sign * .2));
  for (let i = 2; i <= 5; i++) joints[`${side}_tarsus${i}`].quaternion.identity();
}

/** Rigidly attached stylus: the segmented tarsus wraps its shaft, without moving the physical tip. */
export function gripStylus(joints: Record<string, Group>, stylus: Group) {
  stylus.updateWorldMatrix(true, false);
  // Preserve every segment length. Approach beside the cap, descend along the
  // shaft, then curl around its exterior (shaft radius .023, foot radius .045).
  // A fly has a segmented tarsus, not opposing human fingers.
  const angles = [0, .15, 1.45, 2.65], radius = .045;
  for (let i = 1; i <= 4; i++) {
    const joint = joints[`rf_tarsus${i}`], next = joints[`rf_tarsus${i + 1}`];
    const start = stylus.worldToLocal(joint.getWorldPosition(new Vector3()));
    const target = new Vector3(radius * Math.cos(angles[i - 1]), 0, radius * Math.sin(angles[i - 1]));
    const sideways = (target.x - start.x) ** 2 + (target.z - start.z) ** 2;
    target.y = start.y - Math.sqrt(Math.max(0, next.position.lengthSq() - sideways));
    stylus.localToWorld(target);
    aimJoint(joint, next.position, target.sub(joint.getWorldPosition(new Vector3())));
  }
  const claw = joints.rf_tarsus5.getWorldPosition(new Vector3());
  const local = stylus.worldToLocal(claw.clone());
  aimJoint(joints.rf_tarsus5, new Vector3(0, 0, -1), stylus.localToWorld(new Vector3(-.012, local.y - .045, -.045)).sub(claw));
}
