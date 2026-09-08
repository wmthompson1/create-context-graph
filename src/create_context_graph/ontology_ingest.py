"""Manifest-driven ingestion of RDF ontology metadata into Neo4j."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rdflib import Graph, OWL, RDF, RDFS, URIRef


@dataclass(frozen=True)
class OntologyTerm:
    """A class or property declared by an RDF ontology."""

    iri: str
    local_name: str
    label: str
    property_kind: str | None = None
    domains: tuple[str, ...] = ()
    ranges: tuple[str, ...] = ()


@dataclass(frozen=True)
class OntologyManifest:
    """Validated ontology manifest and paths resolved from its directory."""

    path: Path
    ontology_id: str
    ontology_iri: str
    knowledge_base: dict[str, str]
    artifacts: dict[str, Any]
    source_policy: dict[str, str]

    @property
    def root(self) -> Path:
        return self.path.parent


_ONTOLOGY_ID_RE = re.compile(
    r"^[a-z][a-z0-9]*\.[a-z][a-z0-9-]*\.v[0-9]+(?:\.[0-9]+)*$"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: str | Path) -> OntologyManifest:
    """Load the canonical manifest and verify every registered artifact exists."""
    manifest_path = Path(path).resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    ontology_id = data.get("ontology_id", "")
    if not _ONTOLOGY_ID_RE.fullmatch(ontology_id):
        raise ValueError("ontology_id must be a namespace.domain.version identifier")
    ontology_iri = data.get("ontology_iri", "")
    if not ontology_iri:
        raise ValueError("manifest requires ontology_iri")
    artifacts = data.get("artifacts", {})
    required = ("ontology", "mapping", "smoke_query", "acceptance_queries")
    if any(key not in artifacts for key in required):
        raise ValueError("manifest is missing one or more required artifacts")
    artifact_paths = [artifacts["ontology"], artifacts["mapping"], artifacts["smoke_query"], *artifacts["acceptance_queries"]]
    missing = [item for item in artifact_paths if not (manifest_path.parent / item).is_file()]
    if missing:
        raise ValueError(f"manifest references missing artifacts: {', '.join(missing)}")
    return OntologyManifest(
        path=manifest_path,
        ontology_id=ontology_id,
        ontology_iri=ontology_iri,
        knowledge_base=data.get("knowledge_base", {}),
        artifacts=artifacts,
        source_policy=data.get("source_policy", {}),
    )


def parse_ontology(manifest: OntologyManifest) -> tuple[list[OntologyTerm], list[OntologyTerm]]:
    """Parse declared classes and properties from the manifest's Turtle ontology."""
    graph = Graph()
    graph.parse(manifest.root / manifest.artifacts["ontology"], format="turtle")

    def label(subject: URIRef) -> str:
        value = graph.value(subject, RDFS.label)
        return str(value) if value else _local_name(str(subject))

    classes = sorted(
        (
            OntologyTerm(str(subject), _local_name(str(subject)), label(subject))
            for subject in graph.subjects(RDF.type, OWL.Class)
        ),
        key=lambda item: item.iri,
    )
    properties: list[OntologyTerm] = []
    for property_type, kind in ((OWL.ObjectProperty, "object"), (OWL.DatatypeProperty, "datatype")):
        for subject in graph.subjects(RDF.type, property_type):
            properties.append(
                OntologyTerm(
                    str(subject),
                    _local_name(str(subject)),
                    label(subject),
                    kind,
                    tuple(sorted(str(value) for value in graph.objects(subject, RDFS.domain))),
                    tuple(sorted(str(value) for value in graph.objects(subject, RDFS.range))),
                )
            )
    return classes, sorted(properties, key=lambda item: item.iri)


def _local_name(iri: str) -> str:
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def artifact_records(manifest: OntologyManifest) -> list[dict[str, str]]:
    """Return checksummed provenance records for all registered artifacts."""
    entries = [
        (manifest.artifacts["ontology"], "ontology", "turtle"),
        (manifest.artifacts["mapping"], "mapping", "obda"),
        (manifest.artifacts["smoke_query"], "query", "sparql"),
    ]
    if "configuration" in manifest.artifacts:
        entries.append((manifest.artifacts["configuration"], "configuration", "properties"))
    entries.extend((path, "acceptance_query", "sparql") for path in manifest.artifacts["acceptance_queries"])
    return [
        {"path": path, "kind": kind, "format": file_format, "sha256": _sha256(manifest.root / path)}
        for path, kind, file_format in entries
    ]


