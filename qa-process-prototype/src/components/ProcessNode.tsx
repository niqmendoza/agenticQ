import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Bot, Box, BrainCircuit, CheckCheck, Database, FileText, GitBranch, Layers3, Play, Settings2, ShieldCheck, UserRound, Wrench } from 'lucide-react';
import { isGroup, isOptional } from '../data/model';
import type { ProcessItem } from '../types/architecture';

export interface DiagramNodeData extends Record<string, unknown> {
  item: ProcessItem;
  direction: 'RIGHT' | 'DOWN';
  dimmed: boolean;
  related: boolean;
  onOpen: (id: string) => void;
}

const icons = {
  group: Layers3,
  process: Settings2,
  agent: Bot,
  human: UserRound,
  decision: GitBranch,
  tool: Wrench,
  model: BrainCircuit,
  artifact: FileText,
  'external-system': Database,
  validation: ShieldCheck,
  input: Box,
  output: CheckCheck,
};

const typeLabels: Record<string, string> = {
  group: 'Etapa con detalle', process: 'Actividad', agent: 'Asistente de IA', human: 'Persona',
  decision: 'Decisión', tool: 'Herramienta', model: 'Modelo de IA', artifact: 'Documento',
  'external-system': 'Sistema externo', validation: 'Validación', input: 'Entrada', output: 'Salida',
};

export function countLeaves(item: ProcessItem): number {
  return isGroup(item) ? item.children.reduce((sum, child) => sum + countLeaves(child), 0) : 1;
}

export function NodeCard({ data, selected }: NodeProps) {
  const { item, direction, dimmed, onOpen } = data as DiagramNodeData;
  const Icon = icons[item.type] ?? Play;
  const horizontal = direction === 'RIGHT';
  const status = !isGroup(item) ? item.status : undefined;
  return (
    <div className={`process-node kind-${item.type} ${isOptional(item) ? 'node-optional' : ''} ${selected ? 'is-selected' : ''} ${dimmed ? 'is-dimmed' : ''}`}>
      <Handle type="target" position={horizontal ? Position.Left : Position.Top} className="flow-handle" />
      <div className="node-topline">
        <span className="node-icon"><Icon size={17} strokeWidth={1.9} /></span>
        <span className="node-kind">{isOptional(item) ? 'Opcional · reemplazable' : typeLabels[item.type]}</span>
        {status && <span className={`status-dot status-${status}`} title={status} />}
      </div>
      <strong className="node-title">{item.title}</strong>
      <p className="node-description">{isGroup(item) ? item.description : item.shortDescription}</p>
      {isGroup(item) && (
        <button className="node-open nodrag" type="button" onClick={event => { event.stopPropagation(); onOpen(item.id); }} aria-label={`Abrir ${item.title}`}>
          Explorar {countLeaves(item)} etapas <span aria-hidden="true">↗</span>
        </button>
      )}
      <Handle type="source" position={horizontal ? Position.Right : Position.Bottom} className="flow-handle" />
    </div>
  );
}

export function ProcessNode(props: NodeProps) { return <NodeCard {...props} />; }
