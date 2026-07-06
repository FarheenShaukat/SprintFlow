# API Reference

Swagger/OpenAPI is available at `/api/docs/` when the backend is running.

Core endpoint groups:

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`
- `POST /api/auth/logout/`
- `/api/workspaces/`
- `/api/workspaces/{id}/members/`
- `/api/workspaces/{workspace_id}/projects/`
- `/api/projects/{project_id}/sprints/`
- `/api/projects/{project_id}/tasks/`
- `/api/tasks/{task_id}/comments/`
- `/api/tasks/{task_id}/attachments/`
- `/api/projects/{project_id}/activity/`
- `/api/tasks/{task_id}/activity/`
- `/api/ai/task-breakdown/`
- `/api/ai/suggest-priority/`
- `/api/ai/estimate-risk/`
- `/api/ai/suggest-assignee/`
- `/api/ai/sprint-summary/`
- `/api/projects/{project_id}/reports/`
- `/api/projects/{project_id}/sprint-health/`
- `/api/projects/{project_id}/workload/`
- `/api/projects/{project_id}/overdue-tasks/`
