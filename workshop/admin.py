from django.contrib import admin

from .models import CarProject, Manufacturer, Task, TaskCategory


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    search_fields = ("name", "country")
    list_filter = ("country",)


@admin.register(CarProject)
class CarProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "manufacturer", "model", "year", "status")
    search_fields = ("title", "manufacturer__name", "model")
    list_filter = ("status", "manufacturer")
    list_select_related = ("manufacturer",)
    filter_horizontal = ("members",)


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title", "project", "category", "assignee", "status", "priority", "due_date",
    )
    search_fields = (
        "title", "project__title", "assignee__username", "assignee__employee_code",
    )
    list_filter = ("status", "priority", "category", "project")
    list_select_related = ("project", "category", "assignee")
    date_hierarchy = "due_date"
