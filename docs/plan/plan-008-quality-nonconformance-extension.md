# Plan 008: Quality and Nonconformance Extension (MFGQ)

## Decision

Use the existing MFGQ package in `my-mrp-kb/mfgq-extension` as the canonical
quality-domain extension for the manufacturing ontology stack. The extension
will sit on top of the authoritative SAP SALT-KG / OBKG semantic context and
add quality semantics without creating a competing manufacturing ontology.

This plan implements the quality and nonconformance layer as an evidence-bound,
read-only extension and keeps the existing manufacturing ontology and graph as
source-of-truth context.

The canonical package input is:

```text
my-mrp-kb/mfgq-extension/
```

## Scope

The MFGQ quality layer will define a small but operationally useful ontology for:

- nonconformance cases
- nonconformity defects and their root causes
- inspection and measurement evidence
- specification / requirement validation
- disposition, containment, and corrective action tracking
- cross-linkage to SAP context entities such as Material, Batch, Plant, Order,
  Operation, Work Center, Equipment, and Supplier

The design explicitly preserves the SALT-KG architectural pattern:

- SAP / OBKG owns context and master semantics
- MFGQ adds quality semantics
- Neo4j stores the operational graph for traversal and analysis
- SHACL validates instance quality
- Ontop / RDF validation protects ontology integrity

## Inputs

- `my-mrp-kb/mfgq-extension/ontology/mfgq.ttl`
- `my-mrp-kb/mfgq-extension/shacl/mfgq-shapes.ttl`
- `my-mrp-kb/mfgq-extension/neo4j/mfgq-schema.cypher`
- `my-mrp-kb/mfgq-extension/examples/ncr-example.ttl`
- validated manufacturing ontology snapshot from Plan 005 / Plan 006
- SAP SALT-KG / OBKG context entity IDs and naming conventions
- existing Create Context Graph ontology and graph validation conventions

## Outputs

A complete quality and nonconformance extension package, including:

### 1. Ontology layer

- OWL/RDF classes for:
  - `Nonconformance`
  - `Nonconformity`
  - `Defect`
  - `Inspection`
  - `Measurement`
  - `Specification`
  - `Requirement`
  - `Disposition`
  - `ContainmentAction`
  - `CorrectiveAction`
  - `RootCause`
  - `Severity`
  - `Status`

- OWL object properties such as:
  - `affectedPart`
  - `affectedMaterial`
  - `affectedBatch`
  - `occurredAtPlant`
  - `associatedWithOrder`
  - `associatedWithOperation`
  - `associatedWithWorkCenter`
  - `associatedWithEquipment`
  - `associatedWithSupplier`
  - `hasNonconformity`
  - `hasDefect`
  - `detectedBy`
  - `violates`
  - `concernsCharacteristic`
  - `specifies`
  - `producesMeasurement`
  - `measuresCharacteristic`
  - `hasDisposition`
  - `hasContainmentAction`
  - `hasCorrectiveAction`
  - `hasRootCause`
  - `usesInstrument`
  - `evaluation`

- Data properties such as:
  - `identifier`
  - `code`
  - `value`
  - `nominalValue`
  - `lowerLimit`
  - `upperLimit`
  - `unitCode`
  - `severity`
  - `status`
  - `detectedAt`
  - `closedAt`
  - `quantityAffected`
  - `description`
  - `sourceSystem`
  - `sourceId`
  - `sourceRecord`

### 2. SHACL validation layer

- Node shapes for `Nonconformance`, `Nonconformity`, and `Measurement`
- Required property checks
- closed-case disposition validation
- source provenance and cardinality constraints

### 3. Neo4j operational graph layer

- `:Nonconformance`
- `:Nonconformity`
- `:Defect`
- `:Inspection`
- `:Measurement`
- `:Specification`
- `:Disposition`
- `:CorrectiveAction`
- `:RootCause`
- relationship types matching the MFGQ object properties
- indexing and uniqueness for `identifier`, `sourceSystem`, and `sourceId`

### 4. Quality reasoning strategies

Read-only Cypher strategies for:

- NCR lifecycle and status progression
- part and batch defect traceability
- inspection measurement failure analysis
- supplier-linked nonconformance clustering
- corrective action / root-cause linkage
- work-order and operation impact tracing

### 5. SAP-aligned integration mapping

A mapping layer to bind generic integration properties to actual OBKG entity IDs
and predicates used in deployment, instead of leaving the extension generic.

## Design Rules

1. MFGQ is an extension layer, not a replacement for manufacturing context.
2. Do not create duplicate `QualityMaterial`, `QualityPlant`, or `QualityOrder`
   classes unless the SAP context graph genuinely lacks a concept.
