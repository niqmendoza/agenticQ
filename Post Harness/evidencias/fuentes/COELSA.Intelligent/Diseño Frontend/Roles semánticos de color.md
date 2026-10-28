---
title: "Roles semánticos de color"
type: referencia
tags: [coelsa-intelligent, diseño, colores, roles, tailwind, css-variables]
aliases: [Semantic color roles, Roles de color, Color roles COELSA]
description: "Usar cuando necesitás la lista de roles de color disponibles en Tailwind y CSS variables para implementar componentes en COELSA.Intelligent."
estado: vigente
---

# Roles semánticos de color

## Qué es

Los **roles semánticos** son tokens de tema que cambian automáticamente entre light y dark mode via CSS custom properties. Son la capa 2 del [[ECO Design System]]. Siempre se prefieren sobre las escalas primitivas en componentes.

## Roles principales (light / dark)

| Rol CSS | Light | Dark | Uso |
|---------|-------|------|-----|
| `--color-primary` | `#006972` (teal-40) | `#57D8E6` (teal-80) | Botones CTA, acciones principales |
| `--color-on-primary` | `#FFFFFF` | `#00363B` (teal-20) | Texto/icono sobre primary |
| `--color-secondary` | `#004F56` (teal-30) | `#90F2FE` (teal-90) | Acciones secundarias, outlined buttons |
| `--color-on-secondary` | `#FFFFFF` | `#00363B` (teal-20) | Texto/icono sobre secondary |
| `--color-tertiary` | `#9D0061` (custom) | `#FFB0CF` (pink-80) | Badges, notificaciones, acentos |
| `--color-on-tertiary` | `#FFFFFF` | `#63003C` (pink-20) | Texto/icono sobre tertiary |
| `--color-surface` | `#FFFFFF` | `#191C1D` | Fondo base de la app |
| `--color-on-surface` | `#191C1D` | `#EFF1F1` | Texto principal |

## Clases Tailwind disponibles

```html
<!-- Botón principal -->
<button class="bg-primary text-on-primary hover:opacity-90">
  Acción Principal
</button>

<!-- Botón secundario -->
<button class="border-2 border-secondary text-secondary hover:bg-secondary/10">
  Acción Secundaria
</button>

<!-- Badge de acento -->
<span class="bg-tertiary text-on-tertiary px-3 py-1 rounded-full">
  Badge
</span>
```

## Regla de uso de on-* colors

**Siempre** usar el color `on-*` para texto/iconos sobre un fondo de rol:
- Fondo `bg-primary` → texto `text-on-primary`
- Fondo `bg-secondary` → texto `text-on-secondary`
- Fondo `bg-surface` → texto `text-on-surface`

No asumir que "el texto siempre es blanco" o "siempre es negro"; los roles invierten en dark mode.

## Relacionado

- [[Tokens primitivos de color]] — Los valores hex que definen estos roles
- [[Surface Containers]] — Los 5 roles de superficie para jerarquía visual
- [[Dark mode reglas]] — Cómo se invierten los roles en dark mode
- [[ECO Design System]] — El sistema del que estos roles son parte
