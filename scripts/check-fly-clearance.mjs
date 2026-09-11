import fs from 'node:fs';
import { Group, Mesh, MeshBasicMaterial, Vector3, Raycaster, DoubleSide } from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { createJointRig } from '../lib/fly-rig.ts';
import { plantLeg, applyPhysicalPose } from '../lib/fly-pose.ts';

const root = new Group(); root.rotation.x = -Math.PI / 2; root.position.x = -.3;
const data = JSON.parse(fs.readFileSync('public/models/fly/rig.json'));
const joints = createJointRig(data, root), solids = [];
for (const name of ['c_thorax', 'c_head', 'c_abdomen12', 'c_abdomen3', 'c_abdomen4', 'c_abdomen5', 'c_abdomen6', 'l_eye', 'r_eye']) {
  const bytes = fs.readFileSync(`public/models/fly/${name.replace(/^r/, 'l')}.stl`);
  const geometry = new STLLoader().parse(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
  geometry.scale(1000, name.startsWith('r') ? -1000 : 1000, 1000);
  const mesh = new Mesh(geometry, new MeshBasicMaterial({ side: DoubleSide })); mesh.name = name; joints[name].add(mesh); solids.push(mesh);
}
for (const side of ['lf', 'lm', 'lh', 'rm', 'rh']) plantLeg(joints, side);
root.updateWorldMatrix(true, true);
// Positive control: the detector must report a point inside the thorax.
solids[0].geometry.computeBoundingBox();
const center = solids[0].localToWorld(solids[0].geometry.boundingBox.getCenter(new Vector3()));
const controlHits = new Raycaster(center, new Vector3(1, 0, 0)).intersectObject(solids[0], false);
if (!controlHits.length) throw new Error('Collision probe positive control failed');
const hits = [];
let vertexProbes = 0;
for (const side of ['lf', 'lm', 'lh', 'rm', 'rh']) {
  const names = ['trochanterfemur', 'tibia', 'tarsus1', 'tarsus2', 'tarsus3', 'tarsus4', 'tarsus5'];
  for (let i = 0; i < names.length - 1; i++) {
    const a = joints[`${side}_${names[i]}`].getWorldPosition(new Vector3()), b = joints[`${side}_${names[i + 1]}`].getWorldPosition(new Vector3());
    const direction = b.clone().sub(a).normalize(), length = a.distanceTo(b);
    // Parallel probes around the segment check a conservative 0.035 mm limb envelope.
    const u = new Vector3(0, 1, 0).cross(direction).normalize(), v = direction.clone().cross(u);
    for (let probe = 0; probe < 9; probe++) {
      const angle = probe * Math.PI / 4, offset = probe === 8 ? new Vector3() : u.clone().multiplyScalar(Math.cos(angle) * .035).addScaledVector(v, Math.sin(angle) * .035);
      const ray = new Raycaster(a.clone().add(offset), direction, .002, length - .002);
      const collisions = ray.intersectObjects(solids, false);
      if (collisions.length) hits.push({ side, segment: names[i], body: collisions[0].object.name });
    }
  }
  for (const part of names) {
    const bytes = fs.readFileSync(`public/models/fly/${side.replace(/^r/, 'l')}_${part}.stl`);
    const geometry = new STLLoader().parse(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
    geometry.scale(1000, side.startsWith('r') ? -1000 : 1000, 1000);
    const points = geometry.getAttribute('position'), joint = joints[`${side}_${part}`];
    for (let i = 0; i < points.count; i += 57) {
      vertexProbes++;
      const p = joint.localToWorld(new Vector3().fromBufferAttribute(points, i));
      for (const solid of solids) {
        const ray = new Raycaster(p, new Vector3(.937, .231, .263).normalize());
        const intersections = ray.intersectObject(solid, false).map(h => h.distance);
        const unique = intersections.filter((d, index) => index === 0 || d - intersections[index - 1] > .000001);
        if (unique.length % 2) hits.push({side, segment:part, body:solid.name, vertex:i});
      }
    }
  }
}
console.log(JSON.stringify({ probes: 270, vertexProbes, intersections: hits }, null, 2));
const poseFile = process.argv[2] || 'research/results/pose-check.json';
if (fs.existsSync(poseFile)) {
  const frames = JSON.parse(fs.readFileSync(poseFile));
  const stylus = new Group();
  const samples = {};
  for (const part of ['trochanterfemur', 'tibia', 'tarsus1', 'tarsus2', 'tarsus3', 'tarsus4', 'tarsus5']) {
    const bytes = fs.readFileSync(`public/models/fly/lf_${part}.stl`);
    const geometry = new STLLoader().parse(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
    geometry.scale(1000, -1000, 1000);
    const p = geometry.getAttribute('position'); samples[part] = [];
    for (let i = 0; i < p.count; i += 171) samples[part].push(new Vector3().fromBufferAttribute(p, i));
  }
  const movingHits = [];
  for (const frame of frames) {
    const tip = frame.tip; stylus.position.set(tip[0], tip[2], -tip[1]);
    applyPhysicalPose(joints, stylus, frame);
    for (const [part, points] of Object.entries(samples)) for (const local of points) {
      const p = joints[`rf_${part}`].localToWorld(local.clone());
      for (const solid of solids) {
        const ray = new Raycaster(p, new Vector3(.937, .231, .263).normalize());
        const intersections = ray.intersectObject(solid, false).map(h => h.distance);
        const unique = intersections.filter((d, index) => index === 0 || d - intersections[index - 1] > .000001);
        if (unique.length % 2) movingHits.push({time:frame.time, segment:part, body:solid.name});
      }
    }
  }
  console.log(JSON.stringify({physicalFrames:frames.length,movingIntersections:movingHits.slice(0,20),total:movingHits.length},null,2));
  hits.push(...movingHits);
}
if (hits.length) process.exitCode = 1;
