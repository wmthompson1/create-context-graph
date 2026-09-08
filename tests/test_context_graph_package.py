"""Tests for the snapshot-driven manufacturing context-graph package."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from create_context_graph.context_graph_package import render_context_graph_package, write_context_graph_package
from create_context_graph.context_graph_reasoning import (
    MANUFACTURING_REASONING_PROMPT,
    execute_reasoning_strategy,
    load_reasoning_package,
)


def test_renders_deterministic_v11_context_graph_package(tmp_path):
    snapshot = {
        "ontology": {"ontology_id": "salt.manufacturing.v1.1", "ontology_iri": "https://example.org/ontology/salt/manufacturing/v1.1"},
        "classes": [{"local_name": item, "label": item} for item in ["WorkOrder", "BillOfMaterials", "Machine", "WorkCenter", "Part", "Supplier", "MaterialRequirement", "ProductionEvent"]],
        "properties": [
            {"local_name": "hasBillOfMaterials", "label": "has bill of materials", "property_kind": "object", "domains": ["#WorkOrder"], "ranges": ["#BillOfMaterials"]},
            {"local_name": "definesRequirement", "label": "defines requirement", "property_kind": "object", "domains": ["#BillOfMaterials"], "ranges": ["#MaterialRequirement"]},
            {"local_name": "requiresPart", "label": "requires part", "property_kind": "object", "domains": ["#MaterialRequirement"], "ranges": ["#Part"]},
            {"local_name": "usesMachine", "label": "uses machine", "property_kind": "object", "domains": ["#ProductionEvent"], "ranges": ["#Machine"]},
            {"local_name": "executesWorkOrder", "label": "executes work order", "property_kind": "object", "domains": ["#ProductionEvent"], "ranges": ["#WorkOrder"]},
            {"local_name": "suppliesPart", "label": "supplies part", "property_kind": "object", "domains": ["#SupplyCommitment"], "ranges": ["#Part"]},
            {"local_name": "committedBy", "label": "committed by", "property_kind": "object", "domains": ["#SupplyCommitment"], "ranges": ["#Supplier"]},
        ],
    }
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

    first = render_context_graph_package(snapshot_path)
    second = render_context_graph_package(snapshot_path)
    hashes = write_context_graph_package(snapshot_path, tmp_path / "context-graph" )

    assert first == second
    assert set(first) == {"domain.yaml", "schema.cypher", "tools/manufacturing-tools.yaml", "reasoning/strategies.yaml", "ingestion/document-rules.yaml", "validation/package-contract.json"}
    assert "production_lineage" in first["reasoning/strategies.yaml"]
    assert "gds." not in first["reasoning/strategies.yaml"]
    assert "RoutingStep" not in first["reasoning/strategies.yaml"]
    assert "MATCH (node:WorkOrder)" in first["tools/manufacturing-tools.yaml"]
    assert len(hashes) == 6


async def test_dispatches_only_registered_read_only_reasoning_strategies(tmp_path):
    catalog = tmp_path / "strategies.yaml"
    catalog.write_text("""ontology_id: salt.manufacturing.v1.1
execution:
  engine: parameterized_read_only_cypher
  max_hops: 4
strategies:
  - name: supply_coverage
    purpose: Find explicit commitments.
    parameters: [part_id]
    cypher: MATCH (part:Part) WHERE part.ontology_id = $ontology_id AND part.id = $part_id RETURN part
""", encoding="utf-8")
    package = load_reasoning_package(catalog)
    captured = {}

    async def execute_cypher(query, parameters):
        captured.update(query=query, parameters=parameters)
        return [{"part": "P-1"}]

    result = await execute_reasoning_strategy(package, "supply_coverage", {"part_id": "P-1"}, execute_cypher)

    assert result["evidence"] == [{"part": "P-1"}]
    assert captured["parameters"] == {"ontology_id": "salt.manufacturing.v1.1", "part_id": "P-1"}
    with pytest.raises(ValueError, match="unregistered"):
        await execute_reasoning_strategy(package, "unknown", {}, execute_cypher)


def test_rejects_write_capable_or_unscoped_reasoning_strategy(tmp_path):
    catalog = tmp_path / "strategies.yaml"
    catalog.write_text("""ontology_id: salt.manufacturing.v1.1
