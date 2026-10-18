"""Focused Steam Deck library scan regression tests (run with PYTHONPATH=src)."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.steam_helpers import get_unavailable_steam_libraries
from managers.game_manager import GameManager
from ui.dialogs.library.scanner import LibraryScannerMixin


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


if __name__ == "__main__":
    unittest.main()
