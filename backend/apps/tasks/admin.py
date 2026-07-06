from django.contrib import admin

from .models import SubTask, Task, TaskDependency

admin.site.register(Task)
admin.site.register(SubTask)
admin.site.register(TaskDependency)
