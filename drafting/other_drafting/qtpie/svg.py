from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from qtpie.files import read_file


def colored_svg(svg_path: str, color: QColor, size: QSize) -> QPixmap:
    svg_data = read_file(svg_path)

    # Replace 'currentColor' with actual hex color like "#ff00ff"
    color_hex = color.name(QColor.NameFormat.HexRgb)
    svg_data = svg_data.replace("currentColor", color_hex)

    renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap
