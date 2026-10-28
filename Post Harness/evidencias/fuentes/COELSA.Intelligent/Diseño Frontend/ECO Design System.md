---
title: "ECO Design System"
type: concepto
tags: [coelsa-intelligent, diseño, eco-design-system, material-design, ui]
aliases: [ECO Design, Design system COELSA, Sistema de diseño COELSA]
description: "Usar cuando necesitás entender el sistema de diseño visual de COELSA.Intelligent: principios, arquitectura de tokens y archivos canónicos."
estado: vigente
---

# ECO Design System

## Qué es

El **ECO Design System** es el sistema de diseño visual de COELSA.Intelligent, basado en **Material Design 3** y adaptado a la identidad corporativa de COELSA (Teal + Pink).

## Principios fundamentales

| Principio | Descripción |
|-----------|-------------|
| **Tokens primero** | Nunca hardcodear hex. Usar siempre roles/tokens semánticos |
| **Teal = Primary, siempre** | Teal es el color de acción en ambos temas. Pink es acento/decorativo |
| **Accesibilidad no negociable** | WCAG AA (4.5:1 texto normal, 3:1 texto grande) |
| **Jerarquía mediante surfaces** | 5 niveles de surface-container; nunca opacidad arbitraria |
| **Un concepto, un lugar** | Cada token se define una vez en `colors.css` y se expone via Tailwind |

## Arquitectura de 3 niveles

```
Nivel 1: Tokens Primitivos (escalas Teal, Pink, Neutral 0→100)
         src/lib/styles/colors.css
              ↓ referenciados por
Nivel 2: Roles Semánticos (primary, on-primary, surface, etc.)
         src/lib/styles/colors.css + tailwind.config.js
              ↓ consumidos por
Nivel 3: Componentes / Clases Utility
         src/app.css, src/lib/utils/theme.ts, componentes Svelte
```

## Archivos canónicos

| Archivo | Responsabilidad |
|---------|-----------------|
| `src/lib/styles/colors.css` | Definición de todos los tokens CSS |
| `tailwind.config.js` | Expone tokens como clases Tailwind |
| `src/app.css` | Clases tipográficas; imports base |
| `src/tailwind.css` | @font-face Saira; config Tailwind v4 |
| `src/lib/utils/theme.ts` | Helpers para botones interactivos |

## Documentación completa

`docs/ECO-DESIGN-SYSTEM.md` — Single source of truth del sistema.

## Relacionado

- [[Tokens primitivos de color]] — Las escalas inmutables de la Capa 1
- [[Roles semánticos de color]] — Los roles de la Capa 2 que cambian entre temas
- [[Surface Containers]] — Los 5 niveles de jerarquía visual
- [[Tipografía Saira]] — La fuente corporativa del sistema
- [[Dark mode reglas]] — Cómo se comportan los roles en modo oscuro
