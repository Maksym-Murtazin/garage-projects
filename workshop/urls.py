from django.urls import path

from . import views

app_name = "workshop"

urlpatterns = [
    path("", views.index, name="index"),
    path("tasks/", views.TaskListView.as_view(), name="task-list"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task-update"),
    path("projects/<int:pk>/tasks/create/", views.TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path("projects/", views.CarProjectListView.as_view(), name="project-list"),
    path("projects/create/", views.CarProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/edit/", views.CarProjectUpdateView.as_view(), name="project-update"),
    path("projects/<int:pk>/delete/", views.CarProjectDeleteView.as_view(), name="project-delete"),
    path("projects/<int:pk>/join/", views.join_project, name="project-join"),
    path("projects/<int:pk>/leave/", views.leave_project, name="project-leave"),
    path("projects/<int:pk>/", views.CarProjectDetailView.as_view(), name="project-detail"),
]
