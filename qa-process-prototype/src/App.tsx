import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { ArrowUpRight, BookOpen, ChevronRight, GitBranch, Map, Maximize2, Minimize2, Network, Search, Upload, X } from 'lucide-react';
import processData from './data/qa-process.json';
import { buildIndex, isGroup, pathTo, validateModel } from './data/model';
import { HexBackground } from './components/HexBackground';
import { DetailsPanel } from './components/DetailsPanel';
import { Roadmap, RoadmapNavigator, roadmapTitle } from './components/Roadmap';
import type { ProcessModel } from './types/architecture';
const initialModel = processData as ProcessModel;
validateModel(initialModel);
const glossary = [
  ['Caso de prueba', 'Qué vamos a comprobar, con qué datos y cuál debería ser el resultado.'],
  ['PR · solicitud de revisión', 'Una propuesta de cambio en el repositorio. El equipo comenta, pide ajustes y aprueba antes de incorporarla.'],
  ['Cobertura', 'Qué reglas o situaciones ya tienen pruebas y cuáles todavía faltan.'],
  ['Pipeline', 'Una secuencia automática que prepara el entorno, ejecuta las pruebas y guarda sus resultados.'],
  ['Regresión', 'Volver a probar para confirmar que una corrección funciona y no rompió otras funciones.'],
  ['Markdown', 'Un archivo de texto fácil de leer, con títulos, pasos y enlaces a la evidencia.'],
  ['Agente y modelo de IA', 'El modelo propone contenido; el agente lo usa junto con información y herramientas para completar una tarea.'],
  ['RAGFlow · segundo cerebro', 'El lugar donde se consulta el conocimiento de la aplicación. La documentación aprobada es su fuente.'],
];
function App() {
  const [model,setModel]=useState<ProcessModel>(initialModel);
  const [expanded,setExpanded]=useState(()=>new Set(initialModel.groups.map(group=>group.id)));
  const [selectedId,setSelectedId]=useState<string|null>(null);
  const [activePhaseId,setActivePhaseId]=useState<string|null>(null);
  const [connectionsGroupId,setConnectionsGroupId]=useState<string|null>(null);
  const [query,setQuery]=useState('');
  const [showGlossary,setShowGlossary]=useState(false);
  const [modelError,setModelError]=useState('');
  const fileInput=useRef<HTMLInputElement>(null);
  const mainRef=useRef<HTMLElement>(null);
  const glossaryPanel=useRef<HTMLElement>(null);
  const index=useMemo(()=>buildIndex(model),[model]);
  const selectedItem=selectedId?index.byId.get(selectedId)??null:null;
  const selectedPath=pathTo(index,selectedId);
  const activeId=selectedPath[0]?.id??activePhaseId;
  const leafCount=[...index.byId.values()].filter(item=>!isGroup(item)).length;
  const allGroupIds=useMemo(()=>[...index.byId.values()].filter(isGroup).map(group=>group.id),[index]);
  const searchResults=useMemo(()=>{
    const term=query.trim().toLocaleLowerCase('es');
    return term.length<2?[]:[...index.byId.values()].filter(item=>`${item.title} ${item.description}`.toLocaleLowerCase('es').includes(term)).slice(0,8);
  },[query,index]);
  function toggle(id:string){setExpanded(previous=>{const next=new Set(previous);next.has(id)?next.delete(id):next.add(id);return next;});}
  function select(id:string){setSelectedId(id);setActivePhaseId(pathTo(index,id)[0]?.id??null);}
  function navigate(id:string){
    const item=index.byId.get(id);if(!item)return;
    const path=pathTo(index,id);const root=path[0]?.id??id;
    setExpanded(previous=>new Set([...previous,...path.map(group=>group.id)]));
    setSelectedId(id);setActivePhaseId(root);
    requestAnimationFrame(()=>{
      const page=mainRef.current;
      const target=document.querySelector(`[data-branch-id="${CSS.escape(id)}"]`)??document.querySelector(`[data-phase-id="${CSS.escape(root)}"]`);
      if(page&&target) page.scrollTo({top:page.scrollTop+target.getBoundingClientRect().top-page.getBoundingClientRect().top-(innerWidth<=700?100:85),behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
    });
  }
  function home(){setSelectedId(null);setConnectionsGroupId(null);mainRef.current?.scrollTo({top:0,behavior:'smooth'});}
  useEffect(()=>{
    const root=mainRef.current;if(!root)return;
    const observer=new IntersectionObserver(entries=>{
      const visible=entries.filter(entry=>entry.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top);
      if(visible[0])setActivePhaseId(visible[0].target.id.replace('phase-',''));
    },{root,rootMargin:'-15% 0px -50% 0px',threshold:0});
    root.querySelectorAll('.roadmap-row').forEach(el=>observer.observe(el));
    return()=>observer.disconnect();
  },[model,expanded]);
  async function loadModel(event:ChangeEvent<HTMLInputElement>){
    const file=event.target.files?.[0];if(!file)return;
    try{const parsed=JSON.parse(await file.text()) as ProcessModel;validateModel(parsed);setModel(parsed);setExpanded(new Set(parsed.groups.map(group=>group.id)));setSelectedId(null);setConnectionsGroupId(null);setModelError('');setQuery('');}
    catch(error){setModelError(error instanceof Error?error.message:'No se pudo abrir el archivo.');}
    event.target.value='';
  }
  const connectionsId=selectedItem?(isGroup(selectedItem)?selectedItem.id:index.parentId.get(selectedItem.id)??null):null;
  return <div className={`app-shell roadmap-app ${selectedItem?'has-inspector':''}`}>
    <HexBackground/>
    <header className="topbar"><button type="button" className="brand" onClick={home} aria-label="Volver al inicio del mapa"><span className="brand-mark"><Network size={22}/></span><span><strong>QA<span className="brand-slash">/</span>ATI</strong><small>MAPA DEL PROCESO</small></span></button><span className="topbar-center">Un proceso compartido por QA, desarrollo e IA</span><div className="topbar-actions"><button type="button" className="utility-button" onClick={()=>setShowGlossary(true)}><BookOpen size={15}/><span>Guía de términos</span></button><input ref={fileInput} type="file" accept=".json,application/json" hidden onChange={event=>void loadModel(event)}/><button type="button" className="utility-button icon-only" aria-label="Cargar otro proceso desde JSON" title="Cargar otro proceso desde JSON" onClick={()=>fileInput.current?.click()}><Upload size={15}/></button></div></header>
    <main ref={mainRef} className="roadmap-page">
      <header className="roadmap-page-heading"><div className="roadmap-breadcrumb"><Map size={13}/> Procesos <ChevronRight size={12}/><span>QA agentizada</span></div><h1>QA agentizada<span className="heading-period">.</span></h1><p>Una guía visual, paso a paso: del conocimiento aprobado a las pruebas y la corrección.</p><div className="roadmap-heading-bottom"><span className="roadmap-tab"><GitBranch size={15}/>Mapa del proceso</span><span>{model.groups.length} fases · {leafCount} actividades · revisión humana</span></div></header>
      {modelError&&<div className="model-error" role="alert">{modelError}<button onClick={()=>setModelError('')} aria-label="Cerrar mensaje"><X size={15}/></button></div>}
      <div className="roadmap-workspace">
        <RoadmapNavigator groups={model.groups} activeId={activeId} onNavigate={navigate}/>
        <section className="roadmap-main" aria-label="Explorar el proceso de QA">
          <div className="roadmap-map-toolbar"><div className="roadmap-zoom-actions"><button type="button" onClick={()=>setExpanded(new Set(allGroupIds))}><Maximize2 size={13}/><span>Expandir todo</span></button><button type="button" onClick={()=>setExpanded(new Set())}><Minimize2 size={13}/><span>Contraer todo</span></button></div><div className="search-wrap"><Search size={14}/><input value={query} onChange={event=>setQuery(event.target.value)} placeholder="Buscar en el mapa…" aria-label="Buscar en el mapa" onKeyDown={event=>{if(event.key==='Escape')setQuery('');}}/>{query&&<button type="button" onClick={()=>setQuery('')} aria-label="Limpiar búsqueda"><X size={13}/></button>}{query.trim().length>=2&&<div className="search-results">{searchResults.length?searchResults.map(item=><button key={item.id} type="button" onClick={()=>{navigate(item.id);setQuery('');}}><span><strong>{roadmapTitle(item.title)}</strong><small>{isGroup(item)?'Desplegar esta parte':'Ver explicación'}</small></span><ArrowUpRight size={12}/></button>):<p>Sin coincidencias.</p>}</div>}</div></div>
          <div className="current-workflow-note"><strong>La base de hoy</strong><p>Documentación funcional y segundo cerebro → casos con Copilot → revisión del equipo → Azure Test Plans → pruebas con Playwright.</p><span><i/>Los recuadros amarillos son herramientas opcionales o reemplazables. La base actual puede seguir funcionando sin incorporarlas.</span></div>
          <p className="roadmap-instruction">Seguí la línea central. Abrí las ramas con <PlusSign/> y seleccioná una actividad para entenderla.</p>
          <Roadmap model={model} index={index} activeId={activeId} selectedId={selectedId} expanded={expanded} onToggle={toggle} onSelect={select} onNavigate={navigate} connectionsGroupId={connectionsGroupId} onCloseConnections={()=>setConnectionsGroupId(null)}/>
          <footer className="roadmap-footnote"><strong>Un diseño para implementar en equipo.</strong><p>n8n coordina el trabajo propuesto. QA y desarrollo aprueban los casos; las herramientas ejecutan y las personas interpretan los resultados.</p><span>Línea continua: avance · Línea punteada: detalle de una fase · Magenta: revisión o retorno</span></footer>
        </section>
      </div>
    </main>
    {selectedItem&&<aside className="roadmap-inspector" aria-label="Explicación de la actividad"><div className="inspector-header"><span>EN ESTA PARTE DEL MAPA</span><button type="button" onClick={()=>setSelectedId(null)} aria-label="Cerrar explicación"><X size={18}/></button></div><div className="inspector-path">{selectedPath.map((group,i)=><span key={group.id}>{i>0&&<ChevronRight size={10}/>}<button onClick={()=>navigate(group.id)}>{roadmapTitle(group.title)}</button></span>)}</div><DetailsPanel model={model} index={index} item={selectedItem} onClose={()=>setSelectedId(null)} onNavigate={navigate}/>{connectionsId&&<button type="button" className="inspector-connections" onClick={()=>{setConnectionsGroupId(connectionsId);navigate(connectionsId);}}><GitBranch size={14}/>Ver conexiones de esta parte<ArrowUpRight size={14}/></button>}</aside>}
    {showGlossary&&<div className="glossary-backdrop" onClick={()=>setShowGlossary(false)}><section ref={glossaryPanel} className="glossary-panel" role="dialog" aria-modal="true" aria-labelledby="glossary-title" onClick={event=>event.stopPropagation()} onKeyDown={event=>{if(event.key==='Escape')setShowGlossary(false);if(event.key==='Tab'){const buttons=glossaryPanel.current?.querySelectorAll<HTMLButtonElement>('button');if(buttons?.length===1){event.preventDefault();buttons[0].focus();}}}}><div className="section-bar"><span className="eyebrow">PARA LEER EL MAPA</span><button type="button" className="utility-button icon-only" aria-label="Cerrar guía" onClick={()=>setShowGlossary(false)} autoFocus><X size={18}/></button></div><h2 id="glossary-title">El mismo idioma,<br/><em>para todo el equipo.</em></h2><dl>{glossary.map(([term,meaning])=><div key={term}><dt>{term}</dt><dd>{meaning}</dd></div>)}</dl></section></div>}
  </div>;
}
function PlusSign(){return <span className="inline-plus">+</span>;}
export default App;
