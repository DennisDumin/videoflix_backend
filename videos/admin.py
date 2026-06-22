"""Admin configuration for videos."""
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from videos.models import Video


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
            "created_at",
        )


@admin.register(Video)
class VideoAdmin(ImportExportModelAdmin):
    """Upload and manage videos through Django admin."""

    resource_class = VideoResource
    list_display = ("id", "title", "category", "processing_status", "created_at")
    list_filter = ("category", "processing_status", "created_at")
    search_fields = ("title", "description", "category")
    readonly_fields = (
        "processing_status",
        "hls_480p_path",
        "hls_720p_path",
        "hls_1080p_path",
        "created_at",
        "updated_at",
    )
