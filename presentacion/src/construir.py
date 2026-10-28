from pathlib import Path
import base64,json,html,re
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
old=json.loads((ROOT/'archivo-40-slides/contenido.json').read_text())
slides=[]
hero='data:image/png;base64,'+base64.b64encode((ROOT/'assets/conocimiento-volumen.png').read_bytes()).decode()
def add(title,lead,body,detail,theme='',chapter=''):
    if body.startswith('<svg') and len(slides)!=10:
        body=body.replace('fill="var(--paper)"',f'fill="url(#depth-{len(slides)})"').replace('fill="var(--surface)"',f'fill="url(#depth-{len(slides)})"')
    slides.append(dict(title=title,lead=lead,body=body,detail=detail,theme=theme,chapter=chapter))
def svg_start(label,w=1312,h=400):
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{label}" class="graphic"><defs><linearGradient id="depth-{len(slides)}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#305c87"/><stop offset=".3" stop-color="#163a5d"/><stop offset="1" stop-color="#0b1d30"/></linearGradient><marker id="arr-{len(slides)}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="currentColor" stroke-width="1.4"/></marker></defs>'
def st(x,y,text,size=28,fill='var(--ink)',weight=450,anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'+''.join(f'<tspan x="{x}" dy="{0 if i==0 else size*1.33}">{html.escape(t)}</tspan>' for i,t in enumerate(text.split('|')))+'</text>'
def line(d,color='var(--accent)',dash=''):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" {f"stroke-dasharray={chr(34)}{dash}{chr(34)}" if dash else ""} marker-end="url(#arr-{len(slides)})"/>'
def pill(x,y,label,w=220,color='var(--accent)'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="58" rx="29" fill="none" stroke="{color}" stroke-width="1.7"/>'+st(x+w/2,y+37,label,24,color,550,'middle')
def band(t):return '<div class="bottom-note">'+t+'</div>'
add('QA con Copilot','Propuesta para ampliar la capacidad de pruebas y mantener el conocimiento de cada sistema.', '<div class="cover-art"><img src="'+hero+'" alt=""></div><div class="cover-context">El workbook actual es la base del piloto.</div><div class="cover-route"><span>Conocimiento</span><i>→</i><span>Casos y pruebas</span><i>→</i><span>Resultados</span></div><div class="cover-caption">Propuesta de primer piloto · QA, Desarrollo y Negocio</div>',[1,2,3],'cover','Propuesta de trabajo')
add('Punto de partida','Ya tenemos una base de trabajo. La propuesta la conecta y le agrega continuidad.', '<div class="comparison"><div class="compare-column"><span class="eyebrow">Hoy</span><h2>Workbook + Copilot</h2><p>Diseño de casos, exploración web, reportes y Markdown para reproducir bugs.</p><div class="existing">Playwright MCP<br>Herramientas de automatización<br>Azure DevOps</div></div><div class="compare-join">→</div><div class="compare-column"><span class="eyebrow">Propuesta</span><h2>Un ciclo mantenible</h2><p>Conocimiento validado, pruebas reutilizables y relaciones claras entre cambios y resultados.</p><div class="proposed">Documentos con historial<br>Casos vinculados a reglas<br>Ejecuciones repetibles</div></div></div>'+band('Buscamos cubrir más trabajo con la capacidad disponible. El ahorro todavía se tiene que medir.'),[2,3,6],chapter='Contexto')
g=svg_start('Ocho etapas del trabajo por flujo',h=385)
coords=[(35,75),(370,75),(705,75),(1040,75),(1040,275),(705,275),(370,275),(35,275)]
labels=[('Conocimiento','Fuentes y dependencias'),('Borrador funcional','Proceso y excepciones'),('Validación','Reglas y dudas críticas'),('Casos','Esperado y cobertura'),('Automatización','Datos y verificaciones'),('Ejecución','Prueba y evidencia'),('Reporte','Diagnóstico y defectos'),('Mantenimiento','Cambio y versión')]
g+=line('M 82 64 H 1295 V 249 H 82',color='var(--softline)')
for i,((x,y),(title,sub)) in enumerate(zip(coords,labels)):
    g+=f'<circle cx="{x+20}" cy="{y-15}" r="25" fill="var(--paper)" stroke="var(--accent)" stroke-width="1.5"/>'+st(x+20,y-6,str(i+1),24,'var(--accent)',550,'middle')+st(x,y+54,title,29,'var(--ink)',550)+st(x,y+94,sub,23,'var(--muted)')
g+='</svg>'
add('Recorrido de trabajo','Trabajamos por aplicación, módulo o flujo, sin esperar a documentar toda la compañía.',g+band('Cada etapa deja un entregable para la siguiente. Un cambio vuelve a abrir el ciclo.'),[7,8],chapter='Proceso')
g=svg_start('Fuentes, documentación y validación del conocimiento',h=350)
g+=st(35,37,'Fuentes disponibles',22,'var(--muted)',450)+st(35,99,'Código|Tickets|Pruebas y accesos',30,'var(--ink)',500)
g+=line('M 290 142 H 380')
g+='<path d="M 420 40 H 630 L 666 76 V 250 H 420 Z M 630 40 V 76 H 666" fill="var(--surface)" stroke="var(--accent)" stroke-width="2"/>'
g+=st(446,113,'Notas técnicas',29,'var(--ink)',550)+st(446,156,'Qué hace el sistema',22,'var(--muted)')+st(446,199,'Reglas del proceso',23,'var(--accent)',550)+st(446,229,'Qué debería pasar',22,'var(--muted)')+line('M 685 142 H 780')
g+=f'<circle cx="925" cy="105" r="50" fill="var(--surface)" stroke="var(--accent)" stroke-width="2"/>'+st(925,118,'QA',32,'var(--accent)',550,'middle')+st(817,208,'Validación del proceso',29,'var(--ink)',550)+st(817,248,'Negocio o responsable|confirma reglas y excepciones',23,'var(--muted)')
g+=line('M 1102 142 H 1190')+st(1197,134,'Versión',25,'var(--accent)',550)+st(1197,167,'aprobada',25,'var(--accent)',550)+st(35,336,'Cada nota conserva fuente, versión, estado de validación y responsable.',23,'var(--muted)')+'</svg>'
add('Conocimiento compartido','Copilot prepara notas y documentación funcional. Las personas confirman las reglas críticas.',g+band('La IA reconstruye lo implementado. La revisión define lo correcto para el negocio.'),[9,10,11,12,13,14,15,16,17],chapter='Conocimiento')
add('Cómo elegimos lo esperado','Los casos combinan una regla validada con la información técnica necesaria para comprobarla.', '<div class="case-story"><div class="case-rule"><span class="eyebrow">Regla ilustrativa</span><h2>Cancelar un pedido pendiente libera su stock reservado.</h2><p>QA revisa condiciones, excepciones y cobertura.</p></div><div class="case-details"><div><span>Preparación</span><p>Pedido pendiente con una reserva identificada.</p></div><div><span>Acción</span><p>Cancelar el pedido.</p></div><div><span>Verificación</span><p>Estado correcto y reserva liberada.</p></div></div></div><div class="trace"><span>Regla</span><i>→</i><span>Caso</span><i>→</i><span>Prueba</span><i>→</i><span>Evidencia</span></div>'+band('Test Plans conserva los casos. Boards vincula el trabajo. Azure Repos guarda la prueba reutilizable.'),[18,19,20],theme='dark',chapter='Casos')
g=svg_start('Copilot conectado a herramientas según el sistema',h=410)
g+=pill(35,165,'Copilot',245)
g+=line('M 280 194 H 340 V 69 H 445')+line('M 340 194 H 445')+line('M 340 194 V 319 H 445')
g+=st(470,47,'Trabajo y trazabilidad',28,'var(--ink)',550)+st(470,85,'Azure DevOps MCP propuesto',23,'var(--accent)',500)+st(865,48,'Boards · Test Plans',26,'var(--ink)',500)+st(865,83,'Repos · Pipelines',26,'var(--ink)',500)+line('M 815 67 H 850')
g+=st(470,172,'Interfaz web',28,'var(--ink)',550)+st(470,210,'Playwright MCP del workbook',23,'var(--accent)',500)+st(865,188,'Navegar y explorar',26,'var(--ink)',500)+line('M 815 192 H 850')
g+=st(470,297,'Servicios y datos',28,'var(--ink)',550)+st(470,335,'Pruebas y consultas',23,'var(--accent)',500)+st(865,314,'Verificar resultados',26,'var(--ink)',500)+line('M 815 317 H 850')
g+=st(35,397,'La herramienta se elige según la tecnología, también en sistemas antiguos.',23,'var(--muted)')+'</svg>'
add('Herramientas según cada sistema','Copilot usa conexiones y operaciones permitidas. Las nuevas integraciones se validan en el piloto.',g,[21,22,23],chapter='Herramientas')
add('Comprobaciones de negocio','Una respuesta exitosa no alcanza. La prueba verifica la regla y sus efectos.', '<div class="business-check"><div class="request"><span class="eyebrow">Ejemplo de cancelación</span><h2>El sistema respondió</h2><span class="http-code">HTTP 200</span><p>La operación devolvió una respuesta técnica exitosa.</p></div><div class="check-arrow">→</div><div class="checks"><h2>QA comprueba el resultado</h2><p><b>Estado:</b> el pedido quedó cancelado.</p><p><b>Stock:</b> se liberó la reserva correcta.</p><p><b>Excepciones:</b> se respetaron los estados prohibidos.</p></div></div>'+band('Para consultar la base, el agente elige una operación aprobada. El ejecutor y los permisos de lectura fijan el alcance.'),[24,25,26,27],chapter='Verificaciones')
add('Ejecución y diagnóstico','La exploración deja una prueba revisada y guardada. Pipelines la ejecuta cada vez que hace falta.', '<div class="execution"><div class="exec-path"><span>Prueba reutilizable</span><i>→</i><span>Ejecución</span><i>→</i><span>Evidencia</span></div><div class="diagnosis"><div><span class="diagnosis-code">P</span><h2>Producto</h2><p>Contradice la regla validada.</p></div><div><span class="diagnosis-code">A</span><h2>Ambiente</h2><p>Datos, acceso o servicio impiden evaluar.</p></div><div><span class="diagnosis-code">T</span><h2>Prueba</h2><p>Falla el script o su preparación.</p></div></div></div>'+band('QA clasifica los fallos. Solo los defectos confirmados se registran en Boards con reproducción y evidencia.'),[28,29,30],theme='dark',chapter='Resultados')
add('Mantenimiento por versión','Cada cambio actualiza conocimiento, documentación, casos y automatizaciones relacionadas.', '<div class="maintenance"><div class="maint-path"><span>Cambio en Boards</span><i>→</i><span>Aporte de Desarrollo</span><i>→</i><span>Revisión y publicación</span></div><div class="version-row"><div class="version-label"><span class="eyebrow">Ejemplo ilustrativo</span><h2>La versión desplegada define qué probar</h2></div><div class="version"><strong>2.5</strong><span>En Desarrollo</span><p>Documento del cambio nuevo</p></div><div class="version current"><strong>2.4</strong><span>Ambiente QA</span><p>Documento y pruebas de 2.4</p></div></div></div>'+band('Cada corrida identifica sistema, ambiente y revisiones de documentos y pruebas. Los documentos más nuevos pueden adelantarse a QA.'),[31,32,33,34],chapter='Cambios')
add('Primer piloto','Una aplicación, pocos flujos críticos y una validación de datos.', '<div class="pilot"><div class="pilot-scope"><span class="eyebrow">Entrega concreta</span><h2>Un flujo completo</h2><div class="pilot-route"><span>Documento aprobado</span><span>Caso trazable</span><span>Prueba reutilizable</span><span>Ejecución con evidencia</span><span>Mantenimiento probado</span></div></div><div class="pilot-roles"><div><b>Desarrollo</b><span>Aporta cambios y dependencias.</span></div><div><b>QA</b><span>Evalúa cobertura, pruebas y fallos.</span></div><div><b>Negocio / responsable</b><span>Valida las reglas del proceso.</span></div><div><b>Responsable del conocimiento</b><span>Coordina revisión y publicación.</span></div></div></div>'+band('Reusamos lo existente. El piloto confirma responsables, ambiente, tecnología y conexiones.'),[5,35,36],chapter='Piloto')
integral=old[38]['body']
integral=re.sub(r'<p class="micro">.*?</p>','',integral,flags=re.S).replace('class="integral"','class="integral graphic"').replace('#76e6d0','#b6d8fa').replace('#d5f78a','#dfcfac').replace('#edb8de','#d8b4ed').replace('#172431','#182737')
integral=integral.replace('<defs>','<defs><linearGradient id="node-volume" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#244563"/><stop offset=".15" stop-color="#18324c"/><stop offset="1" stop-color="#102438"/></linearGradient>')
add('Sistema integrado','El conocimiento aprobado guía las pruebas. Los cambios y resultados vuelven al conocimiento.', integral,[38,39],theme='dark system',chapter='Visión completa')
add('Qué medimos y cómo seguimos','El piloto crea la línea de base para decidir si conviene extender este modo de trabajo.', '<div class="measurement"><div class="measure-list"><div><h2>Tiempo total</h2><p>Por automatización aceptada, con revisión y mantenimiento.</p></div><div><h2>Estabilidad y cobertura</h2><p>Fallos intermitentes y reglas críticas que podemos comprobar.</p></div><div><h2>Defectos y conocimiento</h2><p>Defectos confirmados y recuperación correcta de información.</p></div></div><div class="decision"><span class="eyebrow">Siguiente decisión</span><h2>Elegir el flujo y los responsables del piloto</h2><p>Evaluar entregables y resultados antes de ampliar el alcance.</p><button class="source-button" data-sources>Fuentes y supuestos técnicos ↗</button></div></div>'+band('La capacidad se tiene que medir. Ahorro y cambios de dotación son objetivos, todavía no son resultados.'),[37,40],chapter='Evaluación')
assert len(slides)==12
# Keep all the agreed detail readable in per-slide drawers, without loading the main canvas.
class Blocks(HTMLParser):
 def __init__(self):super().__init__();self.out=[];self.buf=[];self.kind=None;self.depth=0;self.skip=0
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if t=='svg':self.skip+=1
  if self.skip:return
  if t=='br':
   if self.kind:self.buf.append(' ')
   return
  if self.kind:self.depth+=1
  elif t in ['h3','p','pre','b'] or a.get('class') in ['callout','label','note-heading','checkline','result-line','circuit-end','source-footer']:
   self.kind='h3' if t in ['h3','b'] else 'p';self.depth=1;self.buf=[]
  if t=='br' and self.kind:self.buf.append('\n')
 def handle_endtag(self,t):
  if t=='svg':self.skip=max(0,self.skip-1);return
  if self.skip:return
  if self.kind:
   self.depth-=1
   if self.depth==0:
    txt=' '.join(''.join(self.buf).split())
    if txt:self.out.append((self.kind,txt))
    self.kind=None
 def handle_data(self,d):
  if self.kind and not self.skip:self.buf.append(d)
def detail_html(nums):
 sections=[]
 for n in nums:
  s=old[n-1];p=Blocks();p.feed(s['body'])
  # The final integrated SVG is already shown in the main canvas. Include its explicit reading description.
  if n==9:p.out.append(('p','Las notas relacionan código, reglas, datos y dependencias del flujo.'))
  if n==39:p.out=[('p','Fuentes y cambios alimentan notas y borradores de Copilot. QA o negocio validan las reglas. Azure Repos aprueba una revisión. El buscador publica esa versión. Copilot prepara casos y usa herramientas UI, API y SQL permitidas. Las pruebas aceptadas quedan en Repos. Pipelines ejecuta y guarda evidencia. QA clasifica los fallos y Boards conserva bugs y features con vínculos. El cambio vuelve al conocimiento.')]
  
  if n==15:p.out.insert(0,('p','Ejemplo ilustrativo: dos modelos aceptan un descuento del 20% aunque la regla real permite el 10%. Compartir un error de origen sigue siendo posible.'))
  title=s['title']
  if n==1:continue
  content=''.join(f'<{tag}>{html.escape(text)}</{tag}>' for tag,text in p.out)
  sections.append(f'<article class="detail-section"><h2>{html.escape(title)}</h2><p class="detail-lead">{html.escape(s["lead"])}</p>{content}</article>')
 return ''.join(sections)
css=(ROOT/'src/estilos.css').read_text();js=(ROOT/'src/navegacion.js').read_text();font=base64.b64encode((ROOT/'fuentes/Saira-variable.ttf').read_bytes()).decode();license=(ROOT/'fuentes/OFL-Saira.txt').read_text()
sections=[];drawers=[]
for i,s in enumerate(slides):
 sections.append(f'<section class="slide {s["theme"]}" id="slide-{i+1}" aria-labelledby="title-{i+1}" aria-hidden="{str(i!=0).lower()}" '+('inert' if i else '')+f'><div class="slide-header"><span>{s["chapter"]}</span><span>QA con Copilot</span></div><h1 id="title-{i+1}">{('QA con <br><span>Copilot</span>' if i==0 else s["title"])}</h1><p class="lead">{s["lead"]}</p><div class="slide-body">{s["body"]}</div><div class="slide-footer"><button data-detail="{i}">Ampliar este tema <span>↗</span></button><span>{i+1:02} / 12</span></div></section>')
 drawers.append(f'<template id="detail-{i}">{detail_html(s["detail"])}</template>')
index=''.join(f'<button data-slide="{i}"><span>{i+1:02}</span>{html.escape(s["title"])}</button>' for i,s in enumerate(slides))
sources=old[39]['body'].replace('<button class="text-button" data-license>','<button class="text-button" data-license>')
output='''<!DOCTYPE html><html lang="es-AR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><title>QA con Copilot · Presentación</title><style>@font-face{font-family:Saira;src:url(data:font/ttf;base64,'''+font+''') format('truetype');font-weight:100 900;font-stretch:50% 125%;font-style:normal;font-display:block}'''+css+'''</style></head><body><main id="viewport" aria-label="Presentación QA con Copilot"><div id="stage">'''+''.join(sections)+'''</div></main><nav class="controls" aria-label="Controles de presentación"><button id="prev" aria-label="Slide anterior" title="Anterior (←)">←</button><div class="counter" aria-live="polite"><span id="count">01</span><span>/ 12</span></div><button id="next" aria-label="Slide siguiente" title="Siguiente (→)">→</button><div class="progress" aria-hidden="true"><div id="bar"></div></div><button id="index">Índice</button><button id="detailNav" title="Ampliar tema (D)">Detalle</button><button id="full" title="Pantalla completa (F)" aria-label="Activar pantalla completa">⛶</button><button id="help" title="Ayuda (?)" aria-label="Ayuda">?</button></nav><dialog id="toc"><div class="dialog-head"><h2>Índice</h2><button data-close aria-label="Cerrar índice">×</button></div><div class="toc-grid">'''+index+'''</div></dialog><dialog id="detailDialog"><div class="dialog-head"><h2 id="detailTitle">Detalle</h2><button data-close aria-label="Cerrar detalle">×</button></div><div id="detailContent" class="detail-content"></div></dialog><dialog id="sourcesDialog"><div class="dialog-head"><h2>Fuentes y supuestos técnicos</h2><button data-close aria-label="Cerrar fuentes">×</button></div>'''+sources+'''</dialog><dialog id="helpDialog"><div class="dialog-head"><h2>Cómo recorrer la presentación</h2><button data-close aria-label="Cerrar ayuda">×</button></div><div class="help-copy"><p>Usá <b>← / →</b> o los botones para avanzar.<br><b>Espacio / Page Down</b>: siguiente. <b>Page Up</b>: anterior.<br><b>Inicio / Fin</b>: primera / última slide.</p><p><b>I</b>: índice. <b>D</b>: ampliar el tema. <b>F</b>: pantalla completa.<br><b>Esc</b>: cerrar la ventana.</p><p>Las 12 slides muestran el recorrido principal. <b>Ampliar este tema</b> conserva el detalle del proceso y las decisiones técnicas.</p><p>En celular podés desplazarte hacia abajo. El diagrama completo permite desplazamiento horizontal.</p><p>El HTML funciona offline y no necesita instalación. Los enlaces a fuentes oficiales requieren Internet.</p><p>Podés imprimir las 12 slides en orientación horizontal desde el navegador.</p></div></dialog><dialog id="licenseDialog"><div class="dialog-head"><h2>Saira · SIL Open Font License 1.1</h2><button data-close aria-label="Cerrar licencia">×</button></div><pre class="license">'''+html.escape(license)+'''</pre></dialog>'''+''.join(drawers)+'''<div id="status" role="status"></div><noscript><style>body{overflow:auto}#viewport{height:auto;overflow:visible}#stage{width:100%;height:auto;transform:none!important}.slide{position:relative;display:flex!important}.controls{display:none}</style>Sin JavaScript, podés leer las slides desplazándote por la página.</noscript><script>'''+js+'''</script></body></html>'''
(ROOT/'QA-agentizada.html').write_text(output);(ROOT/'src/contenido.json').write_text(json.dumps(slides,ensure_ascii=False,indent=2))
print('12 slides + detalle por tema. HTML:',len(output),'caracteres')
