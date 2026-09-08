from __future__ import annotations

from pathlib import Path

import yaml


BASE = Path("my-mrp-kb/mfgq-extension")


def test_mfgq_reasoning_query_pack_is_read_only_and_evidence_bound():
    query_pack = BASE / "neo4j/mfgq-quality-reasoning.yaml"
    assert query_pack.exists()

    data = yaml.safe_load(query_pack.read_text(encoding="utf-8"))
    assert data["read_only"] is True
    assert data["evidence_bound"] is True

    names = {item["name"] for item in data["queries"]}
    assert {"open_ncrs_by_plant_material", "supplier_linked_defects", "work_order_quality_impact"}.issubset(names)

    for item in data["queries"]:
        cypher = item["cypher"].upper()
        assert "CREATE" not in cypher
        assert "MERGE" not in cypher
        assert "SET" not in cypher
        assert "DELETE" not in cypher
        assert "MATCH (NC:NONCONFORMANCE" in cypher or "MATCH (NC:NONCONFORMANCE" in cypher or "MATCH (NC:NONCONFORMANCE" in cypher or "MATCH (NC:NONCONFORMANCE" in cypher
        assert "$ONTOLOGY_ID" in item["cypher"] or "$ontology_id" in item["cypher"]
