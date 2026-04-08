"""
Agent runner — wraps LangGraph graph invocation.

Handles:
- Session state reconstruction from DB messages
- User context injection
- RBAC tool filtering (Phase 4)
- Streaming via astream_events (Phase 5)
"""
import time
import uuid
from typing import AsyncGenerator

import structlog
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.graph import get_graph
from app.agent.state import AgentState, Citation
from app.auth.models import UserContext

logger = structlog.get_logger(__name__)


async def run_agent(
    session_id: str,
    user_message: str,
    user_context: UserContext,
    message_history: list[dict] | None = None,
) -> dict:
    """
    Invoke the agent for a single user turn.

    Returns a dict with:
    - content: str — the assistant's text response
    - citations: list[Citation]
    - tool_calls: list[dict] — for audit logging
    - latency_ms: int
    """
    start = time.monotonic()

    # Reconstruct message history
    lc_messages = []
    for msg in (message_history or []):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))

    # Append current user message
    lc_messages.append(HumanMessage(content=user_message))

    initial_state: AgentState = {
        "messages": lc_messages,
        "user_context": user_context.to_prompt_dict(),
        "session_id": session_id,
        "tool_calls": [],
        "citations": [],
        "pending_jira_ticket": None,
        "awaiting_confirmation": False,
    }

    graph = get_graph()

    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception:
        logger.exception("agent_invocation_failed", session_id=session_id, user_id=user_context.user_id)
        raise

    latency_ms = int((time.monotonic() - start) * 1000)

    # Extract last AI message
    ai_messages = [m for m in final_state["messages"] if isinstance(m, AIMessage)]
    content = ai_messages[-1].content if ai_messages else "I'm sorry, I couldn't generate a response."

    # Ensure content is a string (Claude sometimes returns list of content blocks)
    if isinstance(content, list):
        content = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )

    return {
        "content": content,
        "citations": final_state.get("citations", []),
        "tool_calls": final_state.get("tool_calls", []),
        "latency_ms": latency_ms,
        "awaiting_confirmation": final_state.get("awaiting_confirmation", False),
        "pending_jira_ticket": final_state.get("pending_jira_ticket"),
    }
