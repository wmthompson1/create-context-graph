from __future__ import annotations

from pathlib import Path

import yaml


BASE = Path("my-mrp-kb/mfgq-extension")


def test_mfgq_ontology_hardening_has_required_domains_and_provenance():
    ttl = (BASE / "ontology/mfgq.ttl").read_text(encoding="utf-8")

    assert "mfgq:Nonconformance a owl:Class" in ttl and "rdfs:subClassOf prov:Activity" in ttl
    assert "mfgq:severity a owl:ObjectProperty" in ttl
    assert "rdfs:domain mfgq:Nonconformance" in ttl and "rdfs:range mfgq:Severity" in ttl
    assert "mfgq:status a owl:ObjectProperty" in ttl
    assert "rdfs:domain mfgq:Nonconformance" in ttl and "rdfs:range mfgq:Status" in ttl
    assert "mfgq:sourceSystem a owl:DatatypeProperty" in ttl
    assert "mfgq:sourceId a owl:DatatypeProperty" in ttl
    assert "mfgq:sourceRecord a owl:DatatypeProperty" in ttl
    assert "mfgq:hasDisposition a owl:ObjectProperty" in ttl
    assert "rdfs:domain mfgq:Nonconformance" in ttl and "rdfs:range mfgq:Disposition" in ttl


def test_mfgq_shapes_cover_required_quality_constraints():
    shapes = (BASE / "shacl/mfgq-shapes.ttl").read_text(encoding="utf-8")

    assert "sh:targetClass mfgq:Nonconformance" in shapes
    assert "sh:path mfgq:affectedPart" in shapes
    assert "sh:path mfgq:hasNonconformity" in shapes
    assert "sh:path mfgq:detectedBy" in shapes
    assert "Closed nonconformance must have a disposition." in shapes
    assert "sh:path mfgq:value" in shapes


def test_mfgq_quality_tool_set_is_read_only_and_declarative():
    tool_doc = (BASE / "neo4j/mfgq-quality-tools.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(tool_doc)

    assert "tools" in data
    assert len(data["tools"]) >= 5
    assert all("MATCH" in tool["cypher"].upper() for tool in data["tools"])
    assert all("CREATE" not in tool["cypher"].upper() for tool in data["tools"])
    assert all("MERGE" not in tool["cypher"].upper() for tool in data["tools"])
    assert all("SET" not in tool["cypher"].upper() for tool in data["tools"])
