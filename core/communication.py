"""Optional Google Calendar and SMTP communication services for Nexus CRM.

Credentials are intentionally kept outside source control. Calendar access requires
Google OAuth client credentials; outbound mail requires SMTP settings in .env.
"""
from __future__ import annotations

import os
import smtplib
import uuid
from email.message import EmailMessage
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events.owned"]

def _credentials_path() -> Path:
    configured = os.getenv("GOOGLE_CREDENTIALS_FILE", "").strip()
    return Path(configured).expanduser() if configured else PROJECT_ROOT / "credentials.json"


def _token_path() -> Path:
    configured = os.getenv("GOOGLE_TOKEN_FILE", "").strip()
    return Path(configured).expanduser() if configured else PROJECT_ROOT / "token.json"


def _calendar_service():
    credentials_path = _credentials_path()
    if not credentials_path.is_file():
        raise RuntimeError(
            "Google Calendar is not connected yet. Add your Google OAuth credentials "
            f"file at: {credentials_path}"
        )
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google Calendar support is not installed. Run: python -m pip install "
            "google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        ) from exc

    token_path = _token_path()
    creds = Credentials.from_authorized_user_file(str(token_path), CALENDAR_SCOPES) if token_path.is_file() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), CALENDAR_SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _calendar_id() -> str:
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "").strip()
    if not calendar_id or calendar_id.casefold() == "primary":
        raise RuntimeError(
            "For privacy, Nexus CRM will not access your primary personal calendar. "
            "Set GOOGLE_CALENDAR_ID in .env to the dedicated Nexus CRM calendar ID."
        )
    return calendar_id


def _event_datetime(value):
    """Convert a Python/Qt ISO datetime into a Google Calendar RFC3339 value."""
    from datetime import datetime
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.isoformat()


