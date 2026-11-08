from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from workshop.models import Manufacturer


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
