"""Manufacturing AI Agent — Strands implementation."""

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
from app.manufacturing_reasoning import execute_manufacturing_tool


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


SYSTEM_PROMPT = """You are an AI manufacturing intelligence assistant with access to a comprehensive
knowledge graph of production data. You help plant managers, quality engineers,
and supply chain coordinators optimize production, maintain quality standards,
and manage supplier relationships.

Your capabilities include:
- Searching and analyzing work orders, machines, and production lines
- Monitoring quality metrics and defect trends
- Evaluating supplier performance and managing supply chain risks
- Tracking equipment maintenance and operational status
- Optimizing production scheduling and resource allocation

Always provide accurate, data-driven responses. When making recommendations,
cite specific production metrics, quality data, and historical performance
from the knowledge graph.


IMPORTANT: You MUST use the available tools to query the knowledge graph before answering any question about the data. Never guess or make up information — always use tools to look up actual data from the graph.

CRITICAL: Call tools DIRECTLY without any introductory text. Do NOT say "I'll search for..." or "Let me look up..." before calling a tool — just call the tool immediately. Only generate text AFTER you have received the tool results and are ready to provide your final answer."""

SYSTEM_PROMPT += """

For manufacturing reasoning, separate observed evidence, missing evidence, and assumptions. Use only explicit graph nodes and relationships returned by tools. Do not infer relationships from matching names, identifiers, dates, or timestamps. When evidence is absent, say so and request clarification. Cite node IDs and relationship types when present.
"""

# ---------------------------------------------------------------------------
# Agent tools — domain-specific for Manufacturing
# ---------------------------------------------------------------------------

@tool
def lookup_field_semantics(query: str) -> str:
    """Look up enterprise field definitions and their mapped business concepts"""
    cypher = """MATCH (field:CDSField)
    WHERE toLower(field.field_name) CONTAINS toLower($query)
       OR toLower(field.name) CONTAINS toLower($query)
    OPTIONAL MATCH (view:CDSView)-[:DEFINES_FIELD]->(field)
    OPTIONAL MATCH (field)-[:REPRESENTS_CONCEPT]->(concept:BusinessConcept)
    RETURN field, view.name AS view_name, concept.name AS concept_name,
           concept.scope_note AS concept_scope_note
    ORDER BY view_name, field.field_name
    LIMIT 25
"""
    params = {
        "query": query,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="lookup_field_semantics"))
    return json.dumps(result, default=str)

@tool
def search_sales_documents(sales_document: str) -> str:
    """Search sales documents and retrieve their semantic source view"""
    cypher = """MATCH (document:SalesDocument)
    WHERE document.sales_document = $sales_document OR $sales_document = ''
    OPTIONAL MATCH (document)-[:INSTANCE_OF_VIEW]->(view:CDSView)
    OPTIONAL MATCH (document)-[:SOURCED_FROM]->(source:SourceDataset)
    RETURN document, view.name AS view_name, source.name AS source_dataset
    ORDER BY document.sales_document
    LIMIT 25
"""
    params = {
        "sales_document": sales_document,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="search_sales_documents"))
    return json.dumps(result, default=str)

@tool
def search_machine(query: str) -> str:
    """Search for machines by name, type, or status"""
    cypher = """MATCH (m:Machine)
    WHERE toLower(m.name) CONTAINS toLower($query)
       OR toLower(coalesce(m.machine_type, '')) CONTAINS toLower($query)
       OR toLower(coalesce(m.status, '')) CONTAINS toLower($query)
    OPTIONAL MATCH (m)-[:OPERATED_BY]->(pl:ProductionLine)
    RETURN m, pl.name AS production_line
    ORDER BY m.name
    LIMIT 20
"""
    params = {
        "query": query,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="search_machine"))
    return json.dumps(result, default=str)

@tool
def get_work_orders(status: str) -> str:
    """Get work orders filtered by status or priority"""
    cypher = """MATCH (wo:WorkOrder)
    WHERE wo.status = $status OR $status = 'all'
    OPTIONAL MATCH (wo)-[:PRODUCED_ON]->(pl:ProductionLine)
    OPTIONAL MATCH (wo)-[:DEPENDS_ON]->(p:Part)
    RETURN wo, pl.name AS production_line, collect(p.name) AS required_parts
    ORDER BY CASE wo.priority
      WHEN 'critical' THEN 1
      WHEN 'high' THEN 2
      WHEN 'medium' THEN 3
      ELSE 4 END
    LIMIT 50
"""
    params = {
        "status": status,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="get_work_orders"))
    return json.dumps(result, default=str)

