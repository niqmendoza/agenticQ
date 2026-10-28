---
title: "Manejo de errores frontend"
type: concepto
tags: [coelsa-intelligent, diseño, frontend, errores, svelte]
aliases: [Error handling frontend, Componentes de error Svelte, ErrorBoundary COELSA]
description: "Usar cuando necesitás implementar manejo de errores en el frontend de COELSA.Intelligent o entender cómo se renderizan los errores HTTP al usuario."
estado: vigente
---

# Manejo de errores frontend

## Qué es

COELSA.Intelligent tiene un sistema de componentes específicos para cada categoría de error HTTP, más un `ErrorBoundary` para capturar errores de renderizado en componentes Svelte.

## Componentes de error

| Componente | Archivo | Cuándo se muestra |
|-----------|---------|-------------------|
| `NetworkError` | `src/lib/components/error/NetworkError.svelte` | Sin conexión o error de red (0, ECONNREFUSED) |
| `TimeoutError` | `src/lib/components/error/TimeoutError.svelte` | La request excedió el timeout |
| `GenericError` | `src/lib/components/error/GenericError.svelte` | Cualquier error HTTP no categorizado |
| `ErrorBoundary` | `src/lib/components/error/ErrorBoundary.svelte` | Error durante el renderizado de un componente hijo |

## Routing de errores HTTP

`src/routes/+error.svelte` recibe todos los errores HTTP de SvelteKit y los rutea:
- `0` o sin respuesta → `NetworkError`
- Timeout detectado → `TimeoutError`
- Cualquier otro → `GenericError` (con el código y mensaje del backend)

## ErrorBoundary (para errores de render)

Envuelve secciones de UI que podrían fallar durante el renderizado:

```svelte
<ErrorBoundary>
  <ComponenteQuePodriaFallar />
</ErrorBoundary>
```

Si el componente hijo lanza un error durante el render, `ErrorBoundary` lo captura y muestra un fallback en lugar de romper toda la página.

## Relación con el backend

Los errores del backend llegan con la estructura estándar del [[Sistema de errores centralizado]]:
```json
{ "message": "...", "status_code": 400, "details": "..." }
```

Los componentes de error extraen el `message` para mostrarlo al usuario.

## Relacionado

- [[Sistema de errores centralizado]] — Los errores del backend que estos componentes consumen
- [[SvelteKit 2]] — El framework donde viven estos componentes y el router de errores
- [[MOC - Diseño y Frontend]] — Índice del cluster de diseño
