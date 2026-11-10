"""Exercise the public MCP OAuth boundary with real toolkit grants and tokens."""

import base64
import hashlib
import json
from urllib.parse import parse_qs, urlencode, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from oauth2_provider.models import get_access_token_model, get_application_model, get_grant_model


ORIGIN = "https://sprint-flow-five.vercel.app"
RESOURCE = ORIGIN + "/mcp"
CALLBACK = "http://127.0.0.1:54321/callback"
VERIFIER = "a" * 64
CHALLENGE = base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).rstrip(b"=").decode()
OAUTH_SETTINGS = {
    "SCOPES": {"sprintflow": "Read and manage your SprintFlow projects, tasks and teams"},
    "DEFAULT_SCOPES": ["sprintflow"],
    "PKCE_REQUIRED": True,
    "ROTATE_REFRESH_TOKEN": True,
    "OAUTH2_VALIDATOR_CLASS": "apps.integrations.oauth.MCPOAuth2Validator",
    "ALWAYS_RELOAD_OAUTHLIB_CORE": True,
    "DCR_ENABLED": True,
    "DCR_REGISTRATION_PERMISSION_CLASSES": ["oauth2_provider.dcr.AllowAllDCRPermission"],
    "OIDC_ISS_ENDPOINT": ORIGIN,
    "OAUTH2_PROTECTED_RESOURCE_IDENTIFIER": RESOURCE,
    "OAUTH2_PROTECTED_RESOURCE_AUTHORIZATION_SERVERS": [ORIGIN],
    "OAUTH2_RESPONSE_TYPES_SUPPORTED": ["code"],
    "OAUTH2_GRANT_TYPES_SUPPORTED": ["authorization_code", "refresh_token"],
    "OAUTH2_TOKEN_ENDPOINT_AUTH_METHODS_SUPPORTED": ["none"],
    "COMPLIANT_BCP_RFC9700_PKCE_METHOD": True,
    "CIMD_ENABLED": False,
}


