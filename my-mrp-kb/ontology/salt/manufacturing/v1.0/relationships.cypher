UNWIND $properties AS property
MATCH (node:OntologyProperty {ontology_id: $ontology_id, iri: property.iri})
UNWIND property.domains AS domain_iri
MATCH (domain:OntologyClass {ontology_id: $ontology_id, iri: domain_iri})
MERGE (node)-[:HAS_DOMAIN]->(domain);
UNWIND $properties AS property
MATCH (node:OntologyProperty {ontology_id: $ontology_id, iri: property.iri})
UNWIND property.ranges AS range_iri
MATCH (range:OntologyClass {ontology_id: $ontology_id, iri: range_iri})
MERGE (node)-[:HAS_RANGE]->(range);
