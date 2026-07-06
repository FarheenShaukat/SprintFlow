from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "full_name", "is_staff", "created_at")
    ordering = ("email",)
    fieldsets = UserAdmin.fieldsets + (("SprintFlow", {"fields": ("full_name", "avatar_url")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("SprintFlow", {"fields": ("email", "full_name")}),)
