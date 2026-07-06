from django.core.exceptions import ImproperlyConfigured
from django.db.utils import DatabaseError
from django.http import JsonResponse


class ApiDatabaseErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except (DatabaseError, ImproperlyConfigured) as exc:
            if request.path.startswith("/api/"):
                return JsonResponse(
                    {
                        "detail": (
                            "Database is not ready. Confirm DATABASE_URL points to Supabase "
                            f"and migrations have run. {exc}"
                        )
                    },
                    status=503,
                )
            raise
