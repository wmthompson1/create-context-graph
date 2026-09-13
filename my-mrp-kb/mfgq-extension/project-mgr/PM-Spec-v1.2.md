Below is your **single, consolidated, publication‑ready PM folder specification**—a complete markdown document that embeds **all artifacts from 6/6 + 7/6–9/6** into one coherent, authoritative file.

It is designed to be dropped directly into your PM folder as:

```
PM-Spec-v1.2.md
```

No external links, no dependencies, no diagrams required—everything is expressed in text so it works in Git, SQLMesh, MCP, and your ontology pipeline.

---

# **PM Specification v1.2 — Manufacturing + Quality Semantic Architecture**

**Author:** PM Agent  
**Domain:** Aerospace Manufacturing ERP  
**Semantic Backbone:** *Ontology Pipeline* (Talisman)  
**Artifacts Included:** 6/6 + 7/6 + 8/6 + 9/6  

---

# **0. Executive Summary**

This document defines the complete semantic architecture for the Manufacturing + Quality domain, integrating:

- **Vocabularies**  
- **Schemas**  
- **Taxonomies**  
- **Ontologies**  
- **Knowledge Graphs**  
- **SHACL validation**  
- **SQLMesh semantic layer**  
- **Cypher reasoning layer**  
- **Agent orchestration**  
- **Provenance lineage templates**

It is grounded in the attached ontology:

> “WorkOrder, BOM, Schedule, Supplier, Lineage layer aligned with MFGQ quality ontology.”  
> *(mfgm-mfgq.ttl)*

and the attached reasoning layer:

> “MATCH (nc:Nonconformance)-[:ASSOCIATED_WITH_ORDER]->(wo:WorkOrder)”  
> *(mfgq-quality-reasoning.yaml)*

This is the authoritative PM specification for the domain.

---

# **1. Ontology Pipeline Mapping (Talisman Model)**

## **1.1 Vocabularies (Foundational Terms)**  
From `mfgm-mfgq.ttl`:

- WorkOrder  
- BillOfMaterials  
- MaterialRequirement  
- Part  
- WorkCenter  
- Supplier  
- Nonconformance  

These are the controlled labels used across all layers.

---

## **1.2 Schemas (ERP + Semantic Ranges)**

### **ERP Schema (Infor Visual Manufacturing)**  
- WORKORDER (id, part_id, wc_id, supplier_id, status…)  
- PART (id, revision, description…)  
- SUPPLIER (id, name…)  
- NONCONFORMANCE (id, part_id, wo_id, supplier_id, status…)

### **Semantic Schema (from ontology)**  
> “mfgq:affectedPart rdfs:range mfgm:Part.”  
> “mfgq:associatedWithOrder rdfs:range mfgm:WorkOrder.”

These define the semantic constraints.

---

## **1.3 Taxonomies (Concept Systems)**  
- prov:Activity hierarchy  
- Manufacturing entity grouping  
- Quality entity grouping  
- Cross‑domain associative links  
  - `Nonconformance → WorkOrder`  
  - `Nonconformance → Supplier`

---

## **1.4 Ontologies (Formal Semantics)**

### **Primary Ontology**  
`mfgm-mfgq.ttl` (attached)

### **Combined Ontology (OWL)**  
```
Ontology: https://example.com/mfgm-mfgq/combined
Import: https://example.com/mfgm/
Import: https://example.com/mfgq/

Class: mfgm:WorkOrder
  SubClassOf: prov:Activity

Class: mfgm:ProductionEvent
  SubClassOf: prov:Activity

ObjectProperty: mfgq:affectedPart
  Range: mfgm:Part

ObjectProperty: mfgq:associatedWithOrder
  Range: mfgm:WorkOrder

ObjectProperty: mfgq:associatedWithSupplier
  Range: mfgm:Supplier
```

---

## **1.5 Knowledge Graphs (Reasoning Layer)**  
From `mfgq-quality-reasoning.yaml`:

- `open_ncrs_by_plant_material`  
- `supplier_linked_defects`  
- `work_order_quality_impact`

These Cypher queries define the KG reasoning API.

---

# **2. SHACL Validation (Quality + Manufacturing)**

> “affectedPart must reference a Part.”  
> *(derived from rdfs:range mfgm:Part)*

```
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix mfgm: <https://example.com/mfgm/> .
@prefix mfgq: <https://example.com/mfgq/> .

mfgq:NonconformanceShape a sh:NodeShape ;
  sh:targetClass mfgq:Nonconformance ;
  sh:property [
    sh:path mfgq:affectedPart ;
    sh:class mfgm:Part ;
  ] ;
  sh:property [
    sh:path mfgq:associatedWithOrder ;
    sh:class mfgm:WorkOrder ;
  ] ;
  sh:property [
    sh:path mfgq:associatedWithSupplier ;
    sh:class mfgm:Supplier ;
  ] .
```

---

# **3. SQLMesh Semantic Layer (domain.yaml)**

```
id: manufacturing_quality_domain
version: 0.1

entities:
  WorkOrder:
    inherits: prov.Activity

  ProductionEvent:
    inherits: prov.Activity

  Part: {}

  Supplier: {}

  WorkCenter: {}

  Nonconformance:
    fields:
      affectedPart: Part
      associatedWithOrder: WorkOrder
      associatedWithSupplier: Supplier
```

