from core.communication import _calendar_id, _event_body


def test_calendar_event_payload_links_participant_and_meeting_details():
    payload = _event_body({
        "summary": "Applicant interview",
        "event_type": "Interview",
        "participant_name": "Example Applicant",
        "participant_email": "applicant@example.com",
        "participant_phone": "+31 6 12345678",
        "participant_id": 27,
        "mentor_name": "Example Mentor",
        "start": "2026-11-02T10:00:00+01:00",
        "end": "2026-11-02T10:45:00+01:00",
        "meeting_link": "https://meet.google.com/abc-defg-hij",
        "location": "Online",
        "description": "Initial interview",
    })
    assert payload["summary"] == "Applicant interview"
    assert payload["attendees"] == [{"email": "applicant@example.com"}]
    assert payload["start"]["dateTime"].endswith("+01:00")
    assert payload["extendedProperties"]["private"]["participant_id"] == "27"
    assert "Meeting link: https://meet.google.com/abc-defg-hij" in payload["description"]


def test_calendar_event_payload_allows_events_without_participants():
    payload = _event_body({
        "summary": "Team planning",
        "start": "2026-11-02T10:00:00+01:00",
        "end": "2026-11-02T10:45:00+01:00",
    })
    assert payload["attendees"] == []
    assert payload["extendedProperties"]["private"]["nexus_crm"] == "1"


def test_calendar_id_refuses_to_use_personal_primary_calendar(monkeypatch):
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "primary")
    try:
        _calendar_id()
    except RuntimeError as exc:
        assert "primary personal calendar" in str(exc)
    else:
        raise AssertionError("The personal primary calendar must not be used")
