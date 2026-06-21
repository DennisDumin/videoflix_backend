"""Background tasks for video processing."""
from videos.models import Video


def process_video(video_id):
    """Start background processing for one video."""
    video = get_video(video_id)
    if video is None:
        return
    mark_video_as_processing(video)
    print(f"Video processing job started for video {video.id}.")


def get_video(video_id):
    """Return a video by id or None."""
    return Video.objects.filter(id=video_id).first()


def mark_video_as_processing(video):
    """Persist the processing status."""
    video.processing_status = Video.ProcessingStatus.PROCESSING
    video.save(update_fields=["processing_status", "updated_at"])
