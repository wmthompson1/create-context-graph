**start with the schema**, then OBDA, then reasoning strategies. That order keeps the manufacturing scaffold stable, reviewable, and fully evidence‑bound.


---

## ⭐ 1) v1.2 `domain.yaml` Patch Set (agent‑ready)

This is the first step because the domain model is the contract the rest of the system depends on. Your attached deep‑dive confirms the ontology is structurally aligned across TTL, OBDA, domain.yaml, and reasoning strategies:

> “The ontology is structurally consistent across the TTL, OBDA mapping, scaffold domain definition, and reasoning strategy layer.”  
> “The main differences are naming/shape conventions, not semantic contradictions.” 

Below is the **minimal additive patch set** you should apply.

### **Supplier**
```yaml
Supplier:
  attributes:
    risk_score: { type: integer }
    on_time_delivery_pct: { type: float }
    quality_score: { type: float }
    compliance_status: { type: string }
    lead_time_variance_days: { type: integer }
    preferred_supplier_flag: { type: boolean }
```

### **ScheduleSlot**
```yaml
ScheduleSlot:
  attributes:
    planned_capacity: { type: integer }
    remaining_capacity: { type: integer }
    shift_id: { type: string }
    work_center_role: { type: string }
    slot_duration_minutes: { type: integer }
```

### **WorkOrder**
```yaml
WorkOrder:
  attributes:
    lifecycle_stage: { type: string }
    status_history:
      type: list
      item_type: string

  relationships:
    HAS_MATERIAL_REQUIREMENT:
      target: MaterialRequirement
      direction: outgoing
    USES_PART:
      target: Part
      direction: outgoing
```

### **ProductionEvent**
```yaml
ProductionEvent:
  attributes:
    operator: { type: string }
    shift: { type: string }
    reason_code: { type: string }
    event_type: { type: string }
```

This patch set is **purely additive**, preserves the **no‑GDS, no‑write** guarantees, and matches the operational evidence your agent validated.

---

## ⭐ 2) v1.2 OBDA Mapping Updates

Once the domain.yaml is patched, the agent can safely update OBDA mappings. These are minimal additions — no changes to existing mappings.

### **Supplier Risk Attributes**
```obda
mappingId: SupplierRiskScore
target: :Supplier({supplier_id}) :riskScore {risk_score} .
source: SELECT supplier_id, risk_score FROM supplier;

mappingId: SupplierOnTimePct
target: :Supplier({supplier_id}) :onTimeDeliveryPct {on_time_delivery_pct} .
source: SELECT supplier_id, on_time_delivery_pct FROM supplier;

mappingId: SupplierQualityScore
target: :Supplier({supplier_id}) :qualityScore {quality_score} .
source: SELECT supplier_id, quality_score FROM supplier;

mappingId: SupplierComplianceStatus
target: :Supplier({supplier_id}) :complianceStatus {compliance_status} .
source: SELECT supplier_id, compliance_status FROM supplier;

mappingId: SupplierLeadTimeVariance
target: :Supplier({supplier_id}) :leadTimeVarianceDays {lead_time_variance_days} .
source: SELECT supplier_id, lead_time_variance_days FROM supplier;

mappingId: SupplierPreferredFlag
target: :Supplier({supplier_id}) :preferredSupplierFlag {preferred_supplier_flag} .
source: SELECT supplier_id, preferred_supplier_flag FROM supplier;
```

### **ScheduleSlot Capacity**
```obda
mappingId: ScheduleSlotCapacity
target: :ScheduleSlot({slot_id})
        :plannedCapacity {planned_capacity} ;
        :remainingCapacity {remaining_capacity} ;
        :slotDurationMinutes {slot_duration_minutes} .
source: SELECT slot_id, planned_capacity, remaining_capacity, slot_duration_minutes FROM schedule_slot;

mappingId: ScheduleSlotShiftRole
target: :ScheduleSlot({slot_id})
        :shiftId {shift_id} ;
        :workCenterRole {work_center_role} .
source: SELECT slot_id, shift_id, work_center_role FROM schedule_slot;
```

### **WorkOrder Convenience Edges**
```obda
mappingId: WorkOrderMaterialRequirement
target: :WorkOrder({work_order_id}) :hasMaterialRequirement :MaterialRequirement({material_requirement_id}) .
source: SELECT work_order_id, material_requirement_id FROM workorder_material_requirement;

mappingId: WorkOrderUsesPart
target: :WorkOrder({work_order_id}) :usesPart :Part({part_id}) .
source: SELECT work_order_id, part_id FROM workorder_part_usage;
```

