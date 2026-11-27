# Segundo cerebro V3 para QC

El perfil de la aplicación fija el alcance y los flujos críticos. La publicación conserva un bundle OKF con una entrada corta, conceptos de producto y fichas de QC enlazadas. La etapa 01 consume el mismo `corpus/`.

| Ruta | Uso |
|---|---|
| `corpus/inicio.md` | Entrada breve al producto y acceso directo a los flujos críticos publicados. |
| `corpus/index.md`, `temas/` y `mocs/` | Índice exhaustivo, fichas breves y navegación por relaciones. |
| `corpus/qc/<flujo>.md` | Precondiciones, configuración, variantes, oráculos y evidencia de cada escenario. |
| `fichas-qc.json` | Proyección estructurada para enlazar, recuperar y republicar las mismas fichas. |

## Definir el alcance y las fichas

1. Copiá el [perfil de ejemplo](ejemplos/perfil-qc.demo.json). La ruta del repositorio se resuelve desde el archivo de perfil. Fijá la referencia Git, módulos técnicos cuando se necesiten, exclusiones, flujos críticos con su riesgo y límites de contexto. Para las citas QC, declarale a cada ruta o prefijo el tipo de fuente `contrato`, `implementacion`, `configuracion` o `test`. El prefijo más específico tiene prioridad.
2. Completá las fichas breves y la [taxonomía](ejemplos/taxonomia.demo.json). Redactá cada escenario una vez en un archivo de [fichas QC](ejemplos/fichas-qc.demo.json). Cada caso tiene ID, prioridad, capa, actor, precondiciones, configuración, datos sintéticos, acción, resultado observable, evidencia, tipo de prueba y estado de ejecución. Registrá solo variantes que cambien el resultado.
3. Cada resultado admite citas al índice del commit con ruta, tipo, rango y localizador. Si identificaste un test existente, declará la fuente de tipo `test` y el símbolo o selector. El script controla el rango y un indicio de aserción, y la revisión de QC verifica que esa aserción sostenga el resultado. Cuando haya discrepancias, anotá las versiones en `discrepancias` y dejá la ficha bloqueada.
4. Registrá la transición de revisión con la persona responsable y el commit. Para `listo-para-qc` se requiere un concepto enlazado, un caso válido y uno de fallo o una justificación, además de respaldo de contrato o test para cada resultado. Copilot puede proponer candidatos y registrar brechas. `revision.estado` corresponde a la revisión de la ficha. `estado` de la ficha breve describe el comportamiento y `ejecucion.estado` registra una ejecución informada con fecha, entorno y registro cuando existe.

```sh
python v10/00-creacion-segundo-cerebro/scripts/mapear.py procesar --id PILOTO-mapa --perfil PERFIL.json
python v10/00-creacion-segundo-cerebro/scripts/publicar.py procesar --id PILOTO-publicado --mapa MAPA --taxonomia TAXONOMIA.json --revision FICHA.json --fichas-qc FICHAS-QC.json
```

Repetí `--revision` o `--fichas-qc` para procesar varios archivos. Si hay flujos críticos pendientes, el código 3 deja el bundle y registra sus estados en `manifiesto.json`. Para dejar un bloqueo explícito, usá `"revision": {"estado":"bloqueado","motivo":"…"}`. Se admiten escenarios vacíos en una ficha bloqueada.

## Migrar y actualizar

Cuando exista una bóveda previa, usá `--migracion INVENTARIO.json` con una lista como esta. `destino` identifica un flujo QC o un escenario con `flujo/caso`. Una incorporación solo se registra si el destino se publica con sus insumos.

```json
[
  {"nota":"vault anterior/Consulta.md","decision":"incorporada","destino":"consulta-tramite/valido-registro","motivo":"El escenario se reescribió con el contrato del commit."},
  {"nota":"vault anterior/Cambio.md","decision":"historica","motivo":"Contexto de un despliegue anterior."},
  {"nota":"vault anterior/Variante.md","decision":"pendiente","motivo":"Falta contrastar la precondición."}
]
```

