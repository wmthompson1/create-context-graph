"""Generate the metadata-only manufacturing context-graph package."""

from __future__ import annotations

import argparse
import json

from create_context_graph.context_graph_package import write_context_graph_package


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps({"artifacts": write_context_graph_package(args.snapshot, args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()