"""SprintFlow's MCP policy around Django OAuth Toolkit's protocol implementation."""

import ipaddress
import json
from urllib.parse import urlsplit

from django.conf import settings
from django.http import JsonResponse
from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.views import DynamicClientRegistrationView
from oauthlib.oauth2.rfc6749.errors import CustomOAuth2Error


def mcp_resource_url():
    return settings.MCP_PUBLIC_URL.rstrip("/") + "/mcp"


class MCPOAuth2Validator(OAuth2Validator):
    """Bind grants and tokens to MCP; leave PKCE and RFC 8707 handling to DOT."""

    def _bind_mcp_resource(self, request):
        resource = getattr(request, "resource", None)
        if resource and resource != [mcp_resource_url()]:
            raise CustomOAuth2Error(
                error="invalid_target",
                description="The resource must be the SprintFlow MCP endpoint.",
                request=request,
            )
        request.resource = [mcp_resource_url()]

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        self._bind_mcp_resource(request)
        return super().save_authorization_code(client_id, code, request, *args, **kwargs)

    def _check_and_set_request_resource(self, request):
        super()._check_and_set_request_resource(request)
        self._bind_mcp_resource(request)

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        valid = super().validate_code(client_id, code, client, request, *args, **kwargs)
        if valid:
            self._check_and_set_request_resource(request)
        return valid

    def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
        valid = super().validate_refresh_token(refresh_token, client, request, *args, **kwargs)
        if valid:
            self._check_and_set_request_resource(request)
        return valid


def _safe_redirect_uri(uri):
    if not isinstance(uri, str) or any(character.isspace() or ord(character) < 32 for character in uri):
        return False
    try:
        parsed = urlsplit(uri)
        host = parsed.hostname
        parsed.port
    except ValueError:
        return False
    if not host or parsed.username is not None or parsed.password is not None or "#" in uri:
        return False
    if parsed.scheme == "https":
        return True
    if parsed.scheme != "http":
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class MCPClientRegistrationView(DynamicClientRegistrationView):
    """Constrain anonymous registration to public authorization-code clients."""

    def post(self, request, *args, **kwargs):
        try:
            metadata = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return super().post(request, *args, **kwargs)
        if not isinstance(metadata, dict):
            return super().post(request, *args, **kwargs)

        allowed_fields = {
            "redirect_uris", "client_name", "client_uri", "logo_uri", "contacts",
            "tos_uri", "policy_uri", "software_id", "software_version", "scope",
            "grant_types", "response_types", "token_endpoint_auth_method",
        }
        grant_types = metadata.get("grant_types", ["authorization_code"])
        redirects = metadata.get("redirect_uris", [])
        valid_grants = (
            isinstance(grant_types, list)
            and "authorization_code" in grant_types
            and all(grant in ("authorization_code", "refresh_token") for grant in grant_types)
        )
        scope = metadata.get("scope", "sprintflow")
        if (
            set(metadata) - allowed_fields
            or not valid_grants
            or metadata.get("response_types", ["code"]) != ["code"]
            or metadata.get("token_endpoint_auth_method", "none") != "none"
            or not isinstance(scope, str)
            or set(scope.split()) - {"sprintflow"}
        ):
            return JsonResponse({
                "error": "invalid_client_metadata",
                "error_description": "Register a public authorization_code client with PKCE and auth method none.",
            }, status=400)
        if not isinstance(redirects, list) or not redirects or not all(_safe_redirect_uri(uri) for uri in redirects):
            return JsonResponse({
                "error": "invalid_redirect_uri",
                "error_description": "Use HTTPS redirects or HTTP redirects to localhost or a loopback IP.",
            }, status=400)

        metadata.setdefault("token_endpoint_auth_method", "none")
        request._body = json.dumps(metadata).encode("utf-8")
        return super().post(request, *args, **kwargs)
