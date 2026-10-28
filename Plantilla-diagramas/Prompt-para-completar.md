# Mi diagrama de arquitectura

> **Cómo usar este documento**
>
> 1. Hacé una copia y completá los campos entre corchetes.
> 2. Adjuntá esa copia junto con `Plantilla-Arquitectura.html` e `Instrucciones-para-LLM.md` al LLM que uses.
> 3. Pedile que entregue el HTML terminado.
>
> **No necesitás escribir JSON ni conocer programación.** Los códigos como `A`, `A1` y `B` son nombres cortos para identificar los recuadros y sus flechas. El LLM los convertirá a IDs válidos. Si no sabés una respuesta, escribí «Por confirmar».

---

## 01 · El pedido

Quiero que generes **un único HTML autónomo, editable y transportable** con mi diagrama de arquitectura.

Usá el diseño y el motor de la plantilla adjunta. Seguí las instrucciones del archivo `Instrucciones-para-LLM.md`. Cambiá el contenido del ejemplo por el que describo en este documento. Conservá los colores, el fondo de hexágonos, las ramas desplegables, la explicación de cada recuadro y la guía del recorrido.

**Título de la presentación:** [Nombre del tema o proyecto]

**Subtítulo:** [En una frase, qué explica esta arquitectura]

**Marca en la cabecera:** [Texto izquierdo] / [Texto derecho]

**Área o tema:** [Área, producto, equipo o iniciativa]

**Archivo que quiero recibir:** `Arquitectura-[nombre-corto].html`

---

## 02 · A quién se lo voy a explicar

| Campo | Mi respuesta |
|---|---|
| Quién va a leer el mapa | [Dirección, equipo técnico, personas de negocio, público mixto…] |
| Qué conoce del tema | [Nada, conceptos generales, bastante detalle…] |
| Qué debería entender al terminar | [La idea o decisión principal que debe quedar clara] |
| Cuánto detalle necesito | [Resumen para presentar / explicación intermedia / detalle técnico desplegable] |
| Idioma y tono | [Por ejemplo: español claro, profesional y sin jerga innecesaria] |

**Tipo de mapa que necesito:** [Flujo de trabajo / arquitectura de sistemas / ruta de implementación / mixto / otro]

**Qué abarca:** [Qué partes entran en este diagrama]

**Qué queda fuera:** [Qué no debe intentar explicar]

---

## 03 · El punto de partida

**Qué existe o se hace hoy:**

[Describí la situación actual en 3 a 6 líneas. Indicá personas, herramientas o sistemas que ya se usan.]

**Qué queremos lograr:**

[Resultado deseado, problema que se quiere resolver o cambio que se propone.]

**Qué puede hacerse con lo que ya tenemos:**

[La ruta base. Explicá cómo avanzar sin incorporar todas las herramientas o mejoras opcionales.]

**Qué es una propuesta futura:**

[Partes que todavía hay que implementar, probar o acordar.]

**Información confirmada y fuentes:**

[Documentos adjuntos, reglas aprobadas, enlaces o notas. Indicá si alguna fuente es sólo una idea o un borrador.]

---

## 04 · El recorrido o los bloques principales

> Poné los bloques en el orden en que querés que se lean. **Ese orden no crea automáticamente un flujo:** las flechas se definen en la sección 07.
>
> Podés usar 2, 4, 8 o más bloques. No tienen que ser seis ni tienen que representar etapas de tiempo: pueden ser sistemas o áreas de una arquitectura.

| Código | Nombre del bloque | Para qué sirve | Responsable | Condición para entrar, si hay |
|---|---|---|---|---|
| A | [Primer bloque] | [Objetivo] | [Persona o equipo] | [Condición o «No aplica»] |
| B | [Segundo bloque] | [Objetivo] | [Persona o equipo] | [Condición o «No aplica»] |
| C | [Tercer bloque] | [Objetivo] | [Persona o equipo] | [Condición o «No aplica»] |
| D | [Cuarto bloque, si lo necesito] | [Objetivo] | [Persona o equipo] | [Condición o «No aplica»] |

**Entrada visual del mapa:** [Texto de la entrada y código del bloque al que conecta; o «No aplica»]

