import { Group, Quaternion, Vector3 } from 'three';

/** Presentation-only CCD. Normalize every composed rotation to prevent long-run scale drift. */
export function solveCCD(chain: Group[], end: Group, target: Vector3, iterations = 7) {
  const origin = new Vector3(), tip = new Vector3(), a = new Vector3(), b = new Vector3();
  const parentQ = new Quaternion(), delta = new Quaternion();
  for (let pass = 0; pass < iterations; pass++) for (let i = chain.length - 1; i >= 0; i--) {
    const joint = chain[i]; joint.getWorldPosition(origin); end.getWorldPosition(tip);
    a.copy(tip).sub(origin).normalize(); b.copy(target).sub(origin).normalize();
    delta.setFromUnitVectors(a, b);
    joint.parent!.getWorldQuaternion(parentQ).normalize();
    delta.premultiply(parentQ.clone().invert()).multiply(parentQ).normalize();
    joint.quaternion.premultiply(delta).normalize();
    joint.updateWorldMatrix(false, true);
  }
}
