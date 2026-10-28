import type { ModelIndex, ProcessEdge, ProcessGroup, ProcessItem, ProcessModel, VisibleRelation } from '../types/architecture';

export function isGroup(item: ProcessItem): item is ProcessGroup {
  return item.type === 'group';
}

export function isOptional(item: ProcessItem): boolean {
  return isGroup(item) ? item.children.length > 0 && item.children.every(isOptional) : item.status === 'opcional';
}

export function buildIndex(model: ProcessModel): ModelIndex {
  const byId = new Map<string, ProcessItem>();
  const parentId = new Map<string, string | null>();
  function visit(item: ProcessItem, parent: string | null) {
    if (byId.has(item.id)) throw new Error(`ID duplicado: ${item.id}`);
    byId.set(item.id, item);
    parentId.set(item.id, parent);
    if (isGroup(item)) item.children.forEach(child => visit(child, item.id));
  }
  model.groups.forEach(group => visit(group, null));
  return { byId, parentId };
}

export function pathTo(index: ModelIndex, id: string | null): ProcessGroup[] {
  if (!id) return [];
  const path: ProcessGroup[] = [];
  let cursor: string | null = id;
  while (cursor) {
    const item = index.byId.get(cursor);
    if (item && isGroup(item)) path.unshift(item);
    cursor = index.parentId.get(cursor) ?? null;
  }
  return path;
}

export function childrenOf(model: ProcessModel, index: ModelIndex, groupId: string | null): ProcessItem[] {
  if (!groupId) return model.groups;
  const group = index.byId.get(groupId);
  return group && isGroup(group) ? group.children : [];
}

function childRepresentative(id: string, groupId: string | null, index: ModelIndex): string | null {
  if (!index.byId.has(id)) return null;
  let current = id;
  let parent = index.parentId.get(current) ?? null;
  while (parent !== groupId) {
    if (parent === null) return null;
    current = parent;
    parent = index.parentId.get(current) ?? null;
  }
  return current;
}

export function visibleRelations(model: ProcessModel, index: ModelIndex, groupId: string | null): VisibleRelation[] {
  const aggregated = new Map<string, VisibleRelation>();
  const rootIds = new Set(model.groups.map(group => group.id));
  const rootEdges = model.edges.filter(edge => rootIds.has(edge.source) && rootIds.has(edge.target));
  const candidateEdges = groupId ? model.edges.filter(edge => !rootEdges.includes(edge)) : rootEdges.length ? rootEdges : model.edges;
  for (const edge of candidateEdges) {
    const source = childRepresentative(edge.source, groupId, index);
    const target = childRepresentative(edge.target, groupId, index);
    if (!source || !target || source === target) continue;
    const key = `${source}|${target}|${edge.type}`;
    const existing = aggregated.get(key);
    if (existing) {
      existing.count += 1;
      existing.originalIds.push(edge.id);
    } else {
      aggregated.set(key, { ...edge, source, target, count: 1, originalIds: [edge.id] });
    }
  }
  return [...aggregated.values()].map(edge => ({
    ...edge,
    label: edge.count > 1 ? `${edge.label} · +${edge.count - 1}` : edge.label,
  }));
}

export function relationsFor(model: ProcessModel, id: string): ProcessEdge[] {
  return model.edges.filter(edge => edge.source === id || edge.target === id);
}

export function visibleRelatedIds(model: ProcessModel, index: ModelIndex, groupId: string | null, selectedId: string | null): Set<string> {
  if (!selectedId) return new Set();
  const result = new Set([selectedId]);
  for (const edge of model.edges) {
    if (edge.source !== selectedId && edge.target !== selectedId) continue;
    const other = edge.source === selectedId ? edge.target : edge.source;
    const representative = childRepresentative(other, groupId, index);
    if (representative) result.add(representative);
  }
  return result;
}

export function validateModel(model: ProcessModel): void {
  if (!model.title || !Array.isArray(model.groups) || !Array.isArray(model.edges)) throw new Error('El JSON no tiene la estructura esperada.');
  const index = buildIndex(model);
  const kinds = new Set(['process','agent','human','decision','tool','model','artifact','external-system','validation','input','output']);
  for (const item of index.byId.values()) {
    if (!item.title || !item.description) throw new Error(`Falta título o descripción: ${item.id}`);
    if (isGroup(item)) {
      if (!Array.isArray(item.children) || !item.children.length) throw new Error(`Grupo vacío: ${item.id}`);
    } else {
      if (!kinds.has(item.type) || !item.shortDescription || !item.details?.objective || !item.details?.howItWorks || !Array.isArray(item.details.validationCriteria)) throw new Error(`Nodo incompleto: ${item.id}`);
      for (const field of ['responsibilities','inputs','outputs','tools','agents'] as const) {
        if (!Array.isArray(item[field])) throw new Error(`Falta ${field}: ${item.id}`);
      }
      if (typeof item.humanInteraction?.required !== 'boolean') throw new Error(`Falta humanInteraction: ${item.id}`);
    }
  }
  const edgeIds = new Set<string>();
  for (const edge of model.edges) {
    if (edgeIds.has(edge.id)) throw new Error(`Relación duplicada: ${edge.id}`);
    edgeIds.add(edge.id);
    if (!index.byId.has(edge.source) || !index.byId.has(edge.target)) throw new Error(`Relación con nodo inexistente: ${edge.id}`);
  }
}