@override_settings(MCP_PUBLIC_URL=ORIGIN, LOGIN_URL="/oauth/login/", OAUTH2_PROVIDER=OAUTH_SETTINGS)
class MCPOAuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            email="mcp@example.com", password="safe-test-password", full_name="MCP User"
        )

    def register(self, **metadata):
        data = {
            "client_name": "MCP test client",
            "redirect_uris": [CALLBACK],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        }
        data.update(metadata)
        return self.client.post("/oauth/register/", json.dumps(data), content_type="application/json")

    def authorize(self, client_id, **changes):
        self.client.force_login(self.user)
        params = {
            "client_id": client_id,
            "redirect_uri": CALLBACK,
            "response_type": "code",
            "scope": "sprintflow",
            "state": "opaque-client-state",
            "code_challenge": CHALLENGE,
            "code_challenge_method": "S256",
            "resource": RESOURCE,
        }
        params.update(changes)
        params = {key: value for key, value in params.items() if value is not None}
        consent = self.client.get("/oauth/authorize/", params)
        self.assertEqual(consent.status_code, 200)
        self.assertContains(consent, "csrfmiddlewaretoken")
        form = consent.context["form"]
        data = {field.name: field.value() or "" for field in form if field.is_hidden}
        data["allow"] = "Authorize"
        response = self.client.post("/oauth/authorize/", data)
        self.assertEqual(response.status_code, 302)
        result = parse_qs(urlsplit(response["Location"]).query)
        self.assertEqual(result.get("state"), ["opaque-client-state"])
        return result

    def exchange(self, client_id, code, **changes):
        data = {
            "grant_type": "authorization_code", "client_id": client_id,
            "code": code, "redirect_uri": CALLBACK, "code_verifier": VERIFIER,
            "resource": RESOURCE,
        }
        data.update(changes)
        return self.client.post("/oauth/token/", {k: v for k, v in data.items() if v is not None})

    def issue_tokens(self, **authorization_changes):
        registration = self.register()
        self.assertEqual(registration.status_code, 201, registration.content)
        client_id = registration.json()["client_id"]
        result = self.authorize(client_id, **authorization_changes)
        response = self.exchange(client_id, result["code"][0])
        self.assertEqual(response.status_code, 200, response.content)
        return client_id, response.json()

    def test_discovery_uses_public_origin_and_advertises_registration_and_s256(self):
        response = self.client.get("/.well-known/oauth-authorization-server")
        self.assertEqual(response.status_code, 200)
        metadata = response.json()
        self.assertEqual(metadata["issuer"], ORIGIN)
        for key, path in {
            "authorization_endpoint": "/oauth/authorize", "token_endpoint": "/oauth/token",
            "registration_endpoint": "/oauth/register", "revocation_endpoint": "/oauth/revoke_token",
        }.items():
            self.assertEqual(metadata[key], ORIGIN + path)
        self.assertEqual(metadata["code_challenge_methods_supported"], ["S256"])
        self.assertEqual(metadata["token_endpoint_auth_methods_supported"], ["none"])
        resource = self.client.get("/.well-known/oauth-protected-resource/mcp").json()
        self.assertEqual(resource["resource"], RESOURCE)
        self.assertEqual(resource["authorization_servers"], [ORIGIN])
        self.assertEqual(resource["scopes_supported"], ["sprintflow"])

    def test_anonymous_registration_creates_public_client_without_secret(self):
        response = self.register()
        self.assertEqual(response.status_code, 201, response.content)
        self.assertNotIn("client_secret", response.json())
        app = get_application_model().objects.get(client_id=response.json()["client_id"])
        self.assertEqual(app.client_type, "public")
        self.assertEqual(app.authorization_grant_type, "authorization-code")
        self.assertFalse(app.skip_authorization)
        self.assertIsNone(app.user_id)

    def test_registration_defaults_to_public_client(self):
        response = self.client.post("/oauth/register/", json.dumps({"redirect_uris": [CALLBACK]}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["token_endpoint_auth_method"], "none")
        self.assertNotIn("client_secret", response.json())

    def test_registration_rejects_unsafe_metadata(self):
        invalid = [
            {"grant_types": ["password"]}, {"grant_types": ["client_credentials"]},
            {"grant_types": ["refresh_token"]}, {"grant_types": "authorization_code"},
            {"token_endpoint_auth_method": "client_secret_basic"},
            {"response_types": ["token"]}, {"scope": "admin"},
            {"owner": self.user.pk}, {"user": self.user.pk}, {"user_id": self.user.pk},
            {"skip_authorization": True}, {"client_secret": "attacker-chosen"},
            {"redirect_uris": ["http://example.com/callback"]},
            {"redirect_uris": ["javascript:alert(1)"]},
            {"redirect_uris": ["https://example.com/callback#fragment"]},
            {"redirect_uris": ["https://user:pass@example.com/callback"]},
            {"redirect_uris": ["http://127.0.0.1.evil.example/callback"]},
            {"redirect_uris": ["https://example.com/a https://evil.example/b"]},
            {"redirect_uris": []}, {"redirect_uris": [42]},
        ]
        for metadata in invalid:
            with self.subTest(metadata=metadata):
                response = self.register(**metadata)
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn(response.json()["error"], ["invalid_client_metadata", "invalid_redirect_uri"])
        self.assertFalse(get_application_model().objects.exists())

    def test_registration_allows_https_and_loopback_callbacks(self):
        for uri in ["https://claude.ai/api/mcp/auth_callback", "http://localhost:3210/callback",
                    "http://[::1]:3210/callback", "http://127.0.0.2:3210/callback"]:
            with self.subTest(uri=uri):
                response = self.register(redirect_uris=[uri])
                self.assertEqual(response.status_code, 201, response.content)

    def test_registration_management_cannot_bypass_public_client_policy(self):
        registration = self.register().json()
        url = urlsplit(registration["registration_client_uri"]).path
        self.assertEqual(self.client.get(url).status_code, 401)
        headers = {"HTTP_AUTHORIZATION": "Bearer " + registration["registration_access_token"]}
        self.assertEqual(self.client.get(url, **headers).status_code, 200)
        response = self.client.put(url, json.dumps({
            "redirect_uris": ["http://attacker.example/callback"],
            "token_endpoint_auth_method": "client_secret_basic",
        }), content_type="application/json", **headers)
        self.assertEqual(response.status_code, 405)
        app = get_application_model().objects.get(client_id=registration["client_id"])
        self.assertEqual(app.client_type, "public")
        self.assertEqual(app.redirect_uris, CALLBACK)
        self.assertEqual(self.client.delete(url, **headers).status_code, 204)

    def test_malformed_registration_uses_toolkit_errors(self):
        for body in ["not-json", "[]", "null"]:
            with self.subTest(body=body):
                response = self.client.post("/oauth/register/", body, content_type="application/json")
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"], "invalid_client_metadata")

    def test_login_requires_csrf_and_authenticates_email_preserving_next(self):
        browser = Client(enforce_csrf_checks=True)
        next_url = "/oauth/authorize/?" + urlencode({"client_id": "example", "state": "saved"})
        response = browser.get("/oauth/login/", {"next": next_url})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        credentials = {"username": self.user.email, "password": "safe-test-password", "next": next_url}
        self.assertEqual(browser.post("/oauth/login/", credentials).status_code, 403)
        credentials["csrfmiddlewaretoken"] = browser.cookies["csrftoken"].value
        response = browser.post("/oauth/login/", credentials)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], next_url)
        self.assertEqual(int(browser.session["_auth_user_id"]), self.user.pk)

    def test_unauthenticated_authorization_redirects_to_sprintflow_login(self):
        response = self.client.get("/oauth/authorize/", {"client_id": "client", "state": "preserved"})
        self.assertEqual(response.status_code, 302)
        location = urlsplit(response["Location"])
        self.assertEqual(location.path, "/oauth/login/")
        self.assertIn("state=preserved", parse_qs(location.query)["next"][0])

    def test_code_exchange_refresh_and_revocation_preserve_audience(self):
        client_id, tokens = self.issue_tokens()
        access = get_access_token_model().objects.get(token=tokens["access_token"])
        self.assertEqual(access.user, self.user)
        self.assertEqual(access.resource, [RESOURCE])
        self.assertEqual(access.scope, "sprintflow")
        refresh = self.client.post("/oauth/token/", {
            "grant_type": "refresh_token", "client_id": client_id, "refresh_token": tokens["refresh_token"],
        })
        self.assertEqual(refresh.status_code, 200, refresh.content)
        renewed = refresh.json()
        self.assertNotEqual(renewed["refresh_token"], tokens["refresh_token"])
        access = get_access_token_model().objects.get(token=renewed["access_token"])
        self.assertEqual(access.resource, [RESOURCE])
        revoke = self.client.post("/oauth/revoke_token/", {
            "client_id": client_id, "token": renewed["refresh_token"], "token_type_hint": "refresh_token",
        })
        self.assertEqual(revoke.status_code, 200)
        retry = self.client.post("/oauth/token/", {
            "grant_type": "refresh_token", "client_id": client_id, "refresh_token": renewed["refresh_token"],
        })
        self.assertEqual(retry.status_code, 400)
        self.assertEqual(retry.json()["error"], "invalid_grant")
        self.assertFalse(get_access_token_model().objects.filter(pk=access.pk).exists())

    def test_omitted_resource_defaults_to_mcp_audience(self):
        client_id = self.register().json()["client_id"]
        code = self.authorize(client_id, resource=None)["code"][0]
        self.assertEqual(get_grant_model().objects.get(code=code).resource, [RESOURCE])
        response = self.exchange(client_id, code, resource=None)
        self.assertEqual(response.status_code, 200, response.content)
        access = get_access_token_model().objects.get(token=response.json()["access_token"])
        self.assertEqual(access.resource, [RESOURCE])

    def test_bad_verifier_missing_verifier_bad_code_and_code_replay_are_rejected(self):
        client_id = self.register().json()["client_id"]
        code = self.authorize(client_id)["code"][0]
        for overrides in [{"code_verifier": "b" * 64}, {"code_verifier": None}]:
            with self.subTest(overrides=overrides):
                response = self.exchange(client_id, code, **overrides)
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn(response.json()["error"], ["invalid_grant", "invalid_request"])
        response = self.exchange(client_id, "bad-code")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_grant")
        self.assertEqual(self.exchange(client_id, code).status_code, 200)
        response = self.exchange(client_id, code)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_grant")

    def test_missing_pkce_and_plain_pkce_do_not_issue_codes(self):
        client_id = self.register().json()["client_id"]
        plain = self.authorize(client_id, code_challenge=VERIFIER, code_challenge_method="plain")
        self.assertEqual(plain["error"], ["invalid_request"])
        self.client.force_login(self.user)
        response = self.client.get("/oauth/authorize/", {
            "client_id": client_id, "redirect_uri": CALLBACK, "response_type": "code", "scope": "sprintflow",
        })
        self.assertIn(response.status_code, [302, 400])
        self.assertFalse(get_grant_model().objects.exists())

    def test_token_and_refresh_cannot_change_audience(self):
        client_id = self.register().json()["client_id"]
        code = self.authorize(client_id)["code"][0]
        response = self.exchange(client_id, code, resource="https://attacker.example/mcp")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_target")
        client_id, tokens = self.issue_tokens()
        response = self.client.post("/oauth/token/", {
            "grant_type": "refresh_token", "client_id": client_id,
            "refresh_token": tokens["refresh_token"], "resource": ORIGIN + "/other",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_target")

    def test_authorization_rejects_wrong_resource(self):
        client_id = self.register().json()["client_id"]
        result = self.authorize(client_id, resource="https://attacker.example/mcp")
        self.assertEqual(result.get("error"), ["invalid_target"])
        self.assertFalse(get_grant_model().objects.exists())

    def test_consent_tampering_cannot_change_audience(self):
        client_id = self.register().json()["client_id"]
        self.client.force_login(self.user)
        consent = self.client.get("/oauth/authorize/", {
            "client_id": client_id, "redirect_uri": CALLBACK, "response_type": "code",
            "scope": "sprintflow", "code_challenge": CHALLENGE,
            "code_challenge_method": "S256", "resource": RESOURCE, "state": "saved-state",
        })
        data = {field.name: field.value() or "" for field in consent.context["form"] if field.is_hidden}
        data.update(allow="Authorize", resource=ORIGIN + "/other")
        response = self.client.post("/oauth/authorize/", data)
        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlsplit(response["Location"]).query)
        self.assertEqual(query["error"], ["invalid_target"])
        self.assertEqual(query["state"], ["saved-state"])
        self.assertFalse(get_grant_model().objects.exists())

    def test_repeated_resources_cannot_hide_an_unapproved_audience(self):
        client_id = self.register().json()["client_id"]
        code = self.authorize(client_id)["code"][0]
        response = self.exchange(client_id, code, resource=["https://attacker.example/mcp", RESOURCE])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_target")
        self.assertFalse(get_access_token_model().objects.filter(scope="sprintflow").exists())

    def test_denied_consent_does_not_create_grant(self):
        client_id = self.register().json()["client_id"]
        self.client.force_login(self.user)
        response = self.client.post("/oauth/authorize/", {
            "client_id": client_id, "redirect_uri": CALLBACK, "response_type": "code",
            "scope": "sprintflow", "code_challenge": CHALLENGE, "code_challenge_method": "S256",
            "resource": RESOURCE, "state": "denied-state",
        })
        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlsplit(response["Location"]).query)
        self.assertEqual(query["error"], ["access_denied"])
        self.assertEqual(query["state"], ["denied-state"])
        self.assertFalse(get_grant_model().objects.exists())

    def test_account_revocation_is_user_scoped_and_revokes_refresh(self):
        client_id, tokens = self.issue_tokens()
        token = get_access_token_model().objects.get(token=tokens["access_token"])
        other = get_user_model().objects.create_user(email="other@example.com", password="safe-password")
        self.client.force_login(other)
        url = f"/oauth/authorized_tokens/{token.pk}/delete/"
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/oauth/authorized_tokens/").status_code, 200)
        self.assertEqual(self.client.post(url).status_code, 302)
        response = self.client.post("/oauth/token/", {
            "grant_type": "refresh_token", "client_id": client_id, "refresh_token": tokens["refresh_token"],
        })
        self.assertEqual(response.status_code, 400)


