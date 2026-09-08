"""Validated execution for GDS-free context-graph reasoning strategies."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


_WRITE_KEYWORDS = ("CREATE", "MERGE", "SET", "DELETE", "REMOVE", "CALL GDS.")

MANUFACTURING_REASONING_PROMPT = """For manufacturing questions, distinguish observed evidence, missing evidence, and assumptions.
Use only explicit graph nodes, relationships, and document chunks returned by tools. Do not infer a BOM, schedule, production lineage, supplier commitment, or other relationship from matching names, identifiers, dates, or timestamps. If the required explicit edge is absent, say that the evidence is missing and request clarification. Cite evidence using node IDs, relationship types, and document chunk IDs when they are present in the result."""


@dataclass(frozen=True)
class ReasoningStrategy:
    """One registered, evidence-bound Cypher reasoning strategy."""

    name: str
    purpose: str
    parameters: tuple[str, ...]
    cypher: str | None
    tool: str | None


@dataclass(frozen=True)
class ReasoningPackage:
    """Validated runtime contract for one ontology-scoped reasoning package."""

    ontology_id: str
    max_hops: int
    strategies: dict[str, ReasoningStrategy]


def load_reasoning_package(path: str | Path) -> ReasoningPackage:
    """Load and validate a generated GDS-free reasoning strategy catalog."""
    catalog_path = Path(path)
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("ontology_id"), str):
        raise ValueError("reasoning catalog requires an ontology_id")
    execution = data.get("execution")
    if not isinstance(execution, dict) or execution.get("engine") != "parameterized_read_only_cypher":
        raise ValueError("reasoning catalog must use parameterized_read_only_cypher")
    max_hops = execution.get("max_hops")
    if not isinstance(max_hops, int) or max_hops < 1:
        raise ValueError("reasoning catalog requires a positive max_hops")

    strategies: dict[str, ReasoningStrategy] = {}
    for item in data.get("strategies", []):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("reasoning strategy requires a name")
        cypher = item.get("cypher")
        tool = item.get("tool")
        if bool(cypher) == bool(tool):
            raise ValueError(f"strategy {item['name']} requires exactly one of cypher or tool")
        if cypher:
            normalized = cypher.upper()
            if "$ONTOLOGY_ID" not in normalized or any(keyword in normalized for keyword in _WRITE_KEYWORDS):
                raise ValueError(f"strategy {item['name']} is not read-only and ontology-scoped")
        strategies[item["name"]] = ReasoningStrategy(
            name=item["name"],
            purpose=str(item.get("purpose", "")),
            parameters=tuple(item.get("parameters", [])),
            cypher=cypher,
            tool=tool,
        )
    if not strategies:
        raise ValueError("reasoning catalog requires at least one strategy")
    return ReasoningPackage(data["ontology_id"], max_hops, strategies)


ExecuteCypher = Callable[[str, dict[str, Any]], Awaitable[list[dict[str, Any]]]]
ExecuteTool = Callable[[str, dict[str, Any]], Awaitable[list[dict[str, Any]]]]


async def execute_reasoning_strategy(
    package: ReasoningPackage,
    strategy_name: str,
    parameters: dict[str, Any],
    execute_cypher: ExecuteCypher,
    execute_tool: ExecuteTool | None = None,
) -> dict[str, Any]:
    """Execute a named strategy and return its evidence envelope.

    Callers provide the existing graph executor, keeping connection handling and
    streaming instrumentation within the generated application's current path.
    """
    strategy = package.strategies.get(strategy_name)
    if strategy is None:
        raise ValueError(f"unregistered reasoning strategy: {strategy_name}")
    unexpected = set(parameters) - set(strategy.parameters)
    if unexpected:
        raise ValueError(f"unexpected parameters for {strategy_name}: {sorted(unexpected)}")
    missing = set(strategy.parameters) - set(parameters)
    if missing:
        raise ValueError(f"missing parameters for {strategy_name}: {sorted(missing)}")

    scoped_parameters = {"ontology_id": package.ontology_id, **parameters}
    if strategy.cypher:
        records = await execute_cypher(strategy.cypher, scoped_parameters)
    elif execute_tool:
        records = await execute_tool(strategy.tool or "", scoped_parameters)
    else:
        raise ValueError(f"strategy {strategy_name} requires a tool executor")
    return {
        "strategy": strategy.name,
        "purpose": strategy.purpose,
        "reasoning_contract": "evidence_only",
        "ontology_id": package.ontology_id,
        "max_hops": package.max_hops,
        "evidence": records,
    }