from django.urls import path

from .views import (
    ProjectSprintFlowConversationView,
    SprintFlowApproveView,
    SprintFlowEventsView,
    SprintFlowMessageView,
    WorkspaceNewSprintFlowConversationView,
)

urlpatterns = [
    path("projects/<int:project_id>/sprintflow-ai", ProjectSprintFlowConversationView.as_view(), name="sprintflow-ai-project-no-slash"),
    path("projects/<int:project_id>/sprintflow-ai/", ProjectSprintFlowConversationView.as_view(), name="sprintflow-ai-project"),
    path("projects/<int:project_id>/sprintflow-ai/messages", SprintFlowMessageView.as_view(), name="sprintflow-ai-message-no-slash"),
    path("projects/<int:project_id>/sprintflow-ai/messages/", SprintFlowMessageView.as_view(), name="sprintflow-ai-message"),
    path("projects/<int:project_id>/sprintflow-ai/events", SprintFlowEventsView.as_view(), name="sprintflow-ai-events-no-slash"),
    path("projects/<int:project_id>/sprintflow-ai/events/", SprintFlowEventsView.as_view(), name="sprintflow-ai-events"),
    path("projects/<int:project_id>/sprintflow-ai/approve", SprintFlowApproveView.as_view(), name="sprintflow-ai-approve-no-slash"),
    path("projects/<int:project_id>/sprintflow-ai/approve/", SprintFlowApproveView.as_view(), name="sprintflow-ai-approve"),
    path("workspaces/<int:workspace_id>/sprintflow-ai/new", WorkspaceNewSprintFlowConversationView.as_view(), name="sprintflow-ai-new-no-slash"),
    path("workspaces/<int:workspace_id>/sprintflow-ai/new/", WorkspaceNewSprintFlowConversationView.as_view(), name="sprintflow-ai-new"),
    path("sprintflow-ai/conversations/<int:conversation_id>/messages", SprintFlowMessageView.as_view(), name="sprintflow-ai-new-message-no-slash"),
    path("sprintflow-ai/conversations/<int:conversation_id>/messages/", SprintFlowMessageView.as_view(), name="sprintflow-ai-new-message"),
    path("sprintflow-ai/conversations/<int:conversation_id>/approve", SprintFlowApproveView.as_view(), name="sprintflow-ai-new-approve-no-slash"),
    path("sprintflow-ai/conversations/<int:conversation_id>/approve/", SprintFlowApproveView.as_view(), name="sprintflow-ai-new-approve"),
]
