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


class MemberCreateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        cls.url = reverse("members:member-create")
        cls.data = {
            "username": "newbuilder", "first_name": "Alex", "last_name": "Smith",
            "employee_code": "GRG00002",
            "password1": "Workshop-River-739!", "password2": "Workshop-River-739!",
        }

    def test_creation_requires_login_and_csrf(self):
        from django.test import Client

        for method in (self.client.get, self.client.post):
            response = method(self.url)
            self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.member)
        self.assertContains(client.get(self.url), 'name="csrfmiddlewaretoken"')
        self.assertEqual(client.post(self.url, self.data).status_code, 403)
        self.assertEqual(get_user_model().objects.count(), 1)
        response = client.post(self.url, {
            **self.data, "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="newbuilder").exists())

    def test_creation_hashes_password_and_keeps_ordinary_permissions_and_session(self):
        self.client.force_login(self.member)
        response = self.client.post(self.url, {
            **self.data, "is_staff": "on", "is_superuser": "on", "is_active": "",
        })
        created = get_user_model().objects.get(username="newbuilder")
        self.assertRedirects(
            response, reverse("members:member-detail", args=[created.pk]),
        )
        self.assertEqual(created.get_full_name(), "Alex Smith")
        self.assertEqual(created.employee_code, "GRG00002")
        self.assertTrue(created.check_password(self.data["password1"]))
        self.assertTrue(created.is_active)
        self.assertFalse(created.is_staff)
        self.assertFalse(created.is_superuser)
        self.assertEqual(self.client.session["_auth_user_id"], str(self.member.pk))

    def test_invalid_account_data_is_not_saved(self):
        self.client.force_login(self.member)
        cases = [
            ({"employee_code": "ABC00002"}, "employee_code"),
            ({"employee_code": "GRG00001"}, "employee_code"),
            ({"username": "mechanic"}, "username"),
            ({"password2": "different-password"}, "password2"),
            ({"password1": "123", "password2": "123"}, "password2"),
        ]
        for changes, field in cases:
            with self.subTest(changes=changes):
                response = self.client.post(self.url, {**self.data, **changes})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(get_user_model().objects.count(), 1)


class MemberUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.viewer = get_user_model().objects.create_user(
            username="viewer", employee_code="GRG00001",
        )
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00002", password="Original-739!",
        )
        cls.url = reverse("members:member-update", args=[cls.member.pk])
        cls.data = {
            "username": "builder", "first_name": "Alex", "last_name": "Smith",
            "employee_code": "GRG00003",
        }

    def test_edit_requires_login_and_updates_only_profile_fields(self):
        for method in (self.client.get, self.client.post):
            self.assertRedirects(
                method(self.url),
                f"{reverse('login')}?next={self.url}",
            )
        self.client.force_login(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.context["form"].initial["username"], "mechanic")
        self.assertEqual(set(response.context["form"].fields), set(self.data))
        original_password = self.member.password
        response = self.client.post(self.url, {
            **self.data, "password": "replacement", "is_staff": "on",
            "is_superuser": "on", "is_active": "",
        })
        self.assertRedirects(
            response, reverse("members:member-detail", args=[self.member.pk]),
        )
        self.member.refresh_from_db()
        for field, value in self.data.items():
            self.assertEqual(getattr(self.member, field), value)
        self.assertEqual(self.member.password, original_password)
        self.assertFalse(self.member.is_staff)
        self.assertFalse(self.member.is_superuser)
        self.assertTrue(self.member.is_active)
        self.assertEqual(self.client.session["_auth_user_id"], str(self.viewer.pk))

    def test_edit_validates_code_and_uniqueness_without_rejecting_unchanged_values(self):
        self.client.force_login(self.viewer)
        for changes, field in (
            ({"employee_code": "invalid"}, "employee_code"),
            ({"employee_code": self.viewer.employee_code}, "employee_code"),
            ({"username": self.viewer.username}, "username"),
        ):
            with self.subTest(changes=changes):
                response = self.client.post(self.url, {**self.data, **changes})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.member.refresh_from_db()
                self.assertEqual(self.member.username, "mechanic")
                self.assertEqual(self.member.employee_code, "GRG00002")
        response = self.client.post(self.url, {
            **self.data, "username": "mechanic", "employee_code": "GRG00002",
        })
        self.assertRedirects(
            response, reverse("members:member-detail", args=[self.member.pk]),
        )
