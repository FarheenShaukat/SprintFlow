from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from apps.projects.models import Project, ProjectMember, Sprint
from apps.sprintflow_ai.models import GeneratedPlan, SprintFlowConversation, SprintFlowMessage
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMember


@override_settings(GROQ_API_KEY="", OPENAI_API_KEY="")
class SprintFlowAiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email="owner@sprintflow.ai", password="password123", full_name="Owner")
        self.admin = get_user_model().objects.create_user(email="admin@sprintflow.ai", password="password123", full_name="Admin")
        self.member = get_user_model().objects.create_user(email="member@sprintflow.ai", password="password123", full_name="Member")
        self.workspace = Workspace.objects.create(name="Engineering", owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role=WorkspaceMember.Role.OWNER)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.admin, role=WorkspaceMember.Role.ADMIN)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.member, role=WorkspaceMember.Role.MEMBER)
        self.project = Project.objects.create(workspace=self.workspace, name="Existing Project", created_by=self.user)
        ProjectMember.objects.create(project=self.project, user=self.member, role=ProjectMember.Role.MEMBER)
        self.client.force_authenticate(self.user)

    def test_get_project_conversation_creates_one_private_chat_per_project_user(self):
        first = self.client.get(f"/api/projects/{self.project.id}/sprintflow-ai/")
        second = self.client.get(f"/api/projects/{self.project.id}/sprintflow-ai/")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(SprintFlowConversation.objects.filter(project=self.project).count(), 1)

        self.client.force_authenticate(self.admin)
        third = self.client.get(f"/api/projects/{self.project.id}/sprintflow-ai/")

        self.assertEqual(third.status_code, status.HTTP_200_OK)
        self.assertEqual(SprintFlowConversation.objects.filter(project=self.project).count(), 2)
        self.assertEqual(SprintFlowConversation.objects.filter(project=self.project, created_by=self.user).count(), 1)
        self.assertEqual(SprintFlowConversation.objects.filter(project=self.project, created_by=self.admin).count(), 1)

    def test_regular_member_cannot_access_sprintflow_ai(self):
        self.client.force_authenticate(self.member)

        response = self.client.get(f"/api/projects/{self.project.id}/sprintflow-ai/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_admin_member_can_access_sprintflow_ai(self):
        ProjectMember.objects.filter(project=self.project, user=self.member).update(role=ProjectMember.Role.ADMIN)
        self.client.force_authenticate(self.member)

        response = self.client.get(f"/api/projects/{self.project.id}/sprintflow-ai/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_message_creates_plan_card(self):
        response = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Build auth, dashboard, and AI planner"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(GeneratedPlan.objects.filter(conversation__project=self.project).exists())
        self.assertTrue(SprintFlowMessage.objects.filter(message_type=SprintFlowMessage.MessageType.PLAN_CARD).exists())

    def test_uploaded_sprint_outline_is_not_truncated_by_fallback_planner(self):
        outline = """
        Project Name:
        CloudPilot

        SPRINT 0: Planning and Design
        Duration: 1-2 days
        - finalize scope
        - create user stories
        - create ERD
        - create architecture diagram
        - define API naming rules
        - define enums
        - define Git branching strategy
        - create GitHub repository

        SPRINT 1: Spring Boot Foundation
        Duration: 3-4 days
        - create Spring Boot project
        - configure Maven

        SPRINT 2: Authentication and User Management
        Duration: 4-5 days
        - create User and Role entities
        - register and login DTOs

        SPRINT 3: Cloud Projects and Membership
        - CloudProject entity

        SPRINT 4: Resource Quotas and Machine Images
        - ResourceQuota entity

        SPRINT 5: Virtual Machine Management
        - VirtualMachine entity

        SPRINT 6: Storage Volume Management
        - StorageVolume entity

        SPRINT 7: Networks and IP Allocation
        - VirtualNetwork, Subnet, NetworkInterface entities

        SPRINT 8: Dashboard and Monitoring
        - total/running/stopped/error VM counts

        SPRINT 9: Notifications and Audit Logs
        - Notification entity and service

        SPRINT 10: Frontend Integration
        - Next.js authentication

        SPRINT 11: Optional AI Intelligence
        - AI service interface

        SPRINT 12: Testing, CI/CD, and Deployment
        - complete unit tests
        - demo data
        """

        response = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Make a complete sprint plan from this.", "uploaded_text": outline},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        plan = GeneratedPlan.objects.get(conversation__project=self.project)
        self.assertEqual(len(plan.plan_json["sprints"]), 13)
        self.assertEqual(plan.plan_json["sprints"][0]["name"], "Sprint 0: Planning and Design")
        self.assertEqual(len(plan.plan_json["sprints"][0]["tasks"]), 8)
        self.assertEqual(plan.plan_json["sprints"][-1]["name"], "Sprint 12: Testing, CI/CD, and Deployment")

    def test_existing_project_plan_uses_selected_project_name(self):
        response = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Build auth, dashboard, and AI planner"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        plan = GeneratedPlan.objects.get(conversation__project=self.project)
        self.assertEqual(plan.plan_json["project"]["name"], self.project.name)

    def test_new_project_name_can_be_stated_in_chat_and_persists(self):
        created = self.client.post(f"/api/workspaces/{self.workspace.id}/sprintflow-ai/new/")
        conversation_id = created.data["id"]

        first = self.client.post(
            f"/api/sprintflow-ai/conversations/{conversation_id}/messages/",
            {"content": "Call it Inventory Hub. Build stock tracking and reports."},
            format="json",
        )
        second = self.client.post(
            f"/api/sprintflow-ai/conversations/{conversation_id}/messages/",
            {"content": "Add role permissions and audit logs."},
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        latest_plan = GeneratedPlan.objects.filter(conversation_id=conversation_id).first()
        conversation = SprintFlowConversation.objects.get(pk=conversation_id)
        self.assertEqual(conversation.checkpoint_state["user_specified_project_name"], "Inventory Hub")
        self.assertEqual(latest_plan.plan_json["project"]["name"], "Inventory Hub")

    def test_events_context_reflects_manual_project_changes(self):
        sprint = Sprint.objects.create(
            project=self.project,
            name="Manual Sprint",
            goal="Added outside AI",
            start_date="2026-07-09",
            end_date="2026-07-22",
        )
        Task.objects.create(project=self.project, sprint=sprint, title="Manual task", reporter=self.user)
        self.client.get(f"/api/projects/{self.project.id}/sprintflow-ai/")

        response = self.client.get(f"/api/projects/{self.project.id}/sprintflow-ai/events/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["context_summary"]["sprints"], 1)
        self.assertEqual(response.data["context_summary"]["tasks"], 1)

    @override_settings(OPENAI_API_KEY="test-key", OPENAI_MODEL="test-model", GROQ_API_KEY="groq-key", GROQ_MODEL="groq-model")
    @patch("apps.sprintflow_ai.graph.generate_plan_with_groq")
    def test_message_uses_groq_planner_even_when_openai_key_exists(self, mocked_generate):
        mocked_generate.return_value = self._mock_plan("Groq Planned Project", "Generated by mocked Groq planner.")

        response = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Use Groq to plan this project"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_generate.assert_called_once()
        plan = GeneratedPlan.objects.get(conversation__project=self.project)
        self.assertEqual(plan.plan_json["project"]["name"], self.project.name)
        self.assertEqual(
            SprintFlowMessage.objects.filter(message_type=SprintFlowMessage.MessageType.PLAN_CARD).last().payload["provider"],
            "groq",
        )

    @override_settings(OPENAI_API_KEY="test-key", OPENAI_MODEL="test-model", GROQ_API_KEY="groq-key", GROQ_MODEL="groq-model")
    @patch("apps.sprintflow_ai.graph.generate_plan_with_openai")
    def test_message_uses_openai_when_selected(self, mocked_generate):
        mocked_generate.return_value = self._mock_plan("OpenAI Planned Project", "Generated by mocked OpenAI planner.")

        response = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Use OpenAI to plan this project", "ai_provider": "openai"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_generate.assert_called_once()
        self.assertEqual(
            SprintFlowMessage.objects.filter(message_type=SprintFlowMessage.MessageType.PLAN_CARD).last().payload["provider"],
            "openai",
        )

    @override_settings(OPENAI_API_KEY="test-key", OPENAI_MODEL="test-model", GROQ_API_KEY="groq-key", GROQ_MODEL="groq-model")
    @patch("apps.sprintflow_ai.graph.generate_plan_with_groq", side_effect=RuntimeError("Groq unavailable"))
    def test_message_falls_back_when_groq_fails(self, mocked_generate):
        response = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Build auth and dashboard"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_generate.assert_called_once()
        self.assertEqual(
            SprintFlowMessage.objects.filter(message_type=SprintFlowMessage.MessageType.PLAN_CARD).last().payload["provider"],
            "fallback_after_error",
        )

    @override_settings(OPENAI_API_KEY="", GROQ_API_KEY="groq-key", GROQ_MODEL="groq-model")
    @patch("apps.sprintflow_ai.graph.generate_plan_with_groq")
    def test_message_uses_groq_when_openai_key_missing(self, mocked_groq):
        mocked_groq.return_value = self._mock_plan("Groq Only Project", "Generated by mocked Groq planner.")

        response = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Plan with Groq only"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_groq.assert_called_once()
        self.assertEqual(
            SprintFlowMessage.objects.filter(message_type=SprintFlowMessage.MessageType.PLAN_CARD).last().payload["provider"],
            "groq",
        )

    def test_approve_existing_project_plan_creates_sprints_and_tasks(self):
        self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Build authentication and launch flow"},
            format="json",
        )
        plan = GeneratedPlan.objects.get(conversation__project=self.project)

        response = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/approve/",
            {"generated_plan_id": plan.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(Sprint.objects.filter(project=self.project).count(), 0)
        self.assertGreater(Task.objects.filter(project=self.project).count(), 0)

    def test_events_report_pending_approval_and_checkpoint_state(self):
        self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Build authentication and launch flow"},
            format="json",
        )

        response = self.client.get(f"/api/projects/{self.project.id}/sprintflow-ai/events/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["agent_status"], "awaiting_approval")
        self.assertEqual(response.data["current_step"], "awaiting_approval")
        self.assertTrue(response.data["pending_approval"])
        self.assertEqual(response.data["checkpoint"]["state"]["approval_status"], "awaiting")
        self.assertIsNotNone(response.data["latest_run"])

    def test_duplicate_apply_is_blocked(self):
        self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Build authentication and launch flow"},
            format="json",
        )
        plan = GeneratedPlan.objects.get(conversation__project=self.project)

        first = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/approve/",
            {"generated_plan_id": plan.id},
            format="json",
        )
        second = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/approve/",
            {"generated_plan_id": plan.id},
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been applied", str(second.data).lower())

    def test_apply_skips_existing_sprint_and_task_names(self):
        self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/messages/",
            {"content": "Build authentication and launch flow"},
            format="json",
        )
        plan = GeneratedPlan.objects.get(conversation__project=self.project)
        first_sprint = plan.plan_json["sprints"][0]
        first_task = first_sprint["tasks"][0]
        Sprint.objects.create(
            project=self.project,
            name=first_sprint["name"],
            goal="Existing sprint",
            start_date=first_sprint["start_date"],
            end_date=first_sprint["end_date"],
        )
        Task.objects.create(
            project=self.project,
            title=first_task["title"],
            description="Existing task",
            reporter=self.user,
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/sprintflow-ai/approve/",
            {"generated_plan_id": plan.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["skipped_existing_sprints"], 1)
        self.assertGreaterEqual(response.data["skipped_existing_tasks"], 1)
        self.assertEqual(Sprint.objects.filter(project=self.project, name=first_sprint["name"]).count(), 1)
        self.assertEqual(Task.objects.filter(project=self.project, title=first_task["title"]).count(), 1)

    def test_new_project_conversation_applies_plan_and_attaches_project(self):
        created = self.client.post(f"/api/workspaces/{self.workspace.id}/sprintflow-ai/new/")
        conversation_id = created.data["id"]
        self.client.post(
            f"/api/sprintflow-ai/conversations/{conversation_id}/messages/",
            {"content": "Create a CRM for managing customers", "project_name": "Customer CRM"},
            format="json",
        )
        plan = GeneratedPlan.objects.get(conversation_id=conversation_id)

        response = self.client.post(
            f"/api/sprintflow-ai/conversations/{conversation_id}/approve/",
            {"generated_plan_id": plan.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conversation = SprintFlowConversation.objects.get(pk=conversation_id)
        self.assertIsNotNone(conversation.project)
        self.assertEqual(conversation.project.name, "Customer CRM")

    def test_new_project_apply_deduplicates_names_inside_workspace(self):
        created_one = self.client.post(f"/api/workspaces/{self.workspace.id}/sprintflow-ai/new/")
        created_two = self.client.post(f"/api/workspaces/{self.workspace.id}/sprintflow-ai/new/")

        for conversation_id in [created_one.data["id"], created_two.data["id"]]:
            self.client.post(
                f"/api/sprintflow-ai/conversations/{conversation_id}/messages/",
                {"content": "Create the same project plan", "project_name": "Duplicate Planner"},
                format="json",
            )
            plan = GeneratedPlan.objects.filter(conversation_id=conversation_id).first()
            response = self.client.post(
                f"/api/sprintflow-ai/conversations/{conversation_id}/approve/",
                {"generated_plan_id": plan.id},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = list(Project.objects.filter(workspace=self.workspace, name__startswith="Duplicate Planner").order_by("name").values_list("name", flat=True))
        self.assertEqual(names, ["Duplicate Planner", "Duplicate Planner (1)"])

    def test_regular_member_cannot_start_new_project_ai_conversation(self):
        self.client.force_authenticate(self.member)

        response = self.client.post(f"/api/workspaces/{self.workspace.id}/sprintflow-ai/new/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _mock_plan(self, name: str, description: str) -> dict:
        return {
            "project": {
                "name": name,
                "description": description,
                "goals": ["Ship the feature"],
                "assumptions": ["Mocked response"],
                "risks": ["None"],
            },
            "sprints": [
                {
                    "name": "Sprint 1 - Build",
                    "goal": "Build the core flow.",
                    "sequence": 1,
                    "start_date": "2026-07-08",
                    "end_date": "2026-07-21",
                    "tasks": [
                        {
                            "title": "Build mocked AI plan",
                            "description": "Implement the mocked output.",
                            "sequence": 1,
                            "priority": "high",
                            "estimated_hours": 5,
                            "acceptance_criteria": ["Plan is returned"],
                            "subtasks": ["Mock", "Assert"],
                            "depends_on": [],
                        }
                    ],
                }
            ],
        }
