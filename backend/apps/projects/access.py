from apps.projects.models import Project, ProjectMember
from apps.workspaces.models import WorkspaceMember


def workspace_role_for(user, workspace_id):
    return WorkspaceMember.objects.filter(workspace_id=workspace_id, user=user).values_list("role", flat=True).first()


def can_manage_workspace_projects(user, workspace_id):
    return workspace_role_for(user, workspace_id) in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN}


def accessible_projects_for(user):
    admin_workspace_ids = WorkspaceMember.objects.filter(
        user=user,
        role__in=[WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN],
    ).values("workspace_id")
    member_project_ids = ProjectMember.objects.filter(user=user).values("project_id")
    return Project.objects.filter(workspace_id__in=admin_workspace_ids) | Project.objects.filter(id__in=member_project_ids)


def user_can_access_project(user, project):
    if can_manage_workspace_projects(user, project.workspace_id):
        return True
    return ProjectMember.objects.filter(project=project, user=user).exists()
