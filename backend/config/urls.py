from django.contrib import admin
from django.db import connection
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView, LogoutView, MeView, RegisterView


def health_check(request):
    return JsonResponse({"status": "ok"})


def database_health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("select 1")
            cursor.fetchone()
            tables = connection.introspection.table_names(cursor)
    except OperationalError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)
    return JsonResponse({
        "status": "ok",
        "engine": connection.settings_dict["ENGINE"],
        "migrated": "django_migrations" in tables,
        "has_users_table": "accounts_user" in tables,
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health", health_check, name="health-check-no-slash"),
    path("api/health/", health_check, name="health-check"),
    path("api/health/db", database_health_check, name="database-health-check-no-slash"),
    path("api/health/db/", database_health_check, name="database-health-check"),
    path("api/schema", SpectacularAPIView.as_view(), name="schema-no-slash"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui-no-slash"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/register", RegisterView.as_view(), name="register-no-slash"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login", LoginView.as_view(), name="login-no-slash"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh", TokenRefreshView.as_view(), name="token-refresh-no-slash"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/me", MeView.as_view(), name="me-no-slash"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/auth/logout", LogoutView.as_view(), name="logout-no-slash"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/", include("apps.workspaces.urls")),
    path("api/", include("apps.projects.urls")),
    path("api/", include("apps.tasks.urls")),
    path("api/", include("apps.comments.urls")),
    path("api/", include("apps.attachments.urls")),
    path("api/", include("apps.activity.urls")),
    path("api/", include("apps.ai.urls")),
    path("api/", include("apps.reports.urls")),
]
