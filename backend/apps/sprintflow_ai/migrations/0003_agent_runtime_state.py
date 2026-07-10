from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sprintflow_ai", "0002_private_project_user_conversation"),
    ]

    operations = [
        migrations.AddField(
            model_name="sprintflowconversation",
            name="agent_status",
            field=models.CharField(
                choices=[
                    ("idle", "Idle"),
                    ("running", "Running"),
                    ("awaiting_approval", "Awaiting Approval"),
                    ("applying", "Applying"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                ],
                default="idle",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="sprintflowconversation",
            name="checkpoint_state",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="sprintflowconversation",
            name="current_step",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="sprintflowconversation",
            name="last_agent_error",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="SprintFlowAgentRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "Running"),
                            ("awaiting_approval", "Awaiting Approval"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="running",
                        max_length=32,
                    ),
                ),
                ("current_step", models.CharField(blank=True, max_length=120)),
                ("provider", models.CharField(blank=True, max_length=64)),
                ("error", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_runs",
                        to="sprintflow_ai.sprintflowconversation",
                    ),
                ),
            ],
            options={"ordering": ["-started_at", "-id"]},
        ),
    ]
