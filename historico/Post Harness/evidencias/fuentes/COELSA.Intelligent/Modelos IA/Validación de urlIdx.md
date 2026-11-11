---
title: "Validación de urlIdx"
type: decision
tags: [coelsa-intelligent, modelos-ia, litellm, routing, bug-fix]
aliases: [urlIdx fix, LiteLLM routing fix, Respuestas vacías LiteLLM]
description: "Usar cuando diagnosticás respuestas vacías con modelos LiteLLM de prefijo ollama/ o cuando necesitás entender el fix de routing del CHANGELOG v1.3.0."
estado: vigente
---

# Validación de urlIdx

## El problema (upstream bug)

El upstream Open WebUI determinaba el endpoint de un modelo basándose **únicamente** en el campo `owned_by`:
- `owned_by == "ollama"` → endpoint nativo de Ollama
- Cualquier otro → endpoint OpenAI

**El mismatch**: modelos configurados en LiteLLM con prefijo `ollama/` (ej: `ollama/llama3:70b`) tienen `owned_by=ollama`. El upstream los enviaba al endpoint nativo de Ollama, pero LiteLLM **siempre responde en formato OpenAI**, no en el formato nativo de Ollama. El mismatch de formato generaba **respuestas vacías en la UI**.

## La corrección

```python
# backend/server/utils/chat.py (líneas ~263–293)
# ANTES (upstream):
if model.owned_by == "ollama":
    endpoint = OLLAMA_BASE_URL

# DESPUÉS (fix COELSA):
if model.urlIdx is not None:
    # El modelo es proxied (vía LiteLLM o similar) → siempre OpenAI
    endpoint = OPENAI_API_BASE_URL
elif model.owned_by == "ollama":
    # Modelo nativo de Ollama sin proxy
    endpoint = OLLAMA_BASE_URL
else:
    endpoint = OPENAI_API_BASE_URL
```

## Regla resultante

| Condición | Destino |
|-----------|---------|
| `urlIdx` definido | LiteLLM proxy (OpenAI endpoint) |
| `urlIdx` ausente + `owned_by == "ollama"` | Ollama nativo |
| Default | LiteLLM proxy |

## Relacionado

- [[Routing de modelos IA]] — La lógica de routing completa donde vive este fix
- [[LiteLLM proxy]] — El proxy que siempre responde en formato OpenAI
- [[Ollama]] — El servidor nativo que usa su propio formato
- [[MOC - Decisiones]] — D-08 en el índice de decisiones
- [[MOC - Modelos IA y Routing]] — Índice del cluster de modelos
