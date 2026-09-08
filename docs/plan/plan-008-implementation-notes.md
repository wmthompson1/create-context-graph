# Plan 008 implementation notes

## Ontology hardening

The MFGQ core ontology was tightened so that the quality layer has explicit
semantic provenance and domain constraints for the core quality entity model:

- `mfgq:severity` includes a domain of `Nonconformance` and range of
  `Severity`
- `mfgq:status` includes a domain of `Nonconformance` and range of `Status`
- `mfgq:sourceSystem`, `mfgq:sourceId`, and `mfgq:sourceRecord` now carry the
  appropriate domains and ranges for provenance
- `mfgq:hasDisposition` remains a required quality-case relationship for closed
  NCRs

This keeps the quality layer aligned with the SAP context model instead of
creating a parallel enterprise ontology.

## SHACL validation

The SHACL file now covers the required structural rules for the first quality
pass:

- `Nonconformance` requires `affectedPart`, `hasNonconformity`, and `detectedBy`
- `Measurement` enforces `value` and `evaluation`
- a closed nonconformance must have a disposition

## Read-only quality Cypher tool set

The new `mfgq-quality-tools.yaml` file introduces the first declarative set of
read-only quality tools:

- `get_open_nonconformances`
- `get_nonconformance_root_cause`
- `get_part_measurement_failures`
- `get_supplier_nc_history`
- `get_workorder_quality_impact`
- `get_quality_summary_by_plant`

All queries are parameterized and read-only; there are no `CREATE`, `MERGE`,
`SET`, or `DELETE` operations.

This is intentionally the first pass of the quality extension. The next step is
binding the generic MFGQ integration predicates to the exact SAP OBKG identifiers
used in the target deployment.
