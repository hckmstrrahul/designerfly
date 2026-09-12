/** One nominal update advances two 20 ms physics steps at 1×. */
export const PHYSICS_STEP_SECONDS = .02;
export const stepsAtSpeed = (speed: number) => 2 * speed;
export function wingClock() {
  let time = 0;
  return {
    advance(speed: number) {
      time += stepsAtSpeed(speed) * PHYSICS_STEP_SECONDS;
      return { time, phase: (time * 1.6) % 1 };
    },
  };
}
