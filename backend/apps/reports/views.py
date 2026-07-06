from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from apps.projects.models import Project
from apps.tasks.models import Task
from .services import project_report, sprint_health_score


class ProjectReportView(APIView):
    def get(self, request, project_id):
        project = Project.objects.get(pk=project_id, workspace__memberships__user=request.user)
        return Response(project_report(project))


class SprintHealthView(APIView):
    def get(self, request, project_id):
        tasks = Task.objects.filter(project_id=project_id, project__workspace__memberships__user=request.user)
        return Response({"score": sprint_health_score(tasks)})


class WorkloadView(APIView):
    def get(self, request, project_id):
        return Response(project_report(Project.objects.get(pk=project_id, workspace__memberships__user=request.user))["workload"])


class OverdueTasksView(APIView):
    def get(self, request, project_id):
        tasks = Task.objects.filter(project_id=project_id, project__workspace__memberships__user=request.user, due_date__lt=timezone.localdate()).exclude(status=Task.Status.DONE)
        return Response([{"id": task.id, "title": task.title, "due_date": task.due_date, "priority": task.priority} for task in tasks])
