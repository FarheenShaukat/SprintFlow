from .graph import draft_agent_state


def agent_node(state: dict) -> dict:
    """Central planning node used by the LangGraph-compatible runner."""
    return draft_agent_state(state)