### **ProductionEvent Metadata**
```obda
mappingId: ProductionEventMetadata
target: :ProductionEvent({event_id})
        :operator {operator} ;
        :shift {shift} ;
        :reasonCode {reason_code} ;
        :eventType {event_type} .
source: SELECT event_id, operator, shift, reason_code, event_type FROM production_event;
```

These mappings are safe, read‑only, and fully aligned with the ontology.

---

## ⭐ 3) v1.2 `strategies.yaml` Entries

Your attached deep‑dive confirms the evidence paths are real and validated:

> “BOM path is real and meaningful… schedule contention path is real and meaningful… supplier coverage path is real and meaningful… production lineage path is real and meaningful.” 

Here are the new strategies you can add.

### **Supplier Risk Assessment**
```yaml
supplier_risk_assessment:
  description: "Assess supplier risk for parts required by a WorkOrder."
  max_hops: 3
  cypher: |
    MATCH (wo:WorkOrder {work_order_id: $work_order_id})
      -[:USES_PART|DEPENDS_ON]->(p:Part)
      <-[:SUPPLIED_BY]-(s:Supplier)
    RETURN s.supplier_id AS supplier_id,
           s.name AS supplier_name,
           s.risk_score AS risk_score,
           s.on_time_delivery_pct AS on_time_delivery_pct,
           s.quality_score AS quality_score,
           s.compliance_status AS compliance_status
    ORDER BY risk_score DESC
  parameters:
    - name: work_order_id
      type: string
```

### **Schedule Capacity Feasibility**
```yaml
schedule_capacity_feasibility:
  description: "Check whether a WorkOrder fits into remaining ScheduleSlot capacity."
  max_hops: 3
  cypher: |
    MATCH (wo:WorkOrder {work_order_id: $work_order_id})
      -[:SCHEDULED_AT]->(wc:WorkCenter)
      <-[:ALLOCATED_TO]-(slot:ScheduleSlot)
    RETURN slot.slot_id AS slot_id,
           slot.remaining_capacity AS remaining_capacity,
           wo.quantity AS work_order_quantity,
           slot.remaining_capacity >= wo.quantity AS fits_capacity
  parameters:
    - name: work_order_id
      type: string
```

### **Supplier Performance Trends**
```yaml
supplier_performance_trends:
  description: "Summarize performance metrics for suppliers covering BOM parts."
  max_hops: 4
  cypher: |
    MATCH (wo:WorkOrder {work_order_id: $work_order_id})
      -[:HAS_BILL_OF_MATERIALS]->(:BillOfMaterials)
      -[:DEFINES_REQUIREMENT]->(mr:MaterialRequirement)
      -[:REQUIRES_PART]->(p:Part)
      <-[:SUPPLIED_BY]-(s:Supplier)
    RETURN s.supplier_id AS supplier_id,
           s.name AS supplier_name,
           avg(s.on_time_delivery_pct) AS avg_on_time_delivery_pct,
           avg(s.quality_score) AS avg_quality_score,
           max(s.risk_score) AS max_risk_score
    ORDER BY max_risk_score DESC
  parameters:
    - name: work_order_id
      type: string
```

### **WorkOrder Lifecycle Reasoning**
```yaml
workorder_lifecycle_reasoning:
  description: "Explain WorkOrder lifecycle stage based on ProductionEvents."
  max_hops: 3
  cypher: |
    MATCH (wo:WorkOrder {work_order_id: $work_order_id})
      <-[:EXECUTES_WORK_ORDER]-(pe:ProductionEvent)
    RETURN wo.work_order_id AS work_order_id,
           wo.lifecycle_stage AS lifecycle_stage,
           collect(pe.event_type) AS event_types,
           collect(pe.reason_code) AS reason_codes
  parameters:
    - name: work_order_id
      type: string
```

### **ProductionEvent Shift/Operator Analysis**
```yaml
production_shift_analysis:
  description: "Show operators and shifts executing a WorkOrder."
  max_hops: 3
  cypher: |
    MATCH (wo:WorkOrder {work_order_id: $work_order_id})
      <-[:EXECUTES_WORK_ORDER]-(pe:ProductionEvent)
    RETURN pe.event_id AS event_id,
           pe.operator AS operator,
           pe.shift AS shift,
           pe.event_type AS event_type,
           pe.reason_code AS reason_code
    ORDER BY pe.shift, pe.operator
  parameters:
    - name: work_order_id
      type: string
```

---

## ⭐ Ready for the agent to proceed  
Your agent already has the correct priority order:

1. **domain.yaml patch**  
2. **OBDA updates**  
3. **strategies.yaml additions**

This is the correct v1.2 implementation sequence. It keeps the ontology additive, reviewable, and grounded in the evidence paths already validated in the live graph, while preserving the no-GDS, no-write, evidence-bound constraints that make the manufacturing scaffold credible.

