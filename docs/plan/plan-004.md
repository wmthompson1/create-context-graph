# Plan 004: Round-Trip Ontology Regeneration (v1.0 to v1.0-R1)

## Decision

Regenerate the canonical SALT manufacturing ontology artifacts from the
version-scoped Neo4j snapshot produced by Plan 003. The regeneration reads
metadata only: ontology identity, classes, properties, domain/range evidence,
artifact provenance, source policy, and ingestion-run history. It must not
read, infer, or materialize SAP SALT source data, CDS metadata, transactional
content, or external schemas.

`v1.0-R1` identifies a regeneration run, not a new ontology version. The
canonical ontology ID remains `salt.manufacturing.v1.0`, its IRI remains
`https://example.org/ontology/salt/manufacturing/v1.0`, and all regenerated
files remain under `my-mrp-kb/ontology/salt/manufacturing/v1.0/`.

## Inputs

- `ontology.snapshot.json` generated from Neo4j by Plan 003.
- Canonical `manifest.json` for `salt.manufacturing.v1.0`.
- Neo4j provenance required to create the regeneration run and register
	regenerated artifact hashes.

The snapshot is the semantic source for artifact generation. The manifest
supplies the output names, canonical location, Ontop image contract, and
source-policy boundary. The original Turtle must not be parsed to reconstruct
classes or properties.

## Outputs

The regeneration command deterministically replaces these canonical artifact
files:

```text
salt-manufacturing.ttl
salt-manufacturing.obda
salt-manufacturing.sparql
ontop.properties
acceptance/lineage.sparql
acceptance/provenance.sparql
acceptance/semantics.sparql
```

It also emits a deterministic `regeneration-report.json` containing the
ontology ID, snapshot SHA-256, generated artifact SHA-256 values, validation
results, and regeneration-run ID. The report contains no credentials or source
data.

## Generation Contract

### Determinism

- Sort classes, properties, domains, ranges, and artifacts by stable IRI or
	path before rendering.
- Use UTF-8, LF line endings, fixed indentation, and a final newline.
- Do not emit timestamps, random identifiers, machine paths, or query-result
	ordering into generated artifacts.
- Use the snapshot's ontology IRI and the manifest's stable ontology ID;
	reject a mismatch before modifying files.
- The generated report may contain run timestamps, but those values must not
	affect the generated ontology artifacts or their hashes.

### Turtle

- Render an `owl:Ontology` header from the snapshot ontology IRI, stable ID,
	and version.
- Render each `classes[]` item as an `owl:Class` with its stored label.
- Render each `properties[]` item as `owl:ObjectProperty` or
	`owl:DatatypeProperty` from `property_kind`.
- Render sorted `domains[]` and `ranges[]` as `rdfs:domain` and `rdfs:range`.
- Fail if an IRI lies outside the canonical ontology namespace or a property
	lacks a supported kind.

### OBDA

- Use only synthetic, in-memory H2 relations derived from snapshot terms.
- Generate one deterministic synthetic table mapping for each class, a scalar
	column mapping for each datatype property, and a synthetic join mapping for
	each object property.
- Prefix generated mappings with the stable `salt.manufacturing.v1.0`
	namespace and include the canonical version in the header.
- Do not reference SAP tables, CDS views, external JDBC endpoints, or inferred
	relational structures.

### SPARQL and Ontop Properties

- Regenerate the smoke query plus lineage, provenance, and semantics acceptance
	queries from the snapshot and manifest.
- Queries must cover class/property existence, property domain/range evidence,
	ontology IRI and version, artifact count, and ingestion-run count.
- Regenerate `ontop.properties` with the approved synthetic datasource:

```properties
jdbc.url=jdbc:h2:mem:kb
jdbc.driver=org.h2.Driver
```

## Command and Execution Order

Add `scripts/regenerate_artifacts.py` with this interface:

```powershell
.\.venv\Scripts\python.exe scripts\regenerate_artifacts.py `
	--snapshot .\my-mrp-kb\ontology\salt\manufacturing\v1.0\ontology.snapshot.json `
	--manifest .\my-mrp-kb\ontology\salt\manufacturing\v1.0\manifest.json `
	--output-dir .\my-mrp-kb\ontology\salt\manufacturing\v1.0
```

1. Load and validate the snapshot and manifest before writing files.
2. Verify the snapshot ontology ID, IRI, version, and source policy match the
	 manifest; reject unapproved policy status.
3. Render all artifacts in memory and compute their SHA-256 values.
4. Write each artifact atomically into the canonical output directory.
5. Run RDFLib Turtle parsing and `ontop.ps1 validate`.
6. Run the manifest-registered smoke and acceptance SPARQL queries through
	 Ontop.
7. Only after all local validation succeeds, create an `IngestionRun` with
	 `run_type = 'regeneration'` and `status = 'started'` in Neo4j.
8. Upsert the regenerated `OntologyArtifact` checksums, link them to the
	 ontology, and add `(run)-[:USED_ARTIFACT]->(artifact)` relationships.
9. Link the run to the ontology with `[:INGESTED]`, then set its status to
	 `regenerated`. On a Neo4j write failure after run creation, set status to
	 `failed` with a bounded error summary.

Regeneration must not create or update `Ontology`, `OntologyClass`,
`OntologyProperty`, `KnowledgeBase`, `SourcePolicy`, `DECLARES_*`,
`HAS_DOMAIN`, or `HAS_RANGE` records.

## Validation and Idempotence

- Run regeneration twice from the unchanged snapshot and manifest.
- Assert all generated artifact bytes and SHA-256 values are identical between
	runs.
- Assert RDFLib parses the generated Turtle.
- Assert Ontop validates the OBDA/properties pair and executes every generated
	SPARQL query.
- Assert Neo4j records one additional successful regeneration run per command,
	while ontology metadata, class count, property count, and semantic
	relationships remain unchanged.
- Assert every generated artifact node has the current checksum and is linked
	to the associated regeneration run.

## Tests

- Unit tests for snapshot/manifest identity validation, deterministic rendering,
	stable ordering, and SHA-256 output.
- Unit tests rejecting SAP/CDS/table references and unsupported property kinds.
- RDFLib tests for regenerated Turtle classes and domain/range statements.
- Ontop integration test for the regenerated OBDA, properties, smoke query, and
	acceptance queries.
- Mocked Neo4j tests for regeneration-run ordering, artifact provenance, and
	failure status handling.
- Integration test that runs regeneration twice and verifies artifact hashes are
	unchanged, metadata remains immutable, and only the run count increments.

## Non-Goals

- Ingesting SAP SALT source rows, source descriptions, CDS artifacts, or
	transactional data.
- Creating a new ontology version or changing `salt.manufacturing.v1.0`.
- Inferring a production relational model from ontology metadata.
- Mutating ontology semantics during regeneration.
- Enabling librarian or MCP graph writes.

## Completion Criteria

Plan 004 is complete when an unchanged Plan 003 snapshot produces byte-stable
canonical ontology artifacts, all local Ontop and RDF validations pass, and
Neo4j records checksummed artifact provenance plus a successful regeneration
run without changing ontology metadata.
