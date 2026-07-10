from django.contrib import admin

from .models import GeneratedPlan, SprintFlowAgentRun, SprintFlowConversation, SprintFlowMessage


@admin.register(SprintFlowConversation)
class SprintFlowConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "workspace", "project", "created_by", "status", "agent_status", "updated_at")
    list_filter = ("status", "agent_status")
    search_fields = ("thread_id", "project__name", "workspace__name", "created_by__email")


@admin.register(SprintFlowMessage)
class SprintFlowMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "message_type", "created_at")
    list_filter = ("role", "message_type")


@admin.register(GeneratedPlan)
class GeneratedPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "status", "created_at", "updated_at")
    list_filter = ("status",)


@admin.register(SprintFlowAgentRun)
class SprintFlowAgentRunAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "status", "current_step", "provider", "started_at", "completed_at")
    list_filter = ("status", "provider")