**Salida visual del mapa:** [Texto del resultado y código del bloque del que sale; o «No aplica»]

**¿Hay bloques que trabajan en paralelo o se relacionan de otra manera?**

[Explicá cuáles. El LLM no debe convertirlos en una cadena de ejecución si no corresponde.]

---

## 05 · Qué lleva cada recuadro

> Copiá esta ficha una vez por actividad, sistema, persona, decisión o documento que quieras mostrar.
>
> Si un recuadro pertenece a otro, escribí su código en **Dentro de**. Si después querés dividirlo en más partes, agregá nuevas fichas con ese código como padre.

### Ficha de recuadro · [Código]

| Campo | Mi respuesta |
|---|---|
| Código | [Por ejemplo: A1] |
| Dentro de | [Código del bloque o grupo al que pertenece: A, A2, B1…] |
| Título visible | [Nombre breve que debe aparecer en el recuadro] |
| Qué representa | [Actividad / herramienta / persona o equipo / decisión / modelo de IA / documento / sistema externo / entrada / salida / validación / grupo de subpartes] |
| Estado | [Ya existe / propuesto / opcional o reemplazable / por confirmar] |
| Qué hace | [Explicación de 1 a 3 frases] |
| Para qué sirve | [Por qué es necesario o útil] |
| Cómo funciona | [Explicación breve para quien abre el detalle] |
| Qué recibe | [Datos, documentos, pedidos o condiciones de entrada] |
| Qué entrega | [Resultado, archivo, decisión o acción] |
| Quién se encarga | [Responsable] |
| Herramientas asociadas | [Nombres reales, si corresponde; o «Ninguna definida»] |
| Quién revisa y cuándo | [Persona, momento y alcance de la revisión; o «No aplica»] |
| Cómo sabemos que está listo | [Uno o varios criterios concretos] |
| Si es opcional, cómo se hace sin esto | [Alternativa actual o reemplazo. Obligatorio para los opcionales.] |
| Subpartes, si tiene | [Códigos de los subrecuadros; o «No tiene»] |

**Notas o dudas sobre este recuadro:** [Información por confirmar o aclaraciones]

---

## 06 · Cómo se agrupan las subpartes

> Esta estructura sirve para mostrar qué pertenece a qué. No define por sí misma las flechas del proceso.
>
> Podés borrar el ejemplo y escribir una lista indentada con tus códigos.

```text
A · [Bloque principal]
  A1 · [Actividad o componente]
  A2 · [Grupo de actividades]
    A2a · [Detalle dentro del grupo]
    A2b · [Otro detalle]

B · [Otro bloque principal]
  B1 · [Actividad o componente]
  B2 · [Herramienta opcional]

C · [Bloque de revisión o decisión]
  C1 · [Persona que revisa]
  C2 · [Decisión o resultado de la revisión]
```

**Grupos que quiero abiertos al principio:** [De manera predeterminada se ven los bloques y sus primeras ramas. Si necesitás otra apertura inicial, indicalo expresamente.]

---

## 07 · Las flechas y sus textos

> Una fila por conexión. Usá los códigos anteriores para no confundir recuadros con nombres parecidos.
>
> **Qué escribir sobre una flecha:** lo que se entrega, la acción que habilita el siguiente paso o la condición que se cumple. Por ejemplo: «Datos completos», «Propuesta aprobada», «Pedido para procesar».
>
> No hace falta crear una flecha sólo porque un recuadro está dentro de otro: esa pertenencia ya se ve con una línea punteada.

| Código de flecha | Desde | Hacia | Texto de la flecha | Tipo de relación | Condición, si existe |
|---|---|---|---|---|---|
| F1 | [A] | [B] | [Qué permite avanzar o qué se intercambia] | [Avance / datos / aprobación / condición / retorno / opcional] | [Condición concreta o «No aplica»] |
| F2 | [A1] | [B1] | [Texto breve] | [Tipo] | [Condición o «No aplica»] |
| F3 | [C2] | [B] | [Por qué vuelve] | Retorno | [Qué tiene que pasar para volver] |
| F4 | [Código] | [Código] | [Texto breve] | [Tipo] | [Condición o «No aplica»] |

