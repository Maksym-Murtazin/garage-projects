from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class Member(AbstractUser):
    employee_code = models.CharField(
        max_length=8,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"\AGRG[0-9]{5}\Z",
                message="Use GRG followed by five digits, for example GRG00001.",
            ),
        ],
        help_text="Workshop employee code, for example GRG00001.",
    )

    REQUIRED_FIELDS = ["email", "employee_code"]

    class Meta:
        ordering = ["username"]

    def __str__(self):
        full_name = self.get_full_name()
        return f"{self.username} ({full_name})" if full_name else self.username
