from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from workshop.models import CarProject, Manufacturer, Task, TaskCategory


class SeedDemoTests(TestCase):
    def test_demo_data_is_valid_and_rerun_preserves_changes_and_password(self):
        output = StringIO()
        call_command("seed_demo", stdout=output)
        member = get_user_model().objects.get(username="demo")
        password = output.getvalue().split("password: ")[1].splitlines()[0]
        self.assertTrue(self.client.login(username="demo", password=password))
        self.assertFalse(get_user_model().objects.filter(is_staff=True).exists())
        self.assertFalse(get_user_model().objects.filter(is_superuser=True).exists())
        self.assertEqual(get_user_model().objects.count(), 4)
        self.assertEqual(Manufacturer.objects.count(), 3)
        self.assertEqual(TaskCategory.objects.count(), 5)
        self.assertEqual(CarProject.objects.count(), 5)
        self.assertEqual(Task.objects.count(), 12)
        for task in Task.objects.all():
            task.full_clean()
        self.assertSetEqual(set(Task.objects.values_list("status", flat=True)), set(Task.Status.values))
        self.assertTrue(CarProject.objects.filter(tasks__isnull=True, members__isnull=True).exists())

        task = Task.objects.filter(status=Task.Status.TODO).first()
        task.title = "Changed during the demo"
        task.status = Task.Status.DONE
        task.save()
        output = StringIO()
        call_command("seed_demo", stdout=output)
        self.assertIn("Nothing changed", output.getvalue())
        self.assertNotIn("password:", output.getvalue())
        self.assertEqual(Task.objects.count(), 12)
        task.refresh_from_db()
        member.refresh_from_db()
        self.assertEqual(task.title, "Changed during the demo")
        self.assertEqual(task.status, Task.Status.DONE)
        self.assertTrue(member.check_password(password))

    def test_existing_account_prevents_loading_demo(self):
        member = get_user_model().objects.create_user(
            username="owner", employee_code="GRG00001",
        )
        call_command("seed_demo", stdout=StringIO())
        self.assertQuerySetEqual(get_user_model().objects.all(), [member])
        self.assertFalse(Manufacturer.objects.exists())
        self.assertFalse(CarProject.objects.exists())

    def test_failure_rolls_back_all_demo_data(self):
        with patch.object(Task, "full_clean", side_effect=RuntimeError("Interrupted")):
            with self.assertRaises(RuntimeError):
                call_command("seed_demo", stdout=StringIO())
        for model in (get_user_model(), Manufacturer, TaskCategory, CarProject, Task):
            self.assertFalse(model.objects.exists())
