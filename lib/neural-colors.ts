/** Fixed signed rate scale; color does not imply neurotransmitter identity. */
export function activityColor(value: number): string {
  const v = Math.max(-1, Math.min(1, value));
  const neutral = [143, 165, 158], end = v < 0 ? [99, 175, 249] : [255, 139, 103];
  return `rgb(${neutral.map((n, i) => Math.round(n + (end[i] - n) * Math.abs(v))).join(',')})`;
}
export const CELL_COLORS: Record<string, string> = { vnc_sensory: '#73c9e8', vnc_intrinsic: '#bd9ee8', vnc_motor: '#f2bd73' };
/** Actual frame-to-frame change, with fixed 8× visual gain. */
export function activityChange(current: number, previous: number) { return Math.min(1, Math.abs(current - previous) * 8); }
