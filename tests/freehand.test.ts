import test from 'node:test';
import assert from 'node:assert/strict';
import { freehandStroke } from '../lib/freehand.ts';
import { constrainShape } from '../lib/composition.ts';
import type { PenPoint } from '../lib/lettering.ts';
void test('freehand simplifies a straight stroke without losing its endpoints',()=>{
 const shape=freehandStroke(Array.from({length:500},(_,i)=>[-.7+i/499*1.4,.1]),1)!;
 assert.equal(shape.points!.length,2);
 const decoded=shape.points!.map(p=>[shape.x+p[0]*shape.width,shape.y+p[1]*shape.height]);
 assert.ok(Math.abs(decoded[0][0]+.7)<1e-12);assert.ok(Math.abs(decoded[1][0]-.7)<1e-12);
});
void test('freehand rejects taps and invalid points and fits oversized drawings',()=>{
 assert.equal(freehandStroke([[0,0],[0,0],[NaN,1]],1),null);
 const shape=freehandStroke([[-5,-5],[0,5],[5,-5]],1)!;
 assert.deepEqual(constrainShape(shape),shape);assert.equal(shape.width,shape.height);
 assert.ok(shape.points!.every(p=>p.every(v=>Number.isFinite(v)&&Math.abs(v)<=.500001)));
});
void test('complex freehand stays under the API point limit and preserves closed loops',()=>{
 const raw:PenPoint[]=Array.from({length:4097},(_,i)=>{const a=i/4096*Math.PI*2;return [Math.cos(a)*.7,Math.sin(a)*.7];});
 const shape=freehandStroke(raw,3)!;assert.ok(shape.points!.length<=256&&shape.points!.length>12);
 const first=shape.points![0],last=shape.points!.at(-1)!;assert.ok(Math.hypot(first[0]-last[0],first[1]-last[1])<.002);
});
