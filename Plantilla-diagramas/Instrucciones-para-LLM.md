# Guía para el LLM · Diagramas de arquitectura en HTML

> **Objetivo:** transformar el contenido de una persona en un diagrama interactivo, editable y transportable, conservando el diseño de `Plantilla-Arquitectura.html`.
>
> **Entrega:** un archivo `.html` completo. Debe abrirse con doble clic, funcionar sin Internet y poder compartirse por sí solo.

## 1. Qué archivos recibirás

| Archivo | Para qué sirve |
|---|---|
| `Plantilla-Arquitectura.html` | Diseño, ejemplo de datos, validación y motor de interacción. Es la base que tenés que copiar. |
| `Instrucciones-para-LLM.md` | Este contrato de contenido, comportamiento y entrega. |
| `Prompt-para-completar.md` | Brief que la persona completa para describir su tema. Puede incluir documentos adicionales como fuente. |

La plantilla muestra un **ejemplo genérico**. Sus títulos, actores, decisiones y herramientas no son requisitos del nuevo tema. El HTML final de QA es una referencia de estilo y queda fuera de esta adaptación: no lo sobrescribas.

## 2. Procedimiento de trabajo

1. Leé el brief completo y las fuentes que la persona haya proporcionado.
2. Identificá el título, la marca, el objetivo, los bloques principales, sus partes, las personas, los sistemas y las relaciones.
3. Prepará una estructura lógica. Podés cambiar la cantidad de bloques principales y la profundidad de sus subpartes. No hay seis fases obligatorias.
4. Separá **pertenencia** de **flujo**: un subrecuadro pertenece a un grupo; una flecha expresa una relación declarada. Una lista de componentes no implica que se ejecuten en ese orden.
5. Escribí los textos en lenguaje claro y asigná a cada recuadro un identificador único.
6. Convertí «No aplica», «Ninguna definida» y filas de ejemplo no utilizadas en campos omitidos o listas vacías; no los trates como componentes ni tecnologías reales. Completá el JSON de la plantilla siguiendo la sección 4. Modelá también las conexiones principales: no aparecen por el simple orden de los grupos.
7. Revisá decisiones, aprobaciones, condiciones, caminos de retorno y qué se puede hacer sin las opciones adicionales.
8. Copiá la plantilla y reemplazá **sólo el contenido** de `<script id="diagram-data" type="application/json">`. Actualizá también `<title>` y la descripción del documento para que coincidan con el nuevo tema. El motor actualiza esos dos campos al abrirlo y al guardarlo.
9. Conservá el CSS, el marcado de la interfaz y el motor JavaScript. Cambialos únicamente si la persona pide expresamente un cambio visual o funcional.
10. Validá y entregá el HTML completo con un nombre descriptivo, por ejemplo `Arquitectura-[tema].html`. Si disponés de herramientas de archivos, adjuntá o enlazá ese archivo. Si sólo podés responder con texto, devolvé el HTML completo en un único bloque `html`, sin omisiones.

No sustituyas la plantilla por un nuevo proyecto de React, una imagen, un PDF, un enlace a un servidor ni un fragmento suelto. La persona pidió un HTML autónomo.

## 3. Sistema visual que se conserva

- Fondo negro con hexágonos turquesa conectados y un resplandor fucsia suave cerca del cursor.
- Recorrido vertical, ramas laterales que se despliegan y guía de los bloques principales siempre visible.
- Recuadros legibles; explicación al seleccionarlos; búsqueda; expansión y contracción completas.
- Panel de edición de datos y descarga de una nueva copia HTML.
- Adaptación a móvil y respeto por la preferencia de movimiento reducido.

| Color | Significado |
|---|---|
| Negro `#000000` y tonos `#001F23` a `#00A0AD` | Fondo, estructura y recorrido principal. |
| Fucsia `#E11F8F` | Revisión humana, decisiones, retornos y efecto del cursor. |
| Amarillo suave `#D8BF70` | Elemento opcional o reemplazable. Debe explicar su alternativa. |

El color siempre se acompaña de texto. **Propuesto** no equivale a **opcional**: algo puede ser futuro y obligatorio en el diseño elegido. Sólo `status: "opcional"` produce la marca amarilla. Un grupo que contiene exclusivamente opciones también se muestra en amarillo.

## 4. Contrato del contenido editable

