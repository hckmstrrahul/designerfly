import test from 'node:test';
import assert from 'node:assert/strict';
import { CAMERA_PRESETS, cameraPresetIndex } from '../lib/camera-presets.ts';
void test('saved camera choices are bounded and invalid storage falls back to angled',()=>{
 for(const [value,index] of [['0',0],['1',1],['2',2],[null,0],['3',0],['-1',0],['NaN',0],['',0]] as const)assert.equal(cameraPresetIndex(value),index);
 assert.deepEqual(CAMERA_PRESETS.map(p=>p.name),['Angled','Paper','Overhead']);
 assert.ok(CAMERA_PRESETS[1].zoom>CAMERA_PRESETS[0].zoom*2);
 const overhead=CAMERA_PRESETS[2];assert.equal(overhead.position[0],overhead.target[0]);assert.ok(Math.abs(overhead.position[2]-overhead.target[2])<.01);
});
