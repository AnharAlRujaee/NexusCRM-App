"""Trainee directory with PostgreSQL-backed add, edit, delete, refresh, and Excel export."""
from PyQt6.QtWidgets import QHBoxLayout
from core import filters
from core.data_store import DataError, Table, load_trainees, save_trainee, delete_record
from ui.base_page import BasePage
from ui.data_table import RecordDialog, build_table_panel, set_status
from ui.record_editor import run_record_editor
from ui.data_actions import build_data_actions, export_excel
from ui.dialogs import show_message, confirm_message
from ui.theme import ACCENTS, BAD, TEXT_DIM
from ui.widgets import GlassPanel, NeonButton, NeonLineEdit, PageHeader, StatusChip

class TraineesPage(BasePage):
    def __init__(self, nav):
        super().__init__(nav, ACCENTS['trainees'], 'trainees', 'TRAINEES')
        self.table_data = Table([], []); self.error = ''
        header = PageHeader('users', 'Directory', 'Trainees', 'Manage trainee contact details stored in PostgreSQL.', self.accent)
        header.add_chip(StatusChip('POSTGRESQL DATABASE', self.accent))
        self.root.addWidget(header); self.reveal(header)
        actions = build_data_actions(self.accent, self.reload, self.add_record, self.edit_selected, self.export_visible, self, on_delete=self.delete_selected)
        self.root.addWidget(actions); self.reveal(actions)
        search_panel = GlassPanel(self.accent, radius=16); row = QHBoxLayout(search_panel)
        row.setContentsMargins(14,6,14,6); row.setSpacing(8)
        self.search = NeonLineEdit('Search by name, email, phone, or postal code', 'search', self.accent)
        self.search.textChanged.connect(lambda _t: self.refresh()); row.addWidget(self.search,1)
        self.root.addWidget(search_panel); self.reveal(search_panel)
        panel, self.table, self.status = build_table_panel(self.accent)
        self.table.record_activated.connect(self.show_record)
        self.root.addWidget(panel,1); self.reveal(panel)
        self.add_row([self.back_button()], stretch_end=True)
    def on_enter(self):
        self.reload(); super().on_enter()
    def reload(self):
        try: self.table_data=load_trainees(); self.error=''
        except DataError as exc: self.table_data=Table([],[]); self.error=str(exc)
        self.refresh()
    def refresh(self):
        q=self.search.text().strip().casefold(); shown=[]
        for i,row in enumerate(self.table_data.rows):
            if not q or any(q in str(v or '').casefold() for v in row): shown.append(i)
        self.table.set_data(self.table_data.headers,[self.table_data.rows[i] for i in shown],indices=shown)
        if self.error: set_status(self.status,'⚠ '+self.error.upper(),BAD)
        else: set_status(self.status,f'SHOWING {len(shown)} OF {len(self.table_data.rows)} TRAINEES · DOUBLE-CLICK FOR DETAILS',TEXT_DIM)
    def add_record(self):
        saved = run_record_editor(
            'Add trainee', self.table_data.headers, {}, self.accent, self.window(),
            lambda values: save_trainee(values), 'Could not save trainee')
        if saved:
            self.reload()
            self.nav.toast('Trainee saved successfully', self.accent)

    def edit_selected(self):
        idx = self.table.selected_source_index()
        if idx is None or not 0 <= idx < len(self.table_data.rows):
            show_message(self, "No Record Selected", "Please select a record before clicking Edit.", "warning", self.accent)
            return
        record_id = self.table_data.row_ids[idx]
        values = dict(zip(self.table_data.headers, self.table_data.rows[idx]))
        saved = run_record_editor(
            'Edit trainee', self.table_data.headers, values, self.accent, self.window(),
            lambda updated: save_trainee(updated, record_id), 'Could not update trainee')
        if saved:
            self.reload()
            self.nav.toast('Trainee updated successfully', self.accent)
    def delete_selected(self):
        idx = self.table.selected_source_index()
        if idx is None or not 0 <= idx < len(self.table_data.rows):
            show_message(self, "No Record Selected", "Please select a record before clicking Delete.", "warning", self.accent)
            return
        if idx >= len(self.table_data.row_ids):
            show_message(self, "Cannot Delete Record", "The selected record has no database identifier. Refresh and try again.", "error", self.accent)
            return
        if not confirm_message(self, "Confirm deletion", "Delete the selected trainee? This action cannot be undone.", self.accent, destructive=True):
            return
        try:
            delete_record("trainee", self.table_data.row_ids[idx])
            self.reload()
            self.nav.toast("Trainee deleted", self.accent)
        except DataError as exc:
            show_message(self, "Could Not Delete Record", str(exc), "error", self.accent)

    def export_visible(self):
        q=self.search.text().strip().casefold()
        rows=[r for r in self.table_data.rows if not q or any(q in str(v or '').casefold() for v in r)]
        export_excel(self,self.table_data.headers,rows,'nexus_trainees.xlsx')
    def show_record(self,index):
        if 0<=index<len(self.table_data.rows):
            row=self.table_data.rows[index]
            RecordDialog('Trainee record',str(row[0] or 'Trainee'),self.table_data.headers,row,self.accent,self.window()).exec()
