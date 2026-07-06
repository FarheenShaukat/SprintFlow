from django.urls import path

from .views import OverdueTasksView, ProjectReportView, SprintHealthView, WorkloadView

urlpatterns = [
    path("projects/<int:project_id>/reports/", ProjectReportView.as_view(), name="project-reports"),
    path("projects/<int:project_id>/sprint-health/", SprintHealthView.as_view(), name="sprint-health"),
    path("projects/<int:project_id>/workload/", WorkloadView.as_view(), name="workload"),
    path("projects/<int:project_id>/overdue-tasks/", OverdueTasksView.as_view(), name="overdue-tasks"),
]
