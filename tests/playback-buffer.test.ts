import test from 'node:test';
import assert from 'node:assert/strict';
import { PlaybackBuffer } from '../lib/playback-buffer.ts';
const samples = (count: number) => Array.from({ length: count }, (_, id) => ({ id, duration: .04 }));
test('buffer preserves sample order and follows playback speed independently of arrival', () => {
  for (const speed of [1,3,6]) {
    const buffer = new PlaybackBuffer<{id:number;duration:number}>();
    buffer.push(samples(150)); const seen: number[] = [];
    for(let i=0;i<25;i++) seen.push(...buffer.take(.04*speed).map(x=>x.id));
    assert.equal(seen.length,25*speed); assert.deepEqual(seen,Array.from({length:25*speed},(_,i)=>i));
  }
});
test('stalls do not accumulate catch-up and reset discards old samples', () => {
  const buffer = new PlaybackBuffer<{id:number;duration:number}>();
  buffer.take(10); buffer.push(samples(5)); assert.equal(buffer.take(.04).length,1);
  buffer.clear(); assert.equal(buffer.seconds,0); assert.deepEqual(buffer.take(2),[]);
  buffer.push(samples(2)); assert.deepEqual(buffer.take(.04).map(x=>x.id),[0]);
});
test('speed changes preserve all queued samples and fractional timing', () => {
  const buffer = new PlaybackBuffer<{id:number;duration:number}>(); buffer.push(samples(20));
  assert.equal(buffer.take(.02).length,0); assert.equal(buffer.take(.02).length,1);
  assert.deepEqual(buffer.take(.24).map(x=>x.id),[1,2,3,4,5,6]);
  assert.deepEqual(buffer.take(.04).map(x=>x.id),[7]);
});
