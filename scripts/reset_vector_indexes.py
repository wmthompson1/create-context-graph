from neo4j import GraphDatabase

uri = "neo4j://localhost:7687"
user = "neo4j"
password = "neo4j123"

names = [
    "entity_embedding_idx",
    "fact_embedding_idx",
    "message_embedding_idx",
    "preference_embedding_idx",
    "step_embedding_idx",
    "task_embedding_idx",
]

driver = GraphDatabase.driver(uri, auth=(user, password))

try:
    with driver.session(database="neo4j") as session:
        try:
            rows = [dict(r) for r in session.run("SHOW VECTOR INDEXES")]
            print("VECTOR_INDEXES_BEFORE", rows)
        except Exception as exc:
            print("SHOW_VECTOR_INDEXES_ERROR", type(exc).__name__, exc)

        try:
            session.run("MATCH (n) DETACH DELETE n")
            print("GRAPH_CLEARED")
        except Exception as exc:
            print("GRAPH_CLEAR_ERROR", type(exc).__name__, exc)

        for name in names:
            try:
                session.run(f"DROP INDEX {name} IF EXISTS")
                print("DROPPED", name)
            except Exception as exc:
                print("DROP_ERROR", name, type(exc).__name__, exc)

        try:
            rows_after = [dict(r) for r in session.run("SHOW VECTOR INDEXES")]
            print("VECTOR_INDEXES_AFTER", rows_after)
        except Exception as exc:
            print("SHOW_VECTOR_INDEXES_AFTER_ERROR", type(exc).__name__, exc)
finally:
    driver.close()
