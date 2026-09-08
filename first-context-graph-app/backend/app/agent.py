"""Financial Services AI Agent — Strands implementation."""

from __future__ import annotations

import asyncio
import json
import os

from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.tools import tool

from app.config import settings
from app.context_graph_client import execute_cypher, get_schema
from app.memory import store_message, get_context, resolve_session_id


# Ensure ANTHROPIC_API_KEY is available in the environment
if not os.environ.get("ANTHROPIC_API_KEY"):
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    else:
        from dotenv import dotenv_values
        _key = dotenv_values("../.env").get("ANTHROPIC_API_KEY", "")
        if _key:
            os.environ["ANTHROPIC_API_KEY"] = _key


_main_loop: asyncio.AbstractEventLoop | None = None


def _capture_loop():
    """Capture the running event loop. Must be called from async context."""
    global _main_loop
    _main_loop = asyncio.get_running_loop()


def _run_sync(coro):
    """Run an async coroutine from a synchronous worker thread.

    Schedules the coroutine on the main event loop (captured at request time)
    using ``run_coroutine_threadsafe`` so that asyncio.Queue operations and
    Neo4j async driver calls stay on the correct loop.
    """
    loop = _main_loop
    if loop is not None and loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=30)
    return asyncio.run(coro)


SYSTEM_PROMPT = """You are an AI financial intelligence assistant with access to a comprehensive
knowledge graph of financial data. You help financial advisors, compliance
officers, and portfolio managers analyze accounts, transactions, decisions,
and policies.

Your capabilities include:
- Searching and analyzing client portfolios and transaction history
- Reviewing compliance status and policy adherence
- Tracing decision provenance and causal chains
- Identifying patterns and anomalies in financial data
- Finding similar past decisions to inform current choices

Always provide accurate, data-driven responses. When making recommendations,
cite the specific data points and reasoning from the knowledge graph.


IMPORTANT: You MUST use the available tools to query the knowledge graph before answering any question about the data. Never guess or make up information — always use tools to look up actual data from the graph.

CRITICAL: Call tools DIRECTLY without any introductory text. Do NOT say "I'll search for..." or "Let me look up..." before calling a tool — just call the tool immediately. Only generate text AFTER you have received the tool results and are ready to provide your final answer."""

# ---------------------------------------------------------------------------
# Agent tools — domain-specific for Financial Services
# ---------------------------------------------------------------------------

@tool
def search_customer(query: str) -> str:
    """Search for clients, advisors, or other people by name or role"""
    cypher = """MATCH (p:Person)
    WHERE toLower(p.name) CONTAINS toLower($query)
       OR toLower(coalesce(p.role, '')) CONTAINS toLower($query)
    OPTIONAL MATCH (p)-[r]-(related)
    RETURN p, type(r) AS rel_type, related
    LIMIT 20
"""
    params = {
        "query": query,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="search_customer"))
    return json.dumps(result, default=str)

@tool
def get_customer_decisions(name: str) -> str:
    """Get all decisions related to a specific client"""
    cypher = """MATCH (p:Person {name: $name})-[:OWNS|MANAGES]->(a:Account)
    OPTIONAL MATCH (d:Decision)-[:CAUSED]->(t:Transaction)-[:TRANSFERRED_TO|TRANSFERRED_FROM]->(a)
    RETURN p, a, d, t
    ORDER BY d.date DESC
    LIMIT 20
"""
    params = {
        "name": name,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="get_customer_decisions"))
    return json.dumps(result, default=str)

@tool
def find_similar_decisions(decision_id: str) -> str:
    """Find decisions similar to a given decision using vector similarity"""
    cypher = """MATCH (d:Decision {decision_id: $decision_id})
    CALL db.index.vector.queryNodes('decision_embeddings', 5, d.embedding)
    YIELD node, score
    WHERE node.decision_id <> $decision_id
    RETURN node AS similar_decision, score
    ORDER BY score DESC
"""
    params = {
        "decision_id": decision_id,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="find_similar_decisions"))
    return json.dumps(result, default=str)

@tool
def get_causal_chain(decision_id: str) -> str:
    """Trace the causal chain of events from a decision"""
    cypher = """MATCH path = (d:Decision {decision_id: $decision_id})-[:CAUSED|PRECEDED_BY*1..5]-(related)
    RETURN path
"""
    params = {
        "decision_id": decision_id,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="get_causal_chain"))
    return json.dumps(result, default=str)

@tool
def detect_fraud_patterns() -> str:
    """Detect unusual transaction patterns that may indicate fraud"""
    cypher = """MATCH (a:Account)<-[:TRANSFERRED_TO]-(t:Transaction)
    WHERE t.date > datetime() - duration('P30D')
    WITH a, count(t) AS tx_count, sum(t.amount) AS total_amount
    WHERE tx_count > 10 OR total_amount > 100000
    RETURN a.account_id, a.name, tx_count, total_amount
    ORDER BY total_amount DESC
"""
    params = {
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="detect_fraud_patterns"))
    return json.dumps(result, default=str)

@tool
def list_accounts(limit: str) -> str:
    """List Account records with optional limit"""
    cypher = """MATCH (n:Account)
    RETURN n
    ORDER BY n.name
    LIMIT toInteger($limit)
"""
    params = {
        "limit": limit,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="list_accounts"))
    return json.dumps(result, default=str)

@tool
def get_account_by_id(id: str) -> str:
    """Get a specific Account by ID with all connections"""
    cypher = """MATCH (n:Account {account_id: $id})
    OPTIONAL MATCH (n)-[r]-(related)
    RETURN n, type(r) AS relationship, labels(related) AS related_labels, related.name AS related_name
    LIMIT 50
"""
    params = {
        "id": id,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="get_account_by_id"))
    return json.dumps(result, default=str)




