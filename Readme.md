graph TD
    direction TB

    A[User / Messaging App<br>e.g. WhatsApp, Slack, X, Terminal] -->|sends message / command| B[OpenClaw Runtime<br>Agent Execution Loop<br>• Tool invocation<br>• LLM reasoning & calls<br>• State transitions]

    B -->|memory operations<br>write / read / update / delete| C[Pydantic-validated<br>Memory Entries<br>• Strict schemas<br>• Timestamps & UUID<br>• Source provenance<br>• Auto SHA-256 content hash<br>• Versioning & prev-link]

    C <-->|every memory op emits structured event| D[Promtail → Loki<br>Immutable Audit Logs<br>• Append-only structured JSON<br>• Full provenance & timestamps<br>• Queryable by agent/session/user/tool<br>• Tamper-evident history]

    subgraph "Persistent & Auditable Storage Layer"
        E[Local / On-prem Storage<br>• Append-only JSONL primary<br>• SQLite metadata index<br>• Optional encryption-at-rest<br>• Future: S3-compatible / distributed]
    end

    C --> E
    D --> E

    E -->|provenance & audit queries| F[Audit & Observability Interface<br>• CLI query tool<br>• FastAPI / REST endpoint<br>• Grafana mini-dashboard<br>• Trace replay & heatmaps<br>• Access pattern visualization]

    F -->|returns full history, diffs, access logs| B
    F -->|visual inspection & debugging| User

    NIST[NIST SP 800-171 Inspiration<br>• Audit & accountability (AU family)<br>• Media protection & integrity (MP family)<br>• Access control & provenance (AC family)<br>• Configuration management & logging<br>• Battle-tested controls for high-stakes systems]:::callout

    NIST -.->|shapes| C
    NIST -.->|shapes| D
    NIST -.->|shapes| F

    %% Styling for visual impact
    classDef callout fill:#ffeb3b,stroke:#f57f17,stroke-width:2px,color:#000,font-weight:bold
    style A fill:#f8bbd0,stroke:#ad1457
    style B fill:#bbdefb,stroke:#1565c0,stroke-width:2.5px
    style C fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style D fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    style E fill:#e0f7fa,stroke:#006064
    style F fill:#fff9c4,stroke:#f9a825,stroke-width:2px
