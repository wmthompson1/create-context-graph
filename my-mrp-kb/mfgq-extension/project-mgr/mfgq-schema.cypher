// MFGQ Neo4j constraints and indexes.
// SAP context entities are intentionally not recreated here.

CREATE CONSTRAINT mfgq_nc_id IF NOT EXISTS
FOR (n:Nonconformance) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT mfgq_defect_code IF NOT EXISTS
FOR (n:Defect) REQUIRE n.code IS UNIQUE;

CREATE CONSTRAINT mfgq_requirement_id IF NOT EXISTS
FOR (n:Requirement) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT mfgq_measurement_id IF NOT EXISTS
FOR (n:Measurement) REQUIRE n.id IS UNIQUE;

CREATE INDEX mfgq_nc_status IF NOT EXISTS
FOR (n:Nonconformance) ON (n.status);

CREATE INDEX mfgq_nc_detected_at IF NOT EXISTS
FOR (n:Nonconformance) ON (n.detectedAt);

// Example integration pattern:
// MATCH (nc:Nonconformance {id:$ncId})
// MATCH (mat:Material {sourceId:$materialId, sourceSystem:'SAP'})
// MERGE (nc)-[:AFFECTS_MATERIAL]->(mat);
