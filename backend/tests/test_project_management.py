from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.projects.models import Project, ProjectMember
from apps.workspaces.models import Workspace, WorkspaceMember


class WorkspaceProjectManagementTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(email="owner@sprintflow.ai", password="password123", full_name="Owner")
        self.admin = get_user_model().objects.create_user(email="admin@sprintflow.ai", password="password123", full_name="Admin")
        self.member = get_user_model().objects.create_user(email="member@sprintflow.ai", password="password123", full_name="Member")
        self.outsider = get_user_model().objects.create_user(email="outsider@sprintflow.ai", password="password123", full_name="Outsider")
        self.workspace = Workspace.objects.create(name="Engineering", owner=self.owner)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.owner, role=WorkspaceMember.Role.OWNER)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.admin, role=WorkspaceMember.Role.ADMIN)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.member, role=WorkspaceMember.Role.MEMBER)

    def test_workspace_admin_can_create_multiple_projects(self):
        self.client.force_authenticate(self.admin)

        first = self.client.post(f"/api/workspaces/{self.workspace.id}/projects/", {"name": "Mobile App"}, format="json")
        second = self.client.post(f"/api/workspaces/{self.workspace.id}/projects/", {"name": "Admin Portal"}, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.filter(workspace=self.workspace).count(), 2)

    def test_admin_sees_all_projects_but_member_sees_only_assigned_projects(self):
        first = Project.objects.create(workspace=self.workspace, name="Visible", created_by=self.owner)
        Project.objects.create(workspace=self.workspace, name="Hidden", created_by=self.owner)
        ProjectMember.objects.create(project=first, user=self.member, role=ProjectMember.Role.MEMBER)

        self.client.force_authenticate(self.admin)
        admin_response = self.client.get(f"/api/workspaces/{self.workspace.id}/projects/")
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_response.data["count"], 2)

        self.client.force_authenticate(self.member)
        member_response = self.client.get(f"/api/workspaces/{self.workspace.id}/projects/")
        self.assertEqual(member_response.status_code, status.HTTP_200_OK)
        self.assertEqual(member_response.data["count"], 1)
        self.assertEqual(member_response.data["results"][0]["name"], "Visible")

    def test_member_cannot_create_project_when_workspace_disallows_it(self):
        self.client.force_authenticate(self.member)

        response = self.client.post(f"/api/workspaces/{self.workspace.id}/projects/", {"name": "Member Project"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_create_project_when_workspace_allows_it(self):
        self.workspace.allow_member_create_projects = True
        self.workspace.save(update_fields=["allow_member_create_projects"])
        self.client.force_authenticate(self.member)

        response = self.client.post(f"/api/workspaces/{self.workspace.id}/projects/", {"name": "Member Project"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(workspace=self.workspace, name="Member Project").exists())

    def test_non_member_cannot_create_project_in_workspace(self):
        self.client.force_authenticate(self.outsider)

        response = self.client.post(f"/api/workspaces/{self.workspace.id}/projects/", {"name": "Bad Project"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
