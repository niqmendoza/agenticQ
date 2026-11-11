---
title: "Redis"
type: stack
tags: [coelsa-intelligent, stack, redis, websockets, cache]
aliases: [Redis stack, Redis COELSA]
description: "Usar cuando necesitás configurar Redis, entender su rol en los WebSockets o diagnosticar problemas de conectividad entre workers."
estado: vigente
---

# Redis

## Qué es

COELSA.Intelligent usa **Redis 7+** como backend de canal para WebSockets y como cache distribuida. Es la pieza que permite que múltiples instancias del servidor compartan el estado del socket.

## Versión mínima

Redis **7** — para soporte de Streams y configuraciones de seguridad modernas.

## Configuración

```env
# Redis standalone
REDIS_URL=redis://localhost:6379

# Redis Sentinel (alta disponibilidad)
REDIS_SENTINEL_HOSTS=sentinel1:26379,sentinel2:26379
REDIS_SENTINEL_PORT=26379
```

La lógica de conexión está en `backend/server/utils/redis.py` y elige entre standalone y Sentinel según las variables definidas.

## Rol en el sistema

- **Canal de WebSockets**: `python-socketio` usa Redis como bus de mensajes entre instancias de uvicorn. Sin Redis, los WebSockets solo funcionan con un único worker.
- **Cache distribuida**: algunas operaciones costosas cachean resultados en Redis.

## Relacionado

- [[Redis para WebSockets]] — La decisión de arquitectura que justifica el uso de Redis
- [[FastAPI y uvicorn]] — El servidor que usa Redis como canal de socketio
- [[OpenShift]] — El entorno donde escalar horizontalmente requiere Redis
- [[MOC - Stack]] — Contexto de Redis en el stack completo
