"""Protect the fork's runtime data and self-update paths."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from managers.app_update_manager import install_update_candidate
from ui.dialogs.themed_message_box import ThemedMessageBox
from utils.fork_identity import APPIMAGE_NAME
from utils.helpers import get_base_path
from utils.settings import APP_NAME

_tab_path = Path(__file__).resolve().parents[1] / "src/ui/dialogs/settings_tabs/assela_tab.py"
_tab_spec = importlib.util.spec_from_file_location("assella_deck_settings_tab_test", _tab_path)
_tab_module = importlib.util.module_from_spec(_tab_spec)
_tab_spec.loader.exec_module(_tab_module)
uninstall_assela = _tab_module.uninstall_assela


class ForkRuntimeIdentityTests(unittest.TestCase):
    def test_data_and_settings_names_are_distinct(self):
        with tempfile.TemporaryDirectory() as root:
            with patch("platform.system", return_value="Linux"), patch.dict(
                "os.environ", {"XDG_DATA_HOME": root}
            ):
                self.assertEqual(get_base_path(), Path(root) / "ASSella-Deck")
        self.assertEqual(APP_NAME, "ASSella-Deck")

    def test_self_update_replaces_only_fork_appimage(self):
        with tempfile.TemporaryDirectory() as root:
            data = Path(root)
            fork_dir = data / "ASSella-Deck"
            old_dir = data / "ACCELA"
            fork_dir.mkdir()
            old_dir.mkdir()
            installed = fork_dir / APPIMAGE_NAME
            candidate = fork_dir / (APPIMAGE_NAME + ".part")
            legacy = old_dir / "ASSella.AppImage"
            installed.write_bytes(b"fork old")
            candidate.write_bytes(b"fork new")
            legacy.write_bytes(b"upstream")
            with patch("managers.app_update_manager.get_base_path", return_value=fork_dir):
                install_update_candidate(candidate, installed)
                self.assertEqual(installed.read_bytes(), b"fork new")
                self.assertEqual((fork_dir / (APPIMAGE_NAME + ".previous")).read_bytes(), b"fork old")
                self.assertEqual(legacy.read_bytes(), b"upstream")
                with self.assertRaises(ValueError):
                    install_update_candidate(installed, legacy)
                self.assertEqual(legacy.read_bytes(), b"upstream")

    def test_in_app_uninstall_keeps_other_apps(self):
        with tempfile.TemporaryDirectory() as root:
            data = Path(root)
            fork_dir = data / "ASSella-Deck"
            old_dir = data / "ACCELA"
            fork_dir.mkdir()
            old_dir.mkdir()
            (fork_dir / APPIMAGE_NAME).write_bytes(b"fork")
            upstream = old_dir / "ASSella.AppImage"
            upstream.write_bytes(b"upstream")
            old_desktop = data / "applications/assella.desktop"
            old_desktop.parent.mkdir()
            old_desktop.write_text("upstream desktop")
            deck_desktop = data / "applications/assella-deck.desktop"
            deck_desktop.write_text("fork desktop")
            with (
                patch.dict("os.environ", {"XDG_DATA_HOME": root}),
                patch("utils.helpers.get_base_path", return_value=fork_dir),
                patch.object(
                    ThemedMessageBox, "question",
                    return_value=ThemedMessageBox.StandardButton.Yes,
                ),
                patch.object(ThemedMessageBox, "information"),
            ):
                uninstall_assela(None)
            self.assertFalse((fork_dir / APPIMAGE_NAME).exists())
            self.assertFalse(deck_desktop.exists())
            self.assertEqual(upstream.read_bytes(), b"upstream")
            self.assertEqual(old_desktop.read_text(), "upstream desktop")


if __name__ == "__main__":
    unittest.main()
