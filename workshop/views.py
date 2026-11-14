from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.decorators.http import require_POST

from .forms import CarProjectForm, ManufacturerForm, TaskCategoryForm, TaskFilterForm, TaskForm
from .models import CarProject, Manufacturer, Task, TaskCategory


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


class TaskCategoryListView(LoginRequiredMixin, ListView):
    model = TaskCategory
    template_name = "workshop/taskcategory_list.html"
    context_object_name = "categories"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class TaskCategoryCreateView(LoginRequiredMixin, CreateView):
    model = TaskCategory
    form_class = TaskCategoryForm
    template_name = "workshop/taskcategory_form.html"
    success_url = reverse_lazy("workshop:category-list")


class TaskCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = TaskCategory
    form_class = TaskCategoryForm
    template_name = "workshop/taskcategory_form.html"
    success_url = reverse_lazy("workshop:category-list")


class TaskCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = TaskCategory
    template_name = "workshop/taskcategory_confirm_delete.html"
    context_object_name = "category"
    success_url = reverse_lazy("workshop:category-list")
    http_method_names = ["get", "post", "head", "options"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tasks"] = self.object.tasks.select_related("project")
        return context

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            return self.render_to_response(self.get_context_data(form=form), status=409)


class ManufacturerListView(LoginRequiredMixin, ListView):
    model = Manufacturer
    template_name = "workshop/manufacturer_list.html"
    context_object_name = "manufacturers"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(country__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class ManufacturerCreateView(LoginRequiredMixin, CreateView):
    model = Manufacturer
    form_class = ManufacturerForm
    template_name = "workshop/manufacturer_form.html"
    success_url = reverse_lazy("workshop:manufacturer-list")


class ManufacturerUpdateView(LoginRequiredMixin, UpdateView):
    model = Manufacturer
    form_class = ManufacturerForm
    template_name = "workshop/manufacturer_form.html"
    success_url = reverse_lazy("workshop:manufacturer-list")


class ManufacturerDeleteView(LoginRequiredMixin, DeleteView):
    model = Manufacturer
    template_name = "workshop/manufacturer_confirm_delete.html"
    context_object_name = "manufacturer"
    success_url = reverse_lazy("workshop:manufacturer-list")
    http_method_names = ["get", "post", "head", "options"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = self.object.car_projects.all()
        return context

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            return self.render_to_response(self.get_context_data(form=form), status=409)


class CarProjectListView(LoginRequiredMixin, ListView):
    model = CarProject
    template_name = "workshop/carproject_list.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related("manufacturer").annotate(
            task_count=Count("tasks"),
            completed_task_count=Count("tasks", filter=Q(tasks__status=Task.Status.DONE)),
        ).order_by("title", "pk")
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
    queryset = CarProject.objects.select_related("manufacturer").prefetch_related("members").annotate(
        task_count=Count("tasks"),
        completed_task_count=Count("tasks", filter=Q(tasks__status=Task.Status.DONE)),
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tasks"] = self.object.tasks.select_related("category", "assignee")
        context["is_project_member"] = self.request.user in self.object.members.all()
        return context


class CarProjectCreateView(LoginRequiredMixin, CreateView):
    model = CarProject
    form_class = CarProjectForm
    template_name = "workshop/carproject_form.html"


class CarProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = CarProject
    form_class = CarProjectForm
    template_name = "workshop/carproject_form.html"


class CarProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = CarProject
    template_name = "workshop/carproject_confirm_delete.html"
    context_object_name = "project"
    success_url = reverse_lazy("workshop:project-list")
    http_method_names = ["get", "post", "head", "options"]


@login_required
@require_POST
def join_project(request, pk):
    project = get_object_or_404(CarProject, pk=pk)
    project.members.add(request.user)
    return redirect(project)


@login_required
@require_POST
def leave_project(request, pk):
    project = get_object_or_404(CarProject, pk=pk)
    with transaction.atomic():
        project.tasks.filter(assignee=request.user).update(assignee=None)
        project.members.remove(request.user)
    return redirect(project)


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "workshop/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related("project", "category", "assignee")
        self.filter_form = TaskFilterForm(self.request.GET)
        if not self.filter_form.is_valid():
            return queryset.none()
        filters = self.filter_form.cleaned_data
        if filters["q"]:
            query = filters["q"]
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(project__title__icontains=query)
                | Q(assignee__username__icontains=query)
                | Q(assignee__employee_code__icontains=query)
            )
        for field in ("status", "priority", "project"):
            if filters[field]:
                queryset = queryset.filter(**{field: filters[field]})
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "workshop/task_detail.html"
    context_object_name = "task"
    queryset = Task.objects.select_related("project", "category", "assignee")


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "workshop/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.project = get_object_or_404(CarProject, pk=self.kwargs["pk"])
        kwargs["project"] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "workshop/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.object.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        return context


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = "workshop/task_confirm_delete.html"
    context_object_name = "task"
    queryset = Task.objects.select_related("project")
    http_method_names = ["get", "post", "head", "options"]

    def get_success_url(self):
        return self.object.project.get_absolute_url()
