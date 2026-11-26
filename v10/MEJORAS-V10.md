# Mejoras de QA agentizada V10

La base es V9. La implementación conserva sus tres etapas, los scripts heredados y las entregas con hashes. El diseño debe declarar las capacidades nuevas que correspondan a la aplicación.

| # | Etapa | Cambio implementado | Beneficio esperado |
|---|---|---|---|
| 1 | 01, 02, 03 | Redacción de patrones sensibles antes de guardar el índice, al leer documentación funcional y al consolidar logs. El índice registra archivos afectados y conteos. | Menos exposición en el contexto que recibe Copilot y en los informes. |
| 2 | 02, 03 | Preflight funcional con login, control listo y sonda opcional definida en el perfil. | Detectar al inicio si el entorno permite completar un recorrido real. |
| 3 | 03 | Bloqueo por sesión y propagación a dependientes sin registrar intentos ficticios. | Evitar esperas equivalentes por cada caso y aprovechar los canales independientes. |
| 4 | 03 | Registro del click de login, método, ruta, HTTP y causa. | Distinguir credenciales, permisos, límite de login y problemas de navegación. |
| 5 | 03 | Un estado de navegador en memoria por actor y un contexto separado por caso. Sesión nueva en login y logout. | Reducir logins y conservar el aislamiento de los datos del navegador. |
| 6 | 02, 03 | Selección y comprobación exacta del modelo con `verify_model` y orden explícito. | Probar el modelo acordado y detectar una selección incorrecta antes del envío. |
| 7 | 02, 03 | `capture_count` y `scope` apuntan a un turno nuevo y a sus controles. | Evitar que un mensaje previo apruebe una respuesta incorrecta. |
| 8 | 02, 03 | Guardas de estado con `browser_preconditions` y evidencia por control. | Distinguir una condición que no pudo comprobarse de un fallo funcional del producto. |
| 9 | 02, 03 | Descargas con contenido esperado y estados o errores específicos para variantes de límites. | Afirmar el resultado de negocio con evidencia de contenido o error. |
| 10 | 02 | Identidad de variante por requisito, formato y condición. | Ubicar el formato y la condición que requieren corrección o retest. |
| 11 | 01, 02 | Lote de citas inválidas con causa y rangos disponibles. | Resolver múltiples referencias en una sola revisión. |
| 12 | 02 | XLSX y PDF reproducibles con estructura verificada, semilla y SHA-256. | Repetir pruebas de adjuntos con el mismo archivo. |
| 13 | 03 | Historial entre entregas verificadas con estados automáticos, entradas, evidencia y disposición manual. | Preservar el primer resultado y el del retest junto con el criterio de QA. |
| 14 | 01, 02, 03 | Métricas por ID con tiempos, reintentos, causas y último corte nativo por conversación. | Comparar corridas equivalentes y localizar dónde se concentra la espera. |
| CSV | 02 | Exportador determinista en `exportar_azure.py` con el contrato de QA de V9. | Mantener la importación actual y dejar un punto de cambio cuando cambie el contrato. |

La etapa 00 incorporada después de estas 14 mejoras genera un bundle OKF 0.2 desde un commit Git. Los scripts inventarían el código localmente, entregan contexto acotado a Copilot y reutilizan fichas de módulos vigentes. [Formato del segundo cerebro](00-creacion-segundo-cerebro/FORMATO.md)

[Guía de uso](README.md) · [Contrato Playwright](03-ejecuciones/PERFIL-PLAYWRIGHT.md) · [Inventario de scripts](INVENTARIO-SCRIPTS.md)
