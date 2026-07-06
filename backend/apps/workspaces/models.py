from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid


class Workspace(models.Model):
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_workspaces")
    allow_member_create_projects = models.BooleanField(default=False)
    allow_member_create_tasks = models.BooleanField(default=True)
    allow_member_edit_tasks = models.BooleanField(default=True)
    allow_member_comment = models.BooleanField(default=True)
    allow_member_upload_attachments = models.BooleanField(default=True)
    allow_member_invite_members = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class WorkspaceMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspace_memberships")
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("workspace", "user")

    def __str__(self) -> str:
        return f"{self.user} in {self.workspace} ({self.role})"


class WorkspaceInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    full_name = models.CharField(max_length=160, blank=True)
    role = models.CharField(max_length=12, choices=WorkspaceMember.Role.choices, default=WorkspaceMember.Role.MEMBER)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_workspace_invitations")
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="accepted_workspace_invitations")
    email_sent = models.BooleanField(default=False)
    email_error = models.TextField(blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("workspace", "email")
        ordering = ["-created_at"]

    def accept(self, user):
        self.status = self.Status.ACCEPTED
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save(update_fields=["status", "accepted_by", "accepted_at", "updated_at"])
        WorkspaceMember.objects.update_or_create(
            workspace=self.workspace,
            user=user,
            defaults={"role": self.role},
        )

    def __str__(self) -> str:
        return f"{self.email} invited to {self.workspace}"
