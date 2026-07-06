from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.ai.services import suggest_priority, task_breakdown
from apps.projects.models import Project
from apps.reports.services import sprint_health_score
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.accounts.serializers import RegisterSerializer


class ServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email="owner@sprintflow.ai", password="password123", full_name="Owner")
        self.workspace = Workspace.objects.create(name="Workspace", owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role=WorkspaceMember.Role.OWNER)
        self.project = Project.objects.create(workspace=self.workspace, name="Project", created_by=self.user)

    def test_jwt_breakdown_has_expected_steps(self):
        subtasks = task_breakdown("Build JWT authentication")
        self.assertIn("Create register API", subtasks)

    def test_priority_detects_payment_as_critical(self):
        result = suggest_priority("Fix payment checkout error")
        self.assertEqual(result["priority"], Task.Priority.CRITICAL)

    def test_sprint_health_penalizes_blocked_overdue_critical(self):
        Task.objects.create(
            project=self.project,
            title="Risky task",
            reporter=self.user,
            priority=Task.Priority.CRITICAL,
            is_blocked=True,
            due_date=timezone.localdate() - timedelta(days=1),
        )
        self.assertEqual(sprint_health_score(Task.objects.filter(project=self.project)), 85)

    def test_invited_placeholder_user_can_finish_registration(self):
        invited = get_user_model().objects.create(email="invited@sprintflow.ai", full_name="Invited")
        invited.set_unusable_password()
        invited.save()

        serializer = RegisterSerializer(data={
            "email": "invited@sprintflow.ai",
            "full_name": "Invited User",
            "password": "password123",
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertTrue(user.has_usable_password())
        self.assertEqual(user.full_name, "Invited User")
