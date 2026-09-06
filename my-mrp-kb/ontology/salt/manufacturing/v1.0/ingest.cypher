MERGE (ontology:Ontology {ontology_id: $ontology_id})
SET ontology.ontology_iri = $ontology_iri, ontology.namespace = $namespace, ontology.domain = $domain, ontology.version = $version, ontology.manifest_sha256 = $manifest_sha256
MERGE (kb:KnowledgeBase {kb_id: $kb_id})
SET kb.name = $kb_name, kb.document_root = $document_root
MERGE (kb)-[:OWNS_ONTOLOGY]->(ontology);
UNWIND $classes AS class
MERGE (node:OntologyClass {ontology_id: $ontology_id, iri: class.iri})
SET node.local_name = class.local_name, node.label = class.label
WITH node MATCH (ontology:Ontology {ontology_id: $ontology_id})
MERGE (ontology)-[:DECLARES_CLASS]->(node);
UNWIND $properties AS property
MERGE (node:OntologyProperty {ontology_id: $ontology_id, iri: property.iri})
SET node.local_name = property.local_name, node.label = property.label, node.property_kind = property.property_kind
WITH node MATCH (ontology:Ontology {ontology_id: $ontology_id})
MERGE (ontology)-[:DECLARES_PROPERTY]->(node);
