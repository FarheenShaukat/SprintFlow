from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.models import AIInsight
from apps.projects.models import Project
from apps.tasks.models import Task
from .serializers import PriorityInputSerializer, RiskInputSerializer, SprintSummaryInputSerializer, SuggestedAssigneeInputSerializer, TaskBreakdownInputSerializer
from .services import estimate_task_risk, sprint_summary, store_insight, suggest_assignee, suggest_priority, task_breakdown


class TaskBreakdownView(APIView):
    def post(self, request):
        serializer = TaskBreakdownInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = Task.objects.filter(pk=serializer.validated_data.get("task_id"), project__workspace__memberships__user=request.user).first()
        content = {"subtasks": task_breakdown(serializer.validated_data["title"], serializer.validated_data.get("description", ""))}
        store_insight(insight_type=AIInsight.InsightType.BREAKDOWN, content=content, task=task, project=task.project if task else None)
        return Response(content)


class SuggestPriorityView(APIView):
    def post(self, request):
        serializer = PriorityInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content = suggest_priority(serializer.validated_data["title"], serializer.validated_data.get("description", ""), serializer.validated_data.get("due_date"))
        task = Task.objects.filter(pk=serializer.validated_data.get("task_id"), project__workspace__memberships__user=request.user).first()
        if task:
            task.priority = content["priority"]
            task.ai_priority_reason = content["reason"]
            task.save(update_fields=["priority", "ai_priority_reason", "updated_at"])
        store_insight(insight_type=AIInsight.InsightType.PRIORITY, content=content, task=task, project=task.project if task else None)
        return Response(content)


class EstimateRiskView(APIView):
    def post(self, request):
        serializer = RiskInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = Task.objects.get(pk=serializer.validated_data["task_id"], project__workspace__memberships__user=request.user)
        content = estimate_task_risk(task)
        task.ai_risk_score = content["risk_score"]
        task.save(update_fields=["ai_risk_score", "updated_at"])
        store_insight(insight_type=AIInsight.InsightType.RISK, content=content, task=task, project=task.project, risk_score=content["risk_score"])
        return Response(content)


class SuggestAssigneeView(APIView):
    def post(self, request):
        serializer = SuggestedAssigneeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = Project.objects.get(pk=serializer.validated_data["project_id"], workspace__memberships__user=request.user)
        content = suggest_assignee(project, serializer.validated_data["title"], serializer.validated_data.get("description", ""))
        store_insight(insight_type=AIInsight.InsightType.ASSIGNEE, content=content, project=project)
        return Response(content)


class SprintSummaryView(APIView):
    def post(self, request):
        serializer = SprintSummaryInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = Project.objects.get(pk=serializer.validated_data["project_id"], workspace__memberships__user=request.user)
        content = sprint_summary(project)
        store_insight(insight_type=AIInsight.InsightType.SUMMARY, content=content, project=project)
        return Response(content)
