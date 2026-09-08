# **Single‑Slide PM Summary — Baseline vs Manufacturing**

**Context:**  
We validated the baseline scaffold and the manufacturing v1.1 scaffold in **model‑free, evidence‑bound** mode. The result is a clear distinction between a tutorial control case and a production‑grade operational system.

---

## **Baseline Tutorial (financial‑services)**  
- Minimal ontology: Account, Transaction, Person, Organization  
- Lightweight tool catalog  
- No bounded reasoning policy or explicit evidence contract  
- Basic backend startup and generic graph access  
- Useful as a control case for the scaffolding framework, not as a production workload

---

## **Manufacturing v1.1 (salt.manufacturing.v1.1)**  
- Full operational ontology: WorkOrder, BOM, MaterialRequirement, Part, WorkCenter, ScheduleSlot, ProductionEvent, Supplier, SupplyCommitment  
- Six catalog‑backed tools  
- Bounded read‑only Cypher strategies for BOM, schedule contention, supplier coverage, and production lineage  
- Live validation evidence: 186 total nodes, 5 WorkOrders, 25 documents  
- Confirmed relationships: WorkOrder → ProductionLine via `PRODUCED_ON`; Part → Supplier via `SUPPLIED_BY`; WorkOrder → Machine via `ASSIGNED_TO`  
- Explicit ontology checks, max‑hop limits, and graph‑grounded reasoning paths  
- No GDS, no inference, no writes — only explainable operational execution

---

## **PM Takeaway**  
The manufacturing scaffold is a **strict superset** of the baseline tutorial. It adds **structure**, **timing**, **supply**, and **execution reasoning** grounded in direct graph evidence. That is what makes it **production‑grade**, not a demo.

---
