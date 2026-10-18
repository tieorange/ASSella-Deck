"""Keyboard and controller-compatible focus helpers for Qt widgets."""

from collections.abc import Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget


def configure_focus_order(widgets: Iterable[QWidget]) -> list[QWidget]:
    """Apply a predictable tab order and return usable widgets in that order."""
    usable = [widget for widget in widgets if widget is not None]
    for widget in usable:
        widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    for current, following in zip(usable, usable[1:]):
        QWidget.setTabOrder(current, following)
    return usable


def activate_focused() -> bool:
    """Click the focused button-like widget for controller A/Enter routing."""
    widget = QApplication.focusWidget()
    if widget is None or not widget.isEnabled():
        return False
    click = getattr(widget, "click", None)
    if callable(click):
        click()
        return True
    return False
