---
title: "PyTorch CPU-only"
type: decision
tags: [coelsa-intelligent, modelos-ia, pytorch, docker, cpu]
aliases: [CPU-only PyTorch, PyTorch sin CUDA, Torch CPU]
description: "Usar cuando necesitás entender por qué la imagen Docker de COELSA.Intelligent usa PyTorch CPU-only y qué implica para el tamaño de imagen y el rendimiento de embeddings."
estado: vigente
---

# PyTorch CPU-only

## Qué es

El [[Dockerfile]] de COELSA.Intelligent instala **PyTorch en su variante CPU-only** en lugar de la variante con soporte CUDA (GPU):

```dockerfile
RUN pip3 install torch==2.5.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu
```

## Por qué CPU-only

| Variante | Tamaño | Requisito |
|----------|--------|-----------|
| CUDA | ~2GB | GPU NVIDIA en el nodo |
| CPU-only | ~200MB | Solo CPU |

Los contenedores en [[OpenShift]] de COELSA **no tienen acceso a GPU**. La variante CUDA ocuparía ~2GB de imagen innecesariamente. La variante CPU-only es 10x más liviana y suficiente para las necesidades de embeddings del sistema.

## `torchvision` y `torchaudio`

Estas bibliotecas auxiliares fueron removidas del Dockerfile en v1.3.0 (ver CHANGELOG). No hay imports de `torchvision` ni `torchaudio` verificados en el repositorio, por lo que su presencia solo aumentaba el tamaño de imagen sin aportar funcionalidad.

## Impacto en rendimiento de embeddings

El procesamiento de embeddings con CPU es más lento que con GPU. Para el volumen de documentos esperado en COELSA.Intelligent, el impacto es aceptable. Si el tiempo de procesamiento se convierte en un problema, sería necesario:
1. Migrar a nodos con GPU en OpenShift
2. Cambiar a la variante CUDA de PyTorch
3. Activar `USE_CUDA_DOCKER=true` en las variables de entorno

## Relacionado

- [[Dockerfile]] — El archivo donde se instala PyTorch CPU-only
- [[OpenShift]] — El entorno sin GPU donde corre la imagen
- [[Módulo de retrieval]] — El módulo que usa PyTorch para los embeddings
- [[MOC - Decisiones]] — D-06 en el índice de decisiones