**Reglas para interpretar mis flechas:**

[Por ejemplo: A y B intercambian información pero no esperan uno al otro; C sólo comienza con la misma versión aprobada; el resultado vuelve a B si falla una comprobación.]

---

## 08 · Decisiones, revisiones y retornos

> Completá una ficha por decisión importante. Si no hay decisiones, escribí «No aplica».

### Decisión · [Código del recuadro]

- **Pregunta que debe mostrar:** [¿Qué se está decidiendo?]
- **Quién decide:** [Persona, equipo o regla confirmada]
- **Qué revisa:** [Información necesaria para decidir]
- **Si la respuesta es favorable:** [A qué código va y con qué texto de flecha]
- **Si necesita cambios o falta información:** [A qué código vuelve y qué debe corregirse]
- **Si hay otro resultado relevante:** [Cancelar, esperar, escalar, registrar…; o «No aplica»]
- **Criterio para avanzar:** [Qué demuestra que puede continuar]
- **Si hay varias aprobaciones:** [Deben aprobar todos / alcanza con uno / regla específica / por confirmar]
- **Si cambia la propuesta después de aprobarse:** [Quién vuelve a revisar, si corresponde]

**Otros ciclos que debe mostrar el mapa:**

[Reintentos, correcciones, actualización de documentación, aprendizaje o mantenimiento. Indicá origen, destino y motivo.]

---

## 09 · Lo opcional y sus alternativas

> Amarillo significa «puede omitirse o reemplazarse». Una parte futura no es automáticamente opcional.

| Código del recuadro | Qué opción o mejora representa | Qué aportaría | Cómo se hace hoy sin ella | Cuándo tendría sentido adoptarla |
|---|---|---|---|---|
| [B2] | [Herramienta o componente] | [Beneficio esperado] | [Alternativa actual] | [Criterio para evaluarla] |
| [Otro] | [Opción] | [Beneficio] | [Alternativa] | [Criterio] |

**Ruta que quiero que se entienda como base:**

[Describí el camino que funciona sin estas opciones.]

---

## 10 · Términos, supuestos y dudas

### Términos que conviene explicar

| Término | Explicación para el público de esta presentación |
|---|---|
| [Concepto] | [Explicación breve] |
| [Sigla] | [Qué significa y para qué importa] |

### Lo que falta confirmar

- [Pregunta pendiente y, si se sabe, quién podría responderla]
- [Otra pregunta]

### Cosas que no quiero que el LLM invente

[Responsables, tecnología, pasos, aprobaciones, reglas, costos u otras decisiones que no están definidas.]

### Información adicional

[Pegá notas, requisitos o referencias que ayuden a interpretar el mapa. Aclará qué información está aprobada.]

---

## 11 · Instrucción final para el LLM

Con la información anterior:

1. Leé el HTML y la guía adjunta; conservá el diseño y su funcionamiento.
2. Convertí mis códigos y fichas en recuadros, grupos anidados y flechas explícitas. No confundas pertenencia con flujo.
3. Redactá textos claros para el público que indiqué. Mantené los detalles técnicos dentro de la explicación de cada recuadro.
4. Marcá en amarillo sólo lo opcional o reemplazable y explicá su alternativa. Diferenciá lo actual de lo propuesto.
5. No arrastres contenido de QA ni del ejemplo genérico al resultado si no forma parte de mi tema.
6. Si falta un dato importante, marcá «Por confirmar» con la pregunta concreta. Si la falta impide definir el flujo, haceme una pregunta breve antes de darlo por terminado.
7. Revisá IDs, relaciones, decisiones, rutas de retorno y aprobaciones. No agregues conexiones sólo por la posición de los recuadros.
8. Entregá el **HTML completo como archivo**, con estilos, código y datos incluidos, sin dependencias externas. Debe abrirse con doble clic.
9. Indicá brevemente cómo abrirlo, cómo editarlo y qué dudas quedaron pendientes.

**Si te pido sólo el contenido para el editor:** devolvé únicamente el JSON válido para pegarlo en «Editar datos». En cualquier otro caso, entregá el HTML terminado.
