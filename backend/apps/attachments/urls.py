from django.urls import path

from .views import AttachmentViewSet

attachment_list = AttachmentViewSet.as_view({"get": "list", "post": "create"})
attachment_detail = AttachmentViewSet.as_view({"delete": "destroy"})

urlpatterns = [
    path("tasks/<int:task_id>/attachments", attachment_list, name="task-attachments-no-slash"),
    path("tasks/<int:task_id>/attachments/", attachment_list, name="task-attachments"),
    path("attachments/<int:pk>", attachment_detail, name="attachment-detail-no-slash"),
    path("attachments/<int:pk>/", attachment_detail, name="attachment-detail"),
]