El JSON se encuentra entre los comentarios `INICIO DEL CONTENIDO EDITABLE` y `FIN DEL CONTENIDO EDITABLE`. No tiene comentarios internos, funciones, HTML, coordenadas, colores ni posiciones.

### Estructura general

```json
{
  "schemaVersion": "1.0",
  "meta": {
    "title": "Nombre de la arquitectura",
    "subtitle": "Qué explica y para quién está pensada.",
    "topic": "Tema o área",
    "brandLeft": "ARQ",
    "brandRight": "EQUIPO",
    "tagline": "Una frase breve para la cabecera",
    "baseTitle": "El punto de partida",
    "baseDescription": "Qué existe hoy y con qué se puede trabajar.",
    "startLabel": "ENTRADA CONFIRMADA",
    "startId": "entrada",
    "endLabel": "RESULTADO DISPONIBLE",
    "endId": "salida",
    "footerTitle": "Alcance y próximos pasos",
    "footerText": "Qué está confirmado, qué se propone y qué falta decidir."
  },
  "glossary": [
    { "term": "Concepto", "meaning": "Explicación breve en lenguaje común." }
  ],
  "groups": [
    {
      "id": "entrada",
      "type": "group",
      "title": "Recibir la necesidad",
      "description": "Registrar lo que se necesita y confirmar su alcance.",
      "owner": "Persona responsable",
      "children": [
        {
          "id": "solicitud",
          "type": "input",
          "title": "Solicitud confirmada",
          "description": "La persona describe la necesidad y confirma los datos mínimos.",
          "status": "actual",
          "inputs": ["Necesidad inicial"],
          "outputs": ["Solicitud con alcance conocido"]
        }
      ]
    },
    {
      "id": "salida",
      "type": "group",
      "title": "Preparar el resultado",
      "description": "El equipo realiza el trabajo acordado y registra el resultado.",
      "owner": "Equipo implementador",
      "children": [
        {
          "id": "realizar-trabajo",
          "type": "process",
          "title": "Realizar el trabajo",
          "description": "Aplicar la solución con los datos y criterios acordados.",
          "status": "propuesto",
          "outputs": ["Resultado para revisar"]
        }
      ]
    }
  ],
  "edges": [
    {
      "id": "principal-1",
      "source": "entrada",
      "target": "salida",
      "type": "normal",
      "label": "Solicitud lista para trabajar"
    },
    {
      "id": "datos-1",
      "source": "solicitud",
      "target": "realizar-trabajo",
      "type": "data",
      "label": "Datos y alcance confirmados"
    }
  ]
}
```

Este ejemplo es válido, pero no reemplaza la información del brief. El motor dibuja las flechas de `edges`; no infiere conexiones por proximidad o por el nombre de un recuadro.

### `meta`: identidad y contexto

| Campo | Regla |
|---|---|
| `title`, `subtitle`, `brandLeft`, `brandRight` | Obligatorios, con texto no vacío. La marca visible será `brandLeft / brandRight`. |
| `topic`, `tagline` | Textos breves opcionales. No inventes una marca. |
| `baseTitle`, `baseDescription` | Punto de partida y ruta que puede realizarse con lo disponible. Sin descripción, ese bloque se oculta. |
| `startLabel`, `startId` | Opcionales. Usalos juntos para conectar una entrada visual al grupo principal indicado. `startId` debe existir en `groups`. |
| `endLabel`, `endId` | Opcionales. Usalos juntos para conectar un resultado visual desde el grupo principal indicado. No prometas un cierre si el proceso requiere una revisión posterior. |
| `footerTitle`, `footerText` | Alcance, supuestos y próximos pasos. Separá lo existente de lo propuesto. |
| `initialExpanded` | Lista opcional de IDs de grupos que deben estar abiertos al inicio. Sin este campo se abren los grupos principales. `[]` inicia con todas las ramas contraídas. Para abrir un grupo interno, incluí también sus ancestros. |

### `groups`: bloques principales y subpartes

Cada elemento principal debe ser un grupo. Su orden en la lista define el orden de lectura vertical, **no** el orden de ejecución. Usá `edges` para declarar ese flujo.

Un grupo requiere `id`, `type: "group"`, `title`, `description` y `children`. La lista `children` puede estar vacía si ese bloque no necesita detalle. Puede contener otros grupos y recuadros de cualquier tipo, en distintos niveles.

```json
{
  "id": "grupo-principal",
  "type": "group",
  "title": "Nombre del bloque",
  "description": "Qué reúne y para qué sirve.",
  "owner": "Equipo responsable",
  "review": true,
  "condition": "Se abre sólo cuando la entrada está confirmada",
  "children": [
    {
      "id": "subgrupo",
      "type": "group",
      "title": "Parte del bloque",
      "description": "Qué actividades o componentes reúne.",
      "children": []
    }
  ]
}
```

- `review: true` destaca el grupo principal como un punto de revisión humana. No configura una aprobación real.
- `condition` explica la condición de entrada al recuadro; no reemplaza la condición específica de una flecha.
- No agregues `children` a un recuadro que no tenga `type: "group"`.
- Los IDs siguen `^[a-z][a-z0-9-]*$`: por ejemplo, `documento-origen`, `motor-reglas`, `revision-final`. Deben ser únicos en todo el diagrama.

### Recuadros: tipos, estados y explicación

Obligatorios: `id`, `type`, `title`, `description`.

| `type` | Representa |
|---|---|
| `process` | Actividad o paso de trabajo. |
| `tool` | Herramienta, librería o componente que facilita una tarea. |
| `human` | Persona, rol o equipo. |
| `decision` | Pregunta que conduce a distintos caminos. |
| `model` | Modelo de IA que se usa en una tarea. |
| `artifact` | Documento, registro, archivo o evidencia. |
| `external` | Sistema externo al alcance principal. |
| `input` | Entrada del proceso o sistema. |
| `output` | Salida o resultado. |
| `validation` | Comprobación o confirmación. |
| `group` | Conjunto desplegable de recuadros. |

Campos opcionales de explicación:

| Campo | Formato / uso |
|---|---|
| `status` | `actual`, `propuesto` u `opcional`. Si no se conoce, omitilo y explicitá la duda en el contenido. |
| `purpose` | Texto: para qué sirve. |
| `how` | Texto: cómo funciona o cómo se hace. |
| `owner` | Texto: responsable. |
| `inputs`, `outputs` | Listas de textos: qué recibe y qué entrega. |
| `tools` | Lista de herramientas asociadas. No crea otros recuadros automáticamente. |
| `humanReview` | Texto: quién revisa, qué revisa y cuándo interviene. |
| `checks` | Lista de criterios concretos para considerar listo ese paso. |
| `condition` | Texto: condición de entrada al recuadro. |
| `alternative` | Texto **obligatorio si el estado es `opcional`**: cómo cubrir hoy la tarea sin esa opción o qué la reemplaza. |

Ejemplo de opcional:

```json
{
  "id": "herramienta-opcional",
  "type": "tool",
  "title": "Herramienta para asistir la revisión",
  "description": "Podría reducir el trabajo de comparar documentos.",
  "status": "opcional",
  "alternative": "Hoy el equipo compara los documentos manualmente con una lista de criterios. La herramienta se evaluará si ahorra tiempo con resultados equivalentes."
}
```

### `edges`: flechas y etiquetas

Cada conexión requiere `id`, `source`, `target`, `type`, `label`. Los dos extremos tienen que existir; pueden ser grupos o recuadros de cualquier nivel. `id` también debe ser único entre las conexiones.

| `type` | Significado | Cómo escribir la etiqueta |
|---|---|---|
| `normal` | Avance o dependencia de trabajo. | «Propuesta lista», «Continuar con la entrega». |
| `data` | Datos, un documento o una respuesta que se intercambia. | Nombrá lo que viaja: «Pedido validado», «Resultado y evidencia». |
| `approval` | Revisión humana o confirmación. | «Revisar alcance», «Aprobación del responsable». |
| `conditional` | Sólo se avanza si ocurre algo. | «Aprobado», «Hay información suficiente». Agregá **`condition` no vacío**. |
| `feedback` | Volver, corregir o repetir una parte. | «Faltan datos: completar», «Corregir y volver a revisar». |
| `optional` | Relación que sólo se usa si se adopta una opción. | «Si se adopta esta herramienta». |

```json
{
  "id": "continuar-con-aprobacion",
  "source": "revision",
  "target": "ejecucion",
  "type": "conditional",
  "label": "Propuesta aprobada",
  "condition": "Las personas responsables aprobaron la misma versión y las dudas están resueltas"
}
```

En este ejemplo aislado, `revision` y `ejecucion` deben existir en el modelo completo. No pegues la conexión si no creaste esos recuadros.

