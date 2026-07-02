"""Email helpers for account workflows."""
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_activation_email(user):
    """Send an activation email and return the generated token."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = build_frontend_url("activate.html", uid, token)
    html_message = build_activation_html(user.email, activation_url)
    text_message = build_activation_text(activation_url)
    send_account_email(
        user.email, "Activate your Videoflix account", text_message, html_message
    )
    return token


def send_password_reset_email(user):
    """Send a password reset email and return the generated token."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = build_frontend_url("confirm_password.html", uid, token)
    html_message = build_password_reset_html(reset_url)
    text_message = build_password_reset_text(reset_url)
    send_account_email(
        user.email, "Reset your Videoflix password", text_message, html_message
    )
    return token


def send_account_email(recipient, subject, text_message, html_message):
    """Send one account workflow email."""
    send_mail(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        html_message=html_message,
    )


def build_frontend_url(page, uid, token):
    """Build a frontend auth URL with uid and token parameters."""
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    return f"{frontend_url}/pages/auth/{page}?uid={uid}&token={token}"


def build_activation_html(user_email, activation_url):
    """Build the HTML activation email."""
    return render_to_string(
        "accounts/emails/activation_email.html",
        {"activation_url": activation_url, "user_email": user_email},
    )


def build_activation_text(activation_url):
    """Build the plain text activation email."""
    return (
        "Welcome to Videoflix.\n\n"
        f"Activate your account here: {activation_url}\n"
    )


def build_password_reset_html(reset_url):
    """Build the HTML password reset email."""
    return render_to_string(
        "accounts/emails/password_reset_email.html",
        {"reset_url": reset_url},
    )


def build_password_reset_text(reset_url):
    """Build the plain text password reset email."""
    return (
        "You requested a Videoflix password reset.\n\n"
        f"Reset password here: {reset_url}\n"
    )
