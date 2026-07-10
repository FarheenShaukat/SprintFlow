from django.db.models import Count
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets

from apps.activity.services import log_activity
from apps.core.permissions import WorkspaceRolePermission
from apps.projects.access import accessible_projects_for, user_can_access_project
from apps.projects.models import Project, ProjectMember
from apps.workspaces.models import WorkspaceMember
from .filters import TaskFilter
from .models import SubTask, Task, TaskDependency
from .serializers import SubTaskSerializer, TaskDependencySerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [WorkspaceRolePermission]
    filterset_class = TaskFilter
    search_fields = ["title", "description", "blocked_reason"]
    ordering_fields = ["created_at", "due_date", "priority", "status"]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        if project_id:
            project = Project.objects.filter(pk=project_id).first()
            if project:
                workspace_member = WorkspaceMember.objects.filter(workspace=project.workspace, user=self.request.user).first()
                if workspace_member:
                    ProjectMember.objects.get_or_create(
                        project=project,
                        user=self.request.user,
                        defaults={"role": ProjectMember.Role.ADMIN if workspace_member.role in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN} else ProjectMember.Role.MEMBER},
                    )
        qs = (
            Task.objects.filter(project__in=accessible_projects_for(self.request.user))
            .select_related("project", "sprint", "assignee", "reporter")
            .prefetch_related("subtasks")
            .annotate(
                comment_count=Count("comments", distinct=True),
                attachment_count=Count("attachments", distinct=True),
                dependencies_count=Count("dependencies", distinct=True),
            )
            .distinct()
        )
        return qs.filter(project_id=project_id) if project_id else qs

    def perform_create(self, serializer):
        project = Project.objects.get(pk=self.kwargs["project_id"])
        if not user_can_access_project(self.request.user, project):
            raise PermissionDenied("You do not have access to this project.")
        workspace_role = WorkspaceMember.objects.filter(workspace=project.workspace, user=self.request.user).values_list("role", flat=True).first()
        project_role = ProjectMember.objects.filter(project=project, user=self.request.user).values_list("role", flat=True).first()
        if workspace_role == WorkspaceMember.Role.MEMBER and not project.workspace.allow_member_create_tasks and project_role != ProjectMember.Role.ADMIN:
            raise PermissionDenied("Members are not allowed to create tasks in this project.")
        task = serializer.save(project=project, reporter=self.request.user)
        log_activity(user=self.request.user, workspace=project.workspace, project=project, task=task, action="task.created", new_value=task.title)

    def perform_update(self, serializer):
        before = self.get_object()
        workspace_role = WorkspaceMember.objects.filter(workspace=before.project.workspace, user=self.request.user).values_list("role", flat=True).first()
        project_role = ProjectMember.objects.filter(project=before.project, user=self.request.user).values_list("role", flat=True).first()
        if workspace_role == WorkspaceMember.Role.MEMBER and not before.project.workspace.allow_member_edit_tasks and project_role != ProjectMember.Role.ADMIN:
            raise PermissionDenied("Members are not allowed to edit tasks in this project.")
        old_status = before.status
        task = serializer.save()
        if old_status != task.status:
            log_activity(user=self.request.user, workspace=task.project.workspace, project=task.project, task=task, action="task.status_changed", old_value=old_status, new_value=task.status)


class SubTaskViewSet(viewsets.ModelViewSet):
    serializer_class = SubTaskSerializer
    permission_classes = [WorkspaceRolePermission]

    def get_queryset(self):
        return SubTask.objects.filter(task_id=self.kwargs["task_id"], task__project__workspace__memberships__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(task_id=self.kwargs["task_id"])


class TaskDependencyViewSet(viewsets.ModelViewSet):
    serializer_class = TaskDependencySerializer
    permission_classes = [WorkspaceRolePermission]

    def get_queryset(self):
        return TaskDependency.objects.filter(task_id=self.kwargs["task_id"], task__project__workspace__memberships__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(task_id=self.kwargs["task_id"])
