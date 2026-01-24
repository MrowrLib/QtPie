"""Zoom/scale management for QtPie stylesheets.

This module provides a global zoom system that:
1. Stores SCSS variables to inject during compilation
2. Triggers stylesheet recompilation when zoom changes
3. Updates QApplication font size for proper widget metrics

Example::

    from qtpie.styles import set_zoom, get_zoom

    # Set zoom to 150%
    set_zoom(1.5)

    # Get current zoom
    print(get_zoom())  # 1.5
"""

from collections.abc import Callable

from qtpy.QtWidgets import QApplication

# Global state for SCSS variable injection
_scss_variables: dict[str, str] = {}
_zoom_scale: float = 1.0
_base_font_size_pt: float = 10.0

# Callback for triggering recompilation (set by theme system)
_recompile_callback: Callable[[], None] | None = None


def get_scss_variables() -> dict[str, str]:
    """
    Get the current SCSS variables to inject during compilation.

    Returns:
        Dictionary of variable names to values (without $ prefix).
    """
    return _scss_variables.copy()


def set_scss_variable(name: str, value: str) -> None:
    """
    Set an SCSS variable to inject during compilation.

    Args:
        name: Variable name (without $ prefix).
        value: Variable value as SCSS expression.
    """
    global _scss_variables
    _scss_variables[name] = value
    _trigger_recompile()


def set_scss_variables(variables: dict[str, str]) -> None:
    """
    Set multiple SCSS variables to inject during compilation.

    Args:
        variables: Dictionary of variable names to values (without $ prefix).
    """
    global _scss_variables
    _scss_variables.update(variables)
    _trigger_recompile()


def clear_scss_variables() -> None:
    """Clear all SCSS variables."""
    global _scss_variables
    _scss_variables = {}
    _trigger_recompile()


def get_zoom() -> float:
    """
    Get the current zoom scale.

    Returns:
        Current zoom scale (1.0 = 100%).
    """
    return _zoom_scale


def get_base_font_size() -> float:
    """
    Get the base font size in points.

    Returns:
        Base font size in points.
    """
    return _base_font_size_pt


def set_base_font_size(size_pt: float) -> None:
    """
    Set the base font size in points.

    This is the font size at zoom level 1.0.

    Args:
        size_pt: Base font size in points.
    """
    global _base_font_size_pt
    _base_font_size_pt = size_pt
    # Re-apply zoom to update font
    set_zoom(_zoom_scale)


def set_zoom(scale: float) -> None:
    """
    Set the zoom scale and trigger stylesheet recompilation.

    This:
    1. Updates the $scale SCSS variable
    2. Updates QApplication font size for widget metrics
    3. Triggers stylesheet recompilation

    Args:
        scale: Zoom scale (1.0 = 100%, 1.5 = 150%, etc.)

    Example::

        set_zoom(1.5)  # 150% zoom
        set_zoom(0.8)  # 80% zoom
    """
    global _zoom_scale, _scss_variables
    _zoom_scale = scale

    # Update $scale variable for SCSS
    _scss_variables["scale"] = str(scale)

    # Update application font for proper widget metrics
    app = QApplication.instance()
    if app is not None and isinstance(app, QApplication):
        scaled_size = _base_font_size_pt * scale
        font = app.font()
        font.setPointSizeF(scaled_size)
        app.setFont(font)

    # Trigger stylesheet recompilation
    _trigger_recompile()


def register_recompile_callback(callback: Callable[[], None] | None) -> None:
    """
    Register a callback to trigger recompilation when variables change.

    This is called by the theme system to register its recompile function.

    Args:
        callback: Callable to trigger recompilation, or None to unregister.
    """
    global _recompile_callback
    _recompile_callback = callback


def _trigger_recompile() -> None:
    """Trigger stylesheet recompilation if callback is set."""
    if _recompile_callback is not None:
        _recompile_callback()
