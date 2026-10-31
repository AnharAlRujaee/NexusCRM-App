"""NEXUS CRM - PyQt6 interface backed by a local PostgreSQL database.

Run:
    pip install -r requirements.txt
    python main.py

Project layout:
    main.py                         window controller + navigation
    core/                           Excel data access and filter helpers
    ui/                             shared theme, tables, icons, widgets
    pages/                          application screens
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout

from pages.admin_page import AdminPage
from pages.applications_page import ApplicationsPage
from pages.interviews_page import InterviewsPage
from pages.login_page import LoginPage
from pages.mentor_page import MentorInterviewPage
from pages.preferences_admin_page import PreferencesAdminPage
from pages.preferences_page import PreferencesPage
from pages.signup_page import SignupPage
from pages.trainees_page import TraineesPage
from ui.background import FuturisticBackground
from ui.navigation import AnimatedStack
from ui.theme import GLOBAL_STYLE, ui_font
from ui.widgets import Toast


class CRMWindow(QMainWindow):
    # Depth decides the slide direction: deeper = forward, shallower = back.
    DEPTH = {
        "login": 0,
        "signup": 1,
        "preferences": 1,
        "preferences_admin": 1,
        "applications": 2,
        "mentor": 2,
        "interviews": 2,
        "trainees": 2,
        "admin": 2,
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEXUS CRM")
        self.resize(1280, 840)
        self.setMinimumSize(1100, 740)

        self.username = ""
        self.is_admin = False
        self._current_key = None
        self._closing = False

        self.bg = FuturisticBackground()
        self.setCentralWidget(self.bg)
        layout = QVBoxLayout(self.bg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = AnimatedStack()
        layout.addWidget(self.stack)
        self.toast_widget = Toast(self.bg)

        self.pages = {
            "login": LoginPage(self),
            "signup": SignupPage(self),
            "preferences": PreferencesPage(self),
            "preferences_admin": PreferencesAdminPage(self),
            "applications": ApplicationsPage(self),
            "mentor": MentorInterviewPage(self),
            "interviews": InterviewsPage(self),
            "trainees": TraineesPage(self),
            "admin": AdminPage(self),
        }
        for key, page in self.pages.items():
            self.stack.add_page(key, page)

        self.go("login", animate=False)

    # -- navigation -----------------------------------------------------
    def go(self, key, animate=True):
        if key == self._current_key:
            return
        page = self.pages[key]
        old_depth = self.DEPTH.get(self._current_key, 0) if self._current_key is not None else 0
        direction = 1 if self.DEPTH[key] >= old_depth else -1

        self.bg.set_accent(page.accent)
        page.on_enter()
        self.stack.go(key, direction, animate, page.accent)
        self._current_key = key

    def home_key(self):
        return "preferences_admin" if self.is_admin else "preferences"

    def go_home(self):
        """'Return to Preferences Screen' - admin or regular, depending on login."""
        self.go(self.home_key())

    def login(self, username, is_admin):
        self.username = username
        self.is_admin = is_admin
        self.go_home()

    def sign_out(self):
        self.username = ""
        self.is_admin = False
        self.pages["login"].reset()
        self.go("login")

    def account_created(self, username):
        """Sign-up finished: back to login with the new username filled in."""
        self.pages["login"].prefill(username)
        self.go("login")
        self.toast(f"Account '{username}' created \u2014 sign in to continue", self.pages["signup"].accent)

    def toast(self, text, accent):
        self.toast_widget.popup(text, accent)

    # -- window life-cycle --------------------------------------------------
    def fade_in_window(self):
        self.setWindowOpacity(0.0)
        self._open_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._open_anim.setDuration(600)
        self._open_anim.setStartValue(0.0)
        self._open_anim.setEndValue(1.0)
        self._open_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._open_anim.start()

    def exit_app(self):
        if self._closing:
            return
        self._closing = True
        self._close_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._close_anim.setDuration(260)
        self._close_anim.setStartValue(self.windowOpacity())
        self._close_anim.setEndValue(0.0)
        self._close_anim.finished.connect(self.close)
        self._close_anim.start()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NEXUS CRM")
    app.setStyle("Fusion")
    app.setFont(ui_font(14))
    app.setStyleSheet(GLOBAL_STYLE)

    window = CRMWindow()
    window.show()
    window.fade_in_window()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
