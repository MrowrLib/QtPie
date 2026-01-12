"""Dock - Type-safe wrapper for QDockWidget content."""

from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDockWidget, QMainWindow, QTabBar, QWidget


class Dock[W: QWidget]:
    """Wrapper for a docked widget with type-safe access.

    Provides access to both the content widget and the QDockWidget wrapper,
    plus convenience methods for common dock operations.

    Example:
        @window
        class IDE(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")

            def toggle_explorer(self) -> None:
                self._explorer.toggle()

            def focus_console(self) -> None:
                self._console.focus()
    """

    def __init__(self, widget: W, dock_widget: QDockWidget) -> None:
        """Initialize the Dock wrapper.

        Args:
            widget: The content widget (e.g., ExplorerPanel).
            dock_widget: The QDockWidget wrapper.
        """
        self._widget = widget
        self._dock_widget = dock_widget

    @property
    def widget(self) -> W:
        """The content widget (ExplorerPanel, etc.)."""
        return self._widget

    @property
    def dock_widget(self) -> QDockWidget:
        """The QDockWidget wrapper."""
        return self._dock_widget

    # -------------------------------------------------------------------------
    # Visibility methods
    # -------------------------------------------------------------------------

    def show(self) -> None:
        """Show the dock widget."""
        self._dock_widget.show()

    def hide(self) -> None:
        """Hide the dock widget."""
        self._dock_widget.hide()

    def toggle(self) -> None:
        """Toggle the dock widget's visibility."""
        self._dock_widget.setVisible(not self._dock_widget.isVisible())

    def close(self) -> None:
        """Close the dock widget (same as hide)."""
        self._dock_widget.close()

    # -------------------------------------------------------------------------
    # Floating methods
    # -------------------------------------------------------------------------

    def float(self) -> None:
        """Make the dock float (detach from main window)."""
        self._dock_widget.setFloating(True)

    def unfloat(self) -> None:
        """Dock the widget back into the main window."""
        self._dock_widget.setFloating(False)

    # -------------------------------------------------------------------------
    # Tab methods (for tabified docks)
    # -------------------------------------------------------------------------

    def raise_tab(self) -> None:
        """Bring this dock to the front if tabified with others."""
        self._dock_widget.raise_()
        # Also try to activate the tab in the tab bar
        main_window = self._get_main_window()
        if main_window is not None:
            # Find the tab bar containing this dock
            for tab_bar in main_window.findChildren(QTabBar):
                for i in range(tab_bar.count()):
                    # Tab text matches dock title
                    if tab_bar.tabText(i) == self._dock_widget.windowTitle():
                        tab_bar.setCurrentIndex(i)
                        return

    def focus(self) -> None:
        """Show, raise to front, and focus the dock's content widget."""
        self.show()
        self.raise_tab()
        self._widget.setFocus()

    # -------------------------------------------------------------------------
    # State properties
    # -------------------------------------------------------------------------

    @property
    def is_visible(self) -> bool:
        """Whether the dock is currently visible."""
        return self._dock_widget.isVisible()

    @property
    def is_floating(self) -> bool:
        """Whether the dock is floating (detached from main window)."""
        return self._dock_widget.isFloating()

    @property
    def is_tabified(self) -> bool:
        """Whether this dock is tabified with other docks."""
        main_window = self._get_main_window()
        if main_window is None:
            return False
        tabified = main_window.tabifiedDockWidgets(self._dock_widget)
        return len(tabified) > 0

    @property
    def area(self) -> Qt.DockWidgetArea:
        """The dock area where this dock is currently located."""
        main_window = self._get_main_window()
        if main_window is None:
            return Qt.DockWidgetArea.NoDockWidgetArea
        return main_window.dockWidgetArea(self._dock_widget)

    @property
    def tab_index(self) -> int:
        """The index of this dock in its tab group, or -1 if not tabified."""
        main_window = self._get_main_window()
        if main_window is None:
            return -1

        # Find the tab bar containing this dock
        for tab_bar in main_window.findChildren(QTabBar):
            for i in range(tab_bar.count()):
                if tab_bar.tabText(i) == self._dock_widget.windowTitle():
                    return i
        return -1

    @property
    def tab_siblings(self) -> list[Dock[QWidget]]:
        """Other docks tabified with this one (empty if not tabified)."""
        main_window = self._get_main_window()
        if main_window is None:
            return []

        tabified = main_window.tabifiedDockWidgets(self._dock_widget)
        result: list[Dock[QWidget]] = []

        # Find Dock wrappers for each tabified QDockWidget
        # They should be stored on the Window instance
        window_instance = main_window
        for dock_widget in tabified:
            # Search window attributes for Dock instances
            for attr_name in dir(window_instance):
                if attr_name.startswith("_"):
                    attr = getattr(window_instance, attr_name, None)
                    if isinstance(attr, Dock) and attr._dock_widget is dock_widget:
                        result.append(attr)  # pyright: ignore[reportUnknownArgumentType]
                        break

        return result

    # -------------------------------------------------------------------------
    # Dock feature properties (read-only, set during creation)
    # -------------------------------------------------------------------------

    @property
    def is_closable(self) -> bool:
        """Whether the dock can be closed."""
        features = self._dock_widget.features()
        return bool(features & QDockWidget.DockWidgetFeature.DockWidgetClosable)

    @property
    def is_movable(self) -> bool:
        """Whether the dock can be moved to other areas."""
        features = self._dock_widget.features()
        return bool(features & QDockWidget.DockWidgetFeature.DockWidgetMovable)

    @property
    def is_floatable(self) -> bool:
        """Whether the dock can be floated."""
        features = self._dock_widget.features()
        return bool(features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)

    @property
    def allowed_areas(self) -> Qt.DockWidgetArea:
        """The dock areas where this dock can be placed."""
        return self._dock_widget.allowedAreas()  # pyright: ignore[reportReturnType]

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    def _get_main_window(self) -> QMainWindow | None:
        """Get the parent QMainWindow."""
        parent = self._dock_widget.parent()
        if isinstance(parent, QMainWindow):
            return parent
        return None


