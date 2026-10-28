---
title: "Patrones frontend críticos"
type: concepto
tags: [coelsa-intelligent, desarrollo, frontend, svelte, patrones, bugs]
aliases: [Critical frontend patterns, Patrones obligatorios frontend]
description: "Usar como checklist antes de mergear cambios en Chat.svelte o componentes de chat — los 4 patrones que no deben revertirse bajo ninguna circunstancia."
estado: vigente
---

# Patrones frontend críticos

## Qué es

Cuatro patrones de código en el frontend de COELSA.Intelligent que resuelven bugs concretos documentados. Su omisión o reversión reproduce los bugs originales. Son **invariantes del codebase**.

> **Referencia completa**: ver [[Patrones de componentes Svelte]] para el código y explicación detallada de cada patrón.

## Checklist rápido

Antes de mergear cambios en `Chat.svelte` o componentes relacionados:

- [ ] **Guarda de `chatId`**: el setter del store solo se llama si `$chatId !== chatIdProp`
- [ ] **AbortController en `loadChat`**: se cancela la request anterior antes de iniciar la nueva
- [ ] **Unsubscribers en `onDestroy`**: todo store suscrito en `onMount` se desuscribe en `onDestroy`
- [ ] **Bloques reactivos unificados**: los bloques `$:` que dependen del mismo state están en un solo bloque

## Consecuencias de revertirlos

| Patrón omitido | Consecuencia |
|---------------|-------------|
| Guarda de chatId | Loop de renderizado infinito al cambiar de chat |
| AbortController ausente | ~80% más de requests duplicados y errores 404 de chunks |
| Unsubscribers ausentes | Memory leaks; listeners fantasma; requests adicionales |
| Bloques reactivos separados | Doble ejecución por cambio de estado |

## Relacionado

- [[Patrones de componentes Svelte]] — El código completo con explicaciones detalladas
- [[SvelteKit 2]] — El framework donde aplican estos patrones
- [[MOC - Desarrollo]] — Índice del cluster de desarrollo
- [[MOC - Decisiones]] — D-20 en el índice de decisiones
