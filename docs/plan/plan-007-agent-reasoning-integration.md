# Plan 007: Agent Reasoning Integration (Manufacturing)

## Decision

Integrate the GDS-free manufacturing context-graph package into generated
agent workflows. Reasoning is evidence-bound and read-only: agents retrieve
explicitly asserted nodes and relationships through parameterized Cypher, then
explain conclusions from the returned evidence. This plan does not alter
`salt.manufacturing.v1.1`, create production records, or enable agent writes.

The canonical package input is:

```text
context-graph/manufacturing/
```

## Reasoning Model

The runtime loads `domain.yaml`, `tools/manufacturing-tools.yaml`, and
`reasoning/strategies.yaml`. Every query receives `$ontology_id` fixed to
`salt.manufacturing.v1.1`; every user-supplied value remains a Cypher
parameter. The agent may compose retrieved results but must not infer an edge
from shared names, identifiers, dates, or timestamps.

Strategies are deliberately bounded:

- `bom_requirements`: `WorkOrder -> BillOfMaterials -> MaterialRequirement -> Part`.
- `schedule_contention`: compare explicit `ScheduleSlot` intervals allocated
  to one `WorkCenter`.
- `production_lineage`: follow explicit `PRECEDES_EVENT`, consumed-part, and
  produced-part evidence around `ProductionEvent`.
- `supply_coverage`: retrieve `SupplyCommitment -> Supplier` and
  `SupplyCommitment -> Part` evidence for a required part.

GDS algorithms, graph projections, similarity scoring, path inference, and
unbounded traversals are out of scope.

## Tasks

1. Add a package loader to generated backend applications. Validate the source
   ontology ID, package hash, tool names, and strategy contract at startup.
2. Register the six generated read-only manufacturing tools with each supported
   agent framework. Use the existing context-graph client for Cypher execution;
   do not call Copilot Chat as a model API.
3. Add a strategy dispatcher that permits only the named strategies, enforces a
   maximum of four graph hops, and attaches the selected strategy and returned
   node identifiers to each tool result.
4. Add a manufacturing reasoning prompt section: distinguish observed evidence,
   missing evidence, and assumptions; request clarification when an explicit
   link is absent.
5. Add document-link retrieval for permitted document kinds only. Link chunks
   to graph nodes only through explicit identifiers and preserve source,
   document kind, chunk identifier, and import time as provenance.
6. Surface reasoning evidence in streaming responses as tool events, not hidden
   chain-of-thought. Return concise citations to node IDs, relationship types,
   and document chunk IDs.
7. Add deterministic fixture-based tests for BOM, schedule contention,
   production lineage, and supplier coverage, including negative tests proving
   that no result is inferred from matching labels or timestamps alone.

## Validation

- Package loader rejects a non-v1.1 source identity or missing strategy file.
- Each tool remains parameterized and scoped to `$ontology_id`.
- Neo4j `EXPLAIN` validates every tool and reasoning query without GDS.
- Fixture tests show evidence-backed answers and explicit no-evidence results.
- Document ingestion rejects SAP, CDS, and transactional content and preserves
  provenance for allowed documents.
- No Plan 007 query performs `CREATE`, `MERGE`, `SET`, `DELETE`, or invokes
  `gds.*`.

## Non-Goals

- Changing ontology semantics or rewriting Plan 005 artifacts.
- GDS installation or use.
- Autonomous write operations, schedule optimization, or supplier selection.
- Ingesting SAP SALT data, CDS metadata, or production transactions.