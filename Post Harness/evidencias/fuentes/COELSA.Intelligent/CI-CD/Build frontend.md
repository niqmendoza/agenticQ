---
title: "Build frontend"
type: referencia
tags: [coelsa-intelligent, cicd, frontend, build, pyodide]
aliases: [npm build COELSA, Build SvelteKit, build:docker]
description: "Usar cuando necesitás elegir el comando de build correcto para el contexto (local vs CI/CD) o entender por qué el build puede quedarse sin memoria."
estado: vigente
---

# Build frontend

## Qué es

COELSA.Intelligent tiene **dos comandos de build del frontend** con diferencias significativas en cuándo y dónde se usan.

## Los dos comandos

| Comando | Uso | Incluye Pyodide | RAM necesaria |
|---------|-----|-----------------|--------------|
| `npm run build` | Solo local | ✅ Sí (~500MB adicionales) | 8GB+ sin optimizaciones |
| `npm run build:docker` | CI/CD y Docker | ❌ No | ~4GB con optimizaciones |

**Regla**: en el [[Dockerfile]] y los [[Pipelines Azure DevOps]] siempre usar `npm run build:docker`.

## Por qué la diferencia

**Pyodide** es el runtime WASM de Python que permite ejecutar Python en el navegador. Su descarga requiere ~500MB de red y puede fallar en entornos con acceso a red restringido (como los agents de CI/CD de COELSA). `build:docker` omite este paso.

## Optimizaciones automáticas en CI

`vite.config.ts` detecta entornos CI mediante `CI=true`, `TF_BUILD=True` o `DOCKER=true` y aplica automáticamente:

| Optimización | Impacto |
|-------------|---------|
| Sourcemaps deshabilitados | ~50% menos memoria y tiempo |
| Minificación con esbuild (no terser) | ~40% menos memoria |
| `max-old-space-size=4096MB` | Límite de heap Node.js |

## Volumen del build

El build maneja **más de 4.500 módulos**. Sin las optimizaciones de CI, puede superar **8GB de RAM** y fallar en entornos con límites de memoria.

## Relacionado

- [[Dockerfile]] — El Dockerfile que usa `build:docker`
- [[Pipelines Azure DevOps]] — Los pipelines que ejecutan el build
- [[SvelteKit 2]] — El framework que se compila
- [[MOC - CI-CD y Despliegue]] — Índice del cluster de CI/CD
