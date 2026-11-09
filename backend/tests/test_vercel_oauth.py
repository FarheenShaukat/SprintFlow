from unittest.mock import patch
from urllib.parse import urlsplit

from django.test import TestCase


class VercelOAuthRoutingTests(TestCase):
    def test_login_works_with_and_without_trailing_slash(self):
        for path in ["/oauth/login", "/oauth/login/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_public_registration_and_token_posts_do_not_redirect(self):
        for suffix in ["", "/"]:
            registration = self.client.post("/oauth/register" + suffix, {
                "client_name": "Vercel route check", "redirect_uris": ["https://example.com/callback"],
                "token_endpoint_auth_method": "none", "grant_types": ["authorization_code", "refresh_token"],
            }, content_type="application/json")
            self.assertEqual(registration.status_code, 201, registration.content)
            token = self.client.post("/oauth/token" + suffix, {"grant_type": "authorization_code", "client_id": "unknown", "code": "unknown"})
            self.assertIn(token.status_code, [400, 401])
            revoked = self.client.post("/oauth/revoke_token" + suffix, {"client_id": "unknown", "token": "unknown"})
            self.assertNotIn(revoked.status_code, [301, 302, 307, 308])

    def test_discovery_advertises_vercel_canonical_endpoints(self):
        metadata = self.client.get("/.well-known/oauth-authorization-server").json()
        for name in ["authorization_endpoint", "token_endpoint", "registration_endpoint", "revocation_endpoint"]:
            self.assertFalse(urlsplit(metadata[name]).path.endswith("/"), name)

    def test_database_health_checks_oauth_migrations(self):
        response = self.client.get("/api/health/db")
        self.assertTrue(response.json()["oauth_ready"])
        with patch("config.urls.MigrationExecutor") as executor:
            executor.return_value.migration_plan.return_value = [(object(), False)]
            response = self.client.get("/api/health/db")
        self.assertFalse(response.json()["oauth_ready"])
