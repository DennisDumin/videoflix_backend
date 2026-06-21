"""Signals for video processing."""
import django_rq
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from videos.models import Video
from videos.tasks import process_video


@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    """Enqueue processing after a video was created."""
    if not created:
        return
    print("New object created")
    transaction.on_commit(lambda: enqueue_process_video(instance.id))


def enqueue_process_video(video_id):
    """Push video processing into the default RQ queue."""
    queue = django_rq.get_queue("default")
    queue.enqueue(process_video, video_id)
