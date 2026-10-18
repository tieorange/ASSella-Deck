"""SDL controller to Qt focus bridge for Steam Deck gamepad input."""

from __future__ import annotations

import sys
import logging

from PyQt6.QtCore import QObject, QTimer, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class DeckController(QObject):
    """Translate mapped SDL controller events; keyboard Steam Input still works."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pygame = None
        self._controller_module = None
        self._controllers = {}
        self._stick = (0, 0)
        if sys.platform != "linux":
            return
        try:
            import pygame
            from pygame._sdl2 import controller

            pygame.display.init()
            pygame.joystick.init()
            controller.init()
            self._pygame = pygame
            self._controller_module = controller
            self._open_connected()
        except (ImportError, RuntimeError) as error:
            logger.warning("Deck controller input unavailable: %s", error)
            return
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.poll)
        self._timer.start(50)

    def _open_connected(self):
        for index in range(self._controller_module.get_count()):
            if self._controller_module.is_controller(index) and index not in self._controllers:
                self._controllers[index] = self._controller_module.Controller(index)

    def _send(self, key, modifiers=Qt.KeyboardModifier.NoModifier):
        target = QApplication.focusWidget() or QApplication.activeWindow()
        if target is None:
            return
        QApplication.postEvent(target, QKeyEvent(QKeyEvent.Type.KeyPress, key, modifiers))
        QApplication.postEvent(target, QKeyEvent(QKeyEvent.Type.KeyRelease, key, modifiers))

    def poll(self):
        if self._pygame is None:
            return
        pg = self._pygame
        buttons = {
            pg.CONTROLLER_BUTTON_A: Qt.Key.Key_Return,
            pg.CONTROLLER_BUTTON_B: Qt.Key.Key_Escape,
            pg.CONTROLLER_BUTTON_X: Qt.Key.Key_Menu,
            pg.CONTROLLER_BUTTON_Y: Qt.Key.Key_F,
            pg.CONTROLLER_BUTTON_LEFTSHOULDER: Qt.Key.Key_PageUp,
            pg.CONTROLLER_BUTTON_RIGHTSHOULDER: Qt.Key.Key_PageDown,
            pg.CONTROLLER_BUTTON_DPAD_UP: Qt.Key.Key_Up,
            pg.CONTROLLER_BUTTON_DPAD_DOWN: Qt.Key.Key_Down,
            pg.CONTROLLER_BUTTON_DPAD_LEFT: Qt.Key.Key_Left,
            pg.CONTROLLER_BUTTON_DPAD_RIGHT: Qt.Key.Key_Right,
        }
        for event in pg.event.get():
            if event.type == pg.CONTROLLERDEVICEADDED:
                self._open_connected()
            elif event.type == pg.CONTROLLERDEVICEREMOVED:
                self._controllers.clear()
                self._open_connected()
            elif event.type == pg.CONTROLLERBUTTONDOWN:
                key = buttons.get(event.button)
                if key is not None:
                    mods = Qt.KeyboardModifier.ControlModifier if event.button == pg.CONTROLLER_BUTTON_Y else Qt.KeyboardModifier.NoModifier
                    self._send(key, mods)
            elif event.type == pg.CONTROLLERAXISMOTION and event.axis in (pg.CONTROLLER_AXIS_LEFTX, pg.CONTROLLER_AXIS_LEFTY):
                axis_index = 0 if event.axis == pg.CONTROLLER_AXIS_LEFTX else 1
                value = 1 if event.value > 21000 else -1 if event.value < -21000 else 0
                state = list(self._stick)
                if value and value != state[axis_index]:
                    key = (Qt.Key.Key_Right if value > 0 else Qt.Key.Key_Left) if axis_index == 0 else (Qt.Key.Key_Down if value > 0 else Qt.Key.Key_Up)
                    self._send(key)
                state[axis_index] = value
                self._stick = tuple(state)
