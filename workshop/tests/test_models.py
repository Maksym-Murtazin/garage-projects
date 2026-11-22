from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from workshop.models import CarProject, Manufacturer, Task, TaskCategory


class ManufacturerModelTests(TestCase):
    def test_create_manufacturer(self):
        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        manufacturer.refresh_from_db()
        self.assertEqual(manufacturer.name, "BMW")
        self.assertEqual(manufacturer.country, "Germany")
        self.assertEqual(str(manufacturer), "BMW")

    def test_duplicate_name_is_rejected_by_database(self):
        Manufacturer.objects.create(name="BMW", country="Germany")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Manufacturer.objects.create(name="BMW", country="Germany")

    def test_name_and_country_are_required(self):
        for field in ("name", "country"):
            with self.subTest(field=field):
                data = {"name": "BMW", "country": "Germany", field: ""}
                with self.assertRaises(ValidationError) as error:
                    Manufacturer(**data).full_clean()
                self.assertIn(field, error.exception.message_dict)

    def test_manufacturers_are_ordered_by_name(self):
        for name in ("Toyota", "Audi", "BMW"):
            Manufacturer.objects.create(name=name, country="Test country")
        self.assertEqual(
            list(Manufacturer.objects.values_list("name", flat=True)),
            ["Audi", "BMW", "Toyota"],
        )


class CarProjectModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")

    def create_project(self, **overrides):
        data = {
            "title": "E30 restoration",
            "manufacturer": self.manufacturer,
            "model": "320i",
            "year": 1989,
        }
        data.update(overrides)
        return CarProject.objects.create(**data)

    def test_create_project_with_defaults(self):
        project = self.create_project()
        project.refresh_from_db()
        project.full_clean()
        self.assertEqual(str(project), "E30 restoration")
        self.assertEqual(project.manufacturer, self.manufacturer)
        self.assertEqual(project.model, "320i")
        self.assertEqual(project.year, 1989)
        self.assertEqual(project.status, CarProject.Status.PLANNED)
        self.assertEqual(project.description, "")
        self.assertFalse(project.members.exists())

    def test_required_fields_are_validated(self):
        project = self.create_project()
        for field, value in (
            ("title", ""),
            ("model", ""),
            ("year", None),
            ("manufacturer", None),
        ):
            with self.subTest(field=field):
                project.refresh_from_db()
                setattr(project, field, value)
                with self.assertRaises(ValidationError) as error:
                    project.full_clean()
                self.assertIn(field, error.exception.message_dict)

    def test_year_and_status_are_validated(self):
        project = self.create_project()
        for field, value in (("year", 1885), ("year", 10000), ("status", "unknown")):
            with self.subTest(field=field, value=value):
                project.refresh_from_db()
                setattr(project, field, value)
                with self.assertRaises(ValidationError) as error:
                    project.full_clean()
                self.assertIn(field, error.exception.message_dict)
        for status in CarProject.Status.values:
            project.refresh_from_db()
            project.status = status
            project.full_clean()

    def test_members_can_join_multiple_projects_and_leave(self):
        first = self.create_project()
        second = self.create_project(title="Track build")
        member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        colleague = get_user_model().objects.create_user(
            username="painter", employee_code="GRG00002",
        )
        first.members.add(member, colleague)
        second.members.add(member)
        self.assertCountEqual(first.members.all(), [member, colleague])
        self.assertCountEqual(member.car_projects.all(), [first, second])
        first.members.remove(member)
        self.assertCountEqual(first.members.all(), [colleague])
        self.assertCountEqual(member.car_projects.all(), [second])

    def test_manufacturer_with_projects_cannot_be_deleted(self):
        project = self.create_project()
        with self.assertRaises(ProtectedError):
            self.manufacturer.delete()
        self.assertTrue(CarProject.objects.filter(pk=project.pk).exists())

    def test_deleting_project_preserves_manufacturer_and_members(self):
        project = self.create_project()
        member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        project.members.add(member)
        project.delete()
        self.assertTrue(Manufacturer.objects.filter(pk=self.manufacturer.pk).exists())
        self.assertTrue(get_user_model().objects.filter(pk=member.pk).exists())
        self.assertFalse(member.car_projects.exists())

    def test_deleting_member_preserves_project(self):
        project = self.create_project()
        member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        project.members.add(member)
        member.delete()
        self.assertTrue(CarProject.objects.filter(pk=project.pk).exists())
        self.assertFalse(project.members.exists())

    def test_projects_are_ordered_by_title_then_primary_key(self):
        last = self.create_project(title="Track build")
        first = self.create_project()
        second = self.create_project()
        self.assertEqual(list(CarProject.objects.all()), [first, second, last])


class TaskCategoryModelTests(TestCase):
    def test_create_category(self):
        category = TaskCategory.objects.create(name="Suspension")
        category.refresh_from_db()
        self.assertEqual(category.name, "Suspension")
        self.assertEqual(str(category), "Suspension")

    def test_duplicate_name_is_rejected_by_database(self):
        TaskCategory.objects.create(name="Suspension")
        with self.assertRaises(IntegrityError), transaction.atomic():
            TaskCategory.objects.create(name="Suspension")

    def test_name_is_required(self):
        with self.assertRaises(ValidationError) as error:
            TaskCategory(name="").full_clean()
        self.assertIn("name", error.exception.message_dict)

    def test_categories_are_ordered_by_name(self):
        for name in ("Suspension", "Bodywork", "Electrical"):
            TaskCategory.objects.create(name=name)
        self.assertEqual(
            list(TaskCategory.objects.values_list("name", flat=True)),
            ["Bodywork", "Electrical", "Suspension"],
        )


class TaskModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        manufacturer = Manufacturer.objects.create(name="BMW", country="Germany")
        cls.project = CarProject.objects.create(
            title="E30 restoration", manufacturer=manufacturer,
            model="320i", year=1989,
        )
        cls.category = TaskCategory.objects.create(name="Suspension")
        cls.member = get_user_model().objects.create_user(
            username="mechanic", employee_code="GRG00001",
        )
        cls.project.members.add(cls.member)
        cls.task = Task.objects.create(
            title="Replace bushings", project=cls.project,
            category=cls.category, assignee=cls.member,
        )

    def test_assignee_must_belong_to_selected_project(self):
        self.task.full_clean()
        other_project = CarProject.objects.create(
            title="Track build", manufacturer=self.project.manufacturer,
            model="M3", year=2004,
        )
        self.task.project = other_project
        with self.assertRaises(ValidationError) as error:
            self.task.full_clean()
        self.assertIn("assignee", error.exception.message_dict)
        self.task.assignee = None
        self.task.full_clean()

    def test_category_is_protected_and_deleting_assignee_preserves_task(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()
        self.member.delete()
        self.task.refresh_from_db()
        self.assertIsNone(self.task.assignee)
        self.assertEqual(self.task.category, self.category)
        self.assertEqual(self.task.project, self.project)

    def test_deleting_project_removes_its_tasks_only(self):
        self.project.delete()
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
        self.assertTrue(TaskCategory.objects.filter(pk=self.category.pk).exists())
        self.assertTrue(get_user_model().objects.filter(pk=self.member.pk).exists())
