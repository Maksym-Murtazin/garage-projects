from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import CarProject, Task


@login_required
def index(request):
    visits = request.session.get("num_visits", 0) + 1
    request.session["num_visits"] = visits
    context = {
        "project_count": CarProject.objects.count(),
        "active_project_count": CarProject.objects.filter(
            status=CarProject.Status.IN_PROGRESS,
        ).count(),
        "open_task_count": Task.objects.exclude(status=Task.Status.DONE).count(),
        "member_count": get_user_model().objects.filter(is_active=True).count(),
        "num_visits": visits,
    }
    return render(request, "workshop/index.html", context)


class CarProjectListView(LoginRequiredMixin, ListView):
    model = CarProject
    template_name = "workshop/carproject_list.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related("manufacturer")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(manufacturer__name__icontains=query)
                | Q(model__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class CarProjectDetailView(LoginRequiredMixin, DetailView):
    model = CarProject
    template_name = "workshop/carproject_detail.html"
    context_object_name = "project"
    queryset = CarProject.objects.select_related("manufacturer").prefetch_related("members")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tasks"] = self.object.tasks.select_related("category", "assignee")
        return context
