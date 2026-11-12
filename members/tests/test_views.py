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
