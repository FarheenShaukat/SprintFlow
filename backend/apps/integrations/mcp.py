import hashlib
from contextlib import contextmanager
from typing import Any, Literal
from urllib.parse import urlsplit

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import close_old_connections
from django.test import RequestFactory
from django.urls import resolve
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from oauth2_provider.models import get_access_token_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.renderers import JSONRenderer


@contextmanager
def database_connection():
    close_old_connections()
    try:
        yield
    finally:
        close_old_connections()


@database_connection()
def valid_token(token):
    record = get_access_token_model().objects.select_related("user", "application").filter(
        token_checksum=hashlib.sha256(token.encode()).hexdigest(),
    ).first()
    resource = f"{settings.MCP_PUBLIC_URL}/mcp"
    if not record or not record.user or not record.user.is_active:
        return None
    if not record.is_valid(["sprintflow"]) or record.resource != [resource]:
        return None
    return record


class SprintFlowTokenVerifier(TokenVerifier):
    async def verify_token(self, token):
        record = await sync_to_async(valid_token)(token)
        if record is None:
            return None
        return AccessToken(
            token=token, client_id=record.application.client_id,
            scopes=record.scope.split(), expires_at=int(record.expires.timestamp()),
            resource=f"{settings.MCP_PUBLIC_URL}/mcp", subject=str(record.user_id),
        )


class ConnectorAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return request._request.connector_user, None


@database_connection()
def api_request(method, path, data=None):
    access = get_access_token()
    record = valid_token(access.token) if access else None
    if record is None:
        raise ValueError("Connection expired. Reconnect SprintFlow to sign in again.")
    match = resolve(urlsplit(path).path)
    request = RequestFactory().generic(
        method, path, data=JSONRenderer().render(data or {}), content_type="application/json",
        HTTP_HOST=urlsplit(settings.MCP_PUBLIC_URL).netloc,
    )
    request.connector_user = record.user
    callback = match.func
    options = {**callback.initkwargs, "authentication_classes": [ConnectorAuthentication]}
    if hasattr(callback, "actions"):
        view = callback.cls.as_view(callback.actions, **options)
    else:
        view = callback.cls.as_view(**options)
    response = view(request, **match.kwargs)
    if response.status_code >= 400:
        raise ValueError(f"SprintFlow API {response.status_code}: {JSONRenderer().render(response.data).decode()}")
    return response.data


def all_pages(path):
    results = []
    page = 1
    while True:
        data = api_request("GET", f"{path}?page={page}")
        results.extend(data["results"])
        if not data["next"]:
            return {"count": len(results), "results": results}
        page += 1


def create_server():
    public_url = settings.MCP_PUBLIC_URL
    host = urlsplit(public_url).netloc
    server = FastMCP(
        "SprintFlow", instructions="Manage the signed-in user's projects, tasks and teams. Use list_workspaces and list_projects to find IDs. Task completion is status done.",
        stateless_http=True, json_response=True,
        token_verifier=SprintFlowTokenVerifier(),
        auth=AuthSettings(issuer_url=public_url, resource_server_url=f"{public_url}/mcp", required_scopes=["sprintflow"], validate_token_resource=True),
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[host], allowed_origins=[public_url],
        ),
    )
    read = ToolAnnotations(readOnlyHint=True, destructiveHint=False)
    write = ToolAnnotations(readOnlyHint=False, destructiveHint=False)

    @server.tool(annotations=read)
    async def list_workspaces() -> dict[str, Any]:
        """List all teams/workspaces available to the signed-in user."""
        return await sync_to_async(all_pages)("/api/workspaces/")

    @server.tool(annotations=write)
    async def create_workspace(name: str, description: str = "") -> dict[str, Any]:
        """Create a team workspace owned by the signed-in user."""
        return await sync_to_async(api_request)("POST", "/api/workspaces/", {"name": name, "description": description})

    @server.tool(annotations=read)
    async def list_projects(workspace_id: int) -> dict[str, Any]:
        """List all projects the user can access within a team workspace."""
        return await sync_to_async(all_pages)(f"/api/workspaces/{workspace_id}/projects/")

    @server.tool(annotations=write)
    async def create_project(workspace_id: int, name: str, description: str = "") -> dict[str, Any]:
        """Create a project in a workspace, subject to its creation permissions."""
        return await sync_to_async(api_request)("POST", f"/api/workspaces/{workspace_id}/projects/", {"name": name, "description": description})

    @server.tool(annotations=read)
    async def list_tasks(project_id: int) -> dict[str, Any]:
        """Read ALL tasks in a project, automatically including every page."""
        return await sync_to_async(all_pages)(f"/api/projects/{project_id}/tasks/")

    @server.tool(annotations=write)
    async def create_task(project_id: int, title: str, description: str = "", priority: Literal["low", "medium", "high", "critical"] = "medium", assignee_id: int | None = None) -> dict[str, Any]:
        """Add a To Do task. An optional assignee must have access to the project."""
        return await sync_to_async(api_request)("POST", f"/api/projects/{project_id}/tasks/", {"title": title, "description": description, "priority": priority, "assignee": assignee_id})

    @server.tool(annotations=write)
    async def update_task_status(task_id: int, status: Literal["todo", "in_progress", "review", "done"]) -> dict[str, Any]:
        """Move a task to To Do, In Progress, Review or Done (complete)."""
        return await sync_to_async(api_request)("PATCH", f"/api/tasks/{task_id}/", {"status": status})

    @server.tool(annotations=read)
    async def list_workspace_members(workspace_id: int) -> dict[str, Any]:
        """List teammates and their user IDs for project sharing and task assignment."""
        return await sync_to_async(all_pages)(f"/api/workspaces/{workspace_id}/members/")

    @server.tool(annotations=read)
    async def list_project_members(project_id: int) -> dict[str, Any]:
        """List the members who share a project."""
        return await sync_to_async(all_pages)(f"/api/projects/{project_id}/members/")

    @server.tool(annotations=write)
    async def add_project_member(project_id: int, user_id: int, role: Literal["admin", "member", "viewer"] = "member") -> dict[str, Any]:
        """Share a project with an existing workspace teammate. Requires project or workspace admin."""
        return await sync_to_async(api_request)("POST", f"/api/projects/{project_id}/members/", {"user_id": user_id, "role": role})

    @server.tool(annotations=write)
    async def invite_workspace_member(workspace_id: int, email: str, full_name: str = "", role: Literal["admin", "member"] = "member") -> dict[str, Any]:
        """Send a workspace invitation email. After acceptance, grant the teammate project access separately."""
        return await sync_to_async(api_request)("POST", f"/api/workspaces/{workspace_id}/invitations/", {"email": email, "full_name": full_name, "role": role})

    return server


async def mcp_application(scope, receive, send):
    server = create_server()
    app = server.streamable_http_app()
    async with server.session_manager.run():
        await app(scope, receive, send)
