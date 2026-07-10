from django.utils import timezone
from django.conf import settings

from .checkpoints import langgraph_runtime_available, save_checkpoint
from .models import GeneratedPlan, SprintFlowAgentRun, SprintFlowConversation, SprintFlowMessage
from .llm import generate_plan_with_groq, generate_plan_with_openai, has_llm_provider
from .state import SprintFlowState
from .tools import draft_plan_tool, draft_structured_plan_tool, load_project_context_tool, normalize_plan_tool, repair_plan_tool, validate_plan_tool


def run_agent_turn(
    *,
    conversation: SprintFlowConversation,
    user_text: str,
    uploaded_text: str = "",
    explicit_project_name: str = "",
    provider_preference: str = "groq",
) -> list[SprintFlowMessage]:
    run = SprintFlowAgentRun.objects.create(conversation=conversation, current_step="reading_input")
    _set_conversation_status(conversation, SprintFlowConversation.AgentStatus.RUNNING, "reading_input")
    progress_messages = [
        _progress(conversation, "Reading your input and preparing the agent run.", {"step": "reading_input", "run_id": run.id})
    ]
    project_context = load_project_context_tool(conversation.project)
    conversation.last_context_synced_at = timezone.now()
    conversation.save(update_fields=["last_context_synced_at", "updated_at"])
    progress_messages.append(
        _progress(conversation, "Checking current project data before planning.", {"step": "load_context", "run_id": run.id})
    )

    try:
        state = _run_planning_graph({
            "conversation_id": conversation.id,
            "project_id": conversation.project_id,
            "workspace_id": conversation.workspace_id,
            "user_id": conversation.created_by_id,
            "user_text": user_text,
            "uploaded_text": uploaded_text,
            "explicit_project_name": explicit_project_name,
            "provider_preference": provider_preference,
            "project_context": project_context,
            "messages": list(conversation.messages.values("role", "message_type", "content", "payload", "created_at")[:80]),
        })
    except Exception as exc:
        run.status = SprintFlowAgentRun.Status.FAILED
        run.error = str(exc)
        run.current_step = "failed"
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "error", "current_step", "completed_at"])
        conversation.last_agent_error = str(exc)
        _set_conversation_status(conversation, SprintFlowConversation.AgentStatus.FAILED, "failed")
        raise

    plan = state["draft_plan"]
    provider = state["provider"]
    validation_errors = state["validation_errors"]
    generated_plan = GeneratedPlan.objects.create(
        conversation=conversation,
        plan_json=plan,
        validation_errors=validation_errors,
        status=GeneratedPlan.Status.READY if not validation_errors else GeneratedPlan.Status.DRAFTING,
    )
    run.status = SprintFlowAgentRun.Status.AWAITING_APPROVAL if not validation_errors else SprintFlowAgentRun.Status.FAILED
    run.current_step = "awaiting_approval" if not validation_errors else "validation_failed"
    run.provider = provider
    run.metadata = {"generated_plan_id": generated_plan.id, "validation_errors": validation_errors}
    run.completed_at = timezone.now()
    run.save(update_fields=["status", "current_step", "provider", "metadata", "completed_at"])
    _set_conversation_status(
        conversation,
        SprintFlowConversation.AgentStatus.AWAITING_APPROVAL if not validation_errors else SprintFlowConversation.AgentStatus.FAILED,
        "awaiting_approval" if not validation_errors else "validation_failed",
    )
    save_checkpoint(conversation, {
        "latest_run_id": run.id,
        "latest_plan_id": generated_plan.id,
        "approval_status": "awaiting" if not validation_errors else "needs_repair",
        "provider": provider,
        "langgraph_runtime": "available" if langgraph_runtime_available() else "compatibility_fallback",
    })

    messages = [
        *progress_messages,
        SprintFlowMessage.objects.create(
            conversation=conversation,
            role=SprintFlowMessage.Role.ASSISTANT,
            message_type=SprintFlowMessage.MessageType.CONTEXT_SUMMARY,
            content="I refreshed the live project context.",
            payload=project_context["summary"],
        ),
        SprintFlowMessage.objects.create(
            conversation=conversation,
            role=SprintFlowMessage.Role.ASSISTANT,
            message_type=SprintFlowMessage.MessageType.PLAN_CARD,
            content="I drafted a sprint plan. Review it before anything is written to the database.",
            payload={
                "generated_plan_id": generated_plan.id,
                "plan": plan,
                "validation_errors": validation_errors,
                "provider": provider,
                "status": generated_plan.status,
            },
        ),
    ]
    return messages


