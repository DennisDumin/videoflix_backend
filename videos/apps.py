"""Videos app configuration."""
from django.apps import AppConfig


class VideosConfig(AppConfig):
    """Configure the videos app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "videos"

    def ready(self):
        """Load video signals."""
        import videos.signals  # noqa: F401
