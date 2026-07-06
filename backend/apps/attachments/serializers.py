from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = Attachment
        fields = ["id", "task", "uploaded_by", "file_url", "file_name", "file_type", "file_size", "created_at"]
        read_only_fields = ["id", "task", "uploaded_by", "created_at"]
