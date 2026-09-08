"""Generate metadata-only context-graph packages from ontology snapshots."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


_REQUIRED_TOOL_NAMES = (
    "get_work_order",
    "get_bom_components",
    "get_machine_status",
    "get_supplier_parts",
    "get_material_requirements",
    "get_production_events",
)


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _cypher_name(value: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", value.lower())


def _local_name(iri: str) -> str:
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _require_terms(snapshot: dict[str, Any]) -> None:
    classes = {item["local_name"] for item in snapshot["classes"]}
    properties = {item["local_name"] for item in snapshot["properties"]}
    missing_classes = {"WorkOrder", "BillOfMaterials", "Machine", "WorkCenter", "Part", "Supplier", "MaterialRequirement", "ProductionEvent"} - classes
    missing_properties = {"hasBillOfMaterials", "definesRequirement", "requiresPart", "usesMachine", "executesWorkOrder", "suppliesPart", "committedBy"} - properties
    if missing_classes or missing_properties:
        raise ValueError(f"snapshot lacks manufacturing context-graph terms: classes={sorted(missing_classes)}, properties={sorted(missing_properties)}")


def _tool_definitions(ontology_id: str) -> list[dict[str, Any]]:
    def scope(alias: str) -> str:
        return f"WHERE {alias}.ontology_id = $ontology_id"

    return [
        {"name": "get_work_order", "description": "Retrieve one scoped work order by its context-graph identifier.", "parameters": ["id"], "cypher": f"MATCH (node:WorkOrder) {scope('node')} AND node.id = $id RETURN node LIMIT 1"},
        {"name": "get_bom_components", "description": "Retrieve a work order's bill of materials, requirements, and required parts.", "parameters": ["work_order_id"], "cypher": f"MATCH (workOrder:WorkOrder) {scope('workOrder')} AND workOrder.id = $work_order_id MATCH (workOrder)-[:HAS_BILL_OF_MATERIALS]->(bom:BillOfMaterials)-[:DEFINES_REQUIREMENT]->(requirement:MaterialRequirement)-[:REQUIRES_PART]->(part:Part) WHERE bom.ontology_id = $ontology_id AND requirement.ontology_id = $ontology_id AND part.ontology_id = $ontology_id RETURN bom, requirement, part ORDER BY part.id"},
        {"name": "get_machine_status", "description": "Retrieve machines and their work centers, optionally by machine identifier.", "parameters": ["machine_id"], "cypher": f"MATCH (machine:Machine) {scope('machine')} AND ($machine_id IS NULL OR machine.id = $machine_id) OPTIONAL MATCH (machine)-[:HAS_WORK_CENTER]->(workCenter:WorkCenter) WHERE workCenter.ontology_id = $ontology_id RETURN machine, workCenter ORDER BY machine.id"},
        {"name": "get_supplier_parts", "description": "Retrieve supplier commitments and the parts they supply.", "parameters": ["supplier_id"], "cypher": f"MATCH (commitment:SupplyCommitment) {scope('commitment')} MATCH (commitment)-[:COMMITTED_BY]->(supplier:Supplier) WHERE supplier.ontology_id = $ontology_id AND ($supplier_id IS NULL OR supplier.id = $supplier_id) OPTIONAL MATCH (commitment)-[:SUPPLIES_PART]->(part:Part) WHERE part.ontology_id = $ontology_id RETURN supplier, commitment, part ORDER BY supplier.id, part.id"},
        {"name": "get_material_requirements", "description": "Retrieve material requirements, required parts, and their owning bills of materials.", "parameters": ["part_id"], "cypher": f"MATCH (bom:BillOfMaterials) {scope('bom')} MATCH (bom)-[:DEFINES_REQUIREMENT]->(requirement:MaterialRequirement)-[:REQUIRES_PART]->(part:Part) WHERE requirement.ontology_id = $ontology_id AND part.ontology_id = $ontology_id AND ($part_id IS NULL OR part.id = $part_id) RETURN bom, requirement, part ORDER BY requirement.id"},
        {"name": "get_production_events", "description": "Retrieve production events with their work order and machine execution context.", "parameters": ["work_order_id"], "cypher": f"MATCH (event:ProductionEvent) {scope('event')} OPTIONAL MATCH (event)-[:EXECUTES_WORK_ORDER]->(workOrder:WorkOrder) WHERE workOrder.ontology_id = $ontology_id OPTIONAL MATCH (event)-[:USES_MACHINE]->(machine:Machine) WHERE machine.ontology_id = $ontology_id WITH event, workOrder, machine WHERE $work_order_id IS NULL OR workOrder.id = $work_order_id RETURN event, workOrder, machine ORDER BY event.id"},
    ]


def render_context_graph_package(snapshot_path: str | Path) -> dict[str, str]:
    """Render a deterministic context-graph package from a v1.1 snapshot."""
    snapshot_file = Path(snapshot_path)
    snapshot = json.loads(snapshot_file.read_text(encoding="utf-8"))
    ontology = snapshot["ontology"]
    ontology_id = ontology["ontology_id"]
    if ontology_id != "salt.manufacturing.v1.1":
        raise ValueError("context-graph package currently supports salt.manufacturing.v1.1 only")
    _require_terms(snapshot)

    classes = sorted(snapshot["classes"], key=lambda item: item["local_name"])
    properties = sorted(snapshot["properties"], key=lambda item: item["local_name"])
    datatype_properties = [item for item in properties if item["property_kind"] == "datatype"]
    object_properties = [item for item in properties if item["property_kind"] == "object"]
    attributes = {item["local_name"]: [] for item in classes}
    for property_item in datatype_properties:
        for domain in property_item["domains"]:
            attributes[_local_name(domain)].append({
                "name": property_item["local_name"],
                "label": property_item["label"],
                "range": property_item["ranges"][0] if property_item["ranges"] else None,
            })
    for values in attributes.values():
        values.sort(key=lambda item: item["name"])
    domain = {
        "package_version": "1.0",
        "source": {
            "ontology_id": ontology_id,
            "ontology_iri": ontology["ontology_iri"],
            "snapshot_sha256": hashlib.sha256(snapshot_file.read_bytes()).hexdigest(),
            "source_policy": "metadata-only; no SAP, CDS, or transactional source records",
        },
        "entity_types": [
            {"label": item["local_name"], "display_name": item["label"], "identity_property": "id", "attributes": attributes[item["local_name"]]}
            for item in classes
        ],
        "relationships": [
            {"type": item["local_name"], "graph_type": re.sub(r"(?<!^)(?=[A-Z])", "_", item["local_name"]).upper(), "source": _local_name(item["domains"][0]), "target": _local_name(item["ranges"][0])}
            for item in object_properties
        ],
        "embeddings": {"enabled": True, "text_fields": ["id", "identifier", "status"], "exclude_source_content": True},
        "retrieval": {"ontology_id_required": True, "default_limit": 25, "read_only_tools": True},
        "ingestion": {"allowed_document_kinds": ["work_instruction", "bom_pdf", "routing_sheet", "supplier_spec", "manufacturing_documentation"], "chunk_size": 800, "chunk_overlap": 120, "linking": "explicit identifiers only", "provenance_required": True, "reject_sap_cds_transactional_content": True},
        "agent_tools": _tool_definitions(ontology_id),
    }
    domain_yaml = yaml.safe_dump(domain, allow_unicode=False, sort_keys=False)

    constraints = []
    indexes = []
    for item in classes:
        label = item["local_name"]
        stem = _cypher_name(f"{ontology_id}_{label}")
        constraints.append(f"CREATE CONSTRAINT {stem}_identity IF NOT EXISTS FOR (node:{label}) REQUIRE (node.ontology_id, node.id) IS UNIQUE;")
        indexes.append(f"CREATE INDEX {stem}_identifier IF NOT EXISTS FOR (node:{label}) ON (node.ontology_id, node.identifier);")
    schema = "// Generated from salt.manufacturing.v1.1; metadata-only schema, no records are created.\n" + "\n".join(constraints + indexes) + "\n"

    reasoning = {
        "ontology_id": ontology_id,
        "execution": {"engine": "parameterized_read_only_cypher", "max_hops": 4, "ontology_id_required": True, "no_inferred_relationships": True},
        "strategies": [
            {"name": "bom_requirements", "purpose": "Trace explicit work-order BOM requirements to parts.", "parameters": ["work_order_id"], "tool": "get_bom_components"},
            {"name": "schedule_contention", "purpose": "Compare explicit schedule slots assigned to the same work center.", "parameters": ["work_center_id", "window_start", "window_end"], "cypher": "MATCH (slot:ScheduleSlot)-[:ALLOCATED_TO]->(center:WorkCenter) WHERE slot.ontology_id = $ontology_id AND center.ontology_id = $ontology_id AND center.id = $work_center_id AND slot.plannedStart < $window_end AND slot.plannedEnd > $window_start OPTIONAL MATCH (slot)-[:SCHEDULED_FOR]->(workOrder:WorkOrder) WHERE workOrder.ontology_id = $ontology_id RETURN slot, workOrder ORDER BY slot.plannedStart"},
            {"name": "production_lineage", "purpose": "Follow explicitly asserted production-event ordering and material use.", "parameters": ["part_id"], "cypher": "MATCH (event:ProductionEvent)-[material:CONSUMES_PART|PRODUCES_PART]->(part:Part) WHERE event.ontology_id = $ontology_id AND part.ontology_id = $ontology_id AND part.id = $part_id OPTIONAL MATCH (previous:ProductionEvent)-[:PRECEDES_EVENT]->(event) WHERE previous.ontology_id = $ontology_id OPTIONAL MATCH (event)-[:PRECEDES_EVENT]->(next:ProductionEvent) WHERE next.ontology_id = $ontology_id RETURN previous, event, material, part, next ORDER BY event.actualStart"},
            {"name": "supply_coverage", "purpose": "Find explicit supplier commitments for a required part.", "parameters": ["part_id"], "cypher": "MATCH (commitment:SupplyCommitment)-[:SUPPLIES_PART]->(part:Part) WHERE commitment.ontology_id = $ontology_id AND part.ontology_id = $ontology_id AND part.id = $part_id MATCH (commitment)-[:COMMITTED_BY]->(supplier:Supplier) WHERE supplier.ontology_id = $ontology_id RETURN commitment, supplier, part ORDER BY commitment.commitmentDate"},
        ],
    }

    tools_yaml = yaml.safe_dump({"ontology_id": ontology_id, "tools": domain["agent_tools"]}, allow_unicode=False, sort_keys=False)
    ingestion_yaml = yaml.safe_dump({"ontology_id": ontology_id, **domain["ingestion"]}, allow_unicode=False, sort_keys=False)
    reasoning_yaml = yaml.safe_dump(reasoning, allow_unicode=False, sort_keys=False)
    validation = json.dumps({"ontology_id": ontology_id, "required_tools": list(_REQUIRED_TOOL_NAMES), "required_reasoning_strategies": [item["name"] for item in reasoning["strategies"]], "source_policy": domain["source"]["source_policy"]}, indent=2) + "\n"
    return {"domain.yaml": domain_yaml, "schema.cypher": schema, "tools/manufacturing-tools.yaml": tools_yaml, "reasoning/strategies.yaml": reasoning_yaml, "ingestion/document-rules.yaml": ingestion_yaml, "validation/package-contract.json": validation}


def write_context_graph_package(snapshot_path: str | Path, output_dir: str | Path) -> dict[str, str]:
    """Write rendered package artifacts using stable UTF-8 LF text."""
    artifacts = render_context_graph_package(snapshot_path)
    output = Path(output_dir)
    for relative_path, content in artifacts.items():
        destination = output / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
    return {relative_path: _sha256(content) for relative_path, content in artifacts.items()}