"""Dock tab customization features for QtPie windows.

This module provides window-level dock tab features:
- dockNesting: Enable nested dock splitting
- dockTabsPosition: Tab bar position for tabified docks
- dockTabsClosable: Show close buttons on dock tabs
- dockTabsMovable: Allow reordering tabs by dragging
- dockTabsHideTitleBar: Auto-hide title bar when dock is tabified
- dockTabsDragToUndock: Drag tab outside tab bar to float dock
"""

import logging
import sys
from collections.abc import Callable
from typing import Any, Protocol, cast, override

from qtpy.QtCore import QEvent, QObject, QPoint, Qt, QTimer
from qtpy.QtGui import QMouseEvent
from qtpy.QtWidgets import QDockWidget, QMainWindow, QMenu, QTabBar, QTabWidget, QWidget

from .dock import resize_all_docks
from .floating_dock_titlebar import FloatingDockTitleBar

logger = logging.getLogger(__name__)


def _debug(msg: str) -> None:
    """Debug log with immediate flush to catch crashes."""
    logger.debug(msg)
    for handler in logging.root.handlers + logger.handlers:
        handler.flush()
    sys.stderr.flush()
    sys.stdout.flush()


class DockTabConfig(Protocol):
    """Protocol for dock tab configuration (shared by WindowConfig and AppConfig)."""

    dock_nesting: bool
    dock_tabs_position: str
    dock_tabs_closable: bool
    dock_tabs_movable: bool
    dock_tabs_hide_title_bar: bool
    dock_tabs_drag_to_undock: bool
    dock_tabs_drag_margin: int
    dock_tabs_middle_click_close: bool
    dock_disable_floating_double_click: bool
    dock_maximize_floating_on_double_click: bool
    # Context menu configuration
    dock_menu: bool
    dock_menu_close: bool
    dock_menu_close_others: bool
    dock_menu_close_right: bool
    dock_menu_close_left: bool
    dock_menu_close_all: bool
    dock_menu_prepend_actions: bool


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
    # - Any tab feature is enabled (closable, drag-to-undock, hide title bar, middle-click close, context menu)
    # - OR if movable is explicitly False (need to override Qt's default of True)
    # - OR if any per-dock override wants to hide title bar
    # - OR if floating dock double-click behavior is customized
    needs_customization = any(
        [
            config.dock_tabs_closable,
            config.dock_tabs_drag_to_undock,
            config.dock_tabs_hide_title_bar,
            config.dock_tabs_middle_click_close,
            config.dock_disable_floating_double_click,
            config.dock_maximize_floating_on_double_click,
            config.dock_menu,
            any_dock_wants_hide_titlebar,
            any_dock_has_hide_titlebar,
            not config.dock_tabs_movable,  # Need to disable Qt's default movable=True
        ]
    )

    if not needs_customization:
        return

    event_filter = DockTabEventFilter(window, config, overrides)
    window.installEventFilter(event_filter)

    # If middle-click close or floating double-click customization is enabled, install filters on existing docks
    if config.dock_tabs_middle_click_close or config.dock_disable_floating_double_click or config.dock_maximize_floating_on_double_click:
        event_filter.install_dock_title_bar_filters()

    # If hide title bar is enabled (window-level or any per-dock override), OR
    # if double-click features are enabled (need to update title bar when floating state changes)
    if config.dock_tabs_hide_title_bar or any_dock_wants_hide_titlebar or any_dock_has_hide_titlebar or config.dock_disable_floating_double_click or config.dock_maximize_floating_on_double_click:
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
            if self._config.dock_tabs_middle_click_close or self._config.dock_disable_floating_double_click or self._config.dock_maximize_floating_on_double_click:
                self.install_dock_title_bar_filters()
        elif isinstance(watched, QTabBar):
            if self._config.dock_tabs_drag_to_undock:
                self._handle_tab_bar_mouse_event(watched, event)
            if self._config.dock_tabs_middle_click_close:
                if self._handle_middle_click(watched, event):
                    return True  # Event consumed
        elif isinstance(watched, QDockWidget):
            if self._config.dock_tabs_middle_click_close:
                if self._handle_dock_title_bar_middle_click(watched, event):
                    return True  # Event consumed
            if self._config.dock_disable_floating_double_click or self._config.dock_maximize_floating_on_double_click:
                if self._handle_dock_title_bar_double_click(watched, event):
                    return True  # Event consumed
        elif isinstance(watched, FloatingDockTitleBar):
            # Handle double-click on custom title bar
            if self._config.dock_disable_floating_double_click or self._config.dock_maximize_floating_on_double_click:
                if self._handle_custom_titlebar_double_click(watched, event):
                    return True  # Event consumed
        return super().eventFilter(watched, event)

    def _setup_new_dock_hooks(self) -> None:
        """Set up title bar hooks for any newly added docks and update all title bars."""
        needs_hooks = self._config.dock_tabs_hide_title_bar or self._config.dock_disable_floating_double_click or self._config.dock_maximize_floating_on_double_click
        if not needs_hooks:
            return

        for dock in self._window.findChildren(QDockWidget):
            if dock.property("_qtpie_titlebar_hooks"):
                continue

            def make_handler(d: QDockWidget) -> Callable[..., None]:
                def handler(*_args: Any) -> None:
                    dock_title = d.windowTitle()
                    is_floating = d.isFloating()
                    _debug(f"SIGNAL: topLevelChanged/dockLocationChanged for dock={dock_title!r}, is_floating={is_floating}")
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

            if self._config.dock_tabs_drag_to_undock or self._config.dock_tabs_middle_click_close:
                tab_bar.installEventFilter(self)

            # Enable context menu if configured
            if self._config.dock_menu:
                tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

                # Use a closure to capture tab_bar correctly
                # Need to define handler outside lambda for proper typing
                def make_context_menu_handler(
                    tb: QTabBar,
                ) -> Callable[[QPoint], None]:
                    def handler(pos: QPoint) -> None:
                        self._on_tab_context_menu(tb, pos)

                    return handler

                tab_bar.customContextMenuRequested.connect(make_context_menu_handler(tab_bar))

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

    def _handle_middle_click(self, tab_bar: QTabBar, event: QEvent) -> bool:
        """Handle middle mouse button click to close tab.

        Returns True if event was consumed, False otherwise.
        """
        if event.type() != QEvent.Type.MouseButtonRelease:
            return False

        mouse_event = cast(QMouseEvent, event)
        if mouse_event.button() != Qt.MouseButton.MiddleButton:
            return False

        tab_index = tab_bar.tabAt(mouse_event.pos())
        if tab_index < 0:
            return False

        tab_text = tab_bar.tabText(tab_index)
        for dock in self._window.findChildren(QDockWidget):
            if dock.windowTitle() == tab_text:
                dock.close()
                return True

        return False

    def install_dock_title_bar_filters(self) -> None:
        """Install event filters on dock widgets and custom title bars."""
        for dock in self._window.findChildren(QDockWidget):
            if not dock.property("_qtpie_dock_filter"):
                dock.installEventFilter(self)
                dock.setProperty("_qtpie_dock_filter", True)

            # Also install on custom title bar if present
            title_bar = dock.titleBarWidget()
            if isinstance(title_bar, FloatingDockTitleBar):
                if not title_bar.property("_qtpie_titlebar_filter"):
                    title_bar.installEventFilter(self)
                    title_bar.setProperty("_qtpie_titlebar_filter", True)

    def _handle_dock_title_bar_middle_click(self, dock: QDockWidget, event: QEvent) -> bool:
        """Handle middle mouse button click on dock title bar to close dock.

        Returns True if event was consumed, False otherwise.
        """
        if event.type() != QEvent.Type.MouseButtonRelease:
            return False

        mouse_event = cast(QMouseEvent, event)
        if mouse_event.button() != Qt.MouseButton.MiddleButton:
            return False

        # Check if click is in the title bar area (top portion of dock widget)
        # The title bar height is typically around 20-30 pixels
        # Note: titleBarWidget() returns None for default title bar, but stubs say QWidget
        title_bar = cast(QWidget | None, dock.titleBarWidget())
        if title_bar is not None and title_bar.height() > 0:
            # Custom title bar - check if click is within it
            title_bar_rect = title_bar.geometry()
            if not title_bar_rect.contains(mouse_event.pos()):
                return False
        else:
            # Default title bar or hidden title bar - check if click is in the top area
            # Use a reasonable height estimate for the default title bar
            title_bar_height = 30
            if mouse_event.pos().y() > title_bar_height:
                return False

        dock.close()
        return True

    def _handle_dock_title_bar_double_click(self, dock: QDockWidget, event: QEvent) -> bool:
        """Handle double-click on dock title bar for floating docks.

        If dock_maximize_floating_on_double_click is enabled, toggles maximize/restore.
        If only dock_disable_floating_double_click is enabled, just consumes the event.

        Returns True if event was consumed, False otherwise.
        """
        if event.type() != QEvent.Type.MouseButtonDblClick:
            return False

        mouse_event = cast(QMouseEvent, event)
        if mouse_event.button() != Qt.MouseButton.LeftButton:
            return False

        # Only handle floating docks
        if not dock.isFloating():
            return False

        # Check if click is in the title bar area (same logic as middle-click)
        title_bar = cast(QWidget | None, dock.titleBarWidget())
        if title_bar is not None and title_bar.height() > 0:
            title_bar_rect = title_bar.geometry()
            if not title_bar_rect.contains(mouse_event.pos()):
                return False
        else:
            title_bar_height = 30
            if mouse_event.pos().y() > title_bar_height:
                return False

        # Handle based on config
        if self._config.dock_maximize_floating_on_double_click:
            if dock.isMaximized():
                dock.showNormal()
            else:
                dock.showMaximized()
        # else: just consume the event (disable_floating_double_click)

        return True

    def _handle_custom_titlebar_double_click(self, title_bar: FloatingDockTitleBar, event: QEvent) -> bool:
        """Handle double-click on custom title bar widget.

        The custom title bar is only used for floating docks, so we don't need
        to check the floating state or title bar area.

        Returns True if event was consumed, False otherwise.
        """
        if event.type() != QEvent.Type.MouseButtonDblClick:
            return False

        mouse_event = cast(QMouseEvent, event)
        if mouse_event.button() != Qt.MouseButton.LeftButton:
            return False

        # Get the parent dock widget
        dock = title_bar.parent()
        if not isinstance(dock, QDockWidget):
            return False

        # Handle based on config
        if self._config.dock_maximize_floating_on_double_click:
            if dock.isMaximized():
                dock.showNormal()
            else:
                dock.showMaximized()
        # else: just consume the event (disable_floating_double_click)

        return True

    # -------------------------------------------------------------------------
    # Context menu handling
    # -------------------------------------------------------------------------

    def _on_tab_context_menu(self, tab_bar: QTabBar, pos: QPoint) -> None:
        """Handle context menu request on tab bar."""
        # Get the tab index at the click position
        tab_index = tab_bar.tabAt(pos)
        if tab_index < 0:
            return  # Click was not on a tab

        tab_title = tab_bar.tabText(tab_index)
        tab_count = tab_bar.count()

        # Find the QDockWidget for this tab
        dock_widget: QDockWidget | None = None
        for dock in self._window.findChildren(QDockWidget):
            if dock.windowTitle() == tab_title:
                dock_widget = dock
                break

        if dock_widget is None:
            return

        # Check for custom context menu on this dock (from overrides or property)
        custom_menu_class = self._dock_overrides.get(dock_widget, {}).get("context_menu")
        if custom_menu_class is None:
            # Also check dock property (for repeater docks)
            custom_menu_class = dock_widget.property("_qtpie_context_menu")

        if custom_menu_class is not None:
            # Use custom menu
            menu = self._create_custom_context_menu(dock_widget, custom_menu_class, tab_index, tab_count)
        else:
            # Use built-in menu
            menu = self._create_builtin_context_menu(dock_widget, tab_index, tab_count)

        if menu.actions():
            menu.exec(tab_bar.mapToGlobal(pos))

    def _create_builtin_context_menu(
        self,
        dock_widget: QDockWidget,
        tab_index: int,
        tab_count: int,
    ) -> QMenu:
        """Create the built-in context menu with close actions."""
        menu = QMenu()
        config = self._config

        # Close action (always visible unless disabled)
        if config.dock_menu_close:
            close_action = menu.addAction("Close")
            close_action.triggered.connect(dock_widget.close)

        # Close Others (only if >1 tab)
        if config.dock_menu_close_others and tab_count > 1:
            close_others_action = menu.addAction("Close Others")
            close_others_action.triggered.connect(lambda: self._close_others(dock_widget))

        # Close to the Right (only if tabs to the right)
        if config.dock_menu_close_right and tab_index < tab_count - 1:
            close_right_action = menu.addAction("Close to the Right")
            close_right_action.triggered.connect(lambda: self._close_to_right(dock_widget, tab_index))

        # Close to the Left (only if tabs to the left)
        if config.dock_menu_close_left and tab_index > 0:
            close_left_action = menu.addAction("Close to the Left")
            close_left_action.triggered.connect(lambda: self._close_to_left(dock_widget, tab_index))

        # Close All (only if >1 tab)
        if config.dock_menu_close_all and tab_count > 1:
            if menu.actions():
                menu.addSeparator()
            close_all_action = menu.addAction("Close All")
            close_all_action.triggered.connect(lambda: self._close_all(dock_widget))

        return menu

    def _create_custom_context_menu(
        self,
        dock_widget: QDockWidget,
        menu_class: type[QMenu],
        tab_index: int,
        tab_count: int,
    ) -> QMenu:
        """Create a custom menu, optionally prepending built-in actions."""
        # Create the custom menu instance
        custom_menu = menu_class()

        # Prepend built-in actions if configured
        if self._config.dock_menu_prepend_actions:
            # Get existing custom actions before modifying
            custom_actions = list(custom_menu.actions())
            first_custom_action = custom_actions[0] if custom_actions else None

            # Add built-in actions directly to custom_menu (not from another menu)
            # This ensures proper Qt ownership
            config = self._config

            # Close action
            if config.dock_menu_close:
                close_action = custom_menu.addAction("Close")
                close_action.triggered.connect(dock_widget.close)
                if first_custom_action:
                    custom_menu.removeAction(close_action)
                    custom_menu.insertAction(first_custom_action, close_action)

            # Close Others (only if >1 tab)
            if config.dock_menu_close_others and tab_count > 1:
                close_others_action = custom_menu.addAction("Close Others")
                close_others_action.triggered.connect(lambda: self._close_others(dock_widget))
                if first_custom_action:
                    custom_menu.removeAction(close_others_action)
                    custom_menu.insertAction(first_custom_action, close_others_action)

            # Close to the Right (only if tabs to the right)
            if config.dock_menu_close_right and tab_index < tab_count - 1:
                close_right_action = custom_menu.addAction("Close to the Right")
                close_right_action.triggered.connect(lambda: self._close_to_right(dock_widget, tab_index))
                if first_custom_action:
                    custom_menu.removeAction(close_right_action)
                    custom_menu.insertAction(first_custom_action, close_right_action)

            # Close to the Left (only if tabs to the left)
            if config.dock_menu_close_left and tab_index > 0:
                close_left_action = custom_menu.addAction("Close to the Left")
                close_left_action.triggered.connect(lambda: self._close_to_left(dock_widget, tab_index))
                if first_custom_action:
                    custom_menu.removeAction(close_left_action)
                    custom_menu.insertAction(first_custom_action, close_left_action)

            # Close All (only if >1 tab)
            if config.dock_menu_close_all and tab_count > 1:
                close_all_action = custom_menu.addAction("Close All")
                close_all_action.triggered.connect(lambda: self._close_all(dock_widget))
                if first_custom_action:
                    custom_menu.removeAction(close_all_action)
                    custom_menu.insertAction(first_custom_action, close_all_action)

            # Add separator between built-in and custom (if we added any built-in actions)
            if first_custom_action:
                # Check if we actually added anything
                current_actions = custom_menu.actions()
                if current_actions[0] is not first_custom_action:
                    custom_menu.insertSeparator(first_custom_action)

        return custom_menu

    def _close_others(self, dock_widget: QDockWidget) -> None:
        """Close all docks in the same tab group except the given one."""
        siblings = self._window.tabifiedDockWidgets(dock_widget)
        for sibling in siblings:
            sibling.close()
        resize_all_docks(self._window)

    def _close_to_right(self, dock_widget: QDockWidget, current_index: int) -> None:
        """Close all tabs to the right of the given dock."""
        for tab_bar in self._window.findChildren(QTabBar):
            for i in range(tab_bar.count()):
                if tab_bar.tabText(i) == dock_widget.windowTitle():
                    # Found our tab bar - close tabs to the right (reverse order)
                    for j in range(tab_bar.count() - 1, current_index, -1):
                        tab_title = tab_bar.tabText(j)
                        for dock in self._window.findChildren(QDockWidget):
                            if dock.windowTitle() == tab_title:
                                dock.close()
                                break
                    resize_all_docks(self._window)
                    return

    def _close_to_left(self, dock_widget: QDockWidget, current_index: int) -> None:
        """Close all tabs to the left of the given dock."""
        for tab_bar in self._window.findChildren(QTabBar):
            for i in range(tab_bar.count()):
                if tab_bar.tabText(i) == dock_widget.windowTitle():
                    # Found our tab bar - close tabs to the left (reverse order)
                    for j in range(current_index - 1, -1, -1):
                        tab_title = tab_bar.tabText(j)
                        for dock in self._window.findChildren(QDockWidget):
                            if dock.windowTitle() == tab_title:
                                dock.close()
                                break
                    resize_all_docks(self._window)
                    return

    def _close_all(self, dock_widget: QDockWidget) -> None:
        """Close all tabs in the same group including the given dock."""
        siblings = list(self._window.tabifiedDockWidgets(dock_widget))
        siblings.append(dock_widget)
        for dock in siblings:
            dock.close()
        resize_all_docks(self._window)


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
                dock_title = d.windowTitle()
                is_floating = d.isFloating()
                _debug(f"SIGNAL: topLevelChanged/dockLocationChanged for dock={dock_title!r}, is_floating={is_floating}")
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
    dock_title = dock.windowTitle()
    _debug(f"_update_title_bar_for_dock: dock={dock_title!r}")

    # Determine if we need a custom title bar for floating docks
    # (to intercept double-click events that native title bars don't expose)
    needs_custom_titlebar = config.dock_disable_floating_double_click or config.dock_maximize_floating_on_double_click
    is_floating = dock.isFloating()
    _debug(f"  needs_custom_titlebar={needs_custom_titlebar}, is_floating={is_floating}")

    # Check if this dock has hideTitleBar=True (hidden unless floating)
    always_hide = dock_overrides.get(dock, {}).get("hide_title_bar")
    if always_hide is True:
        if is_floating:
            _show_titlebar(dock, use_custom=needs_custom_titlebar)
        else:
            _hide_titlebar(dock)
        return

    # Check per-dock override first
    override = dock_overrides.get(dock, {}).get("hide_title_bar_when_tabbed")
    should_hide = override if override is not None else config.dock_tabs_hide_title_bar

    if not should_hide:
        # Feature disabled for this dock - ensure title bar is shown
        # Use custom title bar for floating docks if double-click features enabled
        use_custom = needs_custom_titlebar and is_floating
        _show_titlebar(dock, use_custom=use_custom)
        return

    # Check if dock is tabified
    is_tabified = len(window.tabifiedDockWidgets(dock)) > 0

    if is_tabified and not is_floating:
        _hide_titlebar(dock)
    else:
        # Use custom title bar for floating docks if double-click features enabled
        use_custom = needs_custom_titlebar and is_floating
        _show_titlebar(dock, use_custom=use_custom)


