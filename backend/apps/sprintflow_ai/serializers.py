from rest_framework import serializers

from .models import GeneratedPlan, SprintFlowConversation, SprintFlowMessage


class SprintFlowMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SprintFlowMessage
        fields = ["id", "role", "message_type", "content", "payload", "created_at"]


class GeneratedPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedPlan
        fields = ["id", "plan_json", "validation_errors", "status", "applied_project", "created_at", "updated_at"]


class SprintFlowConversationSerializer(serializers.ModelSerializer):
    messages = SprintFlowMessageSerializer(many=True, read_only=True)
    latest_plan = serializers.SerializerMethodField()

    class Meta:
        model = SprintFlowConversation
        fields = [
            "id", "workspace", "project", "thread_id", "status", "agent_status", "current_step", "last_agent_error", "last_context_synced_at",
            "latest_plan", "messages", "created_at", "updated_at",
        ]

    def get_latest_plan(self, obj):
        plan = obj.generated_plans.first()
        return GeneratedPlanSerializer(plan).data if plan else None


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True)
    project_name = serializers.CharField(required=False, allow_blank=True, max_length=180)
    file = serializers.FileField(required=False)


class ApprovePlanSerializer(serializers.Serializer):
    generated_plan_id = serializers.IntegerField()
    plan_json = serializers.JSONField(required=False)
