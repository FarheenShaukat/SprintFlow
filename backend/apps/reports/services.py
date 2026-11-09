from django.db.models import Count, Q
from django.utils import timezone

from apps.tasks.models import Task


def task_summary(tasks):
    pending = ~Q(status=Task.Status.DONE)
    return tasks.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=Task.Status.DONE)),
        overdue=Count("id", filter=pending & Q(due_date__lt=timezone.localdate())),
        blocked=Count("id", filter=Q(is_blocked=True)),
        critical_pending=Count("id", filter=pending & Q(priority=Task.Priority.CRITICAL)),
    )


def health_from_summary(summary):
    total = summary["total"]
    completed = summary["completed"]
    overdue = summary["overdue"]
    blocked = summary["blocked"]
    critical_pending = summary["critical_pending"]
    completion_rate = (completed / total) if total else 0

    score = 100
    score -= overdue * 5
    score -= blocked * 7
    score -= critical_pending * 3
    if completion_rate > 0.8:
        score += 5
    return max(0, min(100, score))


def sprint_health_score(tasks):
    return health_from_summary(task_summary(tasks))


def project_report(project):
    tasks = Task.objects.filter(project=project)
    summary = task_summary(tasks)
    total = summary["total"]
    completed = summary["completed"]
    by_status = list(tasks.values("status").annotate(count=Count("id")).order_by("status"))
    by_priority = list(tasks.values("priority").annotate(count=Count("id")).order_by("priority"))
    workload = list(
        tasks.values("assignee__id", "assignee__full_name")
        .annotate(active_tasks=Count("id", filter=~Q(status=Task.Status.DONE)))
        .order_by("-active_tasks")
    )
    health = health_from_summary(summary)
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "overdue_tasks": summary["overdue"],
        "blocked_tasks": summary["blocked"],
        "completion_rate": round((completed / total) * 100, 2) if total else 0,
        "sprint_health_score": health,
        "tasks_by_status": by_status,
        "tasks_by_priority": by_priority,
        "workload": workload,
    }
