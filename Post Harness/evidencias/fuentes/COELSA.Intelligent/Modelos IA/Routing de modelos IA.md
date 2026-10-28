---
title: "Routing de modelos IA"
type: concepto
tags: [coelsa-intelligent, modelos-ia, routing, ollama, litellm]
aliases: [Model routing, Selección de endpoint de modelos]
description: "Usar cuando necesitás entender cómo COELSA.Intelligent decide si una request de chat va al endpoint nativo de Ollama o al proxy LiteLLM."
estado: vigente
---

# Routing de modelos IA

## Qué es

Cuando un usuario envía un mensaje, el backend debe decidir a qué endpoint enviar la request de inferencia. COELSA.Intelligent soporta dos destinos:
- **[[Ollama]]** nativo — endpoint Ollama en `OLLAMA_BASE_URL`
- **[[LiteLLM proxy]]** — proxy OpenAI-compatible en `OPENAI_API_BASE_URL`

## Lógica de routing

```
backend/server/utils/chat.py (líneas ~263–293)
```

El routing evalúa en orden:

1. **¿Tiene `urlIdx`?** → Si está definido, el modelo es proxied → usar endpoint OpenAI (LiteLLM)
2. **¿`owned_by` == "ollama"?** → Usar endpoint nativo de Ollama
3. **Default** → Usar endpoint OpenAI (LiteLLM)

## Por qué `urlIdx` tiene prioridad

El campo `owned_by` no es suficiente para determinar el endpoint correcto. Los modelos con prefijo `ollama/` en LiteLLM tienen `owned_by=ollama` pero **deben** ir al proxy, no al endpoint nativo de Ollama. Si van al endpoint nativo, LiteLLM no puede procesar la respuesta y la UI muestra respuestas vacías.

Ver [[Validación de urlIdx]] para el detalle del bug y la corrección.

## Formatos de respuesta

| Endpoint | Formato de respuesta |
|----------|---------------------|
| Ollama nativo | Formato Ollama propio |
| LiteLLM proxy | Formato OpenAI estándar (siempre) |

## Relacionado

- [[Validación de urlIdx]] — El fix específico que resuelve el bug de respuestas vacías
- [[Ollama]] — El servidor de modelos nativo
- [[LiteLLM proxy]] — El proxy OpenAI-compatible
- [[MCP y tool calling]] — La capa de tool calling que corre sobre el routing
- [[MOC - Modelos IA y Routing]] — Índice del cluster de modelos
