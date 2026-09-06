# Plan 003: Neo4j Ingestion for SALT Manufacturing Ontology

## Decision

Ingest the canonical SALT manufacturing ontology into Neo4j as a versioned,
idempotent metadata graph. The manifest at
`my-mrp-kb/ontology/salt/manufacturing/v1.0/manifest.json` is the ingestion
contract. Its stable identifier, `salt.manufacturing.v1.0`, scopes every
ontology node, relationship, constraint, and provenance record.

Neo4j is the system of record for the ontology graph. Ontop remains the
virtual-graph validator and SPARQL access layer for the relational mapping.
GitHub Copilot in VS Code accesses Neo4j through read-only MCP tools; Copilot
is not an application model API.

## Preconditions

Before an ingestion run:

- `ontop.ps1 validate` succeeds in the canonical ontology directory.
- `manifest.json` parses and all registered artifacts exist.
- The target Neo4j database, URI, user, and password are provided through
  environment variables, never committed configuration.
- The target database is confirmed to be dedicated to this KB or the ingest is
  invoked with an explicit `ontology_id` scope.
- The SALT source-policy status remains `Reference-only pending license review`.
  Do not ingest SAP SALT source rows or descriptions until that review permits it.

## Graph Contract

The initial graph represents ontology metadata, not transactional SAP data.

### Nodes

- `Ontology`: `ontology_id`, `ontology_iri`, `namespace`, `domain`, `version`.
- `KnowledgeBase`: `kb_id`, `name`, `document_root`.
- `OntologyArtifact`: `path`, `kind`, `format`, `sha256`.
- `OntologyClass`: `iri`, `local_name`, `label`.
- `OntologyProperty`: `iri`, `local_name`, `label`, `property_kind`.
- `SourcePolicy`: `source_name`, `usage_status`, `license_review_status`.
- `IngestionRun`: `run_id`, `started_at`, `completed_at`, `tool_version`,
  `manifest_sha256`, `status`.

### Relationships

- `(KnowledgeBase)-[:OWNS_ONTOLOGY]->(Ontology)`
- `(Ontology)-[:DECLARES_CLASS]->(OntologyClass)`
- `(Ontology)-[:DECLARES_PROPERTY]->(OntologyProperty)`
- `(OntologyProperty)-[:HAS_DOMAIN]->(OntologyClass)`
- `(OntologyProperty)-[:HAS_RANGE]->(OntologyClass)`
- `(Ontology)-[:HAS_ARTIFACT]->(OntologyArtifact)`
- `(Ontology)-[:GOVERNED_BY]->(SourcePolicy)`
- `(IngestionRun)-[:INGESTED]->(Ontology)`
- `(IngestionRun)-[:USED_ARTIFACT]->(OntologyArtifact)`

Every MERGE key includes `ontology_id` unless the node is globally identified by
a stable IRI. This prevents a future `v1.1` or another domain from overwriting
the v1.0 graph.

## Phase 1: Manifest-to-Cypher Generation

1. Add an `ontology_ingest.py` module that accepts a manifest path and emits
   four reproducible files next to that manifest:
   `schema.cypher`, `ingest.cypher`, `relationships.cypher`, and
   `provenance.cypher`.
2. Parse Turtle with an RDF parser rather than regular expressions. Extract the
   ontology IRI, classes, object properties, labels, domains, and ranges.
3. Hash the manifest and every registered `.ttl`, `.obda`, `.sparql`, and
   properties artifact with SHA-256. Store the hashes as ontology-artifact
   provenance.
4. Generate only parameterized Cypher and use a strict label/relationship
   allowlist. Do not interpolate manifest values into Cypher identifiers.
5. Add a `--dry-run` mode that writes or displays the generated scripts without
   connecting to Neo4j.

**Exit criteria:** the generator deterministically produces identical Cypher
for an unchanged manifest and validates all artifact paths before connecting.

## Phase 2: Schema and Safe Ingestion

1. Generate `IF NOT EXISTS` constraints for `Ontology.ontology_id`,
   `KnowledgeBase.kb_id`, and scoped `OntologyClass`/`OntologyProperty` IRIs.
2. Add indexes for ontology ID, IRI, local name, artifact path, and ingestion
   run status.
3. Run schema creation separately from content ingestion. Fail before writes if
   an existing ontology ID has a different manifest hash unless an explicit
   `--replace-version` workflow is used.
