# Registro y ejecución · V5

JSON se usa como entrada interna del CLI. Se puede pasar un archivo en `.trabajo/` o usar `record` por stdin. La entrega de Obsidian contiene Markdown.

## Perfil opcional

Adaptá este ejemplo al alcance aprobado. El ejemplo usa rutas ficticias.

```json
{
  "base_url": "https://qa.example.test",
  "credentials": {"operator": "QA_OPERATOR_BEARER"},
  "http_operations": [
    {"method": "GET", "path": "/ready", "probe": {"status": 204}},
    {"method": "GET", "path": "/records/demo", "actors": ["anonymous", "operator"]}
  ],
  "browser_paths": ["/records"],
  "db_sources": ["qa.record_summary"],
  "timeout_seconds": 15
}
```

El origen se declara sin ruta ni credenciales. Las rutas HTTP son exactas, incluyendo query cuando corresponda. `probe` es opcional en GET/HEAD y admite estado y tipo de contenido esperados. Su actor predeterminado es `anonymous`. Los actores distintos de `anonymous` reciben el bearer desde su variable de entorno. El runner HTTP no sigue redirecciones.

El runner Playwright hace un smoke de lectura. `browser_channel` puede indicar `chrome`, `msedge` o `chromium`. `browser_assets` admite URLs HTTPS exactas de scripts y estilos necesarios para ese smoke. Si se declara `browser_walk`, el caso registra semilla, rondas y acciones con controles aprobados en `browser_controls`. Para login, flujos con estado, interacciones complejas y otros sistemas usá la herramienta autorizada que corresponda y registrá el intento.

`openapi --spec ARCHIVO` inventaría operaciones de un OpenAPI/Swagger JSON local sin enviar peticiones. `fixture-variant --help` genera una variación de tipo sobre un fixture JSON de prueba. Ninguno autoriza rutas o acciones nuevas.

## Caso

```json
{
  "kind": "case",
  "id": "REC-01",
  "title": "Consultar un registro sintético",
  "feature": "Consulta de registros",
  "requirement": "REQ-REC-READ",
  "priority": "high",
  "level": "api",
  "scenario": "QA · operador · registro sintético existente",
  "rationale": "Verificar que el operador puede consultar el registro que tiene asignado.",
  "preconditions": ["El registro demo existe y pertenece al actor de QA."],
  "steps": ["Consultar GET /records/demo como operador.", "Verificar estado y campo id."],
  "expected": "La consulta devuelve HTTP 200 y el identificador del registro.",
  "oracle_status": "documented",
  "sources": [{"path": "contrato.md", "locator": "Lectura de un registro"}],
  "http": {"method": "GET", "path": "/records/demo", "actor": "operator"},
  "criteria": [
    {"id": "status", "expected": "HTTP 200", "check": {"type": "status", "equals": 200}},
    {"id": "record-id", "expected": "id igual a demo", "check": {"type": "json_equals", "path": ["id"], "equals": "demo"}}
  ]
}
```

- Los oráculos `inferred` requieren `oracle_rationale`. Los `pending` requieren `oracle_pending_reason` y quedan sin veredicto mientras la expectativa esté abierta. Para `documented`, cada fuente incluye `path` y `locator` o `start`/`end`. Podés agregar `revision`.
- Los `check` solo son necesarios para `execute`. HTTP admite `status`, `content_type`, `json_equals` y `json_type`. Playwright admite `status`, `visible_text` y, con recorrido configurado, `walk_completed` y `no_page_errors`.
- Los recorridos declaran `browser_path` y, cuando aplica, `browser_walk` con `seed`, `rounds` (1 a 3) y 2 a 8 acciones. Cada acción tiene `id` y `type`. Tipos disponibles · `click`/`double_click` con `control` declarado, `resize` con `width` y `height`, `scroll` con `pixels` o `reload`. Ejecutá solo controles de lectura. El runner restringe HTTP del navegador a la carga de lectura del origen y recursos exactos declarados. Para una semilla alternativa se puede usar `--seed`.
- Para un lote, la entrada es una lista como `[{"case":"REC-01","via":"http"}]`. Un cuerpo JSON opcional se indica en `body`, relativo al manifiesto, o con `execute --body ARCHIVO`. La salida del runner usa 0 para aprobado, 1 para fallido, 2 para configuración/entrada inválida y 3 para bloqueado.
- Congelá el plan antes del primer intento. `freeze-plan --requirements ARCHIVO` acepta una lista independiente de IDs, por ejemplo `["REQ-REC-READ","REQ-REC-EDIT"]`.

## Datos de un caso para Azure

Si la corrida entrega un CSV de Azure, agregá los campos opcionales al registro del caso. Alineá `step_expected` con el orden de `steps`. Una cadena vacía indica que ese paso carece de resultado verificable propio. Las precondiciones se toman del campo existente `preconditions`.

```json
{
  "steps": ["Ingresar con una cuenta de QA.", "Cerrar sesión."],
  "step_expected": ["Se muestra el panel principal.", "Se vuelve a la pantalla de inicio de sesión."],
  "azure": {
    "test_case_type": "Positive",
    "functionality": "Acceso",
    "component_type": "UI",
    "type": "Functional"
  }
}
```

