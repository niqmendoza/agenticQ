---
title: "MCP y tool calling"
type: concepto
tags: [coelsa-intelligent, modelos-ia, mcp, tool-calling, function-calling]
aliases: [MCP tool calling, Non-native function calling, JSON prompt tool calling]
description: "Usar cuando necesitás entender cómo COELSA.Intelligent implementa tool calling para modelos sin function calling nativo, o cómo está configurada la integración MCP."
estado: vigente
---

# MCP y tool calling

## Qué es

COELSA.Intelligent integra **Model Context Protocol (MCP)** para exponer herramientas (tools) a los modelos. La herramienta principal configurada es [[Cadena SearXNG Context Forge|búsqueda web via SearXNG]].

## Dos modos de tool calling

### 1. Native function calling
Modelos que soportan function calling nativo (formato OpenAI `tools`). El backend envía las herramientas disponibles en el payload y el modelo responde con llamadas estructuradas.

### 2. Non-native function calling (JSON prompt)
El modelo `gpt-oss:120b` **no soporta tool calling nativo de forma confiable**. COELSA.Intelligent implementa un workaround:

1. Las herramientas disponibles se describen en el **system prompt** como JSON
2. Se le indica al modelo que responda con un JSON específico cuando quiera llamar una herramienta
3. El backend parsea la respuesta del modelo buscando el JSON de tool call
4. Ejecuta la herramienta y vuelve a llamar al modelo con el resultado

## Parsing robusto de JSON

Los modelos grandes frecuentemente incluyen texto adicional antes o después del JSON válido. El parser usa `json.JSONDecoder().raw_decode()` para tolerar este "ruido":

```python
# backend/server/utils/middleware.py
decoder = json.JSONDecoder()
obj, end_idx = decoder.raw_decode(model_response)
# obj es el JSON válido; el texto después de end_idx se descarta
```

## Configuración

```env
TOOL_SERVER_CONNECTIONS=[
  {
    "url": "http://host:8000/contextforge",
    "path": "openapi.json",
    "auth_type": "bearer",
    "key": "..."
  }
]
```

## Relacionado

- [[Cadena SearXNG Context Forge]] — La cadena concreta de tool calling para búsqueda web
- [[LiteLLM proxy]] — El proxy a través del cual pasan las requests al modelo
- [[MOC - Modelos IA y Routing]] — Índice del cluster de modelos
- [[MOC - Decisiones]] — D-09 en el índice de decisiones
