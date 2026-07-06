from rest_framework import serializers

from .models import AIInsight


class TaskBreakdownInputSerializer(serializers.Serializer):
    task_id = serializers.IntegerField(required=False)
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)


class PriorityInputSerializer(serializers.Serializer):
    task_id = serializers.IntegerField(required=False)
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    due_date = serializers.DateField(required=False)


class RiskInputSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()


class SuggestedAssigneeInputSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)


class SprintSummaryInputSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()


class AIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = ["id", "task", "project", "insight_type", "content", "risk_score", "created_at"]
