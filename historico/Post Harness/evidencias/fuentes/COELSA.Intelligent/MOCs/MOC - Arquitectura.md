---
title: "MOC — Arquitectura"
type: moc
tags: [coelsa-intelligent, arquitectura, moc]
aliases: [Arquitectura COELSA, MOC Arquitectura]
description: "Usar cuando necesitás entender las decisiones de diseño estructural de COELSA.Intelligent — qué componentes existen y por qué se tomó cada decisión."
estado: vigente
---

# MOC — Arquitectura

COELSA.Intelligent es un [[Fork de Open WebUI]] adaptado para infraestructura corporativa. Las decisiones de este cluster definen **qué** es el sistema y **por qué** se alejó del upstream.

## Notas de este cluster

- [[Fork de Open WebUI]] — Qué es el fork, qué cambia y por qué no se sigue el upstream directamente
- [[SPA con SSR deshabilitado]] — Por qué `ssr = false` y sus implicaciones de seguridad y compatibilidad
- [[PostgreSQL como base de datos]] — Migración de SQLite a PostgreSQL para escalar en producción
- [[Redis para WebSockets]] — Backend de canal que permite múltiples workers sin pérdida de eventos
- [[Sistema de errores centralizado]] — Jerarquía estándar de 10 tipos de excepción con respuestas JSON consistentes
- [[Headers de usuario COELSA]] — Convención de encabezados HTTP `X-COELSA.Intelligent-User-*`
- [[Idioma por defecto es-AR]] — Castellano Rioplatense como único español; idiomas eliminados del fork

## MOCs vecinos

- [[MOC - Stack]] — Las tecnologías concretas que implementan esta arquitectura
- [[MOC - Decisiones]] — Índice completo de todas las decisiones con sus justificaciones
- [[MOC - Seguridad]] — Hardening y remediaciones aplicadas sobre la arquitectura base
- [[MOC - Desarrollo]] — Patrones de código que materializan las decisiones de arquitectura
