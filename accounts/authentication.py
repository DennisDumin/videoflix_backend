"""JWT authentication that reads access tokens from HttpOnly cookies."""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate via Authorization header or access_token cookie."""

    def authenticate(self, request):
        header = self.get_header(request)
        raw_token = self.get_raw_token(header) if header else self.get_cookie(request)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def get_cookie(self, request):
        """Return the configured access token cookie."""
        return request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
