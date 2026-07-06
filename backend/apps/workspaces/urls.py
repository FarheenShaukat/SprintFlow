from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InvitationAcceptView, WorkspaceInviteView, WorkspaceMemberViewSet, WorkspaceViewSet

router = DefaultRouter()
router.register("workspaces", WorkspaceViewSet, basename="workspace")

member_list = WorkspaceMemberViewSet.as_view({"get": "list", "post": "create"})
member_detail = WorkspaceMemberViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})

urlpatterns = [
    path("", include(router.urls)),
    path("workspaces", WorkspaceViewSet.as_view({"get": "list", "post": "create"}), name="workspace-list-no-slash"),
    path("workspaces/<int:pk>", WorkspaceViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}), name="workspace-detail-no-slash"),
    path("workspaces/<int:workspace_id>/members", member_list, name="workspace-members-no-slash"),
    path("workspaces/<int:workspace_id>/members/", member_list, name="workspace-members"),
    path("workspaces/<int:workspace_id>/members/<int:pk>", member_detail, name="workspace-member-detail-no-slash"),
    path("workspaces/<int:workspace_id>/members/<int:pk>/", member_detail, name="workspace-member-detail"),
    path("workspaces/<int:workspace_id>/invitations", WorkspaceInviteView.as_view(), name="workspace-invite-no-slash"),
    path("workspaces/<int:workspace_id>/invitations/", WorkspaceInviteView.as_view(), name="workspace-invite"),
    path("invitations/<uuid:token>/accept", InvitationAcceptView.as_view(), name="invitation-accept-no-slash"),
    path("invitations/<uuid:token>/accept/", InvitationAcceptView.as_view(), name="invitation-accept"),
]
