---
title: "MOC — Modelos IA y Routing"
type: moc
tags: [coelsa-intelligent, modelos-ia, routing, mcp, moc]
aliases: [MOC Modelos IA, Routing IA COELSA]
description: "Usar cuando trabajás con routing de modelos, LiteLLM, MCP, tool calling o integración con SharePoint en COELSA.Intelligent."
estado: vigente
---

# MOC — Modelos IA y Routing

El sistema soporta dos vías de acceso a modelos: [[Ollama]] nativo y [[LiteLLM proxy]] como proxy OpenAI-compatible. El campo `urlIdx` distingue cuál usar. El tool calling se implementa via [[MCP y tool calling|MCP]] con JSON prompt para modelos sin function calling nativo.

## Notas de este cluster

- [[Routing de modelos IA]] — Lógica de selección de endpoint; cuándo va a Ollama y cuándo al proxy
- [[Validación de urlIdx]] — Fix clave: por qué `urlIdx` determina el routing y no solo `owned_by`
- [[MCP y tool calling]] — Non-native function calling con JSON prompt; `json.JSONDecoder().raw_decode()`
- [[Cadena SearXNG Context Forge]] — Cadena completa: Open WebUI → MCPO → Context Forge → searxng-mcp → SearXNG
- [[SharePoint OneDrive integración]] — Microsoft File Picker v8; permisos `Files.Read.All`; requisitos de CSP
- [[PyTorch CPU-only]] — Por qué se usa la variante CPU-only (~200MB vs ~2GB CUDA); impacto en imagen Docker

## MOCs vecinos

- [[MOC - Stack]] — Ollama y LiteLLM como componentes del stack
- [[MOC - RAG y Búsqueda Vectorial]] — Cómo los modelos consumen el contexto recuperado por RAG
- [[MOC - Seguridad]] — CSP que debe incluir dominios de Microsoft para SharePoint
- [[MOC - Decisiones]] — Decisión de LiteLLM proxy routing fix (urlIdx)
