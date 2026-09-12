import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { constrainShape, INITIAL_STUDY, UI_EXAMPLE, MAX_SHAPES } from '../lib/composition.ts';

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
void test('ellipse preserves independent axes while square preserves equal sides', () => {
  const ellipse=constrainShape({id:1,shape:1,variant:'ellipse',x:2,y:2,width:.8,height:.4});
  assert.equal(ellipse.width,.8);assert.equal(ellipse.height,.4);
  assert.ok(ellipse.x+ellipse.width/2<=1 && ellipse.y+ellipse.height/2<=1);
  const square=constrainShape({id:2,shape:0,variant:'square',x:0,y:0,width:.6,height:.3});
  assert.equal(square.width,square.height);
});

void test('UI example fits the physical workspace and has unique stroke IDs', () => {
  assert.ok(UI_EXAMPLE.length<=MAX_SHAPES);
  assert.equal(new Set(UI_EXAMPLE.map(s=>s.id)).size,UI_EXAMPLE.length);
  for(const s of UI_EXAMPLE) assert.deepEqual(constrainShape(s),s);
});

void test('lettering is bounded, supports line breaks and rejects unsupported input', async () => {
 const {textStudy}=await import('../lib/composition.ts');
 const {validText}=await import('../lib/lettering.ts');
 for(const text of ['HELLO\nWORLD','ABCDEFGHIJKLMNOPQRST','0123456789 .!?-','A\nB\nC\nD\nE']){
  const strokes=textStudy(text);assert.ok(strokes.length>0&&strokes.length<=MAX_SHAPES);
  for(const s of strokes){assert.deepEqual(constrainShape(s),s);assert.ok(s.points!.every(p=>p.every(v=>Number.isFinite(v)&&Math.abs(v)<=.500001)));}
 }
 assert.equal(validText('a short name'),true);assert.equal(validText('é'),false);assert.equal(validText('x'.repeat(40)),true);assert.equal(validText('x'.repeat(41)),false);
});

void test('40 high-stroke letters fit the drawing budget and workspace', async()=>{
 const {textStudy,MAX_SHAPES}=await import('../lib/composition.ts');
 const shapes=textStudy('H'.repeat(40));
 assert.equal(shapes.length,120);
 assert.ok(shapes.length<=MAX_SHAPES);
 for(const s of shapes) for(const [x,y] of s.points!){
  assert.ok(Math.abs(s.x+x*s.width)<=1);
  assert.ok(Math.abs(s.y+y*s.height)<=1);
 }
});

void test('UI primitives send closed preview geometry while authored ink is unchanged', async()=>{
 const {drawingStroke}=await import('../lib/composition.ts');
 for(const shape of [0,1,2]){
  const original={id:1,shape,x:.2,y:-.1,width:.8,height:.4};
  const stroke=drawingStroke(original);
  assert.deepEqual(stroke.points![0],stroke.points!.at(-1));
  assert.equal(stroke.width,original.width);assert.equal(stroke.height,original.height);
  for(const p of stroke.points!)assert.ok(p.every(v=>Math.abs(v)<=.5));
  if(shape===0)assert.deepEqual(stroke.points, [[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5],[-.5,-.5]]);
  if(shape===1)for(const [x,y] of stroke.points!)assert.ok(Math.abs(x*x+y*y-.25)<1e-12);
 }
 for(const stroke of UI_EXAMPLE)assert.equal(drawingStroke(stroke),stroke);
});
