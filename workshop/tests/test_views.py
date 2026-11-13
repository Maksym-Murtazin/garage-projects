from django.contrib.auth import get_user_model
from django.test import Client, TestCase
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


class CarProjectDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.project = CarProject.objects.create(
            title="E30 restoration", manufacturer=manufacturer,
            model="320i", year=1989,
        )

    def test_login_required_and_missing_project_returns_404(self):
        url = reverse("workshop:project-detail", args=[self.project.pk])
        self.assertRedirects(
            self.client.get(url), reverse("login") + "?next=" + url,
        )
        self.client.force_login(self.member)
        self.assertEqual(
            self.client.get(reverse("workshop:project-detail", args=[0])).status_code,
            404,
        )

    def test_detail_displays_only_this_projects_team_and_tasks(self):
        self.client.force_login(self.member)
        url = reverse("workshop:project-detail", args=[self.project.pk])
        response = self.client.get(url)
        self.assertContains(response, "No description yet.")
        self.assertContains(response, "No members have joined this project yet.")
        self.assertContains(response, "No tasks have been added to this project yet.")

        self.project.members.add(self.member)
        category = TaskCategory.objects.create(name="Suspension")
        task = Task.objects.create(
            title="Replace bushings", project=self.project, category=category,
        )
        other_project = CarProject.objects.create(
            title="Track build", manufacturer=self.project.manufacturer,
            model="M3", year=2004,
        )
        outsider = get_user_model().objects.create_user(
            username="painter", employee_code="GRG00002",
        )
        other_project.members.add(outsider)
        Task.objects.create(title="Paint bodywork", project=other_project, category=category)

        response = self.client.get(url)
        self.assertQuerySetEqual(response.context["tasks"], [task])
        for text in ("E30 restoration", "320i", "GRG00001", "Replace bushings",
                     "Suspension", "Unassigned", "No due date"):
            self.assertContains(response, text)
        self.assertNotContains(response, "Paint bodywork")
        self.assertNotContains(response, "GRG00002")


class CarProjectEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        cls.manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.project = CarProject.objects.create(
            title="E30 restoration", manufacturer=cls.manufacturer,
            model="320i", year=1989,
        )
        cls.data = {
            "title": "Track build", "manufacturer": cls.manufacturer.pk,
            "model": "M3", "year": 2004, "description": "Suspension refresh",
            "status": CarProject.Status.IN_PROGRESS,
        }

    def test_anonymous_requests_cannot_create_or_edit(self):
        for url in (
            reverse("workshop:project-create"),
            reverse("workshop:project-update", args=[self.project.pk]),
        ):
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    response = method(url, self.data if method.__name__ == "post" else {})
                    self.assertRedirects(response, reverse("login") + "?next=" + url)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "E30 restoration")
        self.assertEqual(CarProject.objects.count(), 1)

    def test_member_can_create_and_edit_without_changing_team(self):
        self.client.force_login(self.member)
        create_url = reverse("workshop:project-create")
        self.assertEqual(self.client.get(create_url).status_code, 200)
        response = self.client.post(create_url, self.data)
        project = CarProject.objects.get(title="Track build")
        self.assertRedirects(response, project.get_absolute_url())
        project.members.add(self.member)
        update_url = reverse("workshop:project-update", args=[project.pk])
        response = self.client.get(update_url)
        self.assertContains(response, "Suspension refresh")
        response = self.client.post(update_url, {
            **self.data, "title": "Completed build", "status": "completed", "members": [],
        })
        self.assertRedirects(response, project.get_absolute_url())
        project.refresh_from_db()
        self.assertEqual(project.title, "Completed build")
        self.assertEqual(project.status, CarProject.Status.COMPLETED)
        self.assertQuerySetEqual(project.members.all(), [self.member])

    def test_invalid_data_is_not_saved(self):
        self.client.force_login(self.member)
        for url in (
            reverse("workshop:project-create"),
            reverse("workshop:project-update", args=[self.project.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.post(url, {**self.data, "year": 1800})
                self.assertEqual(response.status_code, 200)
                self.assertIn("year", response.context["form"].errors)
        self.project.refresh_from_db()
        self.assertEqual(self.project.year, 1989)
        self.assertEqual(self.project.title, "E30 restoration")
        self.assertEqual(CarProject.objects.count(), 1)


class CarProjectDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        cls.manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.project = CarProject.objects.create(
            title="E30 restoration", manufacturer=cls.manufacturer,
            model="320i", year=1989,
        )
        cls.project.members.add(cls.member)
        cls.category = TaskCategory.objects.create(name="Suspension")
        cls.task = Task.objects.create(
            title="Replace bushings", project=cls.project, category=cls.category,
        )

    def test_anonymous_visitor_cannot_delete_project(self):
        url = reverse("workshop:project-delete", args=[self.project.pk])
        for method in (self.client.get, self.client.post):
            with self.subTest(method=method.__name__):
                self.assertRedirects(method(url), reverse("login") + "?next=" + url)
        self.assertTrue(CarProject.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_deletion_requires_post_with_csrf_and_preserves_shared_records(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.member)
        url = reverse("workshop:project-delete", args=[self.project.pk])
        response = client.get(url)
        self.assertContains(response, "E30 restoration")
        self.assertContains(response, "all 1 of its tasks")
        self.assertContains(response, self.project.get_absolute_url())
        self.assertTrue(CarProject.objects.filter(pk=self.project.pk).exists())
        self.assertEqual(client.post(url).status_code, 403)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

        response = client.post(url, {
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertRedirects(response, reverse("workshop:project-list"))
        self.assertFalse(CarProject.objects.filter(pk=self.project.pk).exists())
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
        self.assertTrue(Manufacturer.objects.filter(pk=self.manufacturer.pk).exists())
        self.assertTrue(TaskCategory.objects.filter(pk=self.category.pk).exists())
        self.assertTrue(get_user_model().objects.filter(pk=self.member.pk).exists())


class ProjectMembershipTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        cls.colleague = get_user_model().objects.create_user(
            username="painter", employee_code="GRG00002",
        )
        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.project = CarProject.objects.create(
            title="Restoration", manufacturer=manufacturer, model="320i", year=1989,
        )
        cls.other_project = CarProject.objects.create(
            title="Track build", manufacturer=manufacturer, model="M3", year=2004,
        )
        cls.category = TaskCategory.objects.create(name="Suspension")

    def test_join_and_leave_change_only_current_members_project_assignments(self):
        self.client.force_login(self.member)
        self.project.members.add(self.colleague)
        self.other_project.members.add(self.member)
        join_url = reverse("workshop:project-join", args=[self.project.pk])
        leave_url = reverse("workshop:project-leave", args=[self.project.pk])
        self.assertContains(self.client.get(self.project.get_absolute_url()), "Join project")
        for _ in range(2):
            self.assertRedirects(
                self.client.post(join_url, {"member": self.colleague.pk}),
                self.project.get_absolute_url(),
            )
        self.assertCountEqual(self.project.members.all(), [self.member, self.colleague])
        self.assertContains(self.client.get(self.project.get_absolute_url()), "Leave project")
        for status in Task.Status.values:
            Task.objects.create(
                title=status, status=status, project=self.project,
                category=self.category, assignee=self.member,
            )
        colleague_task = Task.objects.create(
            title="Paint body", project=self.project,
            category=self.category, assignee=self.colleague,
        )
        other_task = Task.objects.create(
            title="Track suspension", project=self.other_project,
            category=self.category, assignee=self.member,
        )
        for _ in range(2):
            self.assertRedirects(self.client.post(leave_url), self.project.get_absolute_url())
        self.assertQuerySetEqual(self.project.members.all(), [self.colleague])
        self.assertCountEqual(
            self.project.tasks.filter(assignee=None).values_list("status", flat=True),
            Task.Status.values,
        )
        colleague_task.refresh_from_db()
        other_task.refresh_from_db()
        self.assertEqual(colleague_task.assignee, self.colleague)
        self.assertEqual(other_task.assignee, self.member)
        self.assertTrue(self.other_project.members.filter(pk=self.member.pk).exists())

    def test_membership_changes_require_login_post_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        for action in ("join", "leave"):
            url = reverse(f"workshop:project-{action}", args=[self.project.pk])
            self.assertRedirects(self.client.post(url), reverse("login") + "?next=" + url)
        client.force_login(self.member)
        response = client.get(self.project.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        token = client.cookies["csrftoken"].value
        for action in ("join", "leave"):
            url = reverse(f"workshop:project-{action}", args=[self.project.pk])
            self.assertEqual(client.get(url).status_code, 405)
            self.assertEqual(client.post(url).status_code, 403)
            self.assertEqual(client.post(
                reverse(f"workshop:project-{action}", args=[0]),
                {"csrfmiddlewaretoken": token},
            ).status_code, 404)
        self.assertFalse(self.project.members.exists())


class TaskListTests(TestCase):
    def test_list_requires_login(self):
        url = reverse("workshop:task-list")
        self.assertRedirects(self.client.get(url), reverse("login") + "?next=" + url)

    def test_search_filters_and_pagination_work_together(self):
        member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        self.client.force_login(member)
        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        project = CarProject.objects.create(
            title="Restoration", manufacturer=manufacturer, model="320i", year=1989,
        )
        project.members.add(member)
        category = TaskCategory.objects.create(name="Suspension")
        for number in range(11):
            Task.objects.create(
                title=f"Inspect & repair {number:02}", project=project,
                category=category, assignee=member, status="todo", priority="high",
            )
        for overrides in ({"status": "done"}, {"priority": "low"}):
            Task.objects.create(
                **{"title": "Inspect & repair excluded", "project": project,
                   "category": category, "status": "todo", "priority": "high",
                   **overrides},
            )
        other_project = CarProject.objects.create(
            title="Track build", manufacturer=manufacturer, model="M3", year=2004,
        )
        Task.objects.create(
            title="Inspect & repair other", project=other_project,
            category=category, priority="high",
        )
        url = reverse("workshop:task-list")
        for query, count in ((" MECHANIC ", 11), ("grg00001", 11), ("Restoration", 13)):
            with self.subTest(query=query):
                response = self.client.get(url, {"q": query})
                self.assertEqual(response.context["paginator"].count, count)
        params = {"q": "Inspect & repair", "status": "todo",
                  "priority": "high", "project": project.pk}
        response = self.client.get(url, params)
        self.assertEqual(response.context["paginator"].count, 11)
        self.assertContains(
            response,
            f'?q=Inspect+%26+repair&amp;status=todo&amp;priority=high&amp;project={project.pk}&amp;page=2',
        )
        response = self.client.get(url, {**params, "page": 2})
        self.assertEqual(
            [task.title for task in response.context["tasks"]], ["Inspect & repair 10"],
        )
        for field, value in (("project", "invalid"), ("status", "unknown"), ("priority", "unknown")):
            with self.subTest(field=field):
                response = self.client.get(url, {field: value})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["filter_form"].errors)
                self.assertEqual(response.context["paginator"].count, 0)


class TaskDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.project = CarProject.objects.create(
            title="Restoration", manufacturer=manufacturer, model="320i", year=1989,
        )
        cls.project.members.add(cls.member)
        category = TaskCategory.objects.create(name="Suspension")
        cls.task = Task.objects.create(
            title="Replace bushings", project=cls.project, category=category,
            assignee=cls.member, description="Check mounts.\nReplace worn bushings.",
            status="in_progress", priority="high", due_date="2027-03-15",
        )

    def test_login_required_and_missing_task_returns_404(self):
        url = self.task.get_absolute_url()
        self.assertRedirects(self.client.get(url), reverse("login") + "?next=" + url)
        self.client.force_login(self.member)
        self.assertEqual(
            self.client.get(reverse("workshop:task-detail", args=[0])).status_code, 404,
        )

    def test_details_links_and_optional_fields(self):
        self.client.force_login(self.member)
        response = self.client.get(self.task.get_absolute_url())
        for text in (
            "Replace bushings", "Check mounts.", "Replace worn bushings.",
            "Suspension", "GRG00001", "In progress", "High", "Mar 15, 2027",
            self.project.get_absolute_url(),
        ):
            self.assertContains(response, text)
        for url in (reverse("workshop:task-list"), self.project.get_absolute_url()):
            self.assertContains(self.client.get(url), self.task.get_absolute_url())
        self.task.description = ""
        self.task.assignee = None
        self.task.due_date = None
        self.task.save()
        response = self.client.get(self.task.get_absolute_url())
        for text in ("No description yet.", "Unassigned", "No due date"):
            self.assertContains(response, text)


class TaskEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        cls.outsider = get_user_model().objects.create_user(
            username="painter", employee_code="GRG00002",
        )
        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.project = CarProject.objects.create(
            title="Restoration", manufacturer=manufacturer, model="320i", year=1989,
        )
        cls.project.members.add(cls.member)
        category = TaskCategory.objects.create(name="Suspension")
        cls.task = Task.objects.create(
            title="Replace bushings", project=cls.project, category=category,
        )
        cls.data = {
            "title": "Inspect mounts", "description": "Check for wear",
            "category": category.pk, "assignee": cls.member.pk,
            "status": "todo", "priority": "high", "due_date": "2027-03-15",
        }

    def test_anonymous_requests_cannot_create_or_edit(self):
        for url in (
            reverse("workshop:task-create", args=[self.project.pk]),
            reverse("workshop:task-update", args=[self.task.pk]),
        ):
            self.assertRedirects(self.client.get(url), reverse("login") + "?next=" + url)
            self.assertRedirects(self.client.post(url, self.data), reverse("login") + "?next=" + url)
        self.assertEqual(Task.objects.count(), 1)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Replace bushings")

    def test_create_and_edit_keep_project_and_allow_unassigned_task(self):
        self.client.force_login(self.member)
        url = reverse("workshop:task-create", args=[self.project.pk])
        response = self.client.get(url)
        self.assertQuerySetEqual(response.context["form"].fields["assignee"].queryset, [self.member])
        response = self.client.post(url, {**self.data, "project": 0})
        task = Task.objects.get(title="Inspect mounts")
        self.assertRedirects(response, task.get_absolute_url())
        self.assertEqual(task.project, self.project)
        self.assertEqual(task.assignee, self.member)
        update_url = reverse("workshop:task-update", args=[task.pk])
        self.assertContains(self.client.get(update_url), 'value="2027-03-15"')
        response = self.client.post(update_url, {
            **self.data, "assignee": "", "due_date": "", "status": "done", "project": 0,
        })
        self.assertRedirects(response, task.get_absolute_url())
        task.refresh_from_db()
        self.assertIsNone(task.assignee)
        self.assertIsNone(task.due_date)
        self.assertEqual(task.status, Task.Status.DONE)
        self.assertEqual(task.project, self.project)

    def test_outsider_assignment_is_rejected_on_create_and_edit(self):
        self.client.force_login(self.member)
        for url in (
            reverse("workshop:task-create", args=[self.project.pk]),
            reverse("workshop:task-update", args=[self.task.pk]),
        ):
            response = self.client.post(url, {**self.data, "assignee": self.outsider.pk})
            self.assertEqual(response.status_code, 200)
            self.assertIn("assignee", response.context["form"].errors)
        self.assertEqual(Task.objects.count(), 1)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.assignee)
        self.assertEqual(self.task.title, "Replace bushings")


class TaskDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.project = CarProject.objects.create(
            title="Restoration", manufacturer=manufacturer, model="320i", year=1989,
        )
        cls.project.members.add(cls.member)
        cls.category = TaskCategory.objects.create(name="Suspension")
        cls.task = Task.objects.create(
            title="Replace bushings", project=cls.project,
            category=cls.category, assignee=cls.member,
        )
        cls.other_task = Task.objects.create(
            title="Inspect mounts", project=cls.project, category=cls.category,
        )

    def test_anonymous_visitor_cannot_delete_task(self):
        url = reverse("workshop:task-delete", args=[self.task.pk])
        for method in (self.client.get, self.client.post):
            self.assertRedirects(method(url), reverse("login") + "?next=" + url)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_confirmed_deletion_removes_only_selected_task(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.member)
        url = reverse("workshop:task-delete", args=[self.task.pk])
        response = client.get(url)
        self.assertContains(response, "Replace bushings")
        self.assertContains(response, self.task.get_absolute_url())
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        self.assertEqual(client.post(url).status_code, 403)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        response = client.post(url, {
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertRedirects(response, self.project.get_absolute_url())
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
        self.assertTrue(Task.objects.filter(pk=self.other_task.pk).exists())
        self.assertTrue(CarProject.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(TaskCategory.objects.filter(pk=self.category.pk).exists())
        self.assertTrue(self.project.members.filter(pk=self.member.pk).exists())
        self.assertEqual(client.get(url).status_code, 404)


class ManufacturerListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        cls.url = reverse("workshop:manufacturer-list")

    def test_login_search_and_empty_states(self):
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('login')}?next={self.url}",
        )
        self.client.force_login(self.member)
        self.assertContains(self.client.get(self.url), "No manufacturers yet.")
        bmw = Manufacturer.objects.create(name="BMW", country="Germany")
        Manufacturer.objects.create(name="Toyota", country="Japan")
        for query in (" bMw ", "germany"):
            with self.subTest(query=query):
                response = self.client.get(self.url, {"q": query})
                self.assertEqual(list(response.context["manufacturers"]), [bmw])
                self.assertEqual(response.context["query"], query.strip())
                self.assertContains(response, "Germany")
        self.assertContains(
            self.client.get(self.url, {"q": "missing"}),
            "No manufacturers match your search.",
        )

    def test_pagination_keeps_search_and_alphabetical_order(self):
        Manufacturer.objects.bulk_create([
            Manufacturer(name=f"Brand {index:02}", country="Trinidad & Tobago")
            for index in reversed(range(11))
        ])
        Manufacturer.objects.create(name="Other", country="Germany")
        self.client.force_login(self.member)
        response = self.client.get(self.url, {"q": "Trinidad & Tobago"})
        self.assertEqual(response.context["paginator"].count, 11)
        self.assertEqual(
            [manufacturer.name for manufacturer in response.context["manufacturers"]],
            [f"Brand {index:02}" for index in range(10)],
        )
        self.assertContains(response, 'href="?q=Trinidad+%26+Tobago&amp;page=2"')
        response = self.client.get(self.url, {"q": "Trinidad & Tobago", "page": 2})
        self.assertEqual(
            [manufacturer.name for manufacturer in response.context["manufacturers"]],
            ["Brand 10"],
        )


class ManufacturerFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        cls.manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.create_url = reverse("workshop:manufacturer-create")
        cls.update_url = reverse("workshop:manufacturer-update", args=[cls.manufacturer.pk])

    def test_login_required_and_create_and_edit_preserve_project_links(self):
        for url in (self.create_url, self.update_url):
            for method in (self.client.get, self.client.post):
                self.assertRedirects(method(url), f"{reverse('login')}?next={url}")
        self.client.force_login(self.member)
        self.assertContains(self.client.get(self.create_url), 'name="csrfmiddlewaretoken"')
        response = self.client.post(self.create_url, {"name": "Toyota", "country": "Japan"})
        self.assertRedirects(response, reverse("workshop:manufacturer-list"))
        self.assertTrue(Manufacturer.objects.filter(name="Toyota", country="Japan").exists())
        project = CarProject.objects.create(
            title="E30 restoration", manufacturer=self.manufacturer, model="E30", year=1990,
        )
        response = self.client.get(self.update_url)
        self.assertEqual(response.context["form"].initial["name"], "BMW")
        response = self.client.post(self.update_url, {"name": "BMW Group", "country": "Germany"})
        self.assertRedirects(response, reverse("workshop:manufacturer-list"))
        project.refresh_from_db()
        self.assertEqual(project.manufacturer_id, self.manufacturer.pk)
        self.assertEqual(project.manufacturer.name, "BMW Group")
        self.assertEqual(Manufacturer.objects.count(), 2)

    def test_required_fields_and_duplicate_names_are_rejected(self):
        other = Manufacturer.objects.create(name="Toyota", country="Japan")
        self.client.force_login(self.member)
        for url in (self.create_url, self.update_url):
            for data, field in (
                ({"name": " ", "country": "Germany"}, "name"),
                ({"name": "New brand", "country": " "}, "country"),
                ({"name": other.name, "country": "Germany"}, "name"),
            ):
                with self.subTest(url=url, field=field):
                    response = self.client.post(url, data)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(field, response.context["form"].errors)
                    self.assertEqual(Manufacturer.objects.count(), 2)
                    self.manufacturer.refresh_from_db()
                    self.assertEqual(self.manufacturer.name, "BMW")
        response = self.client.post(self.update_url, {"name": "BMW", "country": "Germany"})
        self.assertRedirects(response, reverse("workshop:manufacturer-list"))
