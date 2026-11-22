# Garage Projects

A Django application for a small tuning and restoration workshop. Manage car
projects, coordinate project teams, and track work from the first inspection
to the final checks.

## Getting started

Install Git and Python 3.12, then clone the project:

```sh
git clone --branch main https://github.com/Maksym-Murtazin/garage-projects.git
cd garage-projects
```

Create and activate a virtual environment. On Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
```

From the activated environment, start a local workshop with sample data:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open [the workshop](http://127.0.0.1:8000/) and sign in as **demo** with the
password printed by `seed_demo`. Open a car project to see its team, tasks,
and progress. Stop the local server with Ctrl+C.

### Accounts and sample data

On an empty database, `seed_demo` creates four members, three manufacturers,
five categories, five projects, and twelve tasks. It skips an existing
workshop. Use `python manage.py changepassword demo` to reset the demo password.

For an empty workshop, skip `seed_demo` and run `python manage.py createsuperuser`
after migrations. You can also create an administrator alongside the demo data.
Choose a unique employee code (GRG followed by five digits). The sample accounts
use GRG00001 through GRG00004. Sign in at [Django admin](http://127.0.0.1:8000/admin/).

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

## Developing

The application uses Django, SQLite, server-rendered templates, and CSS.
See [requirements.txt](requirements.txt) for the pinned Django version.
With the virtual environment active, run:

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The test suite uses a separate database.

### Data model and source layout

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

## Configuration

Management commands use `config.settings.dev` by default. This enables debug
pages and uses a development-only key for local testing.

WSGI and ASGI default to `config.settings.prod`, which disables debug pages and
requires HTTPS. Set these environment variables for the production server and
for production management commands such as migrations and static collection:

- `DJANGO_SETTINGS_MODULE=config.settings.prod`
- `DJANGO_SECRET_KEY` — a private, randomly generated key kept across restarts.
- `DJANGO_ALLOWED_HOSTS` — the deployment hostnames, separated by commas.

Use [.env.example](.env.example) as a template. Set the values in your hosting
environment or configure your process launcher to load a private `.env` file.
Django reads the process environment and does not load that file automatically.

## Deployment

With production environment variables set, run these commands on the host:

```sh
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
```

Use a production WSGI or ASGI server with `config.wsgi:application` or
`config.asgi:application`. Configure the host to serve `/static/` from
`staticfiles/` and terminate HTTPS. If a proxy terminates TLS, configure
Django to recognize secure requests only from that trusted proxy.
Keep the SQLite file on persistent storage and verify that a backup can be restored.

Review the [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
against the target host before release.
