William, here is **Plan‑009 — Agent Memory Service**, fully consolidated, repo‑ready, and aligned with everything you’ve built so far (Context Graph v1.4, Ontology Pipeline, MFGM+MFGQ, SQLMesh, Cypher reasoning, and the neo4j‑agent-memory patterns shown in your diagrams).

This version is written as a **project plan** you can drop directly into your repo as:

```
plan-009-agent-memory-service.md
```

It assumes your repo originated from **neo4j-labs/create-context-graph**, but Plan‑009 is designed to **migrate you forward** into a full Agent Memory Service architecture.

---

# **Plan‑009 — Agent Memory Service**
**Version:** 1.0  
**Author:** PM Agent  
**Purpose:** Define the architecture, API, schemas, and implementation plan for a unified Agent Memory Service built on a Neo4j Context Graph.

---

# **0. Background & Migration Context**

Your current repo was constructed from:

- **neo4j-labs/create-context-graph**  
- Your **MFGM + MFGQ ontology**  
- Your **quality reasoning Cypher layer**  
- Your **Context Graph PM specifications (v1.0 → v1.4)**  
- Your **decision-trace and audit log formats**

Plan‑009 evaluates this foundation and defines the **next evolution**:  
a **full Agent Memory Service** that exposes STM, LTM, and RM through a clean API.

This service becomes the **memory backbone** for all agents in your manufacturing reasoning ecosystem.

---

# **1. Architecture Overview**

## **1.1 ASCII Architecture Diagram**

```
+-----------------------------------------------------------+
|                     Agent Clients                         |
|  PM Agent | Quality Agent | MFG Agent | MCP Agent         |
+---------------------------+--------------------------------+
                            |
                            v
+-----------------------------------------------------------+
|                  Agent Memory Service (Plan-009)          |
|  STM API     |     LTM API     |     RM API               |
+---------------------------+--------------------------------+
                            |
                            v
+-----------------------------------------------------------+
|                     Neo4j Context Graph                   |
|  Short-Term | Long-Term | Reasoning Memory                |
|  Messages   | Entities  | Traces, Steps, ToolCalls        |
+-----------------------------------------------------------+
```

---

# **2. Memory Model (STM / LTM / RM)**

This follows the model from your v1.4 spec and the Context Graph talk.

### **2.1 Short-Term Memory (STM)**  
Conversations, sessions, recent messages.

### **2.2 Long-Term Memory (LTM)**  
Ontology-backed entities and relationships:
- WorkOrder  
- Part  
- Supplier  
- Nonconformance  
- All relationships from `mfgm-mfgq.ttl`

### **2.3 Reasoning Memory (RM)**  
Decision traces, tool call audits, provenance chains.

---

# **3. Context Graph API (Service Endpoints)**

## **3.1 STM Endpoints**

```
POST   /stm/message
GET    /stm/messages
GET    /stm/session
DELETE /stm/session
```

## **3.2 LTM Endpoints**

```
POST   /ltm/entity
GET    /ltm/entities
GET    /ltm/entity-graph
POST   /ltm/preference
GET    /ltm/search-near
```

## **3.3 RM Endpoints**

```
POST   /rm/trace
POST   /rm/trace/step
POST   /rm/trace/toolcall
GET    /rm/trace
GET    /rm/traces/similar
```

These match the neo4j-agent-memory API patterns shown in your diagrams.

---

# **4. Neo4j Data Model**

## **4.1 STM Nodes**

```
(:Session {id})
(:Message {id, role, content, ts})
```

Relationships:
```
(Session)-[:FIRST_MESSAGE]->(Message)
(Message)-[:NEXT_MESSAGE]->(Message)
```

## **4.2 LTM Nodes**

```
(:WorkOrder)
(:Part)
(:Supplier)
(:Nonconformance)
```

Ontology-aligned relationships:
```
(Nonconformance)-[:ASSOCIATED_WITH_ORDER]->(WorkOrder)
(Nonconformance)-[:ASSOCIATED_WITH_SUPPLIER]->(Supplier)
(Nonconformance)-[:AFFECTED_PART]->(Part)
```

## **4.3 RM Nodes**

