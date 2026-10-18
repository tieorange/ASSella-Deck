"""Shared Deck presentation tokens and scoped control styles."""

BG = "#101823"
SURFACE = "#1c2836"
SURFACE_RAISED = "#243545"
ACCENT = "#43d6c1"
TEXT = "#f4f7fb"
MUTED = "#b8cad5"
WARNING = "#f6c978"
ERROR = "#ffab9d"
SPACE = 12
TOUCH = 48


def field_style() -> str:
    return f"""
        QLineEdit, QComboBox {{
            background: {SURFACE}; color: {TEXT};
            border: 1px solid #506374; border-radius: 10px;
            padding: 8px 14px; font-size: 11pt;
            selection-background-color: {ACCENT}; selection-color: #061b1b;
        }}
        QLineEdit:focus, QComboBox:focus {{ border: 3px solid {ACCENT}; }}
        QComboBox::drop-down {{ border: none; width: 32px; }}
        QComboBox QAbstractItemView {{ background: {SURFACE}; color: {TEXT};
            selection-background-color: #275c61; }}
    """


def button_style(*, primary: bool = False) -> str:
    background = ACCENT if primary else SURFACE_RAISED
    foreground = "#061b1b" if primary else TEXT
    pressed = "#2bac9d" if primary else "#385369"
    return f"""
        QPushButton {{ background: {background}; color: {foreground};
            border: 1px solid #536473; border-radius: 10px;
            padding: 0 18px; font-size: 11pt; font-weight: 700; }}
        QPushButton:hover {{ background: #6ce6d3; color: #061b1b; }}
        QPushButton:pressed {{ background: {pressed}; color: {foreground}; }}
        QPushButton:focus {{ border: 3px solid {TEXT}; }}
        QPushButton:disabled {{ background: #27313c; color: #81919e; border-color: #3c4954; }}
    """
