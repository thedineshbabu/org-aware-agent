"""
RBAC tool gate — Phase 4.
Controls which LangGraph tools each user role may invoke.
"""
from app.auth.models import UserContext

# Empty list means the tool is available to all authenticated users
TOOL_ROLE_MAP: dict[str, list[str]] = {
    "iam_lookup": ["it_admin"],
    "db_query": ["it_admin", "manager", "developer"],
    "jira_create": [],
    "jira_search": [],
    "rag_search": [],
}


def filter_tools_for_user(all_tools: list, user_context: UserContext) -> list:
    """Return only the tools the user is authorized to invoke."""
    allowed = []
    for tool in all_tools:
        required_roles = TOOL_ROLE_MAP.get(tool.name, [])
        if not required_roles or user_context.has_role(*required_roles):
            allowed.append(tool)
    return allowed
