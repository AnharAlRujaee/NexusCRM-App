"""Administrator workspace: live CRM overview, linked participants and calendar operations."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QComboBox, QDateTimeEdit, QFormLayout, QHBoxLayout, QTabWidget,
    QDialog, QTextEdit, QVBoxLayout, QWidget,
)

from core.communication import (
    create_calendar_event, delete_calendar_event, fetch_calendar_events,
    send_email, update_calendar_event,
)
from core.data_store import (
    DataError, _db, ensure_extended_schema, load_admin_contacts,
    load_applications, load_interviews, load_mentor, load_trainees,
)
from ui.base_page import BasePage
from ui.data_table import DataTable
from ui.dialogs import confirm_message, show_message
from ui.theme import ACCENTS, BAD, OK, TEXT, TEXT_DIM, WARN, page_style, tab_style
from ui.widgets import GlassPanel, NeonButton, NeonLineEdit, PageHeader, StatusChip, make_label


class MailComposeDialog(QDialog):
    """Branded participant email composer."""
    def __init__(self, accent, parent=None, recipients="", subject="", body=""):
        super().__init__(parent)
        self.accent = accent
        self.setWindowTitle("Participant mail · Nexus CRM")
        self.setMinimumSize(620, 560)
        self.resize(700, 620)
        self.setModal(True)
        self.setStyleSheet(page_style(accent) + "QDialog { background: #0A1230; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)
        root.addWidget(PageHeader("mail", "ADMIN COMMUNICATION", "Participant invitation",
                                  "Review recipients and message details before sending.", accent))
        panel = GlassPanel(accent, radius=16)
        form = QFormLayout(panel)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)
        self.recipients = NeonLineEdit("name@example.com, another@example.com", "mail", accent)
        self.recipients.setText(recipients)
        self.subject = NeonLineEdit("Interview / meeting invitation", "edit", accent)
        self.subject.setText(subject)
        self.body = QTextEdit()
        self.body.setPlainText(body)
        self.body.setMinimumHeight(190)
        for label, widget in (("RECIPIENTS", self.recipients), ("SUBJECT", self.subject), ("MESSAGE", self.body)):
            form.addRow(make_label(label, 10, accent, True, 1.5, mono=True), widget)
        root.addWidget(panel, 1)
        root.addWidget(make_label("Emails are sent only after you confirm. Check all addresses before sending.", 11, TEXT_DIM, wrap=True))
        buttons = QHBoxLayout(); buttons.addStretch(1)
        cancel = NeonButton("Cancel", accent, icon="cross", variant="ghost"); cancel.clicked.connect(self.reject)
        send = NeonButton("Send email", accent, icon="mail"); send.clicked.connect(self.accept)
        buttons.addWidget(cancel); buttons.addWidget(send); root.addLayout(buttons)

    def values(self):
        recipients = [x.strip() for x in re.split(r"[,;\n]+", self.recipients.text()) if x.strip()]
        return recipients, self.subject.text().strip(), self.body.toPlainText().strip()


class CalendarEventDialog(QDialog):
    """Create/edit dialog with participant fields linked to the live CRM directory."""
    def __init__(self, accent, contacts, parent=None, event=None):
        super().__init__(parent)
        self.accent = accent
        self.contacts = contacts or []
        self._loading_contact = False
        self.setWindowTitle("Calendar event · Nexus CRM")
        self.setMinimumSize(650, 680)
        self.resize(760, 760)
        self.setModal(True)
        self.setStyleSheet(page_style(accent) + "QDialog { background: #0A1230; }")

        root = QVBoxLayout(self); root.setContentsMargins(22, 18, 22, 18); root.setSpacing(12)
        heading = "Edit calendar event" if event else "Create calendar event"
        root.addWidget(PageHeader("calendar", "NEXUS CRM · CALENDAR", heading,
                                  "Participant details are linked to the live trainee/application directory.", accent))
        panel = GlassPanel(accent, radius=16)
        form = QFormLayout(panel); form.setContentsMargins(20, 18, 20, 18); form.setSpacing(10)

        self.summary = NeonLineEdit("Interview / meeting title", "edit", accent)
        self.event_type = QComboBox(); self.event_type.addItems(["Interview", "Mentor meeting", "Follow-up", "Workshop", "Other"])
        self.contact = QComboBox(); self.contact.setMinimumHeight(44)
        self.contact.addItem("Select a CRM participant…", None)
        for person in self.contacts:
            label = str(person.get("full_name") or "Unnamed")
            if person.get("email"):
                label += f"  ·  {person['email']}"
            self.contact.addItem(label, person)
        self.contact.activated.connect(self._populate_contact)

        self.participant_name = NeonLineEdit("Applicant / trainee name", "user", accent)
        self.participant_email = NeonLineEdit("participant@example.com", "mail", accent)
        self.participant_phone = NeonLineEdit("Phone number", "user", accent)
        self.mentor_name = NeonLineEdit("Assigned mentor / staff member", "user", accent)
        self.start = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.start.setCalendarPopup(True); self.start.setDisplayFormat("ddd, dd MMM yyyy · HH:mm"); self.start.setMinimumHeight(44)
        self.end = QDateTimeEdit(QDateTime.currentDateTime().addSecs(6300))
        self.end.setCalendarPopup(True); self.end.setDisplayFormat("ddd, dd MMM yyyy · HH:mm"); self.end.setMinimumHeight(44)
        self.meeting_link = NeonLineEdit("https://… (Teams / Meet / Zoom)", "arrow", accent)
        self.location = NeonLineEdit("Office / online / other location", "calendar", accent)
        self.description = QTextEdit(); self.description.setPlaceholderText("Agenda, preparation notes or additional details…")
        self.description.setMinimumHeight(100)

        for label, widget in (
            ("MEETING TITLE", self.summary), ("MEETING TYPE", self.event_type),
            ("LINK FROM CRM", self.contact), ("PARTICIPANT NAME", self.participant_name),
            ("PARTICIPANT EMAIL", self.participant_email), ("PHONE NUMBER", self.participant_phone),
            ("MENTOR / STAFF", self.mentor_name), ("START", self.start), ("END", self.end),
            ("MEETING LINK", self.meeting_link), ("LOCATION", self.location),
            ("DESCRIPTION", self.description),
        ):
            form.addRow(make_label(label, 10, accent, True, 1.3, mono=True), widget)
        root.addWidget(panel, 1)
        root.addWidget(make_label("Saving creates or updates the event in your separate Nexus CRM Google Calendar.", 11, TEXT_DIM, wrap=True))
        buttons = QHBoxLayout(); buttons.addStretch(1)
        cancel = NeonButton("Cancel", accent, icon="cross", variant="ghost"); cancel.clicked.connect(self.reject)
        save = NeonButton("Save event", accent, icon="check"); save.clicked.connect(self._validate)
        buttons.addWidget(cancel); buttons.addWidget(save); root.addLayout(buttons)

        if event:
            self.summary.setText(event.get("summary", ""))
            typ = event.get("event_type", "Meeting")
            idx = self.event_type.findText(typ)
            if idx < 0:
                self.event_type.addItem(typ); idx = self.event_type.findText(typ)
            self.event_type.setCurrentIndex(idx)
            self.participant_name.setText(event.get("participant_name", ""))
            self.participant_email.setText(event.get("participant_email", ""))
            self.participant_phone.setText(event.get("participant_phone", ""))
            self.mentor_name.setText(event.get("mentor_name", ""))
            self.meeting_link.setText(event.get("meeting_link", ""))
            self.location.setText(event.get("location", ""))
            description = event.get("description", "")
            description = re.sub(r"\n?Meeting link\s*:\s*https?://\S+", "", description, flags=re.I).strip()
            self.description.setPlainText(description)
            self._set_datetime(self.start, event.get("start"))
            self._set_datetime(self.end, event.get("end"))
            participant_id = str(event.get("participant_id") or "")
            email = (event.get("participant_email") or "").casefold()
            for i in range(1, self.contact.count()):
                person = self.contact.itemData(i) or {}
                same_id = participant_id and str(person.get("trainee_id")) == participant_id
                same_email = email and str(person.get("email") or "").casefold() == email
                if same_id or same_email:
                    self.contact.setCurrentIndex(i)
                    if same_id:
                        self.participant_name.setText(person.get("full_name") or self.participant_name.text())
                        self.participant_email.setText(person.get("email") or self.participant_email.text())
                        self.participant_phone.setText(person.get("phone") or self.participant_phone.text())
                    break

    @staticmethod
    def _set_datetime(widget, value):
        if not value:
            return
        try:
            dt = QDateTime.fromString(str(value), Qt.DateFormat.ISODate)
            if not dt.isValid():
                dt = QDateTime.fromString(str(value), Qt.DateFormat.ISODateWithMs)
            if not dt.isValid() and len(str(value)) == 10:
                dt = QDateTime.fromString(str(value) + "T09:00:00", Qt.DateFormat.ISODate)
            if dt.isValid():
                widget.setDateTime(dt.toLocalTime())
        except Exception:
            pass

    def _populate_contact(self, index):
        if self._loading_contact:
            return
        person = self.contact.itemData(index)
        if not person:
            return
        self._loading_contact = True
        self.participant_name.setText(person.get("full_name") or "")
        self.participant_email.setText(person.get("email") or "")
        self.participant_phone.setText(person.get("phone") or "")
        if person.get("mentor_names") and not self.mentor_name.text().strip():
            self.mentor_name.setText(person.get("mentor_names"))
        self._loading_contact = False

    def _validate(self):
        if not self.summary.text().strip():
            show_message(self, "Meeting title required", "Enter a title for this calendar event.", "warning", self.accent)
            self.summary.setFocus(); return
        if self.end.dateTime() <= self.start.dateTime():
            show_message(self, "Invalid meeting time", "The end time must be later than the start time.", "warning", self.accent)
            self.end.setFocus(); return
        email = self.participant_email.text().strip()
        if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            show_message(self, "Invalid email address", "Enter a valid participant email address or leave the field empty.", "warning", self.accent)
            self.participant_email.setFocus(); return
        link = self.meeting_link.text().strip()
        if link and not re.match(r"^https?://", link, re.I):
            show_message(self, "Invalid meeting link", "Meeting links must start with https:// or http://.", "warning", self.accent)
            self.meeting_link.setFocus(); return
        self.accept()

    def values(self):
        return {
            "summary": self.summary.text().strip(),
            "event_type": self.event_type.currentText(),
            "participant_name": self.participant_name.text().strip(),
            "participant_email": self.participant_email.text().strip(),
            "participant_phone": self.participant_phone.text().strip(),
            "participant_id": str((self.contact.currentData() or {}).get("trainee_id", "")),
            "mentor_name": self.mentor_name.text().strip(),
            "start": self.start.dateTime().toPyDateTime().astimezone().isoformat(),
            "end": self.end.dateTime().toPyDateTime().astimezone().isoformat(),
            "meeting_link": self.meeting_link.text().strip(),
            "location": self.location.text().strip(),
            "description": self.description.toPlainText().strip(),
        }


class AdminPage(BasePage):
    """Central administrator dashboard for PostgreSQL records and calendar events."""
    EVENT_HEADERS = ["Date & time", "Type", "Applicant / Trainee", "Email", "Phone",
                     "Mentor / Staff", "Meeting link", "Status", "Meeting"]

    def __init__(self, nav):
        super().__init__(nav, ACCENTS["admin"], "admin", "ADMIN WORKSPACE")
        header = PageHeader("admin", "SYSTEM OVERVIEW", "Database administration",
                            "Coordinate live CRM records, participant communication and Google Calendar events.", self.accent)
        header.add_chip(StatusChip("ADMIN TOOLS", self.accent))
        self.root.addWidget(header); self.reveal(header)

        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setStyleSheet(tab_style(self.accent))
        self.overview_tab = QWidget(); ov = QVBoxLayout(self.overview_tab)
        ov.setContentsMargins(10, 14, 10, 10); ov.setSpacing(12)
        panel = GlassPanel(self.accent, radius=16); layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20); layout.setSpacing(12)
        layout.addWidget(make_label("DATABASE STATUS", 11, self.accent, True, 2.0, mono=True))
        self.status_label = make_label("Checking database…", 14, TEXT_DIM); self.status_label.setWordWrap(True); layout.addWidget(self.status_label)
        self.summary_label = make_label("", 12, TEXT_DIM); self.summary_label.setWordWrap(True); layout.addWidget(self.summary_label)
        self.overview_table = DataTable(self.accent); self.overview_table.setMinimumHeight(220); layout.addWidget(self.overview_table, 1)
        actions = QHBoxLayout(); self.refresh_button = NeonButton("Refresh overview", self.accent, icon="refresh")
        self.refresh_button.clicked.connect(self.reload); actions.addWidget(self.refresh_button); actions.addStretch(); layout.addLayout(actions)
        ov.addWidget(panel, 1); self.tabs.addTab(self.overview_tab, "Overview")

        self.calendar_tab = QWidget(); cal = QVBoxLayout(self.calendar_tab)
        cal.setContentsMargins(10, 14, 10, 10); cal.setSpacing(10)
        intro = GlassPanel(self.accent, radius=16); intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(20, 14, 20, 14); intro_layout.setSpacing(5)
        intro_layout.addWidget(make_label("CALENDAR EVENTS & PARTICIPANT COORDINATION", 11, self.accent, True, 1.8, mono=True))
        intro_layout.addWidget(make_label("Events are stored in your separate Nexus CRM Google Calendar. Participant details are matched to live CRM records by email.", 12, TEXT_DIM, wrap=True))
        cal.addWidget(intro)

        filters_panel = GlassPanel(self.accent, radius=14); filters = QHBoxLayout(filters_panel)
        filters.setContentsMargins(12, 8, 12, 8); filters.setSpacing(8)
        self.search = NeonLineEdit("Search name, email, phone, mentor, meeting or link…", "search", self.accent)
        self.search.textChanged.connect(self.refresh_event_table); filters.addWidget(self.search, 1)
        self.type_filter = QComboBox(); self.type_filter.addItems(["All types", "Interview", "Mentor meeting", "Follow-up", "Workshop", "Meeting", "Other"])
        self.type_filter.currentTextChanged.connect(self.refresh_event_table); filters.addWidget(self.type_filter)
        self.date_filter = QComboBox(); self.date_filter.addItems(["All upcoming", "Next 7 days", "Next 30 days"])
        self.date_filter.currentTextChanged.connect(self.refresh_event_table); filters.addWidget(self.date_filter)
        self.status_filter = QComboBox(); self.status_filter.addItems(["All status", "Scheduled", "Cancelled"])
        self.status_filter.currentTextChanged.connect(self.refresh_event_table); filters.addWidget(self.status_filter)
        cal.addWidget(filters_panel)

        self.calendar_status = make_label("Calendar events have not been loaded yet.", 12, TEXT_DIM, wrap=True)
        cal.addWidget(self.calendar_status)
        self.events_table = DataTable(self.accent); self.events_table.setMinimumHeight(300)
        self.events_table.record_activated.connect(self.edit_selected_event)
        cal.addWidget(self.events_table, 1)
        tools = QHBoxLayout(); tools.setSpacing(8)
        self.new_event_button = NeonButton("New meeting", self.accent, icon="plus"); self.new_event_button.clicked.connect(self.create_event)
        self.edit_event_button = NeonButton("Edit selected", self.accent, icon="edit", variant="ghost"); self.edit_event_button.clicked.connect(self.edit_selected_event)
        self.cancel_event_button = NeonButton("Cancel event", BAD, icon="cross", variant="ghost"); self.cancel_event_button.clicked.connect(self.cancel_selected_event)
        self.open_link_button = NeonButton("Open meeting link", self.accent, icon="arrow", variant="ghost"); self.open_link_button.clicked.connect(self.open_selected_link)
        self.email_button = NeonButton("Email participant", self.accent, icon="mail", variant="ghost"); self.email_button.clicked.connect(self.email_selected_participant)
        self.refresh_events_button = NeonButton("Refresh", self.accent, icon="refresh", variant="ghost"); self.refresh_events_button.clicked.connect(self.reload_events)
        for button in (self.new_event_button, self.edit_event_button, self.cancel_event_button,
                       self.open_link_button, self.email_button, self.refresh_events_button):
            tools.addWidget(button)
        cal.addLayout(tools)
        self.tabs.addTab(self.calendar_tab, "Calendar & Participants")
        self.root.addWidget(self.tabs, 1); self.reveal(self.tabs)
        self.add_row([self.back_button()], stretch_end=True)
        self._events = []; self._contacts = []

    def on_enter(self):
        super().on_enter(); self.reload(); self.reload_events(show_dialog=False)

    def reload(self):
        self.refresh_button.setEnabled(False)
        try:
            ensure_extended_schema()
            apps = load_applications(); mentors = load_mentor(); projects = load_interviews(); trainees = load_trainees()
            users = _db.fetch_one('SELECT COUNT(*) AS count FROM "Users"')
            counts = [("Applications", len(apps.rows), "Application pipeline"),
                      ("Trainees", len(trainees.rows), "Participant directory"),
                      ("Mentor records", len(mentors.rows), "Mentor assessments"),
                      ("Project tracking", len(projects.rows), "Project tracking"),
                      ("User accounts", int(users["count"]) if users else 0, "Authentication")]
            self.overview_table.set_data(["Module", "Records", "Purpose"], counts, center=("Records",))
            self.status_label.setText("Connected to PostgreSQL. Live data loaded successfully. Refresh reads existing records; it does not re-import Excel or overwrite data.")
            self.status_label.setStyleSheet(f"color: {OK}; background: transparent;")
            self.summary_label.setText("Live record counts · refreshed whenever you open this page or press Refresh overview.")
        except Exception as exc:
            message = str(exc) if isinstance(exc, DataError) else f"Database operation failed ({exc.__class__.__name__}). Check PostgreSQL and your local .env settings."
            self.status_label.setText(message); self.status_label.setStyleSheet(f"color: {BAD}; background: transparent;")
            self.summary_label.setText("No changes were made to your database. Check PostgreSQL and the local .env configuration.")
            self.overview_table.set_data(["Module", "Records", "Purpose"], [])
        finally:
            self.refresh_button.setEnabled(True)

    def reload_events(self, show_dialog=True):
        self.refresh_events_button.setEnabled(False)
        self.calendar_status.setText("Connecting to your Nexus CRM Google Calendar…")
        try:
            self._events = fetch_calendar_events()
            try:
                self._contacts = load_admin_contacts()
            except Exception:
                self._contacts = []
            self._enrich_events()
            self.refresh_event_table()
            self.calendar_status.setText(f"Loaded {len(self._events)} event(s) from the Nexus CRM calendar. Double-click a row to edit it.")
            self.calendar_status.setStyleSheet(f"color: {OK}; background: transparent;")
        except Exception as exc:
            self._events = []
            self.events_table.set_data(self.EVENT_HEADERS, [])
            self.calendar_status.setText(str(exc))
            self.calendar_status.setStyleSheet(f"color: {BAD}; background: transparent;")
            if show_dialog:
                show_message(self, "Google Calendar unavailable", str(exc) + "\n\nYour PostgreSQL overview remains available.", "warning", self.accent)
        finally:
            self.refresh_events_button.setEnabled(True)

    def _enrich_events(self):
        by_email = {str(p.get("email") or "").casefold(): p for p in self._contacts if p.get("email")}
        by_id = {str(p.get("trainee_id")): p for p in self._contacts if p.get("trainee_id") is not None}
        for event in self._events:
            email = str(event.get("participant_email") or "").casefold()
            person = by_id.get(str(event.get("participant_id") or ""))
            if person is None:
                if not email:
                    email = next((str(x).casefold() for x in event.get("attendees", []) if str(x).casefold() in by_email), "")
                person = by_email.get(email)
            if person:
                event["participant_id"] = str(person.get("trainee_id") or "")
                event["participant_name"] = person.get("full_name") or event.get("participant_name", "")
                event["participant_email"] = person.get("email") or event.get("participant_email", "")
                event["participant_phone"] = person.get("phone") or event.get("participant_phone", "")
                event["mentor_name"] = event.get("mentor_name") or person.get("mentor_names", "")
            elif email:
                event["participant_email"] = email

    def refresh_event_table(self, *_args):
        now = datetime.now().astimezone()
        query = self.search.text().strip().casefold()
        typ = self.type_filter.currentText()
        date_mode = self.date_filter.currentText()
        status_mode = self.status_filter.currentText()
        shown = []
        rows = []
        for i, event in enumerate(self._events):
            if typ != "All types" and event.get("event_type", "Meeting") != typ:
                continue
            if status_mode != "All status" and event.get("status", "Scheduled") != status_mode:
                continue
            try:
                start = datetime.fromisoformat(str(event.get("start", "")).replace("Z", "+00:00"))
                local_start = start.astimezone() if start.tzinfo else start
                if date_mode == "Next 7 days" and not (now <= local_start <= now + timedelta(days=7)):
                    continue
                if date_mode == "Next 30 days" and not (now <= local_start <= now + timedelta(days=30)):
                    continue
            except Exception:
                local_start = None
            fields = [event.get("summary", ""), event.get("event_type", ""), event.get("participant_name", ""),
                      event.get("participant_email", ""), event.get("participant_phone", ""), event.get("mentor_name", ""),
                      event.get("meeting_link", ""), event.get("status", ""), event.get("location", "")]
            if query and query not in " ".join(str(x or "") for x in fields).casefold():
                continue
            start_text = local_start.strftime("%Y-%m-%d %H:%M") if local_start else str(event.get("start", ""))
            rows.append([start_text, event.get("event_type", "Meeting"), event.get("participant_name", ""),
                         event.get("participant_email", ""), event.get("participant_phone", ""),
                         event.get("mentor_name", ""), event.get("meeting_link", ""), event.get("status", "Scheduled"),
                         event.get("summary", "")])
            shown.append(i)
        self.events_table.set_data(self.EVENT_HEADERS, rows, indices=shown,
                                   center=("Date & time", "Status"),
                                   max_widths={"Applicant / Trainee": 220, "Email": 220, "Phone": 140,
                                               "Mentor / Staff": 180, "Meeting link": 240, "Meeting": 220})
        if self._events:
            self.calendar_status.setText(f"Showing {len(shown)} of {len(self._events)} events · search and filters apply to this list.")

    def _selected_event(self):
        idx = self.events_table.selected_source_index()
        return self._events[idx] if idx is not None and 0 <= idx < len(self._events) else None

    def create_event(self):
        dialog = CalendarEventDialog(self.accent, self._contacts, self.window())
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            created = create_calendar_event(dialog.values())
            self.reload_events(show_dialog=False)
            self.nav.toast("Meeting added to Nexus CRM calendar", self.accent)
        except Exception as exc:
            show_message(self, "Could not create calendar event", str(exc), "error", self.accent)

    def edit_selected_event(self, *_args):
        event = self._selected_event()
        if not event:
            show_message(self, "Select a meeting", "Choose a calendar event before selecting Edit.", "warning", self.accent); return
        dialog = CalendarEventDialog(self.accent, self._contacts, self.window(), event)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            update_calendar_event(event.get("event_id"), dialog.values())
            self.reload_events(show_dialog=False)
            self.nav.toast("Calendar event updated", self.accent)
        except Exception as exc:
            show_message(self, "Could not update calendar event", str(exc), "error", self.accent)

    def cancel_selected_event(self):
        event = self._selected_event()
        if not event:
            show_message(self, "Select a meeting", "Choose a calendar event before cancelling it.", "warning", self.accent); return
        title = event.get("summary") or "this event"
        if not confirm_message(self, "Cancel calendar event", f"Cancel '{title}' in Google Calendar? Guests will receive an update.", self.accent, destructive=True):
            return
        try:
            delete_calendar_event(event.get("event_id"))
            self.reload_events(show_dialog=False)
            self.nav.toast("Calendar event cancelled", self.accent)
        except Exception as exc:
            show_message(self, "Could not cancel calendar event", str(exc), "error", self.accent)

    def open_selected_link(self):
        event = self._selected_event()
        if not event:
            show_message(self, "Select a meeting", "Choose a calendar event first.", "warning", self.accent); return
        url = event.get("meeting_link") or event.get("html_link")
        if not url:
            show_message(self, "No meeting link", "This event does not contain a meeting link. Edit the event to add one.", "info", self.accent); return
        QDesktopServices.openUrl(QUrl(url))

    def email_selected_participant(self):
        event = self._selected_event()
        if not event:
            show_message(self, "Select a meeting", "Choose a calendar event first.", "warning", self.accent); return
        recipients = list(dict.fromkeys(([event.get("participant_email")] if event.get("participant_email") else []) + event.get("attendees", [])))
        self._compose_mail(event, recipients)

    def invite_participants(self):
        self._compose_mail(None, [])

    def _compose_mail(self, event=None, recipients=None):
        recipients = recipients if recipients is not None else []
        if event:
            body = (f"Hello,\n\nYou are invited to the following event:\n\n"
                    f"Event: {event.get('summary', '')}\nWhen: {event.get('start', '')}\n"
                    f"Meeting link: {event.get('meeting_link', '')}\nLocation: {event.get('location', '')}\n\n"
                    f"{event.get('description', '')}\n\nBest regards")
            subject = f"Invitation: {event.get('summary', 'Nexus CRM event')}"
        else:
            body = "Hello,\n\nYou are invited to an interview / meeting.\n\nDate and time:\nMeeting link:\n\nBest regards"
            subject = "Invitation: interview / meeting"
        dialog = MailComposeDialog(self.accent, self.window(), ", ".join(x for x in recipients if x), subject, body)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        addresses, subject, body = dialog.values()
        if not addresses or not body:
            show_message(self, "Missing information", "Enter at least one recipient and a message before sending.", "warning", self.accent); return
        if not confirm_message(self, "Confirm email", f"Send this email to {len(addresses)} recipient(s)?\n\nSubject: {subject}", self.accent):
            return
        try:
            sent = send_email(addresses, subject, body)
            show_message(self, "Email sent", f"Email successfully sent to {sent} recipient(s).", "info", self.accent)
        except Exception as exc:
            show_message(self, "Could not send email", str(exc), "error", self.accent)
