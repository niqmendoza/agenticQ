import { useEffect, useMemo, useRef, useState } from 'react';
import { Background, BackgroundVariant, Controls, MarkerType, MiniMap, ReactFlow, useReactFlow, type Edge, type Node, type NodeTypes } from '@xyflow/react';
import { childrenOf, visibleRelatedIds, visibleRelations } from '../data/model';
import { elkLayout, type LayoutResult } from '../layout/elkLayout';
import type { ModelIndex, ProcessItem, ProcessModel, RelationKind } from '../types/architecture';
import { AgentNode } from './AgentNode';
import { DecisionNode } from './DecisionNode';
import { DiagramControls } from './DiagramControls';
import { GroupNode } from './GroupNode';
import { ProcessNode, type DiagramNodeData } from './ProcessNode';

const nodeTypes: NodeTypes = {
  group: GroupNode,
  agent: AgentNode,
  decision: DecisionNode,
  process: ProcessNode,
  human: ProcessNode,
  tool: ProcessNode,
  model: AgentNode,
  artifact: ProcessNode,
  'external-system': ProcessNode,
  validation: ProcessNode,
  input: ProcessNode,
  output: ProcessNode,
};

const edgeColors: Record<RelationKind, string> = {
  normal: '#00848F', conditional: '#E11F8F', feedback: '#E11F8F',
  async: '#00A0AD', 'human-approval': '#E11F8F', data: '#006972',
};

export interface ProcessDiagramProps {
  model: ProcessModel;
  index: ModelIndex;
  activeGroupId: string | null;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onOpen: (id: string) => void;
  onOverview: () => void;
}

export function ProcessDiagram({ model, index, activeGroupId, selectedId, onSelect, onOpen, onOverview }: ProcessDiagramProps) {
  const items = useMemo(() => childrenOf(model, index, activeGroupId), [model, index, activeGroupId]);
  const relations = useMemo(() => visibleRelations(model, index, activeGroupId), [model, index, activeGroupId]);
  const [layout, setLayout] = useState<LayoutResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [connectionId, setConnectionId] = useState<string | null>(null);
  const connection = relations.find(edge => edge.id === connectionId);
  const { fitView } = useReactFlow();
  const containerRef = useRef<HTMLDivElement>(null);
  const relatedIds = useMemo(() => visibleRelatedIds(model, index, activeGroupId, selectedId), [model, index, activeGroupId, selectedId]);

  useEffect(() => {
    let live = true;
    setLoading(true);
    setConnectionId(null);
    setLayout(null);
    void elkLayout(items, relations, activeGroupId === null)
      .then(result => { if (live) { setLayout(result); setLoading(false); } })
      .catch(error => { if (live) { console.error('No se pudo calcular el layout', error); setLoading(false); } });
    return () => { live = false; };
  }, [items, relations, activeGroupId]);

  useEffect(() => {
    if (!layout?.nodes.length) return;
    const timer = window.setTimeout(() => void fitView({ padding: 0.19, maxZoom: 1, duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 280 }), 60);
    return () => window.clearTimeout(timer);
  }, [layout, fitView]);

  useEffect(() => {
    if (!containerRef.current || !layout) return;
    let timer = 0;
    const observer = new ResizeObserver(() => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => void fitView({ padding: 0.19, maxZoom: 1, duration: 0 }), 80);
    });
    observer.observe(containerRef.current);
    return () => { observer.disconnect(); window.clearTimeout(timer); };
  }, [layout, fitView]);

  const itemById = useMemo(() => new Map(items.map(item => [item.id, item])), [items]);
  const nodes = useMemo<Node<DiagramNodeData>[]>(() => (layout?.nodes ?? []).flatMap(placed => {
    const item: ProcessItem | undefined = itemById.get(placed.id);
    if (!item) return [];
    return [{
      id: item.id,
      type: item.type,
      position: { x: placed.x, y: placed.y },
      width: placed.width,
      height: placed.height,
      draggable: false,
      selected: selectedId === item.id,
      ariaLabel: `${item.title}. ${item.type === "group" ? "Abrir actividades" : "Ver explicación"}`,
      data: { item, direction: 'RIGHT', dimmed: !!selectedId && !relatedIds.has(item.id), related: relatedIds.has(item.id), onOpen },
    }];
  }), [layout, itemById, activeGroupId, selectedId, relatedIds, onOpen]);

  const edges = useMemo<Edge[]>(() => relations.map(relation => {
    const color = edgeColors[relation.type];
    const dimmed = !!selectedId && !relatedIds.has(relation.source) && !relatedIds.has(relation.target);
    return {
      id: relation.id,
      source: relation.source,
      target: relation.target,
      type: 'smoothstep',
      ariaLabel: `${index.byId.get(relation.source)?.title} hacia ${index.byId.get(relation.target)?.title}: ${relation.label}`,
      selected: connectionId === relation.id,
      animated: relation.type === 'async',
      style: { stroke: color, strokeWidth: relation.type === 'human-approval' ? 2.5 : 2, strokeDasharray: relation.type === 'feedback' ? '6 5' : undefined, opacity: dimmed ? 0.18 : 0.9 },
      labelStyle: { fill: color, fontSize: 11, fontWeight: 700 },
      labelBgStyle: { fill: '#001417', fillOpacity: 0.95 },
      labelBgPadding: [7, 5],
      labelBgBorderRadius: 5,
      markerEnd: { type: MarkerType.ArrowClosed, color },
      data: { originalIds: relation.originalIds, kind: relation.type },
    };
  }), [relations, selectedId, relatedIds, connectionId, index]);

  return (
    <div ref={containerRef} className="diagram-canvas-app">
      {loading && <div className="diagram-loading" role="status">Calculando el mapa…</div>}
      {!loading && !layout && <div className="diagram-loading" role="alert">No se pudo dibujar este nivel del proceso.</div>}
      {connection && <div className="connection-caption" role="status"><strong>{connection.label}</strong><span>{index.byId.get(connection.source)?.title} → {index.byId.get(connection.target)?.title}</span><button type="button" onClick={() => setConnectionId(null)} aria-label="Cerrar explicación de conexión">×</button></div>}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => node.type === 'group' ? onOpen(node.id) : onSelect(node.id)}
        onNodeDoubleClick={(_, node) => { if (node.type === 'group') onOpen(node.id); }}
        onEdgeClick={(_, edge) => setConnectionId(edge.id)}
        onPaneClick={() => { onSelect(null); setConnectionId(null); }}
        nodesDraggable={false}
        nodesConnectable={false}
        edgesFocusable
        zoomOnScroll={false}
        panOnScroll
        minZoom={0.2}
        maxZoom={2.1}
        colorMode="dark"
      >
        <Background variant={BackgroundVariant.Dots} color="#004F56" gap={23} size={1} />
        <Controls showInteractive={false} position="bottom-left" />
        <MiniMap pannable zoomable position="bottom-right" nodeColor={node => {
          const type = node.type;
          if (type === 'human' || type === 'decision') return '#E11F8F';
          if (type === 'group') return '#00A0AD';
          return '#006972';
        }} />
        <DiagramControls onOverview={onOverview} isOverview={activeGroupId === null} />
      </ReactFlow>
    </div>
  );
}
