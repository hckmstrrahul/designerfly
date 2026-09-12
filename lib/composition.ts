import { letteringPaths, type PenPoint } from './lettering.ts';
export interface PlacedShape { id: number; groupId?: number; groupLabel?: string; shape: number; x: number; y: number; width: number; height: number; variant?: 'square' | 'ellipse'; points?: PenPoint[] }
export const MAX_SHAPES = 128;
export const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
export function constrainShape(s: PlacedShape): PlacedShape {
  const width = clamp(s.width, s.points ? .02 : .24, 1.72), height = (s.shape === 1 && s.variant !== 'ellipse') || s.variant === 'square' ? width : clamp(s.height, s.points ? .02 : .24, 1.72);
  return { ...s, width, height, x: clamp(s.x, -1 + width / 2, 1 - width / 2), y: clamp(s.y, -1 + height / 2, 1 - height / 2) };
}
export const INITIAL_STUDY: PlacedShape[] = [
  { id: 1, shape: 0, x: 0, y: -.64, width: 1.55, height: .28 },
  { id: 2, shape: 1, x: -.52, y: -.03, width: .43, height: .43 },
  { id: 3, shape: 0, x: .29, y: -.03, width: .78, height: .43 },
  { id: 4, shape: 0, x: 0, y: .6, width: 1.55, height: .38 },
];
/** Local path coordinates preserve movement and resizing in the editor. */
export function pathShape(points: PenPoint[], id: number): PlacedShape {
 const xs=points.map(p=>p[0]), ys=points.map(p=>p[1]);
 const x=(Math.min(...xs)+Math.max(...xs))/2,y=(Math.min(...ys)+Math.max(...ys))/2;
 const width=Math.max(.02,Math.max(...xs)-Math.min(...xs)),height=Math.max(.02,Math.max(...ys)-Math.min(...ys));
 return {id,shape:0,x,y,width,height,points:points.map(p=>[(p[0]-x)/width,(p[1]-y)/height])};
}
export const textStudy = (text: string): PlacedShape[] => letteringPaths(text).map((p,i)=>pathShape(p,500+i));
export function roundedRect(x:number,y:number,w:number,h:number,r=.035): PenPoint[] {
 const points:PenPoint[]=[];
 for(const [cx,cy,start] of [[x+w/2-r,y-h/2+r,-90],[x+w/2-r,y+h/2-r,0],[x-w/2+r,y+h/2-r,90],[x-w/2+r,y-h/2+r,180]])
  for(let i=0;i<=8;i++){const a=(start+i*90/8)*Math.PI/180;points.push([cx+r*Math.cos(a),cy+r*Math.sin(a)]);}
 return [...points,points[0]];
}
/** Authored editorial UI; every visible detail becomes a physical pen stroke. */
const examplePaths:PenPoint[][]=[];
const round=(x:number,y:number,w:number,h:number,r=.035)=>examplePaths.push(roundedRect(x,y,w,h,r));
const line=(...p:PenPoint[])=>examplePaths.push(p);
// Even vertical gutters between masthead, search, feature, cards and footer.
round(0,-.64,1.72,.20);
line([-.72,-.64],[-.63,-.64]);line([.68,-.68],[.72,-.64],[.68,-.60]);
round(0,-.16,1.72,.52,.04);
line([-.77,.01],[-.43,-.33],[-.09,-.04],[.27,-.28],[.77,.01]);
round(.57,-.29,.13,.13,.06);
for(const x of [-.46,.46]){
 round(x,.45,.80,.50,.035);
 round(x,.37,.66,.20,.025);
 line([x-.28,.43],[x-.11,.30],[x+.03,.40],[x+.14,.32],[x+.28,.43]);
 line([x-.28,.54],[x+.25,.54]);line([x-.28,.62],[x+.07,.62]);
}
line([-.85,.84],[.31,.84]);round(.65,.84,.42,.14,.065);
// One-line masthead, using the same vector alphabet as the text tool.
const masthead=letteringPaths('THE TIMES OF FLIES',40);
const titlePoints=masthead.flat(), titleXs=titlePoints.map(p=>p[0]), titleYs=titlePoints.map(p=>p[1]);
const titleLeft=Math.min(...titleXs), titleRight=Math.max(...titleXs), titleTop=Math.min(...titleYs), titleBottom=Math.max(...titleYs);
for(const p of masthead)examplePaths.push(p.map(([x,y])=>[(x-(titleLeft+titleRight)/2)*1.64/(titleRight-titleLeft),(y-(titleTop+titleBottom)/2)*.10/(titleBottom-titleTop)-.89]));
export const UI_EXAMPLE:PlacedShape[]=examplePaths.map((p,i)=>pathShape(p,101+i));

/** Match editor primitives to the supplied-path motor route used by emojis. */
export function drawingStroke(s: PlacedShape): PlacedShape {
 if (s.points) return s;
 let points: PenPoint[];
 if (s.shape === 0) points = [[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5],[-.5,-.5]];
 else if (s.shape === 1) {
  points = Array.from({length:128},(_,i)=>{
   const angle=i*Math.PI*2/128;
   return [Math.cos(angle)*.5,Math.sin(angle)*.5] as PenPoint;
  });
  points.push([...points[0]]);
 } else points = [[0,-.5],[.5,.5],[-.5,.5],[0,-.5]];
 return {...s,points};
}
