"""Mount at the origin root: path('', include('apps.integrations.urls'))."""

from django.contrib.auth.views import LoginView
from django.urls import include, path
from oauth2_provider import views

from .oauth import MCPClientRegistrationView


oauth_urlpatterns = [
    path("login/", LoginView.as_view(
        template_name="integrations/login.html",
        next_page="oauth2_provider:authorized-token-list",
    ), name="login"),
    path("authorize/", views.AuthorizationView.as_view(
        template_name="integrations/authorize.html",
    ), name="authorize"),
    path("token/", views.TokenView.as_view(), name="token"),
    path("revoke_token/", views.RevokeTokenView.as_view(), name="revoke-token"),
    path("register/", MCPClientRegistrationView.as_view(), name="dcr-register"),
    path("register/<str:client_id>/", views.DynamicClientRegistrationManagementView.as_view(
        http_method_names=["get", "delete", "head", "options"],
    ), name="dcr-register-management"),
    path("authorized_tokens/", views.AuthorizedTokensListView.as_view(), name="authorized-token-list"),
    path("authorized_tokens/<slug:pk>/delete/", views.AuthorizedTokenDeleteView.as_view(),
         name="authorized-token-delete"),
]

metadata_urlpatterns = [
    path(".well-known/oauth-authorization-server", views.OAuthServerMetadataView.as_view(),
         name="oauth-server-metadata"),
    path(".well-known/oauth-protected-resource/mcp", views.OAuthProtectedResourceMetadataView.as_view(),
         name="oauth-resource-metadata"),
    path(".well-known/oauth-protected-resource", views.OAuthProtectedResourceMetadataView.as_view(),
         name="oauth-resource-metadata-root"),
]

urlpatterns = metadata_urlpatterns + [
    path("oauth/", include((oauth_urlpatterns, "oauth2_provider"), namespace="oauth2_provider")),
]
