# Contrato de registros

`python3 src/qa.py record --run RUTA --json ARCHIVO` agrega un objeto o una lista de objetos al historial y regenera el log. Se valida el lote entero antes de escribir; un registro inválido rechaza todo el lote. Guardar los JSON de entrada fuera del corpus. Se aceptan campos adicionales: permiten detallar versión, hora observada, precondiciones, pasos, ambiente, duración, correlación y archivos de evidencia. Evitar secretos y datos personales. Los campos mínimos no prueban que su contenido sea cierto.

| kind | Campos obligatorios | Significado |
| --- | --- | --- |
| `case` | `id`, `title`, `expected`, `oracle_status`, `sources` | Plan; `oracle_status`: `documented`, `inferred`, `pending`. Usar una referencia o explicación de ausencia en `sources`. |
| `execution` | `case_id`, `status`, `observation`, `evidence` | Intento; `status`: `passed`, `failed`, `blocked`, `not_run`. El caso debe existir. |
| `finding` | `id`, `observation`, `evidence`, `interpretation`, `pending` | Defecto o hipótesis, separado de los casos. |
| `note` | `phase`, `observation` | Actividad, decisión, límite o resumen del paso. |

Los IDs de casos y hallazgos no se repiten dentro de su tipo. Los intentos sí se repiten: el resumen cuenta el último resultado de cada caso y conserva todos en la cronología. Las horas asignadas por la herramienta son UTC; la hora observada puede agregarse como `observed_at`. El archivo de evidencia debe ser accesible al equipo y estar sanitizado; el sistema no comprueba su existencia o contenido. No hay bloqueo entre escritores, edición ni eliminación de eventos: para una corrección registrar una nota que identifique el error y, para resultados, un nuevo intento.

`log.md` es una representación derivada de `run.json` y `events.json`, no almacena automáticamente la salida de otras herramientas. Copiar ambos junto con `artifacts/` cuando se transfiera la sesión. El índice guarda texto del corpus; protegerlo como la fuente. El log puede incluir rutas y datos internos: revisar antes de compartir.

## CSV derivados

Cada actualización de la sesión regenera `casos.csv` (casos y último estado; `sin_ejecutar` cuando no hay intento) y `ejecuciones.csv` (todos los intentos). Las columnas de funcionalidad, requisito, prioridad, nivel, precondiciones y pasos se completan con `feature`, `requirement`, `priority`, `level`, `preconditions` y `steps` de cada caso; si no fueron informadas quedan vacías. Listas y objetos se serializan como JSON dentro de la celda. Los CSV usan UTF-8 con BOM, comillas estándar y prefijo de seguridad para texto que pueda interpretarse como fórmula; el valor original permanece en `events.json`. Los CSV son reportes, no un formato de importación de Azure.
