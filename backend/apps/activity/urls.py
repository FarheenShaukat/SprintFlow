from django.urls import path

from .views import ProjectActivityView, TaskActivityView

urlpatterns = [
    path("projects/<int:project_id>/activity/", ProjectActivityView.as_view(), name="project-activity"),
    path("tasks/<int:task_id>/activity/", TaskActivityView.as_view(), name="task-activity"),
]
