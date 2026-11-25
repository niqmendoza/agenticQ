# Instrucciones adicionales para Copilot · Evaluación de modelos V9

Usá estas instrucciones junto con el [alcance del encargo](../../../01-analisis/PROMPT.md). La persona que prepara la evaluación elige el modelo en el cliente y repite la misma consigna en una conversación nueva por corrida.

```text
Esta corrida pertenece a una evaluación de modelos con el harness de QA V9. Ejecutá únicamente el encargo de QA de esta sesión y dejá los registros requeridos por el CLI avanzado.

- Carpeta V9 · {ruta_absoluta_v8}
- ID del benchmark · {benchmark}
- Consigna común congelada · {ruta_consigna_md}
- Etiqueta del modelo · {etiqueta}
- ID exacto del modelo devuelto por la fuente de telemetría · {id_esperado}
- Ruta privada del archivo de contadores y conversación · {ruta_formato_y_conversacion}
- ID nuevo para la sesión de QA · {id_corrida}

1. Usá la consigna congelada. Abrí solo la consigna y el material de QA que ella autoriza. Evitá consultar la rúbrica del evaluador o resultados de otras corridas. Verificá el build y el entorno antes de iniciar la sesión. Tomá los datos de acceso de los mecanismos autorizados. Dejá los secretos en sus fuentes.
2. Inicializá la sesión con v9/03-ejecuciones/scripts/qa.py init --benchmark y verificá la fuente con tokens-check según MEDICION-TOKENS.md. Ejecutá desde la carpeta que contiene v9/.
   python3 v9/03-ejecuciones/scripts/benchmark/evaluate.py preparar --benchmark {benchmark} --run {id_corrida} --modelo {etiqueta} --modelo-esperado {id_esperado}
   Si falla la verificación nativa del modelo o de los tokens, avisá a la persona que coordina y detené las pruebas. Aplicá también las reglas de preflight y de Playwright del encargo congelado.
3. Marcá una vez el inicio de cada etapa con v9/03-ejecuciones/scripts/qa.py tokens-stage. Usá analisis antes de consultar el segundo cerebro, diseno antes de redactar los casos y congelar el plan, ejecucion antes del primer intento y cierre al terminar las pruebas. Usá la misma instantánea del segundo cerebro y los mismos fixtures indicados en la consigna. Si necesitás volver a una fuente durante otra etapa, registrá el motivo en el log y conservá el corte de la etapa donde ocurrió.
4. Ejecutá el encargo con el CLI avanzado y completá las notas de análisis, pruebas y cierre. Dejá rastros verificables de las fuentes consultadas, las reglas recuperadas, los casos diseñados y los intentos observados. La evaluación de calidad la hace un revisor con las evidencias de la corrida.
5. Publicá el paquete de evidencias y las demás entregas aplicables, incluidos preflight, bloqueos y evidencias. Luego ejecutá python3 v9/03-ejecuciones/scripts/benchmark/evaluate.py finalizar --run {id_corrida}. Intentá archivar con python3 v9/03-ejecuciones/scripts/benchmark/evaluate.py archivar --run {id_corrida}. Si la telemetría aún no alcanza el cierre, informá que falta archivar y dejá el comando exacto para repetirlo desde la terminal al terminar la conversación. Si la corrida quedó bloqueada, podés archivarla con --incompleta para conservar sus evidencias y el motivo.
```
