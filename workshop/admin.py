from django.contrib import admin

from .models import CarProject, Manufacturer


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