El mapa muestra las conexiones principales, las relacionadas con el recuadro seleccionado y, al activar **Mostrar conexiones internas**, el resto de las conexiones visibles. Los extremos todavía ocultos se representan por su grupo visible más cercano; la explicación lateral conserva los extremos y la etiqueta originales. Los títulos muy largos de las flechas pueden abreviarse visualmente; su texto completo queda en la explicación y en el título SVG.

Una conexión y una etiqueta son **documentación**, no una integración ejecutable. Dos flechas de aprobación no implementan por sí solas una regla «ambos deben aprobar». Esa regla tiene que quedar explícita en la descripción y en los criterios del recuadro de decisión.

### `glossary`: términos del tema

Lista opcional de `{ "term": "…", "meaning": "…" }`. Definí los términos que una persona no especializada necesite para entender el mapa. No uses metáforas infantiles ni expliques conceptos ajenos al tema. Si la lista está vacía, el botón de términos se oculta.

## 5. Calidad del contenido

- Títulos cortos, preferentemente de 3 a 7 palabras. Una actividad empieza con un verbo; un sistema puede llevar su nombre real; una decisión suele ser una pregunta.
- Descripción de 1 a 3 frases que explique qué hace el recuadro y por qué importa.
- Etiquetas de flecha breves y específicas: nombrar una acción, un dato o una condición. Evitá «siguiente», «cosa» o «proceso» sin contexto.
- Reglas confirmadas y propuestas se distinguen. No presentes una idea como una capacidad ya disponible.
- Si falta información, escribí «Por confirmar» con una pregunta concreta. No inventes responsables, tecnologías, aprobaciones, costos ni integraciones.
- No traslades QA, Playwright, Copilot, RAGFlow, Azure ni los nombres de la presentación de referencia al nuevo tema, salvo que la persona los incluya.
- Una decisión debe explicar sus salidas relevantes: continuar, pedir cambios, cancelar o escalar, según corresponda. No agregues una salida que el usuario no haya autorizado o definido; marcá la duda.
- Un fallo no significa automáticamente que deba cambiarse el producto. Aclarar quién interpreta la evidencia y quién decide la acción cuando el tema lo requiera.
- No conviertas todas las herramientas en requisitos. Cada opción amarilla debe tener una alternativa comprensible.
- No elimines datos para que el dibujo «quede lindo»: agrupá y usá niveles de detalle.

## 6. Edición segura del HTML y validación

1. Extraé el texto del script `diagram-data`, prepará el objeto JSON y validalo con un parser JSON.
2. Comprobá IDs únicos, tipos válidos, extremos existentes y ausencia de coordenadas.
3. Serializá el JSON como UTF-8 con comillas dobles. Escapá `<` como `\u003c` dentro de ese script para evitar un cierre accidental de la etiqueta. Nunca insertes un `</script>` literal como parte de un título o descripción del JSON.
4. Conservá los IDs de la interfaz y las etiquetas `<script>` del motor. No edites código minificado ni reemplaces partes por «el resto sigue igual».
5. Abrí el archivo en un navegador si disponés de esa capacidad. Verificá las ramas, la explicación lateral, la búsqueda, los retornos, las etiquetas y la adaptación a móvil. Si no podés hacer una revisión visual, indicá ese límite sin afirmar que la hiciste.
6. Si usás el editor incorporado, pegá el JSON, elegí **Aplicar cambios** y después **Guardar HTML**. Aplicar sólo cambia la ventana actual; no sobrescribe el archivo original del disco.
7. Confirmá que no aparecieron dependencias externas: scripts con `src`, hojas de estilo remotas, fuentes de Internet, imágenes externas o solicitudes de red para obtener el contenido.
8. La entrega debe contener todo el HTML, CSS, JavaScript y los datos. Nunca enlaces el modelo como archivo externo ni uses `fetch` para leerlo.

## 7. Resultado esperado

Entregá:

- Un archivo `Arquitectura-[tema].html` autónomo y completo, basado en esta plantilla.
- Una explicación breve de cómo abrirlo y editarlo.
- Las dudas importantes pendientes, si las hay. No ocultes información que aún requiere definición.

Si la persona pide únicamente el JSON para pegarlo en el editor, entregá el JSON válido en lugar del HTML. Esa es una salida alternativa explícita; la salida predeterminada sigue siendo el HTML completo.
