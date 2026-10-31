"""Page 1 - Login."""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from core.data_store import DataError, authenticate

from ui.base_page import BasePage
from ui.theme import ACCENTS, BAD, OK, TEXT, TEXT_DIM, TEXT_FAINT
from ui.widgets import (
    GlassPanel, GradientLabel, IconLabel, NeonButton, NeonLineEdit, OrbitRings, make_label,
)


class LoginPage(BasePage):
    def __init__(self, nav):
        super().__init__(nav, ACCENTS["login"], "login", "ACCESS TERMINAL")
        accent = self.accent

        body = QHBoxLayout()
        body.setSpacing(40)
        body.setContentsMargins(20, 0, 20, 0)

        # ---- hero (left) --------------------------------------------------
        hero = QWidget()
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)
        hl.addStretch()
        hl.addWidget(OrbitRings(accent, 230), 0, Qt.AlignmentFlag.AlignLeft)
        hl.addWidget(GradientLabel("NEXUS", 76, "#8B7CFF", "#22D3EE"), 0, Qt.AlignmentFlag.AlignLeft)
        hl.addWidget(make_label("CRM  WORKSPACE", 20, TEXT, True, 7.0), 0, Qt.AlignmentFlag.AlignLeft)
        hl.addSpacing(8)
        hl.addWidget(make_label(
            "One command centre for applications, mentor\nconversations, interviews and events.",
            14, TEXT_DIM))
        hl.addSpacing(12)
        for icon, text, color in (
            ("apps", "Application pipeline", ACCENTS["applications"]),
            ("mentor", "Mentor conversations", ACCENTS["mentor"]),
            ("interviews", "Interview tracking", ACCENTS["interviews"]),
            ("calendar", "Calendar & communication", ACCENTS["admin"]),
        ):
            row = QHBoxLayout()
            row.setSpacing(12)
            row.addWidget(IconLabel(icon, color, 18))
            row.addWidget(make_label(text, 13, TEXT_DIM))
            row.addStretch()
            hl.addLayout(row)
        hl.addStretch()
        body.addWidget(hero, 5)

        # ---- login card (right) ------------------------------------------
        right = QVBoxLayout()
        right.addStretch()
        self.card = GlassPanel(accent, radius=22)
        self.card.setFixedWidth(440)
        form = QVBoxLayout(self.card)
        form.setContentsMargins(36, 34, 36, 30)
        form.setSpacing(12)

        form.addWidget(make_label("SECURE ACCESS", 11, accent, True, 3.0, mono=True))
        form.addWidget(make_label("Welcome back", 29, TEXT, True))
        form.addWidget(make_label("Sign in to enter your CRM workspace.", 13, TEXT_DIM))
        form.addSpacing(10)

        self.username = NeonLineEdit("Username", "user", accent)
        self.password = NeonLineEdit("Password", "lock", accent, password=True)  # eye icon inside
        form.addWidget(self.username)
        form.addWidget(self.password)

        self.message = make_label("", 12, BAD, True)
        self.message.setMinimumHeight(24)
        form.addWidget(self.message)

        self.sign_in = NeonButton("Authenticate", accent, icon="arrow", height=50)
        self.sign_in.clicked.connect(self.attempt_login)
        self.password.returnPressed.connect(self.attempt_login)
        self.username.returnPressed.connect(lambda: self.password.setFocus())
        form.addWidget(self.sign_in)

        form.addWidget(make_label(
            "Sign in with an account from the Users file.\nNo account yet? Use Sign up below.",
            11, TEXT_FAINT))

        extra = QHBoxLayout()
        extra.setSpacing(6)
        signup = NeonButton("Sign up", ACCENTS["signup"], icon="user", variant="ghost", height=40)
        signup.clicked.connect(lambda: self.nav.go("signup"))
        close = NeonButton("Close", accent, icon="power", variant="ghost", height=40)
        close.clicked.connect(self.nav.exit_app)
        extra.addWidget(signup)
        extra.addWidget(close)
        form.addLayout(extra)

        right.addWidget(self.card)
        right.addStretch()
        body.addLayout(right, 4)

        self.root.addLayout(body, 1)
        self.reveal(hero, self.card)

    # ------------------------------------------------------------------
    def set_message(self, text, color):
        self.message.setText(text)
        self.message.setStyleSheet(f"color: {color}; background: transparent;")

    def reset(self):
        self.username.clear()
        self.password.clear()
        self.password.set_revealed(False)
        self.set_message("", BAD)
        self.sign_in.setEnabled(True)

    def on_enter(self):
        super().on_enter()
        self.password.clear()
        self.password.set_revealed(False)
        (self.password if self.username.text() else self.username).setFocus()

    def prefill(self, username):
        self.username.setText(username)
        self.password.clear()
        self.password.set_revealed(False)
        self.set_message("", BAD)
        self.sign_in.setEnabled(True)

    def attempt_login(self):
        if not self.sign_in.isEnabled():
            return
        user = self.username.text().strip()
        pw = self.password.text()
        if not user or not pw:
            self.set_message("\u26A0  Enter both username and password.", BAD)
            self.card.flash(BAD)
            return

        try:
            account = authenticate(user, pw)
        except DataError as exc:
            self.set_message("\u26A0  " + str(exc), BAD)
            self.card.flash(BAD)
            return
        if account is None:
            self.set_message("\u26A0  Incorrect username or password.", BAD)
            self.card.flash(BAD)
            self.password.selectAll()
            self.password.setFocus()
            return

        name, role = account
        self.set_message("\u2713  ACCESS GRANTED \u2014 initializing workspace\u2026", OK)
        self.card.flash(OK)
        self.sign_in.setEnabled(False)
        QTimer.singleShot(650, lambda: self._enter(name, role == "admin"))

    def _enter(self, user, is_admin):
        self.set_message("", BAD)
        self.sign_in.setEnabled(True)
        self.nav.login(user, is_admin)
