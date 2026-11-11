---
title: "LiteLLM proxy"
type: stack
tags: [coelsa-intelligent, stack, litellm, proxy, modelos-ia]
aliases: [LiteLLM, Proxy OpenAI COELSA]
description: "Usar cuando necesitás configurar LiteLLM como proxy, entender el routing de modelos proxied o diagnosticar respuestas vacías con modelos ollama/ prefijados."
estado: vigente
---

# LiteLLM proxy

## Qué es

**LiteLLM** es un proxy OpenAI-compatible que unifica el acceso a múltiples proveedores de modelos (OpenAI, Azure OpenAI, Anthropic, Ollama, etc.) bajo una única API estándar. COELSA.Intelligent lo usa para acceder a modelos que no están en Ollama nativo.

## Configuración

```env
OPENAI_API_BASE_URL=http://litellm:4000/v1
OPENAI_API_KEY=sk-...
```

## El problema de routing (resuelto)

Los modelos con prefijo `ollama/` en LiteLLM tienen `owned_by=ollama`. El upstream de Open WebUI usaba solo `owned_by` para decidir el endpoint, y los enviaba incorrectamente al endpoint nativo de Ollama. LiteLLM siempre responde en **formato OpenAI**, no en formato Ollama nativo, lo que generaba **respuestas vacías en la UI**.

La corrección valida también el campo `urlIdx`: si está presente, el modelo es proxied y debe usar el endpoint OpenAI (LiteLLM), independientemente del valor de `owned_by`.

Ver [[Validación de urlIdx]] para el detalle técnico.

## Modelo con non-native function calling

El modelo `gpt-oss:120b` usa JSON prompt en lugar de function calling nativo porque no soporta tool calling de forma confiable. Ver [[MCP y tool calling]].

## Relacionado

- [[Ollama]] — El servidor de modelos nativos que coexiste con LiteLLM
- [[Routing de modelos IA]] — La lógica que decide cuándo ir a LiteLLM
- [[Validación de urlIdx]] — El fix del bug de respuestas vacías
- [[MCP y tool calling]] — Cómo se implementa tool calling para modelos via LiteLLM
- [[MOC - Stack]] — Contexto de LiteLLM en el stack completo
