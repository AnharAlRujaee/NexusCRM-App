"""Branded, accessible message and confirmation dialogs for Nexus CRM."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
from ui.theme import TEXT, LINE


def _style(accent="#4F9BFF"):
    """Shared dialog styling; accent follows the active CRM module."""
    return f"""
    QMessageBox {{ background: #0A1230; color: {TEXT}; border: 1px solid {LINE}; }}
    QMessageBox QLabel {{ color: {TEXT}; background: transparent; min-width: 320px; max-width: 620px; padding: 8px; }}
    QMessageBox QPushButton {{
        color: {TEXT}; background: rgba(18, 30, 66, 230);
        border: 1px solid {accent}; border-radius: 9px;
        padding: 8px 18px; min-width: 84px; min-height: 26px; font-weight: 600;
    }}
    QMessageBox QPushButton:hover {{ background: rgba(79, 155, 255, 45); }}
    QMessageBox QPushButton:default {{ background: rgba(79, 155, 255, 32); }}
    """


def show_message(parent, title, message, kind="info", accent=None, informative=None):
    """Display a readable, branded message instead of a native-looking popup."""
    accent = accent or getattr(parent, "accent", "#4F9BFF")
    box = QMessageBox(parent)
    box.setWindowTitle(str(title))
    box.setText(str(message) if message else "An unexpected issue occurred. Please try again.")
    box.setTextFormat(Qt.TextFormat.PlainText)
    if informative:
        box.setInformativeText(str(informative))
    icons = {
        "info": QMessageBox.Icon.Information,
        "warning": QMessageBox.Icon.Warning,
        "error": QMessageBox.Icon.Critical,
        "question": QMessageBox.Icon.Question,
    }
    box.setIcon(icons.get(kind, QMessageBox.Icon.Information))
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.setStyleSheet(_style(accent))
    box.setMinimumWidth(420)
    box.exec()
    return box.standardButton(box.clickedButton())


def confirm_message(parent, title, message, accent=None, destructive=False):
    accent = accent or getattr(parent, "accent", "#4F9BFF")
    box = QMessageBox(parent)
    box.setWindowTitle(str(title))
    box.setText(str(message))
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setIcon(QMessageBox.Icon.Warning if destructive else QMessageBox.Icon.Question)
    box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    box.setDefaultButton(QMessageBox.StandardButton.No)
    box.setStyleSheet(_style("#FF5C7A" if destructive else accent))
    box.setMinimumWidth(420)
    return box.exec() == QMessageBox.StandardButton.Yes
