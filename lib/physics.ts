export interface BodyPose { position: number[]; quaternion: number[] }
export interface PhysicsFrame {
  tip: number[]; q: number[]; qvel: number[]; force: number; contact: boolean;
  torque: number[]; bodies: Record<string, BodyPose>; time: number;
  phase?: number; point?: number[]; drawing?: boolean; done?: boolean;
  stage?: string; shape?: number; stroke_index?: number; stroke_count?: number; stroke_phase?: number;
}
export interface PhysicsReport { motor_model?: string; reports: { 'active-motor'?: { neurons: number; after_rmse: number; ablated_rmse: number }; 'motor-validation': { scores: { untrained_rmse: number; trained_rmse: number; ablated_rmse: number } }; 'embodied-validation': { passed: boolean }; 'composition-validation'?: { passed: boolean; scores: { before_refinement_rmse: number; trained_rmse: number; ablated_rmse: number } } } }
export async function physics<T>(path: string, body?: unknown, method?: string): Promise<T> {
  const response = await fetch(`/physics${path}`, { method: method || (body ? 'POST' : 'GET'), headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(8000) });
  if (!response.ok) throw new Error('Physics service unavailable. Start it with npm run physics, then reload.');
  return response.json();
}
