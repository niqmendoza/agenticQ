export type NodeKind =
  | 'process' | 'agent' | 'human' | 'decision' | 'tool' | 'model'
  | 'artifact' | 'external-system' | 'validation' | 'input' | 'output';

export type RelationKind = 'normal' | 'conditional' | 'feedback' | 'async' | 'human-approval' | 'data';
export type RolloutStatus = 'actual' | 'propuesto' | 'opcional';

export interface HumanInteraction {
  required: boolean;
  description: string;
}

export interface ProcessDetails {
  objective: string;
  howItWorks: string;
  validationCriteria: string[];
}

export interface ProcessLeaf {
  id: string;
  type: NodeKind;
  title: string;
  shortDescription: string;
  description: string;
  responsibilities: string[];
  inputs: string[];
  outputs: string[];
  tools: string[];
  agents: string[];
  humanInteraction: HumanInteraction;
  details: ProcessDetails;
  status?: RolloutStatus;
  currentAlternative?: string;
}

export interface ProcessGroup {
  id: string;
  type: 'group';
  title: string;
  description: string;
  children: ProcessItem[];
  milestones?: string[];
  owner?: string;
  entryCondition?: string;
}

export type ProcessItem = ProcessGroup | ProcessLeaf;

export interface ProcessEdge {
  id: string;
  source: string;
  target: string;
  type: RelationKind;
  label: string;
}

export interface ProcessModel {
  title: string;
  description: string;
  modelVersion?: string;
  scope?: Record<string, string[]>;
  groups: ProcessGroup[];
  edges: ProcessEdge[];
}

export interface ModelIndex {
  byId: Map<string, ProcessItem>;
  parentId: Map<string, string | null>;
}

export interface VisibleRelation extends ProcessEdge {
  count: number;
  originalIds: string[];
}
