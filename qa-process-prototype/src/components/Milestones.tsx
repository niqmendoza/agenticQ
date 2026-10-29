import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowUpRight, Check, ChevronDown, Download, Flag, ListChecks } from 'lucide-react';
import { Roadmap, RoadmapNavigator } from './Roadmap';
import { buildIndex } from '../data/model';
import { progressCounts, statusLabels, type ImplementationPlan, type Milestone, type MilestoneEntry, type MilestoneSnapshot, type MilestoneStatus } from '../data/milestones';
import type { ProcessLeaf, ProcessModel } from '../types/architecture';

function milestoneModel(plan: ImplementationPlan): ProcessModel {
  return {
    title: plan.title, description: plan.description,
    groups: plan.phases.map(phase => ({ id: phase.id, type: 'group', title: phase.title, description: phase.description,
      owner: 'Equipo · avance según evidencia',
      children: phase.milestones.map(item => ({
        id: item.id, type: 'validation', title: item.title, shortDescription: item.description, description: item.description,
        responsibilities: [], inputs: [], outputs: [], tools: [], agents: [], humanInteraction: { required: true, description: 'El equipo actualiza el hito con evidencia.' },
        details: { objective: item.description, howItWorks: item.description, validationCriteria: item.criteria },
        status: item.optional ? 'opcional' : 'propuesto',
      })),
    })), edges: [],
  };
}

