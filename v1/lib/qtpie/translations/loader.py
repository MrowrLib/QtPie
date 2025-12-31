"""Translation file loading utilities with QRC support."""

import logging
from pathlib import Path

from qtpy.QtCore import QFile, QIODevice, QTextStream

logger = logging.getLogger(__name__)


def is_qrc_path(path: str) -> bool:
    """Check if a path is a Qt Resource Collection (QRC) path."""
    return path.startswith(":/")


def read_file_content(path: str | Path) -> str | None:
    """
    Read file content from filesystem or QRC resource.

    Args:
        path: Filesystem path (str or Path) or QRC path (e.g., ":/translations/app.yml").

    Returns:
        File content as string, or None if file not found.
    """
    path_str = str(path)

    if is_qrc_path(path_str):
        # Read from QRC resource
        qrc_file = QFile(path_str)
        if qrc_file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
            stream = QTextStream(qrc_file)
            content = stream.readAll()
            qrc_file.close()
            return content
        return None

    # Read from filesystem
    fs_path = Path(path_str) if isinstance(path, str) else path
    if fs_path.exists():
        return fs_path.read_text(encoding="utf-8")

    return None


def can_watch_path(path: str) -> bool:
    """
    Check if a path can be watched for changes.

    QRC paths cannot be watched (they're embedded resources).
    Filesystem paths can be watched.
    """
    return not is_qrc_path(path)
