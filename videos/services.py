"""Services for video file processing."""
import subprocess
from pathlib import Path

from django.conf import settings


HLS_VARIANTS = {
    "480p": 480,
    "720p": 720,
    "1080p": 1080,
}


def process_video_files(video):
    """Create HLS variants and a thumbnail for a video."""
    input_path = Path(video.original_file.path)
    ensure_input_exists(input_path)
    hls_paths = create_hls_variants(video.id, input_path)
    thumbnail_path = create_thumbnail(video, input_path)
    return {**hls_paths, "thumbnail_path": thumbnail_path}


def ensure_input_exists(input_path):
    """Raise an error when the uploaded file is missing."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")


def create_hls_variants(video_id, input_path):
    """Create all configured HLS variants."""
    return {
        field_name(resolution): create_hls_variant(video_id, input_path, resolution, height)
        for resolution, height in HLS_VARIANTS.items()
    }


def create_hls_variant(video_id, input_path, resolution, height):
    """Create one HLS playlist and its transport stream segments."""
    output_dir = get_hls_output_dir(video_id, resolution)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "index.m3u8"
    segment_pattern = output_dir / "segment_%03d.ts"
    run_command(build_hls_command(input_path, manifest_path, segment_pattern, height))
    return media_relative_path(manifest_path)


def build_hls_command(input_path, manifest_path, segment_pattern, height):
    """Build the ffmpeg command for one HLS variant."""
    return [
        "ffmpeg", "-y", "-i", str(input_path), "-vf", f"scale=-2:{height}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-force_key_frames", "expr:gte(t,n_forced*10)",
        "-start_number", "0", "-hls_time", "10", "-hls_list_size", "0",
        "-hls_playlist_type", "vod", "-hls_segment_filename", str(segment_pattern),
        "-f", "hls", str(manifest_path),
    ]


def create_thumbnail(video, input_path):
    """Create a thumbnail when no thumbnail was uploaded."""
    if video.thumbnail:
        return None
    thumbnail_path = Path(settings.MEDIA_ROOT) / "thumbnails" / f"{video.id}.jpg"
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    run_command(build_thumbnail_command(input_path, thumbnail_path))
    return media_relative_path(thumbnail_path)


def build_thumbnail_command(input_path, thumbnail_path):
    """Build the ffmpeg command for a thumbnail image."""
    return [
        "ffmpeg", "-y", "-ss", "00:00:01", "-i", str(input_path),
        "-frames:v", "1", "-q:v", "2", str(thumbnail_path),
    ]


def get_hls_output_dir(video_id, resolution):
    """Return the output directory for one video resolution."""
    return Path(settings.MEDIA_ROOT) / "videos" / str(video_id) / resolution


def media_relative_path(path):
    """Return a path relative to MEDIA_ROOT using URL separators."""
    return str(path.relative_to(settings.MEDIA_ROOT)).replace("\\", "/")


def field_name(resolution):
    """Return the model field name for a resolution."""
    return f"hls_{resolution}_path"


def run_command(command):
    """Run a command and raise when it fails."""
    subprocess.run(command, check=True, capture_output=True, text=True)
