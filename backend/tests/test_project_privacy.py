from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.comments.models import Comment
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMember


class ProjectPrivacyTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(email="privacy-owner@example.com", password="password123", full_name="Owner")
        self.member = get_user_model().objects.create_user(email="privacy-member@example.com", password="password123", full_name="Member")
        self.workspace = Workspace.objects.create(name="Team", owner=self.owner)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.owner, role="owner")
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.member, role="member")
        self.project = Project.objects.create(workspace=self.workspace, name="Restricted", created_by=self.owner)
        self.task = Task.objects.create(project=self.project, title="Secret", reporter=self.owner)
        Comment.objects.create(task=self.task, user=self.owner, content="Private comment")
        self.client.force_authenticate(self.member)

    def test_hidden_project_comments_cannot_be_read_or_created(self):
        path = f"/api/tasks/{self.task.id}/comments/"
        response = self.client.get(path)
        self.assertEqual(response.data["count"], 0)
        response = self.client.post(path, {"content": "Unauthorized"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.filter(task=self.task).count(), 1)

    def test_hidden_project_report_is_not_available(self):
        response = self.client.get(f"/api/projects/{self.project.id}/reports/")
        self.assertEqual(response.status_code, 404)
