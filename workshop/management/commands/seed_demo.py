import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from workshop.models import CarProject, Manufacturer, Task, TaskCategory


class Command(BaseCommand):
    help = "Populate an empty workshop database with fictional demo data."

    def handle(self, *args, **options):
        Member = get_user_model()
        with transaction.atomic():
            if any(model.objects.exists() for model in (
                Member, Manufacturer, CarProject, TaskCategory, Task,
            )):
                self.stdout.write(
                    "The database already contains workshop data or accounts. "
                    "Nothing changed. Use an empty database to load the demo."
                )
                return

            password = secrets.token_urlsafe(12)
            members = []
            for number, (username, first_name, last_name) in enumerate((
                ("demo", "Alex", "Morgan"),
                ("jordan", "Jordan", "Lee"),
                ("sam", "Sam", "Taylor"),
                ("riley", "Riley", "Brooks"),
            ), start=1):
                member = Member(
                    username=username, first_name=first_name, last_name=last_name,
                    employee_code=f"GRG{number:05d}",
                )
                if username == "demo":
                    member.set_password(password)
                else:
                    member.set_unusable_password()
                member.full_clean()
                member.save()
                members.append(member)

            manufacturers = {}
            for name, country in (("BMW", "Germany"), ("Mazda", "Japan"), ("Volvo", "Sweden")):
                manufacturers[name] = Manufacturer.objects.create(name=name, country=country)
            categories = {
                name: TaskCategory.objects.create(name=name)
                for name in ("Bodywork", "Electrical", "Engine", "Interior", "Suspension")
            }
            projects = (
                ("E30 weekend restoration", "BMW", "320i", 1989, "in_progress",
                 "Restore a classic daily driver while keeping its original character.",
                 (0, 1), (
                     ("Inspect suspension mounts", "Suspension", "done", "high", 0, -7),
                     ("Repair rear wheel arches", "Bodywork", "in_progress", "high", 1, 3),
                     ("Replace dashboard bulbs", "Electrical", "todo", "low", None, None),
                 )),
                ("MX-5 track preparation", "Mazda", "MX-5", 2001, "in_progress",
                 "Prepare a lightweight roadster for its first amateur track day.",
                 (0, 2), (
                     ("Check engine compression", "Engine", "done", "medium", 0, -3),
                     ("Set wheel alignment", "Suspension", "in_progress", "high", 2, 1),
                     ("Secure interior trim", "Interior", "todo", "low", None, 10),
                 )),
                ("240 estate refresh", "Volvo", "240", 1991, "planned",
                 "Plan a comfortable touring build with refreshed electrics and interior.",
                 (1, 3), (
                     ("Inspect wiring harness", "Electrical", "todo", "high", 3, 14),
                     ("Assess seat upholstery", "Interior", "todo", "medium", 1, None),
                     ("Survey paint condition", "Bodywork", "todo", "low", None, 21),
                 )),
                ("E46 suspension refresh", "BMW", "330i", 2003, "completed",
                 "Completed suspension service and final road-test checks.",
                 (0, 2), (
                     ("Replace control arm bushes", "Suspension", "done", "high", 2, -14),
                     ("Check charging voltage", "Electrical", "done", "medium", 0, -12),
                     ("Complete engine inspection", "Engine", "done", "medium", 0, -10),
                 )),
                ("RX-7 future rebuild", "Mazda", "RX-7", 1993, "planned",
                 "An early project idea awaiting a team and an initial assessment.", (), ()),
            )
            today = timezone.localdate()
            for title, make, model, year, status, description, team, tasks in projects:
                project = CarProject.objects.create(
                    title=title, manufacturer=manufacturers[make], model=model,
                    year=year, status=status, description=description,
                )
                project.members.set(members[index] for index in team)
                for task_title, category, task_status, priority, assignee, days in tasks:
                    task = Task(
                        title=task_title, project=project, category=categories[category],
                        status=task_status, priority=priority,
                        description=f"Workshop checklist item for {title}.",
                        assignee=members[assignee] if assignee is not None else None,
                        due_date=today + timedelta(days=days) if days is not None else None,
                    )
                    task.full_clean()
                    task.save()

        self.stdout.write(self.style.SUCCESS(
            "Created 4 members, 3 manufacturers, 5 categories, 5 projects and 12 tasks."
        ))
        self.stdout.write(f"Sign in as demo with password: {password}")
        self.stdout.write("Save this password; it is shown only on the first run.")