def generate_scripts(manifest: OntologyManifest) -> dict[str, Path]:
    """Write deterministic parameterized Cypher artifacts next to the manifest."""
    output = {
        "schema": manifest.root / "schema.cypher",
        "ingest": manifest.root / "ingest.cypher",
        "relationships": manifest.root / "relationships.cypher",
        "provenance": manifest.root / "provenance.cypher",
    }
    scripts = {
        "schema": "\n".join([
            "CREATE CONSTRAINT ontology_id_unique IF NOT EXISTS FOR (n:Ontology) REQUIRE n.ontology_id IS UNIQUE;",
            "CREATE CONSTRAINT knowledge_base_id_unique IF NOT EXISTS FOR (n:KnowledgeBase) REQUIRE n.kb_id IS UNIQUE;",
            "CREATE CONSTRAINT ontology_class_key_unique IF NOT EXISTS FOR (n:OntologyClass) REQUIRE (n.ontology_id, n.iri) IS UNIQUE;",
            "CREATE CONSTRAINT ontology_property_key_unique IF NOT EXISTS FOR (n:OntologyProperty) REQUIRE (n.ontology_id, n.iri) IS UNIQUE;",
            "CREATE INDEX ontology_artifact_path IF NOT EXISTS FOR (n:OntologyArtifact) ON (n.ontology_id, n.path);",
            "CREATE INDEX ontology_class_local_name IF NOT EXISTS FOR (n:OntologyClass) ON (n.ontology_id, n.local_name);",
            "CREATE INDEX ontology_property_local_name IF NOT EXISTS FOR (n:OntologyProperty) ON (n.ontology_id, n.local_name);",
            "CREATE INDEX ingestion_run_status IF NOT EXISTS FOR (n:IngestionRun) ON (n.ontology_id, n.status);",
        ]) + "\n",
        "ingest": "\n".join([
            "MERGE (ontology:Ontology {ontology_id: $ontology_id})",
            "SET ontology.ontology_iri = $ontology_iri, ontology.namespace = $namespace, ontology.domain = $domain, ontology.version = $version, ontology.manifest_sha256 = $manifest_sha256",
            "MERGE (kb:KnowledgeBase {kb_id: $kb_id})",
            "SET kb.name = $kb_name, kb.document_root = $document_root",
            "MERGE (kb)-[:OWNS_ONTOLOGY]->(ontology);",
            "UNWIND $classes AS class",
            "MERGE (node:OntologyClass {ontology_id: $ontology_id, iri: class.iri})",
            "SET node.local_name = class.local_name, node.label = class.label",
            "WITH node MATCH (ontology:Ontology {ontology_id: $ontology_id})",
            "MERGE (ontology)-[:DECLARES_CLASS]->(node);",
            "UNWIND $properties AS property",
            "MERGE (node:OntologyProperty {ontology_id: $ontology_id, iri: property.iri})",
            "SET node.local_name = property.local_name, node.label = property.label, node.property_kind = property.property_kind",
            "WITH node MATCH (ontology:Ontology {ontology_id: $ontology_id})",
            "MERGE (ontology)-[:DECLARES_PROPERTY]->(node);",
        ]) + "\n",
        "relationships": "\n".join([
            "UNWIND $properties AS property",
            "MATCH (node:OntologyProperty {ontology_id: $ontology_id, iri: property.iri})",
            "UNWIND property.domains AS domain_iri",
            "MATCH (domain:OntologyClass {ontology_id: $ontology_id, iri: domain_iri})",
            "MERGE (node)-[:HAS_DOMAIN]->(domain);",
            "UNWIND $properties AS property",
            "MATCH (node:OntologyProperty {ontology_id: $ontology_id, iri: property.iri})",
            "UNWIND property.ranges AS range_iri",
            "MATCH (range:OntologyClass {ontology_id: $ontology_id, iri: range_iri})",
            "MERGE (node)-[:HAS_RANGE]->(range);",
        ]) + "\n",
        "provenance": "\n".join([
            "UNWIND $artifacts AS artifact",
            "MERGE (node:OntologyArtifact {ontology_id: $ontology_id, path: artifact.path})",
            "SET node.kind = artifact.kind, node.format = artifact.format, node.sha256 = artifact.sha256",
            "WITH node MATCH (ontology:Ontology {ontology_id: $ontology_id})",
            "MERGE (ontology)-[:HAS_ARTIFACT]->(node);",
            "MERGE (policy:SourcePolicy {ontology_id: $ontology_id, source_name: 'sap_salt_data'})",
            "SET policy.usage_status = $sap_salt_data",
            "WITH policy MATCH (ontology:Ontology {ontology_id: $ontology_id})",
            "MERGE (ontology)-[:GOVERNED_BY]->(policy);",
            "MATCH (run:IngestionRun {run_id: $run_id})",
            "UNWIND $artifacts AS artifact",
            "MATCH (node:OntologyArtifact {ontology_id: $ontology_id, path: artifact.path})",
            "MERGE (run)-[:USED_ARTIFACT]->(node);",
        ]) + "\n",
    }
    for name, path in output.items():
        path.write_text(scripts[name], encoding="utf-8")
    return output


