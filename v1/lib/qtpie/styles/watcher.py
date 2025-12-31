"""File watchers for stylesheet hot-reloading."""

from pathlib import Path

from qtpy.QtCore import QFileSystemWatcher, QObject, QTimer, Signal
from qtpy.QtWidgets import QApplication, QWidget

from qtpie.styles.compiler import compile_scss


class QssWatcher(QObject):
    """
    Watch a QSS file and hot-reload on changes.

    Handles:
    - File that doesn't exist yet (waits for creation)
    - Editor delete+recreate behavior (vim, VSCode, etc.)
    - macOS FSEvents quirks (re-arms watches after changes)
    """

    stylesheetApplied = Signal()

    def __init__(
        self,
        target: QApplication | QWidget,
        qss_path: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._target = target
        self._qss_path = Path(qss_path).resolve()
        self._mtime: float | None = None

        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_dir_changed)
        self._watcher.fileChanged.connect(self._on_file_changed)

        # Debounce timer - 150ms handles editor multi-step saves
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._apply_if_changed)

        # Always watch the parent directory (catches file creation)
        parent_dir = str(self._qss_path.parent)
        self._watcher.addPath(parent_dir)

        # Try to watch the file if it exists
        self._ensure_file_watched()

        # Apply initial stylesheet
        self._apply_if_changed(initial=True)

    def _ensure_file_watched(self) -> None:
        """Ensure file is in watch list (re-arms after delete/rename)."""
        if self._qss_path.exists():
            qss_str = str(self._qss_path)
            if qss_str not in self._watcher.files():
                self._watcher.addPath(qss_str)

    def _on_dir_changed(self, _path: str) -> None:
        """Directory changed - file might have been created."""
        self._ensure_file_watched()
        self._debounce_timer.start()

    def _on_file_changed(self, _path: str) -> None:
        """File changed - might be modified or replaced by editor."""
        # Qt drops watch after delete/rename - always re-arm
        self._ensure_file_watched()
        self._debounce_timer.start()

    def _apply_if_changed(self, initial: bool = False) -> None:
        """Read QSS file and apply to target if actually changed."""
        if not self._qss_path.exists():
            self._mtime = None
            return

        # Check mtime to avoid redundant reloads
        try:
            current_mtime = self._qss_path.stat().st_mtime
        except OSError:
            return

        if not initial and self._mtime is not None and current_mtime <= self._mtime:
            # No actual change
            return

        self._mtime = current_mtime

        try:
            qss = self._qss_path.read_text()
        except OSError:
            return

        self._target.setStyleSheet(qss)
        self.stylesheetApplied.emit()

    def stop(self) -> None:
        """Stop watching."""
        self._debounce_timer.stop()
        self._watcher.directoryChanged.disconnect(self._on_dir_changed)
        self._watcher.fileChanged.disconnect(self._on_file_changed)