def fetch_calendar_events(max_results: int = 250, include_past: bool = False):
    """Return normalized events from the configured Nexus CRM calendar."""
    from datetime import datetime, timezone
    service = _calendar_service()
    params = {
        "calendarId": _calendar_id(),
        "maxResults": max(1, min(int(max_results), 2500)),
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if not include_past:
        params["timeMin"] = datetime.now(timezone.utc).isoformat()
    response = service.events().list(**params).execute()
    events = []
    for item in response.get("items", []):
        start_obj = item.get("start", {})
        end_obj = item.get("end", {})
        start = start_obj.get("dateTime", start_obj.get("date", ""))
        end = end_obj.get("dateTime", end_obj.get("date", ""))
        attendees = item.get("attendees", []) or []
        emails = [a.get("email", "").strip() for a in attendees if a.get("email")]
        private = (item.get("extendedProperties") or {}).get("private", {})
        description = item.get("description", "") or ""
        meeting_link = private.get("meeting_link", "") or item.get("hangoutLink", "")
        if not meeting_link:
            conference = item.get("conferenceData", {}) or {}
            meeting_link = next((entry.get("uri", "") for entry in conference.get("entryPoints", [])
                                 if entry.get("entryPointType") == "video" and entry.get("uri")), "")
        if not meeting_link:
            import re
            match = re.search(r"(?:Meeting link|Join link)\s*:\s*(https?://\S+)", description, re.I)
            meeting_link = match.group(1).rstrip(")],.") if match else ""
        events.append({
            "start": start,
            "end": end,
            "summary": item.get("summary", "Untitled event"),
            "attendees": emails,
            "attendee_text": ", ".join(emails),
            "location": item.get("location", "") or "",
            "description": description,
            "html_link": item.get("htmlLink", "") or "",
            "event_id": item.get("id", ""),
            "event_type": private.get("event_type", "Meeting"),
            "participant_name": private.get("participant_name", ""),
            "participant_email": private.get("participant_email", emails[0] if emails else ""),
            "participant_phone": private.get("participant_phone", ""),
            "participant_id": private.get("participant_id", ""),
            "mentor_name": private.get("mentor_name", ""),
            "meeting_link": meeting_link,
            "status": "Cancelled" if item.get("status") == "cancelled" else "Scheduled",
        })
    return events


def _event_body(data: dict) -> dict:
    """Build the Google event payload, keeping CRM linkage in private properties."""
    from datetime import datetime, timedelta
    start = _event_datetime(data["start"])
    end_value = data.get("end")
    if end_value:
        end = _event_datetime(end_value)
    else:
        end = (datetime.fromisoformat(start) + timedelta(minutes=45)).isoformat()
    attendees = []
    email = str(data.get("participant_email") or "").strip()
    if email:
        attendees.append({"email": email})
    description = str(data.get("description") or "").strip()
    meeting_link = str(data.get("meeting_link") or "").strip()
    if meeting_link:
        description = (description + "\n\n" if description else "") + f"Meeting link: {meeting_link}"
    private = {
        "nexus_crm": "1",
        "event_type": str(data.get("event_type") or "Meeting"),
        "participant_name": str(data.get("participant_name") or ""),
        "participant_email": email,
        "participant_phone": str(data.get("participant_phone") or ""),
        "participant_id": str(data.get("participant_id") or ""),
        "mentor_name": str(data.get("mentor_name") or ""),
        "meeting_link": meeting_link,
    }
    return {
        "summary": str(data.get("summary") or "Nexus CRM meeting").strip(),
        "description": description,
        "location": str(data.get("location") or "").strip(),
        "start": {"dateTime": start},
        "end": {"dateTime": end},
        "attendees": attendees,
        "extendedProperties": {"private": private},
    }


def create_calendar_event(data: dict) -> dict:
    """Create an event in the configured Nexus CRM calendar."""
    service = _calendar_service()
    body = _event_body(data)
    kwargs = {"calendarId": _calendar_id(), "body": body, "sendUpdates": "all"}
    if not body.get("extendedProperties", {}).get("private", {}).get("meeting_link"):
        body["conferenceData"] = {"createRequest": {
            "requestId": uuid.uuid4().hex,
            "conferenceSolutionKey": {"type": "hangoutsMeet"},
        }}
        kwargs["conferenceDataVersion"] = 1
    return service.events().insert(**kwargs).execute()


def update_calendar_event(event_id: str, data: dict) -> dict:
    """Update an existing event in the configured Nexus CRM calendar."""
    if not event_id:
        raise RuntimeError("The selected calendar event has no Google event ID.")
    service = _calendar_service()
    body = _event_body(data)
    # PATCH preserves Google-generated conference data (e.g. an existing Meet URL)
    # when the user edits other event fields.
    return service.events().patch(
        calendarId=_calendar_id(), eventId=event_id, body=body, sendUpdates="all"
    ).execute()


def delete_calendar_event(event_id: str) -> None:
    """Cancel an event in the configured Nexus CRM calendar."""
    if not event_id:
        raise RuntimeError("The selected calendar event has no Google event ID.")
    service = _calendar_service()
    service.events().delete(
        calendarId=_calendar_id(), eventId=event_id, sendUpdates="all"
    ).execute()

def send_email(recipients, subject: str, body: str):
    """Send a plain-text email using SMTP settings loaded from the local .env."""
    recipients = list(dict.fromkeys(e.strip() for e in recipients if e and e.strip()))
    if not recipients:
        raise RuntimeError("Enter at least one valid recipient email address.")
    required = ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM")
    missing = [key for key in required if not os.getenv(key, "").strip()]
    if missing:
        raise RuntimeError(
            "Email is not configured. Add these settings to your local .env: " + ", ".join(missing)
        )
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT must be a number, usually 587 or 465.") from exc
    message = EmailMessage()
    message["From"] = os.environ["SMTP_FROM"].strip()
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject.strip() or "Nexus CRM invitation"
    message.set_content(body.strip())
    host = os.environ["SMTP_HOST"].strip()
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=25) as server:
                server.login(os.environ["SMTP_USERNAME"].strip(), os.environ["SMTP_PASSWORD"])
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=25) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(os.environ["SMTP_USERNAME"].strip(), os.environ["SMTP_PASSWORD"])
                server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise RuntimeError(f"Email could not be sent ({exc.__class__.__name__}). Check SMTP settings and provider security settings.") from exc
    return len(recipients)
