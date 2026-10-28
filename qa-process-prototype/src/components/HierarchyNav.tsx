import { useState } from 'react';
import { ChevronDown, ChevronRight, Layers3 } from 'lucide-react';
import { isGroup } from '../data/model';
import type { ProcessGroup, ProcessItem } from '../types/architecture';

function TreeItem({ item, depth, activeGroupId, selectedId, onNavigate }: {
  item: ProcessItem;
  depth: number;
  activeGroupId: string | null;
  selectedId: string | null;
  onNavigate: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(depth === 0);
  const group = isGroup(item);
  return <div className="tree-branch">
    <div className={`tree-row ${activeGroupId === item.id || selectedId === item.id ? 'tree-active' : ''}`} style={{ paddingLeft: `${13 + depth * 15}px` }}>
      {group ? <button type="button" className="tree-toggle" onClick={() => setExpanded(value => !value)} aria-label={`${expanded ? 'Contraer' : 'Expandir'} ${item.title}`} aria-expanded={expanded}>{expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</button> : <span className="tree-bullet" />}
      <button type="button" className="tree-label" onClick={() => onNavigate(item.id)} title={item.title}>{item.title}</button>
    </div>
    {group && expanded && <div>{item.children.map(child => <TreeItem key={child.id} item={child} depth={depth + 1} activeGroupId={activeGroupId} selectedId={selectedId} onNavigate={onNavigate} />)}</div>}
  </div>;
}

export function HierarchyNav({ groups, activeGroupId, selectedId, onNavigate, onOverview }: {
  groups: ProcessGroup[];
  activeGroupId: string | null;
  selectedId: string | null;
  onNavigate: (id: string) => void;
  onOverview: () => void;
}) {
  return <nav className="hierarchy-nav" aria-label="Jerarquía del proceso">
    <div className="side-heading"><span>EXPLORAR</span><span>{groups.length} fases</span></div>
    <button type="button" className={`overview-link ${activeGroupId === null ? 'active' : ''}`} onClick={onOverview}><Layers3 size={17} /> Vista general</button>
    <div className="tree-list">{groups.map(group => <TreeItem key={group.id} item={group} depth={0} activeGroupId={activeGroupId} selectedId={selectedId} onNavigate={onNavigate} />)}</div>
  </nav>;
}
