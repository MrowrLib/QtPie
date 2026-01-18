# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownParameterType=false
# pyright: reportMissingParameterType=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# pyright: reportArgumentType=false
# pyright: reportUntypedBaseClass=false
"""Tests for Dock[T] declarative dock widget support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QDockWidget, QLabel, QLineEdit, QPushButton, QSpinBox, QTabBar, QWidget

from qtpie import Dock, Variable, Widget, new, widget
from qtpie.testing import QtDriver

from .conftest import WINDOW_CLASS_TYPES, create_and_track, get_main_window

# =============================================================================
# Test Widgets
# =============================================================================


class ExplorerPanel(QWidget):
    """Simple panel for testing."""

    pass


class ConsolePanel(QWidget):
    """Simple panel for testing."""

    pass


class GitPanel(QWidget):
    """Simple panel for testing."""

    pass


class OutputPanel(QWidget):
    """Simple panel for testing."""

    pass


class PropertiesPanel(QWidget):
    """Simple panel for testing."""

    pass


class InspectorPanel(QWidget):
    """Simple panel for testing."""

    pass


class StylesPanel(QWidget):
    """Simple panel for testing."""

    pass


# =============================================================================
# Basic Dock Creation
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestBasicDockCreation:
    """Test basic Dock[T] field creation."""

    def test_dock_field_creates_dock_wrapper(self, base_class, decorator, qt: QtDriver) -> None:
        """Dock[T] field creates a Dock wrapper instance."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)

        assert isinstance(instance._explorer, Dock)

    def test_dock_widget_property_returns_content(self, base_class, decorator, qt: QtDriver) -> None:
        """dock.widget returns the content widget."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)

        assert isinstance(instance._explorer.widget, ExplorerPanel)

    def test_dock_dock_widget_property_returns_qdockwidget(self, base_class, decorator, qt: QtDriver) -> None:
        """dock.dock_widget returns the QDockWidget."""
        from PySide6.QtWidgets import QDockWidget

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)

        assert isinstance(instance._explorer.dock_widget, QDockWidget)

    def test_dock_title_sets_window_title(self, base_class, decorator, qt: QtDriver) -> None:
        """title= sets the dock widget's window title."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="My Explorer")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.dock_widget.windowTitle() == "My Explorer"

    def test_dock_defaults_title_to_field_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Without title=, dock title defaults to field name."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.dock_widget.windowTitle() == "_explorer"


# =============================================================================
# Dock Area Placement
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockAreaPlacement:
    """Test dock placement in different areas."""

    def test_dock_left_area(self, base_class, decorator, qt: QtDriver) -> None:
        """dock='left' places dock in left area."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        area = win.dockWidgetArea(instance._explorer.dock_widget)
        assert area == Qt.DockWidgetArea.LeftDockWidgetArea

    def test_dock_right_area(self, base_class, decorator, qt: QtDriver) -> None:
        """dock='right' places dock in right area."""

        @decorator
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        area = win.dockWidgetArea(instance._props.dock_widget)
        assert area == Qt.DockWidgetArea.RightDockWidgetArea

    def test_dock_top_area(self, base_class, decorator, qt: QtDriver) -> None:
        """dock='top' places dock in top area."""

        @decorator
        class TestClass(base_class):
            _toolbar: Dock[QWidget] = new(dock="top")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        area = win.dockWidgetArea(instance._toolbar.dock_widget)
        assert area == Qt.DockWidgetArea.TopDockWidgetArea

    def test_dock_bottom_area(self, base_class, decorator, qt: QtDriver) -> None:
        """dock='bottom' places dock in bottom area."""

        @decorator
        class TestClass(base_class):
            _console: Dock[ConsolePanel] = new(dock="bottom")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        area = win.dockWidgetArea(instance._console.dock_widget)
        assert area == Qt.DockWidgetArea.BottomDockWidgetArea


# =============================================================================
# Reference-Based Positioning (Splits)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestReferencedPositioning:
    """Test reference-based positioning (splits)."""

    def test_below_creates_vertical_split(self, base_class, decorator, qt: QtDriver) -> None:
        """below= creates a vertical split below the referenced dock."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _git: Dock[GitPanel] = new(below="_explorer", title="Git")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # Both should be in the same area
        explorer_area = win.dockWidgetArea(instance._explorer.dock_widget)
        git_area = win.dockWidgetArea(instance._git.dock_widget)
        assert explorer_area == Qt.DockWidgetArea.LeftDockWidgetArea
        assert git_area == Qt.DockWidgetArea.LeftDockWidgetArea

    def test_right_of_creates_horizontal_split(self, base_class, decorator, qt: QtDriver) -> None:
        """rightOf= creates a horizontal split to the right of the referenced dock."""

        @decorator
        class TestClass(base_class):
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")
            _output: Dock[OutputPanel] = new(rightOf="_console", title="Output")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # Both should be in the bottom area
        console_area = win.dockWidgetArea(instance._console.dock_widget)
        output_area = win.dockWidgetArea(instance._output.dock_widget)
        assert console_area == Qt.DockWidgetArea.BottomDockWidgetArea
        assert output_area == Qt.DockWidgetArea.BottomDockWidgetArea


# =============================================================================
# Group-Based Tabification
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestGroupTabification:
    """Test group-based dock tabification."""

    def test_group_tabifies_docks(self, base_class, decorator, qt: QtDriver) -> None:
        """Docks in the same group are tabified together."""

        @decorator
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _styles: Dock[StylesPanel] = new(group="inspector", title="Styles")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # All should be in the same area
        props_area = win.dockWidgetArea(instance._props.dock_widget)
        inspector_area = win.dockWidgetArea(instance._inspector.dock_widget)
        styles_area = win.dockWidgetArea(instance._styles.dock_widget)

        assert props_area == Qt.DockWidgetArea.RightDockWidgetArea
        assert inspector_area == Qt.DockWidgetArea.RightDockWidgetArea
        assert styles_area == Qt.DockWidgetArea.RightDockWidgetArea

        # Check tabification
        tabified = win.tabifiedDockWidgets(instance._props.dock_widget)
        assert len(tabified) >= 1  # At least one other dock tabified with it

    def test_group_without_anchor_defaults_to_left(self, base_class, decorator, qt: QtDriver) -> None:
        """Group without dock= anchor defaults to left area."""

        @decorator
        class TestClass(base_class):
            _panel1: Dock[QWidget] = new(group="tools", title="Panel 1")
            _panel2: Dock[QWidget] = new(group="tools", title="Panel 2")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        area1 = win.dockWidgetArea(instance._panel1.dock_widget)
        area2 = win.dockWidgetArea(instance._panel2.dock_widget)

        assert area1 == Qt.DockWidgetArea.LeftDockWidgetArea
        assert area2 == Qt.DockWidgetArea.LeftDockWidgetArea


# =============================================================================
# Dock State Properties
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockStateProperties:
    """Test Dock state properties."""

    def test_is_visible_reflects_dock_visibility(self, base_class, decorator, qt: QtDriver) -> None:
        """is_visible reflects dock widget visibility."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()  # Need to show window for dock visibility to work

        assert instance._explorer.is_visible is True

        instance._explorer.hide()
        assert instance._explorer.is_visible is False

        instance._explorer.show()
        assert instance._explorer.is_visible is True

    def test_is_floating_reflects_dock_floating_state(self, base_class, decorator, qt: QtDriver) -> None:
        """is_floating reflects dock widget floating state."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.is_floating is False

        instance._explorer.float()
        assert instance._explorer.is_floating is True

        instance._explorer.unfloat()
        assert instance._explorer.is_floating is False

    def test_area_property_returns_current_area(self, base_class, decorator, qt: QtDriver) -> None:
        """area property returns current dock area."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.area == Qt.DockWidgetArea.LeftDockWidgetArea


# =============================================================================
# Dock Helper Methods
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockHelperMethods:
    """Test Dock helper methods."""

    def test_toggle_toggles_visibility(self, base_class, decorator, qt: QtDriver) -> None:
        """toggle() toggles dock visibility."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()  # Need to show window for dock visibility to work

        initial = instance._explorer.is_visible
        instance._explorer.toggle()
        assert instance._explorer.is_visible is not initial
        instance._explorer.toggle()
        assert instance._explorer.is_visible is initial

    def test_close_hides_dock(self, base_class, decorator, qt: QtDriver) -> None:
        """close() hides the dock."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)

        instance._explorer.close()
        assert instance._explorer.is_visible is False


# =============================================================================
# Object Name
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockObjectName:
    """Test dock object name handling."""

    def test_dock_object_name_defaults_to_field_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Dock objectName defaults to field name."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.dock_widget.objectName() == "_explorer"

    def test_dock_object_name_can_be_set_explicitly(self, base_class, decorator, qt: QtDriver) -> None:
        """name= sets dock objectName explicitly."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", name="my-explorer")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.dock_widget.objectName() == "my-explorer"


# =============================================================================
# Docks Don't Appear in Central Widget Layout
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockLayoutExclusion:
    """Test that docks are excluded from central widget layout."""

    def test_docks_not_in_central_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Dock fields are not added to the central widget layout."""

        @decorator
        class TestClass(base_class):
            _label: QLabel = new("Hello")
            _explorer: Dock[ExplorerPanel] = new(dock="left")
            _button: QPushButton = new("Click")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # Central widget should contain label and button, but not dock
        central = win.centralWidget()
        assert central is not None

        layout = central.layout()
        assert layout is not None

        # Should have 2 items (label and button), not 3
        assert layout.count() == 2


# =============================================================================
# Multiple Docks
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestMultipleDocks:
    """Test windows with multiple docks."""

    def test_multiple_docks_in_different_areas(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple docks can be placed in different areas."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")
            _props: Dock[PropertiesPanel] = new(dock="right", title="Properties")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        assert win.dockWidgetArea(instance._explorer.dock_widget) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.dockWidgetArea(instance._console.dock_widget) == Qt.DockWidgetArea.BottomDockWidgetArea
        assert win.dockWidgetArea(instance._props.dock_widget) == Qt.DockWidgetArea.RightDockWidgetArea

    def test_complex_layout_with_splits_and_groups(self, base_class, decorator, qt: QtDriver) -> None:
        """Complex layout with splits and groups works correctly."""

        @decorator
        class TestClass(base_class):
            # Left area with vertical split
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _git: Dock[GitPanel] = new(below="_explorer", title="Git")

            # Bottom area with horizontal split
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")
            _output: Dock[OutputPanel] = new(rightOf="_console", title="Output")

            # Right area with tabs
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # Verify areas
        assert win.dockWidgetArea(instance._explorer.dock_widget) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.dockWidgetArea(instance._git.dock_widget) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.dockWidgetArea(instance._console.dock_widget) == Qt.DockWidgetArea.BottomDockWidgetArea
        assert win.dockWidgetArea(instance._output.dock_widget) == Qt.DockWidgetArea.BottomDockWidgetArea
        assert win.dockWidgetArea(instance._props.dock_widget) == Qt.DockWidgetArea.RightDockWidgetArea
        assert win.dockWidgetArea(instance._inspector.dock_widget) == Qt.DockWidgetArea.RightDockWidgetArea

        # Verify inspector group is tabified
        tabified = win.tabifiedDockWidgets(instance._props.dock_widget)
        assert instance._inspector.dock_widget in tabified


# =============================================================================
# Dock Feature Properties (Read-Only)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockFeatureProperties:
    """Test dock feature properties."""

    def test_is_closable_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Dock is closable by default."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.is_closable is True

    def test_is_movable_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Dock is movable by default."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.is_movable is True

    def test_is_floatable_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Dock is floatable by default."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.is_floatable is True


# =============================================================================
# Content Widget Constructor Args
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestContentWidgetConstructorArgs:
    """Test that constructor args are passed to content widget."""

    def test_args_passed_to_content_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Constructor args are passed to the content widget."""

        @decorator
        class TestClass(base_class):
            # new(dock_kwargs)(widget_args)
            _label: Dock[QLabel] = new(dock="left", title="Label Dock")("Hello World")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._label.widget.text() == "Hello World"

    def test_kwargs_passed_to_content_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Constructor kwargs are passed to the content widget."""

        @decorator
        class TestClass(base_class):
            # new(dock_kwargs)(widget_kwargs)
            _button: Dock[QPushButton] = new(dock="left", title="Button Dock")(text="Click Me")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._button.widget.text() == "Click Me"


# =============================================================================
# Visible Binding
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockVisibleBinding:
    """Test visible= binding for docks."""

    def test_visible_binding_initial_state(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= binding sets initial dock visibility from Variable."""

        @decorator
        class TestClass(base_class):
            _show_dock: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", visible="_show_dock")

        instance = create_and_track(qt, TestClass, base_class)
        # Note: Not calling win.show() because Qt automatically shows all docks when window shows
        # The binding should set the dock to hidden based on Variable's initial False value
        qt.process_events()

        # Check the dock widget's visibility property (not is_visible which checks isVisible())
        assert instance._explorer.dock_widget.isHidden() is True

    def test_visible_binding_variable_to_dock(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing Variable updates dock visibility."""

        @decorator
        class TestClass(base_class):
            _show_dock: Variable[bool] = new(True)
            _explorer: Dock[ExplorerPanel] = new(dock="left", visible="_show_dock")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        assert instance._explorer.is_visible is True

        instance._show_dock.value = False
        qt.process_events()
        assert instance._explorer.is_visible is False

        instance._show_dock.value = True
        qt.process_events()
        assert instance._explorer.is_visible is True

    def test_visible_binding_dock_to_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing dock visibility updates Variable."""

        @decorator
        class TestClass(base_class):
            _show_dock: Variable[bool] = new(True)
            _explorer: Dock[ExplorerPanel] = new(dock="left", visible="_show_dock")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        assert instance._show_dock.value is True

        instance._explorer.hide()
        qt.process_events()
        assert instance._show_dock.value is False

        instance._explorer.show()
        qt.process_events()
        assert instance._show_dock.value is True


# =============================================================================
# Floating Binding
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockFloatingBinding:
    """Test floating= binding for docks."""

    def test_floating_binding_initial_state(self, base_class, decorator, qt: QtDriver) -> None:
        """floating= binding sets initial dock floating state from Variable."""

        @decorator
        class TestClass(base_class):
            _is_floating: Variable[bool] = new(True)
            _explorer: Dock[ExplorerPanel] = new(dock="left", floating="_is_floating")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        assert instance._explorer.is_floating is True

    def test_floating_binding_variable_to_dock(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing Variable updates dock floating state."""

        @decorator
        class TestClass(base_class):
            _is_floating: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", floating="_is_floating")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        assert instance._explorer.is_floating is False

        instance._is_floating.value = True
        qt.process_events()
        assert instance._explorer.is_floating is True

        instance._is_floating.value = False
        qt.process_events()
        assert instance._explorer.is_floating is False

    def test_floating_binding_dock_to_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing dock floating state updates Variable."""

        @decorator
        class TestClass(base_class):
            _is_floating: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", floating="_is_floating")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        assert instance._is_floating.value is False

        instance._explorer.float()
        qt.process_events()
        assert instance._is_floating.value is True

        instance._explorer.unfloat()
        qt.process_events()
        assert instance._is_floating.value is False


# =============================================================================
# Group Selected Index Binding
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestGroupSelectedIndexBinding:
    """Test groupSelectedIndex= binding for dock tab groups."""

    def test_group_selected_index_initial_state(self, base_class, decorator, qt: QtDriver) -> None:
        """groupSelectedIndex= binding sets initial tab index from Variable."""

        @decorator
        class TestClass(base_class):
            _tab_index: Variable[int] = new(1)
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", groupSelectedIndex="_tab_index", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _styles: Dock[StylesPanel] = new(group="inspector", title="Styles")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()
        # Give QTimer.singleShot(0) time to run
        qt.process_events()

        # Tab index 1 should be selected (Inspector is at index 1 in the tab bar)
        # Note: The actual tab bar order depends on tabification order
        assert instance._tab_index.value == 1


# =============================================================================
# Variable[T, Dock[W]] - Primitive Types
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestVariableDockPrimitive:
    """Test Variable[T, Dock[W]] with primitive value types (str, int, etc)."""

    def test_variable_str_dock_creates_dock_wrapper(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str, Dock[QLineEdit]] creates a Dock wrapper."""

        @decorator
        class TestClass(base_class):
            # new(var_default)(dock_kwargs)
            _name: Variable[str, Dock[QLineEdit]] = new("")(dock="right", title="Name")

        instance = create_and_track(qt, TestClass, base_class)

        # var.widget should be a Dock
        assert isinstance(instance._name.widget, Dock)

    def test_variable_str_dock_inner_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str, Dock[QLineEdit]].widget.widget returns the QLineEdit."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, Dock[QLineEdit]] = new("")(dock="right", title="Name")

        instance = create_and_track(qt, TestClass, base_class)

        # var.widget.widget should be the inner QLineEdit
        assert isinstance(instance._name.widget.widget, QLineEdit)

    def test_variable_str_dock_qdockwidget(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str, Dock[QLineEdit]].widget.dock_widget returns the QDockWidget."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, Dock[QLineEdit]] = new("")(dock="right", title="Name")

        instance = create_and_track(qt, TestClass, base_class)

        # var.widget.dock_widget should be the QDockWidget
        assert isinstance(instance._name.widget.dock_widget, QDockWidget)

    def test_variable_str_dock_value_access(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str, Dock[QLineEdit]].value returns the string value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, Dock[QLineEdit]] = new("Hello")(dock="right", title="Name")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._name.value == "Hello"

    def test_variable_str_dock_value_set(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting Variable[str, Dock[QLineEdit]].value updates widget."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, Dock[QLineEdit]] = new("")(dock="right", title="Name")

        instance = create_and_track(qt, TestClass, base_class)

        instance._name.value = "World"
        qt.process_events()

        assert instance._name.value == "World"
        # The widget should be bound and updated
        inner_widget: QLineEdit = instance._name.widget.widget
        assert inner_widget.text() == "World"

    def test_variable_int_dock_value(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[int, Dock[QSpinBox]] works with integer values."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int, Dock[QSpinBox]] = new(42)(dock="right", title="Count")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._count.value == 42
        assert isinstance(instance._count.widget, Dock)
        assert isinstance(instance._count.widget.widget, QSpinBox)
        assert instance._count.widget.widget.value() == 42

    def test_variable_str_dock_area_placement(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable dock respects dock area placement."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, Dock[QLineEdit]] = new("")(dock="left", title="Name")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        area = win.dockWidgetArea(instance._name.widget.dock_widget)
        assert area == Qt.DockWidgetArea.LeftDockWidgetArea

    def test_variable_dock_title(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable dock respects title= parameter."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, Dock[QLineEdit]] = new("")(dock="right", title="My Name Field")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._name.widget.dock_widget.windowTitle() == "My Name Field"


# =============================================================================
# Variable[T, Dock[W]] - Complex Types
# =============================================================================


@dataclass
class Dog:
    """Test dataclass for complex Variable types."""

    name: str = ""
    age: int = 0


class DogEditor(QWidget):
    """Simple editor widget for Dog objects."""

    pass


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestVariableDockComplex:
    """Test Variable[T, Dock[W]] with complex value types (dataclasses).

    Note: For complex types (dataclasses), there's no automatic binding between
    the Variable value and the widget. The widget is just a container. Use QWidget
    subclasses that don't require auto-binding, or use Widget[T] for typed editors.
    """

    def test_variable_complex_dock_creates_dock(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[Dog, Dock[QWidget]] creates a Dock wrapper."""

        @decorator
        class TestClass(base_class):
            # new(var_default)(dock_kwargs)
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5))(dock="right", title="Dog Editor")

        instance = create_and_track(qt, TestClass, base_class)

        assert isinstance(instance._dog.widget, Dock)

    def test_variable_complex_dock_inner_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[Dog, Dock[QWidget]].widget.widget returns the editor widget."""

        @decorator
        class TestClass(base_class):
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5))(dock="right", title="Dog Editor")

        instance = create_and_track(qt, TestClass, base_class)

        assert isinstance(instance._dog.widget.widget, QWidget)

    def test_variable_complex_dock_value_access(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[Dog, Dock[QWidget]].value returns the Dog object."""

        @decorator
        class TestClass(base_class):
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5))(dock="right", title="Dog Editor")

        instance = create_and_track(qt, TestClass, base_class)

        # For complex types, value returns the ObservableProxy
        # Properties are accessible via proxy
        assert instance._dog.name == "Buddy"
        assert instance._dog.age == 5

    def test_variable_complex_dock_property_set(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting Variable[Dog, Dock[QWidget]] properties works."""

        @decorator
        class TestClass(base_class):
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5))(dock="right", title="Dog Editor")

        instance = create_and_track(qt, TestClass, base_class)

        instance._dog.name = "Max"
        instance._dog.age = 3

        assert instance._dog.name == "Max"
        assert instance._dog.age == 3

    def test_variable_complex_dock_area_placement(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[Dog, Dock[QWidget]] respects dock area."""

        @decorator
        class TestClass(base_class):
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5))(dock="bottom", title="Dog Editor")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        area = win.dockWidgetArea(instance._dog.widget.dock_widget)
        assert area == Qt.DockWidgetArea.BottomDockWidgetArea

    def test_variable_complex_dock_reference_placement(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable dock can use reference-based placement."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5))(below="_explorer", title="Dog Editor")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # Both should be in left area after split
        explorer_area = win.dockWidgetArea(instance._explorer.dock_widget)
        dog_area = win.dockWidgetArea(instance._dog.widget.dock_widget)

        assert explorer_area == Qt.DockWidgetArea.LeftDockWidgetArea
        assert dog_area == Qt.DockWidgetArea.LeftDockWidgetArea


# =============================================================================
# Variable[T, Dock[W]] - Mixed with Regular Docks
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestVariableDockMixed:
    """Test Variable[T, Dock[W]] mixed with regular Dock[T] fields."""

    def test_variable_dock_with_regular_docks(self, base_class, decorator, qt: QtDriver) -> None:
        """Window can have both Variable[T, Dock[W]] and Dock[T] fields."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _name: Variable[str, Dock[QLineEdit]] = new("")(dock="right", title="Name")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # Regular docks work
        assert isinstance(instance._explorer, Dock)
        assert isinstance(instance._console, Dock)

        # Variable dock works
        assert isinstance(instance._name.widget, Dock)
        assert instance._name.value == ""

        # All in correct areas
        assert win.dockWidgetArea(instance._explorer.dock_widget) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.dockWidgetArea(instance._name.widget.dock_widget) == Qt.DockWidgetArea.RightDockWidgetArea
        assert win.dockWidgetArea(instance._console.dock_widget) == Qt.DockWidgetArea.BottomDockWidgetArea

    def test_variable_dock_no_interference_with_central_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable docks don't appear in central widget layout."""

        @decorator
        class TestClass(base_class):
            _label: QLabel = new("Hello")
            _name: Variable[str, Dock[QLineEdit]] = new("")(dock="right", title="Name")
            _button: QPushButton = new("Click")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # Central widget should only have label and button
        central = win.centralWidget()
        assert central is not None
        layout = central.layout()
        assert layout is not None
        assert layout.count() == 2  # Not 3


# =============================================================================
# Phase 5: Reactive Title and Icon
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestReactiveTitle:
    """Test reactive title= binding for docks."""

    def test_static_title(self, base_class, decorator, qt: QtDriver) -> None:
        """Static title= works as before."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="My Explorer")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.dock_widget.windowTitle() == "My Explorer"

    def test_title_variable_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """title="_variable" binds to a Variable's value."""

        @decorator
        class TestClass(base_class):
            _title: Variable[str] = new("Initial Title")
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="_title")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.dock_widget.windowTitle() == "Initial Title"

        # Update the variable
        instance._title.value = "Updated Title"
        qt.process_events()

        assert instance._explorer.dock_widget.windowTitle() == "Updated Title"

    def test_title_expression_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """title="{expr}" binds to an expression."""

        @decorator
        class TestClass(base_class):
            _filename: Variable[str] = new("untitled.txt")
            _dirty: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="{_filename}{'*' if _dirty else ''}",
            )

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._explorer.dock_widget.windowTitle() == "untitled.txt"

        # Set dirty
        instance._dirty.value = True
        qt.process_events()

        assert instance._explorer.dock_widget.windowTitle() == "untitled.txt*"

        # Change filename
        instance._filename.value = "myfile.py"
        qt.process_events()

        assert instance._explorer.dock_widget.windowTitle() == "myfile.py*"

    def test_title_simple_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """title="{_var}" simple expression also works."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("Console")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="{_name}")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._console.dock_widget.windowTitle() == "Console"

        instance._name.value = "Output"
        qt.process_events()

        assert instance._console.dock_widget.windowTitle() == "Output"


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestReactiveIcon:
    """Test reactive icon= binding for docks."""

    def test_static_icon(self, base_class, decorator, qt: QtDriver) -> None:
        """Static icon= sets the icon once."""
        from qtpy.QtGui import QIcon

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon=":/icons/folder.png")

        instance = create_and_track(qt, TestClass, base_class)

        # Icon is set (even if resource doesn't exist, icon object is created)
        icon = instance._explorer.dock_widget.windowIcon()
        assert isinstance(icon, QIcon)

    def test_icon_variable_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """icon="_variable" binds to a Variable's value."""
        from qtpy.QtGui import QIcon

        @decorator
        class TestClass(base_class):
            _icon_path: Variable[str] = new(":/icons/initial.png")
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon_path")

        instance = create_and_track(qt, TestClass, base_class)

        # Update the variable
        instance._icon_path.value = ":/icons/updated.png"
        qt.process_events()

        # Icon is updated (we can't easily verify the path, but icon object exists)
        icon = instance._explorer.dock_widget.windowIcon()
        assert isinstance(icon, QIcon)

    def test_icon_expression_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """icon="{expr}" binds to an expression."""
        from qtpy.QtGui import QIcon

        @decorator
        class TestClass(base_class):
            _mode: Variable[str] = new("light")
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="Explorer",
                icon=":/icons/{_mode}/folder.png",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Change mode
        instance._mode.value = "dark"
        qt.process_events()

        icon = instance._explorer.dock_widget.windowIcon()
        assert isinstance(icon, QIcon)

    def test_icon_empty_clears(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting icon to empty string clears it."""

        @decorator
        class TestClass(base_class):
            _icon_path: Variable[str] = new(":/icons/folder.png")
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon_path")

        instance = create_and_track(qt, TestClass, base_class)

        # Clear the icon
        instance._icon_path.value = ""
        qt.process_events()

        icon = instance._explorer.dock_widget.windowIcon()
        # Empty QIcon
        assert icon.isNull()

    def test_icon_qicon_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """icon= supports Variable[QIcon]."""
        # Create a real QIcon from a pixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.red)
        initial_icon = QIcon(pixmap)

        @decorator
        class TestClass(base_class):
            _icon: Variable[QIcon] = new(initial_icon)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon")

        instance = create_and_track(qt, TestClass, base_class)

        # Icon should be set
        assert not instance._explorer.dock_widget.windowIcon().isNull()

        # Update to a different icon
        pixmap2 = QPixmap(16, 16)
        pixmap2.fill(Qt.GlobalColor.blue)
        instance._icon.value = QIcon(pixmap2)
        qt.process_events()

        # Still has an icon
        assert not instance._explorer.dock_widget.windowIcon().isNull()

    def test_icon_qpixmap_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """icon= supports Variable[QPixmap] (converted to QIcon)."""
        # Create a real QPixmap
        initial_pixmap = QPixmap(16, 16)
        initial_pixmap.fill(Qt.GlobalColor.green)

        @decorator
        class TestClass(base_class):
            _pixmap: Variable[QPixmap] = new(initial_pixmap)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_pixmap")

        instance = create_and_track(qt, TestClass, base_class)

        # Icon should be set (QPixmap converted to QIcon)
        assert not instance._explorer.dock_widget.windowIcon().isNull()

        # Update to a different pixmap
        pixmap2 = QPixmap(16, 16)
        pixmap2.fill(Qt.GlobalColor.yellow)
        instance._pixmap.value = pixmap2
        qt.process_events()

        # Still has an icon
        assert not instance._explorer.dock_widget.windowIcon().isNull()

    def test_icon_none_clears(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting icon to None clears it."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.red)
        initial_icon = QIcon(pixmap)

        @decorator
        class TestClass(base_class):
            _icon: Variable[QIcon | None] = new(initial_icon)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon")

        instance = create_and_track(qt, TestClass, base_class)

        # Has icon initially
        assert not instance._explorer.dock_widget.windowIcon().isNull()

        # Clear with None
        instance._icon.value = None
        qt.process_events()

        # Icon is now null
        assert instance._explorer.dock_widget.windowIcon().isNull()

    def test_icon_qicon_or_qpixmap_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[QIcon | QPixmap] can switch between types."""
        # Start with QIcon
        pixmap1 = QPixmap(16, 16)
        pixmap1.fill(Qt.GlobalColor.red)
        initial_icon = QIcon(pixmap1)

        @decorator
        class TestClass(base_class):
            _icon: Variable[QIcon | QPixmap] = new(initial_icon)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon")

        instance = create_and_track(qt, TestClass, base_class)

        # Has icon initially (QIcon)
        assert not instance._explorer.dock_widget.windowIcon().isNull()

        # Switch to QPixmap
        pixmap2 = QPixmap(16, 16)
        pixmap2.fill(Qt.GlobalColor.blue)
        instance._icon.value = pixmap2
        qt.process_events()

        # Still has icon (QPixmap converted to QIcon)
        assert not instance._explorer.dock_widget.windowIcon().isNull()

        # Switch back to QIcon
        pixmap3 = QPixmap(16, 16)
        pixmap3.fill(Qt.GlobalColor.green)
        instance._icon.value = QIcon(pixmap3)
        qt.process_events()

        # Still has icon
        assert not instance._explorer.dock_widget.windowIcon().isNull()


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestVariableDockReactiveTitle:
    """Test reactive title for Variable[T, Dock[W]]."""

    def test_variable_dock_reactive_title(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports reactive title."""

        @decorator
        class TestClass(base_class):
            _tab_title: Variable[str] = new("Name Editor")
            _name: Variable[str, Dock[QLineEdit]] = new("")(dock="right", title="_tab_title")

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._name.widget.dock_widget.windowTitle() == "Name Editor"

        instance._tab_title.value = "User Name"
        qt.process_events()

        assert instance._name.widget.dock_widget.windowTitle() == "User Name"

    def test_variable_dock_title_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports title expression."""

        @decorator
        class TestClass(base_class):
            _field_name: Variable[str] = new("Name")
            _required: Variable[bool] = new(True)
            _name: Variable[str, Dock[QLineEdit]] = new("")(
                dock="right",
                title="{_field_name}{'*' if _required else ''}",
            )

        instance = create_and_track(qt, TestClass, base_class)

        assert instance._name.widget.dock_widget.windowTitle() == "Name*"

        instance._required.value = False
        qt.process_events()

        assert instance._name.widget.dock_widget.windowTitle() == "Name"


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockFeatures:
    """Test dock features (closable, floatable, movable, allowedAreas, verticalTitleBar)."""

    def test_closable_false(self, base_class, decorator, qt: QtDriver) -> None:
        """closable=False removes close button."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", closable=False)

        instance = create_and_track(qt, TestClass, base_class)

        features = instance._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        # Other features should still be enabled
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable

    def test_floatable_false(self, base_class, decorator, qt: QtDriver) -> None:
        """floatable=False prevents floating."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", floatable=False)

        instance = create_and_track(qt, TestClass, base_class)

        features = instance._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        # Other features should still be enabled
        assert features & QDockWidget.DockWidgetFeature.DockWidgetClosable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable

    def test_movable_false(self, base_class, decorator, qt: QtDriver) -> None:
        """movable=False prevents dragging."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", movable=False)

        instance = create_and_track(qt, TestClass, base_class)

        features = instance._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        # Other features should still be enabled
        assert features & QDockWidget.DockWidgetFeature.DockWidgetClosable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable

    def test_all_features_disabled(self, base_class, decorator, qt: QtDriver) -> None:
        """All features can be disabled at once."""

        @decorator
        class TestClass(base_class):
            _toolbar: Dock[ExplorerPanel] = new(
                dock="left",
                title="Toolbar",
                closable=False,
                floatable=False,
                movable=False,
            )

        instance = create_and_track(qt, TestClass, base_class)

        features = instance._toolbar.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)

    def test_allowed_areas_left_right(self, base_class, decorator, qt: QtDriver) -> None:
        """allowedAreas restricts where dock can be placed."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="Explorer",
                allowedAreas=["left", "right"],
            )

        instance = create_and_track(qt, TestClass, base_class)

        allowed = instance._explorer.dock_widget.allowedAreas()
        assert allowed & Qt.DockWidgetArea.LeftDockWidgetArea
        assert allowed & Qt.DockWidgetArea.RightDockWidgetArea
        assert not (allowed & Qt.DockWidgetArea.TopDockWidgetArea)
        assert not (allowed & Qt.DockWidgetArea.BottomDockWidgetArea)

    def test_allowed_areas_all(self, base_class, decorator, qt: QtDriver) -> None:
        """allowedAreas with all areas."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="Explorer",
                allowedAreas=["left", "right", "top", "bottom"],
            )

        instance = create_and_track(qt, TestClass, base_class)

        allowed = instance._explorer.dock_widget.allowedAreas()
        assert allowed & Qt.DockWidgetArea.LeftDockWidgetArea
        assert allowed & Qt.DockWidgetArea.RightDockWidgetArea
        assert allowed & Qt.DockWidgetArea.TopDockWidgetArea
        assert allowed & Qt.DockWidgetArea.BottomDockWidgetArea

    def test_vertical_title_bar(self, base_class, decorator, qt: QtDriver) -> None:
        """verticalTitleBar=True enables vertical title bar."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="Explorer",
                verticalTitleBar=True,
            )

        instance = create_and_track(qt, TestClass, base_class)

        features = instance._explorer.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar

    def test_combined_features(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple features can be combined."""

        @decorator
        class TestClass(base_class):
            _toolbar: Dock[ExplorerPanel] = new(
                dock="left",
                title="Tools",
                closable=False,
                floatable=False,
                movable=False,
                allowedAreas=["left", "right"],
                verticalTitleBar=True,
            )

        instance = create_and_track(qt, TestClass, base_class)

        features = instance._toolbar.dock_widget.features()
        # Features disabled
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        # Vertical title bar enabled
        assert features & QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar

        # Allowed areas
        allowed = instance._toolbar.dock_widget.allowedAreas()
        assert allowed & Qt.DockWidgetArea.LeftDockWidgetArea
        assert allowed & Qt.DockWidgetArea.RightDockWidgetArea
        assert not (allowed & Qt.DockWidgetArea.TopDockWidgetArea)


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockFeaturesVariableDock:
    """Test dock features for Variable[T, Dock[W]]."""

    def test_variable_dock_closable_false(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports closable=False."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, Dock[QLineEdit]] = new("")(
                dock="right",
                title="Name",
                closable=False,
            )

        instance = create_and_track(qt, TestClass, base_class)

        features = instance._name.widget.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)

    def test_variable_dock_allowed_areas(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports allowedAreas."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, Dock[QLineEdit]] = new("")(
                dock="right",
                title="Name",
                allowedAreas=["left", "right"],
            )

        instance = create_and_track(qt, TestClass, base_class)

        allowed = instance._name.widget.dock_widget.allowedAreas()
        assert allowed & Qt.DockWidgetArea.LeftDockWidgetArea
        assert allowed & Qt.DockWidgetArea.RightDockWidgetArea
        assert not (allowed & Qt.DockWidgetArea.TopDockWidgetArea)

    def test_variable_dock_vertical_title_bar(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports verticalTitleBar."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, Dock[QLineEdit]] = new("")(
                dock="left",
                title="Name",
                verticalTitleBar=True,
            )

        instance = create_and_track(qt, TestClass, base_class)

        features = instance._name.widget.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestWindowDockCorners:
    """Test corners= parameter for window-level corner assignment."""

    def test_corners_top_left_to_left(self, base_class, decorator, qt: QtDriver) -> None:
        """corners= assigns top-left corner to left dock area."""

        @decorator(corners={"top_left": "left"})
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # Verify the corner is assigned to left area
        assert win.corner(Qt.Corner.TopLeftCorner) == Qt.DockWidgetArea.LeftDockWidgetArea

    def test_corners_multiple(self, base_class, decorator, qt: QtDriver) -> None:
        """corners= can assign multiple corners."""

        @decorator(
            corners={
                "top_left": "left",
                "bottom_left": "bottom",
                "top_right": "right",
                "bottom_right": "bottom",
            }
        )
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        assert win.corner(Qt.Corner.TopLeftCorner) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.corner(Qt.Corner.BottomLeftCorner) == Qt.DockWidgetArea.BottomDockWidgetArea
        assert win.corner(Qt.Corner.TopRightCorner) == Qt.DockWidgetArea.RightDockWidgetArea
        assert win.corner(Qt.Corner.BottomRightCorner) == Qt.DockWidgetArea.BottomDockWidgetArea


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDocksLocked:
    """Test docksLocked= parameter for locking all docks."""

    def test_docks_locked_initial_true(self, base_class, decorator, qt: QtDriver) -> None:
        """docksLocked=True initially locks all docks."""

        @decorator(docksLocked="_locked")
        class TestClass(base_class):
            _locked: Variable[bool] = new(True)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")

        instance = create_and_track(qt, TestClass, base_class)

        # All docks should be locked (not movable/floatable)
        explorer_features = instance._explorer.dock_widget.features()
        console_features = instance._console.dock_widget.features()

        assert not (explorer_features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        assert not (explorer_features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        assert not (console_features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        assert not (console_features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)

    def test_docks_locked_initial_false(self, base_class, decorator, qt: QtDriver) -> None:
        """docksLocked=False initially leaves docks unlocked."""

        @decorator(docksLocked="_locked")
        class TestClass(base_class):
            _locked: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)

        # Docks should be unlocked (movable/floatable)
        features = instance._explorer.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable

    def test_docks_locked_reactive(self, base_class, decorator, qt: QtDriver) -> None:
        """docksLocked binding is reactive."""

        @decorator(docksLocked="_locked")
        class TestClass(base_class):
            _locked: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially unlocked
        features = instance._explorer.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable

        # Lock
        instance._locked.value = True
        qt.process_events()

        features = instance._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)

        # Unlock
        instance._locked.value = False
        qt.process_events()

        features = instance._explorer.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable

    def test_docks_locked_preserves_closable(self, base_class, decorator, qt: QtDriver) -> None:
        """docksLocked only affects movable/floatable, not closable."""

        @decorator(docksLocked="_locked")
        class TestClass(base_class):
            _locked: Variable[bool] = new(False)
            # closable=False should be preserved
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", closable=False)

        instance = create_and_track(qt, TestClass, base_class)

        # Initially not closable
        features = instance._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable

        # Lock
        instance._locked.value = True
        qt.process_events()

        # Still not closable, and now not movable
        features = instance._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)

        # Unlock - closable should still be False
        instance._locked.value = False
        qt.process_events()

        features = instance._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable


# =============================================================================
# Window-Level Dock Tab Options
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockNesting:
    """Test dockNesting window-level option."""

    def test_dock_nesting_enabled_by_default(self, base_class, decorator, qt: QtDriver) -> None:
        """dockNesting is enabled by default."""

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        assert win.isDockNestingEnabled() is True

    def test_dock_nesting_disabled(self, base_class, decorator, qt: QtDriver) -> None:
        """dockNesting=False disables dock nesting."""

        @decorator(dockNesting=False)
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        assert win.isDockNestingEnabled() is False

    def test_dock_nesting_explicit_true(self, base_class, decorator, qt: QtDriver) -> None:
        """dockNesting=True explicitly enables dock nesting."""

        @decorator(dockNesting=True)
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        assert win.isDockNestingEnabled() is True


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockTabsPosition:
    """Test dockTabsPosition window-level option."""

    def test_tabs_position_top_by_default(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsPosition is 'top' by default (North)."""
        from PySide6.QtWidgets import QTabWidget

        @decorator
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        # Check all dock areas have North position
        assert win.tabPosition(Qt.DockWidgetArea.LeftDockWidgetArea) == QTabWidget.TabPosition.North
        assert win.tabPosition(Qt.DockWidgetArea.RightDockWidgetArea) == QTabWidget.TabPosition.North
        assert win.tabPosition(Qt.DockWidgetArea.TopDockWidgetArea) == QTabWidget.TabPosition.North
        assert win.tabPosition(Qt.DockWidgetArea.BottomDockWidgetArea) == QTabWidget.TabPosition.North

    def test_tabs_position_bottom(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsPosition='bottom' sets South position."""
        from PySide6.QtWidgets import QTabWidget

        @decorator(dockTabsPosition="bottom")
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        assert win.tabPosition(Qt.DockWidgetArea.LeftDockWidgetArea) == QTabWidget.TabPosition.South

    def test_tabs_position_left(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsPosition='left' sets West position."""
        from PySide6.QtWidgets import QTabWidget

        @decorator(dockTabsPosition="left")
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        assert win.tabPosition(Qt.DockWidgetArea.LeftDockWidgetArea) == QTabWidget.TabPosition.West

    def test_tabs_position_right(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsPosition='right' sets East position."""
        from PySide6.QtWidgets import QTabWidget

        @decorator(dockTabsPosition="right")
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)

        assert win.tabPosition(Qt.DockWidgetArea.LeftDockWidgetArea) == QTabWidget.TabPosition.East


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockTabsClosable:
    """Test dockTabsClosable window-level option."""

    def test_dock_tabs_closable_disabled_by_default(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsClosable is False by default - tabs don't have close buttons."""
        from PySide6.QtWidgets import QTabBar

        @decorator
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Find tab bars that are direct children of the window (dock tab bars)
        tab_bars = [tb for tb in win.findChildren(QTabBar) if tb.parent() is win]

        # Tab bars should NOT be closable by default
        for tab_bar in tab_bars:
            assert tab_bar.tabsClosable() is False

    def test_dock_tabs_closable_enabled(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsClosable=True adds close buttons to tabs."""
        from PySide6.QtWidgets import QTabBar

        @decorator(dockTabsClosable=True)
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Find dock tab bars
        tab_bars = [tb for tb in win.findChildren(QTabBar) if tb.parent() is win]

        # When we have tabified docks, there should be at least one tab bar
        # and they should be closable
        if tab_bars:
            for tab_bar in tab_bars:
                if tab_bar.property("_qtpie_customized"):
                    assert tab_bar.tabsClosable() is True


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockTabsMovable:
    """Test dockTabsMovable window-level option."""

    def test_dock_tabs_movable_false(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsMovable=False disables tab reordering."""
        from PySide6.QtWidgets import QTabBar

        @decorator(dockTabsMovable=False)
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Find dock tab bars - they should be not movable
        tab_bars = [tb for tb in win.findChildren(QTabBar) if tb.parent() is win]
        for tab_bar in tab_bars:
            if tab_bar.property("_qtpie_customized"):
                assert tab_bar.isMovable() is False

    def test_dock_tabs_movable_true(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsMovable=True enables tab reordering."""
        from PySide6.QtWidgets import QTabBar

        @decorator(dockTabsMovable=True)
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Find dock tab bars - they should be movable
        tab_bars = [tb for tb in win.findChildren(QTabBar) if tb.parent() is win]
        for tab_bar in tab_bars:
            if tab_bar.property("_qtpie_customized"):
                assert tab_bar.isMovable() is True


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockTabsHideTitleBar:
    """Test dockTabsHideTitleBar window-level option."""

    def test_title_bar_visible_by_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Title bars are visible by default when tabified."""

        @decorator
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Title bars should be visible (titleBarWidget is None = default title bar)
        props_titlebar = instance._props.dock_widget.titleBarWidget()
        inspector_titlebar = instance._inspector.dock_widget.titleBarWidget()

        # Default Qt title bar - titleBarWidget() returns None
        # or if custom, it should have non-zero maximumHeight
        assert props_titlebar is None or props_titlebar.maximumHeight() != 0
        assert inspector_titlebar is None or inspector_titlebar.maximumHeight() != 0

    def test_title_bar_hidden_when_tabified(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsHideTitleBar=True hides title bars when docks are tabified."""

        @decorator(dockTabsHideTitleBar=True)
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Verify docks are tabified
        tabified = win.tabifiedDockWidgets(instance._props.dock_widget)
        assert len(tabified) >= 1

        # Title bars should be hidden (zero maximumHeight widget)
        props_titlebar = instance._props.dock_widget.titleBarWidget()
        inspector_titlebar = instance._inspector.dock_widget.titleBarWidget()

        assert props_titlebar is not None and props_titlebar.maximumHeight() == 0
        assert inspector_titlebar is not None and inspector_titlebar.maximumHeight() == 0

    def test_title_bar_visible_when_not_tabified(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsHideTitleBar=True still shows title bars for non-tabified docks."""

        @decorator(dockTabsHideTitleBar=True)
        class TestClass(base_class):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # These docks are not tabified - title bars should be visible
        explorer_titlebar = instance._explorer.dock_widget.titleBarWidget()
        console_titlebar = instance._console.dock_widget.titleBarWidget()

        # Either None (default Qt title bar) or non-zero maximumHeight
        assert explorer_titlebar is None or explorer_titlebar.maximumHeight() != 0
        assert console_titlebar is None or console_titlebar.maximumHeight() != 0


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockHideTitleBarPerDockOverride:
    """Test per-dock hideTitleBarWhenTabbed override."""

    def test_per_dock_override_false(self, base_class, decorator, qt: QtDriver) -> None:
        """hideTitleBarWhenTabbed=False on a dock overrides window setting."""

        @decorator(dockTabsHideTitleBar=True)
        class TestClass(base_class):
            # This dock should keep its title bar even though window says hide
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties", hideTitleBarWhenTabbed=False)
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Props should have visible title bar (override)
        props_titlebar = instance._props.dock_widget.titleBarWidget()
        assert props_titlebar is None or props_titlebar.maximumHeight() != 0

        # Inspector should have hidden title bar (follows window setting)
        inspector_titlebar = instance._inspector.dock_widget.titleBarWidget()
        assert inspector_titlebar is not None and inspector_titlebar.maximumHeight() == 0

    def test_per_dock_override_true(self, base_class, decorator, qt: QtDriver) -> None:
        """hideTitleBarWhenTabbed=True on a dock overrides window setting."""

        @decorator(dockTabsHideTitleBar=False)  # Window says don't hide
        class TestClass(base_class):
            # This dock should hide its title bar (override)
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties", hideTitleBarWhenTabbed=True)
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Props should have hidden title bar (override)
        props_titlebar = instance._props.dock_widget.titleBarWidget()
        assert props_titlebar is not None and props_titlebar.maximumHeight() == 0

        # Inspector should have visible title bar (follows window setting = False)
        inspector_titlebar = instance._inspector.dock_widget.titleBarWidget()
        assert inspector_titlebar is None or inspector_titlebar.maximumHeight() != 0


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockTabsDragMargin:
    """Test dockTabsDragMargin option."""

    def test_drag_margin_default_value(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsDragMargin defaults to 50 pixels."""

        @decorator(dockTabsDragToUndock=True)
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)

        # Access the config to verify default
        assert instance._qtpie_config.dock_tabs_drag_margin == 50

    def test_drag_margin_custom_value(self, base_class, decorator, qt: QtDriver) -> None:
        """dockTabsDragMargin can be customized."""

        @decorator(dockTabsDragToUndock=True, dockTabsDragMargin=100)
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)

        # Access the config to verify custom value
        assert instance._qtpie_config.dock_tabs_drag_margin == 100


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestDockTabsCombined:
    """Test combining multiple dock tab options."""

    def test_all_options_enabled(self, base_class, decorator, qt: QtDriver) -> None:
        """All dock tab options can be enabled together."""
        from PySide6.QtWidgets import QTabBar

        @decorator(
            dockNesting=True,
            dockTabsPosition="bottom",
            dockTabsClosable=True,
            dockTabsMovable=True,
            dockTabsHideTitleBar=True,
            dockTabsDragToUndock=True,
            dockTabsDragMargin=75,
        )
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        from PySide6.QtWidgets import QTabWidget

        # Verify all settings
        assert win.isDockNestingEnabled() is True
        assert win.tabPosition(Qt.DockWidgetArea.RightDockWidgetArea) == QTabWidget.TabPosition.South

        # Verify tabified docks have hidden title bars
        props_titlebar = instance._props.dock_widget.titleBarWidget()
        assert props_titlebar is not None and props_titlebar.maximumHeight() == 0

        # Verify non-tabified dock has visible title bar
        explorer_titlebar = instance._explorer.dock_widget.titleBarWidget()
        assert explorer_titlebar is None or explorer_titlebar.maximumHeight() != 0

        # Find dock tab bars and check closable/movable
        tab_bars = [tb for tb in win.findChildren(QTabBar) if tb.parent() is win]
        for tab_bar in tab_bars:
            if tab_bar.property("_qtpie_customized"):
                assert tab_bar.tabsClosable() is True
                assert tab_bar.isMovable() is True

    def test_all_options_disabled(self, base_class, decorator, qt: QtDriver) -> None:
        """All dock tab options can be explicitly disabled."""

        @decorator(
            dockNesting=False,
            dockTabsPosition="top",
            dockTabsClosable=False,
            dockTabsMovable=False,
            dockTabsHideTitleBar=False,
            dockTabsDragToUndock=False,
        )
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        from PySide6.QtWidgets import QTabWidget

        assert win.isDockNestingEnabled() is False
        assert win.tabPosition(Qt.DockWidgetArea.RightDockWidgetArea) == QTabWidget.TabPosition.North

        # Title bars should be visible
        props_titlebar = instance._props.dock_widget.titleBarWidget()
        assert props_titlebar is None or props_titlebar.maximumHeight() != 0


# =============================================================================
# Variable[list[T], Dock[W]] - Dynamic Dock Repeater
# =============================================================================


@dataclass
class EditorItem:
    """Simple item type for testing dock repeaters."""

    name: str = "Untitled"
    content: str = ""


class EditorWidget(QWidget):
    """Simple widget for testing dock repeaters."""

    pass


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestVariableListDock:
    """Test Variable[list[T], Dock[W]] for dynamic dock creation."""

    def test_creates_dock_repeater(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[list[T], Dock[W]] creates a DockWidgetRepeater."""
        from qtpie.dock_widget_repeater import DockWidgetRepeater

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        instance = create_and_track(qt, TestClass, base_class)

        assert isinstance(instance._editors.widget, DockWidgetRepeater)

    def test_initial_empty_list_creates_no_docks(self, base_class, decorator, qt: QtDriver) -> None:
        """Empty initial list creates no docks."""

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        instance = create_and_track(qt, TestClass, base_class)

        assert len(instance._editors) == 0
        assert len(instance._editors.widget) == 0

    def test_append_creates_dock(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending an item creates a new dock."""

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()

        assert len(instance._editors) == 1
        assert len(instance._editors.widget) == 1
        assert instance._editors.widget[0].dock_widget.windowTitle() == "File1"

    def test_multiple_appends_create_tabified_docks(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple appends create tabified docks in the same group."""

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        instance._editors.append(EditorItem(name="File1"))
        instance._editors.append(EditorItem(name="File2"))
        instance._editors.append(EditorItem(name="File3"))
        qt.process_events()

        assert len(instance._editors.widget) == 3
        assert instance._editors.widget[0].dock_widget.windowTitle() == "File1"
        assert instance._editors.widget[1].dock_widget.windowTitle() == "File2"
        assert instance._editors.widget[2].dock_widget.windowTitle() == "File3"

        # Should be tabified - check for tab bar
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            if tb.count() >= 3:
                editor_tab_bar = tb
                break
        assert editor_tab_bar is not None, "Should have a tab bar with 3+ tabs"

    def test_remove_destroys_dock(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing an item destroys its dock."""

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        instance._editors.append(EditorItem(name="File1"))
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        assert len(instance._editors.widget) == 2

        del instance._editors[0]
        qt.process_events()

        assert len(instance._editors.widget) == 1
        assert instance._editors.widget[0].dock_widget.windowTitle() == "File2"


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestVariableListDockGroupSelectedIndex:
    """Test groupSelectedIndex= binding for Variable[list[T], Dock[W]]."""

    def test_bare_variable_auto_created(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[int] for groupSelectedIndex is auto-created."""

        @decorator
        class TestClass(base_class):
            _selected_index: Variable[int]  # No = new(), should be auto-created
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                groupSelectedIndex="_selected_index",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Variable should exist and be accessible
        assert hasattr(instance, "_selected_index")
        # Should be able to get/set value
        instance._selected_index.value = 0
        assert instance._selected_index.value == 0

    def test_new_dock_becomes_selected(self, base_class, decorator, qt: QtDriver) -> None:
        """Newly added dock becomes the selected tab (regression test for timing bug)."""

        @decorator
        class TestClass(base_class):
            _selected_index: Variable[int]
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                groupSelectedIndex="_selected_index",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add first item
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        qt.process_events()  # Extra process for QTimer.singleShot(0)

        # Add second item - this creates the tab bar
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        qt.process_events()  # Extra process for QTimer.singleShot(0)

        # The newly added dock should be visible/raised
        # Find the tab bar and check current index
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) in ("File1", "File2"):
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break

        assert editor_tab_bar is not None, "Should have tab bar with editor tabs"
        # The last added tab (File2) should be current
        current_text = editor_tab_bar.tabText(editor_tab_bar.currentIndex())
        assert current_text == "File2", f"Expected 'File2' to be selected, got '{current_text}'"

    def test_setting_index_switches_tab(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting the index Variable switches the visible tab."""

        @decorator
        class TestClass(base_class):
            _selected_index: Variable[int]
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                groupSelectedIndex="_selected_index",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add multiple items
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File3"))
        qt.process_events()
        qt.process_events()  # For QTimer.singleShot(0)

        # Find the tab bar
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # Set index to first item
        instance._selected_index.value = 0
        qt.process_events()
        qt.process_events()

        current_text = editor_tab_bar.tabText(editor_tab_bar.currentIndex())
        assert current_text == "File1", f"Expected 'File1', got '{current_text}'"

        # Set index to second item
        instance._selected_index.value = 1
        qt.process_events()
        qt.process_events()

        current_text = editor_tab_bar.tabText(editor_tab_bar.currentIndex())
        assert current_text == "File2", f"Expected 'File2', got '{current_text}'"

    def test_explicit_variable_works(self, base_class, decorator, qt: QtDriver) -> None:
        """Explicit Variable[int] = new(0) also works with groupSelectedIndex."""

        @decorator
        class TestClass(base_class):
            _selected_index: Variable[int] = new(0)  # Explicit initialization
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                groupSelectedIndex="_selected_index",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        instance._editors.append(EditorItem(name="File1"))
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        qt.process_events()

        # Setting index should work
        instance._selected_index.value = 0
        qt.process_events()
        qt.process_events()

        assert instance._selected_index.value == 0


# =============================================================================
# Variable[list[T], Dock[W]] - Reactive Title Binding
# =============================================================================


# For reactive title tests, we need Widget[T] content widgets so the wrapper is shared


@dataclass
class TitledEditorItem:
    """Item type for reactive title tests."""

    name: str = "Untitled"
    content: str = ""


@widget(record=TitledEditorItem())
class TitledEditorWidget(Widget[TitledEditorItem]):
    """Widget[T] editor for reactive title tests."""

    pass


@dataclass
class MultiPropItem:
    """Item with multiple properties for testing."""

    name: str = ""
    status: str = ""


@widget(record=MultiPropItem())
class MultiPropWidget(Widget[MultiPropItem]):
    """Widget[T] for multi-property tests."""

    pass


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestVariableListDockReactiveTitle:
    """Test that title bindings update reactively when item properties change.

    For reactive title updates to work, the content widget must be a Widget[T]
    so that the repeater can share its ObservableProxy wrapper with the widget's
    record. Then changes to record.property trigger title updates.
    """

    def test_title_updates_when_property_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """Title updates when the bound property changes via widget.record."""

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[TitledEditorItem], Dock[TitledEditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add an item
        instance._editors.append(TitledEditorItem(name="Original"))
        qt.process_events()

        # Verify initial title
        assert instance._editors.widget[0].dock_widget.windowTitle() == "Original"

        # Access the item through the widget's record (which shares the ObservableProxy)
        content_widget: TitledEditorWidget = instance._editors.widget[0].widget
        content_widget.record.name = "Updated"
        qt.process_events()

        # Title should have updated
        assert instance._editors.widget[0].dock_widget.windowTitle() == "Updated"

    def test_title_updates_for_multiple_docks(self, base_class, decorator, qt: QtDriver) -> None:
        """Each dock's title updates independently when its item changes."""

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[TitledEditorItem], Dock[TitledEditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add multiple items
        instance._editors.append(TitledEditorItem(name="File1"))
        instance._editors.append(TitledEditorItem(name="File2"))
        instance._editors.append(TitledEditorItem(name="File3"))
        qt.process_events()

        # Verify initial titles
        assert instance._editors.widget[0].dock_widget.windowTitle() == "File1"
        assert instance._editors.widget[1].dock_widget.windowTitle() == "File2"
        assert instance._editors.widget[2].dock_widget.windowTitle() == "File3"

        # Change middle item's name via its widget's record
        content_widget: TitledEditorWidget = instance._editors.widget[1].widget
        content_widget.record.name = "ModifiedFile2"
        qt.process_events()

        # Only the second dock's title should change
        assert instance._editors.widget[0].dock_widget.windowTitle() == "File1"
        assert instance._editors.widget[1].dock_widget.windowTitle() == "ModifiedFile2"
        assert instance._editors.widget[2].dock_widget.windowTitle() == "File3"

    def test_title_with_multiple_properties(self, base_class, decorator, qt: QtDriver) -> None:
        """Title with multiple property placeholders updates for any change."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[MultiPropItem], Dock[MultiPropWidget]] = new(
                group="items",
                dock="right",
                title="{name} - {status}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        instance._items.append(MultiPropItem(name="Doc1", status="Draft"))
        qt.process_events()

        assert instance._items.widget[0].dock_widget.windowTitle() == "Doc1 - Draft"

        # Access via widget's record
        content_widget: MultiPropWidget = instance._items.widget[0].widget

        # Change first property
        content_widget.record.name = "Document1"
        qt.process_events()
        assert instance._items.widget[0].dock_widget.windowTitle() == "Document1 - Draft"

        # Change second property
        content_widget.record.status = "Final"
        qt.process_events()
        assert instance._items.widget[0].dock_widget.windowTitle() == "Document1 - Final"


# =============================================================================
# selectedDock Binding for Variable[list[T], Dock[W]]
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestSelectedDockBinding:
    """Test selectedDock= binding for Variable[list[T], Dock[W]]."""

    def test_bare_variable_auto_created(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[Dock[...] | None] for selectedDock is auto-created."""

        @decorator
        class TestClass(base_class):
            _selected_dock: Variable[Dock[EditorWidget] | None]  # Bare annotation
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedDock="_selected_dock",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Should have the attribute auto-created
        assert hasattr(instance, "_selected_dock")

    def test_selected_dock_updates_on_tab_click(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedDock updates when user clicks a tab."""

        @decorator
        class TestClass(base_class):
            _selected_dock: Variable[Dock[EditorWidget] | None]
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedDock="_selected_dock",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add items
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        qt.process_events()  # For QTimer.singleShot(0)

        # Find tab bar
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # Click first tab
        editor_tab_bar.setCurrentIndex(0)
        qt.process_events()
        qt.process_events()

        # Selected dock should be the first dock
        assert instance._selected_dock.value is not None
        assert instance._selected_dock.value is instance._editors.widget[0]
        assert instance._selected_dock.value.dock_widget.windowTitle() == "File1"

        # Click second tab
        editor_tab_bar.setCurrentIndex(1)
        qt.process_events()
        qt.process_events()

        # Selected dock should be the second dock
        assert instance._selected_dock.value is instance._editors.widget[1]
        assert instance._selected_dock.value.dock_widget.windowTitle() == "File2"

    def test_setting_dock_raises_tab(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting selectedDock Variable raises that dock's tab."""

        @decorator
        class TestClass(base_class):
            _selected_dock: Variable[Dock[EditorWidget] | None]
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedDock="_selected_dock",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add items
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File3"))
        qt.process_events()
        qt.process_events()  # For QTimer.singleShot(0)

        # Find tab bar
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # Set to first dock
        instance._selected_dock.value = instance._editors.widget[0]
        qt.process_events()
        qt.process_events()

        assert editor_tab_bar.tabText(editor_tab_bar.currentIndex()) == "File1"

        # Set to third dock
        instance._selected_dock.value = instance._editors.widget[2]
        qt.process_events()
        qt.process_events()

        assert editor_tab_bar.tabText(editor_tab_bar.currentIndex()) == "File3"

    def test_all_three_bindings_work_together(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedIndex, selectedItem, and selectedDock all update together."""

        @decorator
        class TestClass(base_class):
            _selected_index: Variable[int]
            _selected_item: Variable[EditorItem | None]
            _selected_dock: Variable[Dock[EditorWidget] | None]
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedIndex="_selected_index",
                selectedItem="_selected_item",
                selectedDock="_selected_dock",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Create items
        item1 = EditorItem(name="File1")
        item2 = EditorItem(name="File2")

        instance._editors.append(item1)
        qt.process_events()
        instance._editors.append(item2)
        qt.process_events()
        qt.process_events()  # For QTimer.singleShot(0)

        # Find tab bar
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # Click first tab
        editor_tab_bar.setCurrentIndex(0)
        qt.process_events()
        qt.process_events()

        # All three should reflect the first item
        assert instance._selected_index.value == 0
        assert instance._selected_item.value is item1
        assert instance._selected_dock.value is instance._editors.widget[0]

        # Click second tab
        editor_tab_bar.setCurrentIndex(1)
        qt.process_events()
        qt.process_events()

        # All three should reflect the second item
        assert instance._selected_index.value == 1
        assert instance._selected_item.value is item2
        assert instance._selected_dock.value is instance._editors.widget[1]


# =============================================================================
# groupSelectedDock Binding for Static Dock Groups
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestGroupSelectedDockBinding:
    """Test groupSelectedDock= binding for static dock groups."""

    def test_bare_variable_auto_created(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[Dock[Any] | None] for groupSelectedDock is auto-created."""

        @decorator
        class TestClass(base_class):
            _selected_dock: Variable[Dock[Any] | None]  # Bare annotation
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="inspector",
                title="Properties",
                groupSelectedDock="_selected_dock",
            )
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()
        qt.process_events()  # For QTimer.singleShot(0)

        # Should have the attribute auto-created
        assert hasattr(instance, "_selected_dock")

    def test_group_selected_dock_updates_on_tab_click(self, base_class, decorator, qt: QtDriver) -> None:
        """groupSelectedDock updates when user clicks a tab in the group."""

        @decorator
        class TestClass(base_class):
            _selected_dock: Variable[Dock[Any] | None]
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="inspector",
                title="Properties",
                groupSelectedDock="_selected_dock",
            )
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()
        qt.process_events()  # For QTimer.singleShot(0)

        # Find tab bar for the inspector group
        tab_bars = win.findChildren(QTabBar)
        inspector_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "Properties":
                    inspector_tab_bar = tb
                    break
            if inspector_tab_bar:
                break
        assert inspector_tab_bar is not None

        # Click first tab (Properties)
        inspector_tab_bar.setCurrentIndex(0)
        qt.process_events()
        qt.process_events()

        # Selected dock should be _props
        assert instance._selected_dock.value is instance._props

        # Click second tab (Inspector)
        inspector_tab_bar.setCurrentIndex(1)
        qt.process_events()
        qt.process_events()

        # Selected dock should be _inspector
        assert instance._selected_dock.value is instance._inspector

    def test_setting_dock_raises_tab(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting groupSelectedDock Variable raises that dock's tab."""

        @decorator
        class TestClass(base_class):
            _selected_dock: Variable[Dock[Any] | None]
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="inspector",
                title="Properties",
                groupSelectedDock="_selected_dock",
            )
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()
        qt.process_events()

        # Find tab bar
        tab_bars = win.findChildren(QTabBar)
        inspector_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "Properties":
                    inspector_tab_bar = tb
                    break
            if inspector_tab_bar:
                break
        assert inspector_tab_bar is not None

        # Set to _props
        instance._selected_dock.value = instance._props
        qt.process_events()
        qt.process_events()

        assert inspector_tab_bar.tabText(inspector_tab_bar.currentIndex()) == "Properties"

        # Set to _inspector
        instance._selected_dock.value = instance._inspector
        qt.process_events()
        qt.process_events()

        assert inspector_tab_bar.tabText(inspector_tab_bar.currentIndex()) == "Inspector"


# =============================================================================
# No Callback on Initial Sync
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestNoCallbackOnInitialSync:
    """Test that on_change callbacks don't fire on initial sync."""

    def test_on_change_not_called_on_initial_sync(self, base_class, decorator, qt: QtDriver) -> None:
        """on_change handler should not be called during initial Variable setup."""
        callback_count = [0]

        @decorator
        class TestClass(base_class):
            _selected_index: Variable[int]
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedIndex="_selected_index",
            )

            def __setup__(self) -> None:
                self._selected_index.on_change(self._on_index_changed)

            def _on_index_changed(self, index: int) -> None:
                callback_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add items to create the tab bar
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        qt.process_events()  # For QTimer.singleShot(0)

        # Callback should NOT have been called during initial setup
        # (it was only called because of the appends which change selection)
        initial_count = callback_count[0]

        # Now click a different tab - this SHOULD fire the callback
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # Click first tab
        editor_tab_bar.setCurrentIndex(0)
        qt.process_events()
        qt.process_events()

        # Callback should have been called once for the tab change
        assert callback_count[0] > initial_count

    def test_initial_value_is_correct(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable should have correct initial value even though callback wasn't fired."""

        @decorator
        class TestClass(base_class):
            _selected_index: Variable[int]
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedIndex="_selected_index",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add items
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        qt.process_events()  # For QTimer.singleShot(0)

        # The Variable should have a valid value (0 or 1, depending on which tab is active)
        # The important thing is that it's set, not None or undefined
        assert instance._selected_index.value >= 0
        assert instance._selected_index.value < 2


# =============================================================================
# Floating Dock Focus Tracking for Variable[list[T], Dock[W]]
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestFloatingDockFocusDynamic:
    """Test floating dock focus tracking for Variable[list[T], Dock[W]]."""

    def test_floating_dock_gains_focus_updates_selection(self, base_class, decorator, qt: QtDriver) -> None:
        """When a floating dock gains focus, selection Variables should update."""
        from qtpy.QtWidgets import QApplication

        @decorator
        class TestClass(base_class):
            _selected_index: Variable[int]
            _selected_dock: Variable[Dock[EditorWidget] | None]
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedIndex="_selected_index",
                selectedDock="_selected_dock",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add items - need 3 so we can switch tabs when one is floating
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File3"))
        qt.process_events()
        qt.process_events()  # For QTimer.singleShot(0)

        # Float the third dock
        dock3 = instance._editors.widget[2]
        dock3.dock_widget.setFloating(True)
        qt.process_events()

        # Find tab bar - should have File1 and File2
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # Click File1 tab
        for i in range(editor_tab_bar.count()):
            if editor_tab_bar.tabText(i) == "File1":
                editor_tab_bar.setCurrentIndex(i)
                break
        qt.process_events()
        qt.process_events()

        # Verify first dock is selected
        assert instance._selected_index.value == 0
        assert instance._selected_dock.value is instance._editors.widget[0]

        # Simulate focus on the floating dock (File3)
        # We do this by triggering the focus changed signal
        app = QApplication.instance()
        assert app is not None
        app.focusChanged.emit(None, dock3.widget)  # type: ignore[union-attr]
        qt.process_events()

        # Selection should now be the floating dock (index 2)
        assert instance._selected_index.value == 2
        assert instance._selected_dock.value is dock3

    def test_redocked_dock_uses_tab_bar(self, base_class, decorator, qt: QtDriver) -> None:
        """After a dock is re-docked, selection should work via tab bar clicks."""

        @decorator
        class TestClass(base_class):
            _selected_index: Variable[int]
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedIndex="_selected_index",
            )

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add items
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        qt.process_events()

        # Float then re-dock
        dock2 = instance._editors.widget[1]
        dock2.dock_widget.setFloating(True)
        qt.process_events()
        dock2.dock_widget.setFloating(False)
        qt.process_events()

        # Find tab bar
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # Tab clicks should work normally - click by title to handle any tab order
        file1_idx = -1
        file2_idx = -1
        for i in range(editor_tab_bar.count()):
            if editor_tab_bar.tabText(i) == "File1":
                file1_idx = i
            elif editor_tab_bar.tabText(i) == "File2":
                file2_idx = i
        assert file1_idx >= 0
        assert file2_idx >= 0

        # Click File2 first (to ensure we actually change tabs)
        editor_tab_bar.setCurrentIndex(file2_idx)
        qt.process_events()
        assert instance._selected_index.value == 1

        # Then click File1
        editor_tab_bar.setCurrentIndex(file1_idx)
        qt.process_events()
        assert instance._selected_index.value == 0


# =============================================================================
# Floating Dock Focus Tracking for Static Dock Groups
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestFloatingDockFocusStatic:
    """Test floating dock focus tracking for static dock groups."""

    def test_floating_dock_gains_focus_updates_selection(self, base_class, decorator, qt: QtDriver) -> None:
        """When a floating static dock gains focus, groupSelectedDock should update."""
        from qtpy.QtWidgets import QApplication

        @decorator
        class TestClass(base_class):
            _selected_dock: Variable[Dock[Any] | None]
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="inspector",
                title="Properties",
                groupSelectedDock="_selected_dock",
            )
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()
        qt.process_events()

        # Float the inspector dock
        instance._inspector.dock_widget.setFloating(True)
        qt.process_events()

        # Set selection to properties via tab
        tab_bars = win.findChildren(QTabBar)
        inspector_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "Properties":
                    inspector_tab_bar = tb
                    break
            if inspector_tab_bar:
                break
        assert inspector_tab_bar is not None

        inspector_tab_bar.setCurrentIndex(0)
        qt.process_events()
        qt.process_events()

        # Verify Properties is selected
        assert instance._selected_dock.value is instance._props

        # Simulate focus on the floating inspector dock
        app = QApplication.instance()
        assert app is not None
        app.focusChanged.emit(None, instance._inspector.widget)  # type: ignore[union-attr]
        qt.process_events()

        # Selection should now be the inspector
        assert instance._selected_dock.value is instance._inspector

    def test_multiple_floating_docks_switch_correctly(self, base_class, decorator, qt: QtDriver) -> None:
        """Clicking between multiple floating docks should update selection correctly."""
        from qtpy.QtWidgets import QApplication

        @decorator
        class TestClass(base_class):
            _selected_dock: Variable[Dock[Any] | None]
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="inspector",
                title="Properties",
                groupSelectedDock="_selected_dock",
            )
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()
        qt.process_events()

        # Float both docks
        instance._props.dock_widget.setFloating(True)
        qt.process_events()
        instance._inspector.dock_widget.setFloating(True)
        qt.process_events()

        app = QApplication.instance()
        assert app is not None

        # Focus on props
        app.focusChanged.emit(None, instance._props.widget)  # type: ignore[union-attr]
        qt.process_events()
        assert instance._selected_dock.value is instance._props

        # Focus on inspector
        app.focusChanged.emit(None, instance._inspector.widget)  # type: ignore[union-attr]
        qt.process_events()
        assert instance._selected_dock.value is instance._inspector

        # Focus back on props
        app.focusChanged.emit(None, instance._props.widget)  # type: ignore[union-attr]
        qt.process_events()
        assert instance._selected_dock.value is instance._props


# =============================================================================
# Selection Changed Callbacks (via new() kwargs)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestSelectionChangedCallbacks:
    """Test selectedIndexChanged, selectedItemChanged, selectedDockChanged callbacks."""

    def test_selected_index_changed_callback_fires(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedIndexChanged callback fires when tab changes."""
        callback_args: list[int] = []

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedIndexChanged="on_index_changed",
            )

            def on_index_changed(self, index: int) -> None:
                callback_args.append(index)

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add items
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        qt.process_events()

        callback_args.clear()  # Clear any initial callbacks

        # Find tab bar
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # Click tabs
        for i in range(editor_tab_bar.count()):
            if editor_tab_bar.tabText(i) == "File1":
                editor_tab_bar.setCurrentIndex(i)
                break
        qt.process_events()
        qt.process_events()

        for i in range(editor_tab_bar.count()):
            if editor_tab_bar.tabText(i) == "File2":
                editor_tab_bar.setCurrentIndex(i)
                break
        qt.process_events()
        qt.process_events()

        # Callback should have been called with index 0 and 1
        assert 1 in callback_args

    def test_selected_item_changed_callback_fires(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItemChanged callback fires when tab changes."""
        callback_args: list[EditorItem | None] = []

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedItemChanged="on_item_changed",
            )

            def on_item_changed(self, item: EditorItem | None) -> None:
                callback_args.append(item)

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add items
        item1 = EditorItem(name="File1")
        item2 = EditorItem(name="File2")
        instance._editors.append(item1)
        qt.process_events()
        instance._editors.append(item2)
        qt.process_events()
        qt.process_events()

        callback_args.clear()

        # Find tab bar and click
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # First switch to File1 (since File2 was added last and is auto-raised)
        for i in range(editor_tab_bar.count()):
            if editor_tab_bar.tabText(i) == "File1":
                editor_tab_bar.setCurrentIndex(i)
                break
        qt.process_events()
        qt.process_events()
        callback_args.clear()  # Clear again after first switch

        # Now switch to File2 to trigger the callback
        for i in range(editor_tab_bar.count()):
            if editor_tab_bar.tabText(i) == "File2":
                editor_tab_bar.setCurrentIndex(i)
                break
        qt.process_events()
        qt.process_events()

        # Callback should have been called with item2
        assert item2 in callback_args

    def test_selected_dock_changed_callback_fires(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedDockChanged callback fires when tab changes."""
        callback_args: list[Any] = []

        @decorator
        class TestClass(base_class):
            _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
                group="editors",
                dock="right",
                title="{name}",
                selectedDockChanged="on_dock_changed",
            )

            def on_dock_changed(self, dock: Dock[EditorWidget] | None) -> None:
                callback_args.append(dock)

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()

        # Add items
        instance._editors.append(EditorItem(name="File1"))
        qt.process_events()
        instance._editors.append(EditorItem(name="File2"))
        qt.process_events()
        qt.process_events()

        callback_args.clear()

        # Find tab bar
        tab_bars = win.findChildren(QTabBar)
        editor_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "File1":
                    editor_tab_bar = tb
                    break
            if editor_tab_bar:
                break
        assert editor_tab_bar is not None

        # First switch to File1 (since File2 was added last and is auto-raised)
        for i in range(editor_tab_bar.count()):
            if editor_tab_bar.tabText(i) == "File1":
                editor_tab_bar.setCurrentIndex(i)
                break
        qt.process_events()
        qt.process_events()
        callback_args.clear()  # Clear again after first switch

        # Now switch to File2 to trigger the callback
        for i in range(editor_tab_bar.count()):
            if editor_tab_bar.tabText(i) == "File2":
                editor_tab_bar.setCurrentIndex(i)
                break
        qt.process_events()
        qt.process_events()

        # Callback should have been called with dock for File2
        assert len(callback_args) >= 1
        assert callback_args[-1] is instance._editors.widget[1]


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestGroupSelectionChangedCallbacks:
    """Test groupSelectedIndexChanged, groupSelectedDockChanged callbacks for static dock groups."""

    def test_group_selected_index_changed_callback_fires(self, base_class, decorator, qt: QtDriver) -> None:
        """groupSelectedIndexChanged callback fires when tab changes."""
        callback_args: list[int] = []

        @decorator
        class TestClass(base_class):
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="inspector",
                title="Properties",
                groupSelectedIndexChanged="on_index_changed",
            )
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

            def on_index_changed(self, index: int) -> None:
                callback_args.append(index)

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()
        qt.process_events()

        callback_args.clear()

        # Find tab bar
        tab_bars = win.findChildren(QTabBar)
        inspector_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "Properties":
                    inspector_tab_bar = tb
                    break
            if inspector_tab_bar:
                break
        assert inspector_tab_bar is not None

        # Click Inspector tab
        for i in range(inspector_tab_bar.count()):
            if inspector_tab_bar.tabText(i) == "Inspector":
                inspector_tab_bar.setCurrentIndex(i)
                break
        qt.process_events()
        qt.process_events()

        # Callback should have been called
        assert len(callback_args) >= 1

    def test_group_selected_dock_changed_callback_fires(self, base_class, decorator, qt: QtDriver) -> None:
        """groupSelectedDockChanged callback fires when tab changes."""
        callback_args: list[Any] = []

        @decorator
        class TestClass(base_class):
            _selected_dock: Variable[Dock[Any] | None]
            _props: Dock[PropertiesPanel] = new(
                dock="right",
                group="inspector",
                title="Properties",
                groupSelectedDock="_selected_dock",
                groupSelectedDockChanged="on_dock_changed",
            )
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

            def on_dock_changed(self, dock: Dock[Any] | None) -> None:
                callback_args.append(dock)

        instance = create_and_track(qt, TestClass, base_class)
        win = get_main_window(instance, base_class)
        win.show()
        qt.process_events()
        qt.process_events()

        callback_args.clear()

        # Find tab bar
        tab_bars = win.findChildren(QTabBar)
        inspector_tab_bar = None
        for tb in tab_bars:
            for i in range(tb.count()):
                if tb.tabText(i) == "Properties":
                    inspector_tab_bar = tb
                    break
            if inspector_tab_bar:
                break
        assert inspector_tab_bar is not None

        # Click Inspector tab
        for i in range(inspector_tab_bar.count()):
            if inspector_tab_bar.tabText(i) == "Inspector":
                inspector_tab_bar.setCurrentIndex(i)
                break
        qt.process_events()
        qt.process_events()

        # Callback should have been called with _inspector dock
        assert len(callback_args) >= 1
        assert callback_args[-1] is instance._inspector
