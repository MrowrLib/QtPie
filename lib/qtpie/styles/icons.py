"""Theme-aware icon resolution for QtPie.

This module provides functions for resolving icon paths based on the current
theme. Given a base icon path like ":/refresh.svg", it will look for theme-specific
variants in the following order:

1. Theme name specific: ":/refresh-{theme_name}.svg" (e.g., ":/refresh-catppuccin.svg")
2. Theme mode fallback: ":/refresh-{mode}.svg" (e.g., ":/refresh-dark.svg")
3. Original fallback: ":/refresh.svg"

Example::

    from qtpie import resolve_theme_icon

    # With theme "catppuccin" (dark mode):
    path = resolve_theme_icon(":/icons/refresh.svg")
    # Returns first existing of:
    #   - ":/icons/refresh-catppuccin.svg"
    #   - ":/icons/refresh-dark.svg"
    #   - ":/icons/refresh.svg"
"""

from collections.abc import Callable
from pathlib import Path
from weakref import WeakKeyDictionary

from qtpy.QtCore import QFile
from qtpy.QtGui import QIcon

from qtpie.styles.color_scheme import is_dark_mode
from qtpie.styles.theme_runtime import get_theme

# Registry: widget → (base_path, setter_fn)
# Uses WeakKeyDictionary so deleted widgets are automatically removed
_theme_icon_registry: WeakKeyDictionary[object, tuple[str, Callable[[QIcon], None]]] = WeakKeyDictionary()


def register_theme_icon(
    widget: object,
    base_path: str,
    setter: Callable[[QIcon], None],
) -> None:
    """Register a widget for theme icon updates.

    When set_theme() is called, the icon will be re-resolved and setter called.
    Uses WeakKeyDictionary so deleted widgets are auto-removed.

    Args:
        widget: The widget to register (used as key for WeakKeyDictionary).
        base_path: The base icon path (e.g., ":/icons/refresh.svg").
        setter: Function to call with the resolved QIcon when theme changes.
    """
    _theme_icon_registry[widget] = (base_path, setter)


def unregister_theme_icon(widget: object) -> None:
    """Unregister a widget from theme icon updates.

    Args:
        widget: The widget to unregister.
    """
    _theme_icon_registry.pop(widget, None)


def refresh_all_theme_icons() -> None:
    """Re-resolve and update all registered theme icons.

    Called by set_theme() after theme changes. For each registered widget,
    re-resolves the theme icon path and calls the setter with the new icon.
    """
    from qtpie.utils.layouts import resolve_icon

    for _widget, (base_path, setter) in list(_theme_icon_registry.items()):
        try:
            resolved_path = resolve_theme_icon(base_path)
            icon = resolve_icon(resolved_path)
            if icon is not None:
                setter(icon)
        except Exception:
            pass  # Widget may be in invalid state during shutdown


def resolve_theme_icon(base_path: str) -> str:
    """Resolve theme-aware icon path with fallback chain.

    Given a base icon path, returns the most specific existing variant
    for the current theme and color mode.

    Args:
        base_path: Base icon path (e.g., ":/icons/refresh.svg" or "/path/to/icon.svg")

    Returns:
        The resolved path - first existing variant, or the original path if
        no variants exist.

    Resolution order:
        1. {stem}-{theme_name}{suffix} (e.g., ":/foo-catppuccin.svg")
        2. {stem}-{mode}{suffix} (e.g., ":/foo-dark.svg" or ":/foo-light.svg")
        3. {base_path} (original)

    Example::

        # With theme "catppuccin" in dark mode:
        resolve_theme_icon(":/refresh.svg")
        # Tries: ":/refresh-catppuccin.svg", ":/refresh-dark.svg", ":/refresh.svg"
    """
    stem, suffix = _split_path(base_path)

    theme_name = get_theme()  # e.g., "catppuccin" or None
    mode = "dark" if is_dark_mode() else "light"

    candidates: list[str] = []

    # 1. Theme name specific (only if theme is set)
    if theme_name:
        candidates.append(f"{stem}-{theme_name}{suffix}")

    # 2. Theme mode fallback
    candidates.append(f"{stem}-{mode}{suffix}")

    # 3. Original path
    candidates.append(base_path)

    for path in candidates:
        if _resource_exists(path):
            return path

    # Return original even if it doesn't exist - caller handles missing files
    return base_path


def _resource_exists(path: str) -> bool:
    """Check if a resource exists (QRC or filesystem).

    Args:
        path: Resource path to check.

    Returns:
        True if the resource exists, False otherwise.
    """
    if path.startswith(":/"):
        # Qt Resource path - use QFile.exists()
        return QFile(path).exists()
    # Filesystem path
    return Path(path).exists()


def _split_path(path: str) -> tuple[str, str]:
    """Split path into stem and suffix.

    Handles both QRC paths (":/foo.svg") and filesystem paths ("/path/to/foo.svg").
    The suffix includes the dot (e.g., ".svg").

    Args:
        path: Path to split.

    Returns:
        Tuple of (stem, suffix). If no extension, suffix is empty string.

    Examples::

        _split_path(":/icons/foo.svg")  # (":/icons/foo", ".svg")
        _split_path("/path/to/foo.bar.svg")  # ("/path/to/foo.bar", ".svg")
        _split_path(":/icons/foo")  # (":/icons/foo", "")
    """
    # Find the last path segment to check for extension
    last_slash = path.rfind("/")
    filename = path[last_slash + 1 :] if last_slash >= 0 else path

    # Check if filename has an extension
    if "." in filename:
        # Find the last dot in the full path (for the extension)
        idx = path.rfind(".")
        return path[:idx], path[idx:]

    # No extension
    return path, ""
