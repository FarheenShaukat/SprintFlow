# Generated manually for SprintFlow AI vertical slice.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("projects", "0002_projectmember"),
        ("workspaces", "0003_workspace_allow_member_comment_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SprintFlowConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("thread_id", models.CharField(default=uuid.uuid4, max_length=80, unique=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("archived", "Archived")], default="active", max_length=16)),
                ("last_context_synced_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sprintflow_conversations", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="sprintflow_conversations", to="projects.project")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sprintflow_conversations", to="workspaces.workspace")),
            ],
        ),
        migrations.CreateModel(
            name="SprintFlowMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("user", "User"), ("assistant", "Assistant")], max_length=16)),
                ("message_type", models.CharField(choices=[("text", "Text"), ("progress", "Progress"), ("plan_card", "Plan Card"), ("confirmation", "Confirmation"), ("context_summary", "Context Summary")], default="text", max_length=24)),
                ("content", models.TextField(blank=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="sprintflow_ai.sprintflowconversation")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.CreateModel(
            name="GeneratedPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan_json", models.JSONField(default=dict)),
                ("validation_errors", models.JSONField(blank=True, default=list)),
                ("status", models.CharField(choices=[("drafting", "Drafting"), ("ready_for_approval", "Ready for Approval"), ("applied", "Applied")], default="drafting", max_length=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("applied_project", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="applied_sprintflow_plans", to="projects.project")),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="generated_plans", to="sprintflow_ai.sprintflowconversation")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddConstraint(
            model_name="sprintflowconversation",
            constraint=models.UniqueConstraint(condition=Q(project__isnull=False), fields=("project",), name="unique_sprintflow_conversation_per_project"),
        ),
    ]
