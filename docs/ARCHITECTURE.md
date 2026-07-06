# Architecture

SprintFlow AI is split into a Next.js frontend and a Django REST Framework backend.

## Frontend

- Next.js App Router with TypeScript
- Tailwind CSS using the supplied Kinetic Logic UI style
- React Hook Form and Zod for auth forms
- Zustand for client auth state
- TanStack Query is included for API fetching as screens are wired to live data
- Recharts powers reports
- Framer Motion is included for small interaction polish

## Backend

- Django REST Framework APIs
- Custom email-based user model
- Simple JWT access and refresh tokens
- Role-aware workspace membership model
- Separate service modules for activity logging, reports, attachment URL handling, and AI logic
- drf-spectacular Swagger docs at `/api/docs/`

## Data Flow

1. User registers or logs in through Django JWT auth.
2. Frontend stores the access token and sends it to `/api/*`.
3. Workspaces scope projects, sprints, tasks, members, activity, and reports.
4. Task mutations write `ActivityLog` records.
5. AI endpoints calculate suggestions and persist `AIInsight` records.
6. Reports aggregate task status, priority, workload, overdue tasks, and sprint health.
