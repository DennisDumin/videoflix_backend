"""Admin configuration for account models."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Manage email-based users in Django admin."""

    list_display = ("id", "email", "username", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("email",)
    search_fields = ("email", "username")
