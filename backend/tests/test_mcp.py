from datetime import timedelta
from unittest.mock import patch

import httpx
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from oauth2_provider.models import get_access_token_model, get_application_model

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMember


@override_settings(MCP_PUBLIC_URL="http://testserver")
class RemoteMCPTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email="mcp@example.com", password="password123", full_name="MCP User")
        self.workspace = Workspace.objects.create(name="Team", owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role="owner")
        application = get_application_model().objects.create(name="Test connector", client_type="public", authorization_grant_type="authorization-code")
        self.token = get_access_token_model().objects.create(
            user=self.user, application=application, token="mcp-test-token", scope="sprintflow",
            expires=timezone.now() + timedelta(hours=1), resource=["http://testserver/mcp"],
        )

    async def rpc(self, method, params=None, authenticated=True):
        from config.asgi import application

        headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-06-18"}
        if authenticated:
            headers["Authorization"] = "Bearer mcp-test-token"
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://testserver") as client:
            return await client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})

    def call_tool(self, name, arguments):
        response = async_to_sync(self.rpc)("tools/call", {"name": name, "arguments": arguments})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()["result"]
        self.assertFalse(result.get("isError"), result)
        return result["structuredContent"]

    def test_discovery_and_unauthenticated_rejection(self):
        response = async_to_sync(self.rpc)("tools/list", authenticated=False)
        self.assertEqual(response.status_code, 401)
        self.assertIn("resource_metadata", response.headers["www-authenticate"])
        response = async_to_sync(self.rpc)("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("tools", response.json()["result"]["capabilities"])
        response = async_to_sync(self.rpc)("tools/list")
        names = {tool["name"] for tool in response.json()["result"]["tools"]}
        self.assertTrue({"create_project", "create_task", "list_tasks", "update_task_status", "add_project_member"}.issubset(names))

    def test_create_project_and_task_then_complete(self):
        project = self.call_tool("create_project", {"workspace_id": self.workspace.id, "name": "Connected project"})
        task = self.call_tool("create_task", {"project_id": project["id"], "title": "Build feature"})
        self.call_tool("update_task_status", {"task_id": task["id"], "status": "in_progress"})
        self.assertEqual(Task.objects.get(pk=task["id"]).status, "in_progress")
        self.call_tool("update_task_status", {"task_id": task["id"], "status": "done"})
        self.assertEqual(Task.objects.get(pk=task["id"]).status, "done")

    def test_list_tasks_returns_every_page(self):
        project = Project.objects.create(workspace=self.workspace, name="Large", created_by=self.user)
        Task.objects.bulk_create([Task(project=project, title=f"Task {index}", reporter=self.user) for index in range(45)])
        result = self.call_tool("list_tasks", {"project_id": project.id})
        self.assertEqual(result["count"], 45)
        self.assertEqual(len({task["id"] for task in result["results"]}), 45)

    def test_expired_revoked_and_wrong_audience_tokens_rejected(self):
        self.token.resource = ["https://other.example/mcp"]
        self.token.save()
        self.assertEqual(async_to_sync(self.rpc)("tools/list").status_code, 401)

        self.token.resource = ["http://testserver/mcp"]
        self.token.expires = timezone.now() - timedelta(seconds=1)
        self.token.save()
        self.assertEqual(async_to_sync(self.rpc)("tools/list").status_code, 401)
        self.token.delete()
        self.assertEqual(async_to_sync(self.rpc)("tools/list").status_code, 401)

    def test_token_verifier_cleans_database_connections(self):
        from apps.integrations.mcp import SprintFlowTokenVerifier

        with patch("apps.integrations.mcp.close_old_connections") as cleanup:
            self.assertIsNone(async_to_sync(SprintFlowTokenVerifier().verify_token)("invalid-token"))
        self.assertEqual(cleanup.call_count, 2)
        with patch("apps.integrations.mcp.close_old_connections") as cleanup:
            with patch("apps.integrations.mcp.get_access_token_model", side_effect=RuntimeError("database unavailable")):
                with self.assertRaises(RuntimeError):
                    async_to_sync(SprintFlowTokenVerifier().verify_token)("invalid-token")
        self.assertEqual(cleanup.call_count, 2)

    def test_tools_cannot_access_another_users_project(self):
        outsider = get_user_model().objects.create_user(email="other@example.com", password="password123", full_name="Other")
        workspace = Workspace.objects.create(name="Private", owner=outsider)
        project = Project.objects.create(workspace=workspace, name="Secret", created_by=outsider)
        response = async_to_sync(self.rpc)("tools/call", {"name": "create_task", "arguments": {"project_id": project.id, "title": "No access"}})
        self.assertTrue(response.json()["result"]["isError"])
        self.assertFalse(Task.objects.filter(project=project).exists())

    def test_official_client_can_initialize_list_and_call(self):
        async def connect():
            from config.asgi import application
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application), headers={"Authorization": "Bearer mcp-test-token"}) as client:
                async with streamable_http_client("http://testserver/mcp", http_client=client) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools = await session.list_tools()
                        self.assertIn("create_project", {tool.name for tool in tools.tools})
                        result = await session.call_tool("list_workspaces", {})
                        self.assertFalse(result.isError)
                        self.assertEqual(result.structuredContent["results"][0]["name"], "Team")

        async_to_sync(connect)()
