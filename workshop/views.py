from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
