from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.access import accessible_projects_for, can_manage_workspace_projects
from apps.projects.models import Project, ProjectMember
from apps.workspaces.models import Workspace, WorkspaceMember
from .extractors import extract_uploaded_text
from .graph import run_agent_turn
from .models import GeneratedPlan, SprintFlowConversation, SprintFlowMessage
from .serializers import ApprovePlanSerializer, SendMessageSerializer, SprintFlowConversationSerializer, SprintFlowMessageSerializer
from .tools import apply_plan_tool, load_project_context_tool, validate_plan_tool


def _workspace_role(user, workspace_id):
    return WorkspaceMember.objects.filter(workspace_id=workspace_id, user=user).values_list("role", flat=True).first()


def _require_workspace_member(user, workspace_id):
    role = _workspace_role(user, workspace_id)
    if not role:
        raise PermissionDenied("You are not a member of this workspace.")
    return role


def _get_project_for_user(project_id, user):
    return get_object_or_404(accessible_projects_for(user), pk=project_id)


def _is_project_ai_admin(user, project):
    if can_manage_workspace_projects(user, project.workspace_id):
        return True
    return ProjectMember.objects.filter(project=project, user=user, role=ProjectMember.Role.ADMIN).exists()


def _require_project_ai_admin(user, project):
    if not _is_project_ai_admin(user, project):
        raise PermissionDenied("Only workspace admins or project admins can use SprintFlow AI.")


def _require_workspace_ai_admin(user, workspace_id):
    if not can_manage_workspace_projects(user, workspace_id):
        raise PermissionDenied("Only workspace admins can start SprintFlow AI for a new project.")


class ProjectSprintFlowConversationView(APIView):
    def get(self, request, project_id):
        project = _get_project_for_user(project_id, request.user)
        _require_project_ai_admin(request.user, project)
        conversation, created = SprintFlowConversation.objects.get_or_create(
            project=project,
            created_by=request.user,
            defaults={"workspace": project.workspace},
        )
        if created:
            context = load_project_context_tool(project)
            SprintFlowMessage.objects.create(
                conversation=conversation,
                role=SprintFlowMessage.Role.ASSISTANT,
                message_type=SprintFlowMessage.MessageType.CONTEXT_SUMMARY,
                content="I loaded this project's current state.",
                payload=context["summary"],
            )
        return Response(SprintFlowConversationSerializer(conversation).data)


class WorkspaceNewSprintFlowConversationView(APIView):
    def post(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        _require_workspace_ai_admin(request.user, workspace.id)
        conversation = SprintFlowConversation.objects.create(workspace=workspace, created_by=request.user)
        SprintFlowMessage.objects.create(
            conversation=conversation,
            role=SprintFlowMessage.Role.ASSISTANT,
            message_type=SprintFlowMessage.MessageType.TEXT,
            content="Tell me what you want to build. I can draft a project plan before creating anything.",
        )
        return Response(SprintFlowConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)


class SprintFlowMessageView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, project_id=None, conversation_id=None):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = self._get_conversation(request, project_id, conversation_id)
        content = serializer.validated_data.get("content", "")
        raw_uploaded_text = serializer.validated_data.get("uploaded_text", "")
        uploaded_file = serializer.validated_data.get("file")
        if not content.strip() and not uploaded_file and not raw_uploaded_text.strip():
            raise ValidationError("Send a message or attach a file.")

        try:
            extracted_text = extract_uploaded_text(uploaded_file)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        uploaded_text = "\n\n".join(part for part in [raw_uploaded_text.strip(), extracted_text.strip()] if part)

        SprintFlowMessage.objects.create(
            conversation=conversation,
            role=SprintFlowMessage.Role.USER,
            message_type=SprintFlowMessage.MessageType.TEXT,
            content=content or f"Uploaded {uploaded_file.name}",
            payload={"file_name": uploaded_file.name if uploaded_file else ""},
        )
        assistant_messages = run_agent_turn(
            conversation=conversation,
            user_text=content,
            uploaded_text=uploaded_text,
            provider_preference=serializer.validated_data.get("ai_provider", "groq"),
            explicit_project_name=_resolve_explicit_project_name(
                conversation=conversation,
                serializer_value=serializer.validated_data.get("project_name", ""),
                content=content,
            ),
        )
        return Response(SprintFlowMessageSerializer(assistant_messages, many=True).data, status=status.HTTP_201_CREATED)

    def _get_conversation(self, request, project_id, conversation_id):
        if project_id:
            project = _get_project_for_user(project_id, request.user)
            _require_project_ai_admin(request.user, project)
            conversation, _ = SprintFlowConversation.objects.get_or_create(
                project=project,
                created_by=request.user,
                defaults={"workspace": project.workspace},
            )
            return conversation
        conversation = get_object_or_404(SprintFlowConversation, pk=conversation_id, project__isnull=True, created_by=request.user)
        _require_workspace_ai_admin(request.user, conversation.workspace_id)
        return conversation


def _resolve_explicit_project_name(*, conversation, serializer_value: str, content: str) -> str:
    if conversation.project:
        return conversation.project.name

    explicit_name = (serializer_value or "").strip() or _extract_project_name_from_text(content)
    if explicit_name:
        conversation.checkpoint_state = {
            **(conversation.checkpoint_state or {}),
            "user_specified_project_name": explicit_name,
        }
        conversation.save(update_fields=["checkpoint_state", "updated_at"])
        return explicit_name

    return (conversation.checkpoint_state or {}).get("user_specified_project_name", "")


def _extract_project_name_from_text(content: str) -> str:
    import re

    patterns = [
        r"\b(?:call|name)\s+(?:it|this|the project)\s+(?P<name>[A-Za-z0-9][A-Za-z0-9 _-]{1,80})",
        r"\bproject\s+name\s*(?:is|:)\s*(?P<name>[A-Za-z0-9][A-Za-z0-9 _-]{1,80})",
    ]
    for pattern in patterns:
        match = re.search(pattern, content, flags=re.IGNORECASE)
        if match:
            return re.split(r"[.!?\n\r]", match.group("name").strip())[0].strip()[:180]
    return ""


class SprintFlowEventsView(APIView):
    def get(self, request, project_id):
        project = _get_project_for_user(project_id, request.user)
        _require_project_ai_admin(request.user, project)
        conversation = get_object_or_404(SprintFlowConversation, project=project, created_by=request.user)
        context = load_project_context_tool(project)
        latest_run = conversation.agent_runs.first()
        latest_plan = SprintFlowConversationSerializer(conversation).data["latest_plan"]
        return Response({
            "conversation_id": conversation.id,
            "status": conversation.status,
            "agent_status": conversation.agent_status,
            "current_step": conversation.current_step,
            "last_agent_error": conversation.last_agent_error,
            "checkpoint": {
                "thread_id": conversation.thread_id,
                "state": conversation.checkpoint_state,
            },
            "latest_run": {
                "id": latest_run.id,
                "status": latest_run.status,
                "current_step": latest_run.current_step,
                "provider": latest_run.provider,
                "error": latest_run.error,
                "metadata": latest_run.metadata,
                "started_at": latest_run.started_at,
                "completed_at": latest_run.completed_at,
            } if latest_run else None,
            "context_summary": context["summary"],
            "latest_plan": latest_plan,
            "pending_approval": bool(latest_plan and latest_plan["status"] == GeneratedPlan.Status.READY),
        })


class SprintFlowApproveView(APIView):
    def post(self, request, project_id=None, conversation_id=None):
        serializer = ApprovePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = self._get_conversation(request, project_id, conversation_id)
        generated_plan = get_object_or_404(GeneratedPlan, pk=serializer.validated_data["generated_plan_id"], conversation=conversation)
        if generated_plan.status == GeneratedPlan.Status.APPLIED:
            raise ValidationError("This plan has already been applied.")
        if "plan_json" in serializer.validated_data:
            generated_plan.plan_json = serializer.validated_data["plan_json"]
            generated_plan.validation_errors = validate_plan_tool(generated_plan.plan_json)
            generated_plan.save(update_fields=["plan_json", "validation_errors", "updated_at"])
        if generated_plan.validation_errors:
            raise ValidationError({"validation_errors": generated_plan.validation_errors})

        conversation.agent_status = SprintFlowConversation.AgentStatus.APPLYING
        conversation.current_step = "applying"
        conversation.save(update_fields=["agent_status", "current_step", "updated_at"])
        try:
            result = apply_plan_tool(conversation=conversation, generated_plan=generated_plan, user=request.user)
        except ValueError as exc:
            conversation.agent_status = SprintFlowConversation.AgentStatus.FAILED
            conversation.current_step = "apply_failed"
            conversation.last_agent_error = str(exc)
            conversation.save(update_fields=["agent_status", "current_step", "last_agent_error", "updated_at"])
            raise ValidationError(str(exc)) from exc
        conversation.agent_status = SprintFlowConversation.AgentStatus.COMPLETED
        conversation.current_step = "applied"
        conversation.last_agent_error = ""
        conversation.save(update_fields=["agent_status", "current_step", "last_agent_error", "updated_at"])
        SprintFlowMessage.objects.create(
            conversation=conversation,
            role=SprintFlowMessage.Role.ASSISTANT,
            message_type=SprintFlowMessage.MessageType.CONFIRMATION,
            content=f"Created {result['sprint_count']} sprints and {result['task_count']} tasks.",
            payload=result,
        )
        return Response(result)

    def _get_conversation(self, request, project_id, conversation_id):
        if project_id:
            project = _get_project_for_user(project_id, request.user)
            _require_project_ai_admin(request.user, project)
            return get_object_or_404(SprintFlowConversation, project=project, created_by=request.user)
        conversation = get_object_or_404(SprintFlowConversation, pk=conversation_id, project__isnull=True, created_by=request.user)
        _require_workspace_ai_admin(request.user, conversation.workspace_id)
        return conversation
