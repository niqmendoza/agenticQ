---
title: "Chats de referencia"
type: concepto
tags: [coelsa-intelligent, rag, chat, referencia, contexto]
aliases: [Reference chats, Chats adjuntos, Chat como contexto]
description: "Usar cuando necesitás entender cómo un usuario puede adjuntar una conversación previa como contexto en un nuevo mensaje en COELSA.Intelligent."
estado: vigente
---

# Chats de referencia

## Qué es

Los **chats de referencia** permiten a los usuarios adjuntar conversaciones previas como contexto extendido al enviar un nuevo mensaje. El chat adjunto se recupera, se formatea y se inyecta en el prompt del modelo junto con el mensaje actual.

## Cómo se adjunta en el cliente

El chat referenciado viaja como un elemento de tipo `"chat"` dentro del array `files` del payload del socket:

```json
{
  "files": [
    {
      "type": "chat",
      "id": "chat-uuid-del-chat-referenciado"
    }
  ],
  "content": "Basándote en la conversación adjunta..."
}
```

## Procesamiento en el backend

En `backend/server/retrieval/utils.py`:
1. Se detecta el elemento `type == "chat"` en `files`
2. Se recupera el chat por ID desde la BD (tabla `chat`)
3. El historial del chat se formatea como bloque Markdown:
   ```
   ## Conversación de referencia
   **Usuario**: ...
   **Asistente**: ...
   ```
4. El bloque se inyecta al contexto del prompt antes del mensaje del usuario

## Visibilidad en la UI

La opción de adjuntar chats de referencia aparece en el `InputMenu` y depende del permiso `chat.file_upload` (no del historial local del sidebar). El componente `InputMenu/Chats.svelte` hace su propia llamada a `getChatList` al abrirse, independientemente del estado del sidebar.

## Relacionado

- [[Módulo de retrieval]] — El módulo donde se procesa el chat referenciado
- [[Grupos y permisos]] — El permiso `chat.file_upload` que controla la visibilidad
- [[MOC - RAG y Búsqueda Vectorial]] — Índice del cluster de RAG
