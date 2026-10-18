"""Controller friendly queue and current task screen."""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QProgressBar, QVBoxLayout, QWidget

from ..focus import configure_focus_order
from ..navigation import DeckNavigation, FocusReturn
from ..widgets import DeckActionButton, DeckCard, DeckSectionTitle
from .data import snapshot_from_main_window
from .domain import ActivitySnapshot


class ActivityDialog(QDialog):
    def __init__(self, main_window=None, *, snapshot_provider=None, pause=None, cancel=None, retry=None, remove=None, confirm_remove=None):
        super().__init__(main_window)
        self._focus_return = FocusReturn()
        self.main_window = main_window
        self.snapshot_provider = snapshot_provider or (lambda: snapshot_from_main_window(main_window))
        task = getattr(main_window, "task_manager", None)
        queue = getattr(main_window, "job_queue", None)
        self.pause_action = pause or (task.toggle_pause if task else lambda: None)
        self.cancel_action = cancel or (task.cancel_current_job if task else lambda: None)
        self.retry_action = retry or (task.retry_failed_job if task else lambda: None)
        self.remove_action = remove or (queue.remove_job_at if queue else lambda index: None)
        self.confirm_remove = confirm_remove or self._confirm_remove
        self.setWindowTitle("Activity · ASSella Deck")
        self.resize(840, 650)
        self.setMinimumSize(640, 460)
        self.setStyleSheet("QDialog { background: #111722; color: #f4f7fb; } QLabel { color: #f4f7fb; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)
        root.addWidget(DeckSectionTitle("Activity", "Follow downloads and manage what's next."))
        current = DeckCard()
        current_layout = QVBoxLayout(current)
        current_layout.setContentsMargins(20, 18, 20, 18)
        self.active_name = QLabel()
        self.active_name.setStyleSheet("font-size: 18pt; font-weight: 800;")
        self.active_status = QLabel()
        self.active_status.setStyleSheet("color: #a7bac9; font-size: 11pt;")
        self.progress = QProgressBar()
        self.progress.setMinimumHeight(18)
        self.progress.setStyleSheet("QProgressBar { background:#253244; border:0; border-radius:8px; color:white; } QProgressBar::chunk { background:#43d6c1; border-radius:8px; }")
        current_layout.addWidget(self.active_name)
        current_layout.addWidget(self.active_status)
        current_layout.addWidget(self.progress)
        controls = QHBoxLayout()
        self.pause_button = DeckActionButton("Pause")
        self.cancel_button = DeckActionButton("Cancel job")
        self.retry_button = DeckActionButton("Retry failed job")
        self.pause_button.clicked.connect(self._pause)
        self.cancel_button.clicked.connect(self._cancel)
        self.retry_button.clicked.connect(self._retry)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.cancel_button)
        controls.addWidget(self.retry_button)
        controls.addStretch()
        current_layout.addLayout(controls)
        root.addWidget(current)
        self.failure = QLabel()
        self.failure.setWordWrap(True)
        self.failure.setStyleSheet("color:#ffbaa9; padding:8px;")
        root.addWidget(self.failure)
        root.addWidget(DeckSectionTitle("Up next"))
        self.queue_list = QListWidget()
        self.queue_list.currentRowChanged.connect(lambda row: self.remove_button.setEnabled(row >= 0) if hasattr(self, "remove_button") else None)
        self.queue_list.setStyleSheet("QListWidget { background:#1e2530; border:1px solid #384a5b; border-radius:12px; padding:8px; color:white; font-size:11pt; } QListWidget::item { padding:9px; } QListWidget::item:selected { background:#275c61; border-radius:7px; }")
        root.addWidget(self.queue_list, 1)
        footer = QHBoxLayout()
        self.remove_button = DeckActionButton("Remove selected")
        self.remove_button.clicked.connect(self._remove)
        back = DeckActionButton("Back", primary=True)
        back.clicked.connect(self.accept)
        footer.addWidget(self.remove_button)
        footer.addStretch()
        footer.addWidget(back)
        root.addLayout(footer)
        configure_focus_order((self.pause_button, self.cancel_button, self.retry_button, self.queue_list, self.remove_button, back))
        self._navigation = DeckNavigation(self, back=self.reject)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(400)
        self.refresh()
        QTimer.singleShot(0, back.setFocus)

    def refresh(self):
        state = self.snapshot_provider()
        self.active_name.setText(state.active_name)
        self.active_status.setText(state.active_status)
        self.progress.setVisible(state.is_active)
        if state.is_active:
            self.progress.setRange(0, 100 if state.progress_known else 0)
            if state.progress_known:
                self.progress.setValue(state.progress)
        self.pause_button.setEnabled(state.can_pause)
        self.pause_button.setText("Resume" if state.is_paused else "Pause")
        self.cancel_button.setEnabled(state.is_active)
        self.retry_button.setVisible(state.can_retry)
        self.failure.setText(state.failure)
        self.failure.setVisible(bool(state.failure))
        if tuple(self.queue_list.item(i).text() for i in range(self.queue_list.count())) != state.queued:
            row = self.queue_list.currentRow()
            self.queue_list.clear()
            self.queue_list.addItems(state.queued)
            if row >= 0 and row < self.queue_list.count():
                self.queue_list.setCurrentRow(row)
        self.remove_button.setEnabled(self.queue_list.currentRow() >= 0)

    def _pause(self):
        self.pause_action()
        self.refresh()

    def _cancel(self):
        self.cancel_action()
        self.refresh()

    def _retry(self):
        self.retry_action()
        self.refresh()

    def _remove(self):
        row = self.queue_list.currentRow()
        if row >= 0 and self.confirm_remove(self.queue_list.item(row).text()):
            self.remove_action(row)
            self.refresh()

    def _confirm_remove(self, game_name: str) -> bool:
        from ui.dialogs.themed_message_box import ThemedMessageBox

        answer = ThemedMessageBox.question(
            self, "Remove queued game", f"Remove {game_name} from the queue?",
            ThemedMessageBox.StandardButton.Yes | ThemedMessageBox.StandardButton.No,
            ThemedMessageBox.StandardButton.No,
        )
        return answer == ThemedMessageBox.StandardButton.Yes

    def done(self, result):
        self._timer.stop()
        self._focus_return.restore()
        super().done(result)
        self.deleteLater()
