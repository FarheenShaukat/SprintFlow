from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.attachments.models import Attachment
from apps.comments.models import Comment
from .models import SubTask, Task, TaskDependency


class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ["id", "task", "title", "is_completed", "created_at", "updated_at"]
        read_only_fields = ["id", "task", "created_at", "updated_at"]


class TaskDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDependency
        fields = ["id", "task", "depends_on_task", "created_at"]
        read_only_fields = ["id", "task", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    assignee_detail = UserSerializer(source="assignee", read_only=True)
    reporter_detail = UserSerializer(source="reporter", read_only=True)
    subtasks = SubTaskSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    attachment_count = serializers.IntegerField(read_only=True)
    dependencies_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "project", "sprint", "title", "description", "status", "priority",
            "assignee", "assignee_detail", "reporter", "reporter_detail", "due_date",
            "estimated_hours", "actual_hours", "is_blocked", "blocked_reason",
            "ai_priority_reason", "ai_risk_score", "subtasks", "comment_count",
            "attachment_count", "dependencies_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "project", "reporter", "created_at", "updated_at"]

    def create(self, validated_data):
        task = super().create(validated_data)
        subtasks = self.context["request"].data.get("subtasks", [])
        for subtask in subtasks:
            SubTask.objects.create(task=task, title=subtask["title"])
        return task
