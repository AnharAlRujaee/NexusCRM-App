"""Shared design tokens: colours, fonts, small colour helpers and global QSS."""

import time

from PyQt6.QtGui import QColor, QFont

# ---------------------------------------------------------------------------
# Animation clock (seconds since start) - used by everything that "breathes"
# ---------------------------------------------------------------------------
_T0 = time.perf_counter()


def now() -> float:
    return time.perf_counter() - _T0


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
TEXT = "#EAF1FF"
TEXT_DIM = "#8DA2C8"
TEXT_FAINT = "#5B6E94"
LINE = "#26365F"

OK = "#34F5A5"
WARN = "#FFB84D"
BAD = "#FF5C7A"

# One accent colour per section so the user always knows where they are.
ACCENTS = {
    "login": "#8B7CFF",
    "signup": "#E056FD",
    "preferences": "#22D3EE",
    "preferences_admin": "#FF3D81",
    "applications": "#4F9BFF",
    "trainees": "#A78BFA",
    "mentor": "#FFB347",
    "interviews": "#2EF2A0",
    "admin": "#FF3D81",
}

UI_FAMILIES = ["Segoe UI", "Inter", "SF Pro Display", "Helvetica Neue", "Arial"]
MONO_FAMILIES = ["Consolas", "SF Mono", "Menlo", "Courier New", "monospace"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def qcolor(value, alpha=None) -> QColor:
    """Copy a colour (hex string or QColor) and optionally override alpha 0-255."""
    c = QColor(value)
    if alpha is not None:
        c.setAlpha(max(0, min(255, int(alpha))))
    return c


def mix(a, b, t: float) -> QColor:
    """Linear blend between two colours (t=0 -> a, t=1 -> b)."""
    a = QColor(a)
    b = QColor(b)
    t = max(0.0, min(1.0, float(t)))
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
        int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def flags(*items) -> int:
    """OR together Qt flag enums into a plain int (safe for drawText in PyQt6)."""
    value = 0
    for item in items:
        value |= int(item.value)
    return value


def ui_font(px: int, bold: bool = False, spacing: float = 0.0, mono: bool = False) -> QFont:
    font = QFont()
    font.setFamilies(MONO_FAMILIES if mono else UI_FAMILIES)
    font.setPixelSize(int(px))
    font.setBold(bool(bold))
    if spacing:
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, float(spacing))
    return font


