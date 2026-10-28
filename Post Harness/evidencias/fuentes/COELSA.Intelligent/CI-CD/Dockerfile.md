---
title: "Dockerfile"
type: referencia
tags: [coelsa-intelligent, cicd, docker, dockerfile, imagen]
aliases: [Docker image COELSA, Imagen Docker COELSA]
description: "Usar cuando necesitás entender cómo se construye la imagen Docker de COELSA.Intelligent, sus workarounds de SSL corporativo y por qué no incluye CUDA ni Pyodide."
estado: vigente
---

# Dockerfile

## Qué es

El `Dockerfile` en la raíz del proyecto construye la imagen de producción de COELSA.Intelligent. Combina el build del frontend estático con el backend Python en una sola imagen.

## Características clave

### PyTorch CPU-only

```dockerfile
RUN pip3 install torch==2.5.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu
```

La variante CUDA (~2GB) no se usa porque [[OpenShift]] no tiene GPUs disponibles. Ver [[PyTorch CPU-only]].

### Sin Pyodide

El build usa `npm run build:docker` (no `npm run build`), que **no descarga Pyodide**. Ver [[Build frontend]].

### SSL corporativo (riesgo aceptado)

```dockerfile
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
ENV npm_config_strict_ssl=false
ENV PIP_TRUSTED_HOST="download.pytorch.org pypi.org files.pythonhosted.org"
```

Estas variables deshabilitan la verificación SSL en `npm` y `pip` durante el build. Necesario en el entorno de CI/CD con proxy corporativo que intercepta HTTPS. Ver [[SSL corporativo en build]] y [[Riesgos de seguridad aceptados]].

### CHANGELOG en la ruta correcta

```dockerfile
COPY CHANGELOG.md /app/CHANGELOG.md
```

Corrección del v1.3.0: anteriormente se copiaba a `/app/backend/CHANGELOG.md` pero la app lo buscaba en `/app/CHANGELOG.md`.

## Relacionado

- [[PyTorch CPU-only]] — Por qué CPU-only y su impacto en tamaño de imagen
- [[Build frontend]] — El comando `build:docker` que usa el Dockerfile
- [[SSL corporativo en build]] — El riesgo del SSL deshabilitado
- [[Pipelines Azure DevOps]] — Los pipelines que construyen esta imagen
- [[MOC - CI-CD y Despliegue]] — Índice del cluster de CI/CD
