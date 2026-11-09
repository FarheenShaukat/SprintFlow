# Remote MCP and shared projects implementation plan

**Goal:** Connect Claude Connectors and Codex to a hosted SprintFlow URL, with per-user login and shared project tasks.

**Architecture:** Mount the official MCP SDK's stateless Streamable HTTP application beside Django under the same ASGI server. Django OAuth Toolkit provides authorization codes, PKCE, consent, rotating refresh tokens and revocation. MCP tools reuse REST views and their authorization checks in-process. Existing workspaces represent teams; project memberships control collaboration.

**Tech stack:** Django, Django REST Framework, Django OAuth Toolkit, MCP Python SDK, Uvicorn, Next.js.

## Implementation

- [x] Add OAuth discovery, public client registration, login and consent, resource validation and SDK token verification. Test discovery, PKCE, refresh, revocation and unauthenticated rejection.
- [x] Expose workspace/project discovery and creation, task creation/listing/status changes and membership tools. Test the real MCP HTTP protocol and all pages of tasks.
- [x] Fix implicit project enrollment, workspace member leaks and stale access; enforce project roles and valid assignments. Test two collaborators and forbidden access.
- [x] Repair Team page role-aware loading, errors and project-sharing navigation. Ensure boards read all task pages and provide refresh.
- [x] Document the single public URL, deployment, migrations and client connection steps. Add CI coverage and run backend tests, frontend typecheck and build.

## Verification

- 90 backend tests pass, including 20 OAuth cases, official MCP client HTTP transport, all task pages and two-user collaboration.
- Five frontend pagination tests, TypeScript checking and the Next.js production build pass.
- Django system checks, migration drift check and diff whitespace checks pass.
- Report generation reduced from 12 database queries to 4 with identical tested summary results.
- Independent review findings fixed and verified: viewer sprint writes, unchanged removed assignees blocking status updates, and database connection lifecycle cleanup for MCP requests.

## Review focus

- A project URL must never grant its visitor membership.
- All tool requests must use the connecting user's permissions.
- OAuth codes cannot be reused or redeemed with a different redirect or PKCE verifier.
- Pagination must include tasks beyond the first twenty.
- Removing workspace access must also remove project access.

## Hosting

The user supplied https://sprint-flow-five.vercel.app as the deployment. Vercel routing and public configuration target https://sprint-flow-five.vercel.app/mcp. The existing health endpoint is reachable. The MCP change is local until deployed and OAuth migrations must run against the production database before connection. No deployment is claimed without verification.
