"""Home presentation widget used by the main app and the deterministic UI mock."""

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .focus import configure_focus_order
from .navigation import DeckNavigation
from .widgets import DeckActionButton, DeckCard, DeckSectionTitle
from .theme import WARNING


@dataclass(frozen=True)
class HomeSnapshot:
    library_summary: str = "Library is loading"
    updates_summary: str = "Checking for updates"
    activity_summary: str = "No active download"
    storage_summary: str = "Steam storage is being checked"


class DeckHomeOverview(QWidget):
    """Action-first Home overview independent of application services."""

    def __init__(
        self,
        *,
        open_library: Callable[[], None],
        find_game: Callable[[], None],
        open_activity: Callable[[], None],
        refresh_updates: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("deckHomeOverview")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 16)
        root.setSpacing(18)
        root.addWidget(DeckSectionTitle("Your games", "Pick up where you left off, or find something new."))

        hero = DeckCard()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        hero_layout.setSpacing(14)
        hero_layout.addWidget(DeckSectionTitle("Ready to play", "Your library and game discovery are one tap away."))
        actions = QHBoxLayout()
        actions.setSpacing(12)
        self.library_button = DeckActionButton("Open Library", primary=True)
        self.find_button = DeckActionButton("Find a Game")
        self.library_button.setMinimumHeight(62)
        self.find_button.setMinimumHeight(62)
        self.library_button.clicked.connect(open_library)
        self.find_button.clicked.connect(find_game)
        actions.addWidget(self.library_button, 1)
        actions.addWidget(self.find_button, 1)
        hero_layout.addLayout(actions)
        root.addWidget(hero)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        self.library_value = self._add_summary_card(grid, 0, 0, "LIBRARY", "Loading installed games")
        self.updates_value = self._add_summary_card(grid, 0, 1, "UPDATES", "Checking")
        self.activity_value = self._add_summary_card(grid, 1, 0, "ACTIVITY", "No active work")
        self.storage_value = self._add_summary_card(grid, 1, 1, "STORAGE", "Checking")
        root.addLayout(grid)

        footer = QHBoxLayout()
        footer.setSpacing(12)
        self.activity_button = DeckActionButton("View Activity")
        self.activity_button.clicked.connect(open_activity)
        self.refresh_button = DeckActionButton("Refresh updates")
        self.refresh_button.clicked.connect(refresh_updates)
        footer.addWidget(self.activity_button)
        footer.addWidget(self.refresh_button)
        footer.addStretch()
        root.addLayout(footer)
        root.addStretch(1)
        configure_focus_order((self.library_button, self.find_button, self.activity_button, self.refresh_button))
        self._navigation = DeckNavigation(self)
        QTimer.singleShot(0, self.library_button.setFocus)

    def _add_summary_card(self, grid: QGridLayout, row: int, column: int, title: str, value: str) -> QLabel:
        card = DeckCard()
        card.setMinimumHeight(100)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        label = QLabel(title)
        label.setStyleSheet("color: #b8cad5; font-size: 9pt; font-weight: 800; letter-spacing: 1px;")
        layout.addWidget(label)
        summary = QLabel(value)
        summary.setWordWrap(True)
        summary.setStyleSheet("color: #f4f7fb; font-size: 12pt; font-weight: 700;")
        layout.addWidget(summary)
        grid.addWidget(card, row, column)
        return summary

    def apply_snapshot(self, snapshot: HomeSnapshot) -> None:
        self.library_value.setText(snapshot.library_summary)
        self.updates_value.setText(snapshot.updates_summary)
        self.activity_value.setText(snapshot.activity_summary)
        self.storage_value.setText(snapshot.storage_summary)
        unavailable = "unavailable" in snapshot.storage_summary.lower()
        self.storage_value.setStyleSheet(
            f"color: {WARNING if unavailable else '#f4f7fb'}; font-size: 12pt; font-weight: 700;"
        )
