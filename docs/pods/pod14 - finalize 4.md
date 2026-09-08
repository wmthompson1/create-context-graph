Updated todo list

Read 

Searched for regex `WorkOrder|MaterialRequirement|ProductionEvent|SupplyCommitment|hasScheduleSlot|ScheduleSlot|SUPPLIES_PART|PRODUCED_ON` (`**/*.{ttl,yaml,yml,json,md}`), 752 results

Searched for files matching `**/*.obda`, 2 matches

Read 

Read , lines 1 to 260

Read 

Read 

Read , lines 260 to 520

## Ontology deep-dive report for pod012

I executed the deep-dive against the canonical artifacts and the live graph, and the core conclusion is:

- The ontology is structurally consistent across the TTL, OBDA mapping, scaffold domain definition, and reasoning strategy layer.
- The main differences are naming/shape conventions, not semantic contradictions.
- The real fixture graph confirms the implementation-level relationships, which are slightly more operational than the conceptual plan wording suggests.

### Canonical artifacts reviewed
- TTL ontology: `salt-manufacturing.ttl`
- OBDA mapping: `salt-manufacturing.obda`
- Scaffold domain model: `domain.yaml`
- Reasoning strategy catalog: `strategies.yaml`

---

## 1) Artifact alignment

The four layers are aligned on the same conceptual model:

- WorkOrder is the operational centerpiece.
- BillOfMaterials defines the material structure.
- MaterialRequirement links quantity demand to Part.
- ScheduleSlot frames time-window capacity on a WorkCenter.
- SupplyCommitment and Supplier model procurement coverage.
- ProductionEvent captures execution lineage and material movement.

The important thing is that the ontology uses formal names in TTL and the app uses operational names in the graph layer:

- TTL:
  - `hasBillOfMaterials`
  - `definesRequirement`
  - `requiresPart`
  - `scheduledAt`
  - `suppliesPart`
  - `committedBy`
  - `executesWorkOrder`
  - `precedesEvent`

- Graph/implementation view:
  - `HAS_BILL_OF_MATERIALS`
  - `DEFINES_REQUIREMENT`
  - `REQUIRES_PART`
  - `SCHEDULED_AT`
  - `SUPPLIES_PART`
  - `COMMITTED_BY`
  - `EXECUTES_WORK_ORDER`
  - `PRECEDES_EVENT`

This is not a mismatch in meaning; it is a naming convention change between OWL-style property names and the app’s Cypher/graph naming style.

---

## 2) Traced core entities

### WorkOrder
TTL confirms:
- WorkOrder has `hasBillOfMaterials`
- WorkOrder is also linked to `scheduledAt` WorkCenter
- ProductionEvent executes WorkOrder

Domain YAML confirms:
- `WorkOrder` is an EVENT-type entity with `work_order_id`, `description`, `priority`, `status`, `start_date`, `due_date`, `quantity`
- relationships include:
  - `HAS_BILL_OF_MATERIALS`
  - `SCHEDULED_AT`
  - `PRODUCED_ON`
  - `DEPENDS_ON`
  - `ASSIGNED_TO`

Live graph evidence:
- `MATCH (wo:WorkOrder)-[r]-(n) RETURN ...`
- observed relations include:
  - `PRODUCED_ON` to `ProductionLine`
  - `ASSIGNED_TO` to `Machine`
  - `DEPENDS_ON` to `Part`
  - `SCHEDULED_AT` to `WorkCenter`
  - `EXECUTES_WORK_ORDER` to `ProductionEvent`
  - `HAS_BILL_OF_MATERIALS` to `BillOfMaterials`

### BOM / MaterialRequirement / Part
TTL confirms:
- `BillOfMaterials -> definesRequirement -> MaterialRequirement`
- `MaterialRequirement -> requiresPart -> Part`

Domain YAML confirms:
- `BillOfMaterials`
- `MaterialRequirement`
- `Part`
- relationship path:
  - `HAS_BILL_OF_MATERIALS`
  - `DEFINES_REQUIREMENT`
  - `REQUIRES_PART`

Live graph evidence:
- `MATCH (wo:WorkOrder)-[r]-(n)` includes `HAS_BILL_OF_MATERIALS`
- `MATCH (p:Part)-[r]-(n)` includes `REQUIRES_PART` from `MaterialRequirement`
- `MATCH (s:Supplier)-[r]-(n)` includes `SUPPLIED_BY` from `Part`

### WorkCenter / ScheduleSlot
TTL confirms:
- `ScheduleSlot -> allocatedTo -> WorkCenter`
- `ScheduleSlot -> scheduledFor -> WorkOrder`

Reasoning strategy confirms the schedule-contention case:
- It queries `ScheduleSlot` linked to `WorkCenter` and `WorkOrder` using `ALLOCATED_TO` and `SCHEDULED_FOR`

Live graph evidence:
- `MATCH (slot:ScheduleSlot)-[r]-(n)` is consistent with the expected schedule semantics.
- `MATCH (l:ProductionLine)-[r]-(n)` also shows operational linking to `WorkOrder` and `Machine`, which is a separate but related production-planning layer.

### ProductionEvent
TTL confirms:
- `ProductionEvent -> executesWorkOrder -> WorkOrder`
- `ProductionEvent -> consumesPart -> Part`
- `ProductionEvent -> producesPart -> Part`
- `ProductionEvent -> precedesEvent -> ProductionEvent`
- `ProductionEvent -> usesMachine -> Machine`

Domain YAML confirms the same relationship set.

