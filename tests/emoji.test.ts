import test from 'node:test';
import assert from 'node:assert/strict';
import { EMOJIS, emojiStudy } from '../lib/emoji.ts';
import { constrainShape, MAX_SHAPES } from '../lib/composition.ts';
void test('every minimal emoji is a bounded, finite pen composition',()=>{
 assert.equal(EMOJIS.length,12);
 for(const emoji of EMOJIS){
  const shapes=emojiStudy(emoji.id);assert.ok(shapes.length>0&&shapes.length<=MAX_SHAPES);
  for(const shape of shapes){assert.deepEqual(constrainShape(shape),shape);assert.ok(shape.points!.length>=2&&shape.points!.length<=256);assert.ok(shape.points!.every(p=>p.every(v=>Number.isFinite(v)&&Math.abs(v)<=.500001)));}
 }
 assert.throws(()=>emojiStudy('missing'));
});
