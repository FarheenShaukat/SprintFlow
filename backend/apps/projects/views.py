from django.db.models import Count
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets

from apps.activity.services import log_activity
from apps.core.permissions import WorkspaceRolePermission
from apps.workspaces.models import Workspace, WorkspaceMember
from .models import Project, ProjectMember, Sprint
from .serializers import ProjectMemberSerializer, ProjectSerializer, SprintSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [WorkspaceRolePermission]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "deadline", "name"]

    def get_queryset(self):
        qs = Project.objects.filter(workspace__memberships__user=self.request.user).annotate(task_count=Count("tasks")).distinct()
        workspace_id = self.kwargs.get("workspace_id")
        return qs.filter(workspace_id=workspace_id) if workspace_id else qs

    def perform_create(self, serializer):
        workspace = Workspace.objects.get(pk=self.kwargs["workspace_id"])
        workspace_role = WorkspaceMember.objects.filter(workspace=workspace, user=self.request.user).values_list("role", flat=True).first()
        if workspace_role == WorkspaceMember.Role.MEMBER and not workspace.allow_member_create_projects:
            raise PermissionDenied("Members are not allowed to create projects in this workspace.")
        project = serializer.save(workspace=workspace, created_by=self.request.user)
        ProjectMember.objects.update_or_create(project=project, user=self.request.user, defaults={"role": ProjectMember.Role.ADMIN})
        log_activity(user=self.request.user, workspace=workspace, project=project, action="project.created", new_value=project.name)


class SprintViewSet(viewsets.ModelViewSet):
    serializer_class = SprintSerializer
    permission_classes = [WorkspaceRolePermission]
    ordering_fields = ["start_date", "end_date", "created_at"]

    def get_queryset(self):
        qs = Sprint.objects.filter(project__workspace__memberships__user=self.request.user).select_related("project")
        project_id = self.kwargs.get("project_id")
        return qs.filter(project_id=project_id) if project_id else qs

    def perform_create(self, serializer):
        project = Project.objects.get(pk=self.kwargs["project_id"])
        sprint = serializer.save(project=project)
        log_activity(user=self.request.user, workspace=project.workspace, project=project, action="sprint.created", new_value=sprint.name)


class ProjectMemberViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectMemberSerializer
    permission_classes = [WorkspaceRolePermission]

    def get_queryset(self):
        project = Project.objects.filter(pk=self.kwargs["project_id"], workspace__memberships__user=self.request.user).first()
        if project:
            for membership in project.workspace.memberships.select_related("user"):
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=membership.user,
                    defaults={"role": ProjectMember.Role.ADMIN if membership.role in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN} else ProjectMember.Role.MEMBER},
                )
        return ProjectMember.objects.filter(
            project_id=self.kwargs["project_id"],
            project__workspace__memberships__user=self.request.user,
        ).select_related("user", "project")

    def _require_project_manager(self, project):
        role = ProjectMember.objects.filter(project=project, user=self.request.user).values_list("role", flat=True).first()
        workspace_role = WorkspaceMember.objects.filter(workspace=project.workspace, user=self.request.user).values_list("role", flat=True).first()
        if role != ProjectMember.Role.ADMIN and workspace_role not in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN}:
            raise PermissionDenied("Only project admins or workspace admins can manage people in this project.")

    def perform_create(self, serializer):
        project = Project.objects.get(pk=self.kwargs["project_id"])
        self._require_project_manager(project)
        serializer.save(project=project)

    def perform_update(self, serializer):
        self._require_project_manager(serializer.instance.project)
        serializer.save()

    def perform_destroy(self, instance):
        self._require_project_manager(instance.project)
        instance.delete()
