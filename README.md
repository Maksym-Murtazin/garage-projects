# Garage Projects

A Django web application for a small tuning and restoration workshop to
organize car projects, coordinate team members, and track workshop tasks.

## Planned features

- Manage car projects, manufacturers, team members, and task categories.
- Assign team members to projects and allow members to join or leave a project.
- Track tasks by assignee, status, priority, and due date.
- Search and filter lists with pagination.
- View project progress and workshop statistics.
- Sign in to access the shared workshop workspace.

## Development status

The Django project structure is ready. Workshop features are not implemented
yet. Development takes place on the `develop` branch.

## Local setup

Use Python 3.12. The project currently uses Django 5.2.19 and SQLite.

Clone the repository and switch to the development branch:

```text
git clone https://github.com/Maksym-Murtazin/garage-projects.git
cd garage-projects
git switch develop
```

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver
```

### Linux / macOS

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py check
.venv/bin/python manage.py runserver
```

Open http://127.0.0.1:8000/ to see the default Django start page.
Stop the server with `Ctrl+C`.

### Database setup

Do not run `migrate` or `createsuperuser` at this stage. The custom user model
will be added before the first database migration. A warning about unapplied
migrations is expected for now; database-backed pages, including the admin
login, are not ready yet.

### Development settings

These settings are for local development: `DEBUG` is enabled, only local hosts
are allowed, and the fallback secret key is a public development placeholder.
You can override it with the `DJANGO_SECRET_KEY` environment variable.
Deployment configuration will be added separately.
