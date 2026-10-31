"""Project Tracking page backed by PostgreSQL project-tracking records."""

from PyQt6.QtWidgets import QHBoxLayout

from core import filters
from core.data_store import DataError, Table, load_interviews, save_interview, delete_record
from ui.base_page import BasePage
from ui.data_table import RecordDialog, build_table_panel, set_status
from ui.record_editor import run_record_editor
from ui.data_actions import build_data_actions, export_excel
from ui.dialogs import show_message, confirm_message
from ui.theme import ACCENTS, BAD, WARN
from ui.widgets import (
    GlassPanel, NeonButton, NeonLineEdit, PageHeader, StatusChip,
)


class InterviewsPage(BasePage):
    def __init__(self, nav):
        super().__init__(nav, ACCENTS["interviews"], "interviews", "PROJECT TRACKING")
        self.mode = "all"
        self.table_data = Table([], [])
        self.error = ""
        self.i_name = self.i_sent = self.i_received = -1

        header = PageHeader(
            "interviews", "Module 03", "Project Tracking",
            "Track the project exchange stages.", self.accent)
        header.add_chip(StatusChip("POSTGRESQL DATABASE", self.accent))
        self.root.addWidget(header)
        self.reveal(header)
        actions_bar = build_data_actions(self.accent, self.reload, self.add_record, self.edit_selected, self.export_visible, self, on_delete=self.delete_selected)
        self.root.addWidget(actions_bar)
        self.reveal(actions_bar)

        # search
        search_panel = GlassPanel(self.accent, radius=16)
        sl = QHBoxLayout(search_panel)
        sl.setContentsMargins(14, 6, 14, 6)
        sl.setSpacing(8)
        self.search = NeonLineEdit("Search by name or surname \u2014 e.g. \u201cas\u201d", "search", self.accent)
        sl.addWidget(self.search, 1)
        search_btn = NeonButton("Search", self.accent, icon="search")
        search_btn.clicked.connect(lambda: self.refresh())
        self.search.returnPressed.connect(lambda: self.refresh())
        self.search.textChanged.connect(lambda _text: self.refresh())
        sl.addWidget(search_btn)
        self.root.addWidget(search_panel)
        self.reveal(search_panel)

        # Project Sent / Project Received filters
        self.filter_buttons = []
        for text, mode, icon in (
            ("All Project Records", "all", "list"),
            ("Projects Sent", "sent", "upload"),
            ("Projects Received", "received", "download"),
        ):
            b = NeonButton(text, self.accent, icon=icon, variant="ghost", height=42)
            b.setCheckable(True)
            b.clicked.connect(lambda _checked=False, m=mode: self.set_mode(m))
            self.filter_buttons.append((b, mode))
        self.filter_buttons[0][0].setChecked(True)
        self.add_row([b for b, _ in self.filter_buttons], stretch_end=True)

        # table
        panel, self.table, self.status = build_table_panel(self.accent)
        self.table.record_activated.connect(self.show_record)
        self.root.addWidget(panel, 1)
        self.reveal(panel)

        self.add_row([self.back_button()], stretch_end=True)

    # ------------------------------------------------------------------
    def on_enter(self):
        self.reload()
        super().on_enter()

    def reload(self):
        try:
            self.table_data = load_interviews()
            self.error = ""
        except DataError as exc:
            self.table_data = Table([], [])
            self.error = str(exc)
        t = self.table_data
        self.i_name = t.index("Full Name")
        self.i_sent = t.index("Project Sent Date")
        self.i_received = t.index("Project Received Date")
        self.refresh()

    def set_mode(self, mode):
        self.mode = mode
        for b, m in self.filter_buttons:
            b.setChecked(m == mode)
        self.refresh()

    def refresh(self):
        t = self.table_data
        query = self.search.text()

        shown = []
        for i, row in enumerate(t.rows):
            sent = row[self.i_sent] if self.i_sent >= 0 else None
            received = row[self.i_received] if self.i_received >= 0 else None
            if self.mode == "sent" and sent is None:
                continue
            if self.mode == "received" and received is None:
                continue
            name = row[self.i_name] if self.i_name >= 0 else None
            if query.strip() and not filters.name_matches(query, name):
                continue
            shown.append(i)

        self.table.set_data(
            t.headers, [t.rows[i] for i in shown], indices=shown,
            chip_fn=self._chip, center=("Project Sent Date", "Project Received Date"))

        if self.error:
            set_status(self.status, "\u26A0  " + self.error.upper(), BAD)
        else:
            set_status(
                self.status,
                f"SHOWING {len(shown)} OF {len(t.rows)} PROJECT RECORDS   \u00B7   "
                f"CLICK A HEADER TO SORT   \u00B7   DOUBLE-CLICK A ROW FOR DETAILS")

    def add_record(self):
        saved = run_record_editor(
            "Add project-tracking record", self.table_data.headers, {}, self.accent, self.window(),
            lambda values: save_interview(values), "Could not save project-tracking record")
        if saved:
            self.reload()
            self.nav.toast("Project-tracking record saved", self.accent)

    def edit_selected(self):
        idx = self.table.selected_source_index()
        if idx is None or not 0 <= idx < len(self.table_data.rows):
            show_message(self, "No Record Selected", "Please select a record before clicking Edit.", "warning", self.accent)
            return
        record_id = self.table_data.row_ids[idx]
        values = dict(zip(self.table_data.headers, self.table_data.rows[idx]))
        saved = run_record_editor(
            "Edit project-tracking record", self.table_data.headers, values, self.accent, self.window(),
            lambda updated: save_interview(updated, record_id), "Could not update project-tracking record")
        if saved:
            self.reload()
            self.nav.toast("Project-tracking record updated", self.accent)

    def delete_selected(self):
        idx = self.table.selected_source_index()
        if idx is None or not 0 <= idx < len(self.table_data.rows):
            show_message(self, "No Record Selected", "Please select a record before clicking Delete.", "warning", self.accent)
            return
        if idx >= len(self.table_data.row_ids):
            show_message(self, "Cannot Delete Record", "The selected record has no database identifier. Refresh and try again.", "error", self.accent)
            return
        if not confirm_message(self, "Confirm deletion", "Delete the selected project-tracking record? This action cannot be undone.", self.accent, destructive=True):
            return
        try:
            delete_record("project_tracking", self.table_data.row_ids[idx])
            self.reload()
            self.nav.toast("Project-tracking record deleted", self.accent)
        except DataError as exc:
            show_message(self, "Could Not Delete Record", str(exc), "error", self.accent)

    def export_visible(self):
        query = self.search.text().strip(); rows=[]
        for row in self.table_data.rows:
            sent = row[self.i_sent] if self.i_sent >= 0 else None
            received = row[self.i_received] if self.i_received >= 0 else None
            if self.mode == 'sent' and sent is None: continue
            if self.mode == 'received' and received is None: continue
            if query and not filters.name_matches(query, row[self.i_name] if self.i_name >= 0 else None): continue
            rows.append(row)
        export_excel(self, self.table_data.headers, rows, "nexus_project_tracking.xlsx")

    def _chip(self, header, value):
        """A missing date is a step that has not happened yet."""
        if value is None and header == "Project Sent Date":
            return ("NOT SENT", WARN)
        if value is None and header == "Project Received Date":
            return ("PENDING", WARN)
        return None

    def show_record(self, index):
        t = self.table_data
        if not 0 <= index < len(t.rows):
            return
        row = t.rows[index]
        name = row[self.i_name] if self.i_name >= 0 and row[self.i_name] else "Interview"
        RecordDialog("Project-tracking record", str(name).title(), t.headers, row,
                     self.accent, self.window()).exec()
