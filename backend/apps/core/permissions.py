from rest_framework import permissions

from apps.workspaces.models import WorkspaceMember


class WorkspaceRolePermission(permissions.BasePermission):
    owner_actions = {"destroy"}
    admin_actions = {"create", "update", "partial_update", "destroy"}
    member_actions = {"list", "retrieve", "create", "update", "partial_update"}
    manager_actions = {"create", "update", "partial_update", "destroy"}

    def _workspace_id(self, view, obj=None):
        if obj and hasattr(obj, "workspace_id"):
            return obj.workspace_id
        if obj and hasattr(obj, "project") and hasattr(obj.project, "workspace_id"):
            return obj.project.workspace_id
        return (
            view.kwargs.get("workspace_id")
            or view.kwargs.get("pk")
            or view.request.data.get("workspace")
        )

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(view, "basename", "") == "workspace" and getattr(view, "action", "") in {"list", "create"}:
            return True
        return True

    def has_object_permission(self, request, view, obj):
        workspace_id = self._workspace_id(view, obj)
        if not workspace_id:
            return True
        role = (
            WorkspaceMember.objects.filter(workspace_id=workspace_id, user=request.user)
            .values_list("role", flat=True)
            .first()
        )
        model_name = obj.__class__.__name__
        if model_name == "Workspace":
            if view.action == "destroy":
                return role == WorkspaceMember.Role.OWNER
            if view.action in {"update", "partial_update"}:
                return role in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN}

        if model_name == "WorkspaceMember" and view.action in self.manager_actions:
            return role in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN}

        if model_name == "ProjectMember" and view.action in self.manager_actions:
            project_role = obj.project.project_memberships.filter(user=request.user).values_list("role", flat=True).first()
            return role in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN} or project_role == "admin"

        if role == WorkspaceMember.Role.OWNER:
            return True
        if role == WorkspaceMember.Role.ADMIN:
            return view.action not in self.owner_actions
        if role == WorkspaceMember.Role.MEMBER:
            return view.action in self.member_actions
        return False
