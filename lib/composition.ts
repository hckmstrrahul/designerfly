export interface PlacedShape { id: number; shape: number; x: number; y: number; width: number; height: number }
export const MAX_SHAPES = 8;
export const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
export function constrainShape(s: PlacedShape): PlacedShape {
  const width = clamp(s.width, .24, 1.72), height = s.shape === 1 ? width : clamp(s.height, .24, 1.72);
  return { ...s, width, height, x: clamp(s.x, -1 + width / 2, 1 - width / 2), y: clamp(s.y, -1 + height / 2, 1 - height / 2) };
}
export const INITIAL_STUDY: PlacedShape[] = [
  { id: 1, shape: 0, x: 0, y: -.64, width: 1.55, height: .28 },
  { id: 2, shape: 1, x: -.52, y: -.03, width: .43, height: .43 },
  { id: 3, shape: 0, x: .29, y: -.03, width: .78, height: .43 },
  { id: 4, shape: 0, x: 0, y: .6, width: 1.55, height: .38 },
];
/** A hand-authored, editable wireframe. The controller executes this specification. */
export const SEARCH_FEED: PlacedShape[] = [
  { id: 101, shape: 0, x: 0, y: -.72, width: 1.64, height: .28 },
  { id: 102, shape: 1, x: -.65, y: -.15, width: .28, height: .28 },
  { id: 103, shape: 0, x: .2, y: -.15, width: 1.2, height: .38 },
  { id: 104, shape: 1, x: -.65, y: .39, width: .28, height: .28 },
  { id: 105, shape: 0, x: .2, y: .39, width: 1.2, height: .38 },
  { id: 106, shape: 0, x: 0, y: .8, width: 1.64, height: .24 },
];
