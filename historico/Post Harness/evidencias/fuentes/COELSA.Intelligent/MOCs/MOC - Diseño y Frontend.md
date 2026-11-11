---
title: "MOC — Diseño y Frontend"
type: moc
tags: [coelsa-intelligent, diseño, frontend, eco-design-system, moc]
aliases: [MOC Diseño, Frontend COELSA, ECO Design System MOC]
description: "Usar cuando trabajás con la UI, el sistema de diseño ECO, colores, tipografía, dark mode o componentes de error en COELSA.Intelligent."
estado: vigente
---

# MOC — Diseño y Frontend

El diseño visual está gobernado por el [[ECO Design System]], basado en Material Design 3. Teal (`#06ABB9`) es el color primario COELSA; Pink es solo acento decorativo. El frontend es una [[SvelteKit 2|SPA en SvelteKit 2]] con SSR deshabilitado.

## Notas de este cluster

### Sistema de diseño
- [[ECO Design System]] — Overview del sistema basado en Material Design 3; principios y archivos canónicos
- [[Tokens primitivos de color]] — Escalas inmutables Teal, Pink, Neutral (0→100) usadas para definir roles
- [[Roles semánticos de color]] — `primary`, `secondary`, `tertiary`, `surface` y sus pares `on-*`; cambian entre temas
- [[Surface Containers]] — Los 5 niveles de jerarquía visual (lowest → highest) para profundidad sin opacidad
- [[Tipografía Saira]] — Fuente corporativa Saira; clases tipográficas de `app.css`
- [[Dark mode reglas]] — Cómo se invierten roles (no escalas primitivas) al cambiar de tema

### Componentes y patrones
- [[Patrones de componentes Svelte]] — Guarda chatId; AbortController; unsubscribers en onDestroy; bloques reactivos unificados
- [[Manejo de errores frontend]] — `NetworkError`, `TimeoutError`, `GenericError`, `ErrorBoundary`; routing en `+error.svelte`
- [[Internacionalización i18n]] — es-AR principal; en-GB y pt-BR disponibles; idiomas eliminados

## MOCs vecinos

- [[MOC - Arquitectura]] — SSR deshabilitado como decisión de diseño con implicaciones de seguridad
- [[MOC - Desarrollo]] — Patrones críticos que no deben revertirse en el frontend
- [[MOC - Seguridad]] — CSP y nonces que afectan cómo se cargan los scripts del frontend
