"""Stylesheet loading utilities."""

from pathlib import Path

from qtpy.QtCore import QFile, QIODevice, QTextStream


def load_stylesheet(
    qss_path: str | None = None,
    qrc_path: str | None = None,
) -> str:
    """
    Load QSS stylesheet from local file or QRC resource.

    Tries local file first (if provided and exists), then falls back to QRC.
    Returns empty string if neither source provides content.

    Args:
        qss_path: Path to local QSS file (e.g., "build/app.qss").
        qrc_path: Path to QRC resource (e.g., ":/styles/app.qss").

    Returns:
        The stylesheet content, or empty string if not found.
    """
    # Try local file first
    if qss_path:
        local_file = Path(qss_path)
        if local_file.exists():
            return local_file.read_text()

    # Fall back to QRC resource
    if qrc_path:
        qrc_file = QFile(qrc_path)
        if qrc_file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
            stream = QTextStream(qrc_file)
            content = stream.readAll()
            qrc_file.close()
            return content

    return ""
