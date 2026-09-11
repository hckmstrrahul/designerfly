import * as T from 'three';

/** Small procedural surface maps; all anatomical silhouettes still come from FlyGym. */
export function flySurfaceMaps() {
  const make = (draw: (ctx: CanvasRenderingContext2D) => void) => {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 512;
    draw(canvas.getContext('2d')!); const map = new T.CanvasTexture(canvas); map.wrapS = map.wrapT = T.RepeatWrapping; return map;
  };
  let seed = 916;
  const random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
  const cuticle = make(ctx => {
    ctx.fillStyle = '#aaa'; ctx.fillRect(0, 0, 512, 512);
    for (let i = 0; i < 18000; i++) { const v = Math.round(145 + random() * 45); ctx.fillStyle = `rgb(${v},${v},${v})`; ctx.fillRect(random() * 512, random() * 512, 1, 1); }
    ctx.strokeStyle = '#989898'; ctx.lineWidth = .5;
    for (let i = 0; i < 75; i++) { const x = random() * 512, y = random() * 512; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 5, y + 18); ctx.stroke(); }
  });
  const facets = make(ctx => {
    ctx.fillStyle = '#666'; ctx.fillRect(0, 0, 512, 512);
    const radius = 6, step = Math.sqrt(3) * radius;
    for (let row = -1; row < 59; row++) for (let col = -1; col < 52; col++) {
      const x = col * step + (row % 2) * step / 2, y = row * radius * 1.5;
      const gradient = ctx.createRadialGradient(x - 1, y - 1, .5, x, y, radius);
      gradient.addColorStop(0, '#d2d2d2'); gradient.addColorStop(.7, '#b2b2b2'); gradient.addColorStop(1, '#747474'); ctx.fillStyle = gradient;
      ctx.beginPath(); for (let j = 0; j < 6; j++) { const a = (j * 60 + 30) * Math.PI / 180; const px = x + Math.cos(a) * radius, py = y + Math.sin(a) * radius; if (j) ctx.lineTo(px, py); else ctx.moveTo(px, py); } ctx.closePath(); ctx.fill();
    }
  });
  const veins = make(ctx => {
    ctx.fillStyle = '#e2e8db'; ctx.fillRect(0, 0, 512, 512);
    ctx.strokeStyle = '#879887'; ctx.lineCap = 'round'; ctx.lineWidth = 1.4;
    // Longitudinal veins and sparse cross-veins, drawn in span/chord UV coordinates.
    for (const end of [62, 152, 269, 381, 454]) { ctx.beginPath(); ctx.moveTo(254, 505); ctx.bezierCurveTo(245, 370, end, 230, end, 8); ctx.stroke(); }
    ctx.lineWidth = .8; for (const [a, b, y] of [[171, 281, 228], [290, 399, 132]]) { ctx.beginPath(); ctx.moveTo(a, y); ctx.quadraticCurveTo((a + b) / 2, y - 17, b, y + 5); ctx.stroke(); }
    for (let i = 0; i < 4000; i++) { ctx.fillStyle = '#899a8522'; ctx.fillRect(random() * 512, random() * 512, .6, .6); }
  }); veins.colorSpace = T.SRGBColorSpace;
  return { cuticle, facets, veins, dispose: () => { cuticle.dispose(); facets.dispose(); veins.dispose(); } };
}

export function surfaceUV(geometry: T.BufferGeometry, wing = false, mirroredWing = false) {
  geometry.computeBoundingBox(); const b = geometry.boundingBox!, center = b.getCenter(new T.Vector3()), size = b.getSize(new T.Vector3());
  const p = geometry.getAttribute('position'), uv: number[] = [];
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    if (wing) { const span = (y - b.min.y) / size.y; uv.push((x - b.min.x) / size.x, mirroredWing ? 1 - span : span); }
    else uv.push(.5 + Math.atan2(y - center.y, x - center.x) / (2 * Math.PI), .5 + Math.asin(T.MathUtils.clamp((z - center.z) / (size.z * .51), -1, 1)) / Math.PI);
  }
  geometry.setAttribute('uv', new T.Float32BufferAttribute(uv, 2));
}

/** Relax only coarse segmentation noise; keep the source mesh topology. */
export function softenSurface(geometry: T.BufferGeometry) {
  const p = geometry.getAttribute('position'), index = geometry.index; if (!index) return;
  const neighbors = Array.from({ length: p.count }, () => new Set<number>());
  for (let i = 0; i < index.count; i += 3) { const a = index.getX(i), b = index.getX(i + 1), c = index.getX(i + 2); neighbors[a].add(b).add(c); neighbors[b].add(a).add(c); neighbors[c].add(a).add(b); }
  for (let pass = 0; pass < 2; pass++) {
    const next = new Float32Array(p.count * 3);
    neighbors.forEach((ns, i) => { const average = new T.Vector3(); ns.forEach(j => average.add(new T.Vector3().fromBufferAttribute(p, j))); if (ns.size) average.divideScalar(ns.size); else average.fromBufferAttribute(p, i); average.lerp(new T.Vector3().fromBufferAttribute(p, i), .82); average.toArray(next, i * 3); });
    for (let i = 0; i < p.count; i++) p.setXYZ(i, next[i * 3], next[i * 3 + 1], next[i * 3 + 2]);
  }
  geometry.computeVertexNormals();
}
