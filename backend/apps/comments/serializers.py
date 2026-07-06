from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "task", "user", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "task", "user", "created_at", "updated_at"]
