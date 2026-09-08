# Plan 005: Manufacturing Semantic Expansion (v1.1)

## Decision

Create `salt.manufacturing.v1.1` as a new, version-scoped ontology. Do not
modify the validated `salt.manufacturing.v1.0` artifacts or its Neo4j semantic
records. v1.1 extends the metadata-only manufacturing vocabulary with planning,
execution, bill-of-material, scheduling, and supply-chain concepts. It does
not ingest SAP source data, CDS content, or transactional records.

The v1.1 IRI is:

```text
https://example.org/ontology/salt/manufacturing/v1.1
```

## Scope

Add these classes, preserving the existing v1.0 `Machine`, `Part`, `Supplier`,
and `WorkOrder` semantics:

- `WorkCenter`: a production-capacity grouping that owns or schedules machines.
- `ProductionEvent`: an observed or planned execution event for a work order.
- `BillOfMaterials`: a versioned structure defining components for a finished
  part or work order.
- `MaterialRequirement`: a dated quantity demand for a part.
- `ScheduleSlot`: a planned, bounded allocation of a work order to a work
  center or machine.
- `SupplyCommitment`: supplier evidence for a part quantity and delivery date.

Define object properties with explicit domain and range:

- `hasWorkCenter`: `Machine -> WorkCenter`
- `scheduledAt`: `WorkOrder -> WorkCenter`
- `usesMachine`: `ProductionEvent -> Machine`
- `executesWorkOrder`: `ProductionEvent -> WorkOrder`
- `consumesPart`: `ProductionEvent -> Part`
- `producesPart`: `ProductionEvent -> Part`
- `hasBillOfMaterials`: `WorkOrder -> BillOfMaterials`
- `definesRequirement`: `BillOfMaterials -> MaterialRequirement`
- `requiresPart`: `MaterialRequirement -> Part`
- `scheduledFor`: `ScheduleSlot -> WorkOrder`
- `allocatedTo`: `ScheduleSlot -> WorkCenter`
- `suppliesPart`: `SupplyCommitment -> Part`
- `committedBy`: `SupplyCommitment -> Supplier`
- `precedesEvent`: `ProductionEvent -> ProductionEvent`

Datatype properties may express identifiers, quantities, units, planned and
actual timestamps, lead times, priorities, and statuses. Each must have an
explicit XSD range and a domain from the class list above.

## Artifact Layout

Create a complete canonical workspace:

```text
my-mrp-kb/ontology/salt/manufacturing/v1.1/
  manifest.json
  salt-manufacturing.ttl
  salt-manufacturing.obda
  salt-manufacturing.sparql
  ontop.properties
  acceptance/
  drivers/
  ontop.ps1
```

The manifest uses `ontology_id: salt.manufacturing.v1.1` and registers every
artifact. The Ontop mapping remains synthetic in-memory H2 metadata; it must
not name SAP tables, CDS views, or external sources.

## Execution

1. Define the v1.1 ontology and acceptance queries from the semantic contract
   above, using stable IRIs in the v1.1 namespace.
2. Validate Turtle with RDFLib and the complete artifact set with the pinned
   Ontop wrapper before any graph write.
3. Ingest v1.1 through the existing manifest-driven ingest command. Its
   `ontology_id` ensures classes, properties, artifacts, and runs coexist with
   v1.0 without overwrite.
4. Extract a v1.1 snapshot from Neo4j and run the Plan 004 regeneration path
   against that snapshot to prove reversibility for the expanded vocabulary.
5. Add the corresponding entities and relationships to the scaffolded
   manufacturing domain only after their identifiers and direction match the
   canonical v1.1 ontology.

## Competency Questions

Acceptance queries and future read-only tools must support these evidence-bound
questions:

- Which material requirements are defined by a bill of materials for a work
  order?
- Which work center and machine are allocated to an upcoming work order?
- Which production events consumed or produced a part, and in what order?
- Which supplier commitment covers a required part and delivery date?
- Which scheduled work orders contend for the same work center interval?

These questions operate on synthetic metadata examples until an approved source
and evidence model exists. No relationship may be inferred from matching part
names, identifiers, or timestamps alone.

## Validation

- v1.1 RDFLib parsing, Ontop validation, and all SPARQL acceptance queries pass.
- Neo4j contains independently scoped v1.0 and v1.1 ontology graphs.
- Repeating v1.1 ingest creates no duplicate v1.1 semantic nodes or edges.
- v1.1 snapshot regeneration is byte-stable and does not alter v1.0 artifacts.
- Tests prove no SAP/CDS identifiers, source rows, or transactional values enter
  the v1.1 workspace or graph.

## Non-Goals

- Migrating or deleting v1.0.
- Importing SAP SALT data, CDS metadata, or production transactions.
- Enabling MCP, librarian, or agent write operations.
- Inferring schedule, BOM, lineage, or supplier relationships without explicit
  source evidence.