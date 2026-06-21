"""Views for video API endpoints."""
from django.http import FileResponse
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from videos.models import Video
from videos.serializers import VideoListSerializer
from videos.streaming import get_manifest_path, get_segment_path


class VideoListView(ListAPIView):
    """Return video metadata for authenticated users."""

    serializer_class = VideoListSerializer

    def get_queryset(self):
        """Return videos newest first."""
        return Video.objects.order_by("-created_at")


class HLSManifestView(APIView):
    """Return a protected HLS manifest."""

    def get(self, request, movie_id, resolution):
        manifest_path = get_manifest_path(movie_id, resolution)
        return FileResponse(
            manifest_path.open("rb"),
            content_type="application/vnd.apple.mpegurl",
        )


class HLSSegmentView(APIView):
    """Return a protected HLS transport stream segment."""

    def get(self, request, movie_id, resolution, segment):
        segment_path = get_segment_path(movie_id, resolution, segment)
        return FileResponse(segment_path.open("rb"), content_type="video/MP2T")
