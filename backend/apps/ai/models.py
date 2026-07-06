from django.db import models

from apps.projects.models import Project
from apps.tasks.models import Task


class AIInsight(models.Model):
    class InsightType(models.TextChoices):
        BREAKDOWN = "breakdown", "Breakdown"
        PRIORITY = "priority", "Priority"
        RISK = "risk", "Risk"
        ASSIGNEE = "assignee", "Assignee"
        SUMMARY = "summary", "Summary"

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="ai_insights", null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="ai_insights", null=True, blank=True)
    insight_type = models.CharField(max_length=24, choices=InsightType.choices)
    content = models.JSONField(default=dict)
    risk_score = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
