"""Background tasks for video processing."""
from videos.models import Video
from videos.services import process_video_files


def process_video(video_id):
    """Start background processing for one video."""
    video = get_video(video_id)
    if video is None:
        return
    mark_video_as_processing(video)
    try:
        result = process_video_files(video)
        mark_video_as_ready(video, result)
    except Exception:
        mark_video_as_failed(video)
        raise


def get_video(video_id):
    """Return a video by id or None."""
    return Video.objects.filter(id=video_id).first()


def mark_video_as_processing(video):
    """Persist the processing status."""
    video.processing_status = Video.ProcessingStatus.PROCESSING
    video.save(update_fields=["processing_status", "updated_at"])


def mark_video_as_ready(video, result):
    """Persist processing results."""
    video.hls_480p_path = result["hls_480p_path"]
    video.hls_720p_path = result["hls_720p_path"]
    video.hls_1080p_path = result["hls_1080p_path"]
    video.processing_status = Video.ProcessingStatus.READY
    update_fields = get_ready_update_fields(video, result)
    video.save(update_fields=update_fields)


def get_ready_update_fields(video, result):
    """Return fields to update after successful processing."""
    update_fields = [
        "hls_480p_path", "hls_720p_path", "hls_1080p_path",
        "processing_status", "updated_at",
    ]
    if result["thumbnail_path"]:
        video.thumbnail.name = result["thumbnail_path"]
        update_fields.append("thumbnail")
    return update_fields


def mark_video_as_failed(video):
    """Persist a failed processing status."""
    video.processing_status = Video.ProcessingStatus.FAILED
    video.save(update_fields=["processing_status", "updated_at"])
