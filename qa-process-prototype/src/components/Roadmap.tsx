import { useLayoutEffect, useMemo, useRef, useState } from 'react';
import { ArrowDown, ArrowUpRight, ChevronRight, GitBranch, Minus, Plus, RotateCcw } from 'lucide-react';
import { ReactFlowProvider } from '@xyflow/react';
import { isGroup, isOptional, pathTo } from '../data/model';
import { ProcessDiagram } from './ProcessDiagram';
import type { ModelIndex, ProcessGroup, ProcessItem, ProcessModel } from '../types/architecture';

export const roadmapTitle = (title: string) => title.replace(/^\d+\s*·\s*/, '');
function Branch({ item, expanded, selectedId, onToggle, onSelect }: {
  item: ProcessItem; expanded: Set<string>; selectedId: string | null; onToggle: (id: string) => void; onSelect: (id: string) => void;
}) {
  const group = isGroup(item), open = expanded.has(item.id);
  return <div className={`roadmap-branch ${group ? 'branch-group' : 'branch-leaf'} ${open ? 'branch-open' : ''}`}>
    <button type="button" data-branch-id={item.id} className={`topic-button topic-${item.type} ${isOptional(item) ? 'topic-optional' : ''} ${selectedId === item.id ? 'topic-selected' : ''}`} onClick={() => { if (group) onToggle(item.id); onSelect(item.id); }} aria-expanded={group ? open : undefined}>
      <span>{roadmapTitle(item.title)}{isOptional(item) && <small className="optional-topic-label">Opcional · reemplazable</small>}</span>{group ? <span className="topic-toggle">{open ? <Minus size={13}/> : <Plus size={13}/>}</span> : <ArrowUpRight size={12}/>}
    </button>
    {group && open && <div className="branch-children">{item.children.map(child => <Branch key={child.id} item={child} expanded={expanded} selectedId={selectedId} onToggle={onToggle} onSelect={onSelect}/>)}</div>}
  </div>;
}

