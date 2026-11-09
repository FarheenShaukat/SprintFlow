from django.db.models import Count
from django.shortcuts import get_object_or_404
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
        qs = (
            Task.objects.filter(project__in=accessible_projects_for(self.request.user))
            .select_related("project__workspace", "sprint", "assignee", "reporter")
            .prefetch_related("subtasks")
            .annotate(
                comment_count=Count("comments", distinct=True),
                attachment_count=Count("attachments", distinct=True),
                dependencies_count=Count("dependencies", distinct=True),
            )
            .distinct()
            .order_by("id")
        )
        return qs.filter(project_id=project_id) if project_id else qs

    def perform_create(self, serializer):
        project = serializer.context["project"]
        if not user_can_access_project(self.request.user, project):
            raise PermissionDenied("You do not have access to this project.")
        workspace_role = WorkspaceMember.objects.filter(workspace=project.workspace, user=self.request.user).values_list("role", flat=True).first()
        project_role = ProjectMember.objects.filter(project=project, user=self.request.user).values_list("role", flat=True).first()
        if workspace_role == WorkspaceMember.Role.MEMBER and project_role == ProjectMember.Role.VIEWER:
            raise PermissionDenied("Project viewers cannot create tasks.")
        if workspace_role == WorkspaceMember.Role.MEMBER and not project.workspace.allow_member_create_tasks and project_role != ProjectMember.Role.ADMIN:
            raise PermissionDenied("Members are not allowed to create tasks in this project.")
        task = serializer.save(project=project, reporter=self.request.user)
        log_activity(user=self.request.user, workspace=project.workspace, project=project, task=task, action="task.created", new_value=task.title)

    def perform_update(self, serializer):
        before = serializer.instance
        old_status = before.status
        task = serializer.save()
        if old_status != task.status:
            log_activity(user=self.request.user, workspace=task.project.workspace, project=task.project, task=task, action="task.status_changed", old_value=old_status, new_value=task.status)


class SubTaskViewSet(viewsets.ModelViewSet):
    serializer_class = SubTaskSerializer
    permission_classes = [WorkspaceRolePermission]

    def get_queryset(self):
        return SubTask.objects.filter(
            task_id=self.kwargs["task_id"], task__project__in=accessible_projects_for(self.request.user),
        ).select_related("task__project__workspace").order_by("id")

    def perform_create(self, serializer):
        task = get_object_or_404(Task.objects.select_related("project__workspace"), pk=self.kwargs["task_id"])
        self.check_object_permissions(self.request, SubTask(task=task))
        serializer.save(task=task)


class TaskDependencyViewSet(viewsets.ModelViewSet):
    serializer_class = TaskDependencySerializer
    permission_classes = [WorkspaceRolePermission]

    def get_queryset(self):
        return TaskDependency.objects.filter(
            task_id=self.kwargs["task_id"], task__project__in=accessible_projects_for(self.request.user),
        ).select_related("task__project__workspace").order_by("id")

    def perform_create(self, serializer):
        task = serializer.context["task"]
        self.check_object_permissions(self.request, TaskDependency(task=task))
        serializer.save(task=task)
