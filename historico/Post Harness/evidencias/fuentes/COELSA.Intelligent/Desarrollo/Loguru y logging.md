---
title: "Loguru y logging"
type: referencia
tags: [coelsa-intelligent, desarrollo, logging, loguru, debug]
aliases: [Logging COELSA, loguru COELSA, LOG_LEVEL]
description: "Usar cuando necesitás configurar el nivel de logging de COELSA.Intelligent, agregar logs a un módulo nuevo o entender la estructura de niveles de log por módulo."
estado: vigente
---

# Loguru y logging

## Qué es

El backend de COELSA.Intelligent usa **loguru** como librería de logging. El nivel de log se controla por variable de entorno y se puede ajustar por módulo.

## Configuración

```env
LOG_LEVEL=INFO
```

Niveles disponibles: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

## Uso en módulos

```python
from server.env import SRC_LOG_LEVELS
import logging

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])  # o "MODELS", "OAUTH", etc.

log.info("Mensaje informativo")
log.error(f"Error: {e}")
log.exception(f"Error con traceback: {e}")
```

## Niveles por módulo (`SRC_LOG_LEVELS`)

La variable `SRC_LOG_LEVELS` en `server/env.py` mapea áreas del sistema a sus niveles:

| Clave | Módulos afectados |
|-------|------------------|
| `MAIN` | Arranque, config, main.py |
| `MODELS` | ORM, modelos SQLAlchemy |
| `OAUTH` | Autenticación, JWT |
| `RAG` | Retrieval, embeddings |
| `DB` | Consultas a base de datos |

## Filtrado de endpoints frecuentes

El log de acceso de uvicorn filtra las requests a `/health` para evitar spam en los logs:

```python
class EndpointFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage().find("/health") == -1
```

## Relacionado

- [[FastAPI y uvicorn]] — El servidor donde se configura el logging de acceso
- [[Ejecución local]] — Cómo ver los logs en modo desarrollo
- [[MOC - Desarrollo]] — Índice del cluster de desarrollo
