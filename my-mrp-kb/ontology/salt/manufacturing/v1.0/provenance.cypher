UNWIND $artifacts AS artifact
MERGE (node:OntologyArtifact {ontology_id: $ontology_id, path: artifact.path})
SET node.kind = artifact.kind, node.format = artifact.format, node.sha256 = artifact.sha256
WITH node MATCH (ontology:Ontology {ontology_id: $ontology_id})
MERGE (ontology)-[:HAS_ARTIFACT]->(node);
MERGE (policy:SourcePolicy {ontology_id: $ontology_id, source_name: 'sap_salt_data'})
SET policy.usage_status = $sap_salt_data
WITH policy MATCH (ontology:Ontology {ontology_id: $ontology_id})
MERGE (ontology)-[:GOVERNED_BY]->(policy);
MATCH (run:IngestionRun {run_id: $run_id})
UNWIND $artifacts AS artifact
MATCH (node:OntologyArtifact {ontology_id: $ontology_id, path: artifact.path})
MERGE (run)-[:USED_ARTIFACT]->(node);
