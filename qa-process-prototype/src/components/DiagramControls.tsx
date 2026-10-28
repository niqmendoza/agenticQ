import { Maximize2, RotateCcw } from 'lucide-react';
import { useReactFlow } from '@xyflow/react';

export function DiagramControls({ onOverview, isOverview }: { onOverview: () => void; isOverview: boolean }) {
  const { fitView } = useReactFlow();
  return (
    <div className="diagram-actions" aria-label="Controles del diagrama">
      <button type="button" onClick={() => void fitView({ padding: 0.17, duration: 450 })} title="Mostrar todo este nivel"><Maximize2 size={16} /><span>Ver todo</span></button>
      {!isOverview && <button type="button" onClick={onOverview} title="Volver al nivel anterior"><RotateCcw size={16} /><span>Volver un nivel</span></button>}
    </div>
  );
}
