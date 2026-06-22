"""Signals for video processing."""
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from videos.models import Video
from videos.queue import enqueue_process_video


@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    """Enqueue processing after a video was created."""
    if not created:
        return
    transaction.on_commit(lambda: enqueue_process_video(instance.id))