type Line = { id: string; d: string; kind: 'spine' | 'branch' };
export function Roadmap({ model, index, activeId, selectedId, expanded, onToggle, onSelect, onNavigate, connectionsGroupId, onCloseConnections }: {
  model: ProcessModel; index: ModelIndex; activeId: string | null; selectedId: string | null; expanded: Set<string>;
  onToggle: (id: string) => void; onSelect: (id: string) => void; onNavigate: (id: string) => void;
  connectionsGroupId: string | null; onCloseConnections: () => void;
}) {
  const canvas = useRef<HTMLDivElement>(null);
  const [lines, setLines] = useState<Line[]>([]);
  const connectionRoot = connectionsGroupId ? pathTo(index, connectionsGroupId)[0]?.id : null;
  const rootIds = useMemo(() => new Set(model.groups.map(group => group.id)), [model]);
  const returns = model.edges.filter(edge => rootIds.has(edge.source) && rootIds.has(edge.target) && edge.type === 'feedback');
  useLayoutEffect(() => {
    const root = canvas.current;
    if (!root) return;
    function measure() {
      const box = root!.getBoundingClientRect();
      const rect = (selector: string) => {
        const el = root!.querySelector(selector);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {left:r.left-box.left,right:r.right-box.left,top:r.top-box.top,bottom:r.bottom-box.top,cx:r.left-box.left+r.width/2,cy:r.top-box.top+r.height/2};
      };
      const paths: Line[] = [];
      model.groups.forEach((group, i) => {
        const phase = rect(`[data-phase-id="${CSS.escape(group.id)}"]`);
        if (!phase) return;
        if (i > 0) {
          const prev = rect(`[data-phase-id="${CSS.escape(model.groups[i-1].id)}"]`);
          if (prev) paths.push({id:`spine-${group.id}`,kind:'spine',d:`M${prev.cx},${prev.bottom} V${phase.top}`});
        } else paths.push({id:'spine-start',kind:'spine',d:`M${phase.cx},0 V${phase.top}`});
        if (i === model.groups.length-1) paths.push({id:'spine-end',kind:'spine',d:`M${phase.cx},${phase.bottom} V${box.height-22}`});
        if (expanded.has(group.id)) group.children.forEach(child => {
          const node = rect(`[data-branch-id="${CSS.escape(child.id)}"]`);
          if (!node) return;
          const left = node.cx < phase.cx, x1 = left ? phase.left : phase.right, x2 = left ? node.right : node.left;
          const middle = (x1+x2)/2;
          paths.push({id:`branch-${child.id}`,kind:'branch',d:`M${x1},${phase.cy} C${middle},${phase.cy} ${middle},${node.cy} ${x2},${node.cy}`});
        });
      });
      setLines(paths);
    }
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(root);
    root.querySelectorAll('.roadmap-row,.topic-button,.phase-main-button').forEach(el=>observer.observe(el));
    return () => observer.disconnect();
  },[model,expanded,connectionsGroupId]);
  return <div className="roadmap-map" ref={canvas} aria-label="Mapa completo de QA con fases y subpartes">
    <svg className="roadmap-lines" aria-hidden="true"><defs><marker id="roadmap-direction" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="#00A0AD"/></marker></defs>{lines.map(line=><path key={line.id} d={line.d} className={`roadmap-line-${line.kind}`} markerEnd={line.kind==='spine'?'url(#roadmap-direction)':undefined}/>)}</svg>
    <div className="roadmap-start"><span>CAMBIO FUNCIONAL APROBADO</span><ArrowDown size={15}/></div>
    {model.groups.map((group: ProcessGroup,i)=>{
      const open=expanded.has(group.id), phaseReturns=returns.filter(edge=>edge.source===group.id);
      const branch=(side:0|1)=><div className={`roadmap-side roadmap-${side===0?'left':'right'}`}>{open && group.children.filter((_,n)=>n%2===side).map(child=><Branch key={child.id} item={child} expanded={expanded} selectedId={selectedId} onToggle={onToggle} onSelect={onSelect}/>)}</div>;
      return <section key={group.id} id={`phase-${group.id}`} className={`roadmap-row ${activeId===group.id?'row-active':''} ${!open?'row-collapsed':''}`} aria-label={roadmapTitle(group.title)}>
        {branch(0)}
        <div className="roadmap-phase">
          <span className="phase-sequence">FASE {String(i+1).padStart(2,'0')}</span>
          {group.entryCondition && <span className="roadmap-condition">{group.entryCondition}</span>}
          <button type="button" data-phase-id={group.id} className={`phase-main-button ${group.owner==='Personas'?'phase-is-human':''} ${selectedId===group.id?'topic-selected':''}`} onClick={()=>onSelect(group.id)}><span>{roadmapTitle(group.title)}</span><ArrowUpRight size={14}/></button>
          <span className="roadmap-owner">{group.owner}</span>
          <button type="button" className="phase-fold" onClick={()=>onToggle(group.id)} aria-expanded={open} aria-label={`${open?'Contraer':'Desplegar'} ${roadmapTitle(group.title)}`}>{open?<Minus size={11}/>:<Plus size={11}/>} {open?'Contraer ramas':'Desplegar ramas'}</button>
        </div>
        {branch(1)}
        {!!phaseReturns.length && <div className="roadmap-returns">{phaseReturns.map(edge=><button key={edge.id} type="button" onClick={()=>onNavigate(edge.target)}><RotateCcw size={11}/><span>{edge.label}</span><ChevronRight size={11}/></button>)}</div>}
        {connectionRoot===group.id && connectionsGroupId && <div className="roadmap-relationship-view"><div className="relationship-title"><span><GitBranch size={14}/>Conexiones de {roadmapTitle(index.byId.get(connectionsGroupId)?.title??group.title)}</span><button type="button" onClick={onCloseConnections}>Cerrar <Minus size={12}/></button></div><div className="relationship-canvas"><ReactFlowProvider><ProcessDiagram model={model} index={index} activeGroupId={connectionsGroupId} selectedId={selectedId} onSelect={id=>{if(id)onSelect(id);}} onOpen={onNavigate} onOverview={onCloseConnections}/></ReactFlowProvider></div></div>}
      </section>;
    })}
    <div className="roadmap-end"><span>LA CORRECCIÓN VUELVE A PROBARSE</span><button type="button" onClick={()=>onNavigate(model.groups.find(group=>group.id==='execution')?.id??model.groups[0].id)}><RotateCcw size={13}/>Volver a ejecutar y revisar</button></div>
  </div>;
}

export function RoadmapNavigator({groups, activeId, onNavigate}: {groups:ProcessGroup[]; activeId:string|null;onNavigate:(id:string)=>void}) {
  return <nav className="roadmap-navigator" aria-label="Flujo maestro siempre visible"><span className="navigator-label">EL RECORRIDO</span><div className="navigator-spine">{groups.map((group,i)=><button key={group.id} type="button" className={activeId===group.id?'navigator-active':''} onClick={()=>onNavigate(group.id)} aria-current={activeId===group.id?'step':undefined}><span className="navigator-dot">{String(i+1).padStart(2,'0')}</span><span>{roadmapTitle(group.title)}</span></button>)}</div><p>Las fases siguen conectadas mientras explorás sus ramas.</p><span className="navigator-legend"><i/>Avance</span><span className="navigator-legend legend-dotted"><i/>Detalle de una fase</span><span className="navigator-legend legend-return"><i/>Volver para corregir</span><span className="navigator-legend legend-optional"><i/>Opcional o reemplazable</span></nav>;
}
