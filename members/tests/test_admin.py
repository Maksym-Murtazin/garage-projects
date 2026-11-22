from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class MemberAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="admin", employee_code="GRG00001", password="test-password"
        )
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00002"
        )

    def setUp(self):
        self.client.force_login(self.admin)
        self.add_url = reverse("admin:members_member_add")
        self.change_url = reverse(
            "admin:members_member_change", args=[self.member.pk]
        )
        self.list_url = reverse("admin:members_member_changelist")

    def member_data(self, **overrides):
        return {
            "username": "new_mechanic",
            "first_name": "Alex",
            "last_name": "Smith",
            "email": "alex@example.com",
            "employee_code": "GRG00003",
            "usable_password": "true",
            "password1": "Workshop-Test-Password-724!",
            "password2": "Workshop-Test-Password-724!",
            **overrides,
        }

    def test_employee_code_is_displayed_and_searchable(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, self.member.employee_code)
        response = self.client.get(self.list_url, {"q": "GRG00002"})
        self.assertEqual(
            list(response.context["cl"].queryset), [self.member]
        )

    def test_employee_code_is_available_on_both_forms(self):
        for url in (self.add_url, self.change_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'name="employee_code"')

    def test_create_member_with_custom_fields(self):
        data = self.member_data()
        response = self.client.post(self.add_url, data)
        self.assertEqual(response.status_code, 302)
        member = get_user_model().objects.get(username=data["username"])
        for field in ("employee_code", "first_name", "last_name", "email"):
            self.assertEqual(getattr(member, field), data[field])
        self.assertTrue(member.check_password(data["password1"]))
        self.assertFalse(member.is_staff)
        self.assertFalse(member.is_superuser)

    def test_invalid_or_duplicate_code_does_not_create_member(self):
        for code in ("", "BAD00003", self.member.employee_code):
            with self.subTest(code=code):
                response = self.client.post(
                    self.add_url, self.member_data(employee_code=code)
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    "employee_code", response.context["adminform"].form.errors
                )
                self.assertFalse(
                    get_user_model().objects.filter(username="new_mechanic").exists()
                )

    def test_update_employee_code(self):
        response = self.client.get(self.change_url)
        data = response.context["adminform"].form.initial.copy()
        data.update(employee_code="GRG00004", is_active="on")
        data.pop("last_login", None)
        data.pop("date_joined", None)
        data["date_joined_0"] = self.member.date_joined.strftime("%Y-%m-%d")
        data["date_joined_1"] = self.member.date_joined.strftime("%H:%M:%S")
        response = self.client.post(self.change_url, data)
        self.assertEqual(response.status_code, 302)
        self.member.refresh_from_db()
        self.assertEqual(self.member.employee_code, "GRG00004")
        self.assertEqual(self.member.username, "mechanic")

    def test_regular_member_cannot_access_member_admin(self):
        self.client.force_login(self.member)
        for url in (self.list_url, self.add_url, self.change_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response, f"{reverse('admin:login')}?next={url}"
                )
