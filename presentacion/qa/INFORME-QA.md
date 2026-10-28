# QA del HTML de 12 slides

Versión actual: dirección tecnológica confirmada por el usuario. Fondo oscuro, acentos celestes, Saira, visual de portada con volumen y texto directo. Las versiones anteriores quedan archivadas y no forman parte del ZIP.

## Entregable

12 slides principales con detalle ampliable por tema. HTML autocontenido, fuente y visual embebidos, sin build, instalación ni CDN. El detalle conserva los temas de conocimiento, documentación, validación, recuperación, pruebas, SQL, clasificación de fallos, versiones, mantenimiento, herramientas, MVP y métricas. [Mapa de cobertura](cobertura.md).

## Resoluciones comprobadas

| Resolución | Slides capturadas | Lectura y navegación |
|---|---:|---|
| 1920 × 1080 | 12 | Sin cortes ni desbordamientos |
| 1280 × 720 | 12 | Sin cortes ni desbordamientos |
| 1366 × 768 | 12 | Sin cortes ni desbordamientos |
| 390 × 844 | 12 | Desplazamiento vertical, pies accesibles |
| 360 × 640 | 12 | Desplazamiento vertical, pies accesibles |

Se capturaron las 60 vistas de slides. Las carpetas por resolución también incluyen detalles de temas y tramos inferiores de las slides móviles. El montaje `1280x720/montaje-12-slides.jpg` reúne la versión final. `390x844/11-derecha.png` comprueba el extremo derecho del diagrama integral.

## Pruebas funcionales y visuales

- Apertura real de archivo local mediante `file://` en Chrome headless, con el contexto del navegador offline. Cero errores JavaScript y cero solicitudes HTTP/HTTPS.
- Fuente Saira cargada en las cinco resoluciones.
- 50 comprobaciones de navegación aprobadas: flechas, botones, Inicio/Fin, índice, detalle, ayuda, fuentes, licencia y apertura directa por número de slide.
- Los 12 detalles se abren con contenido y sin desbordamiento horizontal en los cinco tamaños.
- Pantalla completa mediante clic, foco inicial dentro del diálogo, animación ambiental y respeto por reducción de movimiento.
- Límites de contenido respecto de cabecera y pie, intersecciones de bloques de texto y etiquetas dentro de los nodos del diagrama integral. Sin problemas pendientes.
- El contraste usa los colores **realmente computados en los elementos** H1, H2, párrafos, etiquetas, notas y botones de detalle. Se calcula contra un fondo de referencia conservador, `rgb(36,69,99)`, para los paneles oscuros. Mínimo de ese control: 4.64:1. Esta medición no equivale a una certificación completa de accesibilidad.
- Revisión visual del conjunto de 12 slides, las slides oscuras, el piloto, las versiones, las conexiones, el diagrama integral y ventanas de detalle móviles. Se corrigieron herencia de color en títulos, espacios verticales, límites de portada y una etiqueta junto a una conexión.
- Impresión de navegador: 12 páginas. `impresion-qa.pdf` es evidencia interna, no reemplaza el HTML.

## Recursos del diseño

Visual de portada original: [conocimiento-volumen.png](../assets/conocimiento-volumen.png).

Prompt completo y modo de generación: [prompt-portada.txt](../assets/prompt-portada.txt). Se usó image_gen incorporado, con fondo transparente. El visual es una metáfora de documentos y conocimiento conectado, no una captura ni evidencia de un sistema real. El archivo original quedó guardado en el proyecto y embebido en el HTML.

Saira variable, sin modificar, bajo SIL Open Font License 1.1. La licencia se lee desde la ventana de fuentes y se conserva en `fuentes/OFL-Saira.txt`.

## Alcance y uso

Motor comprobado: Google Chrome en macOS. Los tamaños de celular se emularon como viewports, no sobre dispositivos físicos. No se verificaron otros motores de navegador. En celular, los diagramas conservan un ancho legible y se recorren horizontalmente.

La herramienta de control del navegador de Codex rechazó el acceso a la pestaña con archivo local por su política de protocolos. No se intentó sortear esa restricción. La presentación se validó como artefacto local mediante el motor de render de QA. Para actualizar una pestaña del usuario que mantenga la versión anterior, hace falta recargarla manualmente.

Las conexiones nuevas y la publicación del buscador se presentan como propuesta de piloto. Cliente, versiones, permisos, ambientes y tecnología se confirman en la implementación. Los ejemplos de pedidos y reglas son ilustrativos. No se muestran ahorro ni cambios de dotación como resultados demostrados.

## Integridad

SHA-256 del HTML:

`abf3d0771a91c2cf2566f0cc3b74ba15bce0d1afa85e9dbba7070500299f3e7f`

El ZIP incluye exactamente el mismo HTML, las instrucciones y la licencia de Saira. Fuente e imagen ya están dentro del HTML.

Registros: `resultados.json`, `detalles.json`. Scripts usados: `validar.cjs`, `verificar-detalles.cjs`.

Ajuste final de la etiqueta “Reglas del proceso”: ancho medido y captura actualizados en los cinco tamaños. Registro: `ajuste-final.json`.
