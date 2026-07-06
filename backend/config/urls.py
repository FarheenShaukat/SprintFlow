from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView, LogoutView, MeView, RegisterView


def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health", health_check, name="health-check-no-slash"),
    path("api/health/", health_check, name="health-check"),
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
