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
round(0,-.72,1.62,.22);
line([-.67,-.73],[-.6,-.73]);line([.53,-.77],[.57,-.73],[.53,-.69]);
round(0,-.22,1.62,.50,.05);
line([-.73,-.12],[-.40,-.39],[-.13,-.16],[.19,-.35],[.73,.01]);
round(.48,-.37,.13,.13,.06);
for(const x of [-.44,.44]){
 round(x,.42,.74,.68,.045);
 round(x,.30,.60,.28,.025);
 line([x-.27,.39],[x-.10,.22],[x+.03,.33],[x+.14,.25],[x+.27,.39]);
 line([x-.27,.54],[x+.22,.54]);line([x-.27,.64],[x+.04,.64]);
}
line([-.80,.86],[.30,.86]);round(.63,.86,.34,.16,.07);
// The masthead uses the exact same supplied lettering paths as the text tool.
for(const p of letteringPaths('FLY'))examplePaths.push(p.map(([x,y])=>[x*.42,y*.42-.90]));
export const UI_EXAMPLE:PlacedShape[]=examplePaths.map((p,i)=>pathShape(p,101+i));
