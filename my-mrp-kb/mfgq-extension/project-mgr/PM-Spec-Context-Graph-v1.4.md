

```markdown
# PM Specification – Context Graph (v1.4)
Domain: Manufacturing + Quality  
Author: PM Agent  
Purpose: Context Graph architecture + API + decision‑trace schema + audit log format.

---

## 0. Executive Summary

This spec defines:

- Three memory types: Short‑Term, Long‑Term, Reasoning
- ASCII diagrams for the architecture
- A Context Graph API (modeled on neo4j-agent-memory)
- A full agent decision‑trace schema
- A Reasoning Memory Audit Log format

It is aligned with:

- `mfgm-mfgq.ttl` (Manufacturing + Quality ontology)
- `mfgq-quality-reasoning.yaml` (Cypher reasoning layer)

> “WorkOrder, BOM, Schedule, Supplier, Lineage layer aligned with MFGQ quality ontology.”
> “MATCH (nc:Nonconformance)-[:ASSOCIATED_WITH_ORDER]->(wo:WorkOrder)”

---

## 1. ASCII Diagrams

### 1.1 Memory Types

```text
+---------------------------+
|      Context Graph        |
+---------------------------+
|   Short-Term  |  Long-Term|
|   (STM)       |  (LTM)    |
+---------------------------+
|     Reasoning Memory      |
|          (RM)             |
+---------------------------+
```

### 1.2 Flow Through Agents

```text
User
  |
  v
+------------------+
|  Interface Agent |
+------------------+
        |
        v
+------------------+
|  Semantic Agents |
| (Ontology, Lineage)
+------------------+
        |
        v
+------------------+
| Execution Agents |
| (Graph, SQLMesh) |
+------------------+
        |
        v
+---------------------------+
|       Context Graph       |
| STM  |  LTM  |   RM       |
+---------------------------+
```

---

## 2. Context Graph API

Modeled on the three memory types.

### 2.1 Short‑Term Memory API (STM)

```python
add_message(session_id, role, content)
search_messages(session_id, query)
get_session(session_id)
get_recent_messages(session_id, limit=20)
delete_session(session_id)
```

### 2.2 Long‑Term Memory API (LTM)

```python
add_entity(entity_type, properties)
search_entities(entity_type, query)
add_preference(entity_id, preference_type, value)
search_locations_near(lat, lon, radius_km)
get_entity_graph(entity_id, depth=2)
```

Entities include:

- WorkOrder (prov:Activity)
- Part
- Supplier
- Nonconformance

### 2.3 Reasoning Memory API (RM)

```python
start_trace(agent_id, session_id, purpose)
record_step(trace_id, description, evidence_ids=[])
record_tool_call(trace_id, tool_name, parameters, result_summary)
get_similar_traces(query, limit=10)
get_trace_provenance(trace_id)
```

---

## 3. Agent Decision‑Trace Schema

A normalized schema for RM.

### 3.1 Core Objects

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
  type: string        # e.g., "Nonconformance", "WorkOrder"
  ontology_id: string # e.g., "mfgq.quality.v0.1"
```

### 3.2 Example Trace (Work Order Quality Impact)

```yaml
Trace:
  id: "trace-wo-778"
  agent_id: "quality-analyst-agent"
  session_id: "sess-123"
  purpose: "work_order_quality_impact"
  steps:
    - id: "step-1"
      order: 1
      description: "Validated ontology constraints for WorkOrder."
    - id: "step-2"
      order: 2
      description: "Executed Cypher template work_order_quality_impact."
      tool_call:
        tool_name: "cypher.query"
        parameters:
          work_order_id: "WO-778"
        result_summary: "3 NCRs, 2 Operations, 5 Inspections, 4 Nonconformities."
      evidence:
        - id: "wo-778"
          type: "WorkOrder"
          ontology_id: "mfgq.quality.v0.1"
        - id: "nc-123"
          type: "Nonconformance"
          ontology_id: "mfgq.quality.v0.1"
```

---

## 4. Reasoning Memory Audit Log Format

A line‑oriented, append‑only log.

### 4.1 Log Record Types

```text
TRACE_START
TRACE_STEP
TRACE_TOOL_CALL
TRACE_END
TRACE_ERROR
```

### 4.2 Example Audit Log

```text
2026-09-13T13:45:01Z TRACE_START trace-wo-778 agent=quality-analyst-agent session=sess-123 purpose=work_order_quality_impact

2026-09-13T13:45:02Z TRACE_STEP trace-wo-778 step=1 desc="Validated ontology constraints for WorkOrder."

2026-09-13T13:45:03Z TRACE_TOOL_CALL trace-wo-778 step=2 tool=cypher.query params="work_order_id=WO-778" result="3 NCRs, 2 Operations, 5 Inspections, 4 Nonconformities."

2026-09-13T13:45:04Z TRACE_STEP trace-wo-778 step=3 desc="Linked Nonconformance nodes to WorkOrder WO-778 and Supplier entities."

2026-09-13T13:45:05Z TRACE_END trace-wo-778 status=success
```

This log is:

- Evidence‑bound
- Immutable
- Suitable for compliance and debugging

---

## 5. Summary

v1.4 adds:

- ASCII diagrams for the Context Graph and agent flow
- A concrete Context Graph API (STM, LTM, RM)
- A full agent decision‑trace schema
- A Reasoning Memory Audit Log format

You can now:

- Implement the API in a neo4j‑backed agent memory service
- Wire your manufacturing + quality agents into this schema
- Persist explainable, auditable reasoning traces for every decision.
```