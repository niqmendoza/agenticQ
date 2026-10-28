---
title: "MOC — Stack"
type: moc
tags: [coelsa-intelligent, stack, tecnologia, moc]
aliases: [Stack COELSA, Tecnologías COELSA, MOC Stack]
description: "Usar cuando necesitás saber qué tecnología usa COELSA.Intelligent en cada capa, su versión mínima requerida y cómo se configura."
estado: vigente
---

# MOC — Stack

El stack de COELSA.Intelligent cubre todas las capas: frontend, backend, persistencia, mensajería, almacenamiento de objetos, búsqueda vectorial, identidad y despliegue.

## Notas de este cluster

### Frontend
- [[SvelteKit 2]] — Framework SPA con TailwindCSS; SSR deshabilitado; más de 4.500 módulos en build

### Backend
- [[FastAPI y uvicorn]] — Servidor HTTP ASGI con python-socketio para WebSockets

### Persistencia
- [[PostgreSQL]] — Base de datos relacional con SQLAlchemy + Alembic; versión mínima 14
- [[Redis]] — Canal de WebSockets y cache distribuida; versión mínima 7

### Almacenamiento de objetos
- [[MinIO S3]] — Almacenamiento compatible S3 para archivos del sistema

### Búsqueda vectorial
- [[Milvus]] — Base de datos vectorial para RAG con multi-tenancy; versión mínima 2.4

### Identidad
- [[Azure AD OAuth]] — Proveedor OAuth 2.0 / OpenID Connect corporativo; único medio de login

### Modelos IA
- [[Ollama]] — Servidor local de modelos LLM (acceso nativo)
- [[LiteLLM proxy]] — Proxy OpenAI-compatible que unifica múltiples proveedores de modelos

### Despliegue
- [[OpenShift]] — Plataforma de orquestación de contenedores con Azure DevOps CI/CD

## MOCs vecinos

- [[MOC - Arquitectura]] — Decisiones de diseño que motivaron la elección de cada componente
- [[MOC - CI-CD y Despliegue]] — Cómo se construye y despliega cada componente del stack
- [[MOC - RAG y Búsqueda Vectorial]] — Cómo se usa Milvus dentro del sistema RAG
- [[MOC - Modelos IA y Routing]] — Cómo interactúan Ollama y LiteLLM con el sistema
