"""Tests for manifest-driven Neo4j ontology ingestion."""

from __future__ import annotations

import json

import pytest

from create_context_graph.ontology_ingest import (
    artifact_records,
    generate_scripts,
    load_manifest,
    parse_ontology,
    promote_regenerated_artifacts,
    record_regeneration_provenance,
    render_regenerated_artifacts,
)


@pytest.fixture
def ontology_manifest(tmp_path):
    (tmp_path / "ontology.ttl").write_text(
        """@prefix ex: <https://example.org/ontology/test/v1.0#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://example.org/ontology/test/v1.0> a owl:Ontology .
ex:Order a owl:Class ; rdfs:label "Order" .
ex:Part a owl:Class ; rdfs:label "Part" .
ex:requiresPart a owl:ObjectProperty ; rdfs:domain ex:Order ; rdfs:range ex:Part .
""",
        encoding="utf-8",
    )
    (tmp_path / "mapping.obda").write_text("[MappingDeclaration] @collection [[]]", encoding="utf-8")
    (tmp_path / "smoke.sparql").write_text("SELECT * WHERE {}", encoding="utf-8")
    (tmp_path / "acceptance.sparql").write_text("ASK {}", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({
        "ontology_id": "salt.manufacturing.v1.0",
        "ontology_iri": "https://example.org/ontology/test/v1.0",
        "knowledge_base": {"id": "test-kb", "label": "Test KB", "document_root": ".."},
        "artifacts": {
            "ontology": "ontology.ttl",
            "mapping": "mapping.obda",
            "smoke_query": "smoke.sparql",
            "acceptance_queries": ["acceptance.sparql"],
        },
        "source_policy": {"sap_salt_data": "reference-only"},
    }), encoding="utf-8")
    return manifest_path


def test_parses_versioned_manifest_and_rdf_terms(ontology_manifest):
    manifest = load_manifest(ontology_manifest)
    classes, properties = parse_ontology(manifest)

    assert manifest.ontology_id == "salt.manufacturing.v1.0"
    assert [item.local_name for item in classes] == ["Order", "Part"]
    assert properties[0].local_name == "requiresPart"
    assert properties[0].domains[-1].endswith("#Order")
    assert properties[0].ranges[-1].endswith("#Part")


def test_generates_parameterized_scripts_and_artifact_hashes(ontology_manifest):
    manifest = load_manifest(ontology_manifest)
    scripts = generate_scripts(manifest)
    artifacts = artifact_records(manifest)

    assert set(scripts) == {"schema", "ingest", "relationships", "provenance"}
    assert "$ontology_id" in scripts["ingest"].read_text(encoding="utf-8")
    assert "HAS_DOMAIN" in scripts["relationships"].read_text(encoding="utf-8")
    assert all(len(item["sha256"]) == 64 for item in artifacts)


def test_rejects_non_versioned_ontology_identifier(ontology_manifest):
    data = json.loads(ontology_manifest.read_text(encoding="utf-8"))
    data["ontology_id"] = "manufacturing"
    ontology_manifest.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="ontology_id"):
        load_manifest(ontology_manifest)


def test_renders_deterministic_artifacts_from_snapshot(ontology_manifest):
    snapshot_path = ontology_manifest.parent / "ontology.snapshot.json"
    snapshot_path.write_text(json.dumps({
        "ontology": {
            "ontology_id": "salt.manufacturing.v1.0",
            "ontology_iri": "https://example.org/ontology/test/v1.0",
            "version": "v1.0",
        },
        "classes": [
            {"iri": "https://example.org/ontology/test/v1.0#Part", "local_name": "Part", "label": "Part"},
            {"iri": "https://example.org/ontology/test/v1.0#Order", "local_name": "Order", "label": "Order"},
        ],
        "properties": [{
            "iri": "https://example.org/ontology/test/v1.0#requiresPart",
            "local_name": "requiresPart",
            "label": "requires part",
            "property_kind": "object",
            "domains": ["https://example.org/ontology/test/v1.0#Order"],
            "ranges": ["https://example.org/ontology/test/v1.0#Part"],
        }],
        "source_policy": [{"usage_status": "Reference-only pending license review"}],
    }), encoding="utf-8")

    first = render_regenerated_artifacts(snapshot_path, ontology_manifest)
    second = render_regenerated_artifacts(snapshot_path, ontology_manifest)

    assert first["artifacts"] == second["artifacts"]
    turtle = first["artifacts"]["ontology.ttl"]
    assert turtle.index("saltmfg:Order") < turtle.index("saltmfg:Part")
    assert "owl:ObjectProperty" in turtle
    obda = first["artifacts"]["mapping.obda"]
    assert "mappingId\tclass-order" in obda
    assert "synthetic_join_row" in obda


def test_renders_datatype_property_mapping_from_snapshot(ontology_manifest):
    snapshot_path = ontology_manifest.parent / "ontology.snapshot.json"
    snapshot_path.write_text(json.dumps({
        "ontology": {
            "ontology_id": "salt.manufacturing.v1.0",
            "ontology_iri": "https://example.org/ontology/test/v1.0",
            "version": "v1.0",
        },
        "classes": [{
            "iri": "https://example.org/ontology/test/v1.0#Order",
            "local_name": "Order",
            "label": "Order",
        }],
        "properties": [{
            "iri": "https://example.org/ontology/test/v1.0#orderNumber",
            "local_name": "orderNumber",
            "label": "order number",
            "property_kind": "datatype",
            "domains": ["https://example.org/ontology/test/v1.0#Order"],
            "ranges": [],
        }],
        "source_policy": [{"usage_status": "Reference-only pending license review"}],
    }), encoding="utf-8")

    rendered = render_regenerated_artifacts(snapshot_path, ontology_manifest)

    assert "owl:DatatypeProperty" in rendered["artifacts"]["ontology.ttl"]
    assert "mappingId\tdatatype-ordernumber-order" in rendered["artifacts"]["mapping.obda"]


def test_regeneration_provenance_requires_every_generated_hash(ontology_manifest):
    manifest = load_manifest(ontology_manifest)
    with pytest.raises(ValueError, match="missing regenerated hash"):
        record_regeneration_provenance(
            ontology_manifest, "snapshot-hash", {}, "neo4j://unused", "neo4j", "unused",
        )


def test_promotes_complete_staged_directory(ontology_manifest, tmp_path):
    destination = tmp_path / "canonical"
    staging = tmp_path / "staging"
    destination.mkdir()
    staging.mkdir()
    (destination / "manifest.json").write_text("old manifest", encoding="utf-8")
    (destination / "ontology.ttl").write_text("old ontology", encoding="utf-8")
    (staging / "manifest.json").write_text("preserved manifest", encoding="utf-8")
    (staging / "ontology.ttl").write_text("new ontology", encoding="utf-8")
    (staging / "mapping.obda").write_text("new mapping", encoding="utf-8")

    hashes = promote_regenerated_artifacts(staging, destination)

    assert (destination / "manifest.json").read_text(encoding="utf-8") == "preserved manifest"
    assert (destination / "ontology.ttl").read_text(encoding="utf-8") == "new ontology"
    assert (destination / "mapping.obda").read_text(encoding="utf-8") == "new mapping"
    assert not staging.exists()
    assert set(hashes) == {"ontology.ttl", "mapping.obda"}