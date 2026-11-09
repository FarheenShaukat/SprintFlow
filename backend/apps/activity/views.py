from rest_framework import generics
from apps.projects.access import accessible_projects_for

from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ProjectActivityView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        return ActivityLog.objects.filter(project_id=self.kwargs["project_id"], project__in=accessible_projects_for(self.request.user)).select_related("user")


class TaskActivityView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        return ActivityLog.objects.filter(task_id=self.kwargs["task_id"], task__project__in=accessible_projects_for(self.request.user)).select_related("user")
