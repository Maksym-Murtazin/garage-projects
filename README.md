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

Member, manufacturer, car project, task category, and task models are ready.
All five models can be managed through the admin site.
The workshop dashboard is available after signing in. It displays project,
task, and active member counts, plus dashboard visits in the current session.
The project list supports searching by title, manufacturer, or car model and
shows 10 projects per page, keeping the search when switching pages. Each project
has a detail page with vehicle information, a description, team members, and tasks.
The project list and detail pages show task progress: completed tasks out of the
total, a progress bar, and a rounded percentage. Projects without tasks display
"No tasks yet." Progress reflects current task statuses; the project status is
still set manually.
Signed-in members can create, edit, and delete projects through the site.
Deletion requires a confirmation page and removes the project's tasks as well.
Members can join or leave a project from its detail page. Leaving unassigns all
of that member's tasks in the project, including completed tasks, without changing
their statuses. Team membership is managed separately from the project form.
The task list supports search by title, project, assignee username, or employee
code, with status, priority, and project filters. Pagination preserves these
parameters. Task titles link to detail pages with the full description, project,
category, assignee, status, priority, and due date. Signed-in members can create
tasks from a project's detail page and edit them from the task detail page.
The project stays fixed, and assignee choices are limited to its team members.
Tasks can also be left unassigned. Task deletion requires confirmation and
returns to the project page, preserving the project and its other tasks.
The member list shows usernames, full names, employee codes, and active or
inactive status. Signed-in members can search by username, first name, last
name, or employee code, with 10 results per page and search preserved in pagination.
Each member has a detail page with their workshop information, joined projects,
and assigned tasks, including completed work. Member profiles are linked from
the member list, project teams, and task detail pages.
Signed-in members can create ordinary workshop accounts from the member list.
The form requires a unique username, a valid unique employee code, and a password
with confirmation; first and last names are optional. Django validates and hashes
the password. New accounts have no staff or superuser privileges. After creation,
the creator stays signed in and is redirected to the new member's profile.
Signed-in members can edit a member's username, first name, last name, and
employee code from their profile. This form preserves passwords, account status,
and permissions, and returns to the edited profile after saving.
Deleting a member requires confirmation and preserves projects and tasks.
The member leaves all project teams, and their tasks become unassigned without
changing status. Signed-in members cannot delete their own account, staff
accounts, or superusers through the workshop site.
The manufacturer list is available to signed-in members and supports searching
by name or country. Results are sorted by name with 10 manufacturers per page,
and pagination preserves the search.
Signed-in members can create and edit manufacturers from this list. Both name
and country are required, and manufacturer names must be unique. Saving returns
to the list; editing a manufacturer preserves its links to existing projects.
Unused manufacturers can be deleted after confirmation. If a manufacturer is
used by projects, the confirmation page lists those projects and blocks deletion.
Submitting a deletion request for a manufacturer in use also preserves it and
returns the explanation, including when a project was added after opening the page.
The task category list is available to signed-in members, with search by name
and alphabetical ordering. It shows 10 categories per page and preserves the
search when switching pages.
Signed-in members can create and edit task categories from this list. Names are
required and must be unique. Saving returns to the list, and renaming a category
preserves its links to existing tasks.
Unused categories can be deleted after confirmation. Categories used by tasks,
including completed tasks, cannot be deleted. The page lists the related tasks
and their projects; direct deletion requests are also blocked.
Development takes place
on the `develop` branch.

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
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

### Linux / macOS

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in with a workshop account to see the dashboard.
Create an administrator using the steps below, or use a member account created
through the admin site. Ordinary active members can access the dashboard without
staff permissions. Use **Sign out** to end the session.
Stop the server with `Ctrl+C`.

### Database setup

The initial migration creates the custom `Member` model. Each member has a
unique employee code: `GRG` followed by five ASCII digits, such as `GRG00001`.

Car projects store a title, manufacturer, car model, production year, optional
description, and status (planned, in progress, or completed). A project can have
multiple team members, and a member can work on several projects. Manufacturers
referenced by projects cannot be deleted.

Task categories have unique names, such as Bodywork, Electrical, or Suspension,
and are sorted alphabetically.

Tasks belong to a project and category, with an optional assignee and due date.
They have a title, optional description, status (to do, in progress, or done),
and priority (low, medium, or high). Model validation requires an assignee to
belong to the selected project. Deleting an assignee leaves the task unassigned;
deleting a project also deletes its tasks. Categories used by tasks cannot be
deleted.

After applying migrations, you can create a local administrator:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

On Linux/macOS, use `.venv/bin/python manage.py createsuperuser`.
Enter a username, email, employee code, and password when prompted.
The admin login is available at http://127.0.0.1:8000/admin/.
Open **Members** to add or edit workshop members. The member list displays
employee codes and supports searching by code, username, name, or email.
Employee codes are required and must be unique. Admin access requires a staff
account with the appropriate permissions; a superuser has full access.

Open **Manufacturers** to add, edit, or delete manufacturers. The list displays
names and countries, supports searching both fields, and has a country filter.

Open **Car projects** to manage projects and select their team members. The list
shows the manufacturer, car model, year, and status. Search by project title,
manufacturer, or car model, and filter by status or manufacturer.

Open **Task categories** to add, edit, or delete categories and search by name.

Open **Tasks** to manage tasks and assign project members. Search by task title,
project title, assignee username, or employee code. Filter by status, priority,
category, or project, and browse by due date. The form rejects an assignee who
does not belong to the selected project; tasks can also be left unassigned.

## Tests

```powershell
.\.venv\Scripts\python.exe manage.py test
```

On Linux/macOS, use `.venv/bin/python manage.py test`.

### Development settings

These settings are for local development: `DEBUG` is enabled, only local hosts
are allowed, and the fallback secret key is a public development placeholder.
You can override it with the `DJANGO_SECRET_KEY` environment variable.
Deployment configuration will be added separately.
