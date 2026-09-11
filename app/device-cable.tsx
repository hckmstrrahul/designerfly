import { useEffect, useRef, useState } from 'react';
type Route = { path: string; x1: number; y1: number; x2: number; y2: number; startAngle: number; endAngle: number };

/** Cables follow the visible chassis ports when the responsive layout changes. */
export function DeviceCable() {
  const ref = useRef<SVGSVGElement>(null);
  const [routes, setRoutes] = useState<Route[]>([]);
  useEffect(() => {
    const host = ref.current!.parentElement!;
    const a = host.querySelector('.activity-device')!, b = host.querySelector('.spectral-device')!, desk = host.querySelector('.drawing-device')!;
    const update = () => {
      const base = host.getBoundingClientRect();
      const scale = base.width / host.offsetWidth || 1;
      const local = (element: Element) => {
        const r = element.getBoundingClientRect();
        return { left: (r.left - base.left) / scale, right: (r.right - base.left) / scale, top: (r.top - base.top) / scale, bottom: (r.bottom - base.top) / scale, width: r.width / scale, height: r.height / scale };
      };
      const first = local(a), second = local(b), drawing = local(desk);
      if (first.top >= drawing.bottom - 1) {
        const connect = (from: typeof first, to: typeof first, side: number): Route => {
          const x1 = from.left + from.width * side, y1 = from.bottom;
          const x2 = to.left + to.width * (side - .1), y2 = to.top;
          const gap = Math.max(24, y2 - y1);
          return {
            path: `M${x1} ${y1} C${x1} ${y1 + gap * .65},${x2} ${y2 - gap * .65},${x2} ${y2}`,
            x1, y1, x2, y2, startAngle: 0, endAngle: 180,
          };
        };
        setRoutes([connect(drawing, first, .76), connect(first, second, .34)]); return;
      }
      const x1 = drawing.right, y1 = drawing.top + drawing.height * .46;
      const x2 = first.left, y2 = first.top + first.height * .39;
      const sx = first.left + first.width * .79, sy = first.bottom;
      const ex = second.right, ey = second.top + second.height * .44;
      const spectrumPath = Math.abs(first.right - second.right) < 2
        ? `M${sx} ${sy} C${sx} ${sy + 12},${ex + 22} ${sy + 8},${ex + 22} ${second.top + 16} L${ex + 22} ${ey - 22} Q${ex + 22} ${ey},${ex} ${ey}`
        : `M${sx} ${sy} C${sx} ${sy + 95},${sx + 28} ${ey + 62},${ex + 95} ${ey + 62} C${ex + 38} ${ey + 62},${ex + 48} ${ey},${ex} ${ey}`;
      setRoutes([
        { path: `M${x1} ${y1} C${x1 + 24} ${y1},${x1 + 18} ${y1 + 42},${x1 + 34} ${y1 + 42} C${x2 - 12} ${y1 + 42},${x2 - 48} ${y2},${x2} ${y2}`, x1, y1, x2, y2, startAngle: -90, endAngle: 90 },
        { path: spectrumPath, x1: sx, y1: sy, x2: ex, y2: ey, startAngle: 0, endAngle: -90 },
      ]);
    };
    const observer = new ResizeObserver(update);
    const mutations = new MutationObserver(update);
    mutations.observe(host, { attributes: true, attributeFilter: ['style'] });
    observer.observe(host); observer.observe(a); observer.observe(b); observer.observe(desk);
    window.addEventListener('resize', update);
    const initialFrame = requestAnimationFrame(update); update();
    return () => { observer.disconnect(); mutations.disconnect(); window.removeEventListener('resize', update); cancelAnimationFrame(initialFrame); };
  }, []);
  return <svg ref={ref} className="sync-cable" aria-hidden="true">{routes.map((route, index) => <g key={index}>
    <path d={route.path} className="sync-cable-shadow" /><path d={route.path} className="sync-cable-body" /><path d={route.path} className="sync-cable-highlight" />
    {[{ x: route.x1, y: route.y1, angle: route.startAngle }, { x: route.x2, y: route.y2, angle: route.endAngle }].map((p, i) => <g key={i} transform={`translate(${p.x} ${p.y}) rotate(${p.angle})`}><rect x={-5} y={-2} width={10} height={15} rx={2} fill="#535b4e" /><rect x={-3} y={2} width={6} height={8} rx={1} fill="#939b87" /></g>)}
  </g>)}</svg>;
}
