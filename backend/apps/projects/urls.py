from django.urls import path

from .views import ProjectMemberViewSet, ProjectViewSet, SprintViewSet

project_list = ProjectViewSet.as_view({"get": "list", "post": "create"})
project_detail = ProjectViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})
sprint_list = SprintViewSet.as_view({"get": "list", "post": "create"})
sprint_detail = SprintViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})
project_member_list = ProjectMemberViewSet.as_view({"get": "list", "post": "create"})
project_member_detail = ProjectMemberViewSet.as_view({"patch": "partial_update", "delete": "destroy"})

urlpatterns = [
    path("workspaces/<int:workspace_id>/projects", project_list, name="workspace-projects-no-slash"),
    path("workspaces/<int:workspace_id>/projects/", project_list, name="workspace-projects"),
    path("projects/<int:pk>", project_detail, name="project-detail-no-slash"),
    path("projects/<int:pk>/", project_detail, name="project-detail"),
    path("projects/<int:project_id>/sprints", sprint_list, name="project-sprints-no-slash"),
    path("projects/<int:project_id>/sprints/", sprint_list, name="project-sprints"),
    path("sprints/<int:pk>", sprint_detail, name="sprint-detail-no-slash"),
    path("sprints/<int:pk>/", sprint_detail, name="sprint-detail"),
    path("projects/<int:project_id>/members", project_member_list, name="project-members-no-slash"),
    path("projects/<int:project_id>/members/", project_member_list, name="project-members"),
    path("projects/<int:project_id>/members/<int:pk>", project_member_detail, name="project-member-detail-no-slash"),
    path("projects/<int:project_id>/members/<int:pk>/", project_member_detail, name="project-member-detail"),
]
