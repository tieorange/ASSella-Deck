#!/usr/bin/env python3
"""Run a deterministic UI mock without touching Steam, network, or user data.

The mock intentionally imports the production Deck presentation widget. It is
safe to run on macOS for computer-use review:

    /private/tmp/assella-deck-venv/bin/python scripts/run_ui_mock.py --deck
"""

from __future__ import annotations

import argparse
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QApplication, QDialog, QLabel, QListWidgetItem, QStackedWidget, QVBoxLayout, QWidget


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ui.deck_ui.home import DeckHomeOverview, HomeSnapshot
from ui.deck_ui.widgets import DeckActionButton, DeckNotice, DeckSectionTitle
from ui.deck_ui.activity.domain import ActivitySnapshot
from ui.deck_ui.activity.presentation import ActivityDialog
from ui.deck_ui.install.presentation import DeckInstallFlow


class MemorySettings:
    def __init__(self):
        self.values = {"accent_color": "#43d6c1", "background_color": "#111722"}

    def value(self, key, default=None, type=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


class MockHomeWindow(QDialog):
    def __init__(self, state="normal"):
        super().__init__()
        self.state = state
        self.settings = MemorySettings()
        self.game_manager = None
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
            library_summary="No games yet" if state == "empty" else "42 games across internal storage and microSD",
            updates_summary="3 games need attention",
            activity_summary="Scan needs attention" if state == "error" else "Hades is waiting in the queue",
            storage_summary="microSD unavailable · cached games visible" if state == "missing-sd" else "Internal: 118 GB free · microSD: 72 GB free",
        ))
        layout.addWidget(self.home)
        self.message = QLabel("Mock mode: no Steam, network, installer, settings, or background services are used.")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setStyleSheet("color: rgba(244,247,251,0.55); padding: 8px;")
        layout.addWidget(self.message)

    def open_library(self):
        from ui.dialogs.gamelibrary import GameLibraryDialog

        with patch("ui.dialogs.gamelibrary.load_steam_cache", return_value=[]), \
             patch.object(GameLibraryDialog, "_trigger_steam_scan"), \
             patch.object(GameLibraryDialog, "_refresh_game_list"), \
             patch.object(GameLibraryDialog, "_open_selected_game", lambda dialog: dialog.main_window.open_details_preview(dialog)):
            dialog = GameLibraryDialog(self)
            dialog.scan_imports_button.hide()
            notices = {
                "normal": "Library is up to date.",
                "loading": "Refreshing libraries. Cached games remain available.",
                "error": "Scan stopped. Cached games remain available; choose Scan Libraries to retry.",
                "missing-sd": "microSD is unavailable. Reconnect it and scan again; cached games remain visible.",
                "empty": "No games found. Connect a Steam library, then scan again.",
                "large": "Showing cached games. Artwork loads as items become visible.",
            }
            dialog.library_notice.setText(notices[self.state])
            rows = () if self.state == "empty" else (
                ("Baldur's Gate 3", "Update available · Internal storage"),
                ("Hades", "Up to date · microSD"),
                ("Slay the Spire", "Artwork loading · Internal storage"),
                ("Celeste", "Storage unavailable · cached"),
            )
            if self.state == "large":
                rows *= 8
            for index, (name, detail) in enumerate(rows):
                item = QListWidgetItem(f"{name}\n{detail}")
                item.setData(Qt.ItemDataRole.UserRole, {"appid": str(1000 + index), "game_name": name})
                item.setSizeHint(QSize(0, 72))
                dialog.games_list.addItem(item)
            dialog.info_label.setText(f"{len(rows)} cached game(s)")
            dialog.games_list.currentItemChanged.connect(
                lambda current, _previous: dialog.open_selected_button.setEnabled(current is not None)
            )
            dialog.exec()

    def open_details_preview(self, parent, on_open=None):
        from ui.dialogs.gamelibrary_v2 import GameDetailsDialogV2

        def preview_tab(dialog, name):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(24, 18, 24, 18)
            layout.addWidget(DeckSectionTitle(name, "Safe fixture content for the Game Details layout."))
            layout.addWidget(DeckNotice("Game operations are disabled in this UI mock."))
            layout.addStretch()
            dialog.stacked.addWidget(page)
            if name == "Builds":
                dialog.builds_center_stack = QStackedWidget()
                for _ in range(3):
                    dialog.builds_center_stack.addWidget(QWidget())

        def preview_hero(_dialog, root):
            hero = QWidget()
            layout = QVBoxLayout(hero)
            layout.setContentsMargins(20, 12, 20, 12)
            layout.addWidget(DeckSectionTitle("Hades", "Installed · Internal storage · Up to date"))
            root.addWidget(hero)

        pages = {
            "_init_info_tab": "Info", "_init_depots_tab": "Depots",
            "_init_builds_tab": "Builds", "_init_tools_tab": "Tools",
            "_init_achievements_tab": "Achievements", "_init_workshop_tab": "Workshop",
            "_init_tickets_tab": "Tickets",
        }

        class MemoryBuildsCache:
            def get_builds_with_age(self, _appid):
                return [], 0

        with ExitStack() as stack:
            for method, title in pages.items():
                stack.enter_context(patch.object(GameDetailsDialogV2, method, lambda dialog, title=title: preview_tab(dialog, title)))
            for method in ("_init_slsonline_logic", "_ensure_builds_loaded", "_ensure_achievements_loaded", "_ensure_workshop_loaded"):
                stack.enter_context(patch.object(GameDetailsDialogV2, method, lambda _dialog: None))
            stack.enter_context(patch.object(GameDetailsDialogV2, "_is_luatools_available", lambda _dialog: False))
            stack.enter_context(patch.object(GameDetailsDialogV2, "_init_hero_v2", preview_hero))
            stack.enter_context(patch("ui.dialogs.gamelibrary_v2.get_settings", return_value=self.settings))
            stack.enter_context(patch("ui.dialogs.gamelibrary_v2.SteamDBBuildsCache", return_value=MemoryBuildsCache()))
            stack.enter_context(patch("ui.dialogs.gamelibrary_v2.SteamDBScraper", return_value=object()))
            stack.enter_context(patch("ui.dialogs.gamelibrary_v2.adapt_child_stylesheets"))
            stack.enter_context(patch("utils.workshop_helpers.check_game_workshop_available_async"))
            stack.enter_context(patch("core.steamdb_scraper.ByparrManager.find_byparr_dir", return_value=None))
            stack.enter_context(patch("ui.dialogs.dialog_raiser.DialogRaiser"))
            dialog = GameDetailsDialogV2(parent, {"appid": "1145360", "game_name": "Hades", "is_atom": True})
            if on_open is not None:
                on_open(dialog)
            dialog.exec()

    def show_find_placeholder(self):
        DeckInstallFlow(self, mock=True).exec()

    def show_activity_placeholder(self):
        state = ActivitySnapshot(
            active_name="Hades", active_status="Downloading", progress=42,
            progress_known=True, is_active=True, can_pause=True,
            queued=("Slay the Spire", "Celeste"),
            failure="Previous transfer interrupted; retry is available." if self.state == "error" else "",
            can_retry=self.state == "error",
        )
        ActivityDialog(
            self, snapshot_provider=lambda: state,
            pause=lambda: self.message.setText("Mock: pause requested"),
            cancel=lambda: self.message.setText("Mock: cancel requested"),
            retry=lambda: self.message.setText("Mock: retry requested"),
            remove=lambda row: self.message.setText(f"Mock: remove queued item {row}"),
            confirm_remove=lambda _name: True,
        ).exec()

    def refresh_updates(self):
        self.home.updates_value.setText("Refresh complete · 3 games need attention")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", action="store_true", help="Use the 1280×800 Steam Deck target size.")
    parser.add_argument("--deck-720", action="store_true", help="Use the 1280×720 Steam Deck target size.")
    parser.add_argument("--state", choices=("normal", "loading", "empty", "error", "missing-sd", "large"), default="normal")
    args = parser.parse_args()
    app = QApplication([])
    window = MockHomeWindow(args.state)
    if args.deck:
        window.resize(1280, 800)
    elif args.deck_720:
        window.resize(1280, 720)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
