---
title: "Ollama"
type: stack
tags: [coelsa-intelligent, stack, ollama, modelos-ia]
aliases: [Ollama stack, Ollama COELSA]
description: "Usar cuando necesitás configurar Ollama, entender cómo el backend se conecta al servidor de modelos local o diagnosticar errores de routing de modelos."
estado: vigente
---

# Ollama

## Qué es

**Ollama** es el servidor de modelos LLM local que COELSA.Intelligent puede usar como backend de inferencia. Es la vía de acceso "nativa" a modelos que corren en la infraestructura propia.

## Configuración

```env
OLLAMA_BASE_URL=http://localhost:11434
```

Puede haber múltiples URLs de Ollama en `OLLAMA_BASE_URLS` (lista JSON).

## Routing de modelos

El sistema determina si una request va a Ollama o a [[LiteLLM proxy]] según el campo `urlIdx` del modelo. Si `urlIdx` está ausente, se usa el endpoint de Ollama nativo. Ver [[Routing de modelos IA]] y [[Validación de urlIdx]].

**Importante**: modelos con prefijo `ollama/` que están configurados como proxied a través de LiteLLM **deben** tener `urlIdx` para ser correctamente ruteados al endpoint OpenAI, no al nativo de Ollama. Usar el endpoint nativo de Ollama para un modelo proxied LiteLLM genera respuestas vacías.

## Diferencia con LiteLLM

| Característica | Ollama (nativo) | LiteLLM proxy |
|----------------|-----------------|---------------|
| Protocolo | API Ollama nativa | OpenAI-compatible |
| Modelos | Solo modelos locales Ollama | Cualquier proveedor |
| Identificador | Sin `urlIdx` (o `urlIdx` = 0) | Con `urlIdx` definido |

## Relacionado

- [[LiteLLM proxy]] — El proxy OpenAI-compatible que complementa a Ollama
- [[Routing de modelos IA]] — La lógica de selección de endpoint
- [[Validación de urlIdx]] — El fix clave para el routing correcto
- [[MOC - Stack]] — Contexto de Ollama en el stack completo
