from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "avatar_url", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "password", "avatar_url"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        email = value.lower()
        existing = User.objects.filter(email=email).first()
        if existing and existing.has_usable_password():
            raise serializers.ValidationError("A user with this email already exists. Please sign in.")
        return email

    def create(self, validated_data):
        password = validated_data.pop("password")
        existing = User.objects.filter(email=validated_data["email"]).first()
        if existing and not existing.has_usable_password():
            existing.full_name = validated_data.get("full_name") or existing.full_name
            existing.avatar_url = validated_data.get("avatar_url", existing.avatar_url)
            existing.set_password(password)
            existing.save()
            return existing
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }
