"""Queue helpers for video background jobs."""
import django_rq

from videos.tasks import process_video


def enqueue_process_video(video_id):
    """Push video processing into the default RQ queue."""
    queue = django_rq.get_queue("default")
    queue.enqueue(process_video, video_id)
