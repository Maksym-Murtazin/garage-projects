from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView

from .forms import MemberCreationForm


class MemberListView(LoginRequiredMixin, ListView):
    model = get_user_model()
    template_name = "members/member_list.html"
    context_object_name = "members"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
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
        return context


class MemberDetailView(LoginRequiredMixin, DetailView):
    model = get_user_model()
    template_name = "members/member_detail.html"
    context_object_name = "member"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = self.object.car_projects.select_related("manufacturer")
        context["tasks"] = self.object.assigned_tasks.select_related("project")
        return context


class MemberCreateView(LoginRequiredMixin, CreateView):
    model = get_user_model()
    form_class = MemberCreationForm
    template_name = "members/member_form.html"

    def get_success_url(self):
        return reverse("members:member-detail", kwargs={"pk": self.object.pk})
