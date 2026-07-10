from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.activity.services import log_activity
from apps.projects.models import Project, ProjectMember, Sprint
from apps.tasks.models import SubTask, Task, TaskDependency
from apps.workspaces.models import Workspace, WorkspaceMember


def load_project_context_tool(project: Project | None) -> dict:
    if not project:
        return {
            "project": None,
            "sprints": [],
            "tasks": [],
            "summary": {"sprints": 0, "tasks": 0, "overdue": 0, "completion_rate": 0},
        }

    tasks = (
        Task.objects.filter(project=project)
        .select_related("sprint", "assignee")
        .prefetch_related("subtasks", "dependencies")
        .order_by("sprint_id", "created_at")
    )
    total = tasks.count()
    completed = tasks.filter(status=Task.Status.DONE).count()
    overdue = tasks.exclude(status=Task.Status.DONE).filter(due_date__lt=timezone.localdate()).count()
    sprints = list(project.sprints.order_by("start_date", "id"))
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "deadline": project.deadline.isoformat() if project.deadline else None,
        },
        "sprints": [
            {
                "id": sprint.id,
                "name": sprint.name,
                "goal": sprint.goal,
                "status": sprint.status,
                "start_date": sprint.start_date.isoformat(),
                "end_date": sprint.end_date.isoformat(),
                "task_count": sprint.tasks.count(),
            }
            for sprint in sprints
        ],
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "sprint_id": task.sprint_id,
                "sprint": task.sprint.name if task.sprint else None,
                "assignee": task.assignee.full_name if task.assignee else None,
                "subtasks": [subtask.title for subtask in task.subtasks.all()],
            }
            for task in tasks[:80]
        ],
        "summary": {
            "sprints": len(sprints),
            "tasks": total,
            "overdue": overdue,
            "completion_rate": round((completed / total) * 100) if total else 0,
        },
    }


def draft_plan_tool(*, user_text: str, uploaded_text: str = "", project_context: dict | None = None, explicit_project_name: str = "") -> dict:
    source = " ".join(part.strip() for part in [user_text, uploaded_text] if part and part.strip())
    project_name = explicit_project_name or _derive_project_name(source)
    context = project_context or {}
    existing_sprints = context.get("sprints", [])
    start_index = len(existing_sprints) + 1
    base_start = timezone.localdate() + timedelta(days=len(existing_sprints) * 14)

    themes = _derive_themes(source)
    sprints = []
    for offset, theme in enumerate(themes):
        sequence = start_index + offset
        start_date = base_start + timedelta(days=offset * 14)
        sprints.append({
            "name": f"Sprint {sequence} - {theme['name']}",
            "goal": theme["goal"],
            "sequence": sequence,
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=13)).isoformat(),
            "tasks": [
                _task(f"Define {theme['short']} requirements", "Clarify scope, acceptance criteria, and constraints.", 1, "medium"),
                _task(f"Build {theme['short']} backend", "Implement models, serializers, APIs, permissions, and tests.", 2, "high"),
                _task(f"Build {theme['short']} frontend", "Create UI, API integration, loading states, and validation.", 3, "high"),
                _task(f"Test and document {theme['short']}", "Run regression checks and update user/developer notes.", 4, "medium"),
            ],
        })

    return {
        "project": {
            "name": project_name,
            "description": source[:500] or "AI-generated project plan.",
            "goals": [theme["goal"] for theme in themes],
            "assumptions": ["Plan was generated from the current chat message and live project context."],
            "risks": ["Review estimates and dependencies before approval."],
        },
        "sprints": sprints,
    }


def validate_plan_tool(plan: dict) -> list[str]:
    errors = []
    if not plan.get("project", {}).get("name"):
        errors.append("Project name is required.")
    sprints = plan.get("sprints", [])
    if not sprints:
        errors.append("At least one sprint is required.")
    if len(sprints) > 12:
        errors.append("Plan cannot contain more than 12 sprints.")
    total_tasks = 0
    for sprint in sprints:
        tasks = sprint.get("tasks", [])
        total_tasks += len(tasks)
        if not sprint.get("name"):
            errors.append("Every sprint needs a name.")
        if not tasks:
            errors.append(f"{sprint.get('name', 'A sprint')} needs at least one task.")
        if len(tasks) > 20:
            errors.append(f"{sprint.get('name', 'A sprint')} cannot contain more than 20 tasks.")
        for task in tasks:
            if not task.get("title"):
                errors.append("Every task needs a title.")
            if task.get("priority") not in {"low", "medium", "high", "critical"}:
                task["priority"] = "medium"
            if len(task.get("subtasks", [])) > 10:
                errors.append(f"{task.get('title', 'A task')} cannot contain more than 10 subtasks.")
    if total_tasks > 150:
        errors.append("Plan cannot contain more than 150 total tasks.")
    return errors


