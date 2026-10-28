---
title: "Redis para WebSockets"
type: decision
tags: [coelsa-intelligent, arquitectura, redis, websockets]
aliases: [Redis WebSocket backend, Canal de WebSockets]
description: "Usar cuando necesitás entender por qué Redis es el canal de comunicación del socket y qué permite en términos de escalado horizontal."
estado: vigente
---

# Redis para WebSockets

## Qué es

El servidor de WebSocket de COELSA.Intelligent (implementado con `python-socketio`) usa **Redis como backend de canal**. Esto permite que múltiples instancias del servidor compartan el estado del socket sin pérdida de eventos entre workers.

## Configuración

```env
REDIS_URL=redis://host:6379
# O con Redis Sentinel para alta disponibilidad:
REDIS_SENTINEL_HOSTS=sentinel1:26379,sentinel2:26379
REDIS_SENTINEL_PORT=26379
```

## Por qué Redis

Sin un backend de canal compartido, cada instancia del servidor tendría su propia cola de eventos. Un mensaje enviado por un cliente conectado al worker A no llegaría a los clientes conectados al worker B. Redis resuelve este problema actuando como bus de mensajes entre instancias.

En [[OpenShift]] el servidor puede escalar horizontalmente (múltiples pods) gracias a este diseño. Sin Redis, el WebSocket funciona solo con un único worker.

## Configuración de conexión (`config.py`)

La conexión a Redis se obtiene a través de `get_redis_connection()` en `server/utils/redis.py`, que soporta tanto Redis standalone como Redis Sentinel.

## Relacionado

- [[Redis]] — Nota de stack con versiones mínimas y configuración
- [[FastAPI y uvicorn]] — El servidor donde se monta python-socketio
- [[OpenShift]] — El entorno donde se escala horizontalmente
- [[MOC - Arquitectura]] — Contexto de la decisión
- [[MOC - Decisiones]] — D-03 en el índice de decisiones
