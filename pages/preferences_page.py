"""Page 2 - Preferences (regular user menu).

The Admin variant lives in ``preferences_admin_page.py`` and extends this class.
"""

from PyQt6.QtWidgets import QHBoxLayout, QGridLayout, QWidget

from ui.base_page import BasePage
from ui.theme import ACCENTS, OK
from ui.widgets import NavCard, NeonButton, PageHeader, StatusChip


class PreferencesPage(BasePage):
    def __init__(self, nav, admin=False):
        key = "preferences_admin" if admin else "preferences"
        crumb = "PREFERENCES / ADMIN" if admin else "PREFERENCES"
        super().__init__(nav, ACCENTS[key], key, crumb)
        self.admin = admin

        header = PageHeader(
            "admin" if admin else "hex",
            "Admin console" if admin else "Main workspace",
            "Preferences \u2014 Admin" if admin else "Preferences",
            "Full access: all modules plus the Admin tools." if admin
            else "Choose a module to continue.",
            self.accent,
        )
        header.add_chip(StatusChip("SYSTEM ONLINE", OK))
        if admin:
            header.add_chip(StatusChip("ADMIN MODE", self.accent))
        self.root.addWidget(header)
        self.reveal(header)

        self.root.addStretch(1)

        cards = QWidget()
        grid = QGridLayout(cards)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        card_widgets = self.build_cards()
        # Six equal grid units let the five-card admin dashboard center its
        # second row, while the regular four-card dashboard forms a balanced 2x2.
        if len(card_widgets) <= 4:
            positions = [(0, 0), (0, 3), (1, 0), (1, 3)]
            span = 3
        else:
            positions = [(0, 0), (0, 2), (0, 4), (1, 1), (1, 3)]
            span = 2
        for card, (r, c) in zip(card_widgets, positions):
            grid.addWidget(card, r, c, 1, span)
        for col in range(6): grid.setColumnStretch(col, 1)
        self.root.addWidget(cards)
        self.reveal(*card_widgets)

        self.root.addStretch(1)

        sign_out = NeonButton("Sign out", self.accent, icon="logout", variant="ghost")
        sign_out.clicked.connect(self.nav.sign_out)
        exit_btn = NeonButton("Close", self.accent, icon="power", variant="ghost")
        exit_btn.clicked.connect(self.nav.exit_app)
        self.add_row([sign_out, exit_btn], stretch_end=True)

    def build_cards(self):
        nav = self.nav
        cards = [
            NavCard("apps", "Applications", "Review and filter candidate applications.",
                    ACCENTS["applications"], "01", "OPEN APPLICATIONS"),
            NavCard("mentor", "Mentor Interview", "Browse mentor conversations by category.",
                    ACCENTS["mentor"], "02", "OPEN MENTOR"),
            NavCard("interviews", "Project Tracking", "Track projects sent and received.",
                    ACCENTS["interviews"], "03", "OPEN PROJECT TRACKING"),
            NavCard("users", "Trainees", "Manage trainee contact details.",
                    ACCENTS["trainees"], "04", "OPEN TRAINEES"),
        ]
        cards[0].clicked.connect(lambda: nav.go("applications"))
        cards[1].clicked.connect(lambda: nav.go("mentor"))
        cards[2].clicked.connect(lambda: nav.go("interviews"))
        cards[3].clicked.connect(lambda: nav.go("trainees"))
        return cards
