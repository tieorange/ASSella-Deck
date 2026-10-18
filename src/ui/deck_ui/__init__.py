"""Shared Deck-oriented presentation primitives.

Feature screens use these widgets instead of duplicating ad-hoc styles and
focus rules. They deliberately contain no Steam, network, or manager logic.
"""

from .focus import activate_focused, configure_focus_order
from .home import DeckHomeOverview
from .widgets import DeckActionButton, DeckCard, DeckSectionTitle

__all__ = (
    "activate_focused",
    "configure_focus_order",
    "DeckActionButton",
    "DeckCard",
    "DeckHomeOverview",
    "DeckSectionTitle",
)
