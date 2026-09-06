# SAP SALT-KG Source Provenance

## Source

- Repository: https://github.com/SAP-samples/salt-kg.git
- Local clone: `sap-salt/`
- Pinned commit: `ff9fb30754abdc987e924fe05dd59fc7f56476b9`
- Retrieved: 2026-09-05

## Intended Use

The clone is a local reference for designing a SALT-compatible manufacturing
metadata ontology and an optional, operator-run importer. It is not a runtime
dependency of generated projects.

The implementation may use generic graph structures derived from the dataset's
published model, such as views, fields, business concepts, taxonomy concepts,
source datasets, and sales documents. Do not copy SALT source rows, metadata
descriptions, or derived fixture content into `src/create_context_graph`,
generated project fixtures, or published documentation without approval.

## License Boundary

The upstream repository states that it is licensed under CC-BY-NC-SA-4.0 and
contains `TDM_RESERVATION.txt`, which reserves commercial text and data mining
rights. Preserve the upstream license files in the clone. Obtain legal approval
before redistributing upstream data, adapted material, or generated fixtures
derived from it.