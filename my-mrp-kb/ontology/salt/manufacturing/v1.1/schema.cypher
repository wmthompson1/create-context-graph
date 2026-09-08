CREATE CONSTRAINT ontology_id_unique IF NOT EXISTS FOR (n:Ontology) REQUIRE n.ontology_id IS UNIQUE;
CREATE CONSTRAINT knowledge_base_id_unique IF NOT EXISTS FOR (n:KnowledgeBase) REQUIRE n.kb_id IS UNIQUE;
CREATE CONSTRAINT ontology_class_key_unique IF NOT EXISTS FOR (n:OntologyClass) REQUIRE (n.ontology_id, n.iri) IS UNIQUE;
CREATE CONSTRAINT ontology_property_key_unique IF NOT EXISTS FOR (n:OntologyProperty) REQUIRE (n.ontology_id, n.iri) IS UNIQUE;
CREATE INDEX ontology_artifact_path IF NOT EXISTS FOR (n:OntologyArtifact) ON (n.ontology_id, n.path);
CREATE INDEX ontology_class_local_name IF NOT EXISTS FOR (n:OntologyClass) ON (n.ontology_id, n.local_name);
CREATE INDEX ontology_property_local_name IF NOT EXISTS FOR (n:OntologyProperty) ON (n.ontology_id, n.local_name);
CREATE INDEX ingestion_run_status IF NOT EXISTS FOR (n:IngestionRun) ON (n.ontology_id, n.status);
