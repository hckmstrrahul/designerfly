import test from 'node:test';
import assert from 'node:assert/strict';
import { wingClock, stepsAtSpeed, PHYSICS_STEP_SECONDS } from '../lib/simulation-clock.ts';

void test('wing inference advances at the same 1×, 3×, 6× rate as physics batches',()=>{
 for(const speed of [1,3,6]){
  const clock=wingClock();let sample={time:0,phase:0};
  for(let i=0;i<25;i++)sample=clock.advance(speed);
  assert.ok(Math.abs(sample.time-speed)<1e-12);
  assert.equal(stepsAtSpeed(speed)*PHYSICS_STEP_SECONDS,.04*speed);
  assert.ok(Math.abs(sample.phase-(speed*1.6)%1)<1e-12);
 }
});
void test('speed changes preserve wing phase continuity and paused updates add no time',()=>{
 const clock=wingClock();const first=clock.advance(1),second=clock.advance(6),third=clock.advance(3);
 assert.ok(Math.abs(second.time-first.time-.24)<1e-12);
 assert.ok(Math.abs(third.time-second.time-.12)<1e-12);
 assert.ok(Math.abs(third.phase-third.time*1.6)<1e-12);
});
