from typing import TypedDict


class SprintFlowState(TypedDict, total=False):
    conversation_id: int
    project_id: int | None
    workspace_id: int
    user_id: int
    messages: list[dict]
    project_context: dict
    uploaded_text: str
    user_text: str
    explicit_project_name: str
    provider_preference: str
    draft_plan: dict
    provider: str
    validation_errors: list[str]
    pending_write: dict
    approval_status: str
    last_tool_result: dict
    current_step: str
