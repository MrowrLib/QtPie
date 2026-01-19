"""Dock tab customization features for QtPie windows.

This module provides window-level dock tab features:
- dockNesting: Enable nested dock splitting
- dockTabsPosition: Tab bar position for tabified docks
- dockTabsClosable: Show close buttons on dock tabs
- dockTabsMovable: Allow reordering tabs by dragging
- dockTabsHideTitleBar: Auto-hide title bar when dock is tabified
- dockTabsDragToUndock: Drag tab outside tab bar to float dock
"""

from collections.abc import Callable
from typing import Any, Protocol, cast, override

from qtpy.QtCore import QEvent, QObject, QPoint, Qt, QTimer
from qtpy.QtGui import QMouseEvent
from qtpy.QtWidgets import QDockWidget, QMainWindow, QTabBar, QTabWidget, QWidget


class DockTabConfig(Protocol):
    """Protocol for dock tab configuration (shared by WindowConfig and AppConfig)."""

    dock_nesting: bool
    dock_tabs_position: str
    dock_tabs_closable: bool
    dock_tabs_movable: bool
    dock_tabs_hide_title_bar: bool
    dock_tabs_drag_to_undock: bool
    dock_tabs_drag_margin: int


# Map user-friendly position names to Qt tab positions
TAB_POSITION_MAP: dict[str, QTabWidget.TabPosition] = {
    "top": QTabWidget.TabPosition.North,
    "bottom": QTabWidget.TabPosition.South,
    "left": QTabWidget.TabPosition.West,
    "right": QTabWidget.TabPosition.East,
}


def setup_dock_tab_options(window: QMainWindow, config: DockTabConfig) -> None:
    """Apply window-level dock tab options (native Qt settings).

    This sets up:
    - Dock nesting (setDockNestingEnabled)
    - Tab position for all dock areas (setTabPosition)

    Args:
        window: The QMainWindow to configure
        config: Configuration with dock_nesting and dock_tabs_position
    """
    # Enable/disable dock nesting
    window.setDockNestingEnabled(config.dock_nesting)

    # Set tab position for all dock areas
    position = TAB_POSITION_MAP.get(config.dock_tabs_position, QTabWidget.TabPosition.North)
    window.setTabPosition(Qt.DockWidgetArea.AllDockWidgetAreas, position)


def install_dock_tab_features(
    window: QMainWindow,
    config: DockTabConfig,
    dock_overrides: dict[QDockWidget, dict[str, Any]] | None = None,
) -> None:
    """Install event filter for dock tab customization.

    This enables advanced tab features:
    - Closable tabs
    - Movable tabs
    - Hide title bar when tabified
    - Drag-to-undock

    Args:
        window: The QMainWindow to configure
        config: Configuration with dock tab options
        dock_overrides: Per-dock overrides, keyed by QDockWidget instance.
                       Supports "hide_title_bar_when_tabbed" override.
    """
    overrides = dock_overrides or {}

    # Check if any dock has hide_title_bar or hide_title_bar_when_tabbed override
    any_dock_wants_hide_titlebar = any(d.get("hide_title_bar_when_tabbed") is True for d in overrides.values())
    any_dock_has_hide_titlebar = any(d.get("hide_title_bar") is True for d in overrides.values())

    # Need to install event filter if:
    # - Any tab feature is enabled (closable, drag-to-undock, hide title bar)
    # - OR if movable is explicitly False (need to override Qt's default of True)
    # - OR if any per-dock override wants to hide title bar
    needs_customization = any(
        [
            config.dock_tabs_closable,
            config.dock_tabs_drag_to_undock,
            config.dock_tabs_hide_title_bar,
            any_dock_wants_hide_titlebar,
            any_dock_has_hide_titlebar,
            not config.dock_tabs_movable,  # Need to disable Qt's default movable=True
        ]
    )

    if not needs_customization:
        return

    event_filter = DockTabEventFilter(window, config, overrides)
    window.installEventFilter(event_filter)

    # If hide title bar is enabled (window-level or any per-dock override), set up hooks
    if config.dock_tabs_hide_title_bar or any_dock_wants_hide_titlebar or any_dock_has_hide_titlebar:
        _setup_title_bar_hooks(window, config, overrides)