def normalize_plan_tool(plan: dict) -> dict:
    plan.setdefault("project", {})
    plan["project"].setdefault("name", "New AI Planned Project")
    plan["project"].setdefault("description", "")
    plan["project"].setdefault("goals", [])
    plan["project"].setdefault("assumptions", [])
    plan["project"].setdefault("risks", [])
    for sprint_index, sprint in enumerate(plan.setdefault("sprints", []), start=1):
        sprint.setdefault("name", f"Sprint {sprint_index}")
        sprint.setdefault("goal", "")
        sprint.setdefault("sequence", sprint_index)
        sprint.setdefault("start_date", (timezone.localdate() + timedelta(days=(sprint_index - 1) * 14)).isoformat())
        sprint.setdefault("end_date", (timezone.localdate() + timedelta(days=(sprint_index * 14) - 1)).isoformat())
        for task_index, task in enumerate(sprint.setdefault("tasks", []), start=1):
            task.setdefault("title", f"Task {task_index}")
            task.setdefault("description", "")
            task.setdefault("sequence", task_index)
            task.setdefault("priority", "medium")
            task.setdefault("estimated_hours", 4)
            task.setdefault("acceptance_criteria", [])
            task.setdefault("subtasks", [])
            task.setdefault("depends_on", [])
    return plan


def repair_plan_tool(plan: dict) -> dict:
    return normalize_plan_tool(plan)


def apply_plan_tool(*, conversation, generated_plan, user) -> dict:
    with transaction.atomic():
        generated_plan = generated_plan.__class__.objects.select_for_update().get(pk=generated_plan.pk)
        if generated_plan.status == generated_plan.Status.APPLIED:
            raise ValueError("This plan has already been applied.")
        plan = generated_plan.plan_json
        errors = validate_plan_tool(plan)
        if errors:
            generated_plan.validation_errors = errors
            generated_plan.save(update_fields=["validation_errors", "updated_at"])
            raise ValueError("Plan is not valid for applying.")

        project = conversation.project
        if not project:
            workspace = Workspace.objects.select_for_update().get(pk=conversation.workspace_id)
            project = Project.objects.create(
                workspace=workspace,
                name=plan["project"]["name"],
                description=plan["project"].get("description", ""),
                created_by=user,
            )
            ProjectMember.objects.update_or_create(project=project, user=user, defaults={"role": ProjectMember.Role.ADMIN})
            for membership in workspace.memberships.select_related("user"):
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=membership.user,
                    defaults={"role": ProjectMember.Role.ADMIN if membership.role in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN} else ProjectMember.Role.MEMBER},
                )
            conversation.project = project
            conversation.save(update_fields=["project", "updated_at"])
            log_activity(user=user, workspace=workspace, project=project, action="project.created", new_value=project.name)

        created_sprints = 0
        created_tasks = 0
        task_lookup = {}
        existing_sprints = {_normalize_key(sprint.name): sprint for sprint in project.sprints.select_for_update()}
        existing_tasks = {_normalize_key(task.title): task for task in project.tasks.select_for_update()}
        for sprint_data in plan.get("sprints", []):
            sprint_key = _normalize_key(sprint_data["name"])
            sprint = existing_sprints.get(sprint_key)
            if not sprint:
                sprint = Sprint.objects.create(
                    project=project,
                    name=sprint_data["name"],
                    goal=sprint_data.get("goal", ""),
                    start_date=sprint_data.get("start_date") or timezone.localdate(),
                    end_date=sprint_data.get("end_date") or timezone.localdate() + timedelta(days=13),
                )
                existing_sprints[sprint_key] = sprint
                created_sprints += 1
                log_activity(user=user, workspace=project.workspace, project=project, action="sprint.created", new_value=sprint.name)
            for task_data in sprint_data.get("tasks", []):
                task_key = _normalize_key(task_data["title"])
                task = existing_tasks.get(task_key)
                if not task:
                    task = Task.objects.create(
                        project=project,
                        sprint=sprint,
                        title=task_data["title"],
                        description=_task_description(task_data),
                        priority=task_data.get("priority", Task.Priority.MEDIUM),
                        estimated_hours=task_data.get("estimated_hours") or None,
                        reporter=user,
                    )
                    existing_tasks[task_key] = task
                    created_tasks += 1
                    existing_subtasks = set()
                    for subtask in task_data.get("subtasks", []):
                        title = str(subtask)[:220]
                        subtask_key = _normalize_key(title)
                        if subtask_key and subtask_key not in existing_subtasks:
                            SubTask.objects.create(task=task, title=title)
                            existing_subtasks.add(subtask_key)
                    log_activity(user=user, workspace=project.workspace, project=project, task=task, action="task.created", new_value=task.title)
                elif task.sprint_id is None:
                    task.sprint = sprint
                    task.save(update_fields=["sprint", "updated_at"])
                task_lookup[task_key] = task

        for sprint_data in plan.get("sprints", []):
            for task_data in sprint_data.get("tasks", []):
                task = task_lookup.get(_normalize_key(task_data["title"]))
                if not task:
                    continue
                for dependency_title in task_data.get("depends_on", []):
                    dependency = task_lookup.get(_normalize_key(str(dependency_title)))
                    if dependency and dependency.id != task.id:
                        TaskDependency.objects.get_or_create(task=task, depends_on_task=dependency)

        generated_plan.applied_project = project
        generated_plan.status = generated_plan.Status.APPLIED
        generated_plan.save(update_fields=["applied_project", "status", "updated_at"])

    return {
        "project_id": project.id,
        "sprint_count": created_sprints,
        "task_count": created_tasks,
        "skipped_existing_sprints": max(len(plan.get("sprints", [])) - created_sprints, 0),
        "skipped_existing_tasks": max(sum(len(sprint.get("tasks", [])) for sprint in plan.get("sprints", [])) - created_tasks, 0),
        "redirect_url": f"/projects/{project.id}/board",
    }


def _normalize_key(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def _derive_project_name(source: str) -> str:
    words = [word.strip(".,:;!?()[]{}") for word in source.split() if len(word.strip(".,:;!?()[]{}")) > 2]
    if not words:
        return "New AI Planned Project"
    return " ".join(words[:4]).title()[:180]


def _derive_themes(source: str) -> list[dict]:
    lower = source.lower()
    themes = [{"name": "Discovery and Foundation", "short": "foundation", "goal": "Clarify scope and prepare the base architecture."}]
    if any(term in lower for term in ["auth", "login", "user", "jwt"]):
        themes.append({"name": "Authentication and Access", "short": "authentication", "goal": "Implement secure user access and permissions."})
    if any(term in lower for term in ["payment", "checkout", "billing"]):
        themes.append({"name": "Payments and Billing", "short": "payments", "goal": "Implement reliable payment and billing workflows."})
    if any(term in lower for term in ["ai", "agent", "planner", "chat"]):
        themes.append({"name": "AI Workflow", "short": "AI workflow", "goal": "Build the AI-assisted planning and automation flow."})
    themes.append({"name": "QA and Launch", "short": "launch", "goal": "Test, document, and prepare the project for release."})
    return themes[:4]


def _task(title: str, description: str, sequence: int, priority: str) -> dict:
    return {
        "title": title,
        "description": description,
        "sequence": sequence,
        "priority": priority,
        "estimated_hours": 6,
        "acceptance_criteria": ["Implementation is complete.", "Behavior is tested.", "User-facing state is documented where needed."],
        "subtasks": ["Confirm scope", "Implement", "Test"],
        "depends_on": [],
    }


def _task_description(task_data: dict) -> str:
    criteria = "\n".join(f"- {item}" for item in task_data.get("acceptance_criteria", []))
    return f"{task_data.get('description', '')}\n\nAcceptance criteria:\n{criteria}".strip()
