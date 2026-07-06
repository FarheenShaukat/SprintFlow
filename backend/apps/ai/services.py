from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from apps.ai.models import AIInsight
from apps.projects.models import Project
from apps.tasks.models import Task


def task_breakdown(title: str, description: str = "") -> list[str]:
    text = f"{title} {description}".lower()
    if "jwt" in text or "auth" in text:
        return [
            "Create or validate the user model",
            "Create register API",
            "Create login API",
            "Generate access and refresh tokens",
            "Protect private routes",
            "Write API tests",
        ]
    if "payment" in text:
        return ["Reproduce checkout issue", "Inspect payment provider logs", "Patch validation flow", "Add regression tests", "Deploy hotfix"]
    return ["Clarify acceptance criteria", "Break implementation into backend and frontend tasks", "Add tests", "Request review", "Update documentation"]


def suggest_priority(title: str, description: str = "", due_date=None) -> dict:
    text = f"{title} {description}".lower()
    critical_terms = ["payment", "security", "leak", "production", "outage", "checkout"]
    high_terms = ["blocked", "deadline", "migration", "auth", "risk"]
    if any(term in text for term in critical_terms):
        priority = Task.Priority.CRITICAL
        reason = "Critical production or security language detected."
    elif due_date and due_date <= timezone.localdate() + timedelta(days=2):
        priority = Task.Priority.HIGH
        reason = "Due date is close, so this should be prioritized."
    elif any(term in text for term in high_terms):
        priority = Task.Priority.HIGH
        reason = "Task contains dependency or delivery-risk keywords."
    else:
        priority = Task.Priority.MEDIUM
        reason = "No urgent risk signals found."
    return {"priority": priority, "reason": reason}


def estimate_task_risk(task: Task) -> dict:
    score = 10
    reasons = []
    if task.due_date and task.due_date <= timezone.localdate() + timedelta(days=2) and task.status != Task.Status.DONE:
        score += 25
        reasons.append("Due date is near.")
    if task.priority in {Task.Priority.HIGH, Task.Priority.CRITICAL}:
        score += 20 if task.priority == Task.Priority.HIGH else 30
        reasons.append("Task priority is elevated.")
    if task.dependencies.exists():
        score += 15
        reasons.append("Task has dependencies.")
    if task.is_blocked:
        score += 25
        reasons.append("Task is currently blocked.")
    active_load = Task.objects.filter(assignee=task.assignee).exclude(status=Task.Status.DONE).count() if task.assignee else 0
    if active_load >= 6:
        score += 15
        reasons.append("Assignee has a heavy active workload.")
    score = min(100, score)
    return {"risk_score": score, "reasons": reasons or ["No major risk detected."]}


def suggest_assignee(project: Project, title: str, description: str = "") -> dict:
    candidates = (
        project.workspace.memberships.select_related("user")
        .annotate(active_tasks=Count("user__assigned_tasks", filter=Q(user__assigned_tasks__project=project) & ~Q(user__assigned_tasks__status=Task.Status.DONE)))
        .order_by("active_tasks", "joined_at")
    )
    selected = candidates.first()
    if not selected:
        return {"assignee_id": None, "reason": "No workspace members are available."}
    return {
        "assignee_id": selected.user_id,
        "full_name": selected.user.full_name,
        "active_tasks": selected.active_tasks,
        "reason": "Lowest active workload among workspace members.",
    }


def sprint_summary(project: Project) -> dict:
    tasks = Task.objects.filter(project=project)
    total = tasks.count()
    completed = tasks.filter(status=Task.Status.DONE).count()
    in_progress = tasks.filter(status=Task.Status.IN_PROGRESS).count()
    overdue = tasks.exclude(status=Task.Status.DONE).filter(due_date__lt=timezone.localdate()).count()
    blocked = tasks.filter(is_blocked=True).count()
    summary = (
        f"This sprint has {total} tasks. {completed} are completed, {in_progress} are in progress, "
        f"{overdue} are overdue, and {blocked} are blocked."
    )
    if blocked or overdue:
        summary += " Main risk is blocked or overdue delivery work."
    return {"summary": summary, "total": total, "completed": completed, "in_progress": in_progress, "overdue": overdue, "blocked": blocked}


def store_insight(*, insight_type, content, task=None, project=None, risk_score=0):
    return AIInsight.objects.create(
        insight_type=insight_type,
        content=content,
        task=task,
        project=project,
        risk_score=risk_score,
    )