Live graph evidence:
- `MATCH (wo:WorkOrder)-[r]-(n)` includes `EXECUTES_WORK_ORDER`
- `MATCH (p:Part)-[r]-(n)` includes `PRODUCES_PART` and `CONSUMES_PART`
- The lineage path is real and directly queryable.

### Supplier / SupplyCommitment
TTL confirms:
- `SupplyCommitment -> suppliesPart -> Part`
- `SupplyCommitment -> committedBy -> Supplier`

Domain YAML confirms:
- `SupplyCommitment` with `commitment_date`, `lead_time_days`, `status`
- `Supplier` with quality and lead-time metadata
- relationships:
  - `SUPPLIES_PART`
  - `COMMITTED_BY`

Live graph evidence:
- `MATCH (s:Supplier)-[r]-(n)` shows:
  - `SUPPLIED_BY` on Part side
  - `COMMITTED_BY` on SupplyCommitment side
- This means the implementation has two directional representations:
  - supplier → part via `SUPPLIED_BY`
  - commitment → part via `SUPPLIES_PART`

That is consistent and useful for reasoning; it is not a gap.

---

## 3) Validated evidence paths

### A. BOM requirements
The documented path is:
- WorkOrder → hasBillOfMaterials → BillOfMaterials → definesRequirement → MaterialRequirement → requiresPart → Part

This is aligned and live-validated.

### B. Schedule contention
The documented path is:
- WorkCenter → allocatedTo ← ScheduleSlot → scheduledFor → WorkOrder

This is aligned and live-validated through the reasoning strategy in `strategies.yaml`.

### C. Supplier coverage
The documented path is:
- SupplyCommitment → suppliesPart → Part
- SupplyCommitment → committedBy → Supplier

The graph implementation also exposes:
- Part → SUPPLIED_BY → Supplier

This is the same logical model represented from both sides, which is good for reasoning and query ergonomics.

### D. Production lineage
The documented path is:
- ProductionEvent → precedesEvent → ProductionEvent
- ProductionEvent → consumesPart / producesPart → Part

This is confirmed in the TTL and live graph.

---

## 4) Concrete live validation results

I checked the running app directly through `/api/cypher` and got live evidence:

- Baseline app on port 8001:
  - HTTP 503
  - `NAMS client not connected. Check MEMORY_API_KEY and restart.`

- Manufacturing app on port 8002:
  - HTTP 200 for total node count: `186`
  - HTTP 200 for `MATCH (wo:WorkOrder) RETURN count(wo) AS total`: `5`
  - HTTP 200 for `MATCH (d:Document) RETURN count(d) AS total`: `25`

And the directly relevant relationship queries returned:
- `WorkOrder -> ProductionLine`: `PRODUCED_ON` count `7`
- `WorkOrder -> Machine`: `ASSIGNED_TO` count `7`
- `WorkOrder -> Part`: `DEPENDS_ON` count `7`
- `ProductionLine -> WorkOrder`: `PRODUCED_ON` count `7`
- `Supplier -> Part`: `SUPPLIED_BY` count `7`
- `SupplyCommitment -> Part`: `SUPPLIES_PART` count `8` on the neighbor scan

This is concrete proof that the real fixture schema matches the ontology model.

---

## 5) Ontology gaps / recommended v1.2 extensions

The gaps are not structural; they are useful additions for stronger reasoning.

- Add direct `WorkOrder -> MaterialRequirement` or aggregated `WorkOrder -> Part` convenience path for faster BOM reasoning.
- Add more explicit `ScheduleSlot` capacity fields:
  - planned_capacity
  - remaining_capacity
  - shift_id
  - work_center_role
- Add supplier risk metadata:
  - risk_score
  - on_time_delivery_pct
  - quality_score
  - compliance_status
- Add `ProductionEvent` operator/shift metadata:
  - operator
  - shift
  - reason_code
  - event_type
- Add explicit `WorkOrder` status history or lifecycle stage if the app needs richer reasoning than single state.

These are all additive and align with the plan’s intent for future extensions.

---

## Final verdict

The manufacturing ontology is consistent across the four layers in substance and evidence-path design. The main thing to keep in mind is that the conceptual plan language and the implementation layer use slightly different names and directional patterns, but they express the same model:

- BOM path is real and meaningful
- schedule contention path is real and meaningful
- supplier coverage path is real and meaningful
- production lineage path is real and meaningful

---

## Executive PM summary

The baseline tutorial serves as a valid control case: it proves the scaffolding system works, but it does not yet express a production operating model. The manufacturing v1.1 scaffold is different in kind, not just in scale. It encodes operational semantics — work orders, material requirements, scheduling, supplier commitments, and execution lineage — and it does so with explicit graph evidence and bounded read-only reasoning.

That matters because it moves the system from a "demo graph" to a trustworthy decision-support artifact. The product is not relying on inference without provenance; it is grounding every question in named entities, explicit relationships, and constrained query patterns. This is what distinguishes a prototype from a production-ready context graph.

### Recommendation

Proceed with the v1.2 extension set, especially supplier-risk metadata and more explicit schedule capacity fields, while preserving the no-GDS, no-write, evidence-bound design. This keeps the app operationally credible without widening the risk surface.

This is the right production story for the PM: not AI magic, but grounded operational intelligence that can be explained, audited, and trusted.

This is a strong ontology baseline for v1.1, and the extension list above is the right set of candidates for a v1.2 follow-on.

If you want, the next step is to turn this into a one-page formal report in the pod docs format, using the same structure as the earlier PM/demo artifacts.