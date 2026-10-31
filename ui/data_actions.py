"""Consistent refresh/CRUD/Excel-export controls for database pages."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QWidget
from ui.widgets import NeonButton
from ui.dialogs import show_message


def build_data_actions(accent, on_refresh, on_add, on_edit, on_export, parent=None, on_delete=None):
    """Consistent CRUD/export actions with Refresh aligned at the far right."""
    box = QWidget(parent)
    row = QHBoxLayout(box)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(8)
    add = NeonButton('Add record', accent, icon='plus', height=40)
    edit = NeonButton('Edit selected', accent, icon='edit', variant='ghost', height=40)
    export = NeonButton('Export Excel', accent, icon='download', variant='ghost', height=40)
    add.clicked.connect(on_add)
    edit.clicked.connect(on_edit)
    row.addWidget(add)
    row.addWidget(edit)
    if on_delete is not None:
        delete = NeonButton('Delete selected', '#FF5C7A', icon='cross', variant='ghost', height=40)
        delete.clicked.connect(on_delete)
        row.addWidget(delete)
    row.addWidget(export)
    row.addStretch(1)
    refresh = NeonButton('Refresh', accent, icon='refresh', variant='ghost', height=40)
    refresh.clicked.connect(on_refresh)
    row.addWidget(refresh)
    return box


def export_excel(parent, headers, rows, default_name):
    """Export the currently visible records to a formatted Excel workbook."""
    name = default_name if default_name.lower().endswith('.xlsx') else f'{default_name}.xlsx'
    path, _ = QFileDialog.getSaveFileName(parent, 'Export records to Excel', name, 'Excel workbooks (*.xlsx)')
    if not path:
        return
    if not path.lower().endswith('.xlsx'):
        path += '.xlsx'
    try:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'CRM Records'
        sheet.append(list(headers))
        for row in rows:
            sheet.append([None if value is None else value for value in row])
        header_fill = PatternFill('solid', fgColor='17305A')
        for cell in sheet[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = header_fill
            cell.alignment = Alignment(vertical='center', wrap_text=True)
        sheet.freeze_panes = 'A2'
        if headers:
            sheet.auto_filter.ref = sheet.dimensions
        for column_index, header in enumerate(headers, start=1):
            values = [str(header or '')]
            values.extend(str(sheet.cell(r, column_index).value or '') for r in range(2, sheet.max_row + 1))
            width = min(max(max((len(value) for value in values), default=10) + 2, 12), 48)
            sheet.column_dimensions[get_column_letter(column_index)].width = width
        sheet.row_dimensions[1].height = 30
        workbook.save(path)
        show_message(parent, 'Export complete', f'Exported {len(rows)} records to Excel:\n{path}', 'info', getattr(parent, 'accent', None))
    except Exception as exc:
        show_message(parent, 'Export failed', f'Could not create the Excel file ({exc.__class__.__name__}). Check the destination and try again.', 'error', getattr(parent, 'accent', None))