class ScssWatcher(QObject):
    """
    Watch SCSS files, compile to QSS, and hot-reload on changes.

    Watches the main SCSS file and all search paths for changes.
    Handles macOS FSEvents quirks by re-arming watches after changes.
    """

    stylesheetApplied = Signal()

    def __init__(
        self,
        target: QApplication | QWidget,
        scss_path: str,
        qss_path: str,
        search_paths: list[str] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._target = target
        self._scss_path = Path(scss_path).resolve()
        self._qss_path = Path(qss_path).resolve()
        self._search_paths = [Path(p).resolve() for p in (search_paths or [])]
        self._mtimes: dict[str, float] = {}

        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_changed)
        self._watcher.fileChanged.connect(self._on_changed)

        # Debounce timer - 150ms handles editor multi-step saves
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._recompile_if_changed)

        # Watch SCSS file's directory
        self._watcher.addPath(str(self._scss_path.parent))
        self._ensure_file_watched(self._scss_path)

        # Watch search path directories and their scss files
        for search_path in self._search_paths:
            if search_path.exists():
                self._watcher.addPath(str(search_path))
                for scss_file in search_path.glob("*.scss"):
                    self._ensure_file_watched(scss_file)

        # Initial compile
        self._recompile_if_changed(initial=True)

    def _ensure_file_watched(self, path: Path) -> None:
        """Ensure file is in watch list (re-arms after delete/rename)."""
        if path.exists():
            path_str = str(path)
            if path_str not in self._watcher.files():
                self._watcher.addPath(path_str)

    def _on_changed(self, path: str) -> None:
        """File or directory changed."""
        changed = Path(path)

        # Re-arm file watch if it was replaced (Qt drops watch after delete/rename)
        if changed.is_file():
            self._ensure_file_watched(changed)

        # If a directory changed, re-watch any scss files in it
        if changed.is_dir():
            for scss_file in changed.glob("*.scss"):
                self._ensure_file_watched(scss_file)

        self._debounce_timer.start()

    def _get_all_scss_mtimes(self) -> dict[str, float]:
        """Get mtimes for all watched scss files."""
        mtimes: dict[str, float] = {}

        # Main file
        if self._scss_path.exists():
            try:
                mtimes[str(self._scss_path)] = self._scss_path.stat().st_mtime
            except OSError:
                pass

        # Search path files
        for search_path in self._search_paths:
            if search_path.exists():
                for scss_file in search_path.glob("*.scss"):
                    try:
                        mtimes[str(scss_file)] = scss_file.stat().st_mtime
                    except OSError:
                        pass

        return mtimes

    def _recompile_if_changed(self, initial: bool = False) -> None:
        """Compile SCSS and apply to target if actually changed."""
        if not self._scss_path.exists():
            return

        # Check if any scss file actually changed
        current_mtimes = self._get_all_scss_mtimes()
        if not initial and current_mtimes == self._mtimes:
            # No actual change
            return

        self._mtimes = current_mtimes

        try:
            compile_scss(
                scss_path=str(self._scss_path),
                qss_path=str(self._qss_path),
                search_paths=[str(p) for p in self._search_paths],
            )

            if self._qss_path.exists():
                qss = self._qss_path.read_text()
                self._target.setStyleSheet(qss)
                self.stylesheetApplied.emit()
        except Exception:
            # Don't crash on SCSS errors - just keep old styles
            pass

    def stop(self) -> None:
        """Stop watching."""
        self._debounce_timer.stop()
        self._watcher.directoryChanged.disconnect(self._on_changed)
        self._watcher.fileChanged.disconnect(self._on_changed)


def watch_qss(
    target: QApplication | QWidget,
    qss_path: str,
) -> QssWatcher:
    """
    Watch a QSS file and hot-reload on changes.

    Args:
        target: QApplication or QWidget to apply stylesheet to.
        qss_path: Path to QSS file (can be non-existent, will watch for creation).

    Returns:
        QssWatcher instance. Keep a reference to prevent garbage collection.
    """
    return QssWatcher(target, qss_path)


def watch_scss(
    target: QApplication | QWidget,
    scss_path: str,
    qss_path: str,
    search_paths: list[str] | None = None,
) -> ScssWatcher:
    """
    Watch SCSS files, compile to QSS, and hot-reload on changes.

    Args:
        target: QApplication or QWidget to apply stylesheet to.
        scss_path: Path to main SCSS file.
        qss_path: Path where compiled QSS will be written.
        search_paths: Directories to search for @import resolution.

    Returns:
        ScssWatcher instance. Keep a reference to prevent garbage collection.
    """
    return ScssWatcher(target, scss_path, qss_path, search_paths)


def watch_styles(
    target: QApplication | QWidget,
    qss_path: str,
    scss_path: str | None = None,
    search_paths: list[str] | None = None,
) -> QssWatcher | ScssWatcher:
    """
    Watch styles and hot-reload on changes.

    If scss_path is provided, compiles SCSS to QSS.
    Otherwise, just watches the QSS file directly.

    Args:
        target: QApplication or QWidget to apply stylesheet to.
        qss_path: Path to QSS file (output if using SCSS, input otherwise).
        scss_path: Optional path to SCSS file. If provided, enables compilation.
        search_paths: Directories for @import resolution (only used with scss_path).

    Returns:
        Watcher instance. Keep a reference to prevent garbage collection.
    """
    if scss_path is not None:
        return watch_scss(target, scss_path, qss_path, search_paths)
    else:
        return watch_qss(target, qss_path)