# ---------------------------------------------------------------------------
# Stylesheets
# ---------------------------------------------------------------------------
GLOBAL_STYLE = f"""
QToolTip {{
    background: #0B1330; color: {TEXT};
    border: 1px solid {LINE}; padding: 6px 8px;
}}
QLabel {{ background: transparent; color: {TEXT}; }}
QDialog, QMessageBox {{
    background: #0A1230;
    color: {TEXT};
}}
QDialog QLabel, QMessageBox QLabel {{ color: {TEXT}; background: transparent; }}
QMessageBox QLabel {{ min-width: 300px; padding: 6px 8px; }}
QMessageBox QPushButton, QDialogButtonBox QPushButton {{
    color: {TEXT}; background: rgba(18, 30, 66, 230);
    border: 1px solid {LINE}; border-radius: 9px;
    padding: 8px 18px; min-width: 84px; min-height: 24px; font-weight: 600;
}}
QMessageBox QPushButton:hover, QDialogButtonBox QPushButton:hover {{
    background: rgba(79, 155, 255, 45);
}}
QTabWidget::pane {{
    border: 1px solid rgba(110, 140, 230, 55);
    border-radius: 14px;
    background: rgba(8, 12, 32, 110);
    top: -1px;
}}
QTabBar::tab {{
    color: {TEXT_DIM}; background: rgba(12, 20, 46, 160);
    border: 1px solid rgba(110, 140, 230, 40); border-bottom: none;
    padding: 11px 18px; margin-right: 5px;
    border-top-left-radius: 10px; border-top-right-radius: 10px;
    min-height: 20px; font-weight: 600;
}}
QTabBar::tab:selected {{
    color: {TEXT}; background: rgba(120, 150, 255, 28);
    border-color: rgba(120, 150, 255, 150);
}}
QTabBar::tab:hover {{ color: {TEXT}; background: rgba(120, 150, 255, 18); }}
QTabBar::tab:disabled {{ color: {TEXT_FAINT}; }}
QTextEdit, QPlainTextEdit {{
    background: rgba(6, 11, 28, 200); color: {TEXT};
    border: 1px solid rgba(110, 140, 230, 70); border-radius: 12px;
    padding: 10px; selection-background-color: rgba(120, 160, 255, 120);
}}
QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid rgba(150, 180, 255, 180); }}
QCheckBox, QRadioButton {{ color: {TEXT}; spacing: 8px; background: transparent; }}
QGroupBox {{ color: {TEXT}; border: 1px solid {LINE}; border-radius: 12px; margin-top: 12px; padding: 12px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; color: {TEXT_DIM}; }}

QLineEdit {{
    background: rgba(6, 11, 28, 200);
    color: {TEXT};
    border: 1px solid rgba(110, 140, 230, 70);
    border-radius: 13px;
    padding: 0px 14px;
    min-height: 46px;
    font-size: 14px;
    selection-background-color: rgba(120, 160, 255, 120);
}}
QLineEdit:hover {{ border: 1px solid rgba(150, 180, 255, 130); }}

QComboBox {{
    background: rgba(6, 11, 28, 200);
    color: {TEXT};
    border: 1px solid rgba(110, 140, 230, 70);
    border-radius: 13px;
    padding: 0px 38px 0px 16px;
    min-height: 46px;
    font-size: 14px;
}}
QComboBox:hover {{ border: 1px solid rgba(150, 180, 255, 130); }}
QComboBox::drop-down {{ border: none; width: 38px; background: transparent; }}
QComboBox::down-arrow {{ image: none; width: 0px; height: 0px; }}
QComboBox QAbstractItemView {{
    background: #0A1230;
    color: {TEXT};
    border: 1px solid {LINE};
    selection-background-color: rgba(120, 160, 255, 80);
    selection-color: white;
    outline: none;
    padding: 4px;
}}
QDateTimeEdit, QDateEdit, QTimeEdit {{
    background: rgba(6, 11, 28, 200);
    color: {TEXT};
    border: 1px solid rgba(110, 140, 230, 70);
    border-radius: 12px;
    padding: 7px 12px;
    min-height: 28px;
    selection-background-color: rgba(120, 160, 255, 120);
}}
QDateTimeEdit:focus, QDateEdit:focus, QTimeEdit:focus {{ border: 1px solid rgba(150, 180, 255, 180); }}
QCalendarWidget QWidget {{ background: #0A1230; color: {TEXT}; }}
QCalendarWidget QToolButton {{ color: {TEXT}; background: rgba(18, 30, 66, 230); border: 1px solid {LINE}; border-radius: 6px; padding: 5px; }}
QCalendarWidget QAbstractItemView {{ background: #0A1230; color: {TEXT}; selection-background-color: rgba(120, 160, 255, 90); selection-color: white; }}

QTableWidget {{
    background: transparent;
    alternate-background-color: rgba(255, 255, 255, 6);
    color: {TEXT};
    border: none;
    gridline-color: rgba(110, 140, 230, 28);
    selection-background-color: rgba(120, 160, 255, 60);
    selection-color: white;
    font-size: 13px;
    outline: none;
}}
QTableWidget::item {{
    padding: 0px 12px;
    border: none;
    border-bottom: 1px solid rgba(110, 140, 230, 22);
}}
QTableWidget::item:hover {{ background: rgba(255, 255, 255, 13); }}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{
    background: rgba(120, 150, 255, 20);
    color: #9FB6E8;
    border: none;
    border-bottom: 1px solid rgba(110, 140, 230, 110);
    padding: 0px 12px;
    font-size: 11px;
    font-weight: 700;
}}
QHeaderView::section:hover {{ background: rgba(120, 150, 255, 38); }}
QTableCornerButton::section {{ background: transparent; border: none; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{
    background: rgba(130, 160, 255, 90); border-radius: 3px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: rgba(160, 190, 255, 160); }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{
    background: rgba(130, 160, 255, 90); border-radius: 3px; min-width: 30px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""


def page_style(accent: str) -> str:
    """Per-page QSS that tints focus rings, selections and table headers."""
    c = QColor(accent)
    r, g, b = c.red(), c.green(), c.blue()
    return f"""
    QLineEdit:focus {{
        border: 1px solid rgba({r}, {g}, {b}, 230);
        background: rgba(10, 18, 44, 230);
    }}
    QComboBox:hover, QComboBox:focus {{ border: 1px solid rgba({r}, {g}, {b}, 230); }}
    QTabBar::tab:selected {{
        color: {TEXT}; background: rgba({r}, {g}, {b}, 38);
        border-color: rgba({r}, {g}, {b}, 190);
    }}
    QTabBar::tab:hover {{ border-color: rgba({r}, {g}, {b}, 110); }}
    QDialogButtonBox QPushButton:default {{ border-color: rgba({r}, {g}, {b}, 210); }}
    QTableWidget::item:selected {{ background: rgba({r}, {g}, {b}, 55); color: white; }}
    QHeaderView::section {{
        color: {accent};
        border-bottom: 1px solid rgba({r}, {g}, {b}, 120);
    }}
    QScrollBar::handle:vertical {{ background: rgba({r}, {g}, {b}, 110); }}
    QScrollBar::handle:horizontal {{ background: rgba({r}, {g}, {b}, 110); }}
    """


def tab_style(accent: str) -> str:
    """Shared tab-header design, tinted with the active module accent."""
    c = QColor(accent)
    r, g, b = c.red(), c.green(), c.blue()
    return f"""
    QTabWidget::pane {{ border: 1px solid rgba(110, 140, 230, 55); border-radius: 14px; background: rgba(8, 12, 32, 110); top: -1px; }}
    QTabBar::tab {{ color: {TEXT_DIM}; background: rgba(12, 20, 46, 160); border: 1px solid rgba(110, 140, 230, 40); border-bottom: none; padding: 11px 18px; margin-right: 5px; border-top-left-radius: 10px; border-top-right-radius: 10px; min-height: 20px; font-weight: 600; }}
    QTabBar::tab:selected {{ color: {TEXT}; background: rgba({r}, {g}, {b}, 32); border-color: {accent}; }}
    QTabBar::tab:hover {{ color: {TEXT}; background: rgba({r}, {g}, {b}, 18); }}
    QTabBar::tab:disabled {{ color: {TEXT_FAINT}; }}
    """
