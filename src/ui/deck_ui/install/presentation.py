"""One guided shell for finding, selecting, and queueing a game."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QButtonGroup, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QStackedWidget, QVBoxLayout, QWidget

from ..focus import configure_focus_order
from ..navigation import DeckNavigation, FocusReturn
from ..widgets import DeckActionButton, DeckCard, DeckNotice, DeckSectionTitle, DeckStepHeader
from ..theme import BG, TEXT, TOUCH, field_style
from .data import draft_from_selection, persist_draft


class DeckInstallFlow(QDialog):
    STEPS = ("Find", "Build & depots", "Storage & backend", "Review")

    def __init__(self, main_window, initial_query: str = "", *, mock: bool = False, mock_state: str = "normal"):
        super().__init__(main_window)
        self.main_window = main_window
        self.mock = mock
        self.mock_state = mock_state
        self._focus_return = FocusReturn()
        self.draft = None
        self._queued = False
        self.selector = None
        self._parsed = None
        self.setWindowTitle("Find and install · ASSella Deck")
        self.resize(1040, 620)
        self.setMinimumSize(720, 460)
        self.setStyleSheet(f"QDialog {{ background:{BG}; color:{TEXT}; }} QLabel {{ color:{TEXT}; }}" + field_style())
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 16, 22, 18)
        root.setSpacing(12)
        root.addWidget(DeckSectionTitle("Find and install", "Choose a game, review its content and storage, then add it to the queue."))
        self.steps = DeckStepHeader(self.STEPS)
        root.addWidget(self.steps)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)
        self.notice = DeckNotice("Search by game name or App ID to begin.")
        root.addWidget(self.notice)

        if mock:
            self.discovery = self._make_mock_discovery()
        else:
            from ui.dialogs.fetchmanifest import FetchManifestDialog
            self.discovery = FetchManifestDialog(main_window, initial_query=initial_query, guided=True)
            self.discovery.manifest_ready.connect(self._on_manifest_ready)
            self.discovery.accepted.connect(lambda: QTimer.singleShot(0, self.accept))
            self.discovery.setParent(self)
            self.discovery.setWindowFlags(Qt.WindowType.Widget)
            self.discovery.setMinimumSize(0, 0)
            self.discovery.title_bar.hide()
        self.stack.addWidget(self.discovery)

        self.backend_page = self._make_backend_page()
        self.stack.addWidget(self.backend_page)
        self.review_page = self._make_review_page()
        self.stack.addWidget(self.review_page)

        footer = QHBoxLayout()
        self.back_button = DeckActionButton("Back")
        self.back_button.clicked.connect(self._back)
        self.recommendation_button = DeckActionButton("Use recommended build")
        self.recommendation_button.clicked.connect(self._apply_recommendation)
        self.recommendation_button.hide()
        self.next_button = DeckActionButton("Next", primary=True)
        self.next_button.clicked.connect(self._next)
        footer.addWidget(self.back_button)
        footer.addWidget(self.recommendation_button)
        footer.addStretch()
        footer.addWidget(self.next_button)
        root.addLayout(footer)
        self._navigation = DeckNavigation(self, back=self._back, search=self.discovery.search_input)
        self._set_step(0)
        QTimer.singleShot(0, self.discovery.search_input.setFocus)

    def _make_mock_discovery(self):
        class MemorySettings:
            def __init__(self):
                self.values = {}

            def setValue(self, key, value):
                self.values[key] = value

        page = QWidget()
        page.settings = MemorySettings()
        layout = QVBoxLayout(page)
        layout.addWidget(DeckSectionTitle("Discover a game", "Fixture data for safe visual review."))
        page.search_input = QLineEdit("Hades")
        page.search_input.setMinimumHeight(TOUCH)
        page.search_input.setStyleSheet(field_style())
        layout.addWidget(page.search_input)
        fixture = DeckActionButton("Select Hades · App ID 1145360", primary=True)
        fixture.clicked.connect(lambda: self._on_manifest_ready((
            {"appid": "1145360", "game_name": "Hades", "depots": {"1145361": {"desc": "Base game"}}, "buildid": "123456"},
            "/mock/hades.zip", "public", {},
        )))
        layout.addWidget(fixture)
        layout.addStretch()
        return page

    def _make_backend_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(14)
        layout.addWidget(DeckSectionTitle("Storage and download method", "Confirm where the game goes and how it downloads."))
        self.storage_label = QLabel()
        self.storage_label.setWordWrap(True)
        self.storage_label.setStyleSheet("font-size:12pt; color:#bdd8e3; padding:12px;")
        layout.addWidget(self.storage_label)
        card = DeckCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        self.assella_radio = QRadioButton("ASSella Downloader · use the selected depots and build")
        self.native_radio = QRadioButton("Steam client · hand off the download to Steam")
        for radio in (self.assella_radio, self.native_radio):
            radio.setMinimumHeight(TOUCH)
            radio.setStyleSheet("QRadioButton { color:#f4f7fb; font-size:11pt; spacing:12px; padding:8px; } QRadioButton:focus { border:2px solid #43d6c1; border-radius:8px; }")
            card_layout.addWidget(radio)
        self.assella_radio.setChecked(True)
        if not self.mock:
            try:
                from utils.plugin_manager import are_plugins_present, is_plugin_check_bypassed
                native_available = are_plugins_present() or is_plugin_check_bypassed()
            except Exception:
                native_available = False
            self.native_radio.setEnabled(native_available)
            if not native_available:
                self.native_radio.setToolTip("Steam client handoff requires the native integration plugin.")
        group = QButtonGroup(page)
        group.addButton(self.assella_radio)
        group.addButton(self.native_radio)
        self._backend_group = group
        layout.addWidget(card)
        layout.addStretch()
        configure_focus_order((self.assella_radio, self.native_radio))
        return page

    def _make_review_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(12)
        layout.addWidget(DeckSectionTitle("Review your install", "Nothing starts until you choose Add to Queue."))
        card = DeckCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(9)
        self.review_labels = []
        self.review_keys = []
        for _ in range(6):
            row = QHBoxLayout()
            key = QLabel()
            key.setMinimumWidth(110)
            key.setStyleSheet("font-size:10.5pt; color:#b8cad5; font-weight:700;")
            value = QLabel()
            value.setWordWrap(True)
            value.setStyleSheet("font-size:11pt; color:#f4f7fb; font-weight:650;")
            row.addWidget(key)
            row.addWidget(value, 1)
            card_layout.addLayout(row)
            self.review_keys.append(key)
            self.review_labels.append(value)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _set_step(self, step: int):
        self.step = step
        self.steps.set_step(step)
        self.stack.setCurrentWidget((self.discovery, self.selector, self.backend_page, self.review_page)[step])
        self.back_button.setText("Close" if step == 0 else "Back")
        self.next_button.setVisible(step != 0)
        self.next_button.setText("Add to Queue" if step == 3 else "Next")
        self.recommendation_button.setVisible(step == 1 and bool(getattr(self, "_recommendation", None)))
        if step == 1 and self.selector:
            self.selector.show()
        if step == 2:
            if self.mock:
                self.storage_label.setText(f"Selected storage: {self.selector.get_storage_label()}")
            else:
                from ui.dialogs.depot_selection.storage_targets import describe
                target = describe(self.draft.storage)
                free = f" · {target.free}" if target.free else ""
                self.storage_label.setText(f"Selected storage: {target.label}{free}\n{self.draft.storage}")
            self.assella_radio.setFocus()
        elif step == 3:
            if self.mock:
                storage_label = self.selector.get_storage_label()
            else:
                from ui.dialogs.depot_selection.storage_targets import describe
                target = describe(self.draft.storage)
                storage_label = target.label + (f" · {target.free}" if target.free else "")
            for key, value, (title, text) in zip(self.review_keys, self.review_labels, self.draft.review_items(storage_label)):
                key.setText(title)
                value.setText(text)
            self.next_button.setFocus()

    def _on_manifest_ready(self, payload):
        parsed, package, branch, metadata = payload
        self._parsed = payload
        if self.selector is not None:
            self.stack.removeWidget(self.selector)
            self.selector.deleteLater()
        if self.mock:
            self.selector = _MockSelector(missing_sd=self.mock_state == "missing-sd")
        else:
            from ui.dialogs.depotselection import DepotSelectionDialog
            self.selector = DepotSelectionDialog(
                parsed["appid"], parsed.get("game_name", ""), parsed["depots"],
                parsed.get("header_url"), self,
                library_path=metadata.get("library_path"), branch=branch,
                branches=getattr(self.discovery, "_discovered_branches", None) or {"public": {}},
                current_build_id=parsed.get("buildid", ""),
                missing_hubcap_depots=parsed.get("missing_depots_from_hubcap") or [],
                missing_depots_info=parsed.get("missing_depots_info") or {},
                refetched_depots=parsed.get("refetched_depots") or [],
            )
            self.selector.setWindowFlags(Qt.WindowType.Widget)
            self.selector.setMinimumSize(0, 0)
            if hasattr(self.selector, "title_bar"):
                self.selector.title_bar.hide()
            self.selector.accepted.connect(self._on_selection_confirmed)
        self.stack.insertWidget(1, self.selector)
        self._recommendation = None
        if not self.mock and hasattr(self.selector, "_apply_build_selection"):
            try:
                from managers.voices_manager import VoicesManager
                self._recommendation = VoicesManager.get_instance().get_recommendation(
                    str(parsed["appid"]), parsed.get("game_name", "")
                )
                if not (self._recommendation or {}).get("recommended_build_id"):
                    self._recommendation = None
            except Exception:
                self._recommendation = None
        self.notice.setText("Choose content, build, and storage. Review your choices before queueing.")
        self._set_step(1)

    def _apply_recommendation(self):
        recommendation = getattr(self, "_recommendation", None) or {}
        build_id = str(recommendation.get("recommended_build_id") or "")
        if not build_id or not hasattr(self.selector, "_apply_build_selection"):
            return
        overrides = {str(depot): {"manifest_id": str(manifest)} for depot, manifest in (recommendation.get("manifest_overrides") or {}).items()}
        if not overrides:
            try:
                from core.steamdb_scraper import SteamDBBuildsCache
                cached = SteamDBBuildsCache().get_build_depots(build_id) or {}
                overrides = {str(depot): {"manifest_id": str(manifest)} for depot, manifest in cached.items()}
            except Exception:
                overrides = {}
        self.selector._apply_build_selection(build_id, overrides)
        self.notice.setText(f"Recommended build {build_id} selected. Check its depots and storage, then continue.")

    def _on_selection_confirmed(self):
        parsed, package, branch, metadata = self._parsed
        try:
            self.draft = draft_from_selection(parsed, package, branch, metadata, self.selector)
        except ValueError as error:
            self.notice.setText(str(error))
            self.selector.show()
            return
        self.notice.setText("Choose a download method. You can still go back and adjust content or storage.")
        self._set_step(2)

    def _next(self):
        if self.step == 1:
            if self.mock:
                self._on_selection_confirmed()
            else:
                confirm = getattr(self.selector, "_on_ok_clicked", self.selector.accept)
                confirm()
        elif self.step == 2:
            self.draft.backend = "native" if self.native_radio.isChecked() else "assella"
            self.draft.metadata["download_backend"] = self.draft.backend
            self._set_step(3)
        elif self.step == 3:
            if self.mock:
                self.notice.setText("Mock review complete. No job was queued.")
                return
            if self._queued:
                return
            from utils.paths import is_valid_download_directory
            if not Path(self.draft.package_path).is_file():
                self.notice.setText("The downloaded package is no longer available. Go Back and choose the game again.")
                return
            if not is_valid_download_directory(self.draft.storage):
                self.notice.setText("The selected storage is unavailable. Reconnect it or go Back to choose another location.")
                return
            self._queued = True
            self.next_button.setEnabled(False)
            try:
                persist_draft(self.discovery.settings, self.draft, self._parsed[0])
                self.main_window.job_queue.add_job(self.draft.package_path, self.draft.metadata)
            except Exception as error:
                self._queued = False
                self.next_button.setEnabled(True)
                self.notice.setText(f"Could not add this game to the queue: {error}. Review your choices and retry.")
                return
            self.accept()

    def _back(self):
        if self.step == 0:
            self.reject()
        elif self.step == 3:
            self._set_step(2)
        elif self.step == 2:
            self._set_step(1)
        else:
            self._set_step(0)

    def done(self, result):
        if not self.mock:
            self.discovery.reject()
            if self.selector is not None:
                self.selector.close()
        self._focus_return.restore()
        super().done(result)


class _MockSelector(QWidget):
    def __init__(self, *, missing_sd: bool = False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(DeckSectionTitle("Hades · content and build", "Choose a branch, build, content, and storage."))
        card = DeckCard()
        fields = QVBoxLayout(card)
        fields.setContentsMargins(20, 16, 20, 16)
        fields.setSpacing(10)
        self.branch = QComboBox()
        self.branch.addItems(("public", "beta"))
        self.build = QComboBox()
        self.build.addItems(("Latest available", "Build 123456"))
        self.depot = QCheckBox("Base game depot · 1145361")
        self.depot.setChecked(True)
        self.storage = QComboBox()
        self.storage.addItem("Internal storage · 118 GB free", "/mock/internal/SteamLibrary")
        self.storage.addItem("microSD · 72 GB free" if not missing_sd else "microSD unavailable", "/mock/microSD/SteamLibrary")
        if missing_sd:
            self.storage.model().item(1).setEnabled(False)
        for title, control in (("Branch", self.branch), ("Build", self.build), ("Content", self.depot), ("Storage", self.storage)):
            label = QLabel(title)
            label.setStyleSheet("color:#b8cad5; font-size:10pt; font-weight:700;")
            fields.addWidget(label)
            control.setMinimumHeight(TOUCH)
            if isinstance(control, QComboBox):
                control.setStyleSheet(field_style())
            else:
                control.setStyleSheet("QCheckBox { color:#f4f7fb; font-size:11pt; spacing:12px; padding:8px; } QCheckBox:focus { border:2px solid #43d6c1; }")
            fields.addWidget(control)
        layout.addWidget(card)
        layout.addStretch()

    def get_selected_depots(self):
        return ["1145361"] if self.depot.isChecked() else []

    def get_selected_storage(self):
        return self.storage.currentData()

    def get_storage_label(self):
        return self.storage.currentText()

    def get_selected_branch(self):
        return self.branch.currentText()

    def is_build_pinned(self):
        return self.build.currentIndex() == 1

    def get_selected_build(self):
        return "123456" if self.is_build_pinned() else ""
