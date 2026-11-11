# QA ATI · mapa del proceso

Prototipo local con un recorrido vertical y ramas desplegables, inspirado en la estructura de [roadmap.sh / Inference Engineering](https://roadmap.sh/inference-engineering). Mantiene la paleta negra y turquesa del proyecto, con magenta para revisión humana y retornos.

## Explorar

Abrí `dist/index.html`. El archivo incluye su código y estilos; no necesita un servidor para consultar el mapa.

- La línea central conecta las seis fases del proceso.
- Las líneas punteadas muestran qué actividades pertenecen a una fase; no representan el orden de ejecución entre ellas.
- Los botones **+ / −** despliegan o contraen subpartes dentro del mismo mapa, sin límite fijo de profundidad.
- La guía lateral conserva visibles las seis fases. En pantallas chicas aparece como una barra superior.
- Al seleccionar una actividad se abre su explicación a la derecha; en móvil aparece abajo.
- **Ver conexiones de esta parte** abre el flujo de dependencias en el mismo recorrido, con React Flow y posiciones calculadas por ELK. Se pueden seleccionar conexiones para leer su significado.
- La búsqueda abre los grupos necesarios y lleva a la actividad elegida.
- **Expandir todo** revela las 44 actividades; **Contraer todo** conserva las seis fases conectadas.
- **Guía de términos** explica conceptos como caso de prueba, PR, cobertura, pipeline y regresión.
- Los recuadros amarillos indican herramientas opcionales o reemplazables. Cada una explica cómo cubrir hoy la tarea sin incorporarla. El bloque **La base de hoy** resume el proceso actual.

## Proceso revisado

1. Documentación aprobada → repositorio con historial → actualización de RAGFlow → comprobar que el contexto esté listo.
2. Comparar casos actuales → proponer borradores → crear o mejorar sólo si hace falta. Un caso suficiente puede conservarse sin duplicarlo.
3. Propuesta de casos y estimativo de QA → revisión de QA → desarrollo informado, sin autorización obligatoria sobre los casos → registrar la versión lista. Los ajustes pedidos por QA vuelven a diseño.
4. Registrar el caso → escribir el test con ayuda de Copilot → revisar el código → ejecutar Playwright. Schemathesis y Hercules son opciones adicionales.
5. QA interpreta los resultados: registrar una prueba conforme, corregir una prueba o su ambiente, aclarar una regla o confirmar un defecto del producto.
6. Defecto confirmado → Markdown para desarrollo → propuesta de corrección → revisión del código → nueva ejecución → QA confirma el cierre con evidencia nueva.

Las nuevas reglas vuelven a documentación y pasan por el repositorio antes de actualizar RAGFlow. Un problema de datos o ambiente se corrige antes de repetir una ejecución.

El fondo incluye una trama de hexágonos turquesa conectados. Cerca del cursor se iluminan en fucsia con una respiración suave; el resplandor se desvanece al salir. El dibujo no captura clics, respeta la preferencia de movimiento reducido y detiene la animación cuando no está activa.

## Fuente y componentes

`src/data/qa-process.json` contiene 6 fases, 45 actividades, 83 relaciones y 16 retornos entre niveles. No contiene coordenadas ni estilos. Los campos opcionales `owner`, `milestones` y `entryCondition` expresan responsables, resúmenes y condiciones del proceso.

- `src/components/Roadmap.tsx`: recorrido, ramas anidadas, conectores medidos sobre el diseño y guía persistente.
- `src/components/DetailsPanel.tsx`: explicación, entradas, salidas, intervención humana y conexiones.
- `src/components/ProcessDiagram.tsx`: grafo detallado de dependencias con React Flow.
- `src/layout/elkLayout.ts`: posiciones calculadas para el grafo de dependencias.
- `src/data/model.ts`: índice, navegación y validación del modelo.
- `src/App.tsx`: búsqueda, carga de JSON y coordinación de las vistas.
- `src/styles.css`: paleta, estilos y adaptación a tamaños de pantalla.

El botón de carga permite abrir otro JSON compatible localmente, sin enviarlo a un servidor. Los estados actual, propuesto y opcional se explican en los detalles de cada actividad.

## Desarrollo y verificación

```bash
pnpm install
pnpm dev
pnpm check:model
pnpm check:flow
pnpm check:milestones
pnpm build
```

Se revisaron el modelo sin coordenadas, diez controles del proceso y la compilación TypeScript/Vite. En la vista de desarrollo se comprobaron las ramas, expansión y contracción completas, búsqueda, explicación lateral, conexiones internas y ausencia de desbordamiento horizontal en 1440 × 1000 y 390 × 844.

Este mapa documenta el diseño. El Hito 2 comprobó una instancia local de RAGFlow y su consulta mediante scripts; la conexión con el entorno del equipo, Copilot, n8n, Azure y los ejecutores requiere los siguientes ensayos.

## Hitos de implementación y archivo compartible

La pestaña **Hitos de implementación** ofrece 29 hitos: 26 para la base y 3 evaluaciones opcionales. Se pueden marcar como pendientes, en curso, completados o bloqueados, y agregar notas o evidencia. Empiezan completados la elección del piloto y los scripts iniciales, más tres avances técnicos del **Hito 2**: RAGFlow local operativo por API, contexto compacto con fuentes y pruebas técnicas de recuperación. Son **5 de 26 hitos de base (19%)**. La calidad del retrieval queda en curso hasta la revisión de utilidad con QA y Copilot. No se marcaron como hechas la generación de casos, las integraciones con Azure o la actualización del conocimiento.

El mapa incorpora la capa de scripts de retrieval antes de diseñar los casos. QA define el alcance estimado y revisa las pruebas; desarrollo conoce la propuesta y puede aportar contexto, pero no la autoriza ni bloquea su avance. La revisión técnica del código sigue siendo un paso separado.

El avance se guarda en el almacenamiento de este navegador cuando está disponible. **Descargar HTML con avances** incluye el estado y las notas dentro de un nuevo HTML autónomo para compartirlo o trasladarlo. Si el navegador bloquea el almacenamiento de archivos locales, la descarga sigue disponible. Los navegadores y dispositivos no se sincronizan entre sí; se comparte la copia descargada. El archivo original del disco no se modifica automáticamente.

`src/data/implementation-plan.json` define el plan; `src/data/milestones.ts` valida y combina avances; `src/data/portable.ts` carga los datos incluidos y genera la descarga autónoma; `src/components/Milestones.tsx` presenta el gráfico de hitos. Los scripts embebidos `qa-process-state` y `qa-milestone-state` permiten reabrir una copia con su modelo y avance.

## Reporte Hito 2

`../informes/Hito-2.html` es el reporte autónomo y editable de esta etapa. Su copia en `public/Hito-2.html` permite abrirlo desde la pestaña de hitos y Vite la incluye en `dist`. Al actualizar el reporte, mantener ambas copias iguales. El reporte conserva resultados, límites y una comparación interactiva de las entregas; no necesita servidor ni recursos externos. La copia principal del mapa es `../informes/Mapa-QA-agentizada.html`.
