import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { constrainShape, INITIAL_STUDY } from '../lib/composition.ts';

void test('moving and resizing keeps all shapes inside the trained area and circles round', () => {
  for (const shape of [0,1,2]) for (const x of [-3,-1,.3,1,3]) for (const width of [.01,.24,.83,1.72,4]) {
    const s=constrainShape({id:1,shape,x,y:-x,width,height:width/2});
    assert.ok(Math.abs(s.x)+s.width/2<=1.000001 && Math.abs(s.y)+s.height/2<=1.000001);
    assert.ok(s.width>=.24 && s.width<=1.72 && s.height>=.24 && s.height<=1.72);
    if(shape===1)assert.equal(s.width,s.height);
  }
  for(const s of INITIAL_STUDY)assert.deepEqual(constrainShape(s),s);
});
void test('held-out physical layouts finish with contact strokes and clear pen travel', () => {
  const report=JSON.parse(readFileSync(new URL('../research/results/composition-validation.json',import.meta.url),'utf8'));
  assert.equal(report.passed,true);assert.equal(report.fixed_interfaces,true);assert.equal(report.pytorch_runtime_parity,true);
  assert.equal(report.strokes,32);
  for(const s of report.results){assert.equal(s.completed,true);assert.equal(s.travel_contacts,0);assert.ok(s.rmse<.035);assert.ok(s.contact_fraction>.95);}
  assert.ok(report.scores.trained_rmse<report.scores.before_refinement_rmse);
  assert.ok(report.scores.ablated_rmse>report.scores.trained_rmse*5);
});