3. All quality cases reference the authoritative SAP context entities.
4. Quality semantics are descriptive and evidence-based, not inferred from names
   or timestamps alone.
5. All quality records carry `sourceSystem`, `sourceId`, and `sourceRecord`.
6. SHACL validates instance integrity; OWL defines semantics; Neo4j delivers
   traversals and operational queries.
7. The namespace remains provisional until the governed MFGQ URI is assigned.

## Tasks

### Task 008.1 — Align MFGQ to the canonical manufacturing context

- Confirm the MFGQ ontology references the same SAP context semantics used in the
  manufacturing ontology and OBKG model.
- Replace generic identifiers with deployment-specific SAP object references.
- Define a controlled mapping table for:
  - Material
  - Batch
  - Plant
  - Production Order
  - Operation
  - Work Center
  - Equipment
  - Supplier

### Task 008.2 — Harden the ontology contract

- Validate all class and property IRIs under the MFGQ namespace.
- Confirm `Nonconformance`, `Nonconformity`, and `Defect` remain distinct.
- Validate measurement, specification, and disposition semantics.
- Ensure each property has an explicit domain and range, or a documented
  controlled extension pattern.

### Task 008.3 — Materialize the Neo4j schema

- Create the Cypher schema from the MFGQ package.
- Add unique constraints for case identifiers and source provenance.
- Add indexes for time-based and status-based analysis.
- Ensure the graph remains integrated with the manufacturing context graph by
  using the same external entity IDs.

### Task 008.4 — Add quality reasoning queries

Implement read-only Cypher queries for:

- open nonconformances by plant / material / supplier
- defect-by-part and defect-by-batch drilldown
- inspection result summary linked to a specification
- work-order and operation impact analysis
- root-cause and corrective-action traceability
- disposition closure verification

### Task 008.5 — Add evidence-driven quality tools

Generate agent tools that accept strict parameters and return evidence-backed
results only. Examples:

- `get_nonconformances_for_work_order`
- `get_measurement_failures_for_part`
- `get_supplier_nc_history`
- `get_root_cause_evidence`
- `get_open_defects_by_plant`
- `get_disposition_status_for_nc`

These tools must not create records, mutate graph state, or infer relationships
without explicit evidence.

### Task 008.6 — Validate the quality extension with SHACL and RDF

- Parse and validate `mfgq.ttl` with RDFLib.
- Validate all example NCR data against the SHACL shapes.
- Run the example instance and confirm the required relationships exist.
- Ensure closed cases must include a disposition.

### Task 008.7 — Add deterministic tests

Add targeted tests for:

- ontology structure and class separation
- SHACL validation of valid and invalid NCR records
- Neo4j schema creation and relationship integrity
- evidence-bound reasoning queries
- supplier, part, batch, and work-order linkage
- source provenance retention
- no duplicate / conflicting quality semantics on re-run

### Task 008.8 — Package the extension for downstream use

- keep the extension in the canonical `my-mrp-kb/mfgq-extension` package
- expose a small versioned metadata manifest
- record artifact hashes and validation outcomes
- preserve a clean separation between the manufacturing ontology and the quality
  extension

## Validation

Plan 008 is complete when all of the following are true:

- the MFGQ ontology validates successfully under RDFLib
- the SHACL shapes pass for representative valid NCR/inspection cases
- the MFGQ schema creates valid Neo4j labels and relationships
- every quality query is parameterized and read-only
- every nonconformance remains linked to authoritative SAP context entities
- no duplicate manufacturing ontology classes are created
- the extension remains safe for evidence-bound reasoning and agent tools
- the package is versioned and reproducible in the canonical workspace

## Non-Goals

- migrating SAP source data into the quality layer
- creating duplicate enterprise master entities
- granting agent write access to nonconformance records
- inferring root cause, defect, or supplier risk without explicit evidence
- replacing the manufacturing ontology with a separate quality ontology
- building a full ERP or QMS replacement model in this phase

## Recommended Implementation Sequence

1. align the MFGQ vocabulary to the exact SAP context entities already present in
   the manufacturing ontology
2. validate the RDF and SHACL layer
3. materialize the Neo4j schema
4. implement the first set of read-only quality queries
5. add agent tool wrappers and evidence-bound reasoning
6. final package validation and provenance capture

## Canonical Artifacts

```text
my-mrp-kb/mfgq-extension/
  README.md
  ontology/
    mfgq.ttl
  shacl/
    mfgq-shapes.ttl
  neo4j/
    mfgq-schema.cypher
  examples/
    ncr-example.ttl
```

This plan keeps the quality extension intentionally small, production-aligned,
and compatible with the manufacturing ontology architecture already in use.
