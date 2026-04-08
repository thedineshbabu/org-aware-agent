"""
LangGraph agent graph — Phase 1 (minimal: single call_model node, no tools).

Phase 2 adds: ToolNode with rag_search, conditional routing.
Phase 3 adds: db_query, jira_search, jira_create tools.
Phase 4 adds: RBAC tool filtering, iam_lookup tool.
"""
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.prompts import build_system_prompt
from app.agent.state import AgentState
from app.core.config import get_settings


def _get_model(tools: list | None = None) -> ChatAnthropic:
    settings = get_settings()
    model = ChatAnthropic(
        model=settings.claude_model,
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )
    if tools:
        return model.bind_tools(tools)
    return model


def _should_use_tools(state: AgentState) -> str:
    """Route to tools if the last message has tool_calls, otherwise end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


async def call_model(state: AgentState) -> dict:
    """Primary LLM node — builds system prompt and calls Claude."""
    system_prompt = build_system_prompt(state["user_context"])
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    # Phase 4: tools are filtered per user; Phase 1 has no tools
    tools = _get_registered_tools()
    model = _get_model(tools if tools else None)

    response = await model.ainvoke(messages)

    # Track tool calls for audit logging
    tool_calls_record = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            tool_calls_record.append({"name": tc["name"], "args_summary": str(tc.get("args", {}))[:200]})

    existing_tool_calls = state.get("tool_calls", [])
    return {
        "messages": [response],
        "tool_calls": existing_tool_calls + tool_calls_record,
    }


def _get_registered_tools() -> list:
    """
    Return all registered LangGraph tools.
    Phase 1: empty list.
    Subsequent phases add tools here and in runner.py (where RBAC filtering occurs).
    """
    tools = []

    # Phase 2: RAG tool
    try:
        from app.tools.rag import rag_search
        tools.append(rag_search)
    except ImportError:
        pass

    # Phase 3: DB and Jira tools
    try:
        from app.tools.sql import db_query
        tools.append(db_query)
    except ImportError:
        pass

    try:
        from app.tools.jira import jira_search, jira_create
        tools.extend([jira_search, jira_create])
    except ImportError:
        pass

    # Phase 4: IAM tool
    try:
        from app.tools.iam import iam_lookup
        tools.append(iam_lookup)
    except ImportError:
        pass

    return tools


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("call_model", call_model)

    tools = _get_registered_tools()
    if tools:
        builder.add_node("tools", ToolNode(tools))
        builder.add_conditional_edges("call_model", _should_use_tools, {"tools": "tools", END: END})
        builder.add_edge("tools", "call_model")
    else:
        builder.add_edge("call_model", END)

    builder.set_entry_point("call_model")
    return builder.compile()


# Compiled graph singleton
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
