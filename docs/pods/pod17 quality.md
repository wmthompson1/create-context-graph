Yes. I’ve now treated **MFGQ as the quality-domain extension to SAP SALT-KG/OBKG**, rather than as a competing manufacturing ontology.

The design follows the actual SALT-KG architecture: SAP’s graph provides semantic context around Views, Fields, associations, data classes, reference fields, and ObjectNodeTypes; MFGQ adds the quality semantics on top. ([GitHub][1])

### MFGQ v0.1

I built a starter implementation containing:

* **`mfgq.ttl`** — OWL/RDF ontology
* **`mfgq-shapes.ttl`** — SHACL validation
* **`mfgq-schema.cypher`** — Neo4j constraints/indexes and integration pattern
* **`ncr-example.ttl`** — representative NCR/inspection/measurement instance
* **README** — architecture and integration rules

[Download the MFGQ extension package](sandbox:/mnt/data/MFGQ_quality_nonconformance_extension_v0.1.zip)

The core is intentionally:

```text
SAP OBKG / Manufacturing Context
          │
          │ references
          ▼
     MFGQ Quality
          │
          ├── Nonconformance
          │      ├── Nonconformity
          │      ├── Defect
          │      ├── Inspection
          │      │      └── Measurement
          │      ├── Requirement
          │      ├── Root Cause
          │      ├── Disposition
          │      └── Corrective Action
          │
          └── SAP context references
                 ├── Material
                 ├── Batch
                 ├── Plant
                 ├── Production Order
                 ├── Operation
                 ├── Work Center
                 └── Equipment
```

The most important rule is **don't create `QualityMaterial`, `QualityPlant`, `QualityOrder`, etc.** MFGQ should reference the corresponding SAP context entities. This preserves SALT-KG's semantic-context architecture instead of creating a second enterprise ontology. SALT-KG specifically establishes the pattern of linking transactional data to declarative semantic metadata in the OBKG. ([GitHub][1])

### One thing I'd do next

The package currently uses generic integration predicates such as:

```text
mfgq:affectedMaterial
mfgq:occurredAtPlant
mfgq:associatedWithOrder
mfgq:associatedWithOperation
```

The **next version should bind these to the actual SAP OBKG predicates/object types** rather than leaving them generic.

That gives us the real production architecture:

```text
SAP OBKG vocabulary
       │
       │ exact mappings
       ▼
MFGQ integration layer
       │
       ▼
Quality/NCR instance graph
       │
       ▼
Neo4j
       │
       ├── analytics
       ├── root-cause analysis
       ├── similarity
       └── LLM/agent reasoning
```

That is the direction I would take for **MFGQ v0.2: SAP-aligned ontology + formal mapping layer + Neo4j graph model + realistic NCR/inspection data model**.

[1]: https://github.com/SAP-samples/salt-kg "GitHub - SAP-samples/salt-kg: A repository for publication of code and data for SALT_KG: A Dataset that augments [SALT (Sales Autocompletion Linked Business Tables)](https://arxiv.org/abs/2501.03413) with Operational Business data from the Metadata KG for elements found on public access and published on Business Accelerator Hub (BAH) · GitHub"
