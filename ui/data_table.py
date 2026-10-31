"""Professional data table for the spreadsheet-backed pages.

* shows every column of the workbook, in workbook order
* column widths fit the content (capped), with horizontal scrolling when the
  table is wider than the window - and stretch to fill the space when it is not
* click a header to sort (numbers and dates sort properly, not as text)
* status cells are drawn as colour chips
* long text is elided in the cell and shown in full in a tooltip
* double-click a row to open every field of that record in a detail dialog
"""

import html
from datetime import datetime

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QScrollArea, QStyle,
    QStyledItemDelegate, QStyleOptionViewItem, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from ui.theme import TEXT, TEXT_DIM, TEXT_FAINT, flags, mix, page_style, qcolor, ui_font
from ui.widgets import GlassPanel, NeonButton, PageHeader, make_label, style_table

ROW_ROLE = int(Qt.ItemDataRole.UserRole.value) + 1    # index of the record in the source data
CHIP_ROLE = ROW_ROLE + 1                              # colour of the chip, when the cell is one

BODY_PX = 13
HEAD_PX = 11
ROW_HEIGHT = 42
HEADER_HEIGHT = 46
MIN_COL = 84
DEFAULT_MAX_COL = 300

_DATE_FORMATS = ("%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d")
_EPOCH = datetime(1970, 1, 1)


def sort_key(value):
    """Order values by their real type: blanks first, then numbers, dates, text."""
    if value is None or value == "":
        return (0, 0.0)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return (1, float(value))
    text = str(value).strip()
    for fmt in _DATE_FORMATS:
        try:
            return (2, (datetime.strptime(text, fmt) - _EPOCH).total_seconds())
        except ValueError:
            pass
    return (3, text.casefold())


class SortItem(QTableWidgetItem):
    """Table item that sorts by a typed key instead of by its display text."""

    def __init__(self, text, key):
        super().__init__(text)
        self._key = key

    def __lt__(self, other):
        if isinstance(other, SortItem):
            return self._key < other._key
        return super().__lt__(other)


class ChipDelegate(QStyledItemDelegate):
    """Draws cells that carry a CHIP_ROLE colour as rounded status pills."""

    def paint(self, painter, option, index):
        color = index.data(CHIP_ROLE)
        if not color:
            super().paint(painter, option, index)
            return

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        text = opt.text
        opt.text = ""
        widget = opt.widget
        style = widget.style() if widget is not None else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)

        centered = bool(opt.displayAlignment & Qt.AlignmentFlag.AlignHCenter)
        font = ui_font(11, True, 0.6)
        fm = QFontMetrics(font)
        rect = QRectF(opt.rect)
        height = 24.0
        width = min(fm.horizontalAdvance(text) + 24.0, rect.width() - 16.0)
        x = rect.center().x() - width / 2.0 if centered else rect.left() + 10.0
        chip = QRectF(x, rect.center().y() - height / 2.0, width, height)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(qcolor(color, 130), 1.0))
        painter.setBrush(qcolor(color, 34))
        painter.drawRoundedRect(chip, height / 2.0, height / 2.0)
        painter.setFont(font)
        painter.setPen(mix(color, QColor(255, 255, 255), 0.30))
        painter.drawText(chip, flags(Qt.AlignmentFlag.AlignCenter),
                         fm.elidedText(text, Qt.TextElideMode.ElideRight, int(width - 14)))
        painter.restore()


def _tooltip(text):
    return f"<table width='420'><tr><td>{html.escape(text)}</td></tr></table>"


