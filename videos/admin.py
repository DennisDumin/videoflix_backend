"""Admin configuration for videos."""
from django.contrib import admin, messages
from django.utils import timezone
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from videos.models import Video
from videos.queue import enqueue_process_video


class VideoResource(resources.ModelResource):
    """Import/export resource for video metadata."""

    class Meta:
        model = Video
        fields = (
            "id",
            "title",
            "description",
            "category",
            "processing_status",
            "processing_error",
            "created_at",
        )


@admin.register(Video)
class VideoAdmin(ImportExportModelAdmin):
    """Upload and manage videos through Django admin."""

    actions = ("reprocess_selected_videos",)
    resource_class = VideoResource
    list_display = ("id", "title", "category", "processing_status", "created_at")
    list_filter = ("category", "processing_status", "created_at")
    search_fields = ("title", "description", "category")
    readonly_fields = (
        "processing_status",
        "hls_480p_path",
        "hls_720p_path",
        "hls_1080p_path",
        "processing_error",
        "created_at",
        "updated_at",
    )

    @admin.action(description="Reprocess selected videos")
    def reprocess_selected_videos(self, request, queryset):
        """Reset selected videos and enqueue new processing jobs."""
        video_ids = list(queryset.values_list("id", flat=True))
        reset_videos_for_processing(queryset)
        for video_id in video_ids:
            enqueue_process_video(video_id)
        self.message_user(
            request,
            f"{len(video_ids)} video(s) queued for processing.",
            messages.SUCCESS,
        )


def reset_videos_for_processing(queryset):
    """Mark selected videos as pending before reprocessing."""
    queryset.update(
        processing_status=Video.ProcessingStatus.PENDING,
        hls_480p_path="",
        hls_720p_path="",
        hls_1080p_path="",
        processing_error="",
        updated_at=timezone.now(),
    )
