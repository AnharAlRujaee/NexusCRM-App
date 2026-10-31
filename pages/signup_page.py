"""Sign Up page - new accounts are saved to data/Users.xlsx as regular users.

Reached from the "Sign up" button on the Login card. On success it returns
to Login with the new username pre-filled.
"""

import re

from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from core.data_store import DataError, register_user

from ui.base_page import BasePage
from ui.theme import ACCENTS, BAD, OK, TEXT, TEXT_DIM, TEXT_FAINT, WARN, flags, qcolor, ui_font
from ui.widgets import (
    GlassPanel, GradientLabel, IconLabel, NeonButton, NeonLineEdit, OrbitRings, make_label,
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class StrengthBar(QWidget):
    """Four-segment password strength meter."""

    LEVELS = [("TOO SHORT", BAD), ("WEAK", BAD), ("FAIR", WARN), ("GOOD", "#B6F03C"), ("STRONG", OK)]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 0
        self._empty = True
        self.setFixedHeight(20)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_password(self, text):
        score = 0
        if len(text) >= 8:
            score += 1
            if re.search(r"[a-z]", text) and re.search(r"[A-Z]", text):
                score += 1
            if re.search(r"\d", text):
                score += 1
            if re.search(r"[^A-Za-z0-9]", text):
                score += 1
        self._score = score if text else 0
        self._empty = not text
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        label, color = self.LEVELS[self._score]
        seg_w = (self.width() - 110 - 3 * 6) / 4.0
        for i in range(4):
            on = (not self._empty) and i < self._score
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(qcolor(color, 230) if on else QColor(255, 255, 255, 22))
            p.drawRoundedRect(QRectF(i * (seg_w + 6), 7, seg_w, 6), 3, 3)
        p.setFont(ui_font(10, True, 1.4, mono=True))
        p.setPen(qcolor(color, 230) if not self._empty else QColor(TEXT_FAINT))
        p.drawText(QRectF(self.width() - 104, 0, 104, self.height()),
                   flags(Qt.AlignmentFlag.AlignRight, Qt.AlignmentFlag.AlignVCenter),
                   "" if self._empty else label)


class SignupPage(BasePage):
    def __init__(self, nav):
        super().__init__(nav, ACCENTS["signup"], "signup", "CREATE ACCOUNT")
        accent = self.accent

        body = QHBoxLayout()
        body.setSpacing(40)
        body.setContentsMargins(20, 0, 20, 0)

        # ---- hero (left) ------------------------------------------------
        hero = QWidget()
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)
        hl.addStretch()
        hl.addWidget(OrbitRings(accent, 210), 0, Qt.AlignmentFlag.AlignLeft)
        hl.addWidget(GradientLabel("JOIN NEXUS", 58, "#E056FD", "#22D3EE"), 0, Qt.AlignmentFlag.AlignLeft)
        hl.addWidget(make_label("CREATE YOUR WORKSPACE ID", 17, TEXT, True, 5.0), 0, Qt.AlignmentFlag.AlignLeft)
        hl.addSpacing(8)
        hl.addWidget(make_label("Set up your account in under a minute.", 14, TEXT_DIM))
        hl.addSpacing(10)
        for text in ("Track applications end to end",
                     "Keep mentor conversations in one place",
                     "Never miss an interview or event"):
            row = QHBoxLayout()
            row.setSpacing(12)
            row.addWidget(IconLabel("check", accent, 18))
            row.addWidget(make_label(text, 13, TEXT_DIM))
            row.addStretch()
            hl.addLayout(row)
        hl.addStretch()
        body.addWidget(hero, 5)

        # ---- form card (right) ------------------------------------------
        right = QVBoxLayout()
        right.addStretch()
        self.card = GlassPanel(accent, radius=22)
        self.card.setFixedWidth(460)
        form = QVBoxLayout(self.card)
        form.setContentsMargins(34, 26, 34, 22)
        form.setSpacing(9)

        form.addWidget(make_label("NEW ACCOUNT", 11, accent, True, 3.0, mono=True))
        form.addWidget(make_label("Create account", 27, TEXT, True))
        form.addSpacing(4)

        self.full_name = NeonLineEdit("Full name", "user", accent)
        self.email = NeonLineEdit("Email address", "mail", accent)
        self.username = NeonLineEdit("Choose a username", "user", accent)
        self.password = NeonLineEdit("Password (min. 8 characters)", "lock", accent, password=True)
        self.confirm = NeonLineEdit("Confirm password", "lock", accent, password=True)
        for edit in (self.full_name, self.email, self.username):
            form.addWidget(edit)
        form.addWidget(self.password)
        self.strength = StrengthBar()
        form.addWidget(self.strength)
        form.addWidget(self.confirm)
        self.password.textChanged.connect(self.strength.set_password)

        self.message = make_label("", 12, BAD, True)
        self.message.setMinimumHeight(22)
        form.addWidget(self.message)

        self.create_btn = NeonButton("Create account", accent, icon="arrow", height=48)
        self.create_btn.clicked.connect(self.attempt_signup)
        self.confirm.returnPressed.connect(self.attempt_signup)
        form.addWidget(self.create_btn)

        back = NeonButton("Back to login", accent, icon="back", variant="ghost", height=40)
        back.clicked.connect(lambda: self.nav.go("login"))
        form.addWidget(back)

        form.addWidget(make_label("New accounts are saved to the Users file as regular users.", 11, TEXT_FAINT))

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
        for edit in (self.full_name, self.email, self.username, self.password, self.confirm):
            edit.clear()
        self.password.set_revealed(False)
        self.confirm.set_revealed(False)
        self.set_message("", BAD)
        self.create_btn.setEnabled(True)

    def on_enter(self):
        super().on_enter()
        self.reset()
        self.full_name.setFocus()

    def validate(self):
        if not all(e.text().strip() for e in
                   (self.full_name, self.email, self.username)) or not self.password.text() \
                or not self.confirm.text():
            return "Please fill in every field."
        if not EMAIL_RE.match(self.email.text().strip()):
            return "Enter a valid email address."
        if len(self.username.text().strip()) < 3:
            return "Username must be at least 3 characters."
        if len(self.password.text()) < 8:
            return "Password must be at least 8 characters."
        if self.password.text() != self.confirm.text():
            return "Passwords do not match."
        return None

    def attempt_signup(self):
        if not self.create_btn.isEnabled():
            return
        error = self.validate()
        if error:
            self.set_message("\u26A0  " + error, BAD)
            self.card.flash(BAD)
            return
        user = self.username.text().strip()
        try:
            register_user(user, self.password.text())
        except DataError as exc:
            self.set_message("\u26A0  " + str(exc), BAD)
            self.card.flash(BAD)
            return
        self.set_message("\u2713  ACCOUNT CREATED \u2014 redirecting to login\u2026", OK)
        self.card.flash(OK)
        self.create_btn.setEnabled(False)
        QTimer.singleShot(800, lambda: self.nav.account_created(user))
