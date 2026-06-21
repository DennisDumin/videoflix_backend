"""Views for video API endpoints."""
from rest_framework.generics import ListAPIView

from videos.models import Video
from videos.serializers import VideoListSerializer


class VideoListView(ListAPIView):
    """Return video metadata for authenticated users."""

    serializer_class = VideoListSerializer

    def get_queryset(self):
        """Return videos newest first."""
        return Video.objects.order_by("-created_at")
