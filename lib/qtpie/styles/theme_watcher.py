"""Theme file watcher for hot-reloading themes."""

import tempfile
from pathlib import Path

from qtpy.QtCore import QObject, Signal
from qtpy.QtWidgets import QApplication, QWidget

from qtpie.styles.color_scheme import ColorScheme, set_color_scheme
from qtpie.styles.themes import Theme, ThemeMode, ThemeSet
from qtpie.styles.watcher import QssWatcher, ScssWatcher


class ThemeWatcher(QObject):
    """
    Watches theme files and hot-reloads on changes.

    Wraps QssWatcher/ScssWatcher and manages switching between themes.
    Only the active theme is watched at any time.
    """

    themeApplied = Signal(str)
    """Emitted when a theme is applied, with theme name."""

    def __init__(
        self,
        target: QApplication | QWidget,
        theme_set: ThemeSet,
        output_dir: str | Path | None = None,
        parent: QObject | None = None,
    ) -> None:
        """
        Initialize ThemeWatcher.

        Args:
            target: QApplication or QWidget to apply stylesheets to.
            theme_set: ThemeSet containing discovered themes.
            output_dir: Directory for compiled SCSS output. None uses temp dir.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._target = target
        self._theme_set = theme_set
        self._output_dir = Path(output_dir) if output_dir else None
        self._current_watcher: QssWatcher | ScssWatcher | None = None
        self._current_theme_name: str | None = None
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None

        # Create temp dir if no output_dir specified
        if self._output_dir is None:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="qtpie_themes_")

    def _get_qss_output_path(self, theme: Theme) -> Path:
        """Get the QSS output path for a theme."""
        if self._output_dir is not None:
            return self._output_dir / f"{theme.name}.qss"
        elif self._temp_dir is not None:
            return Path(self._temp_dir.name) / f"{theme.name}.qss"
        else:
            # Fallback to system temp
            return Path(tempfile.gettempdir()) / f"qtpie_{theme.name}.qss"

    def activate_theme(self, name: str) -> bool:
        """
        Activate a theme and start watching its files.

        Stops watching the previous theme (if any) and starts
        watching the new theme's files.

        Args:
            name: Theme name to activate.

        Returns:
            True if theme was activated, False if theme not found.
        """
        theme = self._theme_set.get_theme(name)
        if theme is None:
            return False

        # Stop current watcher if any
        if self._current_watcher is not None:
            self._current_watcher.stop()
            self._current_watcher = None

        self._current_theme_name = name

        # Apply color scheme
        color_scheme = ColorScheme.Dark if theme.mode == ThemeMode.Dark else ColorScheme.Light
        set_color_scheme(color_scheme, self._target if isinstance(self._target, QApplication) else None)

        # Create appropriate watcher
        if theme.is_scss:
            self._current_watcher = self._create_scss_watcher(theme)
        else:
            self._current_watcher = self._create_qss_watcher(theme)

        if self._current_watcher is not None:
            self._current_watcher.stylesheetApplied.connect(self._on_stylesheet_applied)

        return True

    def _create_qss_watcher(self, theme: Theme) -> QssWatcher | None:
        """Create a QssWatcher for a QSS theme."""
        path = theme.path
        if isinstance(path, Path):
            path_str = str(path)
        else:
            path_str = path

        # Can't watch QRC paths
        if path_str.startswith(":/"):
            # Apply once and return no watcher
            self._apply_qrc_stylesheet(path_str)
            return None

        return QssWatcher(self._target, path_str, parent=self)

    def _create_scss_watcher(self, theme: Theme) -> ScssWatcher | None:
        """Create a ScssWatcher for an SCSS theme."""
        if theme.entry_point is None:
            return None

        entry_point = theme.entry_point
        if isinstance(entry_point, Path):
            scss_path = str(entry_point)
        else:
            scss_path = entry_point

        # Can't watch QRC paths
        if scss_path.startswith(":/"):
            return None

        qss_path = self._get_qss_output_path(theme)
        theme_path = theme.path if isinstance(theme.path, Path) else Path(theme.path)

        # Search paths include the theme folder, themes root, and _shared folder
        # This allows @import '../_shared/...' to work and watches shared folders
        search_paths: list[str] = []
        if theme_path.is_dir():
            search_paths.append(str(theme_path))
        themes_dir = self._theme_set.themes_dir
        if isinstance(themes_dir, Path):
            search_paths.append(str(themes_dir))
            # Add _shared folder so imports within _shared.scss can find siblings
            shared_dir = themes_dir / "_shared"
            if shared_dir.is_dir():
                search_paths.append(str(shared_dir))
        elif not themes_dir.startswith(":/"):
            search_paths.append(themes_dir)
            # Add _shared folder so imports within _shared.scss can find siblings
            shared_dir = Path(themes_dir) / "_shared"
            if shared_dir.is_dir():
                search_paths.append(str(shared_dir))

        return ScssWatcher(
            self._target,
            scss_path,
            str(qss_path),
            search_paths,
            parent=self,
        )

    def _apply_qrc_stylesheet(self, qrc_path: str) -> None:
        """Apply a QRC stylesheet directly (no watching)."""
        from qtpie.styles.loader import load_stylesheet

        qss = load_stylesheet(qrc_path=qrc_path)
        self._target.setStyleSheet(qss)
        self.themeApplied.emit(self._current_theme_name or "")

    def _on_stylesheet_applied(self) -> None:
        """Handle stylesheet applied signal from inner watcher."""
        if self._current_theme_name:
            self.themeApplied.emit(self._current_theme_name)

    def stop(self) -> None:
        """Stop watching and clean up resources."""
        if self._current_watcher is not None:
            self._current_watcher.stop()
            self._current_watcher = None

        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

        self._current_theme_name = None
