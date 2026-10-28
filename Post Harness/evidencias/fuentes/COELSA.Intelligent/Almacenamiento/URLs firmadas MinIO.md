---
title: "URLs firmadas MinIO"
type: concepto
tags: [coelsa-intelligent, almacenamiento, minio, presigned-url, seguridad]
aliases: [Presigned URLs, URLs firmadas S3, Signed URLs MinIO]
description: "Usar cuando necesitás entender cómo los clientes acceden a archivos en MinIO de forma segura y temporaria sin exponer credenciales."
estado: vigente
---

# URLs firmadas MinIO

## Qué es

Las **URLs firmadas** (presigned URLs) son URLs de acceso temporal a objetos en [[MinIO S3]] que no requieren que el cliente tenga credenciales del bucket. El servidor firma la URL con las credenciales S3 y establece un tiempo de expiración.

## Cómo funciona

```python
# Pseudocódigo de generación (StorageProvider.get_presigned_url)
url = s3_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': S3_BUCKET_NAME, 'Key': file_path},
    ExpiresIn=3600  # 1 hora por defecto
)
```

La URL resultante incluye la firma criptográfica y la fecha de expiración en los query params. Solo es válida hasta esa fecha y solo para el objeto específico.

## Por qué URLs firmadas

- **Seguridad**: el cliente nunca recibe credenciales del bucket; solo puede acceder al archivo específico por el tiempo configurado
- **Control de acceso**: si el [[Control de acceso a recursos|access_control]] del archivo cambia, las URLs viejas siguen siendo válidas hasta su expiración pero no se generan nuevas
- **Descarga directa**: el cliente descarga directo de MinIO sin pasar por el backend, reduciendo la carga del servidor

## Configuración de expiración

La expiración por defecto es **3600 segundos (1 hora)**. El parámetro `ExpiresIn` es configurable en la llamada a `get_presigned_url()`.

## Timeouts boto3 (Windows)

Para evitar timeouts en entornos Windows con latencia de red:
- Connect timeout: 30s
- Read timeout: 120s
- 10 reintentos con backoff exponencial
- TCP keepalive habilitado

## Relacionado

- [[MinIO S3]] — El proveedor que genera estas URLs
- [[Flujo de subida de archivos]] — Cuándo se genera la URL firmada en el ciclo de vida del archivo
- [[Sistema híbrido de almacenamiento]] — El contexto general del sistema de almacenamiento
- [[MOC - Almacenamiento]] — Índice del cluster de almacenamiento
