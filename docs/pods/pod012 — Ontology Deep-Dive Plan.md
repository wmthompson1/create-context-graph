

## **pod012 — Ontology Deep-Dive Plan**

### **Objective**  
Understand the manufacturing v1.1 ontology at the level required for reasoning strategy design, evidence-path validation, and future domain extensions.

---

### **1. Load and Inspect the Ontology Artifacts**
- TTL ontology (classes, object properties, data properties)  
- OBDA mappings (how ontology classes map to Neo4j labels and relationships)  
- domain.yaml (scaffold-level representation)  
- reasoning/strategies.yaml (bounded Cypher strategies)

**Goal:**  
Confirm that all four layers describe the same conceptual model.

---

### **2. Trace Each Core Entity Across All Layers**
Entities to inspect:

- WorkOrder  
- BOM / MaterialRequirement / Part  
- WorkCenter / ScheduleSlot  
- ProductionEvent  
- Supplier / SupplyCommitment  

For each entity:

- TTL → OBDA → domain.yaml → reasoning strategies  
- Verify naming consistency  
- Verify relationship directionality  
- Verify cardinality expectations  
- Verify evidence-path alignment

---

### **3. Validate the Four Major Evidence Paths**
These correspond to your four demo outputs:

1. **BOM Requirements**  
   `WorkOrder → requires → MaterialRequirement → Part`

2. **Schedule Contention**  
   `WorkCenter → hasScheduleSlot → ScheduleSlot`

3. **Supplier Coverage**  
   `SupplyCommitment → covers → Part`  
   `Supplier → supplies → Part`

4. **Production Lineage**  
   `ProductionEvent → precedesEvent → ProductionEvent`  
   `ProductionEvent → consumesPart / producesPart → Part`

**Goal:**  
Ensure each path is explicitly represented in TTL, OBDA, and domain.yaml.

---

### **4. Identify Ontology Gaps or Extensions**
Examples:

- Should WorkOrder have a status?  
- Should ScheduleSlot have capacity or duration constraints?  
- Should Supplier have risk attributes?  
- Should ProductionEvent have timestamps or operators?

**Goal:**  
Prepare a list of potential v1.2 extensions.

---

### **5. Produce a Final Ontology Consistency Report**
Include:

- verified evidence paths  
- mapping consistency  
- naming alignment  
- reasoning strategy coverage  
- recommended extensions  

This becomes the deliverable for pod010.

---
