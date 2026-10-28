---
title: "MOC — Decisiones"
type: moc
tags: [coelsa-intelligent, decisiones, adr, moc]
aliases: [MOC Decisiones, ADR COELSA, Decisiones de Arquitectura]
description: "Usar cuando necesitás el índice de todas las decisiones de diseño y arquitectura del fork — para entender el por qué de cada elección sin leer todos los docs."
estado: vigente
---

# MOC — Decisiones

Índice de todas las decisiones de arquitectura, diseño y producto tomadas en COELSA.Intelligent. Cada decisión tiene su nota atómica con contexto, justificación y consecuencias.

## Decisiones de infraestructura y backend

| ID | Decisión | Nota |
|----|----------|------|
| D-01 | Fork de Open WebUI como base | [[Fork de Open WebUI]] |
| D-02 | PostgreSQL en lugar de SQLite | [[PostgreSQL como base de datos]] |
| D-03 | Redis como backend de WebSockets | [[Redis para WebSockets]] |
| D-04 | MinIO/S3 con flujo híbrido | [[Sistema híbrido de almacenamiento]] |
| D-05 | Milvus multi-tenancy (5 colecciones) | [[Milvus multi-tenancy]] |
| D-06 | CPU-only PyTorch en Docker | [[PyTorch CPU-only]] |
| D-07 | bcrypt nativo en lugar de passlib | [[bcrypt para contraseñas]] |

## Decisiones de routing y modelos IA

| ID | Decisión | Nota |
|----|----------|------|
| D-08 | Validación de urlIdx para routing LiteLLM | [[Validación de urlIdx]] |
| D-09 | JSON prompt para MCP non-native | [[MCP y tool calling]] |
| D-10 | Cadena SearXNG via Context Forge | [[Cadena SearXNG Context Forge]] |

## Decisiones de autenticación y acceso

| ID | Decisión | Nota |
|----|----------|------|
| D-11 | Azure AD como único medio de login | [[Azure AD login exclusivo]] |
| D-12 | SSR deshabilitado (SPA pura) | [[SPA con SSR deshabilitado]] |

## Decisiones de seguridad

| ID | Decisión | Nota |
|----|----------|------|
| D-13 | Nonces CSP en OpenShift | [[CSP con nonces]] |
| D-14 | ReDoS: bounded quantifiers en 11 regexes | [[Hardening ReDoS]] |
| D-15 | SSRF: validación de URLs outbound | [[Protección SSRF]] |
| D-16 | Path Traversal: sanitización de paths | [[Path Traversal]] |
| D-17 | Riesgos aceptados documentados | [[Riesgos de seguridad aceptados]] |

## Decisiones de producto y UX

| ID | Decisión | Nota |
|----|----------|------|
| D-18 | es-AR como idioma principal | [[Idioma por defecto es-AR]] |
| D-19 | Sistema de errores centralizado | [[Sistema de errores centralizado]] |
| D-20 | AbortController en loadChat (fix requests duplicados) | [[Patrones frontend críticos]] |

## MOCs vecinos

- [[MOC - Arquitectura]] — Contexto técnico de las decisiones de diseño estructural
- [[MOC - Seguridad]] — Detalle de las decisiones de hardening
- [[MOC - Modelos IA y Routing]] — Contexto de las decisiones de routing e IA
