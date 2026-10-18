"""Small reusable widgets for the Deck redesign."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .theme import TEXT, TOUCH, button_style


class DeckCard(QFrame):
    """An elevated content surface with a consistent controller focus outline."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("deckCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            """
            QFrame#deckCard {
                background: #1c2836;
                border: 1px solid rgba(255, 255, 255, 0.11);
                border-radius: 14px;
            }
            QFrame#deckCard:focus-within {
                border: 2px solid #43d6c1;
            }
            """
        )


class DeckActionButton(QPushButton):
    """A large, focusable action button appropriate for Deck controls."""

    def __init__(self, text: str, *, primary: bool = False, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(TOUCH)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("deckPrimaryAction" if primary else "deckSecondaryAction")
        self.setStyleSheet(button_style(primary=primary))


class DeckSectionTitle(QWidget):
    """A title and concise supporting message for a primary content section."""

    def __init__(self, title: str, description: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        heading = QLabel(title)
        heading.setStyleSheet(f"color: {TEXT}; font-size: 16pt; font-weight: 800;")
        layout.addWidget(heading)
        if description:
            subtitle = QLabel(description)
            subtitle.setWordWrap(True)
            subtitle.setStyleSheet("color: #b8cad5; font-size: 10.5pt;")
            layout.addWidget(subtitle)


class DeckNotice(QFrame):
    """Persistent status or recovery text that remains readable during loading."""

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("deckNotice")
        self.setStyleSheet("QFrame#deckNotice { background:#1d3040; border:1px solid #467087; border-radius:10px; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:#dcecf5; font-size:10.5pt;")
        layout.addWidget(self.label)
        self.action_button = DeckActionButton("Retry")
        self.action_button.setMaximumWidth(170)
        self.action_button.setVisible(False)
        self._action_callback = None
        layout.addWidget(self.action_button)

    def setText(self, text: str):
        self.label.setText(text)

    def setTone(self, tone: str):
        border, background, foreground = {
            "warning": ("#9b7840", "#332c22", "#f6d79c"),
            "error": ("#a85e58", "#392726", "#ffd0c8"),
        }.get(tone, ("#467087", "#1d3040", "#dcecf5"))
        self.setStyleSheet(
            f"QFrame#deckNotice {{ background:{background}; border:1px solid {border}; border-radius:10px; }}"
        )
        self.label.setStyleSheet(f"color:{foreground}; font-size:10.5pt;")

    def setAction(self, text: str, callback=None):
        if self._action_callback is not None:
            self.action_button.clicked.disconnect(self._action_callback)
        self._action_callback = callback
        if callback is not None:
            self.action_button.setText(text)
            self.action_button.clicked.connect(callback)
        self.action_button.setVisible(callback is not None)


class DeckStepHeader(QWidget):
    """Compact progress rail for onboarding and guided installation."""

    def __init__(self, steps: tuple[str, ...], parent: QWidget | None = None):
        super().__init__(parent)
        self.steps = steps
        self.labels = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for i, title in enumerate(steps):
            label = QLabel(f"{i + 1}  {title}")
            label.setStyleSheet("color:#95aabd; background:#243343; border-radius:9px; padding:8px 11px; font-weight:700;")
            layout.addWidget(label, 1)
            self.labels.append(label)
        self.set_step(0)

    def set_step(self, index: int):
        for i, label in enumerate(self.labels):
            if i == index:
                label.setStyleSheet("color:#062022; background:#43d6c1; border-radius:9px; padding:8px 11px; font-weight:800;")
            elif i < index:
                label.setStyleSheet("color:#d6f4e9; background:#24565a; border-radius:9px; padding:8px 11px; font-weight:700;")
            else:
                label.setStyleSheet("color:#95aabd; background:#243343; border-radius:9px; padding:8px 11px; font-weight:700;")


def labeled_status(label: str, value: QLabel, parent: QWidget | None = None) -> QWidget:
    """Compose a compact semantic status row while preserving its value label."""
    row = QWidget(parent)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    key = QLabel(label)
    key.setStyleSheet("color: rgba(244,247,251,0.58); font-size: 9pt;")
    layout.addWidget(key)
    layout.addWidget(value, 1)
    return row