El exportador usa `feature` como funcionalidad si el caso no indica otra. Usa `API` para los casos cuyo nivel es `api` y `Functional` como tipo predeterminado. Completá metadatos específicos si el catálogo del proyecto usa otros valores. El CSV solo contiene datos de diseño del caso y conserva caracteres, comas y saltos de línea con la codificación UTF-8. Los textos que comienzan con operadores de fórmula reciben un apóstrofo para abrir el archivo en planillas.

## Intento externo

Prepará una nota sanitizada en `.trabajo/<id>/evidencias/REC-01-intento-1.md`. Las referencias son relativas a la corrida y usan nombres simples. Puede haber una nota por intento con apartados por criterio o varias notas. Incluí observado, esperado, fecha, escenario y una evidencia mínima verificable. El runner declarativo genera sus propias notas. Para detalles de UI o suites obtenidos por fuera del runner, añadí extractos relevantes y revisados.

```json
{
  "kind": "execution",
  "case_id": "REC-01",
  "status": "passed",
  "observation": "El registro sintético se recuperó con el actor de QA.",
  "execution_method": "http",
  "executor": "agent",
  "started_at": "2026-01-15T10:00:00-03:00",
  "finished_at": "2026-01-15T10:00:01-03:00",
  "duration_ms": 1000,
  "results": [
    {"id": "status", "status": "passed", "observation": "HTTP 200", "evidence": "evidencias/REC-01-intento-1.md"},
    {"id": "record-id", "status": "passed", "observation": "id coincide con demo", "evidence": "evidencias/REC-01-intento-1.md"}
  ]
}
```

`execution_method` admite `http`, `playwright`, `mcp_db`, `cli`, `suite`, `manual` y `other`. Para resultados observados mediante MCP agregá `db_source` declarado en el perfil. `executor` admite `runner`, `agent` y `human`. Cuando corresponda, agregá `classification` con `product`, `environment`, `runner` o `inconclusive`.

Un criterio admite `passed`, `failed`, `blocked` o `not_run`. Registrá duración como `null` si no se observó. El caso falla si falla un criterio. Es parcial si combina aprobados con bloqueos o pendientes. Cada reintento crea otro evento con el mismo ID. Usá IDs distintos cuando cambie el escenario.

## Hallazgos y notas

- `kind: "finding"` requiere `id`, `case_ids` (puede estar vacía), `classification`, `confidence` (`confirmed` o `hypothesis`), `observation`, `interpretation` y `pending`. Un confirmado requiere `evidence` y puede incluir `severity` con justificación.
- `kind: "note"` requiere `phase` y `observation`. Registrá preflight ampliado, cambios de alcance, fallos del runner, fases de medición y restauración. Podés adjuntar una nota existente mediante `evidence`. Registrá como nota cualquier evidencia adicional enlazada desde la evaluación, las métricas o el análisis para que se incluya al publicar.

Un intento tiene su propio veredicto y el informe calcula estado inicial y final a partir de todos los eventos de la corrida. Si la auditoría detecta evidencia faltante, se identifica el intento. El reporte indica requisitos sin caso cuando hay catálogo y los criterios documentados pendientes. La revisión semántica sigue a cargo del agente.

## Datos de un hallazgo para SDD

Agregá `sdd` al hallazgo `product` confirmado que quede abierto. El exportador reutiliza los pasos, requisitos, esperado y fuentes de los casos asociados. Podés indicar reproducción y esperado específicos cuando el hallazgo los requiera. Agregá rutas y localizadores verificados para orientar el cambio.

```json
{
  "fix_status": "open",
  "sdd": {
    "title": "Restaurar la respuesta esperada al consultar un registro",
    "component": "Controlador de consulta de registros",
    "suggestion": "Revisar el estado HTTP que el controlador devuelve cuando la consulta encuentra el registro.",
    "impact": "El operador recibe un error pese a que el registro existe.",
    "evidence_summary": "La respuesta observada fue HTTP 400 para un registro sintético existente.",
    "sources": [
      {"path": "docs/contrato.md", "locator": "Consulta de un registro"},
      {"path": "src/records.py", "locator": "get_record"}
    ],
    "acceptance": ["El operador recibe HTTP 200 y el identificador del registro."],
    "regression": ["Repetir REC-01 y corroborar que una consulta a un registro inexistente conserva su respuesta documentada."]
  }
}
```

Para `sdd`, `component`, `suggestion`, `acceptance` y `regression` son obligatorios. `sources` admite `path` con `locator` o `start` y `end`. Completá solo referencias comprobadas. Si tenés una hipótesis de ubicación, indicá esa incertidumbre en la sugerencia. `fix_status` toma `open` por defecto. Usá `verified_fixed` cuando el arreglo tenga un retest registrado.

Para el HTML, `rationale` describe el motivo del caso. Registrá el contexto breve con una nota `phase: "resumen-gerencial"` y una `observation` escrita en texto simple. El HTML toma los resultados y los conteos del registro de intentos.