@tool
def quality_analysis(query: str) -> str:
    """Analyze quality metrics for a specific part or production line"""
    cypher = """MATCH (qr:QualityReport)-[:INSPECTED]->(p:Part)
    WHERE toLower(p.name) CONTAINS toLower($query)
       OR toLower(p.part_number) CONTAINS toLower($query)
    RETURN p.name AS part, p.part_number,
           count(qr) AS total_inspections,
           sum(CASE WHEN qr.result = 'pass' THEN 1 ELSE 0 END) AS passed,
           sum(CASE WHEN qr.result = 'fail' THEN 1 ELSE 0 END) AS failed,
           avg(qr.defect_count) AS avg_defects
    ORDER BY failed DESC
"""
    params = {
        "query": query,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="quality_analysis"))
    return json.dumps(result, default=str)

@tool
def supplier_performance() -> str:
    """Evaluate supplier performance based on quality and delivery"""
    cypher = """MATCH (s:Supplier)<-[:SUPPLIED_BY]-(p:Part)
    OPTIONAL MATCH (qr:QualityReport)-[:INSPECTED]->(p)
    WITH s, count(DISTINCT p) AS parts_supplied,
         count(qr) AS total_inspections,
         sum(CASE WHEN qr.result = 'fail' THEN 1 ELSE 0 END) AS failures
    RETURN s.name AS supplier, s.quality_rating, s.lead_time_days,
           parts_supplied, total_inspections, failures,
           CASE WHEN total_inspections > 0
             THEN round(1000.0 * (total_inspections - failures) / total_inspections) / 10.0
             ELSE null END AS pass_rate_pct
    ORDER BY s.quality_rating DESC
"""
    params = {
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="supplier_performance"))
    return json.dumps(result, default=str)

@tool
def production_metrics(query: str) -> str:
    """Get production efficiency and output metrics for production lines"""
    cypher = """MATCH (pl:ProductionLine)
    WHERE toLower(pl.name) CONTAINS toLower($query) OR $query = 'all'
    OPTIONAL MATCH (wo:WorkOrder)-[:PRODUCED_ON]->(pl)
    RETURN pl.name AS line, pl.status, pl.capacity_per_hour,
           pl.efficiency_rating,
           count(wo) AS total_orders,
           sum(CASE WHEN wo.status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
           sum(wo.quantity) AS total_units_ordered
    ORDER BY pl.name
"""
    params = {
        "query": query,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="production_metrics"))
    return json.dumps(result, default=str)

@tool
def list_machines(limit: str) -> str:
    """List Machine records with optional limit"""
    cypher = """MATCH (n:Machine)
    RETURN n
    ORDER BY n.name
    LIMIT toInteger($limit)
"""
    params = {
        "limit": limit,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="list_machines"))
    return json.dumps(result, default=str)

@tool
def get_machine_by_id(id: str) -> str:
    """Get a specific Machine by ID with all connections"""
    cypher = """MATCH (n:Machine {machine_id: $id})
    OPTIONAL MATCH (n)-[r]-(related)
    RETURN n, type(r) AS relationship, labels(related) AS related_labels, related.name AS related_name
    LIMIT 50
"""
    params = {
        "id": id,
    }
    result = _run_sync(execute_cypher(cypher, params, tool_name="get_machine_by_id"))
    return json.dumps(result, default=str)


@tool
def get_work_order(id: str) -> str:
    """Retrieve one scoped manufacturing work order by identifier."""
    return json.dumps(_run_sync(execute_manufacturing_tool("get_work_order", {"id": id})), default=str)


@tool
def get_bom_components(work_order_id: str) -> str:
    """Retrieve explicit bill-of-material requirements for a work order."""
    return json.dumps(_run_sync(execute_manufacturing_tool("get_bom_components", {"work_order_id": work_order_id})), default=str)


@tool
def get_machine_status(machine_id: str) -> str:
    """Retrieve a machine and its explicitly assigned work center."""
    return json.dumps(_run_sync(execute_manufacturing_tool("get_machine_status", {"machine_id": machine_id})), default=str)


@tool
def get_supplier_parts(supplier_id: str) -> str:
    """Retrieve explicit supplier commitments and supplied parts."""
    return json.dumps(_run_sync(execute_manufacturing_tool("get_supplier_parts", {"supplier_id": supplier_id})), default=str)


@tool
def get_material_requirements(part_id: str) -> str:
    """Retrieve explicit material requirements for a part."""
    return json.dumps(_run_sync(execute_manufacturing_tool("get_material_requirements", {"part_id": part_id})), default=str)


@tool
def get_production_events(work_order_id: str) -> str:
    """Retrieve explicit production events for a work order."""
    return json.dumps(_run_sync(execute_manufacturing_tool("get_production_events", {"work_order_id": work_order_id})), default=str)


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
        lookup_field_semantics,
        search_sales_documents,
        search_machine,
        get_work_orders,
        quality_analysis,
        supplier_performance,
        production_metrics,
        list_machines,
        get_machine_by_id,
    get_work_order,
    get_bom_components,
    get_machine_status,
    get_supplier_parts,
    get_material_requirements,
    get_production_events,
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
