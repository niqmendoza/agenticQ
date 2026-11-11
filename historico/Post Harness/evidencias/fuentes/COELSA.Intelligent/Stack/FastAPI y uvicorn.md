---
title: "FastAPI y uvicorn"
type: stack
tags: [coelsa-intelligent, stack, backend, fastapi, uvicorn, asgi]
aliases: [Backend FastAPI, API server COELSA]
description: "Usar cuando trabajás con el servidor HTTP del backend: agregar endpoints, entender el ciclo de vida de la app, o debuggear requests."
estado: vigente
---

# FastAPI y uvicorn

## Qué es

El backend de COELSA.Intelligent está construido sobre **FastAPI 0.115** como framework HTTP, corriendo bajo **uvicorn** como servidor ASGI. Además integra **python-socketio** para la comunicación WebSocket en tiempo real.

## Entry point

```
backend/server/main.py
```

`main.py` monta todos los routers, registra los middlewares y define el ciclo de vida de la aplicación (`lifespan`). La app de socketio se monta como sub-aplicación en `/ws`.

## Routers registrados

La API expone rutas bajo `/api/v1/`:

```
audio, auths, channels, chats, configs, evaluations, files,
files_storage_endpoints, folders, functions, groups, images,
knowledge, memories, models, ollama, openai, pipelines,
prompts, retrieval, storage_management, tasks, tools, users, utils
```

## Middlewares

- `CORSMiddleware` — Orígenes permitidos configurables
- `SessionMiddleware` — Sesiones HTTP
- `NonceInjectionMiddleware` — Nonces CSP (ver [[CSP con nonces]])
- `AuditLoggingMiddleware` — Registro de auditoría

## Arranque en desarrollo

```bash
cd backend
./dev.sh   # hot-reload activado
```

Ver [[Ejecución local]] para detalle completo.

## Relacionado

- [[Redis para WebSockets]] — python-socketio usa Redis como canal de mensajes
- [[Agregar router REST]] — Cómo extender la API con nuevos endpoints
- [[CSP con nonces]] — El middleware de nonces que se registra en esta app
- [[Sistema de errores centralizado]] — Los handlers de excepción se registran aquí
- [[MOC - Stack]] — Contexto del backend en el stack completo
