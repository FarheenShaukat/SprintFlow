from rest_framework import generics

from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ProjectActivityView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        return ActivityLog.objects.filter(project_id=self.kwargs["project_id"], project__workspace__memberships__user=self.request.user).select_related("user")


class TaskActivityView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        return ActivityLog.objects.filter(task_id=self.kwargs["task_id"], task__project__workspace__memberships__user=self.request.user).select_related("user")
