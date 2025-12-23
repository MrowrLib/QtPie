"""The @stylesheet decorator for declarative stylesheet loading."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from qtpy.QtCore import QFile, QIODevice, QTextStream
from qtpy.QtWidgets import QApplication, QWidget

from qtpie.styles.watcher import QssWatcher, ScssWatcher

# Attribute name for storing stylesheet config
STYLESHEET_CONFIG_ATTR = "_qtpie_stylesheet_config"
STYLESHEET_WATCHER_ATTR = "_qtpie_stylesheet_watcher"


def _load_qrc_stylesheet(qrc_path: str) -> str:
    """Load stylesheet content from a QRC resource path."""
    qrc_file = QFile(qrc_path)
    if qrc_file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
        stream = QTextStream(qrc_file)
        content = stream.readAll()
        qrc_file.close()
        return content
    return ""


def _compile_scss_to_string(scss_path: str, search_paths: list[str]) -> str:
    """Compile SCSS file to a QSS string."""
    from scss import Compiler  # type: ignore[import-untyped]

    scss_file = Path(scss_path)
    if not scss_file.exists():
        return ""

    compiler = Compiler(search_path=search_paths)
    return cast(str, compiler.compile(str(scss_file)))  # pyright: ignore[reportUnknownMemberType]


def _apply_stylesheet_to_target(
    target: QWidget | QApplication,
    path: str,
    watch: bool,
    scss_search_paths: list[str] | None,
) -> QssWatcher | ScssWatcher | None:
    """
    Apply stylesheet to the target widget or application.

    Returns a watcher if watch=True, otherwise None.
    """
    is_qrc = path.startswith(":/")
    is_scss = path.endswith(".scss")

    # Determine search paths for SCSS
    if scss_search_paths:
        search_paths = list(scss_search_paths)
    elif is_scss:
        search_paths = [str(Path(path).parent)]
    else:
        search_paths = []

    if watch and not is_qrc:
        # Set up a watcher - it will handle initial load too
        if is_scss:
            temp_dir = Path(tempfile.gettempdir()) / "qtpie_scss"
            temp_dir.mkdir(exist_ok=True)
            qss_path = str(temp_dir / f"{Path(path).stem}.qss")
            return ScssWatcher(target, path, qss_path, search_paths or None)
        else:
            return QssWatcher(target, path)

    # One-shot load (no watching)
    if is_qrc:
        content = _load_qrc_stylesheet(path)
    elif is_scss:
        content = _compile_scss_to_string(path, search_paths)
    else:
        qss_file = Path(path)
        content = qss_file.read_text() if qss_file.exists() else ""

    if content:
        target.setStyleSheet(content)

    return None


def stylesheet[T: type](
    path: str,
    *,
    watch: bool = False,
    scss_search_paths: list[str] | None = None,
) -> Callable[[T], T]:
    """
    Decorator that applies a stylesheet to a widget or application class.

    The stylesheet is applied after the class is instantiated. For widgets,
    the stylesheet is applied to the widget. For applications, it's applied
    to the application.

    Args:
        path: Path to stylesheet. Can be:
            - QRC path (e.g., ":/styles/app.qss") - loads from Qt resources
            - QSS file (e.g., "styles.qss") - loads from filesystem
            - SCSS file (e.g., "styles.scss") - compiles and applies
        watch: If True, hot-reload stylesheet on file changes.
            Not applicable to QRC paths.
        scss_search_paths: Directories for SCSS @import resolution.
            If not provided, the SCSS file's parent folder is used.

    Examples:
        # Simple QSS file
        @stylesheet("styles.qss")
        @widget
        class MyWidget(QWidget):
            ...

        # SCSS with hot-reload
        @stylesheet("styles.scss", watch=True)
        @widget
        class MyWidget(QWidget):
            ...

        # SCSS with custom search paths
        @stylesheet("main.scss", scss_search_paths=["partials/"], watch=True)
        @widget
        class MyWidget(QWidget):
            ...

        # On an App subclass
        @stylesheet("app.scss", watch=True)
        class MyApp(App):
            ...
    """

    def decorator(cls: T) -> T:
        # Store config on class
        setattr(
            cls,
            STYLESHEET_CONFIG_ATTR,
            {
                "path": path,
                "watch": watch,
                "scss_search_paths": scss_search_paths,
            },
        )

        # Get the original __init__
        original_init = cls.__init__  # type: ignore[misc]

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            # Call original init
            original_init(self, *args, **kwargs)

            # Apply stylesheet after init
            watcher = _apply_stylesheet_to_target(
                self,
                path,
                watch,
                scss_search_paths,
            )

            # Store watcher on instance to keep it alive
            if watcher is not None:
                setattr(self, STYLESHEET_WATCHER_ATTR, watcher)

        cls.__init__ = new_init  # type: ignore[method-assign,misc]

        return cls

    return decorator  # type: ignore[return-value]
