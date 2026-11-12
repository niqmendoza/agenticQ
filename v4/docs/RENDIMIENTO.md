# Medición exploratoria del motor

Se comparó la copia V3 anterior a la optimización con el motor optimizado, en el mismo equipo, sobre el corpus histórico de 80 documentos y 583 fragmentos. Para 20 consultas (10 consultas repetidas) se midió una indexación nueva y la mediana de cinco ejecuciones del ranking; sin llamadas a modelos ni red. El hash del resultado completo de rankings fue idéntico en ambos motores con `PYTHONHASHSEED=0`.

| Operación | Antes | Después |
| --- | ---: | ---: |
| Indexación nueva | 0,1273 s | 0,0628 s |
| Ranking por lote, mediana | 0,0819 s | 0,0074 s |

Es una medición local y pequeña, no una garantía para otro corpus ni una medida de duración del proceso completo. En indexación se reutiliza el índice de nombres y aliases al resolver enlaces; en búsqueda se leen y deserializan los fragmentos una vez por lote. Se eliminaron del soporte V3 las funciones CLI heredadas de V1 que no usaba el motor; los archivos históricos se conservan.

Para repetir la medición de un motor, desde la raíz del repositorio:

```sh
PYTHONHASHSEED=0 python3 qa-v3/tools/benchmark.py qa-v3/src/engine 'historico/Post Harness/evidencias/fuentes/COELSA.Intelligent'
PYTHONHASHSEED=0 python3 qa-v3/tools/benchmark.py 'historico/Post Harness V2/scripts' 'historico/Post Harness/evidencias/fuentes/COELSA.Intelligent'
```

El resultado incluye un hash del ranking para comparar equivalencia con la misma versión de Python, semilla y corpus. La prueba no verifica la calidad semántica de la búsqueda.
