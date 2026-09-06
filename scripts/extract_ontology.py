"""Export a version-scoped Neo4j ontology metadata snapshot."""

from __future__ import annotations

import argparse
import json
import os

from create_context_graph.ontology_ingest import extract_ontology_snapshot


def _dotenv_values(path: str = ".env") -> dict[str, str]:
    dotenv_path = os.path.join(os.getcwd(), path)
    if not os.path.isfile(dotenv_path):
        return {}
    values: dict[str, str] = {}
    with open(dotenv_path, encoding="utf-8") as dotenv_file:
        for line in dotenv_file:
            key, separator, value = line.strip().partition("=")
            if separator and key and not key.startswith("#"):
                values[key] = value
    return values


def main() -> None:
    dotenv = _dotenv_values()
    neo4j_host = os.getenv("NEO4J_HOST", dotenv.get("NEO4J_HOST", "localhost"))
    neo4j_port = os.getenv("NEO4J_PORT", dotenv.get("NEO4J_PORT", "7687"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--neo4j-uri", default=os.getenv("NEO4J_URI", dotenv.get("NEO4J_URI", f"neo4j://{neo4j_host}:{neo4j_port}")))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USERNAME", dotenv.get("NEO4J_USERNAME", os.getenv("NEO4J_USER", dotenv.get("NEO4J_USER", "neo4j")))))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", dotenv.get("NEO4J_PASSWORD", "")))
    parser.add_argument("--neo4j-database", default=os.getenv("NEO4J_DATABASE", dotenv.get("NEO4J_DATABASE", "")))
    args = parser.parse_args()
    if not args.neo4j_password:
        parser.error("--neo4j-password or NEO4J_PASSWORD is required")
    print(json.dumps(extract_ontology_snapshot(
        args.ontology_id, args.neo4j_uri, args.neo4j_user, args.neo4j_password,
        args.output, args.neo4j_database,
    ), indent=2))


if __name__ == "__main__":
    main()