@tool
def run_cypher(query: str, parameters: str = "{}") -> str:
    """Execute a read-only Cypher query against the knowledge graph."""
    try:
        params = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON parameters"})
    params.setdefault("domain", settings.domain_id)
    try:
        result = _run_sync(execute_cypher(query, params, tool_name="run_cypher"))
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": f"Cypher query failed: {e}"})


@tool
def get_graph_schema() -> str:
    """Get the knowledge graph schema (node labels and relationship types)."""
    result = _run_sync(get_schema())
    return json.dumps(result, default=str)

model = AnthropicModel(model_id="claude-sonnet-4-20250514", max_tokens=4096)

agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        search_customer,
        get_customer_decisions,
        find_similar_decisions,
        get_causal_chain,
        detect_fraud_patterns,
        list_accounts,
        get_account_by_id,
        run_cypher,
        get_graph_schema,
    ],
)



def _extract_text(result) -> str:
    """Extract text from a Strands agent result, handling serialization issues.

    Strands may return objects with various shapes depending on the Anthropic SDK
    version.  This helper tries several extraction strategies to avoid
    PydanticSerializationUnexpectedValue errors from ParsedTextBlock objects.
    """
    # Try direct text attribute (AgentResult)
    if hasattr(result, "text"):
        return str(result.text)

    # Try message.content (Anthropic-style)
    if hasattr(result, "message"):
        msg = result.message
        if hasattr(msg, "content"):
            parts = []
            for block in (msg.content if isinstance(msg.content, list) else [msg.content]):
                if hasattr(block, "text"):
                    parts.append(block.text)
                elif isinstance(block, str):
                    parts.append(block)
            if parts:
                return "\n".join(parts)

    # Fallback: str() with safety wrapper
    try:
        return str(result)
    except Exception:
        return "I processed your request but encountered an issue formatting the response."


# ---------------------------------------------------------------------------
# Message handler
# ---------------------------------------------------------------------------


async def handle_message(message: str, session_id: str | None = None) -> dict:
    """Handle an incoming chat message."""
    session_id = resolve_session_id(session_id)

    # Store user message and retrieve context
    await store_message(session_id, "user", message)
    context = await get_context(session_id, query=message)
    history = context.get("messages", [])

    # Build input with structured conversation history
    if history:
        history_block = "\n\n".join(
            f"[{m['role'].upper()}]\n{m['content']}" for m in history
        )
        input_message = (
            f"<conversation_history>\n{history_block}\n</conversation_history>\n\n"
            f"[USER]\n{message}"
        )
    else:
        input_message = message

    _capture_loop()
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(agent, input_message),
            timeout=90.0,
        )
        # Extract text robustly — handle various result object shapes
        response_text = _extract_text(result)
    except asyncio.TimeoutError:
        response_text = "The request timed out after 90 seconds. Please try a simpler question or try again."
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Strands agent error: %s", e, exc_info=True)
        response_text = f"An error occurred: {e}"

    assistant_result = await store_message(session_id, "assistant", response_text)

    return {
        "response": response_text,
        "session_id": session_id,
        "graph_data": None,
        "entities_extracted": (assistant_result or {}).get("entities", []),
        "preferences_detected": (assistant_result or {}).get("preferences", []),
    }


async def handle_message_stream(message: str, session_id: str | None = None) -> dict:
    """Stream a chat response token-by-token via the SSE collector.

    Strands exposes ``Agent.stream_async`` which yields events as the agent
    runs. We emit each text chunk through ``collector.emit_text_delta``;
    tool-call events fire automatically via ``execute_cypher`` inside each
    @tool. Sync tools run on worker threads and reach back to the event loop
    via ``_run_sync`` — the loop is captured here.
    """
    from app.context_graph_client import get_collector

    session_id = resolve_session_id(session_id)
    collector = get_collector()

    await store_message(session_id, "user", message)
    context = await get_context(session_id, query=message)
    history = context.get("messages", [])

    if history:
        history_block = "\n\n".join(
            f"[{m['role'].upper()}]\n{m['content']}" for m in history
        )
        input_message = (
            f"<conversation_history>\n{history_block}\n</conversation_history>\n\n"
            f"[USER]\n{message}"
        )
    else:
        input_message = message

    _capture_loop()

    response_text = ""
    full_text_parts: list[str] = []
    try:
        async for event in agent.stream_async(input_message):
            # Strands yields dicts with `data` for text deltas and
            # `current_tool_use` for tool activity. We only need text — tool
            # events are pushed by execute_cypher when the @tool runs.
            if isinstance(event, dict):
                chunk = event.get("data")
                if chunk:
                    text_chunk = str(chunk)
                    collector.emit_text_delta(text_chunk)
                    full_text_parts.append(text_chunk)
        response_text = "".join(full_text_parts).strip()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Strands streaming error: %s", e, exc_info=True)
        response_text = "".join(full_text_parts).strip()
        if not response_text:
            response_text = f"An error occurred: {e}"

    if not response_text.strip():
        response_text = "I searched the knowledge graph but couldn't find relevant results for your query. Could you try rephrasing your question?"

    assistant_result = await store_message(session_id, "assistant", response_text)
    if assistant_result:
        collector.emit_entities_extracted(assistant_result.get("entities", []))
        collector.emit_preferences_detected(assistant_result.get("preferences", []))
    collector.emit_done(response_text, session_id)

    return {
        "response": response_text,
        "session_id": session_id,
        "graph_data": None,
    }
