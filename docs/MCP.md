# Connect Claude and Codex to SprintFlow

The remote connector URL for this deployment is:

```text
https://sprint-flow-five.vercel.app/mcp
```

This endpoint is added by this change. It becomes available after the backend changes are deployed and the OAuth database migrations are applied. The existing website alone does not provide an MCP endpoint.

## Claude

1. Open **Customize → Connectors → Add custom connector**.
2. Name it **SprintFlow** and paste the URL above.
3. Choose sign-in authentication and, if an OAuth client choice is shown, **Register automatically**. This server supports automatic registration; it does not fetch published client identity documents.
4. Sign in using your SprintFlow email and password, then authorize access.
5. Enable SprintFlow for the conversation.

Your teammate connects with their own account. Claude only sees projects accessible to the person who authorized it. Do not use a shared owner login.

## Codex

Add a remote HTTP server in your MCP settings using the same URL. For the CLI:

```bash
codex mcp add sprintflow --url https://sprint-flow-five.vercel.app/mcp
codex mcp login sprintflow
```

The equivalent server entry in `~/.codex/config.toml` is:

```toml
[mcp_servers.sprintflow]
url = "https://sprint-flow-five.vercel.app/mcp"
```

Complete the browser sign-in and consent screen. No API key or password belongs in this configuration.

## What you can ask

- “List my teams and the projects in Engineering.”
- “Create a project called Website Refresh in workspace 3.”
- “Add a high-priority task to project 7: Build the login screen.”
- “Move task 12 to in progress.”
- “Mark task 12 complete.”
- “Read all tasks in project 7.”
- “Invite teammate@example.com to workspace 3, then add them to project 7 after they accept.”

## Tools

| Tool | Purpose |
| --- | --- |
| `list_workspaces` / `create_workspace` | Find or create a team workspace |
| `list_projects` / `create_project` | Find or create projects in a workspace |
| `list_tasks` | Read every page of project tasks |
| `create_task` | Add a task, optionally assigned to a teammate |
| `update_task_status` | Set `todo`, `in_progress`, `review`, or `done` |
| `list_workspace_members` | Find teammate user IDs |
| `list_project_members` / `add_project_member` | Inspect or grant project access |
| `invite_workspace_member` | Send an invitation email using the configured email backend |

## Share a project with two people

Workspaces are teams. In the app, open **Team**, choose the workspace, and invite the second person. After they accept and register/sign in, open the workspace, choose **Manage Access** on the project, and grant **Member** access. Both people can create and move tasks in that project. **Viewer** access permits reading only. Workspace settings can disable task creation or editing for members.

Use **Refresh** on the board to see changes from the other person or an MCP client. Live push updates are not implemented.

To disconnect an OAuth application, visit `/oauth/authorized_tokens/` on the backend and revoke its access. Removing someone from a workspace also removes their project memberships.

## Deploy on Vercel

The root `vercel.json` routes `/mcp`, `/oauth/*`, and `/.well-known/*` to the Python ASGI application. The MCP transport is stateless Streamable HTTP with JSON responses, so connector requests do not depend on a particular Vercel function instance or an open SSE connection. OAuth clients, grants and tokens persist in the existing PostgreSQL database.

1. Install the updated backend requirements in your deployment environment.
2. Apply migrations against the production database using the deployment's existing environment:

   ```bash
   cd backend
   python manage.py migrate --noinput
   ```

3. Deploy the changed source through the repository's Vercel project.
4. Confirm the environment uses a stable `DJANGO_SECRET_KEY`, the existing production `DATABASE_URL`, `DJANGO_DEBUG=False`, and `MCP_PUBLIC_URL=https://sprint-flow-five.vercel.app`. The public URL default for Vercel is supplied in `vercel.json`. Set `FRONTEND_URL=https://sprint-flow-five.vercel.app` for invitation links. Configure SMTP for invitations.
5. Verify:

   ```bash
   curl https://sprint-flow-five.vercel.app/.well-known/oauth-authorization-server
   curl https://sprint-flow-five.vercel.app/.well-known/oauth-protected-resource/mcp
   curl -i -X POST https://sprint-flow-five.vercel.app/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
   ```

   Discovery returns JSON. The unauthenticated MCP request must return **401** with a `WWW-Authenticate` resource metadata URL. Then connect and sign in from each client to verify authenticated tools.

OAuth uses authorization codes with S256 PKCE, user consent, one-hour access tokens, rotating refresh tokens, resource audience checks and revocation. The server never accepts a user's identity from a tool argument. Each tool calls the same REST view and permissions as the app.

Periodically run `python manage.py cleartokens` to remove expired OAuth records. Changes to the public hostname require updating `MCP_PUBLIC_URL`, Vercel routing/environment, and reconnecting clients.

## Local development and checks

Use `MCP_PUBLIC_URL=http://localhost:8000` locally, run migrations and start the ASGI server:

```bash
cd backend
python -m uvicorn config.asgi:application --reload
python manage.py test
```

`manage.py runserver` serves Django's WSGI routes and does not serve the ASGI MCP endpoint. Use Uvicorn for MCP development. Claude's hosted connector requires a publicly reachable HTTPS server, so localhost is only for development and SDK testing.

Frontend checks:

```bash
cd frontend
node --test lib/api.test.cjs
npm run typecheck
npm run build
```

## Protocol references

- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x)
- [MCP authorization specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- [Django OAuth Toolkit](https://django-oauth-toolkit.readthedocs.io/en/latest/)
- [Claude remote connectors](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)
- [Codex MCP setup](https://developers.openai.com/codex/mcp)
