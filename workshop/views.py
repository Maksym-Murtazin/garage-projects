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

from config.audit import AuditedDeletionMixin, record_action
from config.view_mixins import UniqueConflictFormMixin

from .forms import (
    CarProjectForm, ManufacturerForm, ProjectStatusForm, ProjectTeamForm,
    TaskCategoryForm, TaskFilterForm, TaskForm,
)
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


class TaskCategoryCreateView(LoginRequiredMixin, UniqueConflictFormMixin, CreateView):
    model = TaskCategory
    form_class = TaskCategoryForm
    template_name = "workshop/taskcategory_form.html"
    success_url = reverse_lazy("workshop:category-list")


class TaskCategoryUpdateView(LoginRequiredMixin, UniqueConflictFormMixin, UpdateView):
    model = TaskCategory
    form_class = TaskCategoryForm
    template_name = "workshop/taskcategory_form.html"
    success_url = reverse_lazy("workshop:category-list")


class TaskCategoryDeleteView(LoginRequiredMixin, AuditedDeletionMixin, DeleteView):
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


class ManufacturerCreateView(LoginRequiredMixin, UniqueConflictFormMixin, CreateView):
    model = Manufacturer
    form_class = ManufacturerForm
    template_name = "workshop/manufacturer_form.html"
    success_url = reverse_lazy("workshop:manufacturer-list")


class ManufacturerUpdateView(LoginRequiredMixin, UniqueConflictFormMixin, UpdateView):
    model = Manufacturer
    form_class = ManufacturerForm
    template_name = "workshop/manufacturer_form.html"
    success_url = reverse_lazy("workshop:manufacturer-list")


class ManufacturerDeleteView(LoginRequiredMixin, AuditedDeletionMixin, DeleteView):
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
        self.status_form = ProjectStatusForm(self.request.GET)
        if not self.status_form.is_valid():
            return queryset.none()
        if self.status_form.cleaned_data["status"]:
            queryset = queryset.filter(status=self.status_form.cleaned_data["status"])
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
        context["status_form"] = self.status_form
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


class CarProjectDeleteView(LoginRequiredMixin, AuditedDeletionMixin, DeleteView):
    model = CarProject
    template_name = "workshop/carproject_confirm_delete.html"
    context_object_name = "project"
    success_url = reverse_lazy("workshop:project-list")
    http_method_names = ["get", "post", "head", "options"]

    def deletion_message(self):
        members = list(self.object.members.values_list("pk", flat=True))
        assignments = list(self.object.tasks.values_list("pk", "assignee_id"))
        return f"Deleted project. Team {members}. Deleted tasks (ID, assignee ID): {assignments}."


class ProjectTeamUpdateView(LoginRequiredMixin, UpdateView):
    model = CarProject
    form_class = ProjectTeamForm
    template_name = "workshop/project_team_form.html"
    context_object_name = "project"
    http_method_names = ["get", "post", "head", "options"]

    def form_valid(self, form):
        with transaction.atomic():
            project = CarProject.objects.select_for_update().get(pk=self.object.pk)
            before = set(project.members.values_list("pk", flat=True))
            after = {member.pk for member in form.cleaned_data["members"]}
            removed = sorted(before - after)
            added = sorted(after - before)
            tasks = project.tasks.filter(assignee_id__in=removed)
            assignments = list(tasks.values_list("pk", "assignee_id"))
            tasks.update(assignee=None)
            response = super().form_valid(form)
            if added or removed:
                record_action(
                    self.request.user, project,
                    f"Team added {added}, removed {removed}. "
                    f"Cleared assignments (task ID, assignee ID): {assignments}.",
                )
            return response


@login_required
@require_POST
@transaction.atomic
def join_project(request, pk):
    project = get_object_or_404(CarProject.objects.select_for_update(), pk=pk)
    if not project.members.filter(pk=request.user.pk).exists():
        project.members.add(request.user)
        record_action(request.user, project, "Joined the project team.")
    return redirect(project)


@login_required
@require_POST
@transaction.atomic
def leave_project(request, pk):
    project = get_object_or_404(CarProject.objects.select_for_update(), pk=pk)
    tasks = project.tasks.filter(assignee=request.user)
    task_ids = list(tasks.values_list("pk", flat=True))
    was_member = project.members.filter(pk=request.user.pk).exists()
    tasks.update(assignee=None)
    project.members.remove(request.user)
    if was_member or task_ids:
        record_action(request.user, project, f"Left the project team. Unassigned tasks {task_ids}.")
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
        if filters["status"] == "open":
            queryset = queryset.exclude(status=Task.Status.DONE)
        elif filters["status"]:
            queryset = queryset.filter(status=filters["status"])
        for field in ("priority", "project"):
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


class TaskDeleteView(LoginRequiredMixin, AuditedDeletionMixin, DeleteView):
    model = Task
    template_name = "workshop/task_confirm_delete.html"
    context_object_name = "task"
    queryset = Task.objects.select_related("project")
    http_method_names = ["get", "post", "head", "options"]

    def get_success_url(self):
        return self.object.project.get_absolute_url()
