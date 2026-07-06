from django.urls import path

from .views import EstimateRiskView, SprintSummaryView, SuggestAssigneeView, SuggestPriorityView, TaskBreakdownView

urlpatterns = [
    path("ai/task-breakdown", TaskBreakdownView.as_view(), name="ai-task-breakdown-no-slash"),
    path("ai/task-breakdown/", TaskBreakdownView.as_view(), name="ai-task-breakdown"),
    path("ai/suggest-priority", SuggestPriorityView.as_view(), name="ai-suggest-priority-no-slash"),
    path("ai/suggest-priority/", SuggestPriorityView.as_view(), name="ai-suggest-priority"),
    path("ai/estimate-risk", EstimateRiskView.as_view(), name="ai-estimate-risk-no-slash"),
    path("ai/estimate-risk/", EstimateRiskView.as_view(), name="ai-estimate-risk"),
    path("ai/suggest-assignee", SuggestAssigneeView.as_view(), name="ai-suggest-assignee-no-slash"),
    path("ai/suggest-assignee/", SuggestAssigneeView.as_view(), name="ai-suggest-assignee"),
    path("ai/sprint-summary", SprintSummaryView.as_view(), name="ai-sprint-summary-no-slash"),
    path("ai/sprint-summary/", SprintSummaryView.as_view(), name="ai-sprint-summary"),
]
