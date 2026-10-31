"""Page 4 - Applications (data from data/Applications.xlsx)."""

from PyQt6.QtWidgets import QHBoxLayout

from core import filters
from core.data_store import DataError, Table, load_applications, load_vit_cohorts, save_application, delete_record
from ui.base_page import BasePage
from ui.data_table import RecordDialog, build_table_panel, set_status
from ui.record_editor import run_record_editor
from ui.data_actions import build_data_actions, export_excel
from ui.dialogs import show_message, confirm_message
from ui.theme import ACCENTS, BAD, OK, TEXT_DIM, WARN
from ui.widgets import (
    GlassPanel, NeonButton, NeonComboBox, NeonLineEdit, PageHeader, StatusChip, make_label,
)

CENTERED = (
    "Application Period", "English Level", "Dutch Level", "Green Check",
    "Internal Tracking 1", "Internal Tracking 2", "Internal Tracking 3",
)

class ApplicationsPage(BasePage):
    VIEWS = [
        "All records", 
        "Duplicates only", 
        "Unique (duplicates removed)",
        "Previous VIT Check (In VIT1/VIT2)",
        "Different Record (Not in VIT1/VIT2)"
    ]

    def __init__(self, nav):
        super().__init__(nav, ACCENTS["applications"], "applications", "APPLICATIONS")
        self.mode = "all"
        self.table_data = Table([], [])
        self.error = ""
        self.dup_flags, self.first_flags = [], []
        self.i_name = self.i_email = self.i_mentor = -1
        self.vit_labels = []
        self.vit_rows = []
        self.vit_table = None
        self.vit_data_error = ""
        self._shown_headers = []
        self._shown_rows = []

        header = PageHeader(
            "apps", "Module 01", "Application pipeline",
            "Search, filter and review every application record.", self.accent)
        header.add_chip(StatusChip("POSTGRESQL DATABASE", self.accent))
        self.root.addWidget(header)
        self.reveal(header)
        actions = build_data_actions(self.accent, self.reload, self.add_record, self.edit_selected, self.export_visible, self, on_delete=self.delete_selected)
        self.root.addWidget(actions)
        self.reveal(actions)

        # search + record view
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
        sl.addSpacing(10)
        sl.addWidget(make_label("RECORDS", 11, TEXT_DIM, True, 2.2, mono=True))
        
        self.view = NeonComboBox(self.accent)
        self.view.addItems(self.VIEWS)
        self.view.setMinimumWidth(330)
        self.view.currentIndexChanged.connect(lambda _i: self.refresh())
        sl.addWidget(self.view)
        
        self.root.addWidget(search_panel)
        self.reveal(search_panel)

        # mentor-meeting filters
        self.filter_buttons = []
        for text, mode, icon in (
            ("All Applications", "all", "list"),
            ("Mentor Meeting Defined", "defined", "check"),
            ("Mentor Meeting Not Defined", "not_defined", "cross"),
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

    def on_enter(self):
        self.reload()
        super().on_enter()

    def reload(self):
        try:
            self.table_data = load_applications()
            self.error = ""
        except DataError as exc:
            self.table_data = Table([], [])
            self.error = str(exc)
            
        t = self.table_data
        self.i_name = t.index("Full Name")
        self.i_email = t.index("Email")
        self.i_mentor = t.index("Mentor Meeting")

        self.vit_rows = []
        self.vit_table = None
        self.vit_data_error = ""
        try:
            mentor = load_vit_cohorts()
            self.vit_table = mentor
            i_candidate = mentor.index("Candidate Name")
            i_group = mentor.index("VIT Group")
            self.vit_rows = mentor.rows
            self.vit_labels = filters.previous_vit_labels(
                t.rows, self.i_name,
                filters.vit_cohort_names(mentor.rows, i_candidate, i_group),
            )
            cohorts = filters.vit_cohort_names(mentor.rows, i_candidate, i_group)
            if not cohorts["VIT1"] and not cohorts["VIT2"]:
                found = sorted({str(row[i_group]).strip() for row in mentor.rows
                                if i_group >= 0 and row[i_group]})
                groups = ", ".join(found) if found else "none"
                self.vit_data_error = (
                    f"Mentor.xlsx has no VIT1/VIT2 candidates (VIT Group values: {groups})"
                )
        except DataError as exc:
            self.vit_data_error = str(exc)
            self.vit_labels = [""] * len(t.rows)

        if hasattr(filters, "duplicate_flags"):
            self.dup_flags, self.first_flags = filters.duplicate_flags(t.rows, self.i_name, self.i_email)
        else:
            self.dup_flags = [False] * len(t.rows)
            self.first_flags = [True] * len(t.rows)

        self.refresh()

    def set_mode(self, mode):
        self.mode = mode
        for b, m in self.filter_buttons:
            b.setChecked(m == mode)
        self.refresh()

    def _has_meeting(self, row):
        value = row[self.i_mentor] if self.i_mentor >= 0 else None
        return value is not None and str(value).strip().upper() in {"OK", "YES", "DEFINED", "TRUE", "DONE"}
        
    def refresh(self):
        t = self.table_data
        query = self.search.text()
        view = self.view.currentIndex()

        if view in (3, 4) and self.vit_data_error:
            self._shown_headers = list(t.headers)
            self._shown_rows = []
            self.table.set_data(self._shown_headers, [])
            set_status(self.status, "\u26A0  " + self.vit_data_error.upper(), WARN)
            return

        shown = []
        if view == 4:
            mentor = self.vit_table
            if mentor is None:
                set_status(self.status, "\u26A0  " + self.vit_data_error.upper(), BAD)
                self.table.set_data([], [])
                return
            records = filters.different_vit_records(
                mentor.rows, mentor.index("Candidate Name"),
                mentor.index("Email"), mentor.index("VIT Group"),
                email_by_name={
                    str(row[self.i_name]).strip().casefold(): row[self.i_email]
                    for row in self.table_data.rows
                    if self.i_name >= 0 and self.i_email >= 0
                    and row[self.i_name] and row[self.i_email]
                },
            )
            records = [row for row in records
                       if not query.strip() or filters.name_matches(query, row[0])]
            self._shown_headers = ["Full Name", "Email", "Found Only In"]
            self._shown_rows = records
            self.table.set_data(self._shown_headers, records, center=("Found Only In",))
            set_status(
                self.status,
                f"{len(records)} PEOPLE APPEAR IN ONLY ONE OF VIT1 / VIT2   \u00B7   "
                "SOURCE: MENTOR.XLSX",
            )
            return

        for i, row in enumerate(t.rows):
            if self.mode == "defined" and not self._has_meeting(row):
                continue
            if self.mode == "not_defined" and self._has_meeting(row):
                continue
                
            if view == 1 and not self.dup_flags[i]: 
                continue
            if view == 2 and not self.first_flags[i]:
                continue
            if view == 3 and not self.vit_labels[i]:
                continue
                
            name = row[self.i_name] if self.i_name >= 0 else None
            if hasattr(filters, "name_matches"):
                if query.strip() and not filters.name_matches(query, name):
                    continue
            else:
                if query.strip() and query.casefold() not in str(name).casefold():
                    continue
                    
            shown.append(i)

        headers = list(t.headers)
        rows = [t.rows[i] for i in shown]
        if view == 3:
            headers.append("Previous VIT")
            rows = [row + [self.vit_labels[index]] for index, row in zip(shown, rows)]
        self._shown_headers = headers
        self._shown_rows = rows
        self.table.set_data(
            headers, rows, indices=shown,
            chip_fn=self._chip, center=CENTERED)

        if self.error:
            set_status(self.status, "\u26A0  " + self.error.upper(), BAD)
        else:
            dups = sum(1 for flag in self.dup_flags if flag)
            note = f"   \u00B7   {self.vit_data_error}" if self.vit_data_error and view not in (3, 4) else ""
            set_status(
                self.status,
                f"SHOWING {len(shown)} OF {len(t.rows)} APPLICATIONS   \u00B7   "
                f"{dups} DUPLICATE ROWS   \u00B7   CLICK A HEADER TO SORT   \u00B7   "
                f"DOUBLE-CLICK A ROW FOR FULL DETAILS" + note,
                WARN if note else TEXT_DIM)

    def add_record(self):
        saved = run_record_editor(
            "Add application", self.table_data.headers, {}, self.accent, self.window(),
            lambda values: save_application(values), "Could not save application")
        if saved:
            self.reload()
            self.nav.toast("Application saved successfully", self.accent)

    def edit_selected(self):
        source_index = self.table.selected_source_index()
        if source_index is None or self.view.currentIndex() == 4:
            show_message(self, "No Record Selected", "Please select a record before clicking Edit. The VIT comparison view is read-only.", "warning", self.accent)
            return
        if not 0 <= source_index < len(self.table_data.rows):
            show_message(self, "Record Not Found", "The selected record could not be found. Refresh and try again.", "warning", self.accent)
            return
        values = dict(zip(self.table_data.headers, self.table_data.rows[source_index]))
        record_id = self.table_data.row_ids[source_index]
        saved = run_record_editor(
            "Edit application", self.table_data.headers, values, self.accent, self.window(),
            lambda updated: save_application(updated, record_id), "Could not update application")
        if saved:
            self.reload()
            self.nav.toast("Application updated successfully", self.accent)

    def delete_selected(self):
        if self.view.currentIndex() == 4:
            show_message(self, "Read-Only View", "Records cannot be deleted from the VIT comparison view. Switch to an application list first.", "warning", self.accent)
            return
        idx = self.table.selected_source_index()
        if idx is None or not 0 <= idx < len(self.table_data.rows):
            show_message(self, "No Record Selected", "Please select a record before clicking Delete.", "warning", self.accent)
            return
        if idx >= len(self.table_data.row_ids):
            show_message(self, "Cannot Delete Record", "The selected record has no database identifier. Refresh and try again.", "error", self.accent)
            return
        if not confirm_message(self, "Confirm deletion", "Delete the selected application? This action cannot be undone.", self.accent, destructive=True):
            return
        try:
            delete_record("application", self.table_data.row_ids[idx])
            self.reload()
            self.nav.toast("Application deleted", self.accent)
        except DataError as exc:
            show_message(self, "Could Not Delete Record", str(exc), "error", self.accent)

    def export_visible(self):
        export_excel(self, self._shown_headers, self._shown_rows, "nexus_applications.xlsx")

    def _chip(self, header, value):
        if value is None:
            return None
        text = str(value).strip().upper()
        if header == "Mentor Meeting":
            return (text, OK if text == "OK" else WARN)
        if header == "Processing Status":
            return (text, OK if text == "DONE" else WARN)
        if header == "Application Period":
            return (text, self.accent)
        return None

    def show_record(self, index):
        if self.view.currentIndex() == 4:
            if not 0 <= index < len(self._shown_rows):
                return
            row = self._shown_rows[index]
            RecordDialog("VIT comparison record", str(row[0]).title(),
                         self._shown_headers, row, self.accent, self.window()).exec()
            return
        t = self.table_data
        if not 0 <= index < len(t.rows):
            return
        row = t.rows[index]
        name = row[self.i_name] if self.i_name >= 0 and row[self.i_name] else "Application"
        RecordDialog("Application record", str(name).title(), t.headers, row,
                     self.accent, self.window()).exec()