import { ArrowDownLeft, ArrowUpRight, ChevronRight, X } from 'lucide-react';
import { isGroup, isOptional, relationsFor } from '../data/model';
import type { ModelIndex, ProcessItem, ProcessModel } from '../types/architecture';

const kindNames: Record<string, string> = {
  group:'Dentro de esta fase', process:'Actividad', agent:'Asistente de IA', human:'Persona', decision:'Decisión',
  tool:'Herramienta', model:'Modelo de IA', artifact:'Documento', 'external-system':'Sistema externo',
  validation:'Validación', input:'Entrada', output:'Salida',
};

function ListBlock({ label, values }: { label: string; values: string[] }) {
  if (!values.length) return null;
  return <div className="detail-list"><h4>{label}</h4><ul>{values.map((value, index) => <li key={`${value}-${index}`}>{value}</li>)}</ul></div>;
}

export function DetailsPanel({ model, index, item, onClose, onNavigate }: {
  model: ProcessModel;
  index: ModelIndex;
  item: ProcessItem | null;
  onClose: () => void;
  onNavigate: (id: string) => void;
}) {
  if (!item) return (
    <aside className="details-panel empty-details" aria-label="Detalles del proceso">
      <div className="empty-symbol">◈</div>
      <span className="eyebrow">Exploración guiada</span>
      <h3>Elegí una etapa</h3>
      <p>Seleccioná una tarjeta del mapa para ver su objetivo, entradas, salidas y conexiones. Abrí un subproceso para recorrer sus actividades.</p>
      <div className="legend-stack"><span><i className="legend-agent" /> Agentes y modelos</span><span><i className="legend-human" /> Personas</span><span><i className="legend-decision" /> Decisiones</span><span><i className="legend-tool" /> Herramientas y sistemas</span></div>
    </aside>
  );

  const related = relationsFor(model, item.id);
  return (
    <aside className="details-panel" aria-label={`Detalles de ${item.title}`}>
      <div className="details-top"><span className={`detail-kind detail-${item.type}`}>{kindNames[item.type]}</span>{!isGroup(item) && <button type="button" onClick={onClose} aria-label="Volver al resumen de la fase"><X size={18} /></button>}</div>
      <h3>{item.title}</h3>
      <p className="detail-lead">{item.description}</p>
      {isOptional(item) && <div className="optional-explanation"><strong>Opcional · se puede reemplazar</strong><p>{isGroup(item) ? "Estas herramientas se pueden evaluar más adelante. Hoy el equipo puede proponer casos con Copilot y revisar la cobertura en Azure Test Plans." : item.currentAlternative ?? "El equipo puede cubrir esta tarea con sus herramientas actuales; esta opción se evalúa si aporta valor."}</p></div>}
      {isGroup(item) ? (
        <>
          <div className="detail-section"><h4>Elegí qué querés entender</h4><div className="child-links">{item.children.map(child => <button key={child.id} className={isOptional(child) ? 'optional-link' : undefined} type="button" onClick={() => onNavigate(child.id)}><span>{child.title}</span><ChevronRight size={15} /></button>)}</div></div>
          <p className="detail-navigation-hint">Abrí una actividad desde el mapa o esta lista. La guía de las seis fases permanece visible para ubicarte.</p>
        </>
      ) : (
        <>
          {item.status && <div className={`rollout rollout-${item.status}`}>{item.status === 'actual' ? 'Ya existe en el proceso' : item.status === 'opcional' ? 'Herramienta opcional' : 'Diseño propuesto'}</div>}
          <div className="detail-section"><h4>Para qué sirve</h4><p>{item.details.objective}</p></div>
          <div className="detail-section"><h4>Cómo se hace</h4><p>{item.details.howItWorks}</p></div>
          <div className="detail-columns"><ListBlock label="Qué recibe" values={item.inputs} /><ListBlock label="Qué entrega" values={item.outputs} /></div>
          <details className="technical-details"><summary>Herramientas y responsabilidades</summary><ListBlock label="Responsabilidades" values={item.responsibilities} /><ListBlock label="Herramientas" values={item.tools} /><ListBlock label="Agentes" values={item.agents} /></details>
          {item.humanInteraction.description && <div className="detail-section human-note"><h4>Quién interviene</h4><p>{item.humanInteraction.description}</p></div>}
          <ListBlock label="Cómo sabemos que está listo" values={item.details.validationCriteria} />
        </>
      )}
      {!!related.length && <div className="detail-section connection-list"><h4>Conexiones directas</h4>{related.map(edge => {
        const outgoing = edge.source === item.id;
        const otherId = outgoing ? edge.target : edge.source;
        const other = index.byId.get(otherId);
        return <button type="button" className={other && isOptional(other) ? 'optional-link' : undefined} key={edge.id} onClick={() => onNavigate(otherId)}><span className="connection-arrow">{outgoing ? <ArrowUpRight size={15} /> : <ArrowDownLeft size={15} />}</span><span><strong>{other?.title ?? otherId}</strong><small>{edge.label}</small></span></button>;
      })}</div>}
    </aside>
  );
}
