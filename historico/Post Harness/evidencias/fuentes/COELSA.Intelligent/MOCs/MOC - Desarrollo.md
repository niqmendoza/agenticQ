---
title: "MOC — Desarrollo"
type: moc
tags: [coelsa-intelligent, desarrollo, patrones, migraciones, moc]
aliases: [MOC Desarrollo, Dev COELSA, Patrones COELSA]
description: "Usar cuando estás desarrollando en COELSA.Intelligent: patrones obligatorios del frontend, cómo agregar rutas REST, migraciones de BD, logging o ejecución local."
estado: vigente
---

# MOC — Desarrollo

Este cluster agrupa las guías prácticas para trabajar en el código de COELSA.Intelligent. Los [[Patrones frontend críticos]] son invariantes que resuelven bugs concretos y no deben revertirse sin entender su implicancia.

## Notas de este cluster

- [[Patrones frontend críticos]] — Las 4 guardas de código obligatorias en Chat.svelte y componentes relacionados
- [[Migraciones Alembic]] — Flujo de migraciones de base de datos; comandos y cuándo ejecutarlas
- [[Agregar router REST]] — Cómo extender la API de FastAPI con un nuevo router
- [[Agregar proveedor de almacenamiento]] — Cómo implementar la interfaz `StorageProvider` para un nuevo backend
- [[Loguru y logging]] — Configuración de logs con loguru; variable `LOG_LEVEL`; niveles por módulo
- [[Ejecución local]] — Comandos para correr frontend y backend en modo desarrollo

## MOCs vecinos

- [[MOC - Arquitectura]] — Las decisiones de diseño que estos patrones materializan
- [[MOC - CI-CD y Despliegue]] — Diferencias entre dev local y el proceso de CI/CD
- [[MOC - Diseño y Frontend]] — El sistema de diseño que el frontend implementa
- [[MOC - Almacenamiento]] — La interfaz StorageProvider que se extiende al agregar providers
