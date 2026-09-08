┌──────────────────────────────────────────────────────────────────────┐
│                         MANUFACTURING REASONING FLOW                 │
│                    Evidence‑Bound • Read‑Only • GDS‑Free             │
├──────────────────────────────────────────────────────────────────────┤
│ 1. Versioned Ontology (v1.1)                                         │
│    • 12 Classes (WorkOrder, BOM, Part, Supplier, etc.)               │
│    • 14 Object Properties (scheduledAt, definesRequirement, etc.)    │
│    • 10 Datatype Properties (quantity, plannedStart, status, etc.)   │
│    • Example: “saltmfg:BillOfMaterials a owl:Class …”                │
│                                                                      │
│ 2. Executable Layer (Ontop + Synthetic Mapping)                      │
│    • Metadata‑only OBDA (no SAP/CDS/transactions)                    │
│    • Deterministic SPARQL execution                                  │
│    • Example: “SELECT ?resource WHERE { ?resource a saltmfg:KnowledgeBase . }” │
│                                                                      │
│ 3. Context‑Graph Package (GDS‑Free)                                  │
│    • domain.yaml: entities + relationships                           │
│    • manufacturing-tools.yaml: 6 read‑only tools                     │
│    • strategies.yaml: bounded Cypher reasoning (max 4 hops)          │
│    • No gds.* calls anywhere                                         │
│                                                                      │
│ 4. Agent Runtime (Strands)                                           │
│    • Loads + validates all three catalogs at startup                 │
│    • Tools execute parameterized Cypher with $ontology_id=v1.1       │
│    • Evidence surfaced via SSE tool events                           │
│                                                                      │
│ 5. Reasoning Strategies (Cypher‑Only)                                │
│    • BOM Requirements: WorkOrder → BOM → MaterialRequirement → Part │
│    • Schedule Contention: ScheduleSlot overlaps for a WorkCenter     │
│    • Production Lineage: PRECEDES_EVENT + consumes/produces links    │
│    • Supplier Coverage: SupplyCommitment → Supplier → Part           │
│                                                                      │
│ 6. Product Moment                                                     │
│    • Agent answers operational questions with explicit evidence       │
│    • No inferred edges, no writes, no GDS                            │
│    • Safe, explainable, operationally relevant reasoning             │
└──────────────────────────────────────────────────────────────────────┘