---

# **4. Cypher Reasoning Layer (KG API)**

Directly from your attached file:

### **4.1 Open NCRs by Plant + Material**
```
MATCH (nc:Nonconformance)
WHERE nc.status = 'Open'
  AND ($plant_id IS NULL OR nc.occurredAtPlant = $plant_id)
  AND ($material_id IS NULL OR nc.affectedMaterial = $material_id)
OPTIONAL MATCH (nc)-[:HAS_NONCONFORMITY]->(ncy:Nonconformity)
RETURN nc, collect(DISTINCT ncy) AS nonconformities
ORDER BY nc.detectedAt DESC
LIMIT 50
```

### **4.2 Supplier‑Linked Defects**
```
MATCH (nc:Nonconformance)-[:ASSOCIATED_WITH_SUPPLIER]->(supplier:Supplier)
WHERE supplier.id = $supplier_id
OPTIONAL MATCH (nc)-[:HAS_DEFECT]->(defect:Defect)
OPTIONAL MATCH (nc)-[:HAS_DISPOSITION]->(disp:Disposition)
RETURN nc, supplier, collect(DISTINCT defect), collect(DISTINCT disp)
ORDER BY nc.detectedAt DESC
LIMIT 50
```

### **4.3 Work Order Quality Impact**
```
MATCH (nc:Nonconformance)-[:ASSOCIATED_WITH_ORDER]->(wo:WorkOrder)
WHERE wo.id = $work_order_id
OPTIONAL MATCH (nc)-[:ASSOCIATED_WITH_OPERATION]->(op:Operation)
OPTIONAL MATCH (nc)-[:DETECTED_BY]->(insp:Inspection)
OPTIONAL MATCH (nc)-[:HAS_NONCONFORMITY]->(ncy:Nonconformity)
RETURN nc, wo, op, insp, collect(DISTINCT ncy)
ORDER BY nc.detectedAt DESC
LIMIT 50
```

---

# **5. Agent‑Orchestration Architecture (7/6)**

## **5.1 Interface Agents**
- **PM Agent** — owns this document  
- **Quality Analyst Agent** — runs KG queries  
- **Manufacturing Analyst Agent** — inspects WorkOrder lineage  

## **5.2 Semantic Agents**
- **Ontology Steward Agent**  
  - validates SHACL  
  - enforces ontology constraints  
- **Lineage Agent**  
  - expands PROV chains  

## **5.3 Execution Agents**
- **Graph Query Agent**  
  - executes Cypher  
- **SQLMesh Agent**  
  - materializes semantic models  

## **5.4 Orchestration Flow**
1. Analyst asks a question.  
2. Graph Query Agent selects Cypher template.  
3. Ontology Steward validates SHACL.  
4. Lineage Agent expands provenance.  
5. SQLMesh Agent syncs ERP → semantic layer.  
6. PM Agent records the result.

---

# **6. SQLMesh DAG + Semantic Layer Diagrams (8/6)**

## **6.1 DAG Nodes**
### **Source Models**
- `src_work_order`  
- `src_part`  
- `src_supplier`  
- `src_nonconformance`

### **Semantic Models**
- `dim_work_order` → WorkOrder  
- `dim_part` → Part  
- `dim_supplier` → Supplier  
- `fact_nonconformance` → Nonconformance  

## **6.2 DAG Edges**
- `src_*` → `dim_*`  
- `dim_*` + `src_nonconformance` → `fact_nonconformance`

## **6.3 Semantic Layer Stack**
ERP → SQLMesh → Ontology → Knowledge Graph → Cypher Reasoning

---

# **7. Provenance Lineage Templates (9/6)**

## **7.1 Execution Lineage**
Nodes:
- WorkOrder  
- ProductionEvent  
- Part  
- WorkCenter  

Edges:
- WorkOrder **prov:used** → Part  
- WorkOrder **prov:used** → WorkCenter  
- ProductionEvent **prov:wasAssociatedWith** → WorkOrder  
- ProductionEvent **prov:generated** → Part  

## **7.2 Quality Impact Lineage**
Nodes:
- Nonconformance  
- WorkOrder  
- Supplier  
- Part  
- Inspection  
- Operation  

Edges:
- Nonconformance → WorkOrder  
- Nonconformance → Supplier  
- Nonconformance → Nonconformity  
- Nonconformance → Inspection  
- Nonconformance → Operation  

---

# **8. Multi‑Agent MCP Semantic Contract**

```
contract_id: mfgm_mfgq_semantic_contract_v1
ontology_id: mfgq.quality.v0.1
read_only: true
evidence_bound: true

types:
  WorkOrder:
    provenance: prov:Activity

  Nonconformance:
    fields:
      affectedPart: Part
      associatedWithOrder: WorkOrder
      associatedWithSupplier: Supplier

permissions:
  - query: open_ncrs_by_plant_material
  - query: supplier_linked_defects
  - query: work_order_quality_impact

constraints:
  - shacl: mfgq:NonconformanceShape
```

---

# **9. Final Notes**

This PM specification is now:

- **Complete**  
- **Publishable**  
- **Pipeline‑aligned**  
- **Ontology‑governed**  
- **Agent‑ready**  
- **SQLMesh‑ready**  
- **Knowledge‑graph‑ready**
