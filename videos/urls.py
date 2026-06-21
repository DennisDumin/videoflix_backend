"""Video API routes."""
from django.urls import path

from videos.views import HLSManifestView, HLSSegmentView, VideoListView


urlpatterns = [
    path("video/", VideoListView.as_view(), name="video-list"),
    path(
        "video/<int:movie_id>/<str:resolution>/index.m3u8",
        HLSManifestView.as_view(),
        name="hls-manifest",
    ),
    path(
        "video/<int:movie_id>/<str:resolution>/<str:segment>",
        HLSSegmentView.as_view(),
        name="hls-segment",
    ),
    path(
        "video/<int:movie_id>/<str:resolution>/<str:segment>/",
        HLSSegmentView.as_view(),
        name="hls-segment-slash",
    ),
]
