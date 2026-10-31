"""Common skeleton shared by every page: top bar, accent-tinted style and
a staggered 'reveal' animation that plays each time the page is entered."""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ui.theme import page_style
from ui.widgets import NeonButton, TopBar, stagger


class BasePage(QWidget):
    def __init__(self, nav, accent, key, crumb):
        super().__init__()
        self.nav = nav
        self.accent = accent
        self.key = key
        self._reveal = []

        self.setStyleSheet(page_style(accent))
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(40, 22, 40, 24)
        self.root.setSpacing(16)

        self.topbar = TopBar(accent, crumb)
        self.root.addWidget(self.topbar)

    # -- building helpers -------------------------------------------------
    def reveal(self, *widgets):
        """Register widgets to animate in (in order) whenever the page opens."""
        self._reveal.extend(widgets)

    def add_row(self, widgets, spacing=6, stretch_end=False):
        """Put widgets side by side in a row container and register it."""
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(spacing)
        for w in widgets:
            lay.addWidget(w)
        if stretch_end:
            lay.addStretch()
        self.root.addWidget(box)
        self.reveal(box)
        return box

    def back_button(self, label="Return to Preferences Screen"):
        btn = NeonButton(label, self.accent, icon="back", variant="ghost")
        btn.clicked.connect(self.nav.go_home)
        return btn

    # -- lifecycle ----------------------------------------------------------
    def on_enter(self):
        """Called by the window right before the page becomes visible."""
        self.topbar.set_session(self.nav.username, self.nav.is_admin)
        self.refresh_session()
        stagger(self._reveal, base=140, step=90)

    def refresh_session(self):
        """Hook for pages that depend on who is logged in."""
