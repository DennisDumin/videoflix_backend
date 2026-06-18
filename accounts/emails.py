"""Email helpers for account workflows."""
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_activation_email(user):
    """Send an activation email and return the generated token."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = build_frontend_url("activate.html", uid, token)
    send_mail(
        "Activate your Videoflix account",
        build_activation_text(activation_url),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=build_activation_html(activation_url),
    )
    return token


def send_password_reset_email(user):
    """Send a password reset email and return the generated token."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = build_frontend_url("confirm_password.html", uid, token)
    send_mail(
        "Reset your Videoflix password",
        build_password_reset_text(reset_url),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=build_password_reset_html(reset_url),
    )
    return token


def build_frontend_url(page, uid, token):
    """Build a frontend auth URL with uid and token parameters."""
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    return f"{frontend_url}/pages/auth/{page}?uid={uid}&token={token}"


def build_activation_text(activation_url):
    """Build the plain text activation email."""
    return (
        "Welcome to Videoflix.\n\n"
        f"Activate your account here: {activation_url}\n"
    )


def build_activation_html(activation_url):
    """Build the HTML activation email."""
    return (
        "<p>Welcome to Videoflix.</p>"
        f'<p><a href="{activation_url}">Activate your account</a></p>'
    )


def build_password_reset_text(reset_url):
    """Build the plain text password reset email."""
    return (
        "You requested a Videoflix password reset.\n\n"
        f"Set a new password here: {reset_url}\n"
    )


def build_password_reset_html(reset_url):
    """Build the HTML password reset email."""
    return (
        "<p>You requested a Videoflix password reset.</p>"
        f'<p><a href="{reset_url}">Set a new password</a></p>'
    )
