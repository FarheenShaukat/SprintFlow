# SprintFlow AI - Final Project Notes

## Project Summary

SprintFlow AI is a full-stack Mini Jira / intelligent project management platform for software teams. It is built as a portfolio project to demonstrate Django REST Framework, JWT authentication, database modeling, REST APIs, frontend engineering, deployment, CI/CD, and product-level SaaS workflows.

The app supports:

- User registration and login with Django JWT
- Workspaces
- Workspace members and invitations
- Project-level members and roles
- Projects and sprints
- Kanban task board
- Task assignment
- Task status updates
- Subtasks
- Comments
- Attachments model/API
- Activity logs
- Reports and analytics
- Sprint health score
- Rule-based AI/task intelligence

## Important Architecture Decision

Authentication is handled by **Django JWT**, not Supabase Auth.

Supabase is used as the **PostgreSQL database provider**.

Correct production flow:

```txt
Next.js frontend -> Django REST API -> Django models -> Supabase PostgreSQL
```

Not:

```txt
Next.js frontend -> Supabase Auth
```

## Tech Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- React Hook Form
- Zod
- Zustand
- Recharts
- Framer Motion
- Lucide icons

### Backend

- Python
- Django
- Django REST Framework
- Simple JWT
- django-filter
- django-cors-headers
- drf-spectacular
- Gunicorn

### Database and Storage

- Supabase PostgreSQL
- Supabase Storage planned for file uploads
- Django models and migrations manage the database schema

### Deployment

- Vercel currently configured for frontend and backend together
- Supabase PostgreSQL for production database
- GitHub Actions CI included

## Folder Structure

```txt
mini jira/
  backend/
    apps/
      accounts/
      workspaces/
      projects/
      tasks/
      comments/
      attachments/
      activity/
      ai/
      reports/
      core/
    config/
    api/
    manage.py
    requirements.txt

  frontend/
    app/
    components/
    lib/
    store/
    types/
    package.json

  docs/
  .github/workflows/
  vercel.json
  requirements.txt
  docker-compose.yml
  README.md
  FINAL.md
```

## Local Run

### Backend

```powershell
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend runs at:

```txt
http://127.0.0.1:8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at:

```txt
http://localhost:3000
```

If port 3000 is busy, Next.js may use 3001.

## Required Environment Variables

Use a single root `.env` file for local development.

Important variables:

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

DATABASE_URL=

NEXT_PUBLIC_API_URL=/api
FRONTEND_URL=http://localhost:3000

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=SprintFlow AI <your-email@gmail.com>

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
OPENAI_API_KEY=
```

## Supabase Database Setup

For production, use Supabase PostgreSQL through `DATABASE_URL`.

Use the **Supabase pooler connection string**, not the direct IPv6 database URL.

Good format:

```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres
```

Avoid direct host format on Vercel:

```env
DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```

Reason: Vercel may fail to connect to Supabase direct IPv6 database hosts. The pooler URL is safer for serverless deployments.

If your password contains special characters, encode them.

Example:

```txt
@ becomes %40
```

## Database Migrations

If Django says:

```txt
You have unapplied migrations
```

Run:

```powershell
cd backend
python manage.py migrate
```

For production Supabase, make sure your local `.env` points to the Supabase pooler `DATABASE_URL`, then run:

```powershell
cd backend
python manage.py migrate
```

This creates tables such as:

- `accounts_user`
- `workspaces_workspace`
- `tasks_task`
- `django_migrations`
- JWT token blacklist tables

## Production Deployment on Vercel

The root `vercel.json` is configured to deploy both:

- Next.js frontend
- Django backend serverless function

Vercel project setting:

```txt
Root Directory = repo root
```

Do not set root directory to `frontend` when using the root `vercel.json`.

Production Vercel env vars:

```env
DATABASE_URL=your-supabase-pooler-url
DJANGO_SECRET_KEY=your-production-secret
DJANGO_ALLOWED_HOSTS=*
NEXT_PUBLIC_API_URL=/api
FRONTEND_URL=https://your-vercel-app.vercel.app
```

Optional:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=SprintFlow AI <your-email@gmail.com>
```

## Production Health Checks

Backend health:

```txt
https://your-vercel-app.vercel.app/api/health/
```

Expected:

```json
{"status":"ok"}
```

Database health:

```txt
https://your-vercel-app.vercel.app/api/health/db/
```

Expected:

```json
{
  "status": "ok",
  "migrated": true,
  "has_users_table": true
}
```

If `has_users_table` is false, run migrations against Supabase.

## Common Production Errors and Fixes

### `Failed to fetch`

Cause:

- Frontend is calling `localhost:8000` in production.

Fix:

```env
NEXT_PUBLIC_API_URL=/api
```

### `DisallowedHost`

Cause:

- Django does not trust the Vercel domain.

Fix:

```env
DJANGO_ALLOWED_HOSTS=*
```

or:

```env
DJANGO_ALLOWED_HOSTS=.vercel.app,your-domain.com
```

### `OperationalError`

Cause:

- Database connection problem.
- Wrong Supabase URL.
- Direct IPv6 DB host on Vercel.

Fix:

- Use Supabase pooler URL.
- Make sure `DATABASE_URL` is set on Vercel.

### `ProgrammingError`

Cause:

- Database connected, but tables are missing.

Fix:

```powershell
cd backend
python manage.py migrate
```

### `ERR_TOO_MANY_REDIRECTS` on `/api/workspaces/`

Cause:

- Production route/trailing slash redirect loop.

Fix already applied:

- Frontend normalizes API paths.
- Backend supports slashless API routes.

## API Endpoints

### Auth

```txt
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
GET  /api/auth/me
POST /api/auth/logout
```

### Workspaces

```txt
GET    /api/workspaces
POST   /api/workspaces
GET    /api/workspaces/{id}
PATCH  /api/workspaces/{id}
DELETE /api/workspaces/{id}
```

### Workspace Members

```txt
GET    /api/workspaces/{id}/members
POST   /api/workspaces/{id}/members
PATCH  /api/workspaces/{id}/members/{member_id}
DELETE /api/workspaces/{id}/members/{member_id}
```

### Invitations

```txt
GET  /api/workspaces/{id}/invitations
POST /api/workspaces/{id}/invitations
GET  /api/invitations/{token}/accept
POST /api/invitations/{token}/accept
```

### Projects

```txt
GET    /api/workspaces/{workspace_id}/projects
POST   /api/workspaces/{workspace_id}/projects
GET    /api/projects/{id}
PATCH  /api/projects/{id}
DELETE /api/projects/{id}
```

### Tasks

```txt
GET    /api/projects/{project_id}/tasks
POST   /api/projects/{project_id}/tasks
GET    /api/tasks/{id}
PATCH  /api/tasks/{id}
DELETE /api/tasks/{id}
```

Task filters:

```txt
?status=todo
?priority=high
?assignee=1
?mine=true
?due=today
?blocked=true
```

### Reports

```txt
GET /api/projects/{project_id}/reports
GET /api/projects/{project_id}/sprint-health
GET /api/projects/{project_id}/workload
GET /api/projects/{project_id}/overdue-tasks
```

### AI

```txt
POST /api/ai/task-breakdown
POST /api/ai/suggest-priority
POST /api/ai/estimate-risk
POST /api/ai/suggest-assignee
POST /api/ai/sprint-summary
```

## AI Status

AI is currently **rule-based**, not OpenAI-powered.

Current AI logic lives in:

```txt
backend/apps/ai/services.py
```

It supports:

- Task breakdown based on keywords
- Priority suggestion based on keywords and due date
- Risk score based on task data
- Suggested assignee based on workload
- Sprint summary based on task counts

This is okay for the current portfolio stage, but describe it honestly as:

```txt
rule-based AI/task intelligence
```

Do not call it OpenAI-powered until a real OpenAI or Gemini API call is connected.

Future AI upgrade:

- Add provider service for OpenAI/Gemini
- Use JSON structured outputs
- Keep rule-based fallback when `OPENAI_API_KEY` is missing

## JWT Auth Behavior

The frontend stores:

```txt
sprintflow_access
sprintflow_refresh
```

The API client:

- Attaches access token
- Refreshes token on `401`
- Retries request once
- Clears tokens if refresh fails
- Shows a sign-in-again prompt when session expires

## Roles and Permissions

Workspace roles:

- Owner
- Admin
- Member

Project roles:

- Admin
- Member
- Viewer

Important permission behavior:

- Owners can manage workspace settings and members.
- Admins can manage projects/tasks/members.
- Members can work based on workspace settings.
- Project-level role can differ from workspace-level role.
- Members can update assigned tasks and add subtasks depending on permissions.

## Kanban Board

Columns:

- To Do
- In Progress
- Review
- Done

Filters:

- All
- My Tasks
- Blocked
- High
- Due today

Board UI includes:

- Canvas-style background
- Zoom controls
- Internal column scrolling
- Task detail modal
- Assignee dropdown
- Subtasks
- Comments
- Status/priority/due date editing

## CI/CD

GitHub Actions workflow:

```txt
.github/workflows/ci.yml
```

Jobs:

- Backend check and tests
- Frontend typecheck and build

Frontend commands:

```txt
npm ci
npm run typecheck
npm run build
```

Backend commands:

```txt
python manage.py check
python manage.py test
```

## Final Portfolio Description

SprintFlow AI is an intelligent project management platform inspired by Jira and Linear. It helps software teams manage workspaces, projects, sprints, tasks, comments, attachments, members, activity logs, and reports. The backend is built with Django REST Framework, JWT authentication, role-based permissions, Swagger documentation, and Supabase PostgreSQL. The frontend is built with Next.js, TypeScript, Tailwind CSS, and a polished SaaS-style interface. The project includes sprint health scoring, workload reports, task filtering, rule-based AI task intelligence, CI/CD, and production deployment configuration.

## Final Notes

- Use Supabase PostgreSQL for production data.
- Do not use SQLite in production.
- Use Supabase pooler URL on Vercel.
- Run migrations after changing database.
- Keep `NEXT_PUBLIC_API_URL=/api` for combined Vercel deployment.
- AI is rule-based until OpenAI/Gemini is connected.
- If production breaks, check `/api/health/db/` first.
