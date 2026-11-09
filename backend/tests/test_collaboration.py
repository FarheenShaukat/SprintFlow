from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from apps.projects.access import accessible_projects_for, user_can_access_project
from apps.projects.models import Project, ProjectMember, Sprint
from apps.tasks.models import SubTask, Task, TaskDependency
from apps.workspaces.models import Workspace, WorkspaceInvitation, WorkspaceMember


class CollaborationTests(APITestCase):
    def test_viewer_cannot_create_or_edit_sprints(self):
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get(f"/api/projects/{self.project.pk}/sprints/").status_code, 200)
        response = self.client.post(f"/api/projects/{self.project.pk}/sprints/", {
            "name": "Unauthorized", "start_date": "2026-02-01", "end_date": "2026-02-14",
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.patch(f"/api/sprints/{self.sprint.pk}/", {"name": "Changed"}).status_code, 403)

    def test_task_can_be_completed_after_assignee_loses_access(self):
        self.task.assignee = self.bob
        self.task.save()
        self.client.force_authenticate(self.owner)
        membership = WorkspaceMember.objects.get(workspace=self.workspace, user=self.bob)
        self.assertEqual(self.client.delete(f"/api/workspaces/{self.workspace.pk}/members/{membership.pk}/").status_code, 204)
        response = self.client.patch(f"/api/tasks/{self.task.pk}/", {"status": "done"})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "done")

    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(email="owner@collaboration.test", full_name="Owner")
        cls.admin = users.create_user(email="admin@collaboration.test", full_name="Admin")
        cls.alice = users.create_user(email="alice@collaboration.test", full_name="Alice")
        cls.bob = users.create_user(email="bob@collaboration.test", full_name="Bob")
        cls.viewer = users.create_user(email="viewer@collaboration.test", full_name="Viewer")
        cls.outsider = users.create_user(email="outsider@collaboration.test", full_name="Outsider")
        cls.workspace = Workspace.objects.create(name="Team", owner=cls.owner)
        for user, role in [(cls.owner, "owner"), (cls.admin, "admin"), (cls.alice, "member"),
                           (cls.bob, "member"), (cls.viewer, "member")]:
            WorkspaceMember.objects.create(workspace=cls.workspace, user=user, role=role)
        cls.project = Project.objects.create(workspace=cls.workspace, name="Shared", created_by=cls.owner)
        cls.hidden = Project.objects.create(workspace=cls.workspace, name="Hidden", created_by=cls.owner)
        cls.alice_membership = ProjectMember.objects.create(project=cls.project, user=cls.alice, role="admin")
        cls.bob_membership = ProjectMember.objects.create(project=cls.project, user=cls.bob, role="member")
        cls.viewer_membership = ProjectMember.objects.create(project=cls.project, user=cls.viewer, role="viewer")
        cls.task = Task.objects.create(project=cls.project, title="Shared task", reporter=cls.alice)
        cls.hidden_task = Task.objects.create(project=cls.hidden, title="Secret", reporter=cls.owner)
        cls.sprint = Sprint.objects.create(project=cls.project, name="Current", start_date=date(2026, 1, 1), end_date=date(2026, 1, 14))
        cls.other_sprint = Sprint.objects.create(project=cls.hidden, name="Other", start_date=date(2026, 1, 1), end_date=date(2026, 1, 14))

    def test_two_project_users_share_created_tasks_and_status_changes(self):
        self.client.force_authenticate(self.alice)
        response = self.client.post(f"/api/projects/{self.project.pk}/tasks/", {
            "title": "Pair on delivery", "assignee": self.bob.pk, "sprint": self.sprint.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        task_id = response.data["id"]
        for user, status in [(self.bob, "in_progress"), (self.alice, "done")]:
            self.client.force_authenticate(user)
            listing = self.client.get(f"/api/projects/{self.project.pk}/tasks/")
            self.assertIn(task_id, [task["id"] for task in listing.data["results"]])
            response = self.client.patch(f"/api/tasks/{task_id}/", {"status": status}, format="json")
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["status"], status)
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get(f"/api/tasks/{task_id}/").data["status"], "done")

    def test_hidden_task_list_does_not_enrol_workspace_member_or_admin(self):
        for user, expected_count in [(self.bob, 0), (self.admin, 1), (self.outsider, 0)]:
            with self.subTest(user=user.email):
                self.client.force_authenticate(user)
                response = self.client.get(f"/api/projects/{self.hidden.pk}/tasks/")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["count"], expected_count)
                self.assertFalse(ProjectMember.objects.filter(project=self.hidden, user=user).exists())
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get(f"/api/tasks/{self.hidden_task.pk}/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/projects/{self.hidden.pk}/tasks/", {"title": "No access"}).status_code, 403)

    def test_viewer_can_read_but_cannot_create_update_or_delete_tasks(self):
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get(f"/api/tasks/{self.task.pk}/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/projects/{self.project.pk}/tasks/", {"title": "Forbidden"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/tasks/{self.task.pk}/", {"status": "done"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/tasks/{self.task.pk}/").status_code, 403)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "todo")

    def test_viewer_cannot_mutate_task_subresources(self):
        subtask = SubTask.objects.create(task=self.task, title="Existing")
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.post(f"/api/tasks/{self.task.pk}/subtasks/", {"title": "Forbidden"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/tasks/{self.task.pk}/subtasks/{subtask.pk}/", {"is_completed": True}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/tasks/{self.task.pk}/subtasks/{subtask.pk}/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/tasks/{self.task.pk}/dependencies/", {"depends_on_task": self.task.pk}).status_code, 403)

    def test_hidden_task_subresources_require_project_access(self):
        subtask = SubTask.objects.create(task=self.hidden_task, title="Secret child")
        dependency = TaskDependency.objects.create(task=self.hidden_task, depends_on_task=self.task)
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get(f"/api/tasks/{self.hidden_task.pk}/subtasks/").data["count"], 0)
        self.assertEqual(self.client.get(f"/api/tasks/{self.hidden_task.pk}/dependencies/").data["count"], 0)
        self.assertEqual(self.client.post(f"/api/tasks/{self.hidden_task.pk}/subtasks/", {"title": "Forbidden"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/tasks/{self.hidden_task.pk}/subtasks/{subtask.pk}/", {"is_completed": True}).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/tasks/{self.hidden_task.pk}/dependencies/{dependency.pk}/").status_code, 404)

    def test_dependencies_cannot_reference_tasks_in_another_project(self):
        self.client.force_authenticate(self.bob)
        response = self.client.post(f"/api/tasks/{self.task.pk}/dependencies/", {"depends_on_task": self.hidden_task.pk})
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(TaskDependency.objects.filter(task=self.task).exists())

    def test_subresource_writes_obey_workspace_task_edit_setting(self):
        self.workspace.allow_member_edit_tasks = False
        self.workspace.save(update_fields=["allow_member_edit_tasks"])
        subtask = SubTask.objects.create(task=self.task, title="Existing")
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.post(f"/api/tasks/{self.task.pk}/subtasks/", {"title": "Forbidden"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/tasks/{self.task.pk}/subtasks/{subtask.pk}/", {"is_completed": True}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/tasks/{self.task.pk}/dependencies/", {"depends_on_task": self.task.pk}).status_code, 403)
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.post(f"/api/tasks/{self.task.pk}/subtasks/", {"title": "Allowed for project admin"}).status_code, 201)

    def test_task_settings_restrict_members_and_preserve_manager_access(self):
        self.workspace.allow_member_create_tasks = False
        self.workspace.allow_member_edit_tasks = False
        self.workspace.save(update_fields=["allow_member_create_tasks", "allow_member_edit_tasks"])
        for user, create_status, update_status in [(self.bob, 403, 403), (self.alice, 201, 200), (self.admin, 201, 200)]:
            with self.subTest(user=user.email):
                self.client.force_authenticate(user)
                response = self.client.post(f"/api/projects/{self.project.pk}/tasks/", {"title": "Permission check"})
                self.assertEqual(response.status_code, create_status, response.data)
                response = self.client.patch(f"/api/tasks/{self.task.pk}/", {"status": "in_progress"})
                self.assertEqual(response.status_code, update_status, response.data)

    def test_stale_project_membership_requires_current_workspace_membership(self):
        WorkspaceMember.objects.filter(workspace=self.workspace, user=self.alice).delete()
        self.assertFalse(user_can_access_project(self.alice, self.project))
        self.assertFalse(accessible_projects_for(self.alice).exists())
        self.client.force_authenticate(self.alice)
        for url in [f"/api/projects/{self.project.pk}/", f"/api/tasks/{self.task.pk}/"]:
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get(f"/api/projects/{self.project.pk}/tasks/").data["count"], 0)
        self.assertEqual(self.client.get(f"/api/projects/{self.project.pk}/members/").data["count"], 0)
        self.assertEqual(self.client.post(f"/api/projects/{self.project.pk}/members/", {"user_id": self.outsider.pk}).status_code, 403)

    def test_project_users_can_read_members_but_only_managers_can_write(self):
        for user in [self.bob, self.viewer, self.admin]:
            self.client.force_authenticate(user)
            response = self.client.get(f"/api/projects/{self.project.pk}/members/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual({row["user"]["id"] for row in response.data["results"]}, {self.alice.pk, self.bob.pk, self.viewer.pk})
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.post(f"/api/projects/{self.project.pk}/members/", {"user_id": self.owner.pk}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/projects/{self.project.pk}/members/{self.viewer_membership.pk}/", {"role": "admin"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/projects/{self.project.pk}/members/{self.viewer_membership.pk}/").status_code, 403)
        self.client.force_authenticate(self.alice)
        response = self.client.post(f"/api/projects/{self.project.pk}/members/", {"user_id": self.owner.pk})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.client.patch(f"/api/projects/{self.project.pk}/members/{self.viewer_membership.pk}/", {"role": "member"}).status_code, 200)
        self.assertEqual(self.client.delete(f"/api/projects/{self.project.pk}/members/{self.viewer_membership.pk}/").status_code, 204)

    def test_project_member_update_rejects_outsider_and_duplicates(self):
        self.client.force_authenticate(self.alice)
        url = f"/api/projects/{self.project.pk}/members/{self.viewer_membership.pk}/"
        for user in [self.outsider, self.bob]:
            response = self.client.patch(url, {"user_id": user.pk}, format="json")
            self.assertEqual(response.status_code, 400, response.data)
        response = self.client.post(f"/api/projects/{self.project.pk}/members/", {"user_id": self.bob.pk})
        self.assertEqual(response.status_code, 400, response.data)
        self.viewer_membership.refresh_from_db()
        self.assertEqual(self.viewer_membership.user_id, self.viewer.pk)

    def test_workspace_member_list_does_not_leak_to_outsiders(self):
        other = Workspace.objects.create(name="Other", owner=self.outsider)
        WorkspaceMember.objects.create(workspace=other, user=self.outsider, role="owner")
        self.client.force_authenticate(self.outsider)
        response = self.client.get(f"/api/workspaces/{self.workspace.pk}/members/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get(f"/api/workspaces/{self.workspace.pk}/members/").data["count"], 5)
        self.assertEqual(self.client.get(f"/api/workspaces/{other.pk}/members/").data["count"], 0)

    def test_workspace_owner_cannot_be_demoted_replaced_or_deleted(self):
        membership = WorkspaceMember.objects.get(workspace=self.workspace, user=self.owner)
        for manager in [self.owner, self.admin]:
            self.client.force_authenticate(manager)
            url = f"/api/workspaces/{self.workspace.pk}/members/{membership.pk}/"
            for payload in [{"role": "admin"}, {"user_id": self.outsider.pk}]:
                response = self.client.patch(url, payload, format="json")
                self.assertEqual(response.status_code, 400, response.data)
            self.assertEqual(self.client.delete(url).status_code, 400)
        membership.refresh_from_db()
        self.assertEqual((membership.user_id, membership.role), (self.owner.pk, "owner"))

    def test_cannot_assign_owner_role_or_duplicate_workspace_members(self):
        self.client.force_authenticate(self.owner)
        url = f"/api/workspaces/{self.workspace.pk}/members/"
        self.assertEqual(self.client.post(url, {"user_id": self.outsider.pk, "role": "owner"}).status_code, 400)
        self.assertEqual(self.client.post(url, {"user_id": self.bob.pk, "role": "member"}).status_code, 400)
        member = WorkspaceMember.objects.get(workspace=self.workspace, user=self.bob)
        self.assertEqual(self.client.patch(f"{url}{member.pk}/", {"role": "owner"}).status_code, 400)
        self.assertEqual(self.client.patch(f"{url}{member.pk}/", {"user_id": self.alice.pk}).status_code, 400)
        self.assertEqual(self.client.post(f"/api/workspaces/{self.workspace.pk}/invitations/", {
            "email": self.outsider.email, "role": "owner",
        }).status_code, 400)

    def test_member_removal_cleans_all_project_memberships_only_in_workspace(self):
        other = Workspace.objects.create(name="Other", owner=self.owner)
        WorkspaceMember.objects.create(workspace=other, user=self.bob)
        other_project = Project.objects.create(workspace=other, name="Other", created_by=self.owner)
        ProjectMember.objects.create(project=other_project, user=self.bob)
        ProjectMember.objects.create(project=self.hidden, user=self.bob)
        membership = WorkspaceMember.objects.get(workspace=self.workspace, user=self.bob)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(f"/api/workspaces/{self.workspace.pk}/members/{membership.pk}/").status_code, 204)
        self.assertFalse(ProjectMember.objects.filter(project__workspace=self.workspace, user=self.bob).exists())
        self.assertTrue(ProjectMember.objects.filter(project=other_project, user=self.bob).exists())
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get(f"/api/tasks/{self.task.pk}/").status_code, 404)

    def test_member_removal_rolls_back_memberships_if_activity_write_fails(self):
        membership = WorkspaceMember.objects.get(workspace=self.workspace, user=self.bob)
        self.client.force_authenticate(self.owner)
        with patch("apps.workspaces.views.log_activity", side_effect=RuntimeError("Activity unavailable")):
            with self.assertRaises(RuntimeError):
                self.client.delete(f"/api/workspaces/{self.workspace.pk}/members/{membership.pk}/")
        self.assertTrue(WorkspaceMember.objects.filter(pk=membership.pk).exists())
        self.assertTrue(ProjectMember.objects.filter(project=self.project, user=self.bob).exists())

    def test_workspace_counts_all_members_for_list_and_detail(self):
        self.client.force_authenticate(self.bob)
        response = self.client.get("/api/workspaces/")
        self.assertEqual(response.data["results"][0]["member_count"], 5)
        self.assertEqual(self.client.get(f"/api/workspaces/{self.workspace.pk}/").data["member_count"], 5)

    def test_task_rejects_cross_project_sprint_on_create_and_update(self):
        self.client.force_authenticate(self.alice)
        response = self.client.post(f"/api/projects/{self.project.pk}/tasks/", {"title": "Invalid", "sprint": self.other_sprint.pk})
        self.assertEqual(response.status_code, 400, response.data)
        response = self.client.patch(f"/api/tasks/{self.task.pk}/", {"sprint": self.other_sprint.pk})
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("sprint", response.data)

    def test_assignee_requires_current_workspace_and_project_access(self):
        workspace_only = get_user_model().objects.create_user(email="workspace-only@collaboration.test", full_name="No project")
        WorkspaceMember.objects.create(workspace=self.workspace, user=workspace_only)
        stale = get_user_model().objects.create_user(email="stale@collaboration.test", full_name="Removed")
        ProjectMember.objects.create(project=self.project, user=stale, role="admin")
        self.client.force_authenticate(self.alice)
        for assignee in [self.outsider, workspace_only, stale]:
            with self.subTest(assignee=assignee.email):
                payload = {"title": "Invalid assignment", "assignee": assignee.pk}
                response = self.client.post(f"/api/projects/{self.project.pk}/tasks/", payload)
                self.assertEqual(response.status_code, 400, response.data)
                self.assertIn("assignee", response.data)
                response = self.client.patch(f"/api/tasks/{self.task.pk}/", {"assignee": assignee.pk})
                self.assertEqual(response.status_code, 400, response.data)
        for assignee in [self.owner, self.admin, self.bob, self.viewer]:
            response = self.client.patch(f"/api/tasks/{self.task.pk}/", {"assignee": assignee.pk})
            self.assertEqual(response.status_code, 200, response.data)
        response = self.client.patch(f"/api/tasks/{self.task.pk}/", {"assignee": None, "sprint": None}, format="json")
        self.assertEqual(response.status_code, 200, response.data)

    def test_project_role_and_task_count_queries_do_not_grow_per_project(self):
        self.client.force_authenticate(self.admin)
        url = f"/api/workspaces/{self.workspace.pk}/projects/"
        with CaptureQueriesContext(connection) as small:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for index in range(8):
            Project.objects.create(workspace=self.workspace, name=f"Extra {index}", created_by=self.owner)
        with CaptureQueriesContext(connection) as large:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 10)
        self.assertEqual(len(large), len(small))
        shared = next(row for row in response.data["results"] if row["id"] == self.project.pk)
        self.assertEqual(shared["task_count"], 1)
        self.assertIsNone(shared["user_project_role"])
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.get(url).data["results"][0]["user_project_role"], "admin")

    def test_project_create_returns_role_without_annotation(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(f"/api/workspaces/{self.workspace.pk}/projects/", {"name": "New"})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["user_project_role"], "admin")

    def test_task_list_queries_do_not_grow_per_task(self):
        self.client.force_authenticate(self.bob)
        url = f"/api/projects/{self.project.pk}/tasks/"
        with CaptureQueriesContext(connection) as small:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for index in range(8):
            task = Task.objects.create(project=self.project, title=f"Extra {index}", reporter=self.alice, assignee=self.bob)
            SubTask.objects.create(task=task, title="Child")
        with CaptureQueriesContext(connection) as large:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 9)
        self.assertEqual(len(large), len(small))

    def test_task_update_fetches_task_once(self):
        self.client.force_authenticate(self.bob)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.patch(f"/api/tasks/{self.task.pk}/", {"status": "in_progress"})
        self.assertEqual(response.status_code, 200, response.data)
        task_reads = [q["sql"] for q in queries if q["sql"].startswith("SELECT") and 'FROM "tasks_task"' in q["sql"]]
        self.assertEqual(len(task_reads), 1, task_reads)

    def test_member_inviter_cannot_grant_admin(self):
        self.workspace.allow_member_invite_members = True
        self.workspace.save(update_fields=["allow_member_invite_members"])
        self.client.force_authenticate(self.bob)
        url = f"/api/workspaces/{self.workspace.pk}/invitations/"
        self.assertEqual(self.client.post(url, {"email": self.outsider.email, "role": "admin"}).status_code, 403)
        self.assertFalse(WorkspaceInvitation.objects.filter(workspace=self.workspace).exists())
        response = self.client.post(url, {"email": self.outsider.email, "role": "member"})
        self.assertEqual(response.status_code, 201, response.data)

    def test_acceptance_preserves_existing_owner_and_admin_roles(self):
        for user, role in [(self.owner, "owner"), (self.admin, "admin")]:
            invitation = WorkspaceInvitation.objects.create(workspace=self.workspace, email=user.email, role="member")
            invitation.accept(user)
            self.assertEqual(WorkspaceMember.objects.get(workspace=self.workspace, user=user).role, role)
            invitation.accept(user)
            self.assertEqual(WorkspaceMember.objects.get(workspace=self.workspace, user=user).role, role)

    def test_acceptance_replay_does_not_reenrol_removed_member(self):
        invitation = WorkspaceInvitation.objects.create(workspace=self.workspace, email=self.outsider.email, role="member")
        invitation.accept(self.outsider)
        first_accepted_at = invitation.accepted_at
        WorkspaceMember.objects.filter(workspace=self.workspace, user=self.outsider).delete()
        stale_copy = WorkspaceInvitation.objects.get(pk=invitation.pk)
        stale_copy.accept(self.outsider)
        self.assertFalse(WorkspaceMember.objects.filter(workspace=self.workspace, user=self.outsider).exists())
        self.assertEqual(stale_copy.accepted_at, first_accepted_at)

    def test_reinviting_rotates_token_and_invalidates_previous_link(self):
        self.client.force_authenticate(self.owner)
        url = f"/api/workspaces/{self.workspace.pk}/invitations/"
        first = self.client.post(url, {"email": self.outsider.email, "role": "member"})
        self.assertEqual(first.status_code, 201, first.data)
        invitation = WorkspaceInvitation.objects.get(workspace=self.workspace, email=self.outsider.email)
        old_token = invitation.token
        invitation.accept(self.outsider)
        second = self.client.post(url, {"email": self.outsider.email, "role": "admin"})
        self.assertEqual(second.status_code, 201, second.data)
        invitation.refresh_from_db()
        self.assertNotEqual(invitation.token, old_token)
        self.assertEqual(invitation.status, "pending")
        self.assertEqual(self.client.get(f"/api/invitations/{old_token}/accept/").status_code, 404)
