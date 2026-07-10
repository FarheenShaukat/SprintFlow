from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("sprintflow_ai", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="sprintflowconversation",
            name="unique_sprintflow_conversation_per_project",
        ),
        migrations.AddConstraint(
            model_name="sprintflowconversation",
            constraint=models.UniqueConstraint(
                condition=Q(project__isnull=False),
                fields=("project", "created_by"),
                name="unique_sprintflow_conversation_per_project_user",
            ),
        ),
    ]
