"""Global runtime API for theme management.

This module provides global functions for getting and setting themes
without requiring direct access to ThemeSet or ThemeWatcher objects.

Example::

    from qtpie import get_theme, get_themes, set_theme, is_dark_theme

    # Get available themes
    print(get_themes())  # ["dark", "light", "monokai"]

    # Get current theme
    print(get_theme())  # "dark"

    # Switch theme
    set_theme("light")

    # Check if dark mode
    if is_dark_theme():
        print("Using dark theme")
"""

from pathlib import Path
from typing import Any

from qtpy.QtWidgets import QApplication

from qtpie.styles.color_scheme import ColorScheme, set_color_scheme
from qtpie.styles.themes import Theme, ThemeMode, ThemeSet

# Module-level state (using Any to avoid circular import issues)
_theme_set: ThemeSet | None = None
_theme_watcher: Any = None  # ThemeWatcher | None - lazy import
_app: Any = None  # QApplication | None - lazy import


def init_themes(
    themes_dir: str | Path,
    app: QApplication,
    initial_theme: str | None = None,
    watch: bool = False,
    output_dir: str | Path | None = None,
) -> ThemeSet:
    """
    Initialize the theme system.

    This is typically called automatically by ``@entrypoint`` when
    ``themes=`` is specified. You can also call it manually for
    programmatic setup.

    Args:
        themes_dir: Path to the themes directory (filesystem or QRC).
        app: The QApplication instance.
        initial_theme: Name of the theme to activate initially.
        watch: Whether to watch theme files for changes.
        output_dir: Directory for compiled SCSS output (None = temp dir).

    Returns:
        The initialized ThemeSet.
    """
    global _theme_set, _theme_watcher, _app

    _app = app
    _theme_set = ThemeSet(themes_dir)

    if initial_theme:
        _theme_set.set_theme(initial_theme)
        _apply_current_theme()

    if watch and not _theme_set.is_qrc:
        # Import here to avoid circular imports
        from qtpie.styles.theme_watcher import ThemeWatcher

        _theme_watcher = ThemeWatcher(app, _theme_set, output_dir)
        if _theme_set.current_theme:
            _theme_watcher.activate_theme(_theme_set.current_theme.name)

    return _theme_set


def _apply_current_theme() -> None:
    """Apply the current theme's stylesheet and color scheme."""
    if _theme_set is None or _app is None:
        return

    theme = _theme_set.current_theme
    if theme is None:
        return

    # Apply color scheme
    color_scheme = ColorScheme.Dark if theme.mode == ThemeMode.Dark else ColorScheme.Light
    set_color_scheme(color_scheme, _app)

    # If we have a watcher, it handles stylesheet application
    if _theme_watcher is not None:
        return

    # No watcher - apply stylesheet directly
    _apply_theme_stylesheet(theme)


def _apply_theme_stylesheet(theme: Theme) -> None:
    """Apply a theme's stylesheet directly (no watcher)."""
    if _app is None:
        return

    if theme.is_scss:
        # Compile SCSS to temp and apply
        import tempfile

        from qtpie.styles.compiler import compile_scss

        if theme.entry_point is None:
            return

        with tempfile.NamedTemporaryFile(suffix=".qss", delete=False) as tmp:
            tmp_path = tmp.name

        entry_point = str(theme.entry_point)
        theme_path = theme.path if isinstance(theme.path, Path) else Path(theme.path)

        # Search paths include theme folder and themes root directory
        search_paths: list[str] = []
        if theme_path.is_dir():
            search_paths.append(str(theme_path))
        if _theme_set is not None:
            themes_dir = _theme_set.themes_dir
            if isinstance(themes_dir, Path):
                search_paths.append(str(themes_dir))
            elif not str(themes_dir).startswith(":/"):
                search_paths.append(str(themes_dir))

        try:
            compile_scss(entry_point, tmp_path, search_paths or None)
            qss = Path(tmp_path).read_text()
            _app.setStyleSheet(qss)
        except Exception:
            pass  # Silently fail for now
    else:
        # QSS file - read and apply
        path = theme.path if isinstance(theme.path, Path) else Path(theme.path)

        if theme.path and str(theme.path).startswith(":/"):
            # QRC path
            from qtpie.styles.loader import load_stylesheet

            qss = load_stylesheet(qrc_path=str(theme.path))
        elif path.exists():
            qss = path.read_text()
        else:
            qss = ""

        _app.setStyleSheet(qss)


def set_theme(name: str) -> bool:
    """
    Switch to the specified theme.

    Applies the theme's stylesheet and sets the color scheme (dark/light mode).

    Args:
        name: Theme name (filename without extension for QSS, folder name for SCSS).

    Returns:
        True if theme was applied, False if theme not found.

    Example::

        set_theme("dark")
        set_theme("solarized-light")
    """
    if _theme_set is None:
        return False

    if not _theme_set.set_theme(name):
        return False

    if _theme_watcher is not None:
        _theme_watcher.activate_theme(name)
    else:
        _apply_current_theme()

    # Refresh all theme icons to reflect the new theme
    from qtpie.styles.icons import refresh_all_theme_icons

    refresh_all_theme_icons()

    return True


def get_theme() -> str | None:
    """
    Get the current theme name.

    Returns:
        Current theme name, or None if no theme system initialized.

    Example::

        current = get_theme()  # "dark"
    """
    if _theme_set is None:
        return None
    return _theme_set.current_theme_name


def get_themes() -> list[str]:
    """
    Get list of available theme names.

    Returns:
        Sorted list of theme names.

    Example::

        themes = get_themes()  # ["dark", "light", "monokai"]
    """
    if _theme_set is None:
        return []
    return _theme_set.theme_names


def is_dark_theme() -> bool:
    """
    Check if the current theme is a dark theme.

    Returns:
        True if current theme is dark mode, False otherwise.
        Returns False if no theme is set.

    Example::

        if is_dark_theme():
            icon = dark_icon
        else:
            icon = light_icon
    """
    if _theme_set is None or _theme_set.current_theme is None:
        return False
    return _theme_set.current_theme.mode == ThemeMode.Dark


def cleanup_themes() -> None:
    """
    Clean up the theme system.

    Stops watchers and clears global state. Called automatically
    when the application exits.
    """
    global _theme_set, _theme_watcher, _app

    if _theme_watcher is not None:
        _theme_watcher.stop()
        _theme_watcher = None

    _theme_set = None
    _app = None
