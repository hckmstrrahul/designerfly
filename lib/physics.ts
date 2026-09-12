export interface BodyPose { position: number[]; quaternion: number[] }
export interface PhysicsFrame {
  tip: number[]; q: number[]; qvel: number[]; force: number; contact: boolean;
  torque: number[]; bodies: Record<string, BodyPose>; time: number;
  phase?: number; point?: number[]; drawing?: boolean; done?: boolean;
  stage?: string; shape?: number; stroke_index?: number; stroke_count?: number; stroke_phase?: number;
}
export interface PhysicsReport { spiking?: { available: boolean; validation: Record<string, unknown> }; motor_model?: string; reports: { 'active-motor'?: { neurons: number; after_rmse: number; ablated_rmse: number }; 'motor-validation': { scores: { untrained_rmse: number; trained_rmse: number; ablated_rmse: number } }; 'embodied-validation': { passed: boolean }; 'composition-validation'?: { passed: boolean; scores: { before_refinement_rmse: number; trained_rmse: number; ablated_rmse: number } } } }
export async function physics<T>(path: string, body?: unknown, method?: string): Promise<T> {
  const response = await fetch(`${import.meta.env.VITE_PHYSICS_URL?.replace(/\/$/,'') || '/physics'}${path}`, { method: method || (body ? 'POST' : 'GET'), headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(8000) });
  if (!response.ok) throw new Error('Drawing service unavailable. Please try again shortly.');
  return response.json();
}