class MCPConfiguredOAuthTests(TestCase):
    """Use config.urls and the real provider settings, with no OAuth overrides."""

    def test_configured_discovery_and_browser_pkce_flow(self):
        self.assertEqual(settings.ROOT_URLCONF, "config.urls")
        browser = Client(enforce_csrf_checks=True)
        origin = settings.MCP_PUBLIC_URL
        resource = origin + "/mcp"
        discovery = browser.get("/.well-known/oauth-authorization-server")
        self.assertEqual(discovery.status_code, 200)
        metadata = discovery.json()
        self.assertEqual(metadata["issuer"], origin)
        self.assertEqual(metadata["code_challenge_methods_supported"], ["S256"])
        self.assertEqual(metadata["token_endpoint_auth_methods_supported"], ["none"])
        protected = browser.get("/.well-known/oauth-protected-resource/mcp")
        self.assertEqual(protected.status_code, 200)
        self.assertEqual(protected.json()["resource"], resource)
        self.assertEqual(protected.json()["authorization_servers"], [origin])
        registration_path = urlsplit(metadata["registration_endpoint"]).path
        registration = browser.post(registration_path, json.dumps({
            "client_name": "Configured connector", "redirect_uris": [CALLBACK],
            "grant_types": ["authorization_code", "refresh_token"], "token_endpoint_auth_method": "none",
        }), content_type="application/json")
        self.assertEqual(registration.status_code, 201, registration.content)
        self.assertNotIn("client_secret", registration.json())
        client_id = registration.json()["client_id"]
        user = get_user_model().objects.create_user(email="configured@example.com", password="safe-password")
        authorization_path = urlsplit(metadata["authorization_endpoint"]).path
        params = {"client_id": client_id, "redirect_uri": CALLBACK, "response_type": "code",
                  "scope": "sprintflow", "state": "browser-state", "code_challenge": CHALLENGE,
                  "code_challenge_method": "S256"}
        authorization_url = authorization_path + "?" + urlencode(params)
        response = browser.get(authorization_url)
        self.assertEqual(response.status_code, 302)
        login_location = response["Location"]
        self.assertEqual(urlsplit(login_location).path, settings.LOGIN_URL)
        self.assertEqual(browser.get(login_location).status_code, 200)
        response = browser.post("/oauth/login/", {
            "username": user.email, "password": "safe-password", "next": authorization_url,
            "csrfmiddlewaretoken": browser.cookies["csrftoken"].value,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], authorization_url)
        consent = browser.get(response["Location"])
        self.assertEqual(consent.status_code, 200)
        form = consent.context["form"]
        data = {field.name: field.value() or "" for field in form if field.is_hidden}
        data["allow"] = "Authorize"
        self.assertEqual(browser.post(authorization_path, data).status_code, 403)
        data["csrfmiddlewaretoken"] = browser.cookies["csrftoken"].value
        response = browser.post(authorization_path, data)
        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlsplit(response["Location"]).query)
        self.assertEqual(query["state"], ["browser-state"])
        response = browser.post(urlsplit(metadata["token_endpoint"]).path, {
            "grant_type": "authorization_code", "client_id": client_id,
            "code": query["code"][0], "redirect_uri": CALLBACK, "code_verifier": VERIFIER,
        })
        self.assertEqual(response.status_code, 200, response.content)
        token = get_access_token_model().objects.get(token=response.json()["access_token"])
        self.assertEqual(token.resource, [resource])
        self.assertEqual(token.scope, "sprintflow")
        self.assertEqual(token.user, user)
