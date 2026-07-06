from django.conf import settings
from rest_framework import viewsets

from apps.activity.services import log_activity
from apps.core.permissions import WorkspaceRolePermission
from apps.tasks.models import Task
from .models import Attachment
from .serializers import AttachmentSerializer
from .services import build_supabase_storage_url


class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [WorkspaceRolePermission]

    def get_queryset(self):
        qs = Attachment.objects.filter(task__project__workspace__memberships__user=self.request.user).select_related("uploaded_by", "task", "task__project")
        task_id = self.kwargs.get("task_id")
        return qs.filter(task_id=task_id) if task_id else qs

    def perform_create(self, serializer):
        task = Task.objects.select_related("project__workspace").get(pk=self.kwargs["task_id"])
        file_url = build_supabase_storage_url(self.request.data.get("file_url", ""), supabase_url=settings.SUPABASE_URL)
        attachment = serializer.save(task=task, uploaded_by=self.request.user, file_url=file_url)
        log_activity(user=self.request.user, workspace=task.project.workspace, project=task.project, task=task, action="attachment.uploaded", new_value=attachment.file_name)
