---
title: "Cadena SearXNG Context Forge"
type: concepto
tags: [coelsa-intelligent, modelos-ia, searxng, mcp, busqueda-web]
aliases: [SearXNG integration, Context Forge chain, Búsqueda web MCP]
description: "Usar cuando necesitás entender cómo está implementada la búsqueda web en COELSA.Intelligent: la cadena completa desde el modelo hasta SearXNG."
estado: vigente
---

# Cadena SearXNG Context Forge

## Qué es

La integración de búsqueda web en COELSA.Intelligent usa una cadena de 4 componentes:

```
Open WebUI → MCPO (puerto 8000) → Context Forge (puerto 4444) → searxng-mcp → SearXNG
```

## Componentes

| Componente | Puerto | Rol |
|-----------|--------|-----|
| **MCPO** | 8000 | Proxy MCP → HTTP que convierte el protocolo MCP a una API HTTP/OpenAPI |
| **Context Forge** | 4444 | Orquestador de contexto; registra herramientas MCP y las expone via OpenAPI |
| **searxng-mcp** | — | Servidor MCP que envuelve SearXNG con el protocolo MCP |
| **SearXNG** | — | Motor de búsqueda metasearch (privado, self-hosted) |

## Por qué esta cadena

- SearXNG es self-hosted para mantener privacidad (sin tracking de búsquedas)
- MCP es el protocolo estándar para tool calling en agentes IA
- MCPO convierte MCP a HTTP/OpenAPI, que es lo que Open WebUI entiende como tool server

## Configuración

```env
TOOL_SERVER_CONNECTIONS=[
  {
    "url": "http://host:8000/contextforge",
    "path": "openapi.json",
    "auth_type": "bearer",
    "key": "tu-api-key"
  }
]
```

## Relación con non-native function calling

Para el modelo `gpt-oss:120b` (sin function calling nativo), la herramienta se describe en el system prompt. Ver [[MCP y tool calling]] para el detalle del JSON prompt.

## Relacionado

- [[MCP y tool calling]] — El mecanismo de tool calling que usa esta cadena
- [[MOC - Modelos IA y Routing]] — Índice del cluster de modelos
- [[MOC - Decisiones]] — D-10 en el índice de decisiones
