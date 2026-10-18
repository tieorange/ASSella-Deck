"""Home presentation widget used by the main app and the deterministic UI mock."""

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .focus import configure_focus_order
from .widgets import DeckActionButton, DeckCard, DeckSectionTitle


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
        root.setContentsMargins(18, 16, 18, 10)
        root.setSpacing(14)
        root.addWidget(DeckSectionTitle("Your games, ready when you are", "Browse your library, install a game, or keep current work moving."))

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.library_button = DeckActionButton("Open Library", primary=True)
        self.find_button = DeckActionButton("Find a Game")
        self.activity_button = DeckActionButton("View Activity")
        self.library_button.clicked.connect(open_library)
        self.find_button.clicked.connect(find_game)
        self.activity_button.clicked.connect(open_activity)
        actions.addWidget(self.library_button, 2)
        actions.addWidget(self.find_button, 1)
        actions.addWidget(self.activity_button, 1)
        root.addLayout(actions)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        self.library_value = self._add_summary_card(grid, 0, 0, "LIBRARY", "Loading installed games")
        self.updates_value = self._add_summary_card(grid, 0, 1, "UPDATES", "Checking")
        self.activity_value = self._add_summary_card(grid, 1, 0, "ACTIVITY", "No active work")
        self.storage_value = self._add_summary_card(grid, 1, 1, "STORAGE", "Checking")
        root.addLayout(grid)

        self.refresh_button = DeckActionButton("Refresh updates")
        self.refresh_button.clicked.connect(refresh_updates)
        root.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignRight)
        configure_focus_order((self.library_button, self.find_button, self.activity_button, self.refresh_button))

    def _add_summary_card(self, grid: QGridLayout, row: int, column: int, title: str, value: str) -> QLabel:
        card = DeckCard()
        card.setMinimumHeight(82)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        label = QLabel(title)
        label.setStyleSheet("color: rgba(244,247,251,0.52); font-size: 8pt; font-weight: 800; letter-spacing: 1px;")
        layout.addWidget(label)
        summary = QLabel(value)
        summary.setWordWrap(True)
        summary.setStyleSheet("color: #f4f7fb; font-size: 11pt; font-weight: 700;")
        layout.addWidget(summary)
        grid.addWidget(card, row, column)
        return summary

    def apply_snapshot(self, snapshot: HomeSnapshot) -> None:
        self.library_value.setText(snapshot.library_summary)
        self.updates_value.setText(snapshot.updates_summary)
        self.activity_value.setText(snapshot.activity_summary)
        self.storage_value.setText(snapshot.storage_summary)
