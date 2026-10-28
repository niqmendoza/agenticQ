# QA de la presentación HTML

Validación local del entregable final, 30 de septiembre de 2026.

**Resultado:** 40 slides, uso offline y controles verificados sobre `file://` en Google Chrome headless de esta PC. HTML autocontenido, sin build, imports ni CDN. Saira variable cargó en todos los tamaños. La licencia completa está dentro del HTML y en `fuentes/OFL-Saira.txt`.

## Resoluciones y evidencia

| Resolución | Slides capturadas | Contenido cortado en escritorio | Navegación |
|---|---:|---|---|
| 1920 × 1080 | 40 | Ninguno | Aprobada |
| 1280 × 720 | 40 | Ninguno | Aprobada |
| 1366 × 768 | 40 | Ninguno | Aprobada |
| 390 × 844 | 40 | Lectura con desplazamiento vertical | Aprobada |
| 360 × 640 | 40 | Lectura con desplazamiento vertical | Aprobada |

Capturas en carpetas con el nombre de cada resolución. `01.png` a `40.png` corresponden a las slides. Hay montajes de revisión de las 40 slides en `1280x720/`. Las capturas `-inferior.png` muestran los tramos finales de slides móviles. `390x844/39-derecha.png` verifica el extremo derecho del diagrama integral.

## Verificaciones realizadas

- Apertura real desde archivo local, con el contexto del navegador offline. Cero solicitudes HTTP/HTTPS y cero errores JavaScript.
- Teclas izquierda/derecha, Inicio/Fin, botones, índice, ayuda, Escape, apertura de una slide por hash y lectura de licencia. Las 45 verificaciones de navegación pasaron.
- Pantalla completa mediante clic, foco dentro del diálogo y animación ambiental normal. Con reducción de movimiento activa, la animación desaparece.
- Medición de límites del contenido de las 40 slides en las tres resoluciones de escritorio. Sin contenido sobre el pie ni desbordamiento horizontal.
- Medición de intersecciones entre bloques de texto. Sin intersecciones no intencionales.
- Anchos de etiquetas del SVG integral frente al espacio disponible. Todas caben dentro de sus nodos.
- Contraste de los once pares de la paleta usados para lectura. Mínimo: 5,73:1. Este control de paleta no equivale a una certificación integral de accesibilidad.
- En móvil, los pies de las 40 slides quedan accesibles al desplazarse. Sin desbordamiento de página. El diagrama integral conserva su ancho y permite desplazamiento horizontal, con indicación visible.
- Revisión visual de los montajes de las 40 slides y capturas detalladas de flujos, conexiones, versiones, entregables, contenido móvil y diagrama integral. Se corrigió el espacio de la nota inferior y se ajustaron las etiquetas del diagrama.
- Prueba de impresión de navegador: 40 páginas. `impresion-qa.pdf` es evidencia interna de QA, no el entregable solicitado.

## Contenido y decisiones de implementación

El mapa de las 40 slides está en [cobertura.md](cobertura.md). La presentación conserva el workbook actual, las responsabilidades de Azure, el segundo cerebro técnico, la validación funcional, la recuperación por versión, casos y automatizaciones reutilizables, controles SQL, clasificación de fallos, mantenimiento con PR y versión bajo prueba, MVP, entregables y métricas propuestas.

Las conexiones nuevas se presentan como arquitectura propuesta. El MVP debe comprobar cliente/entorno, versión, permisos, tecnología y ambiente. RAGFlow aparece como opción de implementación del buscador compartido a confirmar. No se presentan porcentajes de ahorro, reducción de dotación ni ROI como resultados demostrados.

## Alcance de la validación

El motor validado fue Google Chrome en macOS. Los tamaños de celular se probaron mediante viewport de navegador, no en dispositivos físicos. No se comprobó Safari, Firefox ni Edge. La apertura no necesita conexión. Los enlaces a documentación oficial sí requieren Internet. La herramienta de Codex aceptó la apertura de la pestaña local con estado `queued`, que se mostrará al abrir este chat.

## Integridad del entregable

SHA-256 de `QA-agentizada.html`:

`4af3239b8376f5730598a8e4efde22bb8d2e47da8f233e792e97e9184c524bf5`

El ZIP incluye el mismo HTML sin cambios, instrucciones de apertura y licencia. Las evidencias quedan fuera del ZIP de distribución para mantenerlo liviano.

## Registros y reproducción

- `resultados.json`: mediciones, fuente, navegación y errores por resolución.
- `detalles.json`: contraste, etiquetas, foco, movimiento y acceso a pies móviles.
- `extras.json`: acceso al extremo horizontal del diagrama.
- `validar.cjs`, `verificar-detalles.cjs` y `verificar-extra.cjs`: scripts de QA usados en esta PC con el runtime de Codex. No son necesarios para abrir el HTML.
- `../src/`: contenido y código editable de generación.
