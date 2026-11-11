---
title: "Tokens primitivos de color"
type: referencia
tags: [coelsa-intelligent, diseño, colores, tokens, teal, pink, neutral]
aliases: [Color primitives, Escalas de color COELSA, Teal Pink Neutral]
description: "Usar cuando necesitás la escala de valores hex de los colores primitivos de COELSA.Intelligent (Teal, Pink, Neutral) para definir o revisar tokens semánticos."
estado: vigente
---

# Tokens primitivos de color

## Qué es

Las **escalas de color primitivas** son los valores hex base del [[ECO Design System]]. Son **inmutables** (no cambian entre light y dark mode) y van de 0 (negro puro) a 100 (blanco puro). Se usan exclusivamente para **definir roles semánticos**; no deben usarse directamente en componentes.

## Teal — Color primario COELSA

| Tono | Hex | Uso en roles |
|------|-----|-------------|
| `teal-40` | `#006972` | **primary-light** (~6.2:1 sobre blanco ✓ AA) |
| `teal-60` | `#00A0AD` | Solo texto grande sobre blanco (3.2:1) |
| `teal-80` | `#57D8E6` | **primary-dark** |
| `teal-90` | `#90F2FE` | secondary-dark |

> Teal-60 (#00A0AD) **no pasa WCAG AA** para texto normal sobre blanco (3.2:1). Solo texto grande (≥18px o ≥14px bold).

## Pink — Acento decorativo

| Tono | Hex | Uso en roles |
|------|-----|-------------|
| `pink-60` | `#FF43A8` | Sombras, acentos decorativos (2.5:1 — no textual) |
| `pink-80` | `#FFB0CF` | **tertiary-dark** |
| custom | `#9D0061` | tertiary-light (5.1:1 sobre blanco ✓ AA) |

> Pink-60 (#FF43A8) **no pasa WCAG AA**. Solo efectos decorativos no-textuales.
> `#9D0061` es un valor custom fuera de la escala estándar, usado por necesidad de contraste.

## Neutral — Surfaces y grises

| Tono | Hex | Uso en roles |
|------|-----|-------------|
| `neutral-10` | `#191C1D` | on-surface-dark |
| `neutral-95` | `#EFF1F1` | Surface containers light |
| `neutral-100` | `#FFFFFF` | Blanco |

> `gray-*` en Tailwind es alias de `neutral-*` para retrocompatibilidad. En código nuevo usar `neutral-*` o roles.

## Relacionado

- [[ECO Design System]] — El sistema del que estas escalas forman la base
- [[Roles semánticos de color]] — Los roles construidos sobre estas escalas
- [[Dark mode reglas]] — Cómo los mismos primitivos se usan diferente en cada tema
- [[MOC - Diseño y Frontend]] — Índice del cluster de diseño
