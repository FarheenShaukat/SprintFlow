from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404

from apps.projects.models import Project
from apps.projects.access import accessible_projects_for
from apps.tasks.models import Task
from .services import project_report, sprint_health_score


class ProjectReportView(APIView):
    def get(self, request, project_id):
        project = get_object_or_404(accessible_projects_for(request.user), pk=project_id)
        return Response(project_report(project))


class SprintHealthView(APIView):
    def get(self, request, project_id):
        project = get_object_or_404(accessible_projects_for(request.user), pk=project_id)
        tasks = Task.objects.filter(project=project)
        return Response({"score": sprint_health_score(tasks)})


class WorkloadView(APIView):
    def get(self, request, project_id):
        return Response(project_report(get_object_or_404(accessible_projects_for(request.user), pk=project_id))["workload"])


class OverdueTasksView(APIView):
    def get(self, request, project_id):
        project = get_object_or_404(accessible_projects_for(request.user), pk=project_id)
        tasks = Task.objects.filter(project=project, due_date__lt=timezone.localdate()).exclude(status=Task.Status.DONE)
        return Response([{"id": task.id, "title": task.title, "due_date": task.due_date, "priority": task.priority} for task in tasks])
