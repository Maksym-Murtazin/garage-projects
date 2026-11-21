# Garage Projects

A Django application for a small tuning and restoration workshop. Manage car
projects, coordinate project teams, and track work from the first inspection
to the final checks.

## Features

- Create, view, edit, and delete car projects, tasks, and workshop members.
- Manage manufacturers and task categories, with protection against deleting
  records that are still in use.
- Join or leave project teams, or select the whole team through **Manage team**.
- Track task status, priority, optional due dates, and assignments to team members.
- View completed-task counts, progress bars, and percentages for each project.
- Search all lists and filter projects, tasks, and members. Lists show 10 records
  per page and preserve search and filters across pages.
- Open matching lists from dashboard statistics and access your profile from
  your username in the navigation. The dashboard also counts visits per session.
- Sign in to a shared workshop workspace with server-rendered templates and
  custom CSS. All five models are also available in Django admin.

## Technology

Python 3.12, Django 5.2.19, SQLite, Django templates, and CSS.
Dependencies are listed in [requirements.txt](requirements.txt).
Development takes place on the `develop` branch.

## Local setup

Install Python 3.12 and Git, then clone the development branch:

```text
git clone --branch develop https://github.com/Maksym-Murtazin/garage-projects.git
cd garage-projects
```

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
```

### Linux / macOS

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate
```

Next, choose either the demo workshop or your own administrator account below.
Create an account before starting the server so you can sign in immediately.

### Option A: demo workshop

Run this after migrations, before creating any accounts or workshop records:

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo
```

On Linux/macOS:

```bash
.venv/bin/python manage.py seed_demo
```

This creates fictional data: **4 members, 3 manufacturers, 5 categories,
5 projects, and 12 tasks**. Examples include restoration and track preparation,
all project and task statuses, different priorities, unassigned tasks, and a
project without a team or tasks. Due dates are relative to the first run.

Sign in as **demo** using the randomly generated password printed by the command.
Save it locally: the password is shown only once. This account has no admin
privileges. The other demo members cannot sign in until a password is set.

The command only populates an empty workshop database. If any accounts or
workshop records exist, it changes nothing. Re-running it does not duplicate
records, reset passwords, or overwrite edits. Loading is atomic: a failure
leaves no partial demo data. Use a separate empty local database if you want
sample data without replacing existing work.

To reset the demo password:

```powershell
.\.venv\Scripts\python.exe manage.py changepassword demo
```

On Linux/macOS, use `.venv/bin/python manage.py changepassword demo`.

### Option B: your own account

Create an administrator for an empty workshop, or add one after loading the demo:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

On Linux/macOS, use `.venv/bin/python manage.py createsuperuser`.
Enter a username, email, unique employee code, and password when prompted.
An employee code is `GRG` followed by five digits, such as `GRG00001`.
The demo already uses `GRG00001` through `GRG00004`; choose a different code
when adding an administrator to it.

### Start the server

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

On Linux/macOS, use `.venv/bin/python manage.py runserver`.
Open [the workshop](http://127.0.0.1:8000/) and sign in. Use **Sign out** to end
the session and `Ctrl+C` in the terminal to stop the server.
The [admin site](http://127.0.0.1:8000/admin/) requires a superuser or a staff
account with the appropriate permissions.

## Using the workshop

1. Create manufacturers, task categories, and ordinary member accounts from
   their respective lists if you started without demo data.
2. Create a project with its vehicle information and description.
3. Open **Manage team** on the project and select its members, or use
   **Join project** to add yourself.
4. Use **Create task** on the project page. Choose a category, status, priority,
   optional due date, and a team member, or leave the task unassigned.
5. Update tasks as work progresses. The progress bar reflects completed tasks;
   the project's own status is set manually.

| List | Search | Filters |
| --- | --- | --- |
| Projects | Title, manufacturer, car model | Project status |
| Tasks | Title, project title, assignee username or employee code | Status (including Open tasks), priority, project |
| Members | Username, first name, last name, employee code | Active or inactive accounts |
| Manufacturers | Name, country | — |
| Categories | Name | — |

**Open tasks** combines To do and In progress. Dashboard links apply the filters
matching their counts. Use **Reset** to clear filters and search on projects,
tasks, or members; manufacturer and category lists offer **Clear search**.

### Accounts and data rules

This is a shared internal workspace. Signed-in members can manage workshop
records and create ordinary accounts; there is no public registration page.
Creating a member validates and hashes their password without switching the
creator's session. Profile editing preserves passwords, account status, and
permissions. Your profile lists your projects and assigned tasks, including
completed work.

- Task assignees must belong to the project's team. A task's project cannot be
  changed through its edit form.
- Leaving a project or removing members through **Manage team** unassigns all
  of their tasks in that project, including completed tasks, without changing
  task statuses. Team changes and unassignment are saved in one transaction.
- Deleting a project also deletes its tasks. Deleting a task preserves its
  project and the other tasks.
- Deleting a member preserves projects and tasks, removes team memberships,
  and leaves their tasks unassigned. You cannot delete yourself, staff accounts,
  or superusers through the workshop site.
- Manufacturers referenced by projects and categories referenced by any tasks
  cannot be deleted. The confirmation page shows the dependent records.
- Deletions require confirmation. Form submissions, joining, leaving, and
  signing out use POST requests with CSRF protection.

## Data model and source layout

| Model | Purpose and relationships |
| --- | --- |
| `Member` | Extends `AbstractUser` with a unique employee code; joins projects and receives task assignments |
| `Manufacturer` | Stores a name and country; referenced by car projects |
| `CarProject` | Stores vehicle information, description, and status; belongs to a manufacturer and has many members and tasks |
| `TaskCategory` | Names a type of work; referenced by tasks |
| `Task` | Belongs to a project and category; has an optional assignee and due date, plus status and priority |

| Path | Contents |
| --- | --- |
| `config/` | Settings and root URL configuration |
| `members/` | Custom user model, member forms, views, templates, and tests |
| `workshop/` | Projects, tasks, manufacturers, categories, and their tests |
| `workshop/management/commands/seed_demo.py` | Demo data command |
| `workshop/static/workshop/css/styles.css` | Shared site styles |
| `templates/` | Base layout, login page, and pagination include |

## Checks and tests

On Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

On Linux/macOS:

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py test
```

Tests cover model validation, admin integration, authentication, CRUD operations,
search and filters, pagination, team assignments, protected deletion, project
progress, dashboard links, and demo data loading. Django creates a separate test
database; running tests does not replace the local workshop data.

## Configuration

Management commands use `config.settings.dev` by default. This enables debug
pages and uses a development-only key for local testing.

WSGI and ASGI default to `config.settings.prod`, which disables debug pages and
requires HTTPS. Set these environment variables for the production server and
for production management commands such as migrations and static collection:

- `DJANGO_SETTINGS_MODULE=config.settings.prod`
- `DJANGO_SECRET_KEY` — a private, randomly generated key kept across restarts.
- `DJANGO_ALLOWED_HOSTS` — the deployment hostnames, separated by commas.

Run `python manage.py check --deploy` with the production environment before
deployment. Configure TLS at the web server and serve the output of
`python manage.py collectstatic` from `staticfiles/`.
