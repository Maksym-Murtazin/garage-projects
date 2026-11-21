from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from config.audit import AuditedDeletionMixin
from config.view_mixins import UniqueConflictFormMixin

from .forms import MemberCreationForm, MemberStatusForm, MemberUpdateForm


def can_edit_member(actor, member):
    return (
        not member.is_staff
        and not member.is_superuser
        and (actor.pk == member.pk or actor.is_staff)
    )


class MemberListView(LoginRequiredMixin, ListView):
    model = get_user_model()
    template_name = "members/member_list.html"
    context_object_name = "members"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.status_form = MemberStatusForm(self.request.GET)
        if not self.status_form.is_valid():
            return queryset.none()
        status = self.status_form.cleaned_data["status"]
        if status:
            queryset = queryset.filter(is_active=status == "active")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(employee_code__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["status_form"] = self.status_form
        return context


class MemberDetailView(LoginRequiredMixin, DetailView):
    model = get_user_model()
    template_name = "members/member_detail.html"
    context_object_name = "member"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_edit_member"] = can_edit_member(self.request.user, self.object)
        context["projects"] = self.object.car_projects.select_related("manufacturer")
        context["tasks"] = self.object.assigned_tasks.select_related("project")
        return context


class MemberCreateView(LoginRequiredMixin, UniqueConflictFormMixin, CreateView):
    model = get_user_model()
    form_class = MemberCreationForm
    template_name = "members/member_form.html"

    def get_success_url(self):
        return reverse("members:member-detail", kwargs={"pk": self.object.pk})


class MemberUpdateView(LoginRequiredMixin, UniqueConflictFormMixin, UpdateView):
    model = get_user_model()
    form_class = MemberUpdateForm
    template_name = "members/member_form.html"

    def get_object(self, queryset=None):
        member = super().get_object(queryset)
        if not can_edit_member(self.request.user, member):
            raise Http404
        return member

    def get_success_url(self):
        return reverse("members:member-detail", kwargs={"pk": self.object.pk})


class MemberDeleteView(LoginRequiredMixin, AuditedDeletionMixin, DeleteView):
    model = get_user_model()
    template_name = "members/member_confirm_delete.html"
    context_object_name = "member"
    success_url = reverse_lazy("members:member-list")
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return super().get_queryset().filter(
            is_staff=False, is_superuser=False,
        ).exclude(pk=self.request.user.pk)

    def deletion_message(self):
        projects = list(self.object.car_projects.values_list("pk", flat=True))
        tasks = list(self.object.assigned_tasks.values_list("pk", flat=True))
        return f"Deleted member. Removed from projects {projects}. Unassigned tasks {tasks}."
