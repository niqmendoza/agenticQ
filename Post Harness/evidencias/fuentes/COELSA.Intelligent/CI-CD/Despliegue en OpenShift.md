---
title: "Despliegue en OpenShift"
type: referencia
tags: [coelsa-intelligent, cicd, openshift, despliegue, configmap]
aliases: [OpenShift deployment, Deploy COELSA, Despliegue COELSA]
description: "Usar cuando necesitás desplegar COELSA.Intelligent en OpenShift por primera vez o actualizar un entorno existente — pasos ordenados y requisitos previos."
estado: vigente
---

# Despliegue en OpenShift

## Pasos de despliegue

### Prerequisitos (primera vez)

1. **Crear el bucket MinIO**:
   ```bash
   python scripts/create_minio_bucket.py
   ```
   Requiere que las variables `S3_*` estén en `.env`.

2. **Aplicar ConfigMap** con variables de entorno:
   ```bash
   oc apply -f docs/OPENSHIFT-CONFIGMAP.yaml
   ```

3. **Aplicar configuración de Routes** (incluye CSP):
   ```bash
   oc apply -f docs/OPENSHIFT-ROUTE-CONFIG.yaml
   ```

### Deploy de una nueva versión

Ejecutar el pipeline correspondiente:
- **DEV**: `azure-pipeline-DEV.yml`
- **VALIDACION**: `azure-pipeline-VALIDACION.yml`
- **PRODUCCIÓN**: `azure-pipeline-PROD.yml`

### Migraciones de base de datos

```bash
cd backend
alembic upgrade head
```

El servidor aplica migraciones automáticamente al arrancar. Si hay migraciones pendientes críticas, ejecutarlas manualmente antes del deploy.

## Configuración crítica del Route

### Timeout de HAProxy

El timeout de HAProxy en el Route **debe ser mayor a 300 segundos**. El procesamiento de archivos con RAG (embedding + inserción en Milvus) puede superar 5 minutos en documentos grandes.

```yaml
# En la anotación del Route de OpenShift
haproxy.router.openshift.io/timeout: 600s
```

### CSP para SharePoint

Si [[SharePoint OneDrive integración]] está activo, incluir en la CSP:
```
connect-src: login.microsoftonline.com graph.microsoft.com
```

## Relacionado

- [[Pipelines Azure DevOps]] — Los pipelines que automatizan el despliegue
- [[Dockerfile]] — La imagen que se despliega
- [[CSP con nonces]] — La CSP que va en el Route
- [[MinIO S3]] — El bucket que debe crearse antes del primer deploy
- [[MOC - CI-CD y Despliegue]] — Índice del cluster de CI/CD
