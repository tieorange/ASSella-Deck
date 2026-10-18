"""Small reusable widgets for the Deck redesign."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class DeckCard(QFrame):
    """An elevated content surface with a consistent controller focus outline."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("deckCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            """
            QFrame#deckCard {
                background: rgba(30, 37, 48, 0.94);
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
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            self.setObjectName("deckPrimaryAction")
            background = "#43d6c1"
            foreground = "#061b1b"
        else:
            self.setObjectName("deckSecondaryAction")
            background = "rgba(255, 255, 255, 0.08)"
            foreground = "#f4f7fb"
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {background}; color: {foreground}; border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 10px; padding: 0 18px; font-size: 11pt; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(83, 222, 202, 0.86); color: #061b1b; }}
            QPushButton:focus {{ border: 3px solid #f4f7fb; }}
            QPushButton:disabled {{ background: rgba(255,255,255,0.05); color: rgba(244,247,251,0.38); }}
            """
        )


class DeckSectionTitle(QWidget):
    """A title and concise supporting message for a primary content section."""

    def __init__(self, title: str, description: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        heading = QLabel(title)
        heading.setStyleSheet("color: #f4f7fb; font-size: 15pt; font-weight: 800;")
        layout.addWidget(heading)
        if description:
            subtitle = QLabel(description)
            subtitle.setWordWrap(True)
            subtitle.setStyleSheet("color: rgba(244,247,251,0.65); font-size: 10pt;")
            layout.addWidget(subtitle)


class DeckNotice(QFrame):
    """Persistent status or recovery text that remains readable during loading."""

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("deckNotice")
        self.setStyleSheet("QFrame#deckNotice { background:#1d3040; border:1px solid #315469; border-radius:10px; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:#d3e6f1; font-size:10pt;")
        layout.addWidget(self.label)

    def setText(self, text: str):
        self.label.setText(text)


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
