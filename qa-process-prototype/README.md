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
3. PR de casos → aprobación de QA y desarrollo sobre la misma versión → incorporar la propuesta aprobada. Los cambios pedidos vuelven a diseño.
4. Registrar el caso → escribir el test con ayuda de Copilot → revisar el código → ejecutar Playwright. Schemathesis y Hercules son opciones adicionales.
5. QA interpreta los resultados: registrar una prueba conforme, corregir una prueba o su ambiente, aclarar una regla o confirmar un defecto del producto.
6. Defecto confirmado → Markdown para desarrollo → propuesta de corrección → revisión del código → nueva ejecución → QA confirma el cierre con evidencia nueva.

Las nuevas reglas vuelven a documentación y pasan por el repositorio antes de actualizar RAGFlow. Un problema de datos o ambiente se corrige antes de repetir una ejecución.

El fondo incluye una trama de hexágonos turquesa conectados. Cerca del cursor se iluminan en fucsia con una respiración suave; el resplandor se desvanece al salir. El dibujo no captura clics, respeta la preferencia de movimiento reducido y detiene la animación cuando no está activa.

## Fuente y componentes

`src/data/qa-process.json` contiene 6 fases, 44 actividades, 81 relaciones y 16 retornos entre niveles. No contiene coordenadas ni estilos. Los campos opcionales `owner`, `milestones` y `entryCondition` expresan responsables, resúmenes y condiciones del proceso.

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
pnpm build
```

Se revisaron el modelo sin coordenadas, diez controles del proceso y la compilación TypeScript/Vite. En la vista de desarrollo se comprobaron las ramas, expansión y contracción completas, búsqueda, explicación lateral, conexiones internas y ausencia de desbordamiento horizontal en 1440 × 1000 y 390 × 844.

Este prototipo documenta el diseño. Las integraciones con n8n, RAGFlow, Azure y los ejecutores de pruebas todavía deben implementarse y validarse en el entorno del equipo.
