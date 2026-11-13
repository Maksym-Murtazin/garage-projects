from django.urls import path

from .views import MemberCreateView, MemberDetailView, MemberListView, MemberUpdateView

app_name = "members"

urlpatterns = [
    path("", MemberListView.as_view(), name="member-list"),
    path("create/", MemberCreateView.as_view(), name="member-create"),
    path("<int:pk>/", MemberDetailView.as_view(), name="member-detail"),
    path("<int:pk>/edit/", MemberUpdateView.as_view(), name="member-update"),
]
