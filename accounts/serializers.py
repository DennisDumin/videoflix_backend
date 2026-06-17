"""Serializers for account API endpoints."""
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


User = get_user_model()


class PublicUserSerializer(serializers.ModelSerializer):
    """Return public user fields."""

    class Meta:
        model = User
        fields = ("id", "email")


class RegisterSerializer(serializers.Serializer):
    """Validate and create inactive users."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirmed_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate registration payload."""
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError("Invalid registration data.")
        if User.objects.filter(email__iexact=attrs["email"]).exists():
            raise serializers.ValidationError("Invalid registration data.")
        validate_registration_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        """Create an inactive user account."""
        email = validated_data["email"].lower()
        password = validated_data["password"]
        return User.objects.create_user(email=email, password=password, is_active=False)


class LoginSerializer(serializers.Serializer):
    """Validate login credentials."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate active users only."""
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"].lower(),
            password=attrs["password"],
        )
        if not user or not user.is_active:
            raise serializers.ValidationError("Unable to log in with provided credentials.")
        attrs["user"] = user
        return attrs


def validate_registration_password(password):
    """Validate a password without leaking exact policy details."""
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise serializers.ValidationError("Invalid registration data.") from exc
