/** Hue encodes sign; opacity and glow encode strength, not neurotransmitter identity. */
export function activityColor(value: number): string {
  return value < 0 ? 'rgb(239,83,70)' : value > 0 ? 'rgb(94,207,105)' : 'rgb(62,88,65)';
}
export const CELL_COLORS: Record<string, string> = { vnc_sensory: '#73c9e8', vnc_intrinsic: '#bd9ee8', vnc_motor: '#f2bd73' };
/** Actual frame-to-frame change, with fixed 8× visual gain. */
export function activityChange(current: number, previous: number) { return Math.min(1, Math.abs(current - previous) * 8); }