4. Use `MERGE` for all graph identities and `ON CREATE SET`/`ON MATCH SET` for
   timestamps and safe metadata refreshes.
5. Write an `IngestionRun` record before content writes; mark it `succeeded` or
   `failed` with an error summary on completion.

**Exit criteria:** two runs of the same manifest create no duplicate nodes or
relationships and preserve the original ontology ID.

## Phase 3: Neo4j Connection and Execution

1. Reuse the repository's `neo4j` Python driver and existing explicit database
   configuration path; do not introduce a second connection implementation.
2. Add a command that accepts `--manifest`, `--neo4j-uri`, `--neo4j-user`,
   `--neo4j-password`, and `--neo4j-database`. Environment variables may
   supply values, but command arguments take precedence.
3. Run a connection check against the selected database before applying schema
   or content statements.
4. Use transaction batches for artifact and semantic declarations. Keep batch
   sizes configurable and record their counts on the ingestion run.
5. Do not run a global reset. A rollback or cleanup command must delete only
   nodes and relationships scoped to the selected `ontology_id`.

**Exit criteria:** a local Neo4j Community database contains the ontology graph
and a scoped cleanup leaves unrelated databases and ontology versions intact.

## Phase 4: Validation and Acceptance Queries

Generate and run these parameterized checks after ingestion:

```cypher
MATCH (ontology:Ontology {ontology_id: $ontology_id})
OPTIONAL MATCH (ontology)-[:DECLARES_CLASS]->(class:OntologyClass)
OPTIONAL MATCH (ontology)-[:DECLARES_PROPERTY]->(property:OntologyProperty)
RETURN ontology.ontology_id, count(DISTINCT class) AS classes,
       count(DISTINCT property) AS properties
```

```cypher
MATCH (ontology:Ontology {ontology_id: $ontology_id})
MATCH (ontology)-[:HAS_ARTIFACT]->(artifact:OntologyArtifact)
RETURN artifact.path, artifact.sha256, artifact.kind
ORDER BY artifact.path
```

```cypher
MATCH (property:OntologyProperty {ontology_id: $ontology_id})
WHERE property.property_kind = 'object'
OPTIONAL MATCH (property)-[:HAS_DOMAIN]->(domain:OntologyClass)
OPTIONAL MATCH (property)-[:HAS_RANGE]->(range:OntologyClass)
RETURN property.local_name, domain.local_name, range.local_name
ORDER BY property.local_name
```

Compare semantic counts and ontology IRIs from Neo4j with the parsed Turtle.
Run Ontop validation and every manifest-registered SPARQL acceptance query as
a separate check; Ontop validates the mapping contract, while Neo4j validates
the materialized metadata graph.

**Exit criteria:** all generated Cypher checks return expected counts, all
artifact hashes match disk, and the Ontop checks remain green.

## Phase 5: Librarian and MCP Read Access

1. Add a separate read-only Neo4j client to `librarian_server.py`; do not reuse
   `commit_to_arangodb` or silently route Neo4j requests to ArangoDB.
2. Add MCP tools for `get_ontology`, `list_ontology_artifacts`,
   `list_ontology_classes`, and `get_ontology_property`.
3. Require an `ontology_id` parameter for every graph tool and parameterize all
   Cypher queries.
4. Return provenance fields and artifact hashes with semantic results.
5. Leave mutation tools disabled. Any future mutation requires authorization,
   an audit record, idempotency key, and explicit relationship/operation
   allowlist.

**Exit criteria:** GitHub Copilot can use the librarian MCP server to retrieve
the `salt.manufacturing.v1.0` ontology, its artifacts, and a property with its
domain/range evidence.

## Tests

- Unit tests for manifest parsing, deterministic script generation, Turtle
  extraction, SHA-256 provenance, and Cypher parameterization.
- Integration tests against Neo4j Community for constraints, first ingest,
  repeat ingest, different-version coexistence, and scoped cleanup.
- MCP tests that assert each read tool requires `ontology_id`, makes no write,
  and returns ontology provenance.
- Regression tests ensuring SAP SALT reference data is rejected unless its
  manifest source policy changes through the approved review process.

## Non-Goals

- Ingesting the full SAP SALT transactional dataset.
- Translating arbitrary SPARQL to Cypher.
- Treating Ontop as a Neo4j import engine.
- Enabling MCP or librarian graph writes in this phase.