from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InvitationAcceptView, WorkspaceInviteView, WorkspaceMemberViewSet, WorkspaceViewSet

router = DefaultRouter()
router.register("workspaces", WorkspaceViewSet, basename="workspace")

member_list = WorkspaceMemberViewSet.as_view({"get": "list", "post": "create"})
member_detail = WorkspaceMemberViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})

urlpatterns = [
    path("", include(router.urls)),
    path("workspaces/<int:workspace_id>/members/", member_list, name="workspace-members"),
    path("workspaces/<int:workspace_id>/members/<int:pk>/", member_detail, name="workspace-member-detail"),
    path("workspaces/<int:workspace_id>/invitations/", WorkspaceInviteView.as_view(), name="workspace-invite"),
    path("invitations/<uuid:token>/accept/", InvitationAcceptView.as_view(), name="invitation-accept"),
]
