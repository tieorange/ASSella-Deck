"""Shared, screen-local navigation for keyboard and mapped Deck controls."""

from __future__ import annotations

from PyQt6.QtCore import QObject, QEvent, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QAbstractItemView, QAbstractSpinBox, QComboBox, QLineEdit, QSlider, QTextEdit, QWidget

from .focus import activate_focused, move_focus


class DeckNavigation(QObject):
    """Route navigation without swallowing text editing or native Qt selection."""

    def __init__(self, root: QWidget, *, back=None, search=None, actions=None, sections=None):
        super().__init__(root)
        self.root = root
        self.back = back
        self.search = search
        self.actions = actions
        self.sections = list(sections or [])
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() != QEvent.Type.KeyPress:
            return False
        if not isinstance(watched, QWidget) or not (watched is self.root or self.root.isAncestorOf(watched)):
            return False
        if watched.window() is not self.root.window():
            return False
        key = event.key()
        focus = QApplication.focusWidget()
        editing = isinstance(focus, (QLineEdit, QTextEdit))
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_Back):
            if callable(self.back):
                self.back()
                return True
        if editing:
            return False
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
            if not isinstance(focus, (QAbstractItemView, QAbstractSpinBox, QComboBox, QSlider)):
                return move_focus(self.root, key)
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return activate_focused()
        if key == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if self.search is not None:
                self.search.setFocus()
                return True
        if key == Qt.Key.Key_Menu and callable(self.actions):
            self.actions()
            return True
        if key in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown) and self.sections:
            visible = [widget for widget in self.sections if widget.isVisible() and widget.isEnabled()]
            if not visible:
                return False
            active = next((i for i, widget in enumerate(visible) if widget.isChecked()), 0)
            delta = -1 if key == Qt.Key.Key_PageUp else 1
            target = visible[(active + delta) % len(visible)]
            target.setFocus()
            target.click()
            return True
        return False


class FocusReturn:
    """Restore the entry control after a modal screen closes."""

    def __init__(self):
        self.entry = QApplication.focusWidget()

    def restore(self):
        if self.entry is not None and self.entry.isVisible() and self.entry.isEnabled():
            QTimer.singleShot(0, self.entry.setFocus)
