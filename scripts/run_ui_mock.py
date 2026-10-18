#!/usr/bin/env python3
"""Run a deterministic UI mock without touching Steam, network, or user data.

The mock intentionally imports the production Deck presentation widget. It is
safe to run on macOS for computer-use review:

    /private/tmp/assella-deck-venv/bin/python scripts/run_ui_mock.py --deck
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ui.deck_ui.home import DeckHomeOverview, HomeSnapshot
from ui.deck_ui.widgets import DeckActionButton, DeckCard, DeckSectionTitle


class MockLibraryDialog(QDialog):
    """A safe visual fixture for the redesigned Library entry point."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Library — Mock")
        self.setMinimumSize(900, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(DeckSectionTitle("Game Library", "4 installed games · 1 update available · microSD connected"))
        for name, detail in (
            ("Baldur's Gate 3", "Update available · Internal storage"),
            ("Hades", "Up to date · microSD"),
            ("Slay the Spire", "Artwork loading · Internal storage"),
            ("Celeste", "Library temporarily unavailable · cached"),
        ):
            card = DeckCard()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            title = QLabel(name)
            title.setStyleSheet("color: #f4f7fb; font-size: 13pt; font-weight: 800;")
            subtitle = QLabel(detail)
            subtitle.setStyleSheet("color: rgba(244,247,251,0.65); font-size: 10pt;")
            card_layout.addWidget(title)
            card_layout.addWidget(subtitle)
            layout.addWidget(card)
        close = DeckActionButton("Back")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)


class MockHomeWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASSella Deck — UI Mock")
        self.setStyleSheet("QDialog { background: #111722; }")
        self.resize(1280, 800)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.home = DeckHomeOverview(
            open_library=self.open_library,
            find_game=self.show_find_placeholder,
            open_activity=self.show_activity_placeholder,
            refresh_updates=self.refresh_updates,
            parent=self,
        )
        self.home.apply_snapshot(HomeSnapshot(
            library_summary="42 games across internal storage and microSD",
            updates_summary="3 games need attention",
            activity_summary="Hades is waiting in the queue",
            storage_summary="Internal: 118 GB free · microSD: 72 GB free",
        ))
        layout.addWidget(self.home)
        self.message = QLabel("Mock mode: no Steam, network, installer, settings, or background services are used.")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setStyleSheet("color: rgba(244,247,251,0.55); padding: 8px;")
        layout.addWidget(self.message)

    def open_library(self):
        MockLibraryDialog(self).exec()

    def show_find_placeholder(self):
        self.message.setText("Find a Game opens the guided discovery flow in the production implementation.")

    def show_activity_placeholder(self):
        self.message.setText("Activity opens the queue and current-task surface in the production implementation.")

    def refresh_updates(self):
        self.home.updates_value.setText("Refresh complete · 3 games need attention")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", action="store_true", help="Use the 1280×800 Steam Deck target size.")
    args = parser.parse_args()
    app = QApplication([])
    window = MockHomeWindow()
    if args.deck:
        window.resize(1280, 800)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
