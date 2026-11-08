from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase


class MemberModelTests(TestCase):
    def test_create_member_with_employee_code(self):
        member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001", password="test-password"
        )
        member.refresh_from_db()
        self.assertEqual(member.employee_code, "GRG00001")
        self.assertTrue(member.check_password("test-password"))

    def test_employee_code_validation(self):
        member = get_user_model()(username="mechanic", password="unused")
        for code in ("GRG00001", "GRG99999"):
            with self.subTest(code=code):
                member.employee_code = code
                member.full_clean()
        for code in ("", "grg00001", "ABC00001", "GRG0001", "GRG000001",
                     "GRG0000A", "GRG１２３４５", "GRG00001\n"):
            with self.subTest(code=code):
                member.employee_code = code
                with self.assertRaises(ValidationError) as error:
                    member.full_clean()
                self.assertIn("employee_code", error.exception.message_dict)

    def test_employee_code_is_unique_in_database(self):
        get_user_model().objects.create_user(
            username="first", employee_code="GRG00001"
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            get_user_model().objects.create_user(
                username="second", employee_code="GRG00001"
            )

    def test_create_superuser_with_employee_code(self):
        member = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com",
            employee_code="GRG00002", password="test-password",
        )
        self.assertEqual(member.employee_code, "GRG00002")
        self.assertTrue(member.is_staff)
        self.assertTrue(member.is_superuser)

    def test_string_representation(self):
        member = get_user_model()(username="mechanic")
        self.assertEqual(str(member), "mechanic")
        member.first_name = "Alex"
        member.last_name = "Smith"
        self.assertEqual(str(member), "mechanic (Alex Smith)")
