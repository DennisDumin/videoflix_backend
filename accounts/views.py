"""Views for account API endpoints."""
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.middleware.csrf import get_token
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.cookies import delete_token_cookies, set_token_cookies
from accounts.emails import send_activation_email, send_password_reset_email
from accounts.models import User
from accounts.serializers import (
    LoginSerializer,
    PasswordConfirmSerializer,
    PasswordResetSerializer,
    PublicUserSerializer,
    RegisterSerializer,
)


class RegisterView(APIView):
    """Create inactive users and send activation emails."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = send_activation_email(user)
        return Response(build_register_response(user, token), status=status.HTTP_201_CREATED)


class ActivateAccountView(APIView):
    """Activate a user account from uid and token."""

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        user = get_user_from_uid(uidb64)
        if not is_activation_valid(user, token):
            return Response({"message": "Activation failed."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"message": "Account successfully activated."})


class LoginView(APIView):
    """Authenticate users and set JWT cookies."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        response = Response(build_login_response(serializer.validated_data["user"]))
        set_login_cookies(response, serializer.validated_data["user"], request)
        return response


class LogoutView(APIView):
    """Blacklist refresh token and delete JWT cookies."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response(build_logout_response())
        refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=400)
        blacklist_refresh_token(refresh_token)
        delete_token_cookies(response)
        return response


class CookieTokenRefreshView(APIView):
    """Create a new access token from the refresh_token cookie."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=401)
        return refresh_access_token(refresh_token)


class PasswordResetView(APIView):
    """Send a password reset email without exposing account existence."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_active_user_by_email(serializer.validated_data["email"])
        if user:
            send_password_reset_email(user)
        return Response({"detail": "An email has been sent to reset your password."})


class PasswordConfirmView(APIView):
    """Set a new password when uid and token are valid."""

    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        user = get_user_from_uid(uidb64)
        if not is_user_token_valid(user, token):
            return Response({"detail": "Invalid reset link."}, status=400)
        serializer = PasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_new_password(user, serializer.validated_data["new_password"])
        return Response({"detail": "Your Password has been successfully reset."})


def build_register_response(user, token):
    """Build successful registration response data."""
    return {
        "user": PublicUserSerializer(user).data,
        "token": token,
    }


def get_user_from_uid(uidb64):
    """Resolve a user from a base64 encoded id."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def is_activation_valid(user, token):
    """Return whether an activation token is valid."""
    return is_user_token_valid(user, token)


def is_user_token_valid(user, token):
    """Return whether a default Django user token is valid."""
    return user is not None and default_token_generator.check_token(user, token)


def build_login_response(user):
    """Build successful login response data."""
    return {
        "detail": "Login successful",
        "user": {"id": user.id, "username": user.email},
    }


def set_login_cookies(response, user, request):
    """Set login cookies and ensure a CSRF cookie exists."""
    refresh = RefreshToken.for_user(user)
    set_token_cookies(response, refresh.access_token, refresh)
    get_token(request)


def build_logout_response():
    """Build successful logout response data."""
    return {
        "detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."
    }


def blacklist_refresh_token(refresh_token):
    """Blacklist refresh token when token blacklist is available."""
    try:
        RefreshToken(refresh_token).blacklist()
    except TokenError:
        pass


def refresh_access_token(refresh_token):
    """Refresh the access token and set a new access cookie."""
    try:
        refresh = RefreshToken(refresh_token)
    except TokenError:
        return Response({"detail": "Invalid refresh token."}, status=401)
    response = Response({"detail": "Token refreshed", "access": str(refresh.access_token)})
    set_token_cookies(response, refresh.access_token)
    return response


def get_active_user_by_email(email):
    """Return the active user for an email address if one exists."""
    return User.objects.filter(email__iexact=email, is_active=True).first()


def set_new_password(user, password):
    """Persist a new user password."""
    user.set_password(password)
    user.save(update_fields=["password"])
