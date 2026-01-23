# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownParameterType=false
# pyright: reportMissingParameterType=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportMissingImports=false
# pyright: reportArgumentType=false
# pyright: reportCallIssue=false
"""Tests for dock tab context menu features."""

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QTabBar, QWidget

from qtpie import Variable, Window, new, window
from qtpie.dock import Dock
from qtpie.testing import QtDriver

# =============================================================================
# Test Fixtures and Helpers
# =============================================================================


class SimplePanel(QWidget):
    """Simple test panel."""

    pass


class PropertiesPanel(QWidget):
    """Properties panel for testing."""

    pass


class InspectorPanel(QWidget):
    """Inspector panel for testing."""

    pass


class ConsolePanel(QWidget):
    """Console panel for testing."""

    pass


def find_dock_tab_bar(win: Window[Any], tab_texts: list[str]) -> QTabBar | None:
    """Find a tab bar that contains tabs with the given texts."""
    tab_bars = win.findChildren(QTabBar)
    for tb in tab_bars:
        # Check if parent is the window (dock tab bar, not nested QTabWidget)
        if tb.parent() is not win:
            continue
        for text in tab_texts:
            for i in range(tb.count()):
                if tb.tabText(i) == text:
                    return tb
    return None


def get_tab_index(tab_bar: QTabBar, text: str) -> int:
    """Get the index of a tab by its text."""
    for i in range(tab_bar.count()):
        if tab_bar.tabText(i) == text:
            return i
    return -1


def create_context_menu_for_tab(win: Window[Any], tab_bar: QTabBar, tab_index: int) -> QMenu | None:
    """Create the context menu that would appear for a tab.

    This replicates the internal menu creation logic for testing purposes.
    """
    from PySide6.QtWidgets import QDockWidget

    # Get tab info
    tab_title = tab_bar.tabText(tab_index)
    tab_count = tab_bar.count()

    # Find the QDockWidget for this tab
    dock_widget = None
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() == tab_title:
            dock_widget = dock
            break

    if dock_widget is None:
        return None

    config = win._qtpie_config

    # Check for custom context menu
    # First check in fields by finding which field's dock matches this dock_widget
    custom_menu_class = None
    for name, field in config.fields.items():
        if hasattr(win, name):
            dock_obj = getattr(win, name)
            if hasattr(dock_obj, "dock_widget") and dock_obj.dock_widget is dock_widget:
                # Found the field for this dock
                if hasattr(field, "dock_context_menu") and field.dock_context_menu is not None:
                    custom_menu_class = field.dock_context_menu
                break

    # Also check dock property (for repeater docks)
    if custom_menu_class is None:
        custom_menu_class = dock_widget.property("_qtpie_context_menu")

    if custom_menu_class is not None:
        # Create custom menu
        custom_menu = custom_menu_class()

        # Prepend built-in actions if configured
        if config.dock_menu_prepend_actions:
            # Get existing custom actions before modifying
            custom_actions = list(custom_menu.actions())
            first_custom_action = custom_actions[0] if custom_actions else None

            # Add built-in actions directly to custom_menu (ensures proper Qt ownership)
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
                if first_custom_action:
                    custom_menu.removeAction(close_others_action)
                    custom_menu.insertAction(first_custom_action, close_others_action)

            # Close to the Right (only if tabs to the right)
            if config.dock_menu_close_right and tab_index < tab_count - 1:
                close_right_action = custom_menu.addAction("Close to the Right")
                if first_custom_action:
                    custom_menu.removeAction(close_right_action)
                    custom_menu.insertAction(first_custom_action, close_right_action)

            # Close to the Left (only if tabs to the left)
            if config.dock_menu_close_left and tab_index > 0:
                close_left_action = custom_menu.addAction("Close to the Left")
                if first_custom_action:
                    custom_menu.removeAction(close_left_action)
                    custom_menu.insertAction(first_custom_action, close_left_action)

            # Close All (only if >1 tab)
            if config.dock_menu_close_all and tab_count > 1:
                close_all_action = custom_menu.addAction("Close All")
                if first_custom_action:
                    custom_menu.removeAction(close_all_action)
                    custom_menu.insertAction(first_custom_action, close_all_action)

            # Add separator between built-in and custom (if we added any)
            if first_custom_action:
                current_actions = custom_menu.actions()
                if current_actions[0] is not first_custom_action:
                    custom_menu.insertSeparator(first_custom_action)

        return custom_menu
    else:
        return _create_builtin_menu(config, dock_widget, tab_index, tab_count)


def _create_builtin_menu(config: Any, dock_widget: Any, tab_index: int, tab_count: int) -> QMenu:
    """Create the built-in context menu with close actions."""
    menu = QMenu()

    # Close action (always visible unless disabled)
    if config.dock_menu_close:
        close_action = menu.addAction("Close")
        close_action.triggered.connect(dock_widget.close)

    # Close Others (only if >1 tab)
    if config.dock_menu_close_others and tab_count > 1:
        menu.addAction("Close Others")

    # Close to the Right (only if tabs to the right)
    if config.dock_menu_close_right and tab_index < tab_count - 1:
        menu.addAction("Close to the Right")

    # Close to the Left (only if tabs to the left)
    if config.dock_menu_close_left and tab_index > 0:
        menu.addAction("Close to the Left")

    # Close All (only if >1 tab)
    if config.dock_menu_close_all and tab_count > 1:
        if menu.actions():
            menu.addSeparator()
        menu.addAction("Close All")

    return menu


def get_menu_action_texts(menu: QMenu) -> list[str]:
    """Get all action texts from a menu (excluding separators)."""
    return [action.text() for action in menu.actions() if not action.isSeparator()]


# =============================================================================
# Test Built-in Context Menu Creation
# =============================================================================


class TestBuiltinContextMenuCreation:
    """Test that the built-in context menu is created correctly."""

    def test_context_menu_enabled_by_default(self, qt: QtDriver) -> None:
        """dockMenu is True by default and tab bar has context menu policy."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Check config has menu enabled by default
        assert win._qtpie_config.dock_menu is True

        # Find tab bar and verify context menu policy is set
        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None
        assert tab_bar.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu

    def test_context_menu_disabled(self, qt: QtDriver) -> None:
        """dockMenu=False disables context menu on tab bar."""

        @window(dockMenu=False)
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        assert win._qtpie_config.dock_menu is False

        # Find tab bar
        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        # Verify context menu is NOT enabled (default Qt policy)
        assert tab_bar.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu

    def test_builtin_menu_has_close_action(self, qt: QtDriver) -> None:
        """Built-in menu always has Close action."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close" in actions

    def test_builtin_menu_has_all_actions_for_multiple_tabs(self, qt: QtDriver) -> None:
        """Built-in menu has all actions when there are multiple tabs."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _console: Dock[ConsolePanel] = new(group="inspector", title="Console")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector", "Console"])
        assert tab_bar is not None

        # Get menu for middle tab (should have both left and right tabs)
        inspector_idx = get_tab_index(tab_bar, "Inspector")
        menu = create_context_menu_for_tab(win, tab_bar, inspector_idx)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close" in actions
        assert "Close Others" in actions
        assert "Close All" in actions

        # Middle tab should have both left and right options
        props_idx = get_tab_index(tab_bar, "Properties")
        console_idx = get_tab_index(tab_bar, "Console")

        # Inspector is between the other two
        if props_idx < inspector_idx < console_idx or console_idx < inspector_idx < props_idx:
            assert "Close to the Right" in actions
            assert "Close to the Left" in actions


# =============================================================================
# Test Visibility Rules
# =============================================================================


class TestMenuVisibilityRules:
    """Test that menu actions appear/hide based on tab position and count."""

    def test_close_others_only_if_multiple_tabs(self, qt: QtDriver) -> None:
        """Close Others only appears if there's more than one tab.

        With a single dock (no group), the config still applies but there's
        no tab bar. We test this by checking the menu creation logic directly
        with tab_count=1.
        """
        from PySide6.QtWidgets import QDockWidget

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", title="Properties")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Get the dock widget directly
        dock_widget = win.findChild(QDockWidget)
        assert dock_widget is not None

        # Create menu with tab_count=1 to simulate single tab
        menu = _create_builtin_menu(win._qtpie_config, dock_widget, 0, 1)

        actions = get_menu_action_texts(menu)
        assert "Close Others" not in actions

    def test_close_others_appears_with_multiple_tabs(self, qt: QtDriver) -> None:
        """Close Others appears when there are multiple tabs."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close Others" in actions

    def test_close_all_only_if_multiple_tabs(self, qt: QtDriver) -> None:
        """Close All only appears if there's more than one tab."""
        from PySide6.QtWidgets import QDockWidget

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", title="Properties")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Get the dock widget directly
        dock_widget = win.findChild(QDockWidget)
        assert dock_widget is not None

        # Create menu with tab_count=1 to simulate single tab
        menu = _create_builtin_menu(win._qtpie_config, dock_widget, 0, 1)

        actions = get_menu_action_texts(menu)
        assert "Close All" not in actions

    def test_close_to_right_only_if_tabs_to_right(self, qt: QtDriver) -> None:
        """Close to the Right only appears if there are tabs to the right."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        # Last tab should NOT have "Close to the Right"
        last_idx = tab_bar.count() - 1
        menu = create_context_menu_for_tab(win, tab_bar, last_idx)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close to the Right" not in actions

    def test_close_to_left_only_if_tabs_to_left(self, qt: QtDriver) -> None:
        """Close to the Left only appears if there are tabs to the left."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        # First tab should NOT have "Close to the Left"
        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close to the Left" not in actions

    def test_first_tab_has_close_to_right_not_left(self, qt: QtDriver) -> None:
        """First tab has Close to Right but not Close to Left."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close to the Right" in actions
        assert "Close to the Left" not in actions

    def test_last_tab_has_close_to_left_not_right(self, qt: QtDriver) -> None:
        """Last tab has Close to Left but not Close to Right."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        last_idx = tab_bar.count() - 1
        menu = create_context_menu_for_tab(win, tab_bar, last_idx)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close to the Left" in actions
        assert "Close to the Right" not in actions


# =============================================================================
# Test Individual Toggle Options
# =============================================================================


class TestIndividualToggleOptions:
    """Test that individual dockMenu* toggles work correctly."""

    def test_dock_menu_close_false_hides_close_action(self, qt: QtDriver) -> None:
        """dockMenuClose=False hides the Close action."""

        @window(dockMenuClose=False)
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close" not in actions
        # Other actions should still be present
        assert "Close Others" in actions

    def test_dock_menu_close_others_false_hides_close_others(self, qt: QtDriver) -> None:
        """dockMenuCloseOthers=False hides Close Others action."""

        @window(dockMenuCloseOthers=False)
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close" in actions
        assert "Close Others" not in actions

    def test_dock_menu_close_right_false_hides_close_to_right(self, qt: QtDriver) -> None:
        """dockMenuCloseRight=False hides Close to the Right action."""

        @window(dockMenuCloseRight=False)
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        # First tab normally would have Close to Right
        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close to the Right" not in actions

    def test_dock_menu_close_left_false_hides_close_to_left(self, qt: QtDriver) -> None:
        """dockMenuCloseLeft=False hides Close to the Left action."""

        @window(dockMenuCloseLeft=False)
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        # Last tab normally would have Close to Left
        last_idx = tab_bar.count() - 1
        menu = create_context_menu_for_tab(win, tab_bar, last_idx)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close to the Left" not in actions

    def test_dock_menu_close_all_false_hides_close_all(self, qt: QtDriver) -> None:
        """dockMenuCloseAll=False hides Close All action."""

        @window(dockMenuCloseAll=False)
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close All" not in actions

    def test_all_toggles_false_creates_empty_menu(self, qt: QtDriver) -> None:
        """All toggles false creates an empty menu."""

        @window(
            dockMenuClose=False,
            dockMenuCloseOthers=False,
            dockMenuCloseRight=False,
            dockMenuCloseLeft=False,
            dockMenuCloseAll=False,
        )
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert len(actions) == 0


# =============================================================================
# Test Custom Context Menu
# =============================================================================


class CustomDockMenu(QMenu):
    """Custom context menu for testing."""

    def __init__(self) -> None:
        super().__init__()
        self.addAction("Custom Action 1")
        self.addAction("Custom Action 2")


class TestCustomContextMenu:
    """Test custom context menu support."""

    def test_custom_menu_overrides_builtin(self, qt: QtDriver) -> None:
        """contextMenu= parameter creates custom menu instead of built-in."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="g",
                title="Properties",
                contextMenu=CustomDockMenu,
            )
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        props_idx = get_tab_index(tab_bar, "Properties")
        menu = create_context_menu_for_tab(win, tab_bar, props_idx)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        # Should have custom actions, not built-in
        assert "Custom Action 1" in actions
        assert "Custom Action 2" in actions
        assert "Close" not in actions
        assert "Close Others" not in actions

    def test_custom_menu_only_affects_that_dock(self, qt: QtDriver) -> None:
        """Custom menu only applies to the dock it's set on."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="g",
                title="Properties",
                contextMenu=CustomDockMenu,
            )
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        # Inspector should have built-in menu
        inspector_idx = get_tab_index(tab_bar, "Inspector")
        menu = create_context_menu_for_tab(win, tab_bar, inspector_idx)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close" in actions
        assert "Custom Action 1" not in actions

    def test_prepend_actions_adds_builtin_before_custom(self, qt: QtDriver) -> None:
        """dockMenuPrependActions=True adds built-in actions before custom."""

        @window(dockMenuPrependActions=True)
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="g",
                title="Properties",
                contextMenu=CustomDockMenu,
            )
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        props_idx = get_tab_index(tab_bar, "Properties")
        menu = create_context_menu_for_tab(win, tab_bar, props_idx)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        # Should have both built-in and custom actions
        assert "Close" in actions
        assert "Close Others" in actions
        assert "Custom Action 1" in actions
        assert "Custom Action 2" in actions

        # Built-in should come before custom
        close_idx = actions.index("Close")
        custom_idx = actions.index("Custom Action 1")
        assert close_idx < custom_idx

    def test_prepend_false_only_shows_custom(self, qt: QtDriver) -> None:
        """dockMenuPrependActions=False (default) only shows custom menu."""

        @window(dockMenuPrependActions=False)
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="g",
                title="Properties",
                contextMenu=CustomDockMenu,
            )
            _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        props_idx = get_tab_index(tab_bar, "Properties")
        menu = create_context_menu_for_tab(win, tab_bar, props_idx)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Custom Action 1" in actions
        assert "Close" not in actions


# =============================================================================
# Test Dock Close Methods
# =============================================================================


class TestDockMethods:
    """Test new Dock methods for tab operations."""

    def test_close_others_method(self, qt: QtDriver) -> None:
        """close_others() closes all tabs in group except the dock."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _console: Dock[ConsolePanel] = new(group="inspector", title="Console")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # All should be visible
        assert win._props.is_visible is True
        assert win._inspector.is_visible is True
        assert win._console.is_visible is True

        # Close others from props perspective
        win._props.close_others()
        qt.process_events()

        # Props should still be visible, others should be closed
        assert win._props.is_visible is True
        assert win._inspector.is_visible is False
        assert win._console.is_visible is False

    def test_close_to_right_method(self, qt: QtDriver) -> None:
        """close_to_right() closes tabs to the right in tab bar."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _console: Dock[ConsolePanel] = new(group="inspector", title="Console")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Find tab bar to check order
        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector", "Console"])
        assert tab_bar is not None

        props_idx = get_tab_index(tab_bar, "Properties")
        inspector_idx = get_tab_index(tab_bar, "Inspector")
        console_idx = get_tab_index(tab_bar, "Console")

        # Close to the right from props
        win._props.close_to_right()
        qt.process_events()

        # Props should still be visible
        assert win._props.is_visible is True

        # Tabs to the right of props should be closed
        if inspector_idx > props_idx:
            assert win._inspector.is_visible is False
        if console_idx > props_idx:
            assert win._console.is_visible is False

    def test_close_to_left_method(self, qt: QtDriver) -> None:
        """close_to_left() closes tabs to the left in tab bar."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _console: Dock[ConsolePanel] = new(group="inspector", title="Console")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Find tab bar to check order
        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector", "Console"])
        assert tab_bar is not None

        props_idx = get_tab_index(tab_bar, "Properties")
        inspector_idx = get_tab_index(tab_bar, "Inspector")
        console_idx = get_tab_index(tab_bar, "Console")

        # Close to the left from console
        win._console.close_to_left()
        qt.process_events()

        # Console should still be visible
        assert win._console.is_visible is True

        # Tabs to the left of console should be closed
        if props_idx < console_idx:
            assert win._props.is_visible is False
        if inspector_idx < console_idx:
            assert win._inspector.is_visible is False

    def test_close_all_method(self, qt: QtDriver) -> None:
        """close_all() closes all tabs in group including self."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Both visible
        assert win._props.is_visible is True
        assert win._inspector.is_visible is True

        # Close all from props
        win._props.close_all()
        qt.process_events()

        # Both should be closed
        assert win._props.is_visible is False
        assert win._inspector.is_visible is False

    def test_has_tabs_to_right_property(self, qt: QtDriver) -> None:
        """has_tabs_to_right property returns correct value."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Find tab bar to determine order
        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        props_idx = get_tab_index(tab_bar, "Properties")
        inspector_idx = get_tab_index(tab_bar, "Inspector")

        if props_idx < inspector_idx:
            assert win._props.has_tabs_to_right is True
            assert win._inspector.has_tabs_to_right is False
        else:
            assert win._inspector.has_tabs_to_right is True
            assert win._props.has_tabs_to_right is False

    def test_has_tabs_to_left_property(self, qt: QtDriver) -> None:
        """has_tabs_to_left property returns correct value."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Find tab bar to determine order
        tab_bar = find_dock_tab_bar(win, ["Properties", "Inspector"])
        assert tab_bar is not None

        props_idx = get_tab_index(tab_bar, "Properties")
        inspector_idx = get_tab_index(tab_bar, "Inspector")

        if props_idx < inspector_idx:
            assert win._props.has_tabs_to_left is False
            assert win._inspector.has_tabs_to_left is True
        else:
            assert win._inspector.has_tabs_to_left is False
            assert win._props.has_tabs_to_left is True

    def test_tab_count_property(self, qt: QtDriver) -> None:
        """tab_count property returns correct count."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _console: Dock[ConsolePanel] = new(group="inspector", title="Console")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # All three in same group
        assert win._props.tab_count == 3
        assert win._inspector.tab_count == 3
        assert win._console.tab_count == 3


# =============================================================================
# Test Variable[list[T], Dock[W]] Context Menu
# =============================================================================


@dataclass
class EditorItem:
    """Simple item type for testing dock repeaters."""

    name: str = "Untitled"


class EditorWidget(QWidget):
    """Simple widget for testing dock repeaters."""

    pass


class TestVariableListDockContextMenu:
    """Test context menu with Variable[list[T], Dock[W]] repeaters."""

    def test_context_menu_enabled_on_repeater_docks(self, qt: QtDriver) -> None:
        """Context menu is enabled on dynamically created docks."""

        @window
        class TestWindow(Window):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Add items
        win._editors.append(EditorItem(name="File1"))
        qt.process_events()
        win._editors.append(EditorItem(name="File2"))
        qt.process_events()

        # Find tab bar
        tab_bar = find_dock_tab_bar(win, ["File1", "File2"])
        assert tab_bar is not None

        # Tab bar should have context menu enabled
        assert tab_bar.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu

    def test_repeater_dock_has_builtin_menu(self, qt: QtDriver) -> None:
        """Repeater dock gets built-in context menu."""

        @window
        class TestWindow(Window):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        win._editors.append(EditorItem(name="File1"))
        qt.process_events()
        win._editors.append(EditorItem(name="File2"))
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["File1", "File2"])
        assert tab_bar is not None

        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Close" in actions
        assert "Close Others" in actions

    def test_custom_menu_on_repeater_docks(self, qt: QtDriver) -> None:
        """Custom context menu works on repeater docks."""

        @window
        class TestWindow(Window):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                contextMenu=CustomDockMenu,
            )

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        # Add two items to create a tab bar
        win._editors.append(EditorItem(name="File1"))
        win._editors.append(EditorItem(name="File2"))
        qt.process_events()

        tab_bar = find_dock_tab_bar(win, ["File1", "File2"])
        assert tab_bar is not None

        menu = create_context_menu_for_tab(win, tab_bar, 0)
        assert menu is not None

        actions = get_menu_action_texts(menu)
        assert "Custom Action 1" in actions
        assert "Custom Action 2" in actions
        assert "Close" not in actions

    def test_repeater_close_removes_from_list(self, qt: QtDriver) -> None:
        """Closing a repeater dock removes the item from the list."""

        @window
        class TestWindow(Window):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        win._editors.append(EditorItem(name="File1"))
        win._editors.append(EditorItem(name="File2"))
        qt.process_events()

        assert len(win._editors) == 2

        # Close first dock
        win._editors.widget[0].close()
        qt.process_events()

        # List should have one item
        assert len(win._editors) == 1
        assert win._editors[0].name == "File2"
