---
title: "Patrones de componentes Svelte"
type: concepto
tags: [coelsa-intelligent, diseño, frontend, svelte, patrones, bugs]
aliases: [Svelte patterns, Patrones críticos frontend, Chat.svelte patterns]
description: "Usar cuando modificás Chat.svelte o componentes relacionados — contiene los 4 patrones obligatorios que resuelven bugs concretos y no deben revertirse."
estado: vigente
---

# Patrones de componentes Svelte

## Qué es

Hay **4 patrones de código en el frontend** que resuelven bugs concretos. Su omisión o reversión reproduce los bugs originales. Documentados aquí como referencia obligatoria al trabajar en `Chat.svelte` y componentes relacionados.

## 1. Guarda de `chatId` (evita loop de renderizado)

```typescript
// src/routes/(app)/c/[id]/+page.svelte o Chat.svelte
if ($chatId !== chatIdProp) {
    chatId.set(chatIdProp);
}
```

**Por qué**: sin esta guarda, el cambio de chat dispara una actualización del store que a su vez dispara otro cambio de chat, generando un **loop de renderizado infinito**.

## 2. `AbortController` en `loadChat` (reduce requests duplicados ~80%)

```typescript
let currentController: AbortController | null = null;

async function loadChat(id: string) {
    currentController?.abort();  // Cancela la carga anterior
    currentController = new AbortController();
    const data = await fetchChat(id, { signal: currentController.signal });
}
```

**Por qué**: si el usuario cambia de chat antes de que termine de cargar el anterior, sin `AbortController` ambas requests corren en paralelo y pueden pisarse. Reduce ~80% de requests duplicados.

## 3. Unsubscribers en `onDestroy` (evita memory leaks)

```typescript
import { onMount, onDestroy } from 'svelte';

let unsub: () => void;

onMount(() => {
    unsub = someStore.subscribe(value => { ... });
});

onDestroy(() => {
    unsub?.();  // OBLIGATORIO: limpiar la suscripción
});
```

**Por qué**: los stores suscritos en `onMount` acumulan listeners si no se destruyen en `onDestroy`. Los listeners fantasma disparan requests adicionales y pueden causar actualizaciones en componentes desmontados.

## 4. Bloques reactivos unificados (evita ejecuciones duplicadas)

```typescript
// MAL — separados generan doble ejecución:
$: if (selectedModels) updateModels();
$: if (selectedModels) setToolIds();

// BIEN — unificados:
$: {
    if (selectedModels) {
        updateModels();
        setToolIds();
    }
}
```

**Por qué**: los bloques `$:` separados que dependen del mismo reactive value se ejecutan independientemente. Al unificarlos, solo hay una ejecución por cambio de estado.

## Relacionado

- [[SvelteKit 2]] — El framework donde aplican estos patrones
- [[MOC - Desarrollo]] — Índice del cluster de desarrollo
- [[MOC - Decisiones]] — D-20 en el índice de decisiones (AbortController fix)
