"""Reusable add/edit dialog styled consistently with Nexus CRM pages."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QFrame,
    QTextEdit, QScrollArea, QWidget, QLabel,
)
from ui.theme import page_style, TEXT, TEXT_DIM
from ui.widgets import NeonButton, make_label, GlassPanel, PageHeader, NeonLineEdit
from ui.dialogs import show_message

LONG_FIELDS = {
    'Motivation', 'Reasons for Applying to VIT', 'Notes', 'Current Status',
    'Desired IT Department(s)', 'Alternative Recommendation', 'Recommendation',
    'Processing Status', 'Internal Tracking 1', 'Internal Tracking 2', 'Internal Tracking 3',
}


class RecordEditorDialog(QDialog):
    """Shared, branded editor for database records across all CRM pages."""
    def __init__(self, title, headers, values=None, accent='#4F9BFF', parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(760, 780)
        self.setMinimumSize(580, 520)
        self.setModal(True)
        self.setStyleSheet(page_style(accent) + 'QDialog { background: #0A1230; }')
        self.fields = {}
        values = values or {}
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(14)
        header = PageHeader('edit', 'NEXUS CRM · RECORD MANAGEMENT', title,
                            'Update the fields below, then save your changes.', accent)
        root.addWidget(header)

        panel = GlassPanel(accent, radius=16)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)
        outer.addWidget(make_label('RECORD DETAILS', 10, accent, True, 1.8, mono=True))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: none; } QWidget { background: transparent; }')
        body = QWidget()
        form = QFormLayout(body)
        form.setContentsMargins(4, 4, 12, 4)
        form.setSpacing(12)
        for header_text in headers:
            initial = values.get(header_text)
            text = '' if initial is None else str(initial)
            label = make_label(header_text, 12, accent, True)
            label.setMinimumWidth(160)
            if header_text in LONG_FIELDS:
                widget = QTextEdit()
                widget.setPlainText(text)
                widget.setMinimumHeight(78)
                widget.setMaximumHeight(150)
                widget.setStyleSheet(
                    f'QTextEdit {{ background: rgba(6,11,28,200); color: {TEXT}; '
                    f'border: 1px solid rgba(110,140,230,70); border-radius: 12px; '
                    f'padding: 10px; font-size: 13px; }} QTextEdit:focus {{ border: 1px solid {accent}; }}'
                )
            else:
                icon = 'mail' if 'email' in header_text.casefold() else ('calendar' if 'date' in header_text.casefold() or 'timestamp' in header_text.casefold() else 'edit')
                widget = NeonLineEdit('', icon, accent)
                widget.setText(text)
                widget.setClearButtonEnabled(True)
                if header_text in ('Timestamp', 'Date', 'Project Sent Date', 'Project Received Date'):
                    widget.setPlaceholderText('YYYY-MM-DD or YYYY-MM-DD HH:MM')
                elif 'email' in header_text.casefold():
                    widget.setPlaceholderText('name@example.com')
                else:
                    widget.setPlaceholderText(f'Enter {header_text.lower()}')
            self.fields[header_text] = widget
            form.addRow(label, widget)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        root.addWidget(panel, 1)
        root.addWidget(make_label('Changes are saved to PostgreSQL only after you choose Save record.', 11, TEXT_DIM, wrap=True))

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = NeonButton('Cancel', accent, icon='cross', variant='ghost')
        cancel.clicked.connect(self.reject)
        save = NeonButton('Save record', accent, icon='check')
        save.clicked.connect(self._submit)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        buttons.addStretch(1)
        root.addLayout(buttons)

        # Center the editor over the parent window rather than opening at an
        # arbitrary screen position. The field labels themselves remain left-aligned.
        parent_window = parent.window() if parent is not None else None
        if parent_window is not None:
            self.adjustSize()
            self.move(parent_window.frameGeometry().center() - self.rect().center())

    def _submit(self):
        # Every CRM record is associated with a candidate/trainee name.
        name_key = next((key for key in ("Full Name", "Candidate Name") if key in self.fields), None)
        if name_key:
            widget = self.fields[name_key]
            value = widget.toPlainText().strip() if isinstance(widget, QTextEdit) else widget.text().strip()
            if not value:
                show_message(self, "Required Field Missing", f"Please enter {name_key} before saving.", "warning", self.accent)
                widget.setFocus()
                return
        self.accept()

    def values(self):
        result = {}
        for key, widget in self.fields.items():
            result[key] = widget.toPlainText().strip() if isinstance(widget, QTextEdit) else widget.text().strip()
        return result


def run_record_editor(title, headers, values, accent, parent, save_callback, error_title):
    """Run an editor and retry with preserved values if PostgreSQL rejects a save."""
    from core.data_store import DataError

    current_values = dict(values or {})
    while True:
        dialog = RecordEditorDialog(title, headers, current_values, accent, parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        current_values = dialog.values()
        try:
            save_callback(current_values)
            return True
        except DataError as exc:
            show_message(parent, error_title, str(exc), "error", accent)
            # Reopen the form with the user's entries intact so they can correct
            # a validation issue or retry after restoring the database connection.
