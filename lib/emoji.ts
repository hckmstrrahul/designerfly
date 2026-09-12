import { pathShape, type PlacedShape } from './composition.ts';
import type { PenPoint } from './lettering.ts';
const arc=(x:number,y:number,r:number,start=0,end=Math.PI*2):PenPoint[]=>Array.from({length:49},(_,i)=>[x+r*Math.cos(start+(end-start)*i/48),y+r*Math.sin(start+(end-start)*i/48)]);
const heart=(x:number,y:number,scale:number):PenPoint[]=>Array.from({length:65},(_,i)=>{const t=i/64*Math.PI*2;return [x+scale*16*Math.sin(t)**3,y-scale*(13*Math.cos(t)-5*Math.cos(2*t)-2*Math.cos(3*t)-Math.cos(4*t))];});
const face=()=>[arc(0,0,.7),arc(-.24,-.18,.04),arc(.24,-.18,.04)];
export const EMOJIS = [
 {id:'smile',label:'Smile',symbol:'☺',paths:[...face(),arc(0,.04,.34,0,Math.PI)]},
 {id:'wink',label:'Wink',symbol:'😉',paths:[arc(0,0,.7),arc(-.24,-.18,.04),[ [.14,-.14],[.24,-.21],[.34,-.14] ] as PenPoint[],arc(0,.04,.34,0,Math.PI)]},
 {id:'surprise',label:'Surprise',symbol:'😮',paths:[...face(),arc(0,.26,.14)]},
 {id:'cool',label:'Cool',symbol:'😎',paths:[arc(0,0,.7),[[-.55,-.22],[-.4,.02],[-.14,.02],[0,-.22],[.14,.02],[.4,.02],[.55,-.22],[-.55,-.22]] as PenPoint[],arc(0,.1,.25,0,Math.PI)]},
 {id:'heart',label:'Heart',symbol:'♡',paths:[Array.from({length:97},(_,i)=>{const t=i/96*Math.PI*2;return [.045*16*Math.sin(t)**3,-.045*(13*Math.cos(t)-5*Math.cos(2*t)-2*Math.cos(3*t)-Math.cos(4*t))] as PenPoint;})]},
 {id:'star',label:'Star',symbol:'☆',paths:[Array.from({length:11},(_,i)=>{const a=i*Math.PI/5-Math.PI/2,r=i%2?.32:.76;return [Math.cos(a)*r,Math.sin(a)*r] as PenPoint;})]},
 {id:'laugh',label:'Laugh',symbol:'😆',paths:[arc(0,0,.7),[[-.38,-.28],[-.18,-.16],[-.38,-.04]] as PenPoint[],[[.38,-.28],[.18,-.16],[.38,-.04]] as PenPoint[],[[-.34,.12],[.34,.12],...arc(0,.12,.34,0,Math.PI)] as PenPoint[]]},
 {id:'love',label:'Love',symbol:'😍',paths:[arc(0,0,.7),heart(-.25,-.18,.01),heart(.25,-.18,.01),arc(0,.1,.30,0,Math.PI)]},
 {id:'sleepy',label:'Sleepy',symbol:'😴',paths:[arc(0,0,.7),arc(-.25,-.20,.12,0,Math.PI),arc(.25,-.20,.12,0,Math.PI),arc(0,.25,.09),[[.53,-.68],[.77,-.68],[.53,-.45],[.77,-.45]] as PenPoint[]]},
 {id:'sad',label:'Sad',symbol:'☹',paths:[...face(),arc(0,.43,.26,Math.PI,Math.PI*2)]},
 {id:'sun',label:'Sun',symbol:'☀',paths:[arc(0,0,.36),...Array.from({length:8},(_,i)=>{const a=i*Math.PI/4;return [[Math.cos(a)*.50,Math.sin(a)*.50],[Math.cos(a)*.76,Math.sin(a)*.76]] as PenPoint[];})]},
 {id:'lightning',label:'Lightning',symbol:'ϟ',paths:[[[.20,-.78],[-.47,.12],[-.05,.12],[-.20,.78],[.49,-.16],[.08,-.16],[.20,-.78]] as PenPoint[]]},
];
export function emojiStudy(id:string):PlacedShape[]{
 const emoji=EMOJIS.find(e=>e.id===id);if(!emoji)throw new Error('Unknown emoji');
 return emoji.paths.map((p,i)=>pathShape(p,700+i));
}
