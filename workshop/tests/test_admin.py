from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from workshop.models import CarProject, Manufacturer


class ManufacturerAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="admin", employee_code="GRG00001", password="test-password"
        )
        cls.bmw = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.audi = Manufacturer.objects.create(name="Audi", country="Germany")
        cls.toyota = Manufacturer.objects.create(name="Toyota", country="Japan")

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse("admin:workshop_manufacturer_changelist")

    def test_list_displays_name_and_country(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        change_url = reverse(
            "admin:workshop_manufacturer_change", args=[self.bmw.pk]
        )
        self.assertContains(
            response,
            f'<th class="field-name"><a href="{change_url}">BMW</a></th>',
            html=True,
        )
        self.assertContains(
            response, '<td class="field-country">Germany</td>', html=True
        )

    def test_search_by_name_and_country(self):
        for query, expected in (
            ("bMw", [self.bmw]),
            ("jap", [self.toyota]),
            ("missing", []),
        ):
            with self.subTest(query=query):
                response = self.client.get(self.url, {"q": query})
                self.assertEqual(list(response.context["cl"].queryset), expected)

    def test_country_filter_combines_with_search(self):
        response = self.client.get(self.url, {"country": "Germany"})
        self.assertEqual(
            list(response.context["cl"].queryset), [self.audi, self.bmw]
        )
        response = self.client.get(
            self.url, {"country": "Germany", "q": "Audi"}
        )
        self.assertEqual(list(response.context["cl"].queryset), [self.audi])


class CarProjectAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="admin", employee_code="GRG00001", password="test-password"
        )
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00002"
        )
        cls.bmw = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.toyota = Manufacturer.objects.create(name="Toyota", country="Japan")
        cls.restoration = CarProject.objects.create(
            title="E30 restoration", manufacturer=cls.bmw, model="320i", year=1989,
        )
        cls.track = CarProject.objects.create(
            title="Track build", manufacturer=cls.toyota, model="Supra", year=1995,
            status=CarProject.Status.IN_PROGRESS,
        )

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse("admin:workshop_carproject_changelist")

    def test_list_displays_vehicle_details_and_status(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for field, value in (
            ("manufacturer nowrap", "BMW"), ("model", "320i"),
            ("year", "1989"), ("status", "Planned"),
        ):
            with self.subTest(field=field):
                self.assertContains(
                    response, f'<td class="field-{field}">{value}</td>', html=True
                )

    def test_search_by_title_manufacturer_and_model(self):
        for query, expected in (
            ("restoration", [self.restoration]),
            ("bMw", [self.restoration]),
            ("supra", [self.track]),
            ("missing", []),
        ):
            with self.subTest(query=query):
                response = self.client.get(self.url, {"q": query})
                self.assertEqual(list(response.context["cl"].queryset), expected)

    def test_filters_combine_with_search(self):
        for params, expected in (
            ({"status__exact": "planned"}, [self.restoration]),
            ({"manufacturer__id__exact": self.toyota.pk}, [self.track]),
            ({"status__exact": "in_progress",
              "manufacturer__id__exact": self.toyota.pk, "q": "supra"}, [self.track]),
            ({"status__exact": "planned",
              "manufacturer__id__exact": self.toyota.pk}, []),
        ):
            with self.subTest(params=params):
                response = self.client.get(self.url, params)
                self.assertEqual(list(response.context["cl"].queryset), expected)

    def test_add_project_with_members(self):
        response = self.client.post(reverse("admin:workshop_carproject_add"), {
            "title": "Weekend build", "manufacturer": self.bmw.pk,
            "model": "M3", "year": 2004, "description": "Suspension refresh",
            "status": "planned", "members": [self.member.pk], "_save": "Save",
        })
        self.assertRedirects(response, self.url)
        project = CarProject.objects.get(title="Weekend build")
        self.assertEqual(project.description, "Suspension refresh")
        self.assertQuerySetEqual(project.members.all(), [self.member])

    def test_edit_status_and_clear_members(self):
        self.restoration.members.add(self.member)
        response = self.client.post(
            reverse("admin:workshop_carproject_change", args=[self.restoration.pk]),
            {
                "title": self.restoration.title, "manufacturer": self.bmw.pk,
                "model": "320i", "year": 1989, "description": "",
                "status": "completed", "members": [], "_save": "Save",
            },
        )
        self.assertRedirects(response, self.url)
        self.restoration.refresh_from_db()
        self.assertEqual(self.restoration.status, CarProject.Status.COMPLETED)
        self.assertFalse(self.restoration.members.exists())

    def test_invalid_year_does_not_create_project(self):
        response = self.client.post(reverse("admin:workshop_carproject_add"), {
            "title": "Invalid project", "manufacturer": self.bmw.pk,
            "model": "320i", "year": 1800, "status": "planned", "_save": "Save",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("year", response.context["adminform"].form.errors)
        self.assertFalse(CarProject.objects.filter(title="Invalid project").exists())
