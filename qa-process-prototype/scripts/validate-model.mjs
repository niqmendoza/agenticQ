import { readFileSync } from 'node:fs';

const model = JSON.parse(readFileSync(new URL('../src/data/qa-process.json', import.meta.url), 'utf8'));
const byId = new Map();
const allowedKinds = new Set(['process','agent','human','decision','tool','model','artifact','external-system','validation','input','output']);
const allowedRelations = new Set(['normal','conditional','feedback','async','human-approval','data']);

function visit(node) {
  if (!node.id || byId.has(node.id)) throw new Error(`ID faltante o duplicado: ${node.id}`);
  byId.set(node.id, node);
  if (node.type === 'group') {
    if (!Array.isArray(node.children) || !node.children.length) throw new Error(`Grupo vacío: ${node.id}`);
    node.children.forEach(visit);
  } else {
    if (!allowedKinds.has(node.type)) throw new Error(`Tipo no reconocido: ${node.id}`);
    for (const field of ['title','shortDescription','description','responsibilities','inputs','outputs','tools','agents','humanInteraction','details']) {
      if (node[field] === undefined) throw new Error(`Falta ${field} en ${node.id}`);
    }
    for (const field of ['objective','howItWorks','validationCriteria']) {
      if (!node.details[field]) throw new Error(`Falta details.${field} en ${node.id}`);
    }
  }
}

model.groups.forEach(visit);
const edgeIds = new Set();
for (const edge of model.edges) {
  if (edgeIds.has(edge.id)) throw new Error(`Relación duplicada: ${edge.id}`);
  edgeIds.add(edge.id);
  if (!allowedRelations.has(edge.type)) throw new Error(`Tipo de relación no reconocido: ${edge.id}`);
  if (!byId.has(edge.source) || !byId.has(edge.target)) throw new Error(`Extremo inexistente: ${edge.id}`);
}

function checkNoCoordinates(value) {
  if (!value || typeof value !== 'object') return;
  for (const [key, child] of Object.entries(value)) {
    if (['x','y','position','coordinates'].includes(key)) throw new Error(`Coordenada prohibida: ${key}`);
    checkNoCoordinates(child);
  }
}
checkNoCoordinates(model);
const leafCount = [...byId.values()].filter(node => node.type !== 'group').length;
const feedbackCount = model.edges.filter(edge => edge.type === 'feedback').length;
console.log(`Modelo válido: ${model.groups.length} fases, ${leafCount} nodos de detalle, ${model.edges.length} relaciones, ${feedbackCount} retornos.`);
