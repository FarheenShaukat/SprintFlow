from datetime import timedelta

import django_filters
from django.utils import timezone

from .models import Task


class TaskFilter(django_filters.FilterSet):
    blocked = django_filters.BooleanFilter(field_name="is_blocked")
    due = django_filters.CharFilter(method="filter_due")
    mine = django_filters.BooleanFilter(method="filter_mine")

    class Meta:
        model = Task
        fields = ["status", "priority", "assignee", "sprint", "blocked", "mine"]

    def filter_due(self, queryset, name, value):
        today = timezone.localdate()
        if value == "today":
            return queryset.filter(due_date=today)
        if value == "overdue":
            return queryset.exclude(status=Task.Status.DONE).filter(due_date__lt=today)
        if value == "week":
            return queryset.filter(due_date__range=(today, today + timedelta(days=7)))
        return queryset

    def filter_mine(self, queryset, name, value):
        if value:
            return queryset.filter(assignee=self.request.user)
        return queryset
