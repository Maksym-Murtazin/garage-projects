from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class MemberListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
            first_name="Alex", last_name="Smith",
        )
        cls.url = reverse("members:member-list")

    def test_member_list_requires_login_and_searches_each_field(self):
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('login')}?next={self.url}"
        )
        self.client.force_login(self.member)
        get_user_model().objects.create_user(
            username="other", employee_code="GRG00002", is_active=False,
        )
        for query in (" MECHANIC ", "alex", "smith", "grg00001"):
            with self.subTest(query=query):
                response = self.client.get(self.url, {"q": query})
                self.assertEqual(list(response.context["members"]), [self.member])
                self.assertEqual(response.context["query"], query.strip())
        response = self.client.get(self.url)
        self.assertContains(response, "Inactive")
        response = self.client.get(self.url, {"q": "missing"})
        self.assertContains(response, "No members match your search.")

    def test_pagination_preserves_search_and_excludes_unmatched_members(self):
        get_user_model().objects.bulk_create([
            get_user_model()(
                username=f"builder{index:02}", employee_code=f"GRG{index + 10:05}",
                first_name="Body & Paint",
            )
            for index in range(11)
        ])
        self.client.force_login(self.member)
        response = self.client.get(self.url, {"q": "Body & Paint"})
        self.assertEqual(response.context["paginator"].count, 11)
        self.assertEqual(len(response.context["members"]), 10)
        self.assertContains(response, 'href="?q=Body+%26+Paint&amp;page=2"')
        response = self.client.get(self.url, {"q": "Body & Paint", "page": 2})
        self.assertEqual(
            [member.username for member in response.context["members"]],
            ["builder10"],
        )


class MemberDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.viewer = get_user_model().objects.create_user(
            username="viewer", employee_code="GRG00001",
        )
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00002",
            first_name="Alex", last_name="Smith",
        )
        cls.url = reverse("members:member-detail", args=[cls.member.pk])

    def test_access_and_empty_profile(self):
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('login')}?next={self.url}"
        )
        self.client.force_login(self.viewer)
        response = self.client.get(self.url)
        self.assertContains(response, "Alex Smith")
        self.assertContains(response, "GRG00002")
        self.assertContains(response, "This member has not joined any projects yet.")
        self.assertContains(response, "No tasks are assigned to this member.")
        self.assertEqual(response.context["user"], self.viewer)
        self.assertContains(
            self.client.get(reverse("members:member-list")),
            f'href="{self.url}"',
        )

    def test_profile_shows_only_members_projects_and_assigned_tasks(self):
        from workshop.models import CarProject, Manufacturer, Task, TaskCategory

        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        project = CarProject.objects.create(
            title="E30 restoration", manufacturer=manufacturer, model="E30", year=1990,
        )
        project.members.add(self.member, self.viewer)
        CarProject.objects.create(
            title="Other build", manufacturer=manufacturer, model="E36", year=1995,
        ).members.add(self.viewer)
        category = TaskCategory.objects.create(name="Bodywork")
        task = Task.objects.create(
            title="Repair panels", project=project, category=category,
            assignee=self.member, status=Task.Status.DONE,
        )
        Task.objects.create(
            title="Paint doors", project=project, category=category,
            assignee=self.viewer,
        )
        Task.objects.create(title="Inspect roof", project=project, category=category)
        self.client.force_login(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["projects"]), [project])
        self.assertEqual(list(response.context["tasks"]), [task])
        self.assertContains(response, f'href="{project.get_absolute_url()}"')
        self.assertContains(response, f'href="{task.get_absolute_url()}"')
        self.assertContains(response, "Done")
        self.assertNotContains(response, "Paint doors")
        self.assertNotContains(response, "Other build")
        for url in (project.get_absolute_url(), task.get_absolute_url()):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), f'href="{self.url}"')
