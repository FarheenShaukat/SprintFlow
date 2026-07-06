from rest_framework import serializers

from django.contrib.auth import get_user_model
from apps.accounts.serializers import UserSerializer
from .models import Project, ProjectMember, Sprint

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "workspace", "name", "description", "status", "start_date", "deadline", "created_by", "task_count", "created_at", "updated_at"]
        read_only_fields = ["id", "workspace", "created_by", "created_at", "updated_at"]


class SprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sprint
        fields = ["id", "project", "name", "goal", "start_date", "end_date", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "project", "created_at", "updated_at"]


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user", write_only=True)

    class Meta:
        model = ProjectMember
        fields = ["id", "project", "user", "user_id", "role", "joined_at"]
        read_only_fields = ["id", "project", "joined_at"]
