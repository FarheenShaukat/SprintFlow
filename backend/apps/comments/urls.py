from django.urls import path

from .views import CommentViewSet

comment_list = CommentViewSet.as_view({"get": "list", "post": "create"})
comment_detail = CommentViewSet.as_view({"patch": "partial_update", "delete": "destroy"})

urlpatterns = [
    path("tasks/<int:task_id>/comments", comment_list, name="task-comments-no-slash"),
    path("tasks/<int:task_id>/comments/", comment_list, name="task-comments"),
    path("comments/<int:pk>", comment_detail, name="comment-detail-no-slash"),
    path("comments/<int:pk>/", comment_detail, name="comment-detail"),
]
