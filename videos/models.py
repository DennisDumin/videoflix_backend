"""Video models for Videoflix."""
from django.db import models


def video_upload_path(instance, filename):
    """Return the upload path for original video files."""
    return f"videos/originals/{filename}"


def thumbnail_upload_path(instance, filename):
    """Return the upload path for thumbnails."""
    return f"thumbnails/{filename}"


class Video(models.Model):
    """Video metadata and processing paths."""

    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    original_file = models.FileField(upload_to=video_upload_path)
    thumbnail = models.ImageField(upload_to=thumbnail_upload_path, blank=True, null=True)
    processing_status = models.CharField(
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        max_length=20,
    )
    hls_480p_path = models.CharField(blank=True, max_length=500)
    hls_720p_path = models.CharField(blank=True, max_length=500)
    hls_1080p_path = models.CharField(blank=True, max_length=500)
    processing_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title
