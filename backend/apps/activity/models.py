from django.conf import settings
from django.db import models

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.workspaces.models import Workspace


class ActivityLog(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="activity_logs", null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="activity_logs", null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activity_logs", null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="activity_logs", null=True, blank=True)
    action = models.CharField(max_length=120)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
