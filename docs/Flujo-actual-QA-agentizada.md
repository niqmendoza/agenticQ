# Proceso actual de QA agentizada

Estado documentado al 2 de noviembre de 2026. Turquesa: implementado y probado en el piloto. Rosa: revisión humana pendiente. Amarillo y flechas punteadas: conexiones futuras o tareas de apoyo.

```mermaid
flowchart TB
    subgraph PREP["Preparación local · implementada"]
        DOC["Segundo cerebro<br/>80 documentos"] --> LOAD["setup_api.py<br/>Configura y carga documentos"]
        LOAD --> RAG["RAGFlow en Docker<br/>143 fragmentos indexados"]
        MAN["manage.py<br/>Arranca, detiene y consulta Docker"] --> RAG
        CHECK["check_api.py<br/>Diagnóstico de carga y consultas"] -. "consulta" .-> RAG
    end

    subgraph AUTO["Flujo implementado · se ejecuta por scripts"]
        ASK["Pregunta sobre una funcionalidad"] --> RET["retrieve.py<br/>Coordina la recuperación"]
        RET --> API["ragflow_client.py<br/>Consulta la API del dataset"]
        API <-->|"solicitud y fragmentos"| RAG
        API --> PACK["context_packet.py<br/>Limita tamaño, conserva fuentes<br/>y evita repeticiones"]
        PACK --> CTX["context.json<br/>Contexto compacto qa-context/1"]
        CTX --> GEN["draft_cases.py<br/>Verifica con verify_context.py<br/>y arma catálogo de reglas"]
        TASK["task.json<br/>Consigna y máximo de casos"] --> GEN
        GEN -->|"Hay fragmentos"| SELECT["Qwen 4B en Ollama · llamada 1<br/>Selecciona reglas del catálogo"]
        GEN -->|"Sin fragmentos"| DOUBT["Preguntas abiertas<br/>Sin generar casos para esa consigna"]
        SELECT --> GATE{"¿Encuentra reglas suficientes<br/>sin conflicto entre fuentes?"}
        GATE -->|"No, según el modelo"| DOUBT
        GATE -->|"Sí, según el modelo"| STEPS["Qwen 4B en Ollama · llamada 2<br/>Propone pasos funcionales"]
        STEPS --> BUILD["draft_cases.py + verify_result<br/>Copia la regla del esperado<br/>y resuelve/verifica referencias"]
        BUILD --> OUTPUT["drafts.json + PARA-REVISION-QA.md<br/>5 borradores en el último ensayo"]
        BUILD -->|"Salida inválida"| FAIL["Error explícito<br/>Sin entrega utilizable"]
    end

    subgraph HUMAN["Revisión del equipo · pendiente"]
        OUTPUT --> QA["QA revisa y ajusta<br/>Reglas, pasos, esperados y cobertura"]
        DOUBT --> QA
        QA -. "Aclara la consigna o las fuentes<br/>y vuelve a ejecutar" .-> TASK
        QA -. "Comparte la propuesta" .-> DEV["Desarrollo informado<br/>Sin aprobación obligatoria de casos"]
    end

    subgraph NEXT["Integraciones pendientes · todavía sin conectar"]
        INV["Azure Test Plans<br/>Consultar casos existentes"] -. "Comparar y evitar duplicados" .-> QA
        QA -. "Cuando los casos estén listos" .-> AZ["Azure Test Plans<br/>Crear o actualizar casos"]
        AZ -.-> CODE["Código de pruebas<br/>y revisión técnica"]
        CODE -.-> RUN["Playwright y pipeline<br/>Ejecución automática"]
        RUN -.-> TRIAGE["QA interpreta resultados"]
        TRIAGE -. "Defecto confirmado" .-> BUG["Markdown de defectos<br/>para desarrollo"]
        N8N["n8n<br/>Orquestación futura"] -. "Podrá coordinar los scripts" .-> RET
    end

    classDef built fill:#00363B,stroke:#00A0AD,color:#E8F8F7
    classDef human fill:#340C25,stroke:#E11F8F,color:#FFE8F5
    classDef future fill:#292515,stroke:#D8BF70,color:#FFF1C2
    classDef warning fill:#291B13,stroke:#D8BF70,color:#FFF1C2
    class DOC,LOAD,RAG,MAN,CHECK,ASK,RET,API,PACK,CTX,GEN,TASK,SELECT,GATE,STEPS,BUILD,OUTPUT built
    class QA,DEV human
    class INV,AZ,CODE,RUN,TRIAGE,BUG,N8N future
    class DOUBT,FAIL warning
    style PREP fill:#001F23,stroke:#004F56,color:#E8F8F7
    style AUTO fill:#001F23,stroke:#00848F,color:#E8F8F7
    style HUMAN fill:#170B13,stroke:#E11F8F,color:#FFE8F5
    style NEXT fill:#17160E,stroke:#D8BF70,color:#FFF1C2
```

El Markdown que ya generamos contiene **borradores de casos para QA**. El Markdown de defectos confirmados es una entrega futura distinta. Las verificaciones de los scripts comprueban integridad y formato; no garantizan corrección semántica ni cobertura. La última suite registrada pasó 57 tests.

Scripts de apoyo que ya existen:

- Recuperación y calibración: `ragflow-local/evaluate_retrieval.py`, `calibrate_retrieval.py`, `evaluate_adapter.py`.
- Comparación de modelos y ensayo integrado: `ollama-pilot/evaluate_small_models.py`, `evaluate_grounded_drafts.py`.
- Referencia local: `scripts/brain.py` y `document_utils.py` consultan archivos locales; se conservaron como ruta medida de comparación y no se usan como sustituto directo del contexto remoto en este diagrama.
- Métricas y reportes: `scripts/collect_metrics.py`, `extract_usage.py`, `extract_transcript.py`, `build_report.py`, `build_explanation.py` y `ragflow-local/build_test_report.py`.
