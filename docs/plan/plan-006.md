Absolutely, William — now that the agent has fixed the UTF‑8 loader and Plan 005 is fully complete, here is a **clean, production‑ready Plan 006** you can hand directly to the agent.

This version is structured exactly like your existing Plans 001–005:  
- version‑scoped  
- artifact‑driven  
- reversible  
- provenance‑aware  
- metadata‑only  
- no SAP/CDS/transactional content  
- safe for Neo4j and Ontop  
- aligned with Create Context Graph conventions  

It is ready for assignment.

---

# **📘 Plan 006 — Context Graph Integration (Manufacturing Domain)**  
**Purpose:**  
Transform the validated SALT manufacturing ontology (v1.1) into a complete **context graph domain**, enabling graph‑based reasoning, agent tools, retrieval, and multi‑agent workflows.

This plan does **not** modify ontology semantics.  
It packages them into a domain that agents can use.

---

## **1. Inputs**
- `salt.manufacturing.v1.1` snapshot  
- v1.1 regenerated artifacts  
- v1.1 manifest  
- manufacturing domain YAML (updated with v1.1 entities + relationships)  
- Neo4j metadata (classes, properties, domain/range)  
- existing ingestion/extraction/regeneration pipeline  
- Create Context Graph scaffolding

---

## **2. Outputs**
A complete manufacturing **context graph package**, including:

### **2.1 `domain.yaml` (finalized)**
Defines:
- entity types  
- relationship types  
- properties  
- embeddings  
- retrieval rules  
- ingestion rules  
- agent tools  

### **2.2 `schema.cypher`**
Creates:
- node labels  
- relationship types  
- constraints  
- indexes  

### **2.3 GDS-Free Reasoning Strategies**
Defines parameterized, read-only Cypher strategies for:
- BOM requirement traversal
- schedule-contention checks
- production lineage
- supplier commitment coverage

Neo4j Graph Data Science is not a dependency of this package.

### **2.4 Agent Tools**
Auto‑generated tools for:
- retrieving WorkOrders  
- retrieving BOM components  
- retrieving Machines / WorkCenters  
- retrieving ProductionEvents  
- retrieving MaterialRequirements  
- retrieving Suppliers / Parts  

### **2.5 Document Ingestion Rules**
For:
- work instructions  
- BOM PDFs  
- routing sheets  
- supplier specs  
- manufacturing documentation  

### **2.6 Packaged Context Graph Directory**
```
context-graph/
    manufacturing/
        domain.yaml
        schema.cypher
        reasoning/
        tools/
        ingestion/
        validation/
```

---

## **3. Tasks**

### **Task 6.1 — Finalize Domain YAML**
From v1.1 snapshot:
- map classes → entity types  
- map object properties → directed relationships  
- map datatype properties → attributes  
- define embeddings for text fields  
- define retrieval rules  
- define ingestion rules  
- define agent tools  

### **Task 6.2 — Generate Schema Cypher**
From domain YAML:
- create constraints  
- create indexes  
- create node labels  
- create relationship types  

### **Task 6.3 — Generate GDS-Free Reasoning Strategies**
Define Cypher-only strategies for:
- BOM requirements
- MRP lineage
- WorkOrder → ProductionEvent → Machine execution
- Supplier → SupplyCommitment → Part coverage

### **Task 6.4 — Generate Agent Tools**
Auto‑generate:
- `get_work_order`  
- `get_bom_components`  
- `get_machine_status`  
- `get_supplier_parts`  
- `get_material_requirements`  
- `get_production_events`  

### **Task 6.5 — Generate Document Ingestion Rules**
Define:
- text extraction  
- chunking  
- embedding  
- linking to graph nodes  
- provenance rules  

### **Task 6.6 — Validate Context Graph**
Run:
- schema.cypher  
- reasoning/strategies.yaml
- tool tests  
- ingestion tests  
- provenance tests  

### **Task 6.7 — Package Context Graph**
Produce:
```
context-graph/
    manufacturing/
        domain.yaml
        schema.cypher
        gds.cypher
        tools/
        ingestion/
        validation/
```

---

## **4. Success Criteria**
Plan 006 is complete when:

- domain.yaml is finalized from v1.1 snapshot  
- schema.cypher builds a valid graph  
- GDS-free reasoning strategies validate with Neo4j `EXPLAIN`
- agent tools work  
- ingestion rules work  
- provenance is correct  
- no SAP/CDS/transactional data is touched  
- all domain YAMLs load cleanly under UTF‑8  
- broad domain loader test passes  

---
