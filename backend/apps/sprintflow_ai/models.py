import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.projects.models import Project
from apps.workspaces.models import Workspace


class SprintFlowConversation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    class AgentStatus(models.TextChoices):
        IDLE = "idle", "Idle"
        RUNNING = "running", "Running"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting Approval"
        APPLYING = "applying", "Applying"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="sprintflow_conversations")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sprintflow_conversations", null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sprintflow_conversations")
    thread_id = models.CharField(max_length=80, unique=True, default=uuid.uuid4)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    agent_status = models.CharField(max_length=32, choices=AgentStatus.choices, default=AgentStatus.IDLE)
    current_step = models.CharField(max_length=120, blank=True)
    checkpoint_state = models.JSONField(default=dict, blank=True)
    last_agent_error = models.TextField(blank=True)
    last_context_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "created_by"],
                condition=Q(project__isnull=False),
                name="unique_sprintflow_conversation_per_project_user",
            )
        ]

    def __str__(self) -> str:
        return f"SprintFlow AI for {self.created_by} on {self.project or self.workspace}"


class SprintFlowMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        PROGRESS = "progress", "Progress"
        PLAN_CARD = "plan_card", "Plan Card"
        CONFIRMATION = "confirmation", "Confirmation"
        CONTEXT_SUMMARY = "context_summary", "Context Summary"

    conversation = models.ForeignKey(SprintFlowConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=Role.choices)
    message_type = models.CharField(max_length=24, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:60]}"


class GeneratedPlan(models.Model):
    class Status(models.TextChoices):
        DRAFTING = "drafting", "Drafting"
        READY = "ready_for_approval", "Ready for Approval"
        APPLIED = "applied", "Applied"

    conversation = models.ForeignKey(SprintFlowConversation, on_delete=models.CASCADE, related_name="generated_plans")
    plan_json = models.JSONField(default=dict)
    validation_errors = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFTING)
    applied_project = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name="applied_sprintflow_plans", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Generated plan {self.id} ({self.status})"


class SprintFlowAgentRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting Approval"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    conversation = models.ForeignKey(SprintFlowConversation, on_delete=models.CASCADE, related_name="agent_runs")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.RUNNING)
    current_step = models.CharField(max_length=120, blank=True)
    provider = models.CharField(max_length=64, blank=True)
    error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at", "-id"]

    def __str__(self) -> str:
        return f"SprintFlow AI run {self.id} ({self.status})"
