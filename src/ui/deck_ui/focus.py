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


def move_focus(root: QWidget, direction: Qt.Key) -> bool:
    """Move to the nearest visible control in a spatial direction."""
    current = QApplication.focusWidget()
    if current is None or not (current is root or root.isAncestorOf(current)):
        return False
    center = current.mapToGlobal(current.rect().center())
    candidates = []
    for widget in root.findChildren(QWidget):
        if widget is current or not widget.isVisible() or not widget.isEnabled():
            continue
        if widget.focusPolicy() not in (Qt.FocusPolicy.StrongFocus, Qt.FocusPolicy.TabFocus, Qt.FocusPolicy.WheelFocus):
            continue
        point = widget.mapToGlobal(widget.rect().center())
        dx, dy = point.x() - center.x(), point.y() - center.y()
        if direction == Qt.Key.Key_Left and dx >= -4 or direction == Qt.Key.Key_Right and dx <= 4:
            continue
        if direction == Qt.Key.Key_Up and dy >= -4 or direction == Qt.Key.Key_Down and dy <= 4:
            continue
        primary = abs(dx) if direction in (Qt.Key.Key_Left, Qt.Key.Key_Right) else abs(dy)
        secondary = abs(dy) if direction in (Qt.Key.Key_Left, Qt.Key.Key_Right) else abs(dx)
        candidates.append((primary + secondary * 2, widget))
    if not candidates:
        return False
    min(candidates, key=lambda item: item[0])[1].setFocus()
    return True
