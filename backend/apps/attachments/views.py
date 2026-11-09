from django.conf import settings
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from apps.activity.services import log_activity
from apps.core.permissions import WorkspaceRolePermission
from apps.tasks.models import Task
from apps.projects.access import accessible_projects_for
from apps.projects.models import ProjectMember
from apps.workspaces.models import WorkspaceMember
from .models import Attachment
from .serializers import AttachmentSerializer
from .services import build_supabase_storage_url


class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [WorkspaceRolePermission]

    def get_queryset(self):
        qs = Attachment.objects.filter(task__project__in=accessible_projects_for(self.request.user)).select_related("uploaded_by", "task", "task__project").order_by("created_at", "id")
        task_id = self.kwargs.get("task_id")
        return qs.filter(task_id=task_id) if task_id else qs

    def perform_create(self, serializer):
        task = get_object_or_404(Task.objects.filter(project__in=accessible_projects_for(self.request.user)).select_related("project__workspace"), pk=self.kwargs["task_id"])
        workspace_role = WorkspaceMember.objects.filter(workspace=task.project.workspace, user=self.request.user).values_list("role", flat=True).first()
        if workspace_role == WorkspaceMember.Role.MEMBER:
            if not task.project.workspace.allow_member_upload_attachments or ProjectMember.objects.filter(project=task.project, user=self.request.user, role="viewer").exists():
                raise PermissionDenied("You are not allowed to upload attachments in this project.")
        file_url = build_supabase_storage_url(self.request.data.get("file_url", ""), supabase_url=settings.SUPABASE_URL)
        attachment = serializer.save(task=task, uploaded_by=self.request.user, file_url=file_url)
        log_activity(user=self.request.user, workspace=task.project.workspace, project=task.project, task=task, action="attachment.uploaded", new_value=attachment.file_name)
