from django.urls import path

from .views import MemberListView

app_name = "members"

urlpatterns = [
    path("", MemberListView.as_view(), name="member-list"),
]
