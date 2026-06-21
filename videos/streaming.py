"""Helpers for protected HLS file streaming."""
from pathlib import Path

from django.conf import settings
from django.http import Http404

from videos.models import Video


ALLOWED_RESOLUTIONS = {"480p", "720p", "1080p"}


def get_manifest_path(video_id, resolution):
    """Return the manifest path for a video and resolution."""
    video = get_video_or_404(video_id)
    validate_resolution(resolution)
    manifest_path = get_resolution_manifest(video, resolution)
    return ensure_media_file(manifest_path)


def get_segment_path(video_id, resolution, segment):
    """Return the segment path for a video and resolution."""
    validate_segment(segment)
    manifest_path = get_manifest_path(video_id, resolution)
    segment_path = manifest_path.parent / segment
    return ensure_media_file(segment_path)


def get_video_or_404(video_id):
    """Return a video or raise 404."""
    try:
        return Video.objects.get(id=video_id)
    except Video.DoesNotExist as exc:
        raise Http404("Video not found.") from exc


def validate_resolution(resolution):
    """Raise 404 for unsupported HLS resolutions."""
    if resolution not in ALLOWED_RESOLUTIONS:
        raise Http404("Resolution not found.")


def validate_segment(segment):
    """Allow only direct .ts segment filenames."""
    if "/" in segment or "\\" in segment or not segment.endswith(".ts"):
        raise Http404("Segment not found.")


def get_resolution_manifest(video, resolution):
    """Return the stored manifest path for a resolution."""
    path = getattr(video, f"hls_{resolution}_path", "")
    if not path:
        raise Http404("Manifest not found.")
    return Path(settings.MEDIA_ROOT) / path


def ensure_media_file(path):
    """Return a media file path or raise 404."""
    media_root = Path(settings.MEDIA_ROOT).resolve()
    resolved_path = path.resolve()
    if not is_inside_media_root(resolved_path, media_root):
        raise Http404("File not found.")
    if not resolved_path.is_file():
        raise Http404("File not found.")
    return resolved_path


def is_inside_media_root(path, media_root):
    """Return whether path is inside MEDIA_ROOT."""
    return media_root == path or media_root in path.parents
