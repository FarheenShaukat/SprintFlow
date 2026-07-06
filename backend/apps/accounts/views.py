from django.db.utils import DatabaseError
from django.core.management import call_command
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EmailTokenObtainPairSerializer, RegisterSerializer, UserSerializer

_migration_attempted = False


def retry_after_migration(callback):
    global _migration_attempted
    try:
        return callback()
    except DatabaseError as exc:
        if _migration_attempted:
            raise exc
        _migration_attempted = True
        call_command("migrate", interactive=False, verbosity=0)
        return callback()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            return retry_after_migration(lambda: super(RegisterView, self).create(request, *args, **kwargs))
        except DatabaseError as exc:
            return Response(
                {"detail": f"Database is not ready. Check DATABASE_URL and run migrations. {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            return retry_after_migration(lambda: super(LoginView, self).post(request, *args, **kwargs))
        except DatabaseError as exc:
            return Response(
                {"detail": f"Database is not ready. Check DATABASE_URL and run migrations. {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            RefreshToken(refresh).blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)
