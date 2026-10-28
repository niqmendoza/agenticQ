---
title: "Path Traversal"
type: concepto
tags: [coelsa-intelligent, seguridad, path-traversal, owasp, archivos]
aliases: [Path traversal protection, Directory traversal, Sanitización de paths]
description: "Usar cuando agregás un endpoint que opera sobre rutas de archivos o nombres de archivo provistos por el usuario — para asegurarte de sanitizar el input."
estado: vigente
---

# Path Traversal

## Qué es

**Path Traversal** (también llamado Directory Traversal) es una vulnerabilidad donde un atacante usa secuencias como `../../../etc/passwd` en nombres de archivo o paths para acceder a archivos fuera del directorio esperado.

COELSA.Intelligent aplicó sanitización de paths de entrada en **8 endpoints**.

## El fix en StorageProvider

```python
# backend/server/storage/provider.py — LocalStorageProvider.upload_file()
# Security: Path Injection Prevention
# 'filename' puede contener '../../../etc/passwd'

# Extraer solo el nombre base (sin directorios)
safe_filename = os.path.basename(filename)

# Resolver la ruta final y verificar que esté dentro de UPLOAD_DIR
file_path = os.path.realpath(os.path.join(UPLOAD_DIR, safe_filename))
if not file_path.startswith(os.path.realpath(UPLOAD_DIR)):
    raise ValueError("Path traversal detectado")
```

## Patrón de sanitización

1. **`os.path.basename()`**: elimina cualquier componente de directorio del nombre
2. **`os.path.realpath()`**: resuelve symlinks y `..`
3. **Verificar prefijo**: confirmar que la ruta final esté dentro del directorio permitido

Este patrón debe aplicarse en **cualquier endpoint nuevo** que:
- Acepte un nombre de archivo del usuario
- Use ese nombre para operar sobre el sistema de archivos

## Relacionado

- [[Hardening ReDoS]] — Otra remediación OWASP del mismo ciclo de hardening
- [[Protección SSRF]] — Otra remediación del mismo ciclo
- [[Flujo de subida de archivos]] — El flujo donde aplica esta sanitización
- [[MOC - Seguridad]] — Índice del cluster de seguridad
