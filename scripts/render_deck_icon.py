"""Export the fork's SVG icon to desktop PNG and multi-size ICO assets."""

import struct
from pathlib import Path

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer


LOGO = Path(__file__).resolve().parents[1] / "src/res/logo"


def png_bytes(renderer: QSvgRenderer, size: int) -> bytes:
    canvas = QImage(size * 4, size * 4, QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    renderer.render(painter)
    painter.end()
    image = canvas.scaled(
        size, size, Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise OSError("Could not render the ASSella Deck icon")
    buffer.close()
    return bytes(data)


def render() -> None:
    renderer = QSvgRenderer(str(LOGO / "icon.svg"))
    if not renderer.isValid():
        raise ValueError("The ASSella Deck SVG icon is invalid")

    sizes = (16, 24, 32, 48, 64, 128, 256)
    images = [png_bytes(renderer, size) for size in sizes]
    (LOGO / "icon.png").write_bytes(images[-1])

    directory = bytearray(struct.pack("<HHH", 0, 1, len(images)))
    payload = bytearray()
    offset = 6 + 16 * len(images)
    for size, data in zip(sizes, images):
        directory.extend(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset))
        payload.extend(data)
        offset += len(data)
    (LOGO / "icon.ico").write_bytes(directory + payload)


if __name__ == "__main__":
    render()
