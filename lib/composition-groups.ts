import { constrainShape, type PlacedShape } from './composition.ts';

export function selectionBounds(shapes: PlacedShape[], selected: PlacedShape): PlacedShape {
  if (selected.groupId === undefined) return selected;
  const members = shapes.filter(s => s.groupId === selected.groupId);
  const left = Math.min(...members.map(s => s.x - s.width / 2));
  const right = Math.max(...members.map(s => s.x + s.width / 2));
  const top = Math.min(...members.map(s => s.y - s.height / 2));
  const bottom = Math.max(...members.map(s => s.y + s.height / 2));
  return { ...selected, x: (left + right) / 2, y: (top + bottom) / 2, width: right - left, height: bottom - top };
}
export function sameSelection(a: PlacedShape, b: PlacedShape) {
  return b.groupId === undefined ? a.id === b.id : a.groupId === b.groupId;
}
export function transformSelection(shapes: PlacedShape[], selected: PlacedShape, dx: number, dy: number, resize: boolean): PlacedShape[] {
  const bounds = selectionBounds(shapes, selected);
  if (selected.groupId === undefined) return shapes.map(s => s.id === selected.id ? constrainShape(resize ? {...s,width:s.width+dx*2,height:s.height+dy*2} : {...s,x:s.x+dx,y:s.y+dy}) : s);
  const scale = resize ? Math.max(.1 / Math.max(bounds.width,bounds.height), Math.min(1.72 / Math.max(bounds.width,bounds.height), 1 + (dx * bounds.width + dy * bounds.height) * 2 / (bounds.width ** 2 + bounds.height ** 2))) : 1;
  const width = bounds.width * scale, height = bounds.height * scale;
  const x = Math.max(-1+width/2,Math.min(1-width/2,bounds.x+(resize?0:dx)));
  const y = Math.max(-1+height/2,Math.min(1-height/2,bounds.y+(resize?0:dy)));
  return shapes.map(s=>sameSelection(s,selected)?validStrokeBounds({...s,x:x+(s.x-bounds.x)*scale,y:y+(s.y-bounds.y)*scale,width:s.width*scale,height:s.height*scale}):s);
}

/** Keep API bounds valid without widening small pen strokes. */
export function validStrokeBounds(s: PlacedShape): PlacedShape {
 const width=Math.max(.02,s.width),height=Math.max(.02,s.height);
 return {...s,width,height,points:s.points?.map(([x,y])=>[x*s.width/width,y*s.height/height])};
}
