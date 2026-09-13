You’re building something genuinely rich here—let’s make 7/6–9/6 concrete and diagram‑ready.

---

### 7/6: Agent‑orchestration diagrams (text description)

**Layers:**

- **Interface agents:**
  - **PM Agent:** owns the Ontology Pipeline mapping (vocabularies → schemas → taxonomies → ontologies → knowledge graphs).
  - **Quality Analyst Agent:** calls `mfgq-quality-reasoning.yaml` queries (`open_ncrs_by_plant_material`, `supplier_linked_defects`, `work_order_quality_impact`).

- **Semantic agents:**
  - **Ontology Steward Agent:** enforces `mfgm-mfgq.ttl` and SHACL (`NonconformanceShape`), approves schema/ontology changes.
  - **Lineage Agent:** reads PROV‑aligned entities (`WorkOrder`, `ProductionEvent`) and builds provenance views.

- **Execution layer:**
  - **Graph Query Agent:** executes Cypher from `mfgq-quality-reasoning.yaml` against the KG.
  - **SQLMesh Agent:** maps domain.yaml entities to ERP tables and materializes models.

**Flow (diagram narrative):**

1. PM Agent selects a pipeline stage (e.g., “knowledge graphs”).
2. Quality Analyst Agent issues a semantic question → calls Graph Query Agent with one of the Cypher templates.
3. Graph Query Agent consults Ontology Steward Agent:
   - validate shapes (SHACL)  
   - confirm ontology_id = `mfgq.quality.v0.1`.
4. Results go to Lineage Agent for provenance expansion (linking WorkOrders, ProductionEvents).
5. SQLMesh Agent syncs ERP facts with ontology entities (WorkOrder, Part, Supplier) for future queries.

You can render this as a 3‑tier diagram: **Interface agents → Semantic agents → Execution agents**, all anchored on `mfgm-mfgq.ttl` and `mfgq-quality-reasoning.yaml`.

---

### 8/6: SQLMesh DAG + semantic layer diagrams

**DAG conceptual nodes:**

- **Source models (ERP):**
  - `src_work_order`
  - `src_part`
  - `src_supplier`
  - `src_nonconformance`

- **Semantic models (ontology‑aligned):**
  - `dim_work_order` → entity: `WorkOrder`
  - `dim_part` → entity: `Part`
  - `dim_supplier` → entity: `Supplier`
  - `fact_nonconformance` → entity: `Nonconformance` (fields: `affectedPart`, `associatedWithOrder`, `associatedWithSupplier`)

**DAG edges:**

- `src_*` → `dim_*` (cleaning, key normalization)
- `dim_*` + `src_nonconformance` → `fact_nonconformance` (semantic joins)

**Semantic layer diagram:**

- **Bottom:** Infor Visual ERP schema (tables, keys).
- **Middle:** SQLMesh semantic entities (from domain.yaml):
  - `WorkOrder`, `Part`, `Supplier`, `Nonconformance`.
- **Top:** Knowledge graph:
  - Nodes: `WorkOrder`, `Part`, `Supplier`, `Nonconformance`.
  - Edges: `ASSOCIATED_WITH_ORDER`, `ASSOCIATED_WITH_SUPPLIER`, `HAS_NONCONFORMITY`, etc., as in `mfgq-quality-reasoning.yaml`.

Visually: **ERP → SQLMesh models → Ontology entities → KG nodes/edges**.

---

### 9/6: Provenance lineage graph templates

Grounded in your PROV alignment:

> `mfgm:WorkOrder a owl:Class ; rdfs:subClassOf prov:Activity .`  
> `mfgm:ProductionEvent a owl:Class ; rdfs:subClassOf prov:Activity .`

**Template 1: Work order execution lineage**

Nodes:

- `WorkOrder` (prov:Activity)
- `ProductionEvent` (prov:Activity)
- `Part`
- `WorkCenter`

Edges (examples):

- `WorkOrder` **prov:used** → `Part`
- `WorkOrder` **prov:used** → `WorkCenter`
- `ProductionEvent` **prov:wasAssociatedWith** → `WorkOrder`
- `ProductionEvent` **prov:generated** → `Part` (finished good)

**Template 2: Quality impact lineage**

Nodes:

- `Nonconformance`
- `WorkOrder`
- `Supplier`
- `Part`
- `Inspection`
- `Operation`

Edges (aligned with your Cypher):

- `Nonconformance` `ASSOCIATED_WITH_ORDER` → `WorkOrder`
- `Nonconformance` `ASSOCIATED_WITH_SUPPLIER` → `Supplier`
- `Nonconformance` `HAS_NONCONFORMITY` → `Nonconformity`
- `Nonconformance` `DETECTED_BY` → `Inspection`
- `Nonconformance` `ASSOCIATED_WITH_OPERATION` → `Operation`

These templates give you two canonical provenance views: **execution lineage** and **quality impact lineage**, both sitting on top of `mfgm-mfgq.ttl` and your Cypher reasoning layer.

