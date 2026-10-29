export type MilestoneStatus = 'pendiente' | 'en-curso' | 'completado' | 'bloqueado';
export interface Milestone {
  id: string;
  title: string;
  description: string;
  processNodeId: string;
  criteria: string[];
  optional?: boolean;
  initialStatus?: MilestoneStatus;
  initialNote?: string;
  confirmation?: string;
}
export interface MilestonePhase {
  id: string;
  title: string;
  description: string;
  milestones: Milestone[];
}
export interface ImplementationPlan {
  schemaVersion: number;
  title: string;
  description: string;
  phases: MilestonePhase[];
  report?: { title: string; href: string };
}
export interface MilestoneEntry {
  status: MilestoneStatus;
  note: string;
  updatedAt?: string;
}
export interface MilestoneSnapshot {
  schemaVersion: 1;
  updatedAt?: string;
  entries: Record<string, MilestoneEntry>;
}
export const statusLabels: Record<MilestoneStatus, string> = {
  pendiente: 'Pendiente', 'en-curso': 'En curso', completado: 'Completado', bloqueado: 'Bloqueado',
};
const validStatuses = new Set(Object.keys(statusLabels));

export function initialProgress(plan: ImplementationPlan): MilestoneSnapshot {
  return {
    schemaVersion: 1,
    entries: Object.fromEntries(plan.phases.flatMap(phase => phase.milestones.map(item => [item.id, {
      status: item.initialStatus ?? 'pendiente', note: item.initialNote ?? '',
    }]))),
  };
}

export function parseSnapshot(raw: string, plan: ImplementationPlan): MilestoneSnapshot {
  const parsed: unknown = JSON.parse(raw);
  if (!parsed || typeof parsed !== 'object') throw new Error('El avance no tiene un formato válido.');
  const candidate = parsed as Record<string, unknown>;
  if (candidate.schemaVersion !== 1 || !candidate.entries || typeof candidate.entries !== 'object' || Array.isArray(candidate.entries)) throw new Error('El avance no tiene la estructura esperada.');
  if (candidate.updatedAt !== undefined && (typeof candidate.updatedAt !== 'string' || !Number.isFinite(Date.parse(candidate.updatedAt)))) throw new Error('La fecha del avance no es válida.');
  const knownIds = new Set(plan.phases.flatMap(phase => phase.milestones.map(item => item.id)));
  const entries: Record<string, MilestoneEntry> = {};
  for (const [id, value] of Object.entries(candidate.entries)) {
    if (!knownIds.has(id)) continue;
    if (!value || typeof value !== 'object') throw new Error(`El hito ${id} no es válido.`);
    const entry = value as Record<string, unknown>;
    if (typeof entry.status !== 'string' || !validStatuses.has(entry.status) || typeof entry.note !== 'string') throw new Error(`Estado o nota inválidos en ${id}.`);
    if (entry.updatedAt !== undefined && (typeof entry.updatedAt !== 'string' || !Number.isFinite(Date.parse(entry.updatedAt)))) throw new Error(`Fecha inválida en ${id}.`);
    entries[id] = { status: entry.status as MilestoneStatus, note: entry.note, ...(entry.updatedAt ? { updatedAt: entry.updatedAt as string } : {}) };
  }
  return { schemaVersion: 1, entries, ...(candidate.updatedAt ? { updatedAt: candidate.updatedAt as string } : {}) };
}

export function mergeProgress(plan: ImplementationPlan, candidates: MilestoneSnapshot[]): MilestoneSnapshot {
  const seed = initialProgress(plan);
  // Merge per milestone: a note on one milestone must not erase newer work on another.
  const dates: Record<string, number> = {};
  for (const snapshot of [...candidates].sort((a, b) => (Date.parse(a.updatedAt ?? '') || 0) - (Date.parse(b.updatedAt ?? '') || 0))) {
    for (const [id, entry] of Object.entries(snapshot.entries)) {
      if (!Object.hasOwn(seed.entries, id)) continue;
      const time = Date.parse(entry.updatedAt ?? '') || 0;
      if (time >= (dates[id] ?? -1)) { seed.entries[id] = { ...entry }; dates[id] = time; }
    }
    if (snapshot.updatedAt && (!seed.updatedAt || Date.parse(snapshot.updatedAt) > Date.parse(seed.updatedAt))) seed.updatedAt = snapshot.updatedAt;
  }
  return seed;
}

export function updateMilestone(snapshot: MilestoneSnapshot, id: string, change: Partial<Pick<MilestoneEntry, 'status' | 'note'>>, now = new Date().toISOString()): MilestoneSnapshot {
  if (!Object.hasOwn(snapshot.entries, id)) throw new Error('Hito desconocido.');
  if (Object.hasOwn(change, 'status') && !validStatuses.has(change.status ?? '')) throw new Error('Estado inválido.');
  if (Object.hasOwn(change, 'note') && typeof change.note !== 'string') throw new Error('La nota debe ser texto.');
  return { ...snapshot, updatedAt: now, entries: { ...snapshot.entries, [id]: { ...snapshot.entries[id], ...change, updatedAt: now } } };
}

export function progressCounts(items: Milestone[], snapshot: MilestoneSnapshot) {
  const required = items.filter(item => !item.optional);
  const completed = required.filter(item => snapshot.entries[item.id]?.status === 'completado').length;
  const optional = items.filter(item => item.optional);
  return { total: required.length, completed, percent: required.length ? Math.round(completed / required.length * 100) : 0,
    optional: optional.length, optionalCompleted: optional.filter(item => snapshot.entries[item.id]?.status === 'completado').length };
}

export function safeJson(value: unknown): string {
  return JSON.stringify(value).replace(/</g, '\\u003c').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');
}
