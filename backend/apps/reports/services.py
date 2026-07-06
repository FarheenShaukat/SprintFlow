from django.db.models import Count, Q
from django.utils import timezone

from apps.tasks.models import Task


def sprint_health_score(tasks):
    total = tasks.count()
    completed = tasks.filter(status=Task.Status.DONE).count()
    overdue = tasks.exclude(status=Task.Status.DONE).filter(due_date__lt=timezone.localdate()).count()
    blocked = tasks.filter(is_blocked=True).count()
    critical_pending = tasks.exclude(status=Task.Status.DONE).filter(priority=Task.Priority.CRITICAL).count()
    completion_rate = (completed / total) if total else 0

    score = 100
    score -= overdue * 5
    score -= blocked * 7
    score -= critical_pending * 3
    if completion_rate > 0.8:
        score += 5
    return max(0, min(100, score))


def project_report(project):
    tasks = Task.objects.filter(project=project)
    total = tasks.count()
    completed = tasks.filter(status=Task.Status.DONE).count()
    overdue = tasks.exclude(status=Task.Status.DONE).filter(due_date__lt=timezone.localdate()).count()
    blocked = tasks.filter(is_blocked=True).count()
    by_status = list(tasks.values("status").annotate(count=Count("id")).order_by("status"))
    by_priority = list(tasks.values("priority").annotate(count=Count("id")).order_by("priority"))
    workload = list(
        tasks.values("assignee__id", "assignee__full_name")
        .annotate(active_tasks=Count("id", filter=~Q(status=Task.Status.DONE)))
        .order_by("-active_tasks")
    )
    health = sprint_health_score(tasks)
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "overdue_tasks": overdue,
        "blocked_tasks": blocked,
        "completion_rate": round((completed / total) * 100, 2) if total else 0,
        "sprint_health_score": health,
        "tasks_by_status": by_status,
        "tasks_by_priority": by_priority,
        "workload": workload,
    }
