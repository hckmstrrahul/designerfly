type Position = readonly number[] | null;

/** Orthographic anatomical projection, uniformly fitted to both screen dimensions. */
export function fitNeuralProjection(positions: Position[], width: number, height: number) {
  const angle = .38;
  const raw = positions.map(p => p ? [p[0] * Math.cos(angle) - p[1] * Math.sin(angle), p[2] + p[1] * .18] : null);
  const valid = raw.filter((p): p is number[] => p !== null);
  if (!valid.length) return raw;
  let left = Infinity, right = -Infinity, top = Infinity, bottom = -Infinity;
  for (const p of valid) { left = Math.min(left, p[0]); right = Math.max(right, p[0]); top = Math.min(top, p[1]); bottom = Math.max(bottom, p[1]); }
  const scale = Math.min(Math.max(1, width - 36) / Math.max(1, right - left), Math.max(1, height - 32) / Math.max(1, bottom - top));
  return raw.map(p => p ? [width / 2 + (p[0] - (left + right) / 2) * scale, height / 2 + (p[1] - (top + bottom) / 2) * scale] : null);
}
