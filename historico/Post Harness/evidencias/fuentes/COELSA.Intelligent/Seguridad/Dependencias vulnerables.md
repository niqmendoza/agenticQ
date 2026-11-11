---
title: "Dependencias vulnerables"
type: referencia
tags: [coelsa-intelligent, seguridad, dependencias, cve, npm, overrides]
aliases: [Vulnerable dependencies, CVEs COELSA, Package overrides]
description: "Usar cuando necesitás saber qué dependencias de COELSA.Intelligent tienen CVEs activos, qué versiones son seguras y cómo están manejadas en package.json."
estado: vigente
---

# Dependencias vulnerables

## Qué es

COELSA.Intelligent gestiona las dependencias vulnerables mediante el campo `overrides` en `package.json`, que fuerza a npm a usar versiones seguras de paquetes transitivos aunque los paquetes padre no hayan actualizado sus dependencias.

## Estado actual de CVEs

| Paquete | Versión anterior | Versión segura | Severidad | Estado |
|---------|-----------------|----------------|-----------|--------|
| `jspdf` | ^4.0.0 | ^4.2.1 | HIGH | ✅ Actualizado via override |
| `tar` | 7.5.6 | 7.6.0+ | HIGH | ✅ Actualizado via override |
| `markdown-it` | 14.1.0 | — | — | ⚠️ Falso positivo — ver [[CVE-2025-7969 markdown-it]] |

## Cómo funciona el override

```json
// package.json
{
  "overrides": {
    "jspdf": "^4.2.1",
    "tar": "^7.6.0"
  }
}
```

Cuando npm resuelve el árbol de dependencias, usa la versión del `overrides` en lugar de la que pide el paquete padre. Esto es equivalente a un "force resolution" en otros gestores de paquetes.

## Cuándo revisar

- Al ejecutar `npm audit` — si aparecen nuevas HIGH/CRITICAL, evaluar si requieren override o actualización directa
- Al hacer upgrade de dependencias principales — verificar que los overrides siguen siendo necesarios

## Relacionado

- [[CVE-2025-7969 markdown-it]] — El CVE que resultó ser un falso positivo
- [[MOC - Seguridad]] — Índice del cluster de seguridad
