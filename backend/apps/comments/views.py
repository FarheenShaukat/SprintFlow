from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from apps.activity.services import log_activity
from apps.core.permissions import WorkspaceRolePermission
from apps.tasks.models import Task
from apps.workspaces.models import WorkspaceMember
from .models import Comment
from .serializers import CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [WorkspaceRolePermission]

    def get_queryset(self):
        qs = Comment.objects.filter(task__project__workspace__memberships__user=self.request.user).select_related("user", "task", "task__project")
        task_id = self.kwargs.get("task_id")
        return qs.filter(task_id=task_id) if task_id else qs

    def perform_create(self, serializer):
        task = Task.objects.select_related("project__workspace").get(pk=self.kwargs["task_id"])
        workspace_role = WorkspaceMember.objects.filter(workspace=task.project.workspace, user=self.request.user).values_list("role", flat=True).first()
        if workspace_role == WorkspaceMember.Role.MEMBER and not task.project.workspace.allow_member_comment:
            raise PermissionDenied("Members are not allowed to comment in this workspace.")
        comment = serializer.save(task=task, user=self.request.user)
        log_activity(user=self.request.user, workspace=task.project.workspace, project=task.project, task=task, action="comment.added", new_value=comment.content[:180])