Para actualizar, indicá `--anterior` en el mapa y en la publicación. Si cambia una fuente citada, un concepto enlazado o el alcance de un flujo, las fichas reutilizadas pasan a bloqueadas con el motivo en `invalidaciones`. Las citas que cambiaron se retiran del escenario publicado hasta volver a verificarlas. El responsable y el commit de revisión quedan registrados.

## Recuperar y diagnosticar

El agente puede abrir la ficha del flujo desde `inicio.md` y recuperar un caso por ID. Con `--mapa` el comando trae solo los rangos de las fuentes de ese caso, bajo el presupuesto de recuperación del perfil. El mapa debe coincidir con el commit publicado. Para la búsqueda por texto, la etapa 01 conserva su interfaz `analizar.py --cerebro`.

```sh
python v10/00-creacion-segundo-cerebro/scripts/recuperar_qc.py procesar --id PILOTO-caso --cerebro ENTREGA --flujo consulta-tramite --caso valido-registro
python v10/00-creacion-segundo-cerebro/scripts/recuperar_qc.py procesar --id PILOTO-fuente --cerebro ENTREGA --mapa MAPA --flujo consulta-tramite --caso valido-registro
```

Prepará las [consultas de referencia](ejemplos/consultas-qc.demo.json) antes de revisar resultados. `piloto_qc.py` prueba el mismo motor de recuperación de 01, individualmente y en lote, y agrega la evidencia seleccionada al presupuesto. Reporta casos ausentes, problemas de selección, recortes y evidencia faltante. Para declarar recuperación satisfactoria requiere diez consultas distintas como mínimo, al menos una por flujo crítico y 90% de recuperación en ambas modalidades.

```sh
python v10/00-creacion-segundo-cerebro/scripts/piloto_qc.py procesar --id PILOTO-informe --cerebro ENTREGA --mapa MAPA --consultas CONSULTAS.json --republicacion SEGUNDA_ENTREGA
```

Agregá `--medir-tokens` con `tiktoken` instalado para medir el Markdown con `o200k_base`. `tema_base:true` en las consultas selecciona las rutas para una línea de base anotada en el perfil. Se cuenta la portada una vez por sesión y cada ficha una vez. El informe separa ese costo de los tokens nativos de Copilot y de los caracteres de evidencia. Un aumento frente a la línea base se documenta con `--justificacion-costo`.

Con `--consumo-id` se agrega el corte registrado por `publicar.py medir`. La lectura de caché se informa por separado cuando la fuente exporta el campo. Con `--revision-utilidad` se registra la muestra revisada por QC.

```json
{
  "por": "Responsable de QC",
  "commit": "COMMIT_REVISADO",
  "casos": {
    "consulta-tramite/valido-registro": {"util": true, "detalle": "El escenario contiene los insumos y criterios para diseñar el caso."}
  }
}
```

El diagnóstico deja `piloto-qc.json` y `piloto-qc.md`. Un control sin medición queda en `null` y el código 3 mantiene el piloto inconcluso. Las aserciones ejecutadas se registran con la evidencia del ejecutor. [Medición y diagnóstico](MEDICION.md)

## Primer piloto de COELSA

Usá [las consultas propuestas](ejemplos/consultas-qc.coelsa.json) después de confirmarlas con QC. Definí los IDs de flujo del archivo en el perfil y vinculalos a los casos que respalde el checkout del piloto. La marca `tema_base` agrupa sesión JWT, descarga firmada y RAGFlow para comparar contra los 2.500 tokens del reporte. El alcance funcional incluye además publicación de modelos y recuperación de chat. Si falta soporte, publicá el bloqueo con motivo y conservá la ruta como pendiente. Para el segundo piloto reutilizá el generador con el perfil y los insumos de otra aplicación.