def ingest_ontology(
    manifest_path: str | Path,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    neo4j_database: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generate scripts and optionally ingest one ontology version into Neo4j."""
    manifest = load_manifest(manifest_path)
    classes, properties = parse_ontology(manifest)
    scripts = generate_scripts(manifest)
    result = {"ontology_id": manifest.ontology_id, "classes": len(classes), "properties": len(properties), "scripts": {key: str(value) for key, value in scripts.items()}}
    if dry_run:
        return result

    from neo4j import GraphDatabase

    params = {
        "ontology_id": manifest.ontology_id,
        "ontology_iri": manifest.ontology_iri,
        "namespace": manifest.ontology_id.split(".", 2)[0],
        "domain": manifest.ontology_id.split(".", 2)[1],
        "version": manifest.ontology_id.split(".", 2)[2],
        "kb_id": manifest.knowledge_base["id"],
        "kb_name": manifest.knowledge_base["label"],
        "document_root": manifest.knowledge_base["document_root"],
        "classes": [term.__dict__ for term in classes],
        "properties": [term.__dict__ for term in properties],
        "artifacts": artifact_records(manifest),
        "sap_salt_data": manifest.source_policy.get("sap_salt_data", "unspecified"),
        "run_id": f"{manifest.ontology_id}:{datetime.now(UTC).isoformat()}",
        "started_at": datetime.now(UTC).isoformat(),
        "manifest_sha256": _sha256(manifest.path),
    }
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
    try:
        with driver.session(database=neo4j_database or None) as session:
            session.run("RETURN 1").consume()
            _run_script(session, scripts["schema"], params)
            collision = session.run(
                "MATCH (ontology:Ontology {ontology_id: $ontology_id}) "
                "WHERE ontology.manifest_sha256 IS NOT NULL "
                "AND ontology.manifest_sha256 <> $manifest_sha256 "
                "RETURN ontology.ontology_id AS ontology_id",
                params,
            ).single()
            if collision:
                raise ValueError(
                    f"ontology_id {manifest.ontology_id} already exists with a different manifest hash"
                )
            session.run(
                "MERGE (run:IngestionRun {run_id: $run_id}) "
                "SET run.ontology_id = $ontology_id, run.started_at = datetime($started_at), "
                "run.manifest_sha256 = $manifest_sha256, run.status = 'started'",
                params,
            ).consume()
            try:
                for name in ("ingest", "relationships", "provenance"):
                    _run_script(session, scripts[name], params)
                session.run(
                    "MATCH (run:IngestionRun {run_id: $run_id}) "
                    "SET run.completed_at = datetime(), run.status = 'succeeded'",
                    params,
                ).consume()
            except Exception as exc:
                session.run(
                    "MATCH (run:IngestionRun {run_id: $run_id}) "
                    "SET run.completed_at = datetime(), run.status = 'failed', "
                    "run.error_summary = $error_summary",
                    {**params, "error_summary": str(exc)[:1000]},
                ).consume()
                raise
    finally:
        driver.close()
    return result


def _run_script(session: Any, script_path: Path, params: dict[str, Any]) -> None:
    """Execute the generated statements, which are delimited by semicolon-newline."""
    for statement in script_path.read_text(encoding="utf-8").split(";\n"):
        if statement.strip():
            session.run(statement, params).consume()


def extract_ontology_snapshot(
    ontology_id: str,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    output_path: str | Path,
    neo4j_database: str = "",
) -> dict[str, Any]:
    """Export one version-scoped ontology metadata graph as deterministic JSON."""
    if not _ONTOLOGY_ID_RE.fullmatch(ontology_id):
        raise ValueError("ontology_id must be a namespace.domain.version identifier")

    from neo4j import GraphDatabase

    params = {"ontology_id": ontology_id}
    queries = {
        "ontology": (
            "MATCH (kb:KnowledgeBase)-[:OWNS_ONTOLOGY]->(ontology:Ontology {ontology_id: $ontology_id}) "
            "RETURN ontology {.*} AS ontology, kb {.*} AS knowledge_base"
        ),
        "classes": (
            "MATCH (:Ontology {ontology_id: $ontology_id})-[:DECLARES_CLASS]->(class:OntologyClass) "
            "RETURN class {.*} AS class ORDER BY class.iri"
        ),
        "properties": (
            "MATCH (:Ontology {ontology_id: $ontology_id})-[:DECLARES_PROPERTY]->(property:OntologyProperty) "
            "OPTIONAL MATCH (property)-[:HAS_DOMAIN]->(domain:OntologyClass) "
            "OPTIONAL MATCH (property)-[:HAS_RANGE]->(range:OntologyClass) "
            "RETURN property {.*} AS property, collect(DISTINCT domain.iri) AS domains, "
            "collect(DISTINCT range.iri) AS ranges ORDER BY property.iri"
        ),
        "artifacts": (
            "MATCH (:Ontology {ontology_id: $ontology_id})-[:HAS_ARTIFACT]->(artifact:OntologyArtifact) "
            "RETURN artifact {.*} AS artifact ORDER BY artifact.path"
        ),
        "source_policy": (
            "MATCH (:Ontology {ontology_id: $ontology_id})-[:GOVERNED_BY]->(policy:SourcePolicy) "
            "RETURN policy {.*} AS policy ORDER BY policy.source_name"
        ),
        "ingestion_runs": (
            "MATCH (run:IngestionRun {ontology_id: $ontology_id}) "
            "RETURN run {.*} AS run ORDER BY run.started_at"
        ),
    }
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
    try:
        with driver.session(database=neo4j_database or None) as session:
            ontology_rows = [record.data() for record in session.run(queries["ontology"], params)]
            if not ontology_rows:
                raise ValueError(f"ontology_id {ontology_id} was not found")
            snapshot = {
                "ontology": ontology_rows[0]["ontology"],
                "knowledge_base": ontology_rows[0]["knowledge_base"],
                "classes": [record["class"] for record in session.run(queries["classes"], params)],
                "properties": [
                    {
                        **record["property"],
                        "domains": sorted(item for item in record["domains"] if item is not None),
                        "ranges": sorted(item for item in record["ranges"] if item is not None),
                    }
                    for record in session.run(queries["properties"], params)
                ],
                "artifacts": [record["artifact"] for record in session.run(queries["artifacts"], params)],
                "source_policy": [record["policy"] for record in session.run(queries["source_policy"], params)],
                "ingestion_runs": [record["run"] for record in session.run(queries["ingestion_runs"], params)],
            }
    finally:
        driver.close()

    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(snapshot, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {
        "ontology_id": ontology_id,
        "classes": len(snapshot["classes"]),
        "properties": len(snapshot["properties"]),
        "artifacts": len(snapshot["artifacts"]),
        "output": str(destination),
    }


def render_regenerated_artifacts(
    snapshot_path: str | Path,
    manifest_path: str | Path,
) -> dict[str, Any]:
    """Render canonical ontology artifacts from a Neo4j metadata snapshot."""
    manifest = load_manifest(manifest_path)
    snapshot = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    ontology = snapshot.get("ontology", {})
    if ontology.get("ontology_id") != manifest.ontology_id:
        raise ValueError("snapshot ontology_id does not match manifest")
    if ontology.get("ontology_iri") != manifest.ontology_iri:
        raise ValueError("snapshot ontology_iri does not match manifest")
    if ontology.get("version") != manifest.ontology_id.split(".", 2)[2]:
        raise ValueError("snapshot version does not match manifest ontology_id")
    if not any(
        policy.get("usage_status") == "Reference-only pending license review"
        for policy in snapshot.get("source_policy", [])
    ):
        raise ValueError("snapshot source policy is not approved for metadata-only regeneration")

    namespace = f"{manifest.ontology_iri}#"
    classes = _validated_snapshot_terms(snapshot.get("classes", []), namespace, "class")
    properties = _validated_snapshot_terms(snapshot.get("properties", []), namespace, "property")
    for property_term in properties:
        if property_term.get("property_kind") not in {"object", "datatype"}:
            raise ValueError(f"unsupported property kind: {property_term.get('property_kind')}")
        for iri in [*property_term.get("domains", []), *property_term.get("ranges", [])]:
            if not iri.startswith(namespace):
                raise ValueError(f"property domain or range is outside ontology namespace: {iri}")

    output_names = {
        "ontology": manifest.artifacts["ontology"],
        "mapping": manifest.artifacts["mapping"],
        "configuration": manifest.artifacts.get("configuration", "ontop.properties"),
        "smoke_query": manifest.artifacts["smoke_query"],
        "lineage": "acceptance/lineage.sparql",
        "provenance": "acceptance/provenance.sparql",
        "semantics": "acceptance/semantics.sparql",
    }
    rendered = {
        output_names["ontology"]: _render_turtle(manifest, classes, properties),
        output_names["mapping"]: _render_obda(manifest, classes, properties),
        output_names["configuration"]: "jdbc.url=jdbc:h2:mem:kb\njdbc.driver=org.h2.Driver\n",
        output_names["smoke_query"]: _render_smoke_query(manifest),
        output_names["lineage"]: _render_lineage_query(manifest, properties),
        output_names["provenance"]: _render_provenance_query(manifest),
        output_names["semantics"]: _render_semantics_query(manifest, classes, properties),
    }
    return {
        "ontology_id": manifest.ontology_id,
        "snapshot_sha256": _sha256(Path(snapshot_path)),
        "artifacts": dict(sorted(rendered.items())),
    }


def write_regenerated_artifacts(rendered: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    """Write rendered artifacts with stable UTF-8 and LF output."""
    destination = Path(output_dir).resolve()
    hashes: dict[str, str] = {}
    for relative_path, content in rendered["artifacts"].items():
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        hashes[relative_path] = _sha256(target)
    return hashes


def validate_staged_artifacts(staging_dir: str | Path, ontop_wrapper: str | Path) -> None:
    """Parse staged Turtle and validate all staged artifacts through Ontop."""
    staging_root = Path(staging_dir).resolve()
    turtle_path = next(staging_root.glob("*.ttl"), None)
    if turtle_path is None:
        raise ValueError("staged artifacts do not include a Turtle ontology")
    graph = Graph()
    graph.parse(turtle_path, format="turtle")
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(Path(ontop_wrapper).resolve()),
    ]
    completed = subprocess.run(
        [
            *command,
            "-Command",
            "validate",
            "-OntologyRoot",
            str(staging_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        output = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Ontop validation failed for staged artifacts: {output}")
    for query_path in sorted(staging_root.rglob("*.sparql")):
        completed = subprocess.run(
            [
                *command,
                "-Command",
                "query",
                "-Query",
                str(query_path.relative_to(staging_root)).replace("\\", "/"),
                "-OntologyRoot",
                str(staging_root),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            output = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"Ontop query failed for {query_path.name}: {output}")


def promote_regenerated_artifacts(staging_dir: str | Path, output_dir: str | Path) -> dict[str, str]:
    """Replace the validated ontology directory through a rename-and-rollback swap."""
    staging_root = Path(staging_dir).resolve()
    destination = Path(output_dir).resolve()
    backup = destination.with_name(f".{destination.name}.regeneration-backup")
    if backup.exists():
        raise FileExistsError(f"regeneration backup already exists: {backup}")
    os.replace(destination, backup)
    try:
        os.replace(staging_root, destination)
    except Exception:
        os.replace(backup, destination)
        raise
    shutil.rmtree(backup)
    hashes: dict[str, str] = {}
    for target in sorted(path for path in destination.rglob("*") if path.is_file()):
        relative_path = target.relative_to(destination)
        if relative_path.suffix in {".ttl", ".obda", ".sparql", ".properties"}:
            hashes[str(relative_path).replace("\\", "/")] = _sha256(target)
    return hashes


def record_regeneration_provenance(
    manifest_path: str | Path,
    snapshot_sha256: str,
    artifact_hashes: dict[str, str],
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    neo4j_database: str = "",
) -> dict[str, str]:
    """Record a completed artifact regeneration without changing ontology semantics."""
    manifest = load_manifest(manifest_path)
    artifacts = artifact_records(manifest)
    for artifact in artifacts:
        try:
            artifact["sha256"] = artifact_hashes[artifact["path"]]
        except KeyError as exc:
            raise ValueError(f"missing regenerated hash for {artifact['path']}") from exc

    from neo4j import GraphDatabase

    now = datetime.now(UTC).isoformat()
    params = {
        "ontology_id": manifest.ontology_id,
        "run_id": f"{manifest.ontology_id}:regeneration:{now}",
        "started_at": now,
        "snapshot_sha256": snapshot_sha256,
        "artifacts": artifacts,
    }
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
    try:
        with driver.session(database=neo4j_database or None) as session:
            ontology = session.run(
                "MATCH (ontology:Ontology {ontology_id: $ontology_id}) RETURN ontology.ontology_id AS ontology_id",
                params,
            ).single()
            if ontology is None:
                raise ValueError(f"ontology_id {manifest.ontology_id} was not found")
            session.run(
                "CREATE (run:IngestionRun {run_id: $run_id, ontology_id: $ontology_id, "
                "run_type: 'regeneration', status: 'started', started_at: datetime($started_at), "
                "snapshot_sha256: $snapshot_sha256})",
                params,
            ).consume()
            try:
                session.run(
                    "MATCH (ontology:Ontology {ontology_id: $ontology_id}) "
                    "MATCH (run:IngestionRun {run_id: $run_id}) "
                    "MERGE (run)-[:INGESTED]->(ontology) "
                    "WITH ontology, run "
                    "UNWIND $artifacts AS artifact "
                    "MERGE (node:OntologyArtifact {ontology_id: $ontology_id, path: artifact.path}) "
                    "SET node.kind = artifact.kind, node.format = artifact.format, node.sha256 = artifact.sha256 "
                    "MERGE (ontology)-[:HAS_ARTIFACT]->(node) "
                    "MERGE (run)-[:USED_ARTIFACT]->(node)",
                    params,
                ).consume()
                session.run(
                    "MATCH (run:IngestionRun {run_id: $run_id}) "
                    "SET run.completed_at = datetime(), run.status = 'regenerated'",
                    params,
                ).consume()
            except Exception as exc:
                session.run(
                    "MATCH (run:IngestionRun {run_id: $run_id}) "
                    "SET run.completed_at = datetime(), run.status = 'failed', "
                    "run.error_summary = $error_summary",
                    {**params, "error_summary": str(exc)[:1000]},
                ).consume()
                raise
    finally:
        driver.close()
    return {"run_id": params["run_id"], "status": "regenerated"}


def _validated_snapshot_terms(
    terms: list[dict[str, Any]], namespace: str, term_kind: str,
) -> list[dict[str, Any]]:
    validated = sorted((dict(term) for term in terms), key=lambda term: term["iri"])
    for term in validated:
        if not term.get("iri", "").startswith(namespace):
            raise ValueError(f"{term_kind} IRI is outside ontology namespace: {term.get('iri')}")
        if not term.get("local_name") or not term.get("label"):
            raise ValueError(f"{term_kind} requires local_name and label")
    return validated


def _render_turtle(
    manifest: OntologyManifest, classes: list[dict[str, Any]], properties: list[dict[str, Any]],
) -> str:
    version = manifest.ontology_id.split(".", 2)[2]
    lines = [
        f"@prefix saltmfg: <{manifest.ontology_iri}#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
        f"<{manifest.ontology_iri}> a owl:Ontology ;",
        f"    rdfs:label {json.dumps(f'SALT Manufacturing Ontology {version}')} ;",
        f"    rdfs:comment {json.dumps(f'ontology_id: {manifest.ontology_id}')} .",
        "",
    ]
    for term in classes:
        lines.extend([f"saltmfg:{term['local_name']} a owl:Class ;", f"    rdfs:label {json.dumps(term['label'])} .", ""])
    for term in properties:
        property_type = "owl:ObjectProperty" if term["property_kind"] == "object" else "owl:DatatypeProperty"
        predicates = [f"saltmfg:{term['local_name']} a {property_type}"]
        predicates.extend(f"rdfs:domain <{iri}>" for iri in sorted(term.get("domains", [])))
        predicates.extend(f"rdfs:range <{iri}>" for iri in sorted(term.get("ranges", [])))
        predicates.append(f"rdfs:label {json.dumps(term['label'])}")
        lines.append(" ;\n    ".join(predicates) + " .")
        lines.append("")
    return "\n".join(lines)


def _render_obda(
    manifest: OntologyManifest, classes: list[dict[str, Any]], properties: list[dict[str, Any]],
) -> str:
    lines = [
        "[PrefixDeclaration]",
        f":\t{manifest.ontology_iri}#",
        "",
        "[MappingDeclaration] @collection [[",
    ]
    for term in classes:
        mapping_id = f"class-{_mapping_name(term['local_name'])}"
        lines.extend([f"mappingId\t{mapping_id}", f"target\t\t<{manifest.ontology_iri}/synthetic/{term['local_name']}> a :{term['local_name']} .", "source\t\tSELECT 1 AS synthetic_row", ""])
    for term in properties:
        if term["property_kind"] == "datatype":
            for domain in sorted(term.get("domains", [])):
                lines.extend([
                    f"mappingId\tdatatype-{_mapping_name(term['local_name'])}-{_mapping_name(_local_name(domain))}",
                    f"target\t\t<{manifest.ontology_iri}/synthetic/{_local_name(domain)}> :{term['local_name']} {{value}} .",
                    f"source\t\tSELECT '{term['local_name']}' AS value",
                    "",
                ])
            continue
        for domain in sorted(term.get("domains", [])):
            for range_iri in sorted(term.get("ranges", [])):
                lines.extend([
                    f"mappingId\tobject-{_mapping_name(term['local_name'])}-{_mapping_name(_local_name(domain))}-{_mapping_name(_local_name(range_iri))}",
                    f"target\t\t<{manifest.ontology_iri}/synthetic/{_local_name(domain)}> :{term['local_name']} <{manifest.ontology_iri}/synthetic/{_local_name(range_iri)}> .",
                    "source\t\tSELECT 1 AS synthetic_join_row",
                    "",
                ])
    lines.append("]]" )
    return "\n".join(lines) + "\n"


def _render_smoke_query(manifest: OntologyManifest) -> str:
    return "\n".join([
        f"PREFIX saltmfg: <{manifest.ontology_iri}#>",
        "",
        "SELECT ?resource",
        "WHERE {",
        "  ?resource a saltmfg:KnowledgeBase .",
        "}",
        "ORDER BY ?resource",
        "",
    ])


def _render_lineage_query(manifest: OntologyManifest, properties: list[dict[str, Any]]) -> str:
    object_property = next((term for term in properties if term["property_kind"] == "object"), None)
    if object_property is None:
        return "ASK { }\n"
    return "\n".join([
        f"PREFIX saltmfg: <{manifest.ontology_iri}#>",
        "",
        "ASK {",
        f"  ?source saltmfg:{object_property['local_name']} ?target .",
        "}",
        "",
    ])


def _render_provenance_query(manifest: OntologyManifest) -> str:
    return "\n".join([
        "PREFIX owl: <http://www.w3.org/2002/07/owl#>",
        "",
        "ASK {",
        f"  <{manifest.ontology_iri}> a owl:Ontology .",
        "}",
        "",
    ])


def _render_semantics_query(
    manifest: OntologyManifest, classes: list[dict[str, Any]], properties: list[dict[str, Any]],
) -> str:
    checks = [f"  ?resource a saltmfg:{term['local_name']} ." for term in classes]
    checks.extend(f"  ?source saltmfg:{term['local_name']} ?target ." for term in properties)
    return "\n".join([
        f"PREFIX saltmfg: <{manifest.ontology_iri}#>",
        "",
        "SELECT ?resource ?source ?target",
        "WHERE {",
        *checks,
        "}",
        "",
    ])


def _mapping_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")