```
(:ReasoningTrace {id, agent_id, session_id, purpose})
(:ReasoningStep {id, order, description})
(:ToolCall {id, tool_name, parameters, result_summary})
```

Relationships:
```
(ReasoningTrace)-[:HAS_STEP]->(ReasoningStep)
(ReasoningStep)-[:USED_TOOL]->(ToolCall)
(ToolCall)-[:EVIDENCE]->(Entity)
```

---

# **5. Decision‑Trace Schema (Full)**

```yaml
Trace:
  id: string
  agent_id: string
  session_id: string
  purpose: string
  started_at: datetime
  completed_at: datetime
  steps: Step[]

Step:
  id: string
  trace_id: string
  order: int
  description: string
  tool_call: ToolCall | null
  evidence: EvidenceRef[]
  created_at: datetime

ToolCall:
  id: string
  trace_id: string
  tool_name: string
  parameters: map
  result_summary: string
  started_at: datetime
  completed_at: datetime

EvidenceRef:
  id: string
  type: string
  ontology_id: string
```

---

# **6. Reasoning Memory Audit Log Format**

Append-only, line-oriented:

```
2026-09-13T13:45:01Z TRACE_START trace-wo-778 agent=quality-analyst session=sess-123 purpose=work_order_quality_impact
2026-09-13T13:45:02Z TRACE_STEP trace-wo-778 step=1 desc="Validated ontology constraints for WorkOrder."
2026-09-13T13:45:03Z TRACE_TOOL_CALL trace-wo-778 step=2 tool=cypher.query params="work_order_id=WO-778" result="3 NCRs, 2 Operations, 5 Inspections, 4 Nonconformities."
2026-09-13T13:45:05Z TRACE_END trace-wo-778 status=success
```

This is your compliance and debugging backbone.

---

# **7. Migration Assessment (from create-context-graph)**

Your repo originated from **neo4j-labs/create-context-graph**, which provides:

- basic STM (messages)
- basic LTM (entities)
- basic RM (traces)

Plan‑009 upgrades this into:

- a full **Agent Memory Service**
- a clean **API layer**
- a **manufacturing-quality ontology-backed LTM**
- a **decision-trace RM** aligned with your Cypher reasoning layer
- a **provenance audit log**

Migration steps:

1. **Retain** the existing Neo4j schema from create-context-graph.  
2. **Extend** it with MFGM+MFGQ entities and relationships.  
3. **Add** RM nodes (ReasoningTrace, ReasoningStep, ToolCall).  
4. **Wrap** everything in the Plan‑009 API service.  
5. **Integrate** with your agents (PM, Quality, MFG, MCP).  

This is a forward-compatible evolution.

---

# **8. Implementation Roadmap**

## **Phase 1 — Foundation**
- Install Neo4j
- Load MFGM+MFGQ ontology entities
- Load Cypher reasoning templates

## **Phase 2 — Memory Service**
- Implement STM API
- Implement LTM API
- Implement RM API

## **Phase 3 — Decision Tracing**
- Add ReasoningTrace nodes
- Add ReasoningStep nodes
- Add ToolCall nodes
- Add audit log writer

## **Phase 4 — Agent Integration**
- PM Agent → RM + LTM  
- Quality Agent → RM + Cypher  
- MFG Agent → LTM + provenance  
- MCP Agent → RM + audit log  

## **Phase 5 — Compliance & Explainability**
- SHACL validation  
- Evidence-bound reasoning  
- Full audit trail  

---

# **9. Deliverables**

Plan‑009 produces:

- **Agent Memory Service** (HTTP API)
- **Context Graph API** (STM, LTM, RM)
- **Decision‑Trace Schema**
- **Audit Log Format**
- **Neo4j Context Graph schema**
- **Migration plan from create-context-graph**

---

# **10. Next Step**

If you want, I can generate:

- **Plan‑010 — Implementation Blueprint (FastAPI + Neo4j)**  
- **Plan‑011 — Cypher Migrations for STM/LTM/RM**  
- **Plan‑012 — Agent SDK for Memory Service**  
- **Plan‑013 — Full repo folder structure**

Just tell me which plan you want next.