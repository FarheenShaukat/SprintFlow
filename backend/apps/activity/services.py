from .models import ActivityLog


def log_activity(*, user=None, workspace=None, project=None, task=None, action="", old_value="", new_value=""):
    return ActivityLog.objects.create(
        user=user,
        workspace=workspace,
        project=project,
        task=task,
        action=action,
        old_value=old_value or "",
        new_value=new_value or "",
    )
