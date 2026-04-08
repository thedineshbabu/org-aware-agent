from dataclasses import dataclass, field
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


@dataclass
class Citation:
    doc_name: str
    section: str
    url: str
    chunk_text: str
    last_updated: str = ""


class AgentState(TypedDict):
    # Core message history — add_messages handles append-only merge
    messages: Annotated[list[BaseMessage], add_messages]

    # Identity context (injected before every run)
    user_context: dict

    # Session tracking
    session_id: str

    # Tool invocation record (for audit log)
    tool_calls: list[dict]

    # RAG citations accumulated during a turn
    citations: list[Citation]

    # Jira create multi-turn state (Phase 3)
    pending_jira_ticket: dict | None

    # Whether we are waiting for the user to confirm a Jira ticket creation
    awaiting_confirmation: bool
