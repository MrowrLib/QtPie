"""Theme discovery and management for QtPie applications."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from qtpy.QtCore import QDir


class ThemeMode(Enum):
    """Theme mode options."""

    Dark = "dark"
    Light = "light"


@dataclass(frozen=True)
class Theme:
    """Represents a single theme."""

    name: str
    """Theme identifier (filename without extension for QSS, folder name for SCSS)."""

    mode: ThemeMode
    """Dark or Light mode."""

    path: Path | str
    """Path to QSS file or SCSS folder. String for QRC paths."""

    is_scss: bool
    """True if SCSS folder, False if QSS file."""

    entry_point: Path | str | None = None
    """For SCSS themes: the main .scss file (first without _ prefix)."""


def detect_mode(name: str) -> ThemeMode:
    """
    Detect theme mode from theme name using naming conventions.

    Rules:
    - "dark" or "light" exact match
    - "*-dark" or "*-light" suffix (e.g., "solarized-dark")
    - "dark-*" or "light-*" prefix (e.g., "dark-contrast")
    - Otherwise defaults to Dark

    Args:
        name: The theme name to analyze.

    Returns:
        ThemeMode.Dark or ThemeMode.Light based on naming convention.
    """
    name_lower = name.lower()

    # Exact match
    if name_lower == "dark":
        return ThemeMode.Dark
    if name_lower == "light":
        return ThemeMode.Light

    # Suffix match: *-dark, *-light
    if name_lower.endswith("-dark"):
        return ThemeMode.Dark
    if name_lower.endswith("-light"):
        return ThemeMode.Light

    # Prefix match: dark-*, light-*
    if name_lower.startswith("dark-"):
        return ThemeMode.Dark
    if name_lower.startswith("light-"):
        return ThemeMode.Light

    # Default to dark
    return ThemeMode.Dark


def find_scss_entry_point(folder: Path) -> Path | None:
    """
    Find the main SCSS file in a theme folder.

    The entry point is the first .scss file that doesn't start with underscore.
    Files starting with underscore are conventionally SCSS partials.

    Args:
        folder: Path to the SCSS theme folder.

    Returns:
        Path to the entry point .scss file, or None if not found.
    """
    scss_files = sorted(folder.glob("*.scss"))

    for f in scss_files:
        if not f.name.startswith("_"):
            return f

    return None


def _is_qrc_path(path: str | Path) -> bool:
    """Check if a path is a QRC resource path."""
    if isinstance(path, Path):
        return False
    return path.startswith(":/")


def _discover_themes_filesystem(themes_dir: Path) -> dict[str, Theme]:
    """
    Discover themes from a filesystem directory.

    Args:
        themes_dir: Path to the themes directory.

    Returns:
        Dictionary mapping theme names to Theme objects.
    """
    themes: dict[str, Theme] = {}

    if not themes_dir.exists():
        return themes

    # Find QSS files
    for qss_file in themes_dir.glob("*.qss"):
        name = qss_file.stem
        themes[name] = Theme(
            name=name,
            mode=detect_mode(name),
            path=qss_file,
            is_scss=False,
            entry_point=None,
        )

    # Find SCSS folders
    for item in themes_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            entry_point = find_scss_entry_point(item)
            if entry_point is not None:
                name = item.name
                themes[name] = Theme(
                    name=name,
                    mode=detect_mode(name),
                    path=item,
                    is_scss=True,
                    entry_point=entry_point,
                )

    return themes


def _discover_themes_qrc(themes_dir: str) -> dict[str, Theme]:
    """
    Discover themes from a QRC resource directory.

    Only QSS files are supported in QRC (SCSS cannot be compiled from resources).

    Args:
        themes_dir: QRC path to the themes directory (e.g., ":/themes").

    Returns:
        Dictionary mapping theme names to Theme objects.
    """
    themes: dict[str, Theme] = {}

    qdir = QDir(themes_dir)
    if not qdir.exists():
        return themes

    # Find QSS files
    qdir.setNameFilters(["*.qss"])
    for entry in qdir.entryList():
        name = entry.removesuffix(".qss")
        qss_path = f"{themes_dir}/{entry}"
        themes[name] = Theme(
            name=name,
            mode=detect_mode(name),
            path=qss_path,
            is_scss=False,
            entry_point=None,
        )

    # Check for subdirectories (QSS only, SCSS ignored in QRC)
    qdir.setNameFilters([])
    qdir.setFilter(QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot)
    for subdir in qdir.entryList():
        subdir_path = f"{themes_dir}/{subdir}"
        sub_qdir = QDir(subdir_path)
        sub_qdir.setNameFilters(["*.qss"])
        qss_files = sub_qdir.entryList()
        if qss_files:
            # Use first QSS file in subdirectory
            qss_path = f"{subdir_path}/{qss_files[0]}"
            themes[subdir] = Theme(
                name=subdir,
                mode=detect_mode(subdir),
                path=qss_path,
                is_scss=False,
                entry_point=None,
            )

    return themes


class ThemeSet:
    """
    Discovers and manages themes from a folder (filesystem or QRC).

    Themes can be:
    - QSS files: ``themes/dark.qss`` becomes theme "dark"
    - SCSS folders: ``themes/dark/main.scss`` becomes theme "dark"

    For QRC paths (starting with ``:/``), only QSS files are supported.
    """

    def __init__(self, themes_dir: str | Path) -> None:
        """
        Initialize ThemeSet by discovering themes in the given directory.

        Args:
            themes_dir: Path to themes directory. Can be filesystem path or QRC path.
        """
        self._themes_dir = themes_dir
        self._is_qrc = _is_qrc_path(themes_dir)
        self._themes: dict[str, Theme] = {}
        self._current_theme: Theme | None = None

        self.refresh()

    @property
    def themes_dir(self) -> str | Path:
        """The themes directory path."""
        return self._themes_dir

    @property
    def is_qrc(self) -> bool:
        """True if themes are loaded from QRC resources."""
        return self._is_qrc

    @property
    def themes(self) -> dict[str, Theme]:
        """Dictionary of discovered themes."""
        return self._themes

    @property
    def theme_names(self) -> list[str]:
        """Sorted list of theme names."""
        return sorted(self._themes.keys())

    @property
    def current_theme(self) -> Theme | None:
        """The currently active theme, or None if no theme is set."""
        return self._current_theme

    @property
    def current_theme_name(self) -> str | None:
        """Name of the currently active theme, or None if no theme is set."""
        return self._current_theme.name if self._current_theme else None

    def get_theme(self, name: str) -> Theme | None:
        """
        Get a theme by name.

        Args:
            name: The theme name.

        Returns:
            The Theme object, or None if not found.
        """
        return self._themes.get(name)

    def set_theme(self, name: str) -> bool:
        """
        Set the current theme by name.

        Args:
            name: The theme name to activate.

        Returns:
            True if the theme was found and set, False otherwise.
        """
        theme = self._themes.get(name)
        if theme is None:
            return False
        self._current_theme = theme
        return True

    def refresh(self) -> None:
        """Re-scan the themes directory and update the themes dictionary."""
        if self._is_qrc:
            self._themes = _discover_themes_qrc(str(self._themes_dir))
        else:
            path = Path(self._themes_dir) if isinstance(self._themes_dir, str) else self._themes_dir
            self._themes = _discover_themes_filesystem(path)

        # Clear current theme if it no longer exists
        if self._current_theme and self._current_theme.name not in self._themes:
            self._current_theme = None