def _hide_titlebar(dock: QDockWidget) -> None:
    """Hide a dock widget's title bar by replacing it with a zero-height widget."""
    dock_title = dock.windowTitle()
    _debug(f"_hide_titlebar: dock={dock_title!r}")
    if dock.property("_qtpie_titlebar_hidden"):
        _debug("  -> early return: already hidden")
        return  # Already hidden
    hidden = QWidget()
    hidden.setFixedHeight(0)
    dock.setTitleBarWidget(hidden)
    dock.setProperty("_qtpie_titlebar_hidden", True)
    _debug("  -> title bar hidden")


def _show_titlebar(dock: QDockWidget, use_custom: bool = False) -> None:
    """Restore or set a dock widget's title bar.

    Args:
        dock: The dock widget to update
        use_custom: If True, use a custom title bar widget instead of the native one.
                   This is needed for intercepting double-click events on floating docks.
    """
    dock_title = dock.windowTitle()
    _debug(f"_show_titlebar: dock={dock_title!r}, use_custom={use_custom}")

    was_hidden = dock.property("_qtpie_titlebar_hidden")
    has_custom = dock.property("_qtpie_custom_titlebar")
    _debug(f"  was_hidden={was_hidden}, has_custom={has_custom}")

    # Check if we need to do anything
    if not was_hidden and not use_custom and not has_custom:
        _debug("  -> early return: title bar is already native and we don't need custom")
        return  # Title bar is already native and we don't need custom
    if use_custom and has_custom:
        _debug("  -> early return: already using custom title bar")
        return  # Already using custom title bar

    # Set property first to prevent recursion
    dock.setProperty("_qtpie_titlebar_hidden", False)

    was_floating = dock.isFloating()
    _debug(f"  was_floating={was_floating}")

    # Use custom title bar if requested (for double-click interception)
    if use_custom:
        # Setting a custom titlebar works directly even when floating
        _debug("  -> creating FloatingDockTitleBar")
        custom_titlebar = FloatingDockTitleBar(dock)
        _debug("  -> setTitleBarWidget(custom_titlebar)")
        dock.setTitleBarWidget(custom_titlebar)
        dock.setProperty("_qtpie_custom_titlebar", True)
        _debug("  -> custom title bar set")
    else:
        # Restoring native titlebar requires unfloat/refloat dance when floating
        # because setTitleBarWidget(None) doesn't work properly when dock is floating
        if was_floating:
            _debug("  -> blockSignals(True)")
            dock.blockSignals(True)
            _debug("  -> setFloating(False)")
            dock.setFloating(False)
            _debug("  -> setFloating(False) completed")

        _debug("  -> setTitleBarWidget(None) to restore native")
        # Get the old titlebar before replacing it
        old_titlebar = dock.titleBarWidget()
        # Restore the default title bar
        dock.setTitleBarWidget(None)  # type: ignore[arg-type]
        dock.setProperty("_qtpie_custom_titlebar", False)
        # Explicitly delete the old custom titlebar to avoid dangling references
        if isinstance(old_titlebar, FloatingDockTitleBar):
            _debug("  -> deleting old FloatingDockTitleBar")
            old_titlebar.deleteLater()
        _debug("  -> native title bar restored")

        # Refloat if it was floating
        if was_floating:
            _debug("  -> setFloating(True)")
            dock.setFloating(True)
            _debug("  -> blockSignals(False)")
            dock.blockSignals(False)
            _debug("  -> refloat completed")
