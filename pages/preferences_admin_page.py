"""Page 3 - Preferences (Admin menu).

Same three destinations as the regular menu plus the Admin button,
in a pink "admin" colour scheme with an ADMIN MODE badge.
"""

from pages.preferences_page import PreferencesPage
from ui.theme import ACCENTS
from ui.widgets import NavCard


class PreferencesAdminPage(PreferencesPage):
    def __init__(self, nav):
        super().__init__(nav, admin=True)

    def build_cards(self):
        cards = super().build_cards()
        admin_card = NavCard("admin", "Admin", "Calendar events and participant mail tools.",
                             ACCENTS["admin"], "04", "OPEN ADMIN")
        admin_card.clicked.connect(lambda: self.nav.go("admin"))
        cards.append(admin_card)
        return cards
