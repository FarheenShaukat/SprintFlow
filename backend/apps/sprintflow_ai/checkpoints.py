def langgraph_runtime_available() -> bool:
    try:
        from langgraph.graph import END, START, StateGraph  # noqa: F401
    except Exception:
        return False
    return True


def save_checkpoint(conversation, state: dict) -> None:
    conversation.checkpoint_state = {
        **(conversation.checkpoint_state or {}),
        **state,
    }
    conversation.save(update_fields=["checkpoint_state", "updated_at"])


def load_checkpoint(conversation) -> dict:
    return conversation.checkpoint_state or {}


def get_checkpointer():
    """Return the active checkpoint adapter for this deployment.

    The project stores durable agent state on SprintFlowConversation so it
    works on local SQLite and serverless deployments. When the installed
    LangGraph package set is compatible, graph.py compiles a StateGraph on
    top of this same persisted state. This avoids losing chat/approval state
    if the optional LangGraph runtime import is broken in a developer env.
    """
    return {"type": "django_json", "durable": True}
