from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from workshop.models import CarProject, Manufacturer, Task, TaskCategory


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001", password="test-password",
        )

    def test_anonymous_visitor_is_redirected_to_login(self):
        response = self.client.get(reverse("workshop:index"))
        self.assertRedirects(response, reverse("login") + "?next=/")
        self.assertNotIn("num_visits", self.client.session)

    def test_statistics_and_session_visits(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("workshop:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project_count"], 0)
        self.assertEqual(response.context["open_task_count"], 0)
        self.assertEqual(response.context["num_visits"], 1)

        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        category = TaskCategory.objects.create(name="Suspension")
        for status in CarProject.Status.values:
            project = CarProject.objects.create(
                title=status, manufacturer=manufacturer, model="320i",
                year=1989, status=status,
            )
        for status in Task.Status.values:
            Task.objects.create(
                title=status, project=project, category=category, status=status,
            )
        get_user_model().objects.create_user(
            username="inactive", employee_code="GRG00002", is_active=False,
        )
        response = self.client.get(reverse("workshop:index"))
        self.assertEqual(response.context["project_count"], 3)
        self.assertEqual(response.context["active_project_count"], 1)
        self.assertEqual(response.context["open_task_count"], 2)
        self.assertEqual(response.context["member_count"], 1)
        self.assertEqual(response.context["num_visits"], 2)
        self.assertEqual(self.client.session["num_visits"], 2)

    def test_member_can_sign_in_and_sign_out(self):
        response = self.client.post(reverse("login"), {
            "username": "mechanic", "password": "test-password",
        })
        self.assertRedirects(response, reverse("workshop:index"))
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("num_visits", self.client.session)
        self.assertRedirects(
            self.client.get(reverse("workshop:index")),
            reverse("login") + "?next=/",
        )


class CarProjectListTests(TestCase):
    def test_list_requires_login(self):
        response = self.client.get(reverse("workshop:project-list"))
        self.assertRedirects(response, reverse("login") + "?next=/projects/")

    def test_search_and_pagination_preserve_query(self):
        member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        self.client.force_login(member)
        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        for number in range(11):
            CarProject.objects.create(
                title=f"Road & track {number:02}", manufacturer=manufacturer,
                model="320i", year=1989,
            )
        CarProject.objects.create(
            title="Restoration", manufacturer=manufacturer, model="M3", year=2004,
        )
        url = reverse("workshop:project-list")
        for query, count in ((" bMw ", 12), ("320I", 11), ("missing", 0)):
            with self.subTest(query=query):
                response = self.client.get(url, {"q": query})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["paginator"].count, count)

        response = self.client.get(url, {"q": "Road & track"})
        self.assertEqual(len(response.context["projects"]), 10)
        self.assertContains(response, '?q=Road+%26+track&amp;page=2')
        response = self.client.get(url, {"q": "Road & track", "page": 2})
        self.assertEqual(response.context["paginator"].count, 11)
        self.assertEqual(
            [project.title for project in response.context["projects"]],
            ["Road & track 10"],
        )
