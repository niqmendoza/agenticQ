import { validateModel } from './model.ts';
import type { ProcessModel } from '../types/architecture';
import { mergeProgress, parseSnapshot, safeJson, type ImplementationPlan, type MilestoneSnapshot } from './milestones.ts';

export function readEmbeddedModel(fallback: ProcessModel): ProcessModel {
  try {
    const raw = document.getElementById('qa-process-state')?.textContent;
    if (!raw?.trim() || raw.trim() === 'null') return fallback;
    const parsed = JSON.parse(raw) as ProcessModel;
    validateModel(parsed);
    return parsed;
  } catch { return fallback; }
}

export function progressStorageKey(): string {
  return `qa-ati-implementation-v1:${window.location.pathname}`;
}

export function readProgress(plan: ImplementationPlan): MilestoneSnapshot {
  const candidates: MilestoneSnapshot[] = [];
  const embedded = document.getElementById('qa-milestone-state')?.textContent;
  if (embedded?.trim()) { try { candidates.push(parseSnapshot(embedded, plan)); } catch { /* Keep a valid baseline if an old embedded format is encountered. */ } }
  try {
    const stored = localStorage.getItem(progressStorageKey());
    if (stored) candidates.push(parseSnapshot(stored, plan));
  } catch { /* The HTML remains usable if this browser blocks storage for local files. */ }
  return mergeProgress(plan, candidates);
}

export function rememberProgress(snapshot: MilestoneSnapshot): boolean {
  try { localStorage.setItem(progressStorageKey(), safeJson(snapshot)); return true; } catch { return false; }
}

export function standaloneHTML(source: Document, model: ProcessModel, progress: MilestoneSnapshot): string {
  const copy = source.documentElement.cloneNode(true) as HTMLElement;
  copy.querySelector('#root')?.replaceChildren();
  for (const [id, content] of [['qa-process-state', model], ['qa-milestone-state', progress]] as const) {
    let block = copy.querySelector<HTMLScriptElement>(`#${id}`);
    if (!block) { block = source.createElement('script'); block.id = id; block.type = 'application/json'; copy.querySelector('body')?.append(block); }
    block.textContent = safeJson(content);
  }
  return '<!doctype html>\n' + copy.outerHTML;
}

export function saveStandalone(model: ProcessModel, progress: MilestoneSnapshot) {
  const blob = new Blob([standaloneHTML(document, model, progress)], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url; link.download = 'Mapa-QA-agentizada-con-avances.html';
  link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
