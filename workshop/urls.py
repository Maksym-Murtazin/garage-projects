from django.urls import path

from . import views

app_name = "workshop"

urlpatterns = [
    path("", views.index, name="index"),
    path("projects/", views.CarProjectListView.as_view(), name="project-list"),
    path("projects/<int:pk>/", views.CarProjectDetailView.as_view(), name="project-detail"),
]