function MilestoneCard({ item, entry, onChange, onOpenProcess }: {
  item: Milestone; entry: MilestoneEntry; onChange: (change: Partial<Pick<MilestoneEntry, 'status' | 'note'>>) => void; onOpenProcess: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const done = entry.status === 'completado';
  return <article className={`milestone-card milestone-${entry.status} ${item.optional ? 'milestone-optional' : ''}`}>
    <div className="milestone-card-heading">
      <label className="milestone-check" title={done ? 'Volver a pendiente' : 'Marcar como completado'}><input type="checkbox" checked={done} aria-label={`Completar ${item.title}`} onChange={event => onChange({ status: event.target.checked ? 'completado' : 'pendiente' })}/><span aria-hidden="true">{done && <Check size={12}/>}</span></label>
      <button type="button" data-branch-id={item.id} className="milestone-title" onClick={() => setOpen(value => !value)} aria-expanded={open}>{item.title}<ChevronDown size={13} className={open ? 'milestone-chevron-open' : ''}/></button>
    </div>
    <div className="milestone-card-status"><span className={`milestone-state state-${entry.status}`}>{statusLabels[entry.status]}</span>{item.optional && <span className="milestone-option-tag">Opcional</span>}</div>
    {item.initialStatus === 'completado' && done && !open && item.confirmation && <p className="milestone-confirmation">{item.confirmation}</p>}
    {open && <div className="milestone-card-detail">
      <p>{item.description}</p>
      {item.confirmation && <p className="milestone-confirmation">{item.confirmation}</p>}
      <label className="milestone-field">Estado<select value={entry.status} onChange={event => onChange({ status: event.target.value as MilestoneStatus })}>{Object.entries(statusLabels).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <div className="milestone-criteria"><strong>Para darlo por terminado</strong><ul>{item.criteria.map(criterion => <li key={criterion}>{criterion}</li>)}</ul></div>
      {item.optional && <p className="milestone-optional-note">No es requisito para completar la base del sistema. Registrar su evaluación no implica que haya que adoptarlo.</p>}
      <label className="milestone-field">Notas o evidencia<textarea value={entry.note} maxLength={5000} placeholder="Qué se hizo, qué falta o dónde está la evidencia…" onChange={event => onChange({ note: event.target.value })}/></label>
      {entry.updatedAt && <small className="milestone-edited">Última edición: {new Date(entry.updatedAt).toLocaleString('es-AR')}</small>}
      <button type="button" className="milestone-process-link" onClick={() => onOpenProcess(item.processNodeId)}>Ver esta parte del proceso <ArrowUpRight size={12}/></button>
    </div>}
  </article>;
}

export function Milestones({ plan, snapshot, storageAvailable, onChange, onSave, onOpenProcess, onBackToProcess }: {
  plan: ImplementationPlan; snapshot: MilestoneSnapshot; storageAvailable: boolean;
  onChange: (id: string, change: Partial<Pick<MilestoneEntry, 'status' | 'note'>>) => void;
  onSave: () => void; onOpenProcess: (id: string) => void; onBackToProcess: () => void;
}) {
  const model = useMemo(() => milestoneModel(plan), [plan]);
  const index = useMemo(() => buildIndex(model), [model]);
  const items = useMemo(() => new Map(plan.phases.flatMap(phase => phase.milestones.map(item => [item.id, item] as const))), [plan]);
  const [expanded, setExpanded] = useState(() => new Set(plan.phases.map(phase => phase.id)));
  const [activeId, setActiveId] = useState(plan.phases[0].id);
  const wrapperRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;
    const observer = new IntersectionObserver(entries => {
      const visible = entries.filter(entry => entry.isIntersecting).sort((a,b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (visible[0]) setActiveId(visible[0].target.id.replace('phase-', ''));
    }, { root: wrapper.closest('.roadmap-page'), rootMargin: '-15% 0px -50% 0px', threshold: 0 });
    wrapper.querySelectorAll('.roadmap-row').forEach(row => observer.observe(row));
    return () => observer.disconnect();
  }, [expanded]);
  const totals = progressCounts([...items.values()], snapshot);
  const completedAll = [...items.values()].filter(item => snapshot.entries[item.id]?.status === 'completado').length;
  function navigate(id: string) {
    setActiveId(id); setExpanded(previous => new Set([...previous, id]));
    requestAnimationFrame(() => document.getElementById(`phase-${id}`)?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' }));
  }
  function toggle(id: string) { setExpanded(previous => { const next = new Set(previous); next.has(id) ? next.delete(id) : next.add(id); return next; }); }
  return <div ref={wrapperRef} className="milestones-view">
    <section className="milestones-summary" aria-label="Avance de la implementación">
      <div><span className="eyebrow"><Flag size={12}/> CONSTRUIR EL SISTEMA</span><h2>{totals.completed}<span> / {totals.total}</span><small>hitos de la base completados</small></h2><p>Las evaluaciones opcionales se cuentan aparte: {totals.optionalCompleted} de {totals.optional} completadas.</p></div>
      <div className="milestones-progress-block"><div className="milestones-progress-label"><span>Avance de la base</span><strong>{totals.percent}%</strong></div><div className="milestones-progress-track" role="progressbar" aria-label="Avance de hitos requeridos" aria-valuenow={totals.completed} aria-valuemin={0} aria-valuemax={totals.total}><span style={{ width: `${totals.percent}%` }}/></div><button type="button" className="milestones-save" onClick={onSave}><Download size={15}/>Descargar HTML con avances</button></div>
    </section>
    <div className="milestones-storage-note"><ListChecks size={16}/><p>{storageAvailable ? 'Los cambios se guardan en este navegador. Para compartir el avance o llevarlo a otra computadora, descargá el HTML con avances.' : 'Este navegador no permite guardar el avance localmente. Descargá el HTML con avances antes de cerrar para conservarlo.'}<span>Hito 2 registrado: RAGFlow local por API, contexto compacto y pruebas técnicas completados. La validación de utilidad con QA y Copilot sigue en curso.</span>{plan.report && <a className="milestone-process-link" href={plan.report.href} target="_blank" rel="noopener">Abrir {plan.report.title} <ArrowUpRight size={12}/></a>}</p></div>
    <div className="roadmap-workspace milestone-workspace"><RoadmapNavigator groups={model.groups} activeId={activeId} onNavigate={navigate}/><section className="roadmap-main" aria-label="Recorrido de hitos de implementación">
      <div className="roadmap-map-toolbar"><div className="roadmap-zoom-actions"><button type="button" onClick={() => setExpanded(new Set(plan.phases.map(phase => phase.id)))}>Expandir las etapas</button><button type="button" onClick={() => setExpanded(new Set())}>Contraer las etapas</button></div><span className="milestones-total">{completedAll} de {items.size} hitos completados, incluidos opcionales</span></div>
      <p className="roadmap-instruction">Marcá cada hito o abrilo para cambiar su estado y registrar evidencia. Es una guía de trabajo; las etapas pueden avanzar en paralelo.</p>
      <Roadmap model={model} index={index} activeId={activeId} selectedId={null} expanded={expanded} onToggle={toggle} onSelect={navigate} onNavigate={navigate} connectionsGroupId={null} onCloseConnections={() => {}}
        renderLeaf={(leaf: ProcessLeaf) => { const item = items.get(leaf.id); return item ? <MilestoneCard item={item} entry={snapshot.entries[item.id]} onChange={change => onChange(item.id, change)} onOpenProcess={onOpenProcess}/> : null; }}
        renderPhaseExtra={phase => { const definition = plan.phases.find(item => item.id === phase.id)!; const counts = progressCounts(definition.milestones, snapshot); return <div className="milestone-phase-progress"><span>{counts.completed}/{counts.total} hitos de base</span><div><i style={{ width: `${counts.percent}%` }}/></div></div>; }}
        presentation={{ startLabel: 'PLAN DE IMPLEMENTACIÓN · AVANCE SEGÚN EVIDENCIA', endLabel: 'VALIDAR EL PILOTO Y SEGUIR MEJORANDO', endActionLabel: 'Ver el mapa del proceso', onEndAction: onBackToProcess, ariaLabel: 'Mapa de hitos de implementación de QA agentizada' }}/>
    </section></div>
  </div>;
}
