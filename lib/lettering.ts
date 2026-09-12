/** Original single-stroke alphabet. These are supplied pen paths, not learned language. */
export type PenPoint = [number, number];
const glyphs: Record<string, string> = {
 A:'04 20 44|12 32', B:'04 00 30 41 32 02|32 43 34 04', C:'40 10 01 03 14 44',
 D:'04 00 20 41 43 24 04', E:'40 00 04 44|02 32', F:'04 00 40|02 32',
 G:'40 10 01 03 14 44 42 22', H:'00 04|40 44|02 42', I:'00 40|20 24|04 44',
 J:'00 40 43 34 14 03', K:'00 04|40 02 44', L:'00 04 44', M:'04 00 22 40 44',
 N:'04 00 44 40', O:'10 30 41 43 34 14 03 01 10', P:'04 00 30 41 32 02',
 Q:'10 30 41 43 34 14 03 01 10|23 44', R:'04 00 30 41 32 02|22 44',
 S:'40 10 01 12 32 43 34 04', T:'00 40|20 24', U:'00 03 14 34 43 40',
 V:'00 24 40', W:'00 14 22 34 40', X:'00 44|40 04', Y:'00 22 40|22 24', Z:'00 40 04 44',
 '0':'10 30 41 43 34 14 03 01 10|13 31','1':'11 20 24|14 34','2':'00 30 41 32 04 44',
 '3':'00 30 41 22 43 34 04','4':'00 02 42|40 44','5':'40 00 02 32 43 34 04',
 '6':'40 10 01 03 14 34 43 32 02','7':'00 40 14','8':'12 01 10 30 41 32 12 03 14 34 43 32',
 '9':'42 12 01 10 30 41 43 34 04','-':'02 42','.':'24 25','!':'20 22|24 25','?':'00 30 41 22|24 25',
};
export const normalizeText = (value: string) => value.toUpperCase();
export const MAX_TEXT_LENGTH = 40;
export const validText = (value: string) => value.length <= MAX_TEXT_LENGTH && /^[A-Z0-9 .!?\-\n]*$/.test(normalizeText(value));
export function letteringPaths(value: string): PenPoint[][] {
 if (!validText(value)) throw new Error(`Use up to ${MAX_TEXT_LENGTH} letters, numbers, spaces or . ! ? -`);
 const lines = normalizeText(value).split('\n').flatMap(line => line.match(/.{1,7}/g) || ['']);
 const paths: PenPoint[][] = [], columns = Math.max(1,...lines.map(l=>l.length));
 const step = Math.min(.25,1.7/columns), h = Math.min(.32,1.65/Math.max(1,lines.length));
 lines.forEach((line,row) => line.split('').forEach((letter,col) => {
  const x = -line.length*step/2+col*step, y = -lines.length*h/2+row*h;
  for (const stroke of (glyphs[letter] || '').split('|').filter(Boolean)) paths.push(stroke.split(' ').map(p=>[x+Number(p[0])/4*step*.72,y+Number(p[1])/5*h*.76]));
 }));
 return paths;
}
