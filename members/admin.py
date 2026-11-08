from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Member


@admin.register(Member)
class MemberAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("employee_code",)
    search_fields = UserAdmin.search_fields + ("employee_code",)
    fieldsets = UserAdmin.fieldsets + (
        ("Workshop", {"fields": ("employee_code",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Member details",
            {"fields": ("first_name", "last_name", "email", "employee_code")},
        ),
    )
