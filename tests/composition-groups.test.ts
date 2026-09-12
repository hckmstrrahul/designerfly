import test from 'node:test';
import assert from 'node:assert/strict';
import { emojiStudy } from '../lib/emoji.ts';
import { sameSelection, selectionBounds, transformSelection } from '../lib/composition-groups.ts';

void test('emoji group moves and resizes as one bounded object without changing relative geometry',()=>{
 const members=emojiStudy('smile').map(s=>({...s,groupId:100}));
 const before=selectionBounds(members,members[0]);
 const moved=transformSelection(members,members[0],10,-10,false);
 const bounds=selectionBounds(moved,moved[0]);
 assert.ok(bounds.x+bounds.width/2<=1.000001);
 assert.ok(bounds.y-bounds.height/2>=-1.000001);
 members.forEach((s,i)=>assert.ok(Math.abs((moved[i].x-bounds.x)-(s.x-before.x))<1e-10));
 const resized=transformSelection(members,members[0],10,10,true);
 const after=selectionBounds(resized,resized[0]);
 const scale=after.width/before.width;
 assert.ok(Math.max(after.width,after.height)<=1.720001);
 members.forEach((s,i)=>assert.ok(Math.abs(resized[i].height-s.height*scale)<1e-10));
 assert.ok(members.every(s=>sameSelection(s,members[0])));
 assert.equal(sameSelection({...members[0],groupId:101},members[0]),false);
});
