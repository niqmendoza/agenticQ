import ELK from 'elkjs/lib/elk.bundled.js';
import type { ProcessItem, VisibleRelation } from '../types/architecture';

const elk = new ELK();

export interface LayoutNode {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface LayoutResult {
  nodes: LayoutNode[];
}

function size(item: ProcessItem) {
  if (item.type === 'group') return { width: 258, height: 174 };
  if (item.type === 'decision') return { width: 242, height: 166 };
  return { width: 242, height: 156 };
}

export async function elkLayout(items: ProcessItem[], relations: VisibleRelation[], overview: boolean): Promise<LayoutResult> {
  if (items.length === 0) return { nodes: [] };
  const graph = await elk.layout({
    id: 'view',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'RIGHT',
      'elk.edgeRouting': 'ORTHOGONAL',
      'elk.spacing.nodeNode': overview ? '64' : '40',
      'elk.layered.spacing.nodeNodeBetweenLayers': overview ? '80' : '62',
      'elk.padding': '[top=20,left=20,bottom=20,right=20]',
      'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
    },
    children: items.map(item => ({ id: item.id, ...size(item) })),
    edges: relations.map(edge => ({ id: edge.id, sources: [edge.source], targets: [edge.target] })),
  });
  return {
    nodes: (graph.children ?? []).map(child => ({
      id: child.id,
      x: child.x ?? 0,
      y: child.y ?? 0,
      width: child.width ?? 274,
      height: child.height ?? 156,
    })),
  };
}
