from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Manufacturer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarProject(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    title = models.CharField(max_length=150)
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        related_name="car_projects",
    )
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1886), MaxValueValidator(9999)],
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="car_projects",
        blank=True,
    )

    class Meta:
        ordering = ["title", "pk"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("workshop:project-detail", kwargs={"pk": self.pk})


class TaskCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "task categories"

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    project = models.ForeignKey(
        CarProject, on_delete=models.CASCADE, related_name="tasks",
    )
    category = models.ForeignKey(
        TaskCategory, on_delete=models.PROTECT, related_name="tasks",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TODO,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM,
    )
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["title", "pk"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.project_id and self.assignee_id:
            if not CarProject.objects.filter(
                pk=self.project_id, members=self.assignee_id,
            ).exists():
                raise ValidationError({
                    "assignee": "The assignee must be a member of this project.",
                })
