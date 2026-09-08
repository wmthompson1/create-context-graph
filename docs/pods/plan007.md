

---

## ⭐ Five‑Minute Demonstration  
A tight, narrative‑driven walkthrough that shows the value of the manufacturing reasoning layer without overwhelming the audience.

### **Minute 0–1 — Set the stage: the manufacturing ontology**
Show the v1.1 ontology and explain that everything is explicit, typed, and evidence‑bound.

Quote (from your ontology):  
> “saltmfg:BillOfMaterials a owl:Class ; rdfs:label ‘Bill of materials’.”  


Explain that the ontology defines 12 classes, 14 object properties, and 10 datatype properties — all versioned under `salt.manufacturing.v1.1`.

### **Minute 1–2 — Show the executable layer (Ontop + synthetic mapping)**
Open the OBDA file and highlight that it is synthetic, metadata‑only, and SAP‑free.

Quote:  
> “source SELECT 1 AS synthetic_row”  


Run the smoke SPARQL query to show the ontology executes deterministically.

Quote:  
> “SELECT ?resource WHERE { ?resource a saltmfg:KnowledgeBase . }”  


### **Minute 2–3 — Show the packaged context‑graph**
Walk through the three catalogs:

- `domain.yaml`  
- `tools/manufacturing-tools.yaml`  
- `reasoning/strategies.yaml`  

Explain that the reasoning engine is **parameterized, read‑only Cypher**, with no `gds.*` anywhere.

### **Minute 3–4 — Live agent workflow (primary demo)**
Run the **BOM requirements** strategy.

User asks:  
**“For WorkOrder X, what parts are required and through which BOM?”**

Agent performs:

WorkOrder → BillOfMaterials → MaterialRequirement → Part

Returns explicit evidence with node IDs and relationship types.

This is the “aha” moment — explainability, safety, and operational relevance.

### **Minute 4–5 — Optional second workflow**
Run **schedule contention**:

User asks:  
**“Are there overlapping schedule slots for WorkCenter Y tomorrow?”**

Agent compares ScheduleSlot intervals and returns an evidence‑bound answer.

Close by emphasizing:

- No GDS  
- No SAP/CDS/transactional ingestion  
- No inferred edges  
- Fully versioned, reversible, explainable reasoning

---

## ⭐ Artifacts to prepare before the demo  
These ensure the demo runs smoothly and avoids last‑minute surprises.

### **1. Ontology + Ontop workspace**
- `salt-manufacturing.ttl`  
- `salt-manufacturing.obda`  
- `salt-manufacturing.sparql`  
- v1.1 `manifest.json`  
- Ontop wrapper + synthetic H2 driver

### **2. Context‑graph manufacturing package**
- `context-graph/manufacturing/domain.yaml`  
- `context-graph/manufacturing/tools/manufacturing-tools.yaml`  
- `context-graph/manufacturing/reasoning/strategies.yaml`  

### **3. Generated Strands scaffold**
- `backend/app/manufacturing_reasoning.py`  
- `backend/app/agent.py`  
- `backend/pyproject.toml` including `pyyaml>=6.0`

### **4. Neo4j Community instance**
- v1.1 ontology metadata ingested  
- synthetic nodes/relationships matching OBDA  
- `.env` credentials verified

### **5. Fixture data**
At least one synthetic example for:

- WorkOrder  
- BillOfMaterials  
- MaterialRequirement  
- Part  
- WorkCenter  
- ScheduleSlot  
- ProductionEvent  
- Supplier  
- SupplyCommitment  

So the BOM and schedule‑contention demos return meaningful evidence.

---