class DockTabEventFilter(QObject):
    """Event filter for dock tab bar customization.

    Handles:
    - LayoutRequest: Find new tab bars and customize them
    - Mouse events on tab bars: Drag-to-undock logic
    """

    def __init__(
        self,
        window: QMainWindow,
        config: DockTabConfig,
        dock_overrides: dict[QDockWidget, dict[str, Any]],
    ) -> None:
        super().__init__(window)
        self._window = window
        self._config = config
        self._dock_overrides = dock_overrides
        self._drag_start_pos: QPoint = QPoint()
        self._drag_tab_index: int = -1
        self._drag_tab_text: str | None = None

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Filter events for tab bar customization."""
        if event.type() == QEvent.Type.LayoutRequest:
            # A layout change occurred - check for new tab bars and new docks
            self._customize_tab_bars()
            self._setup_new_dock_hooks()
        elif isinstance(watched, QTabBar) and self._config.dock_tabs_drag_to_undock:
            self._handle_tab_bar_mouse_event(watched, event)
        return super().eventFilter(watched, event)

    def _setup_new_dock_hooks(self) -> None:
        """Set up title bar hooks for any newly added docks and update all title bars."""
        if not self._config.dock_tabs_hide_title_bar:
            return

        for dock in self._window.findChildren(QDockWidget):
            if dock.property("_qtpie_titlebar_hooks"):
                continue

            def make_handler(d: QDockWidget) -> Callable[..., None]:
                def handler(*_args: Any) -> None:
                    _update_title_bar_for_dock(self._window, d, self._config, self._dock_overrides)

                return handler  # noqa: B023 - closure factory pattern, `d` is captured via parameter

            handler = make_handler(dock)
            dock.topLevelChanged.connect(handler)
            dock.dockLocationChanged.connect(handler)
            dock.setProperty("_qtpie_titlebar_hooks", True)

        # Update ALL dock title bars on layout change
        # This ensures existing docks hide their title bars when a new dock joins their tab group
        for dock in self._window.findChildren(QDockWidget):
            _update_title_bar_for_dock(self._window, dock, self._config, self._dock_overrides)

    def _customize_tab_bars(self) -> None:
        """Find and customize all dock tab bars."""
        for tab_bar in self._window.findChildren(QTabBar):
            if tab_bar.property("_qtpie_customized"):
                continue

            # Check if this is a dock tab bar (child of QMainWindow, not in a QTabWidget)
            parent = tab_bar.parent()
            if parent is not self._window:
                continue

            # Apply customizations
            if self._config.dock_tabs_closable:
                tab_bar.setTabsClosable(True)
                tab_bar.tabCloseRequested.connect(self._on_tab_close_requested)

            # Qt default is movable=True for dock tab bars, so explicitly set to match config
            tab_bar.setMovable(self._config.dock_tabs_movable)

            if self._config.dock_tabs_drag_to_undock:
                tab_bar.installEventFilter(self)

            tab_bar.setProperty("_qtpie_customized", True)

    def _handle_tab_bar_mouse_event(self, tab_bar: QTabBar, event: QEvent) -> None:
        """Handle mouse events on tab bar for drag-to-undock."""
        if event.type() == QEvent.Type.MouseButtonPress:
            mouse_event = cast(QMouseEvent, event)
            self._drag_start_pos = mouse_event.pos()
            self._drag_tab_index = tab_bar.tabAt(self._drag_start_pos)
            if self._drag_tab_index >= 0:
                self._drag_tab_text = tab_bar.tabText(self._drag_tab_index)
        elif event.type() == QEvent.Type.MouseMove and self._drag_tab_text is not None:
            mouse_event = cast(QMouseEvent, event)
            margin = self._config.dock_tabs_drag_margin
            padded = tab_bar.rect().adjusted(-margin, -margin, margin, margin)
            if not padded.contains(mouse_event.pos()):
                # Defer undock to next event loop iteration - this allows the current
                # event to finish processing before we destroy the tab bar
                tab_text = self._drag_tab_text
                self._drag_tab_text = None
                QTimer.singleShot(0, lambda: self._undock_tab(tab_text))
        elif event.type() in {QEvent.Type.MouseButtonRelease, QEvent.Type.Leave}:
            self._drag_tab_text = None

    def _undock_tab(self, tab_text: str) -> None:
        """Undock the tab with the given title to a floating window."""
        for dock in self._window.findChildren(QDockWidget):
            if dock.windowTitle() == tab_text:
                siblings = self._window.tabifiedDockWidgets(dock)
                # Must remove and re-add the dock to properly detach it from the tab group
                # Just setFloating(True) doesn't properly restore the title bar on Windows
                self._window.removeDockWidget(dock)
                self._window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
                dock.setFloating(True)
                dock.show()

                # Update title bars for all affected docks
                for d in [*siblings, dock]:
                    _update_title_bar_for_dock(self._window, d, self._config, self._dock_overrides)
                break

    def _on_tab_close_requested(self, index: int) -> None:
        """Handle tab close button click."""
        tab_bar = self.sender()
        if not isinstance(tab_bar, QTabBar):
            return

        tab_text = tab_bar.tabText(index)
        for dock in self._window.findChildren(QDockWidget):
            if dock.windowTitle() == tab_text:
                dock.close()
                break


def _setup_title_bar_hooks(
    window: QMainWindow,
    config: DockTabConfig,
    dock_overrides: dict[QDockWidget, dict[str, Any]],
) -> None:
    """Set up signal connections for title bar visibility management.

    Connects to topLevelChanged and dockLocationChanged signals on each dock
    to update title bar visibility when tabification state changes.
    """
    for dock in window.findChildren(QDockWidget):
        if dock.property("_qtpie_titlebar_hooks"):
            continue

        def make_handler(d: QDockWidget) -> Callable[..., None]:
            def handler(*_args: Any) -> None:
                _update_title_bar_for_dock(window, d, config, dock_overrides)

            return handler  # noqa: B023 - closure factory pattern, `d` is captured via parameter

        handler = make_handler(dock)
        dock.topLevelChanged.connect(handler)
        dock.dockLocationChanged.connect(handler)
        dock.setProperty("_qtpie_titlebar_hooks", True)

        # Apply initial state
        _update_title_bar_for_dock(window, dock, config, dock_overrides)


def _update_title_bar_for_dock(
    window: QMainWindow,
    dock: QDockWidget,
    config: DockTabConfig,
    dock_overrides: dict[QDockWidget, dict[str, Any]],
) -> None:
    """Update title bar visibility for a dock based on its tabification state.

    If the dock is tabified with others, hide its title bar (the tab bar shows the title).
    If the dock is standalone or floating, show its title bar.

    Args:
        window: The QMainWindow containing the dock
        dock: The dock widget to update
        config: Configuration with dock_tabs_hide_title_bar setting
        dock_overrides: Per-dock overrides
    """
    # Check if this dock has hideTitleBar=True (hidden unless floating)
    always_hide = dock_overrides.get(dock, {}).get("hide_title_bar")
    if always_hide is True:
        if dock.isFloating():
            _show_titlebar(dock)
        else:
            _hide_titlebar(dock)
        return

    # Check per-dock override first
    override = dock_overrides.get(dock, {}).get("hide_title_bar_when_tabbed")
    should_hide = override if override is not None else config.dock_tabs_hide_title_bar

    if not should_hide:
        # Feature disabled for this dock - ensure title bar is shown
        _show_titlebar(dock)
        return

    # Check if dock is tabified
    is_tabified = len(window.tabifiedDockWidgets(dock)) > 0
    is_floating = dock.isFloating()

    if is_tabified and not is_floating:
        _hide_titlebar(dock)
    else:
        _show_titlebar(dock)


def _hide_titlebar(dock: QDockWidget) -> None:
    """Hide a dock widget's title bar by replacing it with a zero-height widget."""
    if dock.property("_qtpie_titlebar_hidden"):
        return  # Already hidden
    hidden = QWidget()
    hidden.setFixedHeight(0)
    dock.setTitleBarWidget(hidden)
    dock.setProperty("_qtpie_titlebar_hidden", True)


def _show_titlebar(dock: QDockWidget) -> None:
    """Restore a dock widget's default title bar."""
    if not dock.property("_qtpie_titlebar_hidden"):
        return  # Not hidden by us

    # Set property first to prevent recursion
    dock.setProperty("_qtpie_titlebar_hidden", False)

    was_floating = dock.isFloating()

    # If already floating, we must unfloat first - setTitleBarWidget(None) doesn't
    # restore the title bar properly when the dock is already floating.
    # Block signals to prevent re-entry during the unfloat/refloat dance.
    if was_floating:
        dock.blockSignals(True)
        dock.setFloating(False)

    # Restore the default title bar
    dock.setTitleBarWidget(None)  # type: ignore[arg-type]

    # Refloat if it was floating
    if was_floating:
        dock.setFloating(True)
        dock.blockSignals(False)
