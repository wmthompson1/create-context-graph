# MFGQ — Manufacturing Quality / Nonconformance Extension

MFGQ is a deliberately small quality-domain ontology designed to extend an existing SAP operational/business context graph rather than duplicate SAP master/context entities.

## Alignment target

The SAP SALT-KG work links transactional tables to an Operational Business Knowledge Graph (OBKG), including Views, Fields, associations, data classes, reference fields, and ObjectNodeTypes. MFGQ treats that SAP context as authoritative and adds quality semantics around it.

## Design rules

1. Nonconformance is a first-class managed case/event.
2. Nonconformance, Nonconformity, and Defect are distinct.
3. SAP entities such as Material, Plant, Order, Operation, Equipment, Batch, Supplier remain external context entities.
4. Measurements are first-class entities.
5. OWL defines semantics; SHACL defines data-quality constraints; Neo4j provides operational graph traversal.
6. Source-system/source-id provenance is retained.
7. The namespace is intentionally provisional and should be replaced by the organization's governed MFGQ URI/PURL before production.

## Core traversal

Nonconformance
 -> affectedPart / affectedMaterial / affectedBatch
 -> associatedWithOrder / Operation / WorkCenter / Equipment
 -> hasNonconformity -> violates -> Requirement
 -> hasDefect
 -> detectedBy -> Inspection -> producesMeasurement -> Measurement
 -> hasRootCause / causedBy
 -> hasDisposition
 -> hasCorrectiveAction

## Important implementation choice

Do not create QualityMaterial, QualityPlant, QualityOrder, etc. unless the SAP context graph genuinely lacks the concept. MFGQ should add semantics, not create a competing enterprise ontology.

## Next production step

Bind the generic integration properties to the exact SAP OBKG identifiers/predicates used in the target deployment, then add mappings for the organization's QMS/NCR source system.

This is now formalized in the SAP binding layer and the Neo4j mapping manifest:

- `ontology/mfgq-sap-bindings.ttl`
- `neo4j/mfgq-sap-mappings.yaml`

The quality extension keeps the SAP context graph authoritative and maps each MFGQ relationship to the equivalent SAP OBKG predicate rather than inventing a duplicate enterprise model.
