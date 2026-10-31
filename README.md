# NEXUS CRM

PyQt6 CRM application backed by PostgreSQL, with a shared visual design system and Google Calendar / SMTP communication tools.

## Run on macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

If a working `.venv` already exists, activate it and run `python main.py`; do not recreate it unnecessarily.

## Local configuration and security

- Keep `.env`, `token.json`, and your Google OAuth client-secret JSON file local and private.
- `.env.example` is a template only. Copy it to `.env` and fill in your own local settings if you are setting up a new machine.
- Never commit or share passwords, SMTP app passwords, OAuth client-secret files, or `token.json`.
- `GOOGLE_CALENDAR_ID` should point to the separate calendar created for Nexus CRM, not `primary`.
- Google Calendar API must be enabled and the Google account used for authorization must be included as a test user while the OAuth app is in Testing mode.
- The Calendar scope used by this version is `https://www.googleapis.com/auth/calendar.events.owned`. If you change scopes later, delete the local token and authorize again.

## Admin workspace

The Admin page includes:

- PostgreSQL overview counts for Applications, Trainees, Mentors, Project Tracking and Users.
- Search across calendar event title, type, participant, email, phone, mentor and meeting link.
- Filters by meeting type and upcoming date window.
- A live participant selector populated from the canonical `Trainees` table. Applications are joined through `TraineeID`, so the participant's current name, email and phone are displayed without duplicating contact records.
- Create, edit and cancel calendar events in the configured Nexus CRM calendar.
- Participant email invitations through the existing SMTP configuration.
- A meeting-link column and an action to open the link. New events request a Google Meet conference automatically when no manual meeting URL is supplied; Google may take a short time to return the generated link.
- Events added or edited in Google Calendar appear in the CRM after Refresh. For events created outside the CRM, participant details are matched using attendee email addresses.

Google Calendar remains the event source of truth. The CRM reads the latest calendar events on refresh and writes changes made through the Admin page back to Google Calendar. Participant contact details are read from PostgreSQL, not copied into a separate CRM calendar table.

## Data and migrations

- Existing PostgreSQL tables and data are retained. The app's `ensure_extended_schema()` adds missing optional fields without dropping tables.
- Refreshing the Admin overview does not import Excel files or overwrite database records.
- `database_schema.sql`, `database_migration_v2.sql`, `database_import.py`, and the files in `tests/` are retained for maintenance and data migration workflows.

## Tests

Install the optional development requirements and run from the project root:

```bash
python -m pip install -r requirements-dev.txt
PYTHONPATH=. python -m pytest -q
```

## Build

- macOS: `bash build_macos.sh`
- Windows: `build_windows.bat`
# NexusCRM-App
