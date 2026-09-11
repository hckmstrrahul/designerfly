import fs from 'node:fs';
import crypto from 'node:crypto';

const model = JSON.parse(fs.readFileSync('public/models/circuit-refined.json'));
const cells = [], sources = [];
// Keep branch points and retain one point per ~4 microns along each branch.
// These are measured SWC centerlines; never join branches from different cells.
for (const file of fs.readdirSync('research/data/skeletons').sort()) {
  const bodyId = file.replace('.swc', ''), neuron = model.bodyIds.map(String).indexOf(bodyId);
  if (neuron < 0) continue;
  const bytes = fs.readFileSync(`research/data/skeletons/${file}`);
  const rows = bytes.toString().split('\n').filter(l => l && !l.startsWith('#')).map(l => l.trim().split(/\s+/).map(Number));
  const nodes = new Map(rows.map(r => [r[0], r])), children = new Map();
  for (const r of rows) if (nodes.has(r[6])) children.set(r[6], [...(children.get(r[6]) || []), r[0]]);
  const points = [], edges = [], indices = new Map();
  function point(row) { if (!indices.has(row[0])) { indices.set(row[0], points.length); points.push(row.slice(2, 5)); } return indices.get(row[0]); }
  for (const row of rows) {
    if (nodes.has(row[6]) && (children.get(row[0]) || []).length === 1) continue;
    for (const child of children.get(row[0]) || []) {
      let previous = row, current = nodes.get(child), distance = 0;
      while (current) {
        const branch = children.get(current[0]) || [];
        distance += Math.hypot(...current.slice(2, 5).map((v, i) => v - nodes.get(current[6])[i + 2]));
        if (distance >= 512 || branch.length !== 1) { edges.push([point(previous), point(current)]); previous = current; distance = 0; }
        current = branch.length === 1 ? nodes.get(branch[0]) : null;
      }
    }
  }
  cells.push({ bodyId, neuron, points, edges });
  sources.push({bodyId, sha256:crypto.createHash('sha256').update(bytes).digest('hex')});
}
const source = 'https://storage.googleapis.com/flyem-male-cns/v1.0/segmentation/skeletons-malecns/skeletons-swc/';
const asset = { dataset:'MaleCNS v1.0', source, license:'CC-BY-4.0', units:'8 nm', scope:'96 cached neurons belonging to the trained VNC subset; not the whole CNS', cells };
fs.writeFileSync('public/models/neural-anatomy.json', JSON.stringify(asset));
fs.writeFileSync('research/results/anatomy-manifest.json', JSON.stringify({source, sources, cells:cells.length, segments:cells.reduce((n,c)=>n+c.edges.length,0)}, null, 2));
console.log({cells:cells.length,segments:cells.reduce((n,c)=>n+c.edges.length,0),bytes:fs.statSync('public/models/neural-anatomy.json').size});
