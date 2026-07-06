from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import Workspace, WorkspaceInvitation, WorkspaceMember

User = get_user_model()


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Workspace
        fields = [
            "id", "name", "description", "owner", "member_count",
            "allow_member_create_projects", "allow_member_create_tasks",
            "allow_member_edit_tasks", "allow_member_comment",
            "allow_member_upload_attachments", "allow_member_invite_members",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user", write_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ["id", "workspace", "user", "user_id", "role", "joined_at"]
        read_only_fields = ["id", "workspace", "joined_at"]


class WorkspaceInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=160)
    role = serializers.ChoiceField(choices=WorkspaceMember.Role.choices, default=WorkspaceMember.Role.MEMBER)


class WorkspaceInvitationSerializer(serializers.ModelSerializer):
    invited_by = UserSerializer(read_only=True)
    accepted_by = UserSerializer(read_only=True)

    class Meta:
        model = WorkspaceInvitation
        fields = [
            "id", "workspace", "email", "full_name", "role", "status", "invited_by",
            "accepted_by", "email_sent", "email_error", "accepted_at", "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InvitationAcceptSerializer(serializers.Serializer):
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    workspace_id = serializers.IntegerField(read_only=True)
    workspace_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    user_exists = serializers.BooleanField(read_only=True)
