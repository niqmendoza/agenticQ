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
- **Expandir todo** revela las 51 actividades; **Contraer todo** conserva las seis fases conectadas.
- **Guía de términos** explica conceptos como caso de prueba, PR, cobertura, pipeline y regresión.
- Los recuadros amarillos indican herramientas opcionales o reemplazables. Cada una explica cómo cubrir hoy la tarea sin incorporarla. El bloque **El recorrido con Agentic QC V6** resume el proceso verificado localmente.

## Proceso revisado

1. Reunir documentación, reglas y fuentes de la aplicación. Versionar los segundos cerebros de QC en el proyecto solicitado de Azure Repos. Está en curso la conexión con RAGFlow para consultar lo publicado en main.
2. Comparar los casos existentes y decidir qué conservar, ajustar o crear.
3. QA revisa alcance y resultados esperados. Los casos reutilizables pasan al catálogo versionado de V6.
4. Ejecutar la suite sobre un build identificado con Playwright para interfaz y API directa, o con consultas de lectura para persistencia.
5. Revisar el dictamen, la evidencia y los casos pendientes. V6 conserva los resultados en JSON, JUnit, HTML y ZIP.
6. Entregar la ficha Markdown del defecto confirmado, repetir el caso en el build corregido y registrar el retest. Usar el resultado de V5 cuando esté disponible para comparar ambas corridas.

La importación y la asociación con casos de Azure Test Plans quedan pendientes de validación en el entorno corporativo. n8n figura como propuesta de coordinación.

El fondo incluye una trama de hexágonos turquesa conectados. Cerca del cursor se iluminan en fucsia con una respiración suave; el resplandor se desvanece al salir. El dibujo no captura clics, respeta la preferencia de movimiento reducido y detiene la animación cuando no está activa.

## Fuente y componentes

`src/data/qa-process.json` contiene seis fases, 51 actividades y 91 relaciones. No contiene coordenadas ni estilos. Los campos opcionales `owner`, `milestones` y `entryCondition` expresan responsables, resúmenes y condiciones del proceso.

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

Se revisaron el modelo sin coordenadas, diecisiete controles del proceso y la compilación TypeScript/Vite. En la vista de desarrollo se comprobaron las ramas, expansión y contracción completas, búsqueda, explicación lateral, conexiones internas y ausencia de desbordamiento horizontal en 1440 × 1000 y 390 × 844.

## Hitos de implementación y archivo compartible

La pestaña **Hitos de implementación** conserva los avances del Hito 2 y añade la verificación técnica de V5 y los hitos de V6. La línea de base muestra **12 de 38 hitos requeridos (32%)** y tres evaluaciones opcionales. Los hitos distinguen las pruebas técnicas de los ensayos con la aplicación real.

- **V5** aprobó 15 de 15 pruebas del harness con Playwright y Chrome. La corrida B5 está finalizando las pruebas del alcance de la nueva release de COELSA.Intelligent. Queda pendiente publicar el resultado por caso.
- **V6** aprobó 19 de 19 pruebas. En el chatbot de demostración pasaron los tres casos del build sano. En el build con la regresión de estado fallaron la interfaz y la API y aprobó el caso independiente.
- **Próximas iteraciones.** Alinear Agentic QC con la estructura TypeScript de QA y ampliar la cobertura de COELSA.Intelligent a toda la aplicación a partir de su código.
- **Próximo contraste.** Repetir en V6 los casos equivalentes del piloto bajo las mismas condiciones y comparar el resultado por ID de caso.

El avance se guarda en el almacenamiento de este navegador cuando está disponible. **Descargar HTML con avances** incluye el estado y las notas dentro de un nuevo HTML autónomo para compartirlo o trasladarlo. Si el navegador bloquea el almacenamiento de archivos locales, la descarga sigue disponible. Los navegadores y dispositivos no se sincronizan entre sí; se comparte la copia descargada. El archivo original del disco no se modifica automáticamente.

`src/data/implementation-plan.json` define el plan; `src/data/milestones.ts` valida y combina avances; `src/data/portable.ts` carga los datos incluidos y genera la descarga autónoma; `src/components/Milestones.tsx` presenta el gráfico de hitos. Los scripts embebidos `qa-process-state` y `qa-milestone-state` permiten reabrir una copia con su modelo y avance.

## Reporte Hito 2

`../informes/Hito-2.html` es el reporte autónomo y editable de esta etapa. Su copia en `public/Hito-2.html` permite abrirlo desde la pestaña de hitos y Vite la incluye en `dist`. Al actualizar el reporte, mantener ambas copias iguales. El reporte conserva resultados, límites y una comparación interactiva de las entregas; no necesita servidor ni recursos externos. La copia principal del mapa es `../informes/Mapa-QA-agentizada.html`.

Para actualizar el HTML compartible después de modificar las fuentes, ejecutá `pnpm build` y copiá `dist/index.html` a `../informes/Mapa-QA-agentizada.html`. Las dos copias abren directamente en el navegador.
