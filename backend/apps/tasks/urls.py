from django.urls import path

from .views import SubTaskViewSet, TaskDependencyViewSet, TaskViewSet

task_list = TaskViewSet.as_view({"get": "list", "post": "create"})
task_detail = TaskViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})
subtask_list = SubTaskViewSet.as_view({"get": "list", "post": "create"})
subtask_detail = SubTaskViewSet.as_view({"patch": "partial_update", "delete": "destroy"})
dependency_list = TaskDependencyViewSet.as_view({"get": "list", "post": "create"})
dependency_detail = TaskDependencyViewSet.as_view({"delete": "destroy"})

urlpatterns = [
    path("projects/<int:project_id>/tasks/", task_list, name="project-tasks"),
    path("tasks/<int:pk>/", task_detail, name="task-detail"),
    path("tasks/<int:task_id>/subtasks/", subtask_list, name="task-subtasks"),
    path("tasks/<int:task_id>/subtasks/<int:pk>/", subtask_detail, name="task-subtask-detail"),
    path("tasks/<int:task_id>/dependencies/", dependency_list, name="task-dependencies"),
    path("tasks/<int:task_id>/dependencies/<int:pk>/", dependency_detail, name="task-dependency-detail"),
]
