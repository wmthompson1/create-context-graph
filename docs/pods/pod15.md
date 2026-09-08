
> Proceed with the v1.2 extension set… while preserving the no‑GDS, no‑write, evidence‑bound design.

---

# **1) v1.2 Ontology Update Plan (agent‑ready)**

### **Supplier‑Risk Metadata (add to Supplier)**
- risk_score  
- on_time_delivery_pct  
- quality_score  
- compliance_status  
- lead_time_variance_days  
- preferred_supplier_flag  

### **ScheduleSlot Capacity Fields (add to ScheduleSlot)**
- planned_capacity  
- remaining_capacity  
- shift_id  
- work_center_role  
- slot_duration_minutes  

### **WorkOrder Convenience Edges**
- WorkOrder → MaterialRequirement  
- WorkOrder → Part  

### **ProductionEvent Operational Metadata**
- operator  
- shift  
- reason_code  
- event_type  

### **WorkOrder Lifecycle Metadata**
- lifecycle_stage  
- status_history  

### **Agent Implementation Steps**
1. Update TTL  
2. Update OBDA  
3. Update domain.yaml  
4. Update fixture generator  
5. Update reasoning strategies  
6. Validate live graph  
7. Produce v1.2 consistency report  

---

# **2) v1.2 Reasoning Strategy Additions (bounded Cypher)**

### **Supplier Risk Assessment**
Evidence path:  
`WorkOrder → Part → SUPPLIED_BY → Supplier`

Returns:  
risk_score, on_time_delivery_pct, quality_score, compliance_status

---

### **Schedule Capacity Feasibility**
Evidence path:  
`WorkOrder → WorkCenter → ScheduleSlot`

Returns:  
remaining_capacity vs WorkOrder.quantity

---

### **Supplier Performance Trends**
Evidence path:  
`Supplier → SUPPLIES_PART → Part`

Returns:  
aggregated quality/on‑time metrics

---

### **WorkOrder Lifecycle Reasoning**
Evidence path:  
`ProductionEvent → EXECUTES_WORK_ORDER → WorkOrder`

Returns:  
event_type → lifecycle_stage mapping

---

### **ProductionEvent Shift/Operator Analysis**
Evidence path:  
`ProductionEvent → EXECUTES_WORK_ORDER → WorkOrder`

Returns:  
operator, shift, reason_code

---

# **3) PM‑Ready v1.2 Roadmap Slide**

## **Manufacturing Ontology v1.2 Roadmap**

**Purpose:**  
Add operational depth while preserving the manufacturing scaffold’s core guarantees:  
**read‑only, bounded Cypher, evidence‑bound, no GDS, no inference.**

---

### **v1.2 Additions**
**Supplier Risk Metadata**  
risk_score, on_time_delivery_pct, quality_score, compliance_status, lead_time_variance, preferred_supplier_flag  

**ScheduleSlot Capacity Fields**  
planned_capacity, remaining_capacity, shift_id, work_center_role, slot_duration_minutes  

**WorkOrder Convenience Edges**  
WorkOrder → MaterialRequirement  
WorkOrder → Part  

**ProductionEvent Metadata**  
operator, shift, reason_code, event_type  

**WorkOrder Lifecycle Metadata**  
lifecycle_stage, status_history  

---

### **v1.2 Reasoning Enhancements**
- Supplier risk assessment  
- Schedule capacity feasibility  
- Supplier performance trends  
- WorkOrder lifecycle reasoning  
- ProductionEvent shift/operator analysis  

All strategies remain **bounded Cypher**, **read‑only**, **evidence‑bound**, **no GDS**.

---

### **PM Takeaway**
v1.2 adds **operational realism** without expanding the risk surface.  
It strengthens procurement, scheduling, and execution reasoning while preserving the manufacturing scaffold’s safety guarantees.  
This is the next safe, credible evolution of the ontology.

---

The PM agent can help you do the next pass:

- generate the **v1.2 domain.yaml patch set**,  
- update the **OBDA mappings**,  
- produce the **v1.2 reasoning/strategies.yaml** entries, and  
- validate the live graph against the expanded manufacturing evidence paths.

This is the right follow-on task for the PM agent: turn the recommended v1.2 additions into concrete, testable ontology and reasoning changes while preserving the no-GDS, no-write, evidence-bound design.

