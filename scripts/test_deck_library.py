"""Focused Steam Deck library scan regression tests (run with PYTHONPATH=src)."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import sys
from collections import deque

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.steam_helpers import get_unavailable_steam_libraries
from managers.game_manager import GameManager
from ui.dialogs.library.scanner import LibraryScannerMixin
from ui.dialogs.library.filter_sort import LibraryFilterSortMixin
from ui.dialogs.library.image_loader import LibraryImageLoaderMixin
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QApplication, QLabel, QListWidget, QListWidgetItem


class LibraryPathTests(unittest.TestCase):
    def test_reports_unmounted_library(self):
        with tempfile.TemporaryDirectory() as directory:
            steam = Path(directory) / "Steam"
            (steam / "steamapps").mkdir(parents=True)
            missing = Path(directory) / "SD Card"
            (steam / "steamapps" / "libraryfolders.vdf").write_text(
                f'"libraryfolders"\n{{\n"1"\n{{\n"path" "{missing}"\n}}\n}}\n'
            )
            with patch("core.steam_helpers.find_steam_install", return_value=str(steam)):
                self.assertEqual(get_unavailable_steam_libraries(), [str(missing)])
                (missing / "steamapps").mkdir(parents=True)
                self.assertEqual(get_unavailable_steam_libraries(), [])


class GameManagerScanTests(unittest.TestCase):
    def setUp(self):
        self.cache = Mock()
        self.cache.get_games.return_value = []
        self.cache.save.return_value = None
        patcher = patch("utils.games_cache.get_games_cache", return_value=self.cache)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.manager = GameManager()

    def test_no_steam_library_preserves_cached_games(self):
        self.manager.games = [{"appid": "10", "game_name": "Cached"}]
        with patch("managers.game_manager.get_steam_libraries", return_value=[]), patch(
            "managers.game_manager.get_unavailable_steam_libraries", return_value=[]
        ):
            with self.assertRaises(FileNotFoundError):
                self.manager._perform_scan()
        self.assertEqual(len(self.manager.games), 1)
        self.cache.save.assert_not_called()

    def test_unmounted_card_retains_cached_game(self):
        game = {
            "appid": "10", "game_name": "Cached", "install_path": "/card/steamapps/common/Cached",
            "library_path": "/card", "is_accela_install": True,
        }
        self.manager.games = [game]
        with patch("managers.game_manager.get_steam_libraries", return_value=["/internal"]), patch(
            "managers.game_manager.get_unavailable_steam_libraries", return_value=["/card"]
        ), patch("managers.game_manager.find_steam_install", return_value="/internal"), patch.object(
            self.manager, "_build_acf_cache", return_value={}
        ), patch.object(self.manager, "_get_owned_steam_appids", return_value=set()), patch.object(
            self.manager, "_get_sls_additional_apps", return_value=set()
        ), patch.object(self.manager, "_scan_library", return_value=0), patch.object(
            self.manager, "_fix_slssteam_config"
        ), patch.object(self.manager, "_sync_games_to_slssteam_config"), patch.object(
            self.manager, "_sync_app_tokens_from_manifests"
        ), patch.object(self.manager, "_calculate_pending_sizes_async"):
            self.manager._perform_scan()
        self.assertTrue(self.manager.games[0]["library_unavailable"])

    def test_repeated_scan_is_rejected(self):
        self.manager.scan_runner = object()
        self.assertFalse(self.manager.scan_steam_libraries_async())

    def test_worker_error_clears_scan_state(self):
        errors = []
        self.manager.scan_failed.connect(errors.append)
        self.manager.is_scanning = True
        self.manager._on_scan_error((RuntimeError, RuntimeError("card removed"), ""))
        self.assertFalse(self.manager.is_scanning)
        self.assertEqual(errors, ["card removed"])

    def test_cancelled_scan_ignores_late_result(self):
        completions = []
        self.manager.scan_complete.connect(completions.append)
        self.manager.is_scanning = True
        self.manager.cancel_scan()
        self.manager._on_scan_finished(4)
        self.assertFalse(self.manager.is_scanning)
        self.assertEqual(completions, [])


class ScannerViewTests(unittest.TestCase):
    def test_failure_reenables_retry_without_clearing_cached_list(self):
        view = LibraryScannerMixin()
        view.scan_button = Mock()
        view.info_label = Mock()
        view.games_list = Mock()
        view._scanning = True
        view._refreshing = True
        view._on_scan_failed("Drive unavailable")
        view.scan_button.setEnabled.assert_called_with(True)
        view.games_list.clear.assert_not_called()
        self.assertFalse(view._scanning)
        self.assertFalse(view._refreshing)


class LargeLibraryViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_renders_in_bounded_batches(self):
        class View(LibraryFilterSortMixin):
            def _sort_games(self, games):
                return games

            def _add_game_to_list(self, game):
                self.games_list.addItem(game["game_name"])
                return 0

            def _start_pending_image_fetches(self):
                pass

            def _populate_ratings_badges(self):
                pass

        view = View()
        view._closing = False
        view._active_fetchers = {}
        view._image_fetch_queue = deque()
        view._pending_image_fetches = {}
        view._current_fetches = 0
        view._items_by_appid = {}
        view._manifest_mtimes = {}
        view.settings = None
        view.games_list = QListWidget()
        view.info_label = QLabel()
        view.game_manager = Mock()
        view.game_manager.get_all_games.return_value = [
            {"appid": str(i), "game_name": f"Game {i}", "is_accela_install": True}
            for i in range(95)
        ]
        callbacks = []
        with patch("ui.dialogs.library.filter_sort.QTimer.singleShot", side_effect=lambda _, fn: callbacks.append(fn)):
            view._refresh_game_list()
            self.assertEqual(view.games_list.count(), 0)
            callbacks.pop(0)()
            self.assertEqual(view.games_list.count(), 30)
            while callbacks:
                callbacks.pop(0)()
        self.assertEqual(view.games_list.count(), 95)
        self.assertFalse(view._refreshing)

    def test_artwork_queue_starts_with_visible_items(self):
        class View(LibraryImageLoaderMixin):
            pass

        view = View()
        view._closing = False
        view.games_list = QListWidget()
        view.games_list.resize(600, 400)
        view._pending_image_fetches = {}
        view._image_cache = {}
        view._fetch_item_image = Mock()
        for i in range(100):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, {"appid": str(i + 1)})
            item.setSizeHint(QSize(200, 50))
            view.games_list.addItem(item)
            view._pending_image_fetches[str(i + 1)] = item
        view.games_list.show()
        self.app.processEvents()
        view._start_pending_image_fetches()
        first_batch = view._fetch_item_image.call_count
        self.assertGreater(first_batch, 0)
        self.assertLess(first_batch, 100)
        view.games_list.verticalScrollBar().setValue(view.games_list.verticalScrollBar().maximum())
        self.app.processEvents()
        view._start_pending_image_fetches()
        self.assertGreater(view._fetch_item_image.call_count, first_batch)


if __name__ == "__main__":
    unittest.main()
