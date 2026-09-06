"""Tests for manifest-driven Neo4j ontology ingestion."""

from __future__ import annotations

import json

import pytest

from create_context_graph.ontology_ingest import (
    artifact_records,
    generate_scripts,
    load_manifest,
    parse_ontology,
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