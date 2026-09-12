import { clamp, constrainShape, pathShape, type PlacedShape } from './composition.ts';
import type { PenPoint } from './lettering.ts';

const distance=(p:PenPoint,a:PenPoint,b:PenPoint)=>{
 const dx=b[0]-a[0],dy=b[1]-a[1],length=dx*dx+dy*dy;
 const t=length ? clamp(((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length,0,1) : 0;
 return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);
};
function simplify(points:PenPoint[],tolerance:number):PenPoint[]{
 const keep=new Set([0,points.length-1]), stack:[[number,number]]|[number,number][]=[[0,points.length-1]];
 while(stack.length){const [start,end]=stack.pop()!;let greatest=tolerance,index=-1;
  for(let i=start+1;i<end;i++){const d=distance(points[i],points[start],points[end]);if(d>greatest){greatest=d;index=i;}}
  if(index!==-1){keep.add(index);stack.push([start,index],[index,end]);}
 }
 return [...keep].sort((a,b)=>a-b).map(i=>points[i]);
}
/** Supplied freehand geometry. Remove sub-pixel jitter and fit the supported workspace. */
export function freehandStroke(raw:PenPoint[],id:number):PlacedShape|null {
 const points:PenPoint[]=[];
 for(const p of raw){if(!p.every(Number.isFinite))continue;const q:PenPoint=[clamp(p[0],-.98,.98),clamp(p[1],-.98,.98)];
  const last=points.at(-1);if(!last||Math.hypot(q[0]-last[0],q[1]-last[1])>.001)points.push(q);
 }
 if(points.length<2)return null;
 const length=points.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p[0]-points[i][0],p[1]-points[i][1]),0);
 if(length<.012)return null;
 let tolerance=.006,clean=simplify(points,tolerance);
 while(clean.length>256){tolerance*=1.5;clean=simplify(points,tolerance);}
 const shape=pathShape(clean,id),scale=Math.min(1,1.72/Math.max(shape.width,shape.height));
 return constrainShape({...shape,width:shape.width*scale,height:shape.height*scale});
}
