#!/usr/bin/env python3
"""Run a deterministic UI mock without touching Steam, network, or user data.

The mock intentionally imports the production Deck presentation widget. It is
safe to run on macOS for computer-use review:

    /private/tmp/assella-deck-venv/bin/python scripts/run_ui_mock.py --deck
"""

from __future__ import annotations

import argparse
import sys
import time
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QAbstractButton, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidgetItem, QStackedWidget, QVBoxLayout, QWidget


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ui.deck_ui.home import DeckHomeOverview, HomeSnapshot
from ui.deck_ui.widgets import DeckActionButton, DeckCard, DeckNotice, DeckSectionTitle
from ui.deck_ui.activity.domain import ActivitySnapshot
from ui.deck_ui.activity.presentation import ActivityDialog
from ui.deck_ui.install.presentation import DeckInstallFlow


def fixture_artwork(title: str, index: int) -> QPixmap:
    """Paint an in-memory cover placeholder; no files or image requests."""
    colors = (("#214a66", "#4a2472"), ("#59324d", "#a94d4b"), ("#234b49", "#55673a"))
    first, second = colors[index % len(colors)]
    image = QPixmap(220, 128)
    painter = QPainter(image)
    gradient = QLinearGradient(0, 0, 220, 128)
    gradient.setColorAt(0, QColor(first))
    gradient.setColorAt(1, QColor(second))
    painter.fillRect(image.rect(), gradient)
    painter.setPen(QColor("#f4f7fb"))
    font = QFont()
    font.setPointSize(26)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "".join(word[0] for word in title.split()[:2]))
    painter.end()
    return image


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
            library_summary="No games yet" if state == "empty" else "Refreshing · 42 cached games" if state == "loading" else "42 games across internal storage and microSD",
            updates_summary="3 games need attention" if state not in ("empty", "loading") else "Checking for updates" if state == "loading" else "No updates yet",
            activity_summary="Transfer needs attention" if state == "error" else "No active work" if state == "empty" else "Hades is downloading · 42%",
            storage_summary="microSD unavailable · cached games visible" if state == "missing-sd" else "Internal: 118 GB free · microSD: 72 GB free",
        ))
        layout.addWidget(self.home)
        self.message = QLabel("Mock mode: no Steam, network, installer, settings, or background services are used.")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setStyleSheet("color: rgba(244,247,251,0.55); padding: 8px;")
        layout.addWidget(self.message)

    def open_library(self):
        from ui.dialogs.gamelibrary import GameLibraryDialog
        from ui.dialogs.library.widgets import GameItemWidget

        with patch("ui.dialogs.gamelibrary.load_steam_cache", return_value=[]), \
             patch.object(GameLibraryDialog, "_trigger_steam_scan"), \
             patch.object(GameLibraryDialog, "_refresh_game_list"), \
             patch.object(GameLibraryDialog, "_open_selected_game", lambda dialog: dialog.main_window.open_details_preview(dialog)):
            dialog = GameLibraryDialog(self)
            dialog.scan_imports_button.hide()
            dialog._pinned_cache = {}
            notices = {
                "normal": "Library is up to date.",
                "loading": "Refreshing libraries. Cached games remain available.",
                "error": "Scan stopped. Cached games remain available; choose Scan Libraries to retry.",
                "missing-sd": "microSD is unavailable. Reconnect it and scan again; cached games remain visible.",
                "empty": "No games found. Connect a Steam library, then scan again.",
                "large": "Showing cached games. Artwork loads as items become visible.",
            }
            dialog.library_notice.setText(notices[self.state])
            dialog.library_notice.setTone("warning" if self.state == "missing-sd" else "error" if self.state == "error" else "info")
            if self.state in ("error", "missing-sd"):
                dialog.library_notice.setAction("Retry scan", lambda: dialog.library_notice.setText("Mock scan complete. Cached games remain visible."))
            rows = () if self.state == "empty" else (
                ("Baldur's Gate 3", "update_available", "Internal storage", "ACCELA"),
                ("Hades", "up_to_date", "microSD", "at0-m"),
                ("Slay the Spire", "checking", "Internal storage", "Steam"),
                ("Celeste", "cannot_determine", "microSD unavailable" if self.state == "missing-sd" else "Internal storage", "ACCELA"),
            )
            if self.state == "large":
                rows *= 32
            with patch("utils.settings.get_settings", return_value=self.settings), \
                 patch("utils.dlc_helpers.is_dlc_only_mode", return_value=False):
                for index, (name, status, storage, source) in enumerate(rows):
                    game = {"appid": str(1000 + index), "game_name": name,
                            "source": source, "storage_label": storage, "update_status": status,
                            "is_steam_tab": source == "Steam", "is_atom": source == "at0-m"}
                    dialog._manifest_mtimes[game["appid"]] = time.time() - 3600
                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, game)
                    item.setSizeHint(QSize(0, 136))
                    dialog.games_list.addItem(item)
                    widget = GameItemWidget(game, "8.4 GB", "#43d6c1", "#101823", parent_dialog=dialog)
                    widget.image_label.setPixmap(fixture_artwork(name, index))
                    dialog.games_list.setItemWidget(item, widget)
            def filter_fixture():
                source = {"accela": "ACCELA", "at0m": "at0-m", "steam": "Steam"}[dialog._active_tab]
                query = dialog.search_input.text().casefold()
                shown = 0
                for index in range(dialog.games_list.count()):
                    item = dialog.games_list.item(index)
                    game = item.data(Qt.ItemDataRole.UserRole)
                    visible = game["source"] == source and query in game["game_name"].casefold()
                    item.setHidden(not visible)
                    shown += visible
                if dialog.games_list.currentItem() is not None and dialog.games_list.currentItem().isHidden():
                    dialog.games_list.setCurrentRow(-1)
                dialog.info_label.setText(f"{shown} shown · {len(rows)} cached")
                dialog._set_empty_state(shown == 0, searching=bool(query))

            dialog.search_input.textChanged.connect(lambda _query: filter_fixture())
            dialog.tab_bar.current_tab_changed.connect(lambda _tab: filter_fixture())
            filter_fixture()
            dialog.games_list.currentItemChanged.connect(
                lambda current, _previous: dialog.open_selected_button.setEnabled(current is not None)
            )
            dialog.exec()

    def open_details_preview(self, parent, on_open=None):
        from ui.dialogs.gamelibrary_v2 import GameDetailsDialogV2
        selected = getattr(parent, "games_list", None)
        selected_item = selected.currentItem() if selected is not None else None
        selected_game = selected_item.data(Qt.ItemDataRole.UserRole) if selected_item is not None else {}
        game_name = selected_game.get("game_name", "Hades")
        appid = selected_game.get("appid", "1145360")

        def preview_tab(dialog, name):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(24, 18, 24, 18)
            details = {
                "Info": ("Installed build", "Public branch · build 123456", "Storage", "Internal storage · 118 GB free"),
                "Depots": ("Selected content", "Base game depot · ready", "Manifest", "Cached · checked recently"),
                "Builds": ("Current build", "123456 · public", "Available build", "123457 · update available"),
                "Tools": ("Game tools", "Available after connecting to Steam", "Compatibility", "Proton settings are unchanged"),
                "Achievements": ("Achievements", "No local progress in the fixture", "Sync", "Connect Steam to refresh"),
                "Workshop": ("Workshop content", "No downloaded items in the fixture", "Updates", "No changes pending"),
                "Tickets": ("Ownership tickets", "No ticket loaded in the fixture", "Status", "Manual import available in the app"),
            }
            first_label, first_value, second_label, second_value = details[name]
            layout.addWidget(DeckSectionTitle(name, "Game information and actions for this section."))
            for heading, value in ((first_label, first_value), (second_label, second_value)):
                card = DeckCard()
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(18, 14, 18, 14)
                card_layout.addWidget(DeckSectionTitle(heading, value))
                layout.addWidget(card)
            layout.addWidget(DeckNotice("Preview only · game operations are disabled in this mock."))
            layout.addStretch()
            dialog.stacked.addWidget(page)
            if name == "Builds":
                dialog.builds_center_stack = QStackedWidget()
                for _ in range(3):
                    dialog.builds_center_stack.addWidget(QWidget())

        def preview_hero(_dialog, root):
            hero = QWidget()
            layout = QHBoxLayout(hero)
            layout.setContentsMargins(20, 12, 20, 12)
            cover = QLabel()
            cover.setPixmap(fixture_artwork(game_name, 1).scaled(145, 84))
            layout.addWidget(cover)
            layout.addWidget(DeckSectionTitle(game_name, "Installed · Internal storage · Up to date"), 1)
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
            dialog = GameDetailsDialogV2(parent, {"appid": appid, "game_name": game_name, "is_atom": True})
            if on_open is not None:
                on_open(dialog)
            dialog.exec()

    def show_find_placeholder(self):
        DeckInstallFlow(self, mock=True, mock_state=self.state).exec()

    def show_activity_placeholder(self):
        state = ActivitySnapshot(
            active_name="Hades", active_status="Downloading", progress=42,
            progress_known=self.state != "loading", is_active=self.state != "empty", can_pause=self.state not in ("empty", "error"),
            queued=() if self.state == "empty" else ("Slay the Spire", "Celeste") * (16 if self.state == "large" else 1),
            failure="Previous transfer interrupted; retry is available." if self.state == "error" else "",
            can_retry=self.state == "error",
        )
        if self.state == "empty":
            state = ActivitySnapshot()
        elif self.state == "error":
            state = ActivitySnapshot(
                active_name="No active download", active_status="Last transfer failed",
                queued=("Slay the Spire", "Celeste"),
                failure="Previous transfer interrupted; retry is available.", can_retry=True,
            )
        holder = {"state": state}

        def pause():
            current = holder["state"]
            holder["state"] = replace(current, is_paused=not current.is_paused,
                                      active_status="Paused" if not current.is_paused else "Downloading")

        def cancel():
            holder["state"] = replace(holder["state"], is_active=False, can_pause=False,
                                      active_status="Cancelled", progress_known=False)

        def retry():
            holder["state"] = replace(holder["state"], is_active=True, can_pause=True,
                                      can_retry=False, failure="", active_status="Retrying")

        def remove(row):
            current = holder["state"]
            holder["state"] = replace(current, queued=current.queued[:row] + current.queued[row + 1:])

        ActivityDialog(
            self, snapshot_provider=lambda: holder["state"],
            pause=pause, cancel=cancel, retry=retry, remove=remove,
            confirm_remove=lambda _name: True,
        ).exec()

    def refresh_updates(self):
        self.home.updates_value.setText("Refresh complete · 3 games need attention")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", action="store_true", help="Use the 1280×800 Steam Deck target size.")
    parser.add_argument("--deck-720", action="store_true", help="Use the 1280×720 Steam Deck target size.")
    parser.add_argument("--state", choices=("normal", "loading", "empty", "error", "missing-sd", "large"), default="normal")
    parser.add_argument("--screen", choices=("home", "onboarding", "confirmation"), default="home")
    args = parser.parse_args()
    app = QApplication([])
    if args.screen == "confirmation":
        from ui.dialogs.themed_message_box import ThemedMessageBox
        with patch("ui.dialogs.themed_message_box.get_settings", return_value=MemorySettings()):
            dialog = ThemedMessageBox(
                "Remove queued game", "Remove Hades from the queue? You can add it again later.",
                ThemedMessageBox.StandardButton.Yes | ThemedMessageBox.StandardButton.No,
                ThemedMessageBox.StandardButton.No, severity="question",
            )
            dialog.show()
            return app.exec()
    if args.screen == "onboarding":
        from ui.dialogs.canary_welcome_dialog import CanaryWelcomeDialog

        class MockSteamEnvironment:
            is_flatpak = False

            def steam_found(self):
                return False

        with ExitStack() as stack:
            stack.enter_context(patch("ui.dialogs.canary_welcome_dialog.get_settings", return_value=MemorySettings()))
            stack.enter_context(patch("core.steam_helpers.get_steam_env", return_value=MockSteamEnvironment()))
            stack.enter_context(patch("core.steam_helpers.get_steam_libraries", return_value=[]))
            stack.enter_context(patch("utils.slssteam_integration.is_steam_process_running", return_value=False))
            for method in ("_start_gif", "_check_sls_installation", "_run_config_check_async", "_start_hubcap_validation"):
                stack.enter_context(patch.object(CanaryWelcomeDialog, method, lambda _dialog, *args, **kwargs: None))
            dialog = CanaryWelcomeDialog(manual=True)
            dialog.stack.setCurrentIndex(1)
            for control in dialog.findChildren(QAbstractButton):
                if not any(word in control.text().lower() for word in ("back", "next", "skip", "close", "✕")):
                    control.setEnabled(False)
            for control_type in (QLineEdit, QComboBox, QCheckBox):
                for control in dialog.findChildren(control_type):
                    control.setEnabled(False)
            dialog.show()
            return app.exec()
    window = MockHomeWindow(args.state)
    if args.deck:
        window.resize(1280, 800)
    elif args.deck_720:
        window.resize(1280, 720)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
