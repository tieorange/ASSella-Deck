"""Focused checks for the reusable action-first Home presentation."""

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6.QtWidgets import QApplication

from ui.deck_ui.home import DeckHomeOverview, HomeSnapshot


APP = QApplication.instance() or QApplication([])


class DeckHomeOverviewTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.widget = DeckHomeOverview(
            open_library=lambda: self.calls.append("library"),
            find_game=lambda: self.calls.append("find"),
            open_activity=lambda: self.calls.append("activity"),
            refresh_updates=lambda: self.calls.append("refresh"),
        )

    def test_primary_actions_are_focusable_and_connected(self):
        for button in (
            self.widget.library_button,
            self.widget.find_button,
            self.widget.activity_button,
            self.widget.refresh_button,
        ):
            self.assertTrue(button.focusPolicy())
            button.click()
        self.assertEqual(self.calls, ["library", "find", "activity", "refresh"])

    def test_snapshot_updates_all_summaries(self):
        self.widget.apply_snapshot(HomeSnapshot("Games", "Updates", "Activity", "Storage"))
        self.assertEqual(self.widget.library_value.text(), "Games")
        self.assertEqual(self.widget.updates_value.text(), "Updates")
        self.assertEqual(self.widget.activity_value.text(), "Activity")
        self.assertEqual(self.widget.storage_value.text(), "Storage")


if __name__ == "__main__":
    unittest.main()
