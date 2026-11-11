---
title: "Agregar proveedor de almacenamiento"
type: referencia
tags: [coelsa-intelligent, desarrollo, backend, almacenamiento, storage-provider]
aliases: [Nuevo storage provider, StorageProvider interface, Agregar backend storage]
description: "Usar cuando necesitás implementar un nuevo proveedor de almacenamiento (ej: Azure Blob, GCS) para COELSA.Intelligent siguiendo la interfaz StorageProvider."
estado: vigente
---

# Agregar proveedor de almacenamiento

## Qué es

Guía para implementar un nuevo backend de almacenamiento en COELSA.Intelligent. El sistema usa una interfaz abstracta `StorageProvider` que permite agregar nuevos providers sin modificar el código de negocio.

## La interfaz abstracta

```python
# backend/server/storage/provider.py
class StorageProvider(ABC):
    
    @abstractmethod
    def get_file(self, file_path: str) -> str:
        """Retorna la ruta local o URL al archivo."""
        pass
    
    @abstractmethod
    def upload_file(self, file: BinaryIO, filename: str) -> Tuple[bytes, str]:
        """Sube el archivo y retorna (contenido, path)."""
        pass
    
    @abstractmethod
    def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        """Genera una URL firmada de acceso temporal."""
        pass
    
    @abstractmethod
    def get_storage_stats(self) -> dict:
        """Retorna estadísticas de uso del almacenamiento."""
        pass
    
    @abstractmethod
    def delete_all_files(self) -> None:
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        pass
```

## Pasos para agregar un nuevo provider

### 1. Crear la clase del provider

```python
# backend/server/storage/provider.py — agregar junto a las clases existentes
class MiNuevoProvider(StorageProvider):
    
    def get_file(self, file_path: str) -> str:
        # implementación
        ...
    
    def upload_file(self, file, filename):
        # implementación con sanitización de path (ver Path Traversal)
        ...
    
    # ... implementar todos los métodos abstractos
```

### 2. Registrar en la factory

En `provider.py`, agregar el nuevo provider a la selección por variable de entorno:

```python
STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "local")

if STORAGE_PROVIDER == "s3":
    Storage = S3StorageProvider(...)
elif STORAGE_PROVIDER == "mi-nuevo":
    Storage = MiNuevoProvider(...)
else:
    Storage = LocalStorageProvider()
```

## Notas de seguridad

Siempre incluir sanitización de path traversal en `upload_file`. Ver [[Path Traversal]].

## Relacionado

- [[Sistema híbrido de almacenamiento]] — El contexto donde opera el provider
- [[MinIO S3]] — El provider S3 como referencia de implementación
- [[Path Traversal]] — La sanitización de paths obligatoria en upload_file
- [[MOC - Desarrollo]] — Índice del cluster de desarrollo
