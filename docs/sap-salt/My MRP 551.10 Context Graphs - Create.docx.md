**Manufacturing \- Create Context Graphs**

*Neo4j Create Context Graphs Project*

*The convergence of industrial operations, enterprise resource planning, and semantic knowledge modeling is redefining how manufacturers govern, share, and reason over production data. Neo4j staff created a repo.*

**Prepared for:** Manufacturing Data Architects, ERP/MES System Designers, Knowledge Engineers, OT Analysts, and Enterprise Information Managers

**Prepared by:** William  |  Federal Way, Washington, United States

**Date:** Sept 5, 2026  |  Pacific Daylight Time

**Classification:** Internal Reference  |  Version 1.0

1. # **From a podcast (not mine)**

**Url for topic:**  [https://github.com/neo4j-labs/create-context-graph](https://github.com/neo4j-labs/create-context-graph)

**URL for idea origin podcast: [⚡️ How to turn Documents into Knowledge: Graphs in Modern AI — Emil Eifrem, CEO Neo4J](https://www.youtube.com/watch?v=yyuVR-ML9X8)** 

The tool the speaker discusses (40:22) is called create-context-graph. It is an interactive CLI scaffolding tool, similar to *create-react-app*, designed to help you quickly build AI agent applications backed by a *Neo4j* knowledge graph.

It provides out-of-the-box support for multiple domains and integrates with various agent platforms to handle short-term conversational state, long-term memory (entities/concepts), and decision traces.

You can find the official repository here:

* Repository: [https://github.com/neo4j-labs/create-context-graph](https://github.com/neo4j-labs/create-context-graph)

## **Sample Helper \- SKOS Representation of Manufacturing Taxonomies**

SKOS (Simple Knowledge Organization System) is the W3C standard for encoding controlled vocabularies, taxonomies, and thesauri as RDF. Its core constructs map directly to manufacturing taxonomy requirements:

* **skos:ConceptScheme** — the containing structure for a taxonomy (e.g., the UNSPSC scheme, the Operation Type scheme)

* **skos:Concept** — an individual term or category node within the taxonomy

* **skos:prefLabel** — the canonical, preferred label for the concept in a given language

* **skos:altLabel** — alternative labels, synonyms, and system-specific names (e.g., "Work Order" as altLabel for "Production Order" as prefLabel)

* **skos:notation** — formal codes used to identify the concept (UNSPSC codes, eCl@ss codes, SAP activity type codes)

* **skos:broader / skos:narrower** — parent–child hierarchy relationships

* **skos:scopeNote** — explanatory notes distinguishing concepts that vary by system context

* **skos:exactMatch / skos:closeMatch** — alignment mappings to equivalent concepts in external taxonomies

Scope notes are particularly valuable for manufacturing taxonomy governance: a skos:scopeNote on the "Production Order" concept can document precisely how its meaning differs in SAP (a PP order with cost accumulation), Oracle (a discrete job with associated cost element), and Rockwell FactoryTalk (a work order linked to a routing and BOM), providing human-readable disambiguation while the formal SKOS concept serves as the semantic anchor for data integration mappings.

# **Helper — Knowledge Graphs in Manufacturing**

## **The Manufacturing Knowledge Graph**

A **manufacturing knowledge graph** is an integrated, graph-structured knowledge base that connects products, processes, resources, orders, quality events, and supply chain entities through typed, semantically annotated relationships. It is the realization of manufacturing ontologies and taxonomies in an operational data environment: where ontologies define the schema (the classes and properties), the knowledge graph populates that schema with actual production instances — specific products, specific work orders, specific machines, specific quality events.

The manufacturing knowledge graph differs fundamentally from both a relational data warehouse and a traditional ERP database. Where a data warehouse denormalizes data into star or snowflake schemas optimized for aggregate query performance, and where an ERP database normalizes data into relational tables optimized for transactional consistency, a knowledge graph is optimized for **connected traversal** — following chains of typed relationships across entity boundaries without schema rigidity, enabling queries that cross the conceptual boundaries between production, quality, equipment, and supply chain domains.

Key entity types in a manufacturing knowledge graph include: Product, Component, Material, Process, Operation, WorkOrder, WorkCenter, ProductionOrder, PlannedOrder, Supplier, Customer, Equipment, MaintenanceEvent, QualityInspection, DefectReport, DigitalTwin, CustomerOrder, and EngineeringChangeNotice. Each entity type is an OWL class; each instance is an OWL individual populated from source systems; and the relationships between them are OWL ObjectProperties 