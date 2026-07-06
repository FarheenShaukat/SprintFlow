# SprintFlow AI

SprintFlow AI is an intelligent project management platform inspired by Jira and Linear. It helps software teams manage workspaces, projects, sprints, tasks, comments, attachments, activity logs, AI-powered task insights, sprint health scoring, and analytics.

## Why This Project Was Built

This is a portfolio-grade full-stack project for an Associate Software Engineer role. It demonstrates Python, Django REST Framework, JWT auth, databases, REST APIs, Docker, CI/CD, modern frontend development, and clean product thinking.

## Features

- Email/password authentication with Django JWT
- Workspaces with owner, admin, and member roles
- SMTP-backed member invitations with console email fallback for development
- Project and sprint management
- Kanban board with To Do, In Progress, Review, and Done
- Task filters for status, priority, assignee, due date, and blocked state
- Task details with comments, attachments, activity, and AI insights
- Activity logs for important workflow events
- Reports for workload, overdue tasks, sprint health, task status, and priority
- Swagger/OpenAPI docs through drf-spectacular

## Smart AI Features

- Task breakdown suggestions
- Smart priority suggestions
- Risk detection
- Suggested assignee based on workload
- Sprint summary generation

AI is intentionally left as a final-phase feature. The backend has an AI service area ready, and the frontend shows disabled AI panels until OpenAI or Gemini is connected.

## Tech Stack

Frontend:

- Next.js, TypeScript, Tailwind CSS
- React Hook Form, Zod
- TanStack Query, Zustand
- Recharts, Framer Motion

Backend:

- Python, Django, Django REST Framework
- Simple JWT
- drf-spectacular
- django-cors-headers
- django-filter

Database/Auth/Storage:

- Supabase PostgreSQL via `DATABASE_URL`
- Django JWT auth
- Supabase Storage URL support for task attachments

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Database Design

See [docs/ERD.md](docs/ERD.md).

## API Documentation

Run the backend and open:

- Swagger: `http://localhost:8000/api/docs/`
- Schema: `http://localhost:8000/api/schema/`

Endpoint summary is in [docs/API.md](docs/API.md).

## Setup

Create or edit the single root env file:

```bash
cp .env.example .env
```

This repo already includes a development `.env` with SQLite fallback. Put your Supabase PostgreSQL `DATABASE_URL` there when you are ready to use Supabase.

Run with Docker:

```bash
docker compose up --build
```

Run locally:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

All environment variables live in the root `.env`:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `NEXT_PUBLIC_API_URL`
- `FRONTEND_URL`
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

For SMTP in development, use your provider credentials. Gmail example:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=SprintFlow AI <your-email@gmail.com>
```

For Gmail, `EMAIL_HOST_PASSWORD` must be an app password, not your normal Gmail password.

## Screenshots

The original supplied screen exports are preserved in [prototype/index.html](</c:/Users/MUGHAL TRADERS/Desktop/projects/mini jira/prototype/index.html>).

## Demo Credentials

Use after creating seed data or registering through the UI:

- Email: `demo@sprintflow.ai`
- Password: `password123`

## Deployment

- Frontend: Vercel
- Backend: Render, Railway, or Fly.io
- Database: Supabase PostgreSQL
- Storage: Supabase Storage

## Future Improvements

- Add real OpenAI/Gemini provider calls behind the AI service layer
- Add drag-and-drop persistence to the Kanban board
- Add Supabase signed upload flow
- Add Playwright end-to-end tests
- Add a seed command and Postman collection