# Type alias for dock area strings
DockArea = str  # "left", "right", "top", "bottom"

# Map string area names to Qt dock areas
DOCK_AREA_MAP: dict[str, Qt.DockWidgetArea] = {
    "left": Qt.DockWidgetArea.LeftDockWidgetArea,
    "right": Qt.DockWidgetArea.RightDockWidgetArea,
    "top": Qt.DockWidgetArea.TopDockWidgetArea,
    "bottom": Qt.DockWidgetArea.BottomDockWidgetArea,
}

# Reverse map for string names
DOCK_AREA_NAMES: dict[Qt.DockWidgetArea, str] = {v: k for k, v in DOCK_AREA_MAP.items()}


def parse_dock_area(area: str) -> Qt.DockWidgetArea:
    """Convert a string area name to Qt.DockWidgetArea.

    Args:
        area: One of "left", "right", "top", "bottom"

    Returns:
        The corresponding Qt.DockWidgetArea

    Raises:
        ValueError: If the area name is not valid
    """
    area_lower = area.lower()
    if area_lower not in DOCK_AREA_MAP:
        valid = ", ".join(DOCK_AREA_MAP.keys())
        raise ValueError(f"Invalid dock area '{area}'. Must be one of: {valid}")
    return DOCK_AREA_MAP[area_lower]


def parse_allowed_areas(areas: list[str]) -> Qt.DockWidgetArea:
    """Convert a list of area names to Qt.DockWidgetArea flags.

    Args:
        areas: List of area names, e.g., ["left", "right"]

    Returns:
        Combined Qt.DockWidgetArea flags
    """
    result = Qt.DockWidgetArea.NoDockWidgetArea
    for area in areas:
        result = result | parse_dock_area(area)  # pyright: ignore[reportArgumentType,reportAssignmentType]
    return result
