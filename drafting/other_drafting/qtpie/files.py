from pathlib import Path

from PySide6.QtCore import QFile, QTextStream


def read_file(path: Path | str) -> str:
    file = QFile(path)
    if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(file)
        return stream.readAll()
    raise FileNotFoundError(f"Could not open file {path}")


def write_file(path: Path | str, contents: str) -> None:
    file = QFile(path)
    if file.open(QFile.OpenModeFlag.WriteOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(file)
        stream << contents  # type: ignore
        file.close()
    else:
        raise FileNotFoundError(f"Could not open file {path}")
