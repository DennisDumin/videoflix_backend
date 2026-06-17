"""Helpers for Videoflix JWT cookies."""
from django.conf import settings


def set_token_cookies(response, access_token, refresh_token=None):
    """Set HttpOnly JWT cookies on a response."""
    set_cookie(response, settings.JWT_ACCESS_COOKIE_NAME, access_token, "ACCESS")
    if refresh_token:
        set_cookie(response, settings.JWT_REFRESH_COOKIE_NAME, refresh_token, "REFRESH")


def set_cookie(response, name, token, token_type):
    """Set one JWT cookie using SIMPLE_JWT lifetime settings."""
    max_age = get_max_age(token_type)
    response.set_cookie(
        name,
        str(token),
        max_age=max_age,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path="/",
    )


def get_max_age(token_type):
    """Return cookie max age in seconds."""
    key = f"{token_type}_TOKEN_LIFETIME"
    return int(settings.SIMPLE_JWT[key].total_seconds())


def delete_token_cookies(response):
    """Delete JWT cookies from a response."""
    cookie_options = {
        "path": "/",
        "samesite": settings.JWT_COOKIE_SAMESITE,
    }
    response.delete_cookie(settings.JWT_ACCESS_COOKIE_NAME, **cookie_options)
    response.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME, **cookie_options)
