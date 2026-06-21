"""Serializers for video API endpoints."""
from rest_framework import serializers

from videos.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """Serialize video metadata expected by the frontend."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "category",
        )

    def get_thumbnail_url(self, video):
        """Return an absolute thumbnail URL when available."""
        if not video.thumbnail:
            return None
        request = self.context.get("request")
        if request is None:
            return video.thumbnail.url
        return request.build_absolute_uri(video.thumbnail.url)
