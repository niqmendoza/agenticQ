---
title: "SvelteKit 2"
type: stack
tags: [coelsa-intelligent, stack, frontend, sveltekit, spa]
aliases: [Frontend SvelteKit, SvelteKit COELSA]
description: "Usar cuando trabajás con el frontend de COELSA.Intelligent: rutas, stores, componentes, build o modo de desarrollo."
estado: vigente
---

# SvelteKit 2

## Qué es

El frontend de COELSA.Intelligent está construido con **SvelteKit 2** en modo SPA (Single Page Application). SSR está explícitamente deshabilitado. Ver [[SPA con SSR deshabilitado]].

## Estructura de carpetas relevante

```
src/
  routes/
    +layout.js        ← ssr = false; trailingSlash = 'ignore'
    +layout.svelte    ← layout raíz con providers de estado
    (app)/            ← rutas autenticadas (chat, admin, workspace)
    auth/             ← login via Azure AD
    +error.svelte     ← manejo de errores HTTP
  lib/
    components/       ← componentes Svelte reutilizables
    stores/           ← estado global reactivo
    i18n/             ← traducciones (es-AR, en-GB, pt-BR)
    utils/            ← helpers y funciones utilitarias
    apis/             ← cliente HTTP para cada dominio del backend
```

## Build

| Comando | Uso | Diferencia |
|---------|-----|------------|
| `npm run dev` | Desarrollo local | Hot-reload; no compatible con nonces CSP |
| `npm run build` | Local completo | Incluye descarga de Pyodide (~500MB) |
| `npm run build:docker` | CI/CD / Docker | Sin Pyodide; más rápido y liviano |

Ver [[Build frontend]] para el detalle de las diferencias y optimizaciones de CI.

## Stack de UI

- **TailwindCSS** — Clases utility con el [[ECO Design System]] de COELSA
- **i18next** — Internacionalización (ver [[Internacionalización i18n]])

## Relacionado

- [[SPA con SSR deshabilitado]] — La decisión de arquitectura que define el modo SPA
- [[Build frontend]] — Diferencias entre comandos de build y optimizaciones CI
- [[Patrones de componentes Svelte]] — Patrones obligatorios que no deben revertirse
- [[ECO Design System]] — El sistema de diseño que se implementa con Tailwind
- [[MOC - Stack]] — Contexto del frontend en el stack completo
