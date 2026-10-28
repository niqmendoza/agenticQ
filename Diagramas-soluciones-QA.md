# Diagramas editables del reporte de soluciones QA

Actualización: 5 de octubre de 2026. Fuente del [reporte HTML](Reporte-soluciones-QA.html). El HTML incluye SVG renderizados: no necesita Mermaid ni conexión al abrir. Para editar, cambiar estos bloques y regenerar las figuras.

Las herramientas se revisaron por código y documentación; no se instalaron sus stacks. Los controles humanos y conexiones con la compañía forman parte del diseño propuesto. Las líneas punteadas marcan puentes por construir. El diagrama conjunto es una propuesta completa, no una instalación existente.

## 1. Hercules

El ejecutor usa IA durante el escenario. Los reportes son una salida documentada; su revisión y asociación con Azure se integran en el proceso propuesto.

```mermaid
flowchart TD
    A["Caso aprobado<br/>Escenario + datos"] --> B["IA planifica<br/>Acciones del escenario"]
    B --> C["Herramientas<br/>API / navegador"]
    C --> D["Aserciones<br/>Reportes + evidencia"]
    D --> E["QA revisa<br/>Valida el hallazgo"]
    E -. "Integración propuesta" .-> F["Azure + Markdown"]
    class A existing
    class B model
    class C,D tool
    class E human
    class F proposed

    classDef existing fill:#e4f4ef,stroke:#5eac96,color:#164f40,stroke-width:2px
    classDef model fill:#f0e8fb,stroke:#9d78c9,color:#523574,stroke-width:2px
    classDef tool fill:#e9f1fe,stroke:#769aca,color:#254769,stroke-width:2px
    classDef human fill:#fff3d9,stroke:#c6a051,color:#664c1e,stroke-width:2px
    classDef proposed fill:#fff0e8,stroke:#c69073,color:#7a4b32,stroke-dasharray:5 4,stroke-width:2px
```

## 2. Schemathesis

El contrato permite generar variaciones y secuencias; la regla funcional específica necesita un check codificado. El runner base no usa LLM.

```mermaid
flowchart TD
    A["Contrato API<br/>OpenAPI / GraphQL"] --> C["Schemathesis<br/>Genera solicitudes"]
    B["Reglas validadas<br/>Checks en código"] --> D["Ejecutor sin IA<br/>Comprueba respuestas"]
    C --> D
    D --> E["Reportes<br/>Fallos reproducibles"]
    E --> F["QA clasifica"]
    F -. "Asociación por conectar" .-> G["Azure + evidencia"]
    class A,B existing
    class C,D,E tool
    class F human
    class G proposed

    classDef existing fill:#e4f4ef,stroke:#5eac96,color:#164f40,stroke-width:2px
    classDef model fill:#f0e8fb,stroke:#9d78c9,color:#523574,stroke-width:2px
    classDef tool fill:#e9f1fe,stroke:#769aca,color:#254769,stroke-width:2px
    classDef human fill:#fff3d9,stroke:#c6a051,color:#664c1e,stroke-width:2px
    classDef proposed fill:#fff0e8,stroke:#c69073,color:#7a4b32,stroke-dasharray:5 4,stroke-width:2px
```

## 3. TestForge

Genera propuestas de casos; no se verificó un runner de pruebas de la aplicación. En el circuito conjunto se usa un puente propuesto, sin habilitar un segundo publicador.

```mermaid
flowchart TD
    A["Requisito validado<br/>Documento / Azure"] --> B["IA analiza y diseña"]
    B --> C["Propuestas JSON<br/>Lote adicional"]
    C --> D["QA revisa<br/>Compara con legacy"]
    D -. "Puente por construir" .-> E["iTestFlow<br/>Única vía de publicación"]
    D --> F["Publicación Azure<br/>PAT / navegador"]
    G["Licencia por aclarar<br/>Antes de adopción"] -.-> B
    class A existing
    class B model
    class C tool
    class D human
    class E,G proposed
    class F tool

    classDef existing fill:#e4f4ef,stroke:#5eac96,color:#164f40,stroke-width:2px
    classDef model fill:#f0e8fb,stroke:#9d78c9,color:#523574,stroke-width:2px
    classDef tool fill:#e9f1fe,stroke:#769aca,color:#254769,stroke-width:2px
    classDef human fill:#fff3d9,stroke:#c6a051,color:#664c1e,stroke-width:2px
    classDef proposed fill:#fff0e8,stroke:#c69073,color:#7a4b32,stroke-dasharray:5 4,stroke-width:2px
```

La publicación propia de TestForge está documentada, pero es una alternativa al circuito con iTestFlow; no se habilitan ambos para los mismos casos. El código ejecutable y la ejecución de la aplicación se preparan aparte.

## 4. iTestFlow

Incluye revisión/publicación y código de ejecución UI/API/DB. Reconciliar IDs legacy, consultar RAGFlow y recibir resultados externos requiere diseño y verificación.

