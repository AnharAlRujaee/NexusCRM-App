# NEXUS CRM — PostgreSQL setup and safety

## Run the application

1. Install Python 3.13 (or a compatible Python version) and PostgreSQL.
2. Create/choose the `nexus_crm` database and run `database_schema.sql` in pgAdmin if the schema is not already present.
3. Create a local `.env` file in the project root with your own database settings (see `.env.example`). Do not share `.env`.
4. Install dependencies with `python -m pip install -r requirements.txt`.
5. Run `python main.py`. Sign in with a user already stored in your database, or use Sign up if no account exists.

## Safe database behaviour

- Refresh buttons only read current PostgreSQL data. They never re-import Excel and never clear or replace records.
- On first startup, the app adds missing optional columns and the `VITHistory` table with non-destructive `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` / `CREATE TABLE IF NOT EXISTS` operations. If the source workbooks are present and row counts match, missing optional fields are backfilled in source order.
- `database_import.py` refuses to import over a populated database unless you explicitly use `--replace`. **`--replace` is destructive**: back up your database first. It is not needed for ordinary app use or refresh.
- The `data/Users.xlsx` in this package is a blank template without password rows. Existing logins are read from PostgreSQL; do not store real passwords in shared workbooks.

## Modules

- Applications: search, duplicate filters, mentor-meeting filters, VIT history comparison, add/edit, CSV export.
- Mentor Interview: search/category filters, add/edit, CSV export.
- Interviews / Project Tracking: sent/received filters, add/edit, CSV export.
- Trainees: directory, search, add/edit, CSV export.
- Admin: live database status, searchable/filterable Google Calendar events, linked applicant/trainee email and phone details, mentor association, event create/edit/cancel, meeting links, and participant email invitations.

Dates in editor dialogs should be entered as `YYYY-MM-DD` or `YYYY-MM-DD HH:MM`.
