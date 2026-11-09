"""Mount at the origin root: path('', include('apps.integrations.urls'))."""

from django.contrib.auth.views import LoginView
from django.urls import include, path, re_path
from oauth2_provider import views

from .oauth import MCPClientRegistrationView


oauth_urlpatterns = [
    re_path(r"^login/?$", LoginView.as_view(
        template_name="integrations/login.html",
        next_page="oauth2_provider:authorized-token-list",
    ), name="login"),
    re_path(r"^authorize/?$", views.AuthorizationView.as_view(
        template_name="integrations/authorize.html",
    ), name="authorize"),
    re_path(r"^token/?$", views.TokenView.as_view(), name="token"),
    re_path(r"^revoke_token/?$", views.RevokeTokenView.as_view(), name="revoke-token"),
    re_path(r"^register/?$", MCPClientRegistrationView.as_view(), name="dcr-register"),
    re_path(r"^register/(?P<client_id>[^/]+)/?$", views.DynamicClientRegistrationManagementView.as_view(
        http_method_names=["get", "delete", "head", "options"],
    ), name="dcr-register-management"),
    re_path(r"^authorized_tokens/?$", views.AuthorizedTokensListView.as_view(), name="authorized-token-list"),
    re_path(r"^authorized_tokens/(?P<pk>[-a-zA-Z0-9_]+)/delete/?$", views.AuthorizedTokenDeleteView.as_view(),
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
