import { useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import { ArrowDownRight, ArrowUpRight, CheckCheck, FileCheck2, GitPullRequest, Layers3, RotateCcw, Sparkles, Waypoints } from 'lucide-react';
import type { ProcessEdge, ProcessGroup, ProcessModel } from '../types/architecture';

const icons = [FileCheck2, Sparkles, GitPullRequest, Waypoints, CheckCheck, RotateCcw];
const cleanTitle = (title: string) => title.replace(/^\d+\s*·\s*/, '');
type Box = { x: number; y: number; w: number; h: number };
type Route = { edge: ProcessEdge; path: string; labelX: number; labelY: number };

export function MasterFlow({ model, activeId, compact, onOpen, onReset }: {
  model: ProcessModel; activeId: string | null; compact: boolean; onOpen: (id: string) => void; onReset: () => void;
}) {
  const canvas = useRef<HTMLDivElement>(null);
  const cards = useRef(new Map<string, HTMLButtonElement>());
  const [columns, setColumns] = useState(6);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [hovered, setHovered] = useState<string | null>(null);
  const ids = new Set(model.groups.map(g => g.id));
  const connections = model.edges.filter(edge => ids.has(edge.source) && ids.has(edge.target));
  const forwards = connections.filter(edge => edge.type !== 'feedback');
  const returns = connections.filter(edge => edge.type === 'feedback');
  const count = model.groups.length;

  useLayoutEffect(() => {
    const el = canvas.current;
    if (!el) return;
    function measure() {
      const root = el!.getBoundingClientRect();
      const cols = root.width < 600 ? 2 : root.width < 1000 ? 3 : Math.min(6, count);
      setColumns(cols);
      const boxes = new Map<string, Box>();
      cards.current.forEach((card, id) => {
        const rect = card.getBoundingClientRect();
        boxes.set(id, { x: rect.left - root.left, y: rect.top - root.top, w: rect.width, h: rect.height });
      });
      const routes: Route[] = [];
      connections.forEach(edge => {
        const a = boxes.get(edge.source), b = boxes.get(edge.target);
        if (!a || !b) return;
        if (edge.type === 'feedback') {
          if (cols < count) return;
          const lane = returns.findIndex(e => e.id === edge.id);
          const x1 = a.x + a.w * (0.32 + lane * 0.07), x2 = b.x + b.w * (0.32 + lane * 0.07);
          const y1 = a.y + a.h, y2 = b.y + b.h, y = Math.max(y1, y2) + (compact ? 24 : 32) + lane * (compact ? 20 : 28);
          routes.push({ edge, path: `M${x1},${y1} V${y - 12} Q${x1},${y} ${x1 - 12},${y} H${x2 + 12} Q${x2},${y} ${x2},${y - 12} V${y2 + 4}`, labelX: (x1 + x2) / 2, labelY: y });
        } else if (Math.abs(a.y - b.y) < 5) {
          const right = b.x > a.x;
          const x1 = right ? a.x + a.w : a.x, x2 = right ? b.x : b.x + b.w;
          const y = a.y + a.h / 2;
          routes.push({ edge, path: `M${x1},${y} H${x2}`, labelX: (x1 + x2) / 2, labelY: y });
        } else {
          const x1 = a.x + a.w / 2, x2 = b.x + b.w / 2;
          const y1 = a.y + a.h, y2 = b.y;
          routes.push({ edge, path: `M${x1},${y1} V${(y1 + y2) / 2} H${x2} V${y2}`, labelX: x1, labelY: (y1 + y2) / 2 });
        }
      });
      setRoutes(routes);
    }
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    cards.current.forEach(card => observer.observe(card));
    return () => observer.disconnect();
  // Model and compact state alter measured card geometry. ResizeObserver covers viewport changes.
  }, [model, compact, columns, count]);

  function position(i: number): CSSProperties {
    const row = Math.floor(i / columns);
    const col = row % 2 ? columns - (i % columns) : (i % columns) + 1;
    return { gridColumn: col, gridRow: row + 1 };
  }

  return <section className={`master-section ${compact ? 'master-compact' : ''}`} aria-label="Flujo maestro completo">
    <div className="section-bar"><div className="section-title"><Layers3 size={16} /><span>FLUJO MAESTRO</span><span className="section-note">{compact ? 'Seguís viendo el recorrido completo' : 'Un recorrido conectado, de principio a fin'}</span></div>{compact ? <button type="button" className="text-action" onClick={onReset}>Cerrar detalle <ArrowUpRight size={14} /></button> : <span className="master-hint">Elegí una fase para explorar <ArrowDownRight size={15} /></span>}</div>
    <div ref={canvas} className={`master-canvas ${columns < count ? 'master-wrapped' : ''}`} style={{ '--master-columns': columns, '--return-count': returns.length } as CSSProperties}>
      <svg className="master-connections" aria-hidden="true"><defs><marker id="master-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#00A0AD" /></marker><marker id="return-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#E11F8F" /></marker></defs>
        {routes.map(({edge, path, labelX, labelY}) => {
          const feedback = edge.type === 'feedback';
          const active = hovered === edge.id || (!!activeId && (edge.source === activeId || edge.target === activeId));
          return <g key={edge.id} className={`master-route ${feedback ? 'route-return' : 'route-forward'} ${active ? 'route-active' : ''}`}>
            <path d={path} markerEnd={`url(#${feedback ? 'return-arrow' : 'master-arrow'})`} />
            {!feedback && <path d={path} className="route-pulse" />}
            {feedback && <><rect x={labelX - Math.min(158, edge.label.length * 3.1 + 12)} y={labelY - 9} width={Math.min(316, edge.label.length * 6.2 + 24)} height={18} rx={9} /><text x={labelX} y={labelY + 3}>{edge.label}</text></>}
          </g>;
        })}
      </svg>
      <div className="master-grid">{model.groups.map((group: ProcessGroup, i) => {
        const Icon = icons[i % icons.length];
        return <button key={group.id} ref={element => { if (element) cards.current.set(group.id, element); else cards.current.delete(group.id); }} type="button" className={`master-phase ${activeId === group.id ? 'phase-selected' : ''} ${group.owner === 'Personas' ? 'phase-human' : ''}`} style={position(i)} onClick={() => onOpen(group.id)} aria-pressed={activeId === group.id} aria-label={`Explorar ${cleanTitle(group.title)}`}>
          <div className="phase-top"><span className="phase-number">{String(i + 1).padStart(2, '0')}</span><Icon size={21} strokeWidth={1.5}/><ArrowUpRight className="phase-open" size={15}/></div>
          <h3>{cleanTitle(group.title)}</h3>{group.entryCondition && <span className="phase-condition">{group.entryCondition}</span>}
          <p className="phase-description">{group.description}</p>
          <div className="phase-milestones">{(group.milestones ?? group.children.slice(0, 3).map(child => child.title)).map((step, n) => <span key={n}><i />{step}</span>)}</div>
          <span className="phase-owner"><span className="owner-dot" />{group.owner ?? 'Equipo + herramientas'}</span>
          <span className="phase-explore">{activeId === group.id ? 'ESTÁS EXPLORANDO ESTA FASE' : 'ABRIR ESTA FASE'}<ArrowUpRight size={12}/></span>
        </button>;
      })}</div>
      {columns < count && <div className="return-chips" aria-label="Caminos de regreso">{returns.map(edge => <button key={edge.id} type="button" onClick={() => onOpen(edge.target)}><RotateCcw size={12}/>{edge.label}</button>)}</div>}
    </div>
    <div className="master-footer"><span><i className="legend-line" /> Avance del proceso</span><span><i className="legend-line return-line"/> Volver para corregir</span><span className="master-footer-note">{compact ? 'El detalle cambia; este mapa permanece.' : 'Las herramientas proponen y ejecutan. Las personas validan.'}</span></div>
    <div className="sr-only">{forwards.map(edge => <p key={edge.id}>{edge.source} → {edge.target}: {edge.label}</p>)}{returns.map(edge => <button key={edge.id} onFocus={() => setHovered(edge.id)} onBlur={() => setHovered(null)} onClick={() => onOpen(edge.target)}>{edge.label}</button>)}</div>
  </section>;
}