class DataTable(QTableWidget):
    """Glass-styled, sortable, scrollable table (see module docstring)."""

    record_activated = pyqtSignal(int)      # source-row index of a double-clicked record

    def __init__(self, accent, parent=None):
        super().__init__(0, 0, parent)
        self._accent = accent
        self._headers = []
        self._center = set()
        self._natural = []
        self._auto_fit = True
        self._fitting = False
        self._sort_col = -1
        self._sort_asc = True

        self.setFont(ui_font(BODY_PX))
        style_table(self)

        head = self.horizontalHeader()
        head.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        head.setStretchLastSection(False)
        head.setMinimumSectionSize(MIN_COL)
        head.setFixedHeight(HEADER_HEIGHT)
        head.setFont(ui_font(HEAD_PX, True))
        head.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        head.setSectionsClickable(True)
        head.setCursor(Qt.CursorShape.PointingHandCursor)
        head.sectionClicked.connect(self._on_header_clicked)
        head.sectionResized.connect(self._on_section_resized)

        self.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setItemDelegate(ChipDelegate(self))
        self.cellDoubleClicked.connect(self._on_double_click)

    # -- filling ----------------------------------------------------------
    def set_data(self, headers, rows, indices=None, chip_fn=None, center=(), max_widths=None):
        """Show ``rows`` under ``headers``.

        indices   source-row number of each row (so a double-click can find the
                  full record even after filtering / sorting); defaults to 0..n
        chip_fn   chip_fn(header, value) -> (text, colour) to draw a status chip, or None
        center    header names whose cells are centred
        max_widths  {header: max pixel width} overriding the default cap
        """
        headers = list(headers)
        rows = list(rows)
        indices = list(indices) if indices is not None else list(range(len(rows)))
        max_widths = max_widths or {}
        self._headers = headers
        self._center = set(center)

        centered = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        body_fm = QFontMetrics(ui_font(BODY_PX))
        head_fm = QFontMetrics(ui_font(HEAD_PX, True))
        chip_fm = QFontMetrics(ui_font(11, True, 0.6))

        self._fitting = True
        self.setUpdatesEnabled(False)
        try:
            self.clearContents()
            self.setRowCount(0)
            self.setColumnCount(len(headers))
            self.setHorizontalHeaderLabels([h.upper() for h in headers])
            self.setRowCount(len(rows))

            # +44: header padding and room for the sort arrow
            natural = [head_fm.horizontalAdvance(h.upper()) + 44 for h in headers]

            for r, row in enumerate(rows):
                for c, value in enumerate(row[: len(headers)]):
                    header = headers[c]
                    chip = chip_fn(header, value) if chip_fn else None
                    if chip:
                        text, color = chip
                        needed = chip_fm.horizontalAdvance(text) + 24 + 24
                    else:
                        text = "\u2014" if value is None else str(value)
                        needed = body_fm.horizontalAdvance(text[:160]) + 30

                    item = SortItem(text, sort_key(value))
                    item.setData(ROW_ROLE, indices[r])
                    item.setTextAlignment(centered if header in self._center else left)
                    if chip:
                        item.setData(CHIP_ROLE, color)
                    elif value is None:
                        item.setForeground(QBrush(QColor(TEXT_FAINT)))
                    if len(text) > 30:
                        item.setToolTip(_tooltip(text))
                    self.setItem(r, c, item)
                    natural[c] = max(natural[c], needed)

            self._natural = [
                max(MIN_COL, min(w, max_widths.get(headers[c], DEFAULT_MAX_COL)))
                for c, w in enumerate(natural)
            ]
            for c, header in enumerate(headers):
                head_item = self.horizontalHeaderItem(c)
                if head_item is not None:
                    head_item.setTextAlignment(centered if header in self._center else left)

            if 0 <= self._sort_col < len(headers):
                self.sortItems(self._sort_col,
                               Qt.SortOrder.AscendingOrder if self._sort_asc else Qt.SortOrder.DescendingOrder)
            self._update_header_labels()
        finally:
            self.setUpdatesEnabled(True)
            self._fitting = False

        self._auto_fit = True
        self._apply_widths()

    # -- column widths --------------------------------------------------------
    def _apply_widths(self):
        count = self.columnCount()
        if not count or len(self._natural) != count:
            return
        avail = self.viewport().width()
        total = sum(self._natural)
        widths = self._natural
        if self._auto_fit and avail > 0 and total < avail:
            scale = avail / float(total)            # table is narrower than the window: fill it
            widths = [int(w * scale) for w in self._natural]
        self._fitting = True
        try:
            for c, w in enumerate(widths):
                self.setColumnWidth(c, w)
        finally:
            self._fitting = False

    def _on_section_resized(self, _index, _old, _new):
        if not self._fitting:
            self._auto_fit = False                  # the user dragged a column: stop auto-fitting

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._auto_fit:
            self._apply_widths()

    def selected_source_index(self):
        row = self.currentRow()
        if row < 0 or self.columnCount() == 0:
            return None
        item = self.item(row, 0)
        if item is None:
            return None
        value = item.data(ROW_ROLE)
        return int(value) if value is not None else None

    # -- sorting --------------------------------------------------------------
    def _on_header_clicked(self, column):
        if column == self._sort_col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col, self._sort_asc = column, True
        self.sortItems(self._sort_col,
                       Qt.SortOrder.AscendingOrder if self._sort_asc else Qt.SortOrder.DescendingOrder)
        self._update_header_labels()

    def _update_header_labels(self):
        for c, header in enumerate(self._headers):
            item = self.horizontalHeaderItem(c)
            if item is None:
                continue
            label = header.upper()
            if c == self._sort_col:
                label += "  \u25B2" if self._sort_asc else "  \u25BC"
            item.setText(label)

    # -- records ----------------------------------------------------------------
    def _on_double_click(self, row, _column):
        item = self.item(row, 0)
        if item is None:
            return
        index = item.data(ROW_ROLE)
        if index is not None:
            self.record_activated.emit(int(index))


class RecordDialog(QDialog):
    """Every field of one record, with long answers shown in full."""

    def __init__(self, eyebrow, title, headers, values, accent, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(660, 720)
        self.setStyleSheet(page_style(accent) + "QDialog { background: #0A1230; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(12)
        header = PageHeader(
            "edit", eyebrow.upper(), title,
            "Review the complete record details. This view does not change saved data.", accent,
        )
        root.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.viewport().setAutoFillBackground(False)
        body = QWidget()
        body.setAutoFillBackground(False)
        body.setStyleSheet("background: transparent;")
        form = QVBoxLayout(body)
        form.setContentsMargins(0, 4, 10, 4)
        form.setSpacing(12)
        for header, value in zip(headers, values):
            block = QVBoxLayout()
            block.setSpacing(2)
            block.addWidget(make_label(header.upper(), 10, accent, True, 1.6, mono=True))
            empty = value is None or value == ""
            label = make_label("\u2014" if empty else str(value), 13,
                               TEXT_FAINT if empty else TEXT, wrap=True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            block.addWidget(label)
            form.addLayout(block)
        form.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        close = NeonButton("Close", accent, icon="cross", variant="ghost", height=40)
        close.clicked.connect(self.accept)
        bottom.addWidget(close)
        root.addLayout(bottom)


def build_table_panel(accent):
    """Glass panel holding a DataTable and a one-line status label under it."""
    panel = GlassPanel(accent, radius=18)
    lay = QVBoxLayout(panel)
    lay.setContentsMargins(14, 14, 14, 10)
    lay.setSpacing(6)
    table = DataTable(accent)
    lay.addWidget(table, 1)
    status = make_label("", 11, TEXT_DIM, True, 1.4, mono=True)
    lay.addWidget(status)
    return panel, table, status


def set_status(label, text, color=TEXT_DIM):
    label.setText(text)
    label.setStyleSheet(f"color: {color}; background: transparent;")
