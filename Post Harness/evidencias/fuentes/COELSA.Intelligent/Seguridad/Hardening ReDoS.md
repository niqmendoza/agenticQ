---
title: "Hardening ReDoS"
type: concepto
tags: [coelsa-intelligent, seguridad, redos, regex, owasp]
aliases: [ReDoS protection, Bounded quantifiers, Regex hardening]
description: "Usar cuando necesitás entender qué expresiones regulares fueron remediadas contra ReDoS en COELSA.Intelligent o cuando agregás una nueva regex al código."
estado: vigente
---

# Hardening ReDoS

## Qué es

**ReDoS** (Regular Expression Denial of Service) es una vulnerabilidad donde una regex maliciosa o un input especialmente crafteado hace que el motor de regex tarde tiempo exponencial en evaluar. COELSA.Intelligent aplicó **bounded quantifiers** a 11 expresiones regulares que no tenían límites de longitud.

## El fix: bounded quantifiers

```python
# ANTES (vulnerable):
re.compile(r'[a-z]+')          # Sin límite
re.compile(r'\s*')             # Sin límite
re.compile(r'.+?')             # Sin límite

# DESPUÉS (con bounds):
re.compile(r'[a-z]{1,50}')     # Máximo 50 caracteres
re.compile(r'[ \t]{0,10}')     # Máximo 10 espacios
re.compile(r'.{1,500}?')       # Máximo 500 caracteres
```

La regla es: **ningún quantifier sin límite superior** en código que procesa input de usuario.

## Archivos afectados

- `backend/server/utils/middleware.py`
- `backend/server/utils/misc.py`
- `backend/server/utils/plugin.py`
- Archivos TypeScript del frontend (varios)

**Total**: 11 expresiones regulares en backend (Python) y frontend (TypeScript).

## Cuándo verificar

Cada vez que se agrega una nueva regex que procesa input de usuario, verificar:
1. ¿Tiene cuantificadores sin límite (`+`, `*`, `{n,}`)?
2. ¿El input puede ser controlado por un usuario no confiable?
3. Si ambas respuestas son sí → agregar bounds explícitos

## Relacionado

- [[Protección SSRF]] — Otra remediación OWASP del mismo ciclo de hardening
- [[Path Traversal]] — Otra remediación del mismo ciclo
- [[MOC - Seguridad]] — Índice del cluster de seguridad
