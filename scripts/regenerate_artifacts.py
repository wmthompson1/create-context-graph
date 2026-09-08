"""Regenerate canonical ontology artifacts from a Neo4j metadata snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from create_context_graph.ontology_ingest import (
    promote_regenerated_artifacts,
    record_regeneration_provenance,
    render_regenerated_artifacts,
    validate_staged_artifacts,
    write_regenerated_artifacts,
)


def _dotenv_values(path: str = ".env") -> dict[str, str]:
    dotenv_path = Path.cwd() / path
    if not dotenv_path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.strip().partition("=")
        if separator and key and not key.startswith("#"):
            values[key] = value
    return values


def main() -> None:
    dotenv = _dotenv_values()
    neo4j_host = os.getenv("NEO4J_HOST", dotenv.get("NEO4J_HOST", "localhost"))
    neo4j_port = os.getenv("NEO4J_PORT", dotenv.get("NEO4J_PORT", "7687"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--neo4j-uri", default=os.getenv("NEO4J_URI", dotenv.get("NEO4J_URI", f"neo4j://{neo4j_host}:{neo4j_port}")))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USERNAME", dotenv.get("NEO4J_USERNAME", os.getenv("NEO4J_USER", dotenv.get("NEO4J_USER", "neo4j")))))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", dotenv.get("NEO4J_PASSWORD", "")))
    parser.add_argument("--neo4j-database", default=os.getenv("NEO4J_DATABASE", dotenv.get("NEO4J_DATABASE", "")))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rendered = render_regenerated_artifacts(args.snapshot, args.manifest)
    hashes = {
        path: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for path, content in rendered["artifacts"].items()
    }
    if not args.dry_run:
        if not args.neo4j_password:
            parser.error("--neo4j-password or NEO4J_PASSWORD is required unless --dry-run is used")
        output_dir = Path(args.output_dir).resolve()
        ontop_wrapper = Path(args.manifest).resolve().parent / "ontop.ps1"
        with tempfile.TemporaryDirectory(prefix=".regeneration-", dir=output_dir.parent) as staging_dir:
            shutil.copytree(output_dir, staging_dir, dirs_exist_ok=True)
            write_regenerated_artifacts(rendered, staging_dir)
            validate_staged_artifacts(staging_dir, ontop_wrapper)
            hashes = promote_regenerated_artifacts(staging_dir, output_dir)
        provenance = record_regeneration_provenance(
            args.manifest, rendered["snapshot_sha256"], hashes, args.neo4j_uri,
            args.neo4j_user, args.neo4j_password, args.neo4j_database,
        )
    else:
        provenance = None
    report = {
        "ontology_id": rendered["ontology_id"],
        "snapshot_sha256": rendered["snapshot_sha256"],
        "artifacts": hashes,
        "written": not args.dry_run,
        "validated": not args.dry_run,
        "provenance": provenance,
    }
    if not args.dry_run:
        report_path = Path(args.output_dir).resolve() / "regeneration-report.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["report"] = str(report_path)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()