#!/usr/bin/env python3
"""Focused navigation, guided review, and Activity behavior without services."""

import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QWidget

from ui.deck_ui.activity.domain import ActivitySnapshot
from ui.deck_ui.activity.presentation import ActivityDialog
from ui.deck_ui.install.presentation import DeckInstallFlow
from ui.deck_ui.navigation import DeckNavigation


class DeckNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_back_and_section_switch(self):
        root = QWidget()
        root.resize(300, 100)
        first = QPushButton("First", root)
        second = QPushButton("Second", root)
        first.move(10, 10)
        second.move(150, 10)
        first.setCheckable(True)
        second.setCheckable(True)
        first.setChecked(True)
        calls = []
        nav = DeckNavigation(root, back=lambda: calls.append("back"), sections=(first, second))
        root.show()
        second.show()
        root.activateWindow()
        self.app.processEvents()
        first.setFocus()
        QTest.keyClick(first, Qt.Key.Key_Right)
        self.assertTrue(second.hasFocus())
        first.setFocus()
        QTest.keyClick(first, Qt.Key.Key_PageDown)
        self.assertTrue(second.isChecked())
        QTest.keyClick(second, Qt.Key.Key_Escape)
        self.assertEqual(calls, ["back"])
        root.close()

    def test_guided_review_requires_final_action(self):
        flow = DeckInstallFlow(None, mock=True)
        flow.show()
        button = flow.discovery.findChildren(QPushButton)[0]
        button.click()
        self.assertEqual(flow.step, 1)
        flow._next()
        self.assertEqual(flow.step, 2)
        flow.native_radio.setChecked(True)
        flow._next()
        self.assertEqual(flow.step, 3)
        self.assertEqual(flow.draft.metadata["download_backend"], "native")
        self.assertIn("Steam client", flow.review_labels[-1].text())
        flow._back()
        self.assertEqual(flow.step, 2)
        flow._next()
        flow._next()
        self.assertIn("No job was queued", flow.notice.label.text())
        flow.close()

    def test_production_discovery_embeds_without_starting_services(self):
        from ui.dialogs.fetchmanifest import FetchManifestDialog

        with TemporaryDirectory() as temporary:
            parent = QDialog()
            parent.settings = QSettings(str(Path(temporary) / "settings.ini"), QSettings.Format.IniFormat)
            parent.show()
            with patch.object(FetchManifestDialog, "_request_api_status_update"), patch.object(FetchManifestDialog, "_scan_cached_app_ids", return_value=set()):
                flow = DeckInstallFlow(parent)
                self.assertIsInstance(flow.discovery, FetchManifestDialog)
                self.assertEqual(flow.stack.currentWidget(), flow.discovery)
                self.assertEqual(flow.step, 0)
                flow.close()
            parent.close()

    def test_activity_controls_and_queue(self):
        calls = []
        state = ActivitySnapshot(
            active_name="Hades", active_status="Downloading", is_active=True,
            can_pause=True, queued=("Celeste",), progress=42, progress_known=True,
        )
        dialog = ActivityDialog(
            snapshot_provider=lambda: state,
            pause=lambda: calls.append("pause"),
            cancel=lambda: calls.append("cancel"),
            retry=lambda: calls.append("retry"),
            remove=lambda row: calls.append(("remove", row)),
            confirm_remove=lambda _name: True,
        )
        dialog.show()
        dialog.pause_button.click()
        dialog.queue_list.setCurrentRow(0)
        dialog.remove_button.click()
        self.assertEqual(calls, ["pause", ("remove", 0)])
        self.assertEqual(dialog.progress.value(), 42)
        dialog.close()

    def test_failed_package_can_be_requeued_when_file_remains(self):
        from managers.task_manager import TaskManager

        queued = []
        with TemporaryDirectory() as temporary:
            package = Path(temporary) / "game.zip"
            package.write_bytes(b"fixture")
            task = SimpleNamespace(
                last_failed_job={"path": str(package), "metadata": {"game_name": "Hades"}},
                main_window=SimpleNamespace(job_queue=SimpleNamespace(add_job=lambda path, metadata: queued.append((path, metadata)))),
            )
            self.assertTrue(TaskManager.retry_failed_job(task))
            self.assertEqual(queued, [(str(package), {"game_name": "Hades"})])
            self.assertIsNone(task.last_failed_job)

    def test_game_details_section_rail_switches_pages(self):
        from run_ui_mock import MockHomeWindow

        home = MockHomeWindow()
        home.show()

        def check_and_close(dialog):
            dialog._tab_buttons[1].click()
            self.assertEqual(dialog.stacked.currentIndex(), 1)
            self.assertFalse(dialog._tab_buttons[0].isChecked())
            self.assertTrue(dialog._tab_buttons[1].isChecked())
            QTimer.singleShot(0, dialog.accept)

        home.open_details_preview(home, on_open=check_and_close)
        home.close()


if __name__ == "__main__":
    unittest.main()