```mermaid
flowchart TD
    A["Fuentes + requisitos<br/>Documentos / Azure"] --> B["IA propone<br/>Casos + cobertura"]
    B --> C["QA edita y aprueba"]
    C --> D["Publicación Azure<br/>Casos + vínculos"]
    D --> E["Ejecución con agente<br/>UI / API / DB"]
    E --> F["QA revisa resultados"]
    F --> G["Publicar resultados<br/>En Azure"]
    H["Legacy + RAGFlow<br/>Puente por construir"] -.-> B
    class A existing
    class B,E model
    class C,F human
    class D,G tool
    class H proposed

    classDef existing fill:#e4f4ef,stroke:#5eac96,color:#164f40,stroke-width:2px
    classDef model fill:#f0e8fb,stroke:#9d78c9,color:#523574,stroke-width:2px
    classDef tool fill:#e9f1fe,stroke:#769aca,color:#254769,stroke-width:2px
    classDef human fill:#fff3d9,stroke:#c6a051,color:#664c1e,stroke-width:2px
    classDef proposed fill:#fff0e8,stroke:#c69073,color:#7a4b32,stroke-dasharray:5 4,stroke-width:2px
```

Crear casos no ejecuta automáticamente el código. La flecha hacia ejecución indica el recorrido que debe configurarse y probarse; no un disparo automático confirmado.

## 5. Git, RAGFlow y versiones

Git conserva revisiones; RAGFlow es el índice consultable existente. La sincronización, metadatos y filtros de la versión instalada siguen por verificar.

```mermaid
flowchart TD
    A["Código + notas<br/>Comportamiento observado"] --> B["Negocio valida<br/>Lo que debe pasar"]
    B --> C["Git<br/>Revisión aprobada"]
    C -. "Sincronización propuesta" .-> D["RAGFlow<br/>Índice + metadatos"]
    D --> E["Consulta con fuentes<br/>Versión + estado + commit"]
    E -. "Conectar generadores" .-> F["Propuestas de casos"]
    class A,C existing
    class B human
    class D,E tool
    class F proposed

    classDef existing fill:#e4f4ef,stroke:#5eac96,color:#164f40,stroke-width:2px
    classDef model fill:#f0e8fb,stroke:#9d78c9,color:#523574,stroke-width:2px
    classDef tool fill:#e9f1fe,stroke:#769aca,color:#254769,stroke-width:2px
    classDef human fill:#fff3d9,stroke:#c6a051,color:#664c1e,stroke-width:2px
    classDef proposed fill:#fff0e8,stroke:#c69073,color:#7a4b32,stroke-dasharray:5 4,stroke-width:2px
```

## 6. Las cuatro soluciones orquestadas

Diseño por construir. TestForge agrega un lote pequeño distinto, condicionado a aclarar licencia; iTestFlow concentra revisión y publicación. El piloto puede usar menos piezas. Mantener IDs requiere reconciliación explícita, no regeneración indiscriminada.

```mermaid
flowchart TD
    A["Git + reglas validadas"] -. "Sincronizar revisión" .-> B["RAGFlow"]
    B -. "Recuperar contexto" .-> C["iTestFlow<br/>Legacy + propuestas"]
    B -. "Lote adicional" .-> D["TestForge<br/>Licencia por aclarar"]
    D -. "Normalizar por puente" .-> C
    C --> E["QA + negocio<br/>Aprueban cambios"]
    E --> F["Azure Test Plans<br/>Única vía de publicación"]
    F -. "Preparar código aprobado" .-> G["Runner / pipeline"]
    G --> H["Schemathesis<br/>Contrato + checks"]
    G --> I["Hercules<br/>Escenario entre servicios"]
    H -. "Colector propuesto" .-> J["Resultados + evidencia"]
    I -. "Colector propuesto" .-> J
    J --> K["IA explica + QA valida"]
    K -->|Conforme| L["Registrar resultado<br/>Cerrar si corresponde"]
    K -->|Defecto confirmado| M["Azure + Markdown<br/>Para desarrollo"]
    M --> N["Dev + Copilot<br/>Corrigen"]
    N --> O["Reejecutar + regresión"]
    O --> G
    K -. "Falta una regla" .-> E
    class A,B,F existing
    class C,D,I model
    class E,K,N human
    class G,H,J,O,L tool
    class M proposed

    classDef existing fill:#e4f4ef,stroke:#5eac96,color:#164f40,stroke-width:2px
    classDef model fill:#f0e8fb,stroke:#9d78c9,color:#523574,stroke-width:2px
    classDef tool fill:#e9f1fe,stroke:#769aca,color:#254769,stroke-width:2px
    classDef human fill:#fff3d9,stroke:#c6a051,color:#664c1e,stroke-width:2px
    classDef proposed fill:#fff0e8,stroke:#c69073,color:#7a4b32,stroke-dasharray:5 4,stroke-width:2px
```

Un problema de test, entorno, datos o intermitencia se investiga y se reejecuta tras resolver su causa; no se entrega como defecto de producto confirmado. La clasificación conserva las hipótesis y evidencia anterior.