def draft_agent_state(state: SprintFlowState) -> SprintFlowState:
    plan, provider = _draft_plan_with_providers(
        user_text=state.get("user_text", ""),
        uploaded_text=state.get("uploaded_text", ""),
        project_context=state.get("project_context", {}),
        explicit_project_name=state.get("explicit_project_name", ""),
        provider_preference=state.get("provider_preference", "groq"),
    )
    plan = normalize_plan_tool(plan)
    current_project = state.get("project_context", {}).get("project")
    if current_project:
        plan["project"]["name"] = current_project["name"]
        if current_project.get("description"):
            plan["project"]["description"] = current_project["description"]
    validation_errors = validate_plan_tool(plan)
    if validation_errors:
        plan = repair_plan_tool(plan)
        validation_errors = validate_plan_tool(plan)
    return {
        **state,
        "draft_plan": plan,
        "provider": provider,
        "validation_errors": validation_errors,
        "pending_write": {"type": "apply_plan"} if not validation_errors else {},
        "approval_status": "awaiting" if not validation_errors else "needs_repair",
        "current_step": "awaiting_approval" if not validation_errors else "validation_failed",
    }


def _run_planning_graph(state: SprintFlowState) -> SprintFlowState:
    if not langgraph_runtime_available():
        return draft_agent_state(state)

    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(SprintFlowState)
    graph.add_node("agent_node", draft_agent_state)
    graph.add_edge(START, "agent_node")
    graph.add_edge("agent_node", END)
    result = graph.compile().invoke(state)
    return result if result.get("draft_plan") else draft_agent_state(state)


def _draft_plan_with_providers(
    *,
    user_text: str,
    uploaded_text: str,
    project_context: dict,
    explicit_project_name: str = "",
    provider_preference: str = "groq",
) -> tuple[dict, str]:
    provider_errors = 0
    structured_plan = draft_structured_plan_tool(
        user_text=user_text,
        uploaded_text=uploaded_text,
        explicit_project_name=explicit_project_name,
    )
    if structured_plan:
        return structured_plan, "structured"

    providers = ["openai", "groq"] if provider_preference == "openai" else ["groq", "openai"]

    for provider in providers:
        if provider == "groq" and has_llm_provider(getattr(settings, "GROQ_API_KEY", "")):
            try:
                return (
                    generate_plan_with_groq(
                        api_key=settings.GROQ_API_KEY,
                        model=getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
                        base_url=getattr(settings, "GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
                        user_text=user_text,
                        uploaded_text=uploaded_text,
                        project_context=project_context,
                        explicit_project_name=explicit_project_name,
                    ),
                    "groq",
                )
            except Exception:
                provider_errors += 1
        if provider == "openai" and has_llm_provider(getattr(settings, "OPENAI_API_KEY", "")):
            try:
                return (
                    generate_plan_with_openai(
                        api_key=settings.OPENAI_API_KEY,
                        model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
                        user_text=user_text,
                        uploaded_text=uploaded_text,
                        project_context=project_context,
                        explicit_project_name=explicit_project_name,
                    ),
                    "openai",
                )
            except Exception:
                provider_errors += 1

    return (
        draft_plan_tool(
            user_text=user_text,
            uploaded_text=uploaded_text,
            project_context=project_context,
            explicit_project_name=explicit_project_name,
        ),
        "fallback_after_error" if provider_errors else "fallback",
    )


def _progress(conversation: SprintFlowConversation, content: str, payload: dict) -> SprintFlowMessage:
    return SprintFlowMessage.objects.create(
        conversation=conversation,
        role=SprintFlowMessage.Role.ASSISTANT,
        message_type=SprintFlowMessage.MessageType.PROGRESS,
        content=content,
        payload=payload,
    )


def _set_conversation_status(conversation: SprintFlowConversation, status: str, step: str) -> None:
    conversation.agent_status = status
    conversation.current_step = step
    if status != SprintFlowConversation.AgentStatus.FAILED:
        conversation.last_agent_error = ""
    conversation.save(update_fields=["agent_status", "current_step", "last_agent_error", "updated_at"])