execution:
  engine: parameterized_read_only_cypher
  max_hops: 4
strategies:
  - name: unsafe
    parameters: []
    cypher: CREATE (:Part)
""", encoding="utf-8")

    with pytest.raises(ValueError, match="read-only"):
        load_reasoning_package(catalog)


def test_manufacturing_v12_extensions_are_present():
    spec = Path("manufacturing-context-graph/context-graph/manufacturing/domain.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(spec)

    supplier_props = {p["name"] for p in next(e for e in data["entity_types"] if e["label"] == "Supplier")["properties"]}
    schedule_props = {p["name"] for p in next(e for e in data["entity_types"] if e["label"] == "ScheduleSlot")["properties"]}
    work_order_props = {p["name"] for p in next(e for e in data["entity_types"] if e["label"] == "WorkOrder")["properties"]}
    event_props = {p["name"] for p in next(e for e in data["entity_types"] if e["label"] == "ProductionEvent")["properties"]}

    assert {"risk_score", "on_time_delivery_pct", "quality_score", "compliance_status"} <= supplier_props
    assert {"planned_capacity", "remaining_capacity", "shift_id", "work_center_role"} <= schedule_props
    assert {"lifecycle_stage"} <= work_order_props
    assert {"operator", "shift", "reason_code", "event_type"} <= event_props

    strategy_data = yaml.safe_load(Path("manufacturing-context-graph/context-graph/manufacturing/reasoning/strategies.yaml").read_text(encoding="utf-8"))
    strategy_names = {item["name"] for item in strategy_data["strategies"]}
    assert {"supplier_risk_assessment", "schedule_capacity_feasibility", "supplier_performance_trends", "workorder_lifecycle_reasoning", "production_shift_analysis"} <= strategy_names


@pytest.mark.parametrize("strategy_name, parameters", [
    ("bom_requirements", {"work_order_id": "WO-1"}),
    ("schedule_contention", {"work_center_id": "WC-1", "window_start": "2026-01-01T08:00:00", "window_end": "2026-01-01T16:00:00"}),
    ("production_lineage", {"part_id": "P-1"}),
    ("supply_coverage", {"part_id": "P-1"}),
])
async def test_manufacturing_strategies_return_only_executor_evidence(strategy_name, parameters):
    package = load_reasoning_package("context-graph/manufacturing/reasoning/strategies.yaml")
    observed = [{"node_id": "evidence-1", "relationship_type": "EXPLICIT"}]

    async def execute_cypher(query, scoped_parameters):
        assert "$ontology_id" in query
        assert scoped_parameters["ontology_id"] == "salt.manufacturing.v1.1"
        return observed

    async def execute_tool(tool_name, scoped_parameters):
        assert tool_name == "get_bom_components"
        assert scoped_parameters["ontology_id"] == "salt.manufacturing.v1.1"
        return observed

    result = await execute_reasoning_strategy(
        package, strategy_name, parameters, execute_cypher, execute_tool,
    )

    assert result["evidence"] == observed
    assert result["reasoning_contract"] == "evidence_only"


async def test_reasoning_never_infers_evidence_when_executor_returns_none():
    package = load_reasoning_package("context-graph/manufacturing/reasoning/strategies.yaml")

    async def execute_cypher(query, scoped_parameters):
        return []

    result = await execute_reasoning_strategy(
        package, "supply_coverage", {"part_id": "P-1"}, execute_cypher,
    )

    assert result["evidence"] == []
    assert "Do not infer" in MANUFACTURING_REASONING_PROMPT