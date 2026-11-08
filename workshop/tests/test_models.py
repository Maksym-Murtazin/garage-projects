from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from workshop.models import Manufacturer


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
