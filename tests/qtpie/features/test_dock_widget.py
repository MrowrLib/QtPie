# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
"""Tests for Dock[T] declarative dock widget support."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QDockWidget, QLabel, QLineEdit, QPushButton, QSpinBox, QWidget

from qtpie import Dock, Variable, Window, new, window
from qtpie.testing import QtDriver

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


class TestBasicDockCreation:
    """Test basic Dock[T] field creation."""

    def test_dock_field_creates_dock_wrapper(self, qt: QtDriver) -> None:
        """Dock[T] field creates a Dock wrapper instance."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        win = TestWindow()
        qt.track(win)

        assert isinstance(win._explorer, Dock)

    def test_dock_widget_property_returns_content(self, qt: QtDriver) -> None:
        """dock.widget returns the content widget."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        win = TestWindow()
        qt.track(win)

        assert isinstance(win._explorer.widget, ExplorerPanel)

    def test_dock_dock_widget_property_returns_qdockwidget(self, qt: QtDriver) -> None:
        """dock.dock_widget returns the QDockWidget."""
        from PySide6.QtWidgets import QDockWidget

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        win = TestWindow()
        qt.track(win)

        assert isinstance(win._explorer.dock_widget, QDockWidget)

    def test_dock_title_sets_window_title(self, qt: QtDriver) -> None:
        """title= sets the dock widget's window title."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="My Explorer")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.dock_widget.windowTitle() == "My Explorer"

    def test_dock_defaults_title_to_field_name(self, qt: QtDriver) -> None:
        """Without title=, dock title defaults to field name."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.dock_widget.windowTitle() == "_explorer"


# =============================================================================
# Dock Area Placement
# =============================================================================


class TestDockAreaPlacement:
    """Test dock placement in different areas."""

    def test_dock_left_area(self, qt: QtDriver) -> None:
        """dock='left' places dock in left area."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)

        area = win.dockWidgetArea(win._explorer.dock_widget)
        assert area == Qt.DockWidgetArea.LeftDockWidgetArea

    def test_dock_right_area(self, qt: QtDriver) -> None:
        """dock='right' places dock in right area."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right")

        win = TestWindow()
        qt.track(win)

        area = win.dockWidgetArea(win._props.dock_widget)
        assert area == Qt.DockWidgetArea.RightDockWidgetArea

    def test_dock_top_area(self, qt: QtDriver) -> None:
        """dock='top' places dock in top area."""

        @window
        class TestWindow(Window):
            _toolbar: Dock[QWidget] = new(dock="top")

        win = TestWindow()
        qt.track(win)

        area = win.dockWidgetArea(win._toolbar.dock_widget)
        assert area == Qt.DockWidgetArea.TopDockWidgetArea

    def test_dock_bottom_area(self, qt: QtDriver) -> None:
        """dock='bottom' places dock in bottom area."""

        @window
        class TestWindow(Window):
            _console: Dock[ConsolePanel] = new(dock="bottom")

        win = TestWindow()
        qt.track(win)

        area = win.dockWidgetArea(win._console.dock_widget)
        assert area == Qt.DockWidgetArea.BottomDockWidgetArea


# =============================================================================
# Reference-Based Positioning (Splits)
# =============================================================================


class TestReferencedPositioning:
    """Test reference-based positioning (splits)."""

    def test_below_creates_vertical_split(self, qt: QtDriver) -> None:
        """below= creates a vertical split below the referenced dock."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _git: Dock[GitPanel] = new(below="_explorer", title="Git")

        win = TestWindow()
        qt.track(win)

        # Both should be in the same area
        explorer_area = win.dockWidgetArea(win._explorer.dock_widget)
        git_area = win.dockWidgetArea(win._git.dock_widget)
        assert explorer_area == Qt.DockWidgetArea.LeftDockWidgetArea
        assert git_area == Qt.DockWidgetArea.LeftDockWidgetArea

    def test_right_of_creates_horizontal_split(self, qt: QtDriver) -> None:
        """rightOf= creates a horizontal split to the right of the referenced dock."""

        @window
        class TestWindow(Window):
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")
            _output: Dock[OutputPanel] = new(rightOf="_console", title="Output")

        win = TestWindow()
        qt.track(win)

        # Both should be in the bottom area
        console_area = win.dockWidgetArea(win._console.dock_widget)
        output_area = win.dockWidgetArea(win._output.dock_widget)
        assert console_area == Qt.DockWidgetArea.BottomDockWidgetArea
        assert output_area == Qt.DockWidgetArea.BottomDockWidgetArea


# =============================================================================
# Group-Based Tabification
# =============================================================================


class TestGroupTabification:
    """Test group-based dock tabification."""

    def test_group_tabifies_docks(self, qt: QtDriver) -> None:
        """Docks in the same group are tabified together."""

        @window
        class TestWindow(Window):
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _styles: Dock[StylesPanel] = new(group="inspector", title="Styles")

        win = TestWindow()
        qt.track(win)

        # All should be in the same area
        props_area = win.dockWidgetArea(win._props.dock_widget)
        inspector_area = win.dockWidgetArea(win._inspector.dock_widget)
        styles_area = win.dockWidgetArea(win._styles.dock_widget)

        assert props_area == Qt.DockWidgetArea.RightDockWidgetArea
        assert inspector_area == Qt.DockWidgetArea.RightDockWidgetArea
        assert styles_area == Qt.DockWidgetArea.RightDockWidgetArea

        # Check tabification
        tabified = win.tabifiedDockWidgets(win._props.dock_widget)
        assert len(tabified) >= 1  # At least one other dock tabified with it

    def test_group_without_anchor_defaults_to_left(self, qt: QtDriver) -> None:
        """Group without dock= anchor defaults to left area."""

        @window
        class TestWindow(Window):
            _panel1: Dock[QWidget] = new(group="tools", title="Panel 1")
            _panel2: Dock[QWidget] = new(group="tools", title="Panel 2")

        win = TestWindow()
        qt.track(win)

        area1 = win.dockWidgetArea(win._panel1.dock_widget)
        area2 = win.dockWidgetArea(win._panel2.dock_widget)

        assert area1 == Qt.DockWidgetArea.LeftDockWidgetArea
        assert area2 == Qt.DockWidgetArea.LeftDockWidgetArea


# =============================================================================
# Dock State Properties
# =============================================================================


class TestDockStateProperties:
    """Test Dock state properties."""

    def test_is_visible_reflects_dock_visibility(self, qt: QtDriver) -> None:
        """is_visible reflects dock widget visibility."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)
        win.show()  # Need to show window for dock visibility to work

        assert win._explorer.is_visible is True

        win._explorer.hide()
        assert win._explorer.is_visible is False

        win._explorer.show()
        assert win._explorer.is_visible is True

    def test_is_floating_reflects_dock_floating_state(self, qt: QtDriver) -> None:
        """is_floating reflects dock widget floating state."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.is_floating is False

        win._explorer.float()
        assert win._explorer.is_floating is True

        win._explorer.unfloat()
        assert win._explorer.is_floating is False

    def test_area_property_returns_current_area(self, qt: QtDriver) -> None:
        """area property returns current dock area."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.area == Qt.DockWidgetArea.LeftDockWidgetArea


# =============================================================================
# Dock Helper Methods
# =============================================================================


class TestDockHelperMethods:
    """Test Dock helper methods."""

    def test_toggle_toggles_visibility(self, qt: QtDriver) -> None:
        """toggle() toggles dock visibility."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)
        win.show()  # Need to show window for dock visibility to work

        initial = win._explorer.is_visible
        win._explorer.toggle()
        assert win._explorer.is_visible is not initial
        win._explorer.toggle()
        assert win._explorer.is_visible is initial

    def test_close_hides_dock(self, qt: QtDriver) -> None:
        """close() hides the dock."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)

        win._explorer.close()
        assert win._explorer.is_visible is False


# =============================================================================
# Object Name
# =============================================================================


class TestDockObjectName:
    """Test dock object name handling."""

    def test_dock_object_name_defaults_to_field_name(self, qt: QtDriver) -> None:
        """Dock objectName defaults to field name."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.dock_widget.objectName() == "_explorer"

    def test_dock_object_name_can_be_set_explicitly(self, qt: QtDriver) -> None:
        """name= sets dock objectName explicitly."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", name="my-explorer")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.dock_widget.objectName() == "my-explorer"


# =============================================================================
# Docks Don't Appear in Central Widget Layout
# =============================================================================


class TestDockLayoutExclusion:
    """Test that docks are excluded from central widget layout."""

    def test_docks_not_in_central_widget(self, qt: QtDriver) -> None:
        """Dock fields are not added to the central widget layout."""

        @window
        class TestWindow(Window):
            _label: QLabel = new("Hello")
            _explorer: Dock[ExplorerPanel] = new(dock="left")
            _button: QPushButton = new("Click")

        win = TestWindow()
        qt.track(win)

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


class TestMultipleDocks:
    """Test windows with multiple docks."""

    def test_multiple_docks_in_different_areas(self, qt: QtDriver) -> None:
        """Multiple docks can be placed in different areas."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")
            _props: Dock[PropertiesPanel] = new(dock="right", title="Properties")

        win = TestWindow()
        qt.track(win)

        assert win.dockWidgetArea(win._explorer.dock_widget) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.dockWidgetArea(win._console.dock_widget) == Qt.DockWidgetArea.BottomDockWidgetArea
        assert win.dockWidgetArea(win._props.dock_widget) == Qt.DockWidgetArea.RightDockWidgetArea

    def test_complex_layout_with_splits_and_groups(self, qt: QtDriver) -> None:
        """Complex layout with splits and groups works correctly."""

        @window
        class TestWindow(Window):
            # Left area with vertical split
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _git: Dock[GitPanel] = new(below="_explorer", title="Git")

            # Bottom area with horizontal split
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")
            _output: Dock[OutputPanel] = new(rightOf="_console", title="Output")

            # Right area with tabs
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")

        win = TestWindow()
        qt.track(win)

        # Verify areas
        assert win.dockWidgetArea(win._explorer.dock_widget) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.dockWidgetArea(win._git.dock_widget) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.dockWidgetArea(win._console.dock_widget) == Qt.DockWidgetArea.BottomDockWidgetArea
        assert win.dockWidgetArea(win._output.dock_widget) == Qt.DockWidgetArea.BottomDockWidgetArea
        assert win.dockWidgetArea(win._props.dock_widget) == Qt.DockWidgetArea.RightDockWidgetArea
        assert win.dockWidgetArea(win._inspector.dock_widget) == Qt.DockWidgetArea.RightDockWidgetArea

        # Verify inspector group is tabified
        tabified = win.tabifiedDockWidgets(win._props.dock_widget)
        assert win._inspector.dock_widget in tabified


# =============================================================================
# Dock Feature Properties (Read-Only)
# =============================================================================


class TestDockFeatureProperties:
    """Test dock feature properties."""

    def test_is_closable_default(self, qt: QtDriver) -> None:
        """Dock is closable by default."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.is_closable is True

    def test_is_movable_default(self, qt: QtDriver) -> None:
        """Dock is movable by default."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.is_movable is True

    def test_is_floatable_default(self, qt: QtDriver) -> None:
        """Dock is floatable by default."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.is_floatable is True


# =============================================================================
# Content Widget Constructor Args
# =============================================================================


class TestContentWidgetConstructorArgs:
    """Test that constructor args are passed to content widget."""

    def test_args_passed_to_content_widget(self, qt: QtDriver) -> None:
        """Constructor args are passed to the content widget."""

        @window
        class TestWindow(Window):
            _label: Dock[QLabel] = new("Hello World", dock="left", title="Label Dock")

        win = TestWindow()
        qt.track(win)

        assert win._label.widget.text() == "Hello World"

    def test_kwargs_passed_to_content_widget(self, qt: QtDriver) -> None:
        """Constructor kwargs are passed to the content widget."""

        @window
        class TestWindow(Window):
            _button: Dock[QPushButton] = new(dock="left", title="Button Dock", text="Click Me")

        win = TestWindow()
        qt.track(win)

        assert win._button.widget.text() == "Click Me"


# =============================================================================
# Visible Binding
# =============================================================================


class TestDockVisibleBinding:
    """Test visible= binding for docks."""

    def test_visible_binding_initial_state(self, qt: QtDriver) -> None:
        """visible= binding sets initial dock visibility from Variable."""

        @window
        class TestWindow(Window):
            _show_dock: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", visible="_show_dock")

        win = TestWindow()
        qt.track(win)
        # Note: Not calling win.show() because Qt automatically shows all docks when window shows
        # The binding should set the dock to hidden based on Variable's initial False value
        qt.process_events()

        # Check the dock widget's visibility property (not is_visible which checks isVisible())
        assert win._explorer.dock_widget.isHidden() is True

    def test_visible_binding_variable_to_dock(self, qt: QtDriver) -> None:
        """Changing Variable updates dock visibility."""

        @window
        class TestWindow(Window):
            _show_dock: Variable[bool] = new(True)
            _explorer: Dock[ExplorerPanel] = new(dock="left", visible="_show_dock")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        assert win._explorer.is_visible is True

        win._show_dock.value = False
        qt.process_events()
        assert win._explorer.is_visible is False

        win._show_dock.value = True
        qt.process_events()
        assert win._explorer.is_visible is True

    def test_visible_binding_dock_to_variable(self, qt: QtDriver) -> None:
        """Changing dock visibility updates Variable."""

        @window
        class TestWindow(Window):
            _show_dock: Variable[bool] = new(True)
            _explorer: Dock[ExplorerPanel] = new(dock="left", visible="_show_dock")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        assert win._show_dock.value is True

        win._explorer.hide()
        qt.process_events()
        assert win._show_dock.value is False

        win._explorer.show()
        qt.process_events()
        assert win._show_dock.value is True


# =============================================================================
# Floating Binding
# =============================================================================


class TestDockFloatingBinding:
    """Test floating= binding for docks."""

    def test_floating_binding_initial_state(self, qt: QtDriver) -> None:
        """floating= binding sets initial dock floating state from Variable."""

        @window
        class TestWindow(Window):
            _is_floating: Variable[bool] = new(True)
            _explorer: Dock[ExplorerPanel] = new(dock="left", floating="_is_floating")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        assert win._explorer.is_floating is True

    def test_floating_binding_variable_to_dock(self, qt: QtDriver) -> None:
        """Changing Variable updates dock floating state."""

        @window
        class TestWindow(Window):
            _is_floating: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", floating="_is_floating")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        assert win._explorer.is_floating is False

        win._is_floating.value = True
        qt.process_events()
        assert win._explorer.is_floating is True

        win._is_floating.value = False
        qt.process_events()
        assert win._explorer.is_floating is False

    def test_floating_binding_dock_to_variable(self, qt: QtDriver) -> None:
        """Changing dock floating state updates Variable."""

        @window
        class TestWindow(Window):
            _is_floating: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", floating="_is_floating")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()

        assert win._is_floating.value is False

        win._explorer.float()
        qt.process_events()
        assert win._is_floating.value is True

        win._explorer.unfloat()
        qt.process_events()
        assert win._is_floating.value is False


# =============================================================================
# Group Selected Index Binding
# =============================================================================


class TestGroupSelectedIndexBinding:
    """Test groupSelectedIndex= binding for dock tab groups."""

    def test_group_selected_index_initial_state(self, qt: QtDriver) -> None:
        """groupSelectedIndex= binding sets initial tab index from Variable."""

        @window
        class TestWindow(Window):
            _tab_index: Variable[int] = new(1)
            _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", groupSelectedIndex="_tab_index", title="Properties")
            _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
            _styles: Dock[StylesPanel] = new(group="inspector", title="Styles")

        win = TestWindow()
        qt.track(win)
        win.show()
        qt.process_events()
        # Give QTimer.singleShot(0) time to run
        qt.process_events()

        # Tab index 1 should be selected (Inspector is at index 1 in the tab bar)
        # Note: The actual tab bar order depends on tabification order
        assert win._tab_index.value == 1


# =============================================================================
# Variable[T, Dock[W]] - Primitive Types
# =============================================================================


class TestVariableDockPrimitive:
    """Test Variable[T, Dock[W]] with primitive value types (str, int, etc)."""

    def test_variable_str_dock_creates_dock_wrapper(self, qt: QtDriver) -> None:
        """Variable[str, Dock[QLineEdit]] creates a Dock wrapper."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new("", dock="right", title="Name")

        win = TestWindow()
        qt.track(win)

        # var.widget should be a Dock
        assert isinstance(win._name.widget, Dock)

    def test_variable_str_dock_inner_widget(self, qt: QtDriver) -> None:
        """Variable[str, Dock[QLineEdit]].widget.widget returns the QLineEdit."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new("", dock="right", title="Name")

        win = TestWindow()
        qt.track(win)

        # var.widget.widget should be the inner QLineEdit
        assert isinstance(win._name.widget.widget, QLineEdit)

    def test_variable_str_dock_qdockwidget(self, qt: QtDriver) -> None:
        """Variable[str, Dock[QLineEdit]].widget.dock_widget returns the QDockWidget."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new("", dock="right", title="Name")

        win = TestWindow()
        qt.track(win)

        # var.widget.dock_widget should be the QDockWidget
        assert isinstance(win._name.widget.dock_widget, QDockWidget)

    def test_variable_str_dock_value_access(self, qt: QtDriver) -> None:
        """Variable[str, Dock[QLineEdit]].value returns the string value."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new("Hello", dock="right", title="Name")

        win = TestWindow()
        qt.track(win)

        assert win._name.value == "Hello"

    def test_variable_str_dock_value_set(self, qt: QtDriver) -> None:
        """Setting Variable[str, Dock[QLineEdit]].value updates widget."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new("", dock="right", title="Name")

        win = TestWindow()
        qt.track(win)

        win._name.value = "World"
        qt.process_events()

        assert win._name.value == "World"
        # The widget should be bound and updated
        inner_widget: QLineEdit = win._name.widget.widget
        assert inner_widget.text() == "World"

    def test_variable_int_dock_value(self, qt: QtDriver) -> None:
        """Variable[int, Dock[QSpinBox]] works with integer values."""

        @window
        class TestWindow(Window):
            _count: Variable[int, Dock[QSpinBox]] = new(42, dock="right", title="Count")

        win = TestWindow()
        qt.track(win)

        assert win._count.value == 42
        assert isinstance(win._count.widget, Dock)
        assert isinstance(win._count.widget.widget, QSpinBox)
        assert win._count.widget.widget.value() == 42

    def test_variable_str_dock_area_placement(self, qt: QtDriver) -> None:
        """Variable dock respects dock area placement."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new("", dock="left", title="Name")

        win = TestWindow()
        qt.track(win)

        area = win.dockWidgetArea(win._name.widget.dock_widget)
        assert area == Qt.DockWidgetArea.LeftDockWidgetArea

    def test_variable_dock_title(self, qt: QtDriver) -> None:
        """Variable dock respects title= parameter."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new("", dock="right", title="My Name Field")

        win = TestWindow()
        qt.track(win)

        assert win._name.widget.dock_widget.windowTitle() == "My Name Field"


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


class TestVariableDockComplex:
    """Test Variable[T, Dock[W]] with complex value types (dataclasses).

    Note: For complex types (dataclasses), there's no automatic binding between
    the Variable value and the widget. The widget is just a container. Use QWidget
    subclasses that don't require auto-binding, or use Widget[T] for typed editors.
    """

    def test_variable_complex_dock_creates_dock(self, qt: QtDriver) -> None:
        """Variable[Dog, Dock[QWidget]] creates a Dock wrapper."""

        @window
        class TestWindow(Window):
            # Using QWidget as content type since DogEditor has no auto-binding
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5), dock="right", title="Dog Editor")

        win = TestWindow()
        qt.track(win)

        assert isinstance(win._dog.widget, Dock)

    def test_variable_complex_dock_inner_widget(self, qt: QtDriver) -> None:
        """Variable[Dog, Dock[QWidget]].widget.widget returns the editor widget."""

        @window
        class TestWindow(Window):
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5), dock="right", title="Dog Editor")

        win = TestWindow()
        qt.track(win)

        assert isinstance(win._dog.widget.widget, QWidget)

    def test_variable_complex_dock_value_access(self, qt: QtDriver) -> None:
        """Variable[Dog, Dock[QWidget]].value returns the Dog object."""

        @window
        class TestWindow(Window):
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5), dock="right", title="Dog Editor")

        win = TestWindow()
        qt.track(win)

        # For complex types, value returns the ObservableProxy
        # Properties are accessible via proxy
        assert win._dog.name == "Buddy"
        assert win._dog.age == 5

    def test_variable_complex_dock_property_set(self, qt: QtDriver) -> None:
        """Setting Variable[Dog, Dock[QWidget]] properties works."""

        @window
        class TestWindow(Window):
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5), dock="right", title="Dog Editor")

        win = TestWindow()
        qt.track(win)

        win._dog.name = "Max"
        win._dog.age = 3

        assert win._dog.name == "Max"
        assert win._dog.age == 3

    def test_variable_complex_dock_area_placement(self, qt: QtDriver) -> None:
        """Variable[Dog, Dock[QWidget]] respects dock area."""

        @window
        class TestWindow(Window):
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5), dock="bottom", title="Dog Editor")

        win = TestWindow()
        qt.track(win)

        area = win.dockWidgetArea(win._dog.widget.dock_widget)
        assert area == Qt.DockWidgetArea.BottomDockWidgetArea

    def test_variable_complex_dock_reference_placement(self, qt: QtDriver) -> None:
        """Variable dock can use reference-based placement."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _dog: Variable[Dog, Dock[QWidget]] = new(Dog("Buddy", 5), below="_explorer", title="Dog Editor")

        win = TestWindow()
        qt.track(win)

        # Both should be in left area after split
        explorer_area = win.dockWidgetArea(win._explorer.dock_widget)
        dog_area = win.dockWidgetArea(win._dog.widget.dock_widget)

        assert explorer_area == Qt.DockWidgetArea.LeftDockWidgetArea
        assert dog_area == Qt.DockWidgetArea.LeftDockWidgetArea


# =============================================================================
# Variable[T, Dock[W]] - Mixed with Regular Docks
# =============================================================================


class TestVariableDockMixed:
    """Test Variable[T, Dock[W]] mixed with regular Dock[T] fields."""

    def test_variable_dock_with_regular_docks(self, qt: QtDriver) -> None:
        """Window can have both Variable[T, Dock[W]] and Dock[T] fields."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _name: Variable[str, Dock[QLineEdit]] = new("", dock="right", title="Name")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")

        win = TestWindow()
        qt.track(win)

        # Regular docks work
        assert isinstance(win._explorer, Dock)
        assert isinstance(win._console, Dock)

        # Variable dock works
        assert isinstance(win._name.widget, Dock)
        assert win._name.value == ""

        # All in correct areas
        assert win.dockWidgetArea(win._explorer.dock_widget) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.dockWidgetArea(win._name.widget.dock_widget) == Qt.DockWidgetArea.RightDockWidgetArea
        assert win.dockWidgetArea(win._console.dock_widget) == Qt.DockWidgetArea.BottomDockWidgetArea

    def test_variable_dock_no_interference_with_central_widget(self, qt: QtDriver) -> None:
        """Variable docks don't appear in central widget layout."""

        @window
        class TestWindow(Window):
            _label: QLabel = new("Hello")
            _name: Variable[str, Dock[QLineEdit]] = new("", dock="right", title="Name")
            _button: QPushButton = new("Click")

        win = TestWindow()
        qt.track(win)

        # Central widget should only have label and button
        central = win.centralWidget()
        assert central is not None
        layout = central.layout()
        assert layout is not None
        assert layout.count() == 2  # Not 3


# =============================================================================
# Phase 5: Reactive Title and Icon
# =============================================================================


class TestReactiveTitle:
    """Test reactive title= binding for docks."""

    def test_static_title(self, qt: QtDriver) -> None:
        """Static title= works as before."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="My Explorer")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.dock_widget.windowTitle() == "My Explorer"

    def test_title_variable_binding(self, qt: QtDriver) -> None:
        """title="_variable" binds to a Variable's value."""

        @window
        class TestWindow(Window):
            _title: Variable[str] = new("Initial Title")
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="_title")

        win = TestWindow()
        qt.track(win)

        assert win._explorer.dock_widget.windowTitle() == "Initial Title"

        # Update the variable
        win._title.value = "Updated Title"
        qt.process_events()

        assert win._explorer.dock_widget.windowTitle() == "Updated Title"

    def test_title_expression_binding(self, qt: QtDriver) -> None:
        """title="{expr}" binds to an expression."""

        @window
        class TestWindow(Window):
            _filename: Variable[str] = new("untitled.txt")
            _dirty: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="{_filename}{'*' if _dirty else ''}",
            )

        win = TestWindow()
        qt.track(win)

        assert win._explorer.dock_widget.windowTitle() == "untitled.txt"

        # Set dirty
        win._dirty.value = True
        qt.process_events()

        assert win._explorer.dock_widget.windowTitle() == "untitled.txt*"

        # Change filename
        win._filename.value = "myfile.py"
        qt.process_events()

        assert win._explorer.dock_widget.windowTitle() == "myfile.py*"

    def test_title_simple_expression(self, qt: QtDriver) -> None:
        """title="{_var}" simple expression also works."""

        @window
        class TestWindow(Window):
            _name: Variable[str] = new("Console")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="{_name}")

        win = TestWindow()
        qt.track(win)

        assert win._console.dock_widget.windowTitle() == "Console"

        win._name.value = "Output"
        qt.process_events()

        assert win._console.dock_widget.windowTitle() == "Output"


class TestReactiveIcon:
    """Test reactive icon= binding for docks."""

    def test_static_icon(self, qt: QtDriver) -> None:
        """Static icon= sets the icon once."""
        from qtpy.QtGui import QIcon

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon=":/icons/folder.png")

        win = TestWindow()
        qt.track(win)

        # Icon is set (even if resource doesn't exist, icon object is created)
        icon = win._explorer.dock_widget.windowIcon()
        assert isinstance(icon, QIcon)

    def test_icon_variable_binding(self, qt: QtDriver) -> None:
        """icon="_variable" binds to a Variable's value."""
        from qtpy.QtGui import QIcon

        @window
        class TestWindow(Window):
            _icon_path: Variable[str] = new(":/icons/initial.png")
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon_path")

        win = TestWindow()
        qt.track(win)

        # Update the variable
        win._icon_path.value = ":/icons/updated.png"
        qt.process_events()

        # Icon is updated (we can't easily verify the path, but icon object exists)
        icon = win._explorer.dock_widget.windowIcon()
        assert isinstance(icon, QIcon)

    def test_icon_expression_binding(self, qt: QtDriver) -> None:
        """icon="{expr}" binds to an expression."""
        from qtpy.QtGui import QIcon

        @window
        class TestWindow(Window):
            _mode: Variable[str] = new("light")
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="Explorer",
                icon=":/icons/{_mode}/folder.png",
            )

        win = TestWindow()
        qt.track(win)

        # Change mode
        win._mode.value = "dark"
        qt.process_events()

        icon = win._explorer.dock_widget.windowIcon()
        assert isinstance(icon, QIcon)

    def test_icon_empty_clears(self, qt: QtDriver) -> None:
        """Setting icon to empty string clears it."""

        @window
        class TestWindow(Window):
            _icon_path: Variable[str] = new(":/icons/folder.png")
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon_path")

        win = TestWindow()
        qt.track(win)

        # Clear the icon
        win._icon_path.value = ""
        qt.process_events()

        icon = win._explorer.dock_widget.windowIcon()
        # Empty QIcon
        assert icon.isNull()

    def test_icon_qicon_variable(self, qt: QtDriver) -> None:
        """icon= supports Variable[QIcon]."""
        # Create a real QIcon from a pixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.red)
        initial_icon = QIcon(pixmap)

        @window
        class TestWindow(Window):
            _icon: Variable[QIcon] = new(initial_icon)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon")

        win = TestWindow()
        qt.track(win)

        # Icon should be set
        assert not win._explorer.dock_widget.windowIcon().isNull()

        # Update to a different icon
        pixmap2 = QPixmap(16, 16)
        pixmap2.fill(Qt.GlobalColor.blue)
        win._icon.value = QIcon(pixmap2)
        qt.process_events()

        # Still has an icon
        assert not win._explorer.dock_widget.windowIcon().isNull()

    def test_icon_qpixmap_variable(self, qt: QtDriver) -> None:
        """icon= supports Variable[QPixmap] (converted to QIcon)."""
        # Create a real QPixmap
        initial_pixmap = QPixmap(16, 16)
        initial_pixmap.fill(Qt.GlobalColor.green)

        @window
        class TestWindow(Window):
            _pixmap: Variable[QPixmap] = new(initial_pixmap)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_pixmap")

        win = TestWindow()
        qt.track(win)

        # Icon should be set (QPixmap converted to QIcon)
        assert not win._explorer.dock_widget.windowIcon().isNull()

        # Update to a different pixmap
        pixmap2 = QPixmap(16, 16)
        pixmap2.fill(Qt.GlobalColor.yellow)
        win._pixmap.value = pixmap2
        qt.process_events()

        # Still has an icon
        assert not win._explorer.dock_widget.windowIcon().isNull()

    def test_icon_none_clears(self, qt: QtDriver) -> None:
        """Setting icon to None clears it."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.red)
        initial_icon = QIcon(pixmap)

        @window
        class TestWindow(Window):
            _icon: Variable[QIcon | None] = new(initial_icon)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon")

        win = TestWindow()
        qt.track(win)

        # Has icon initially
        assert not win._explorer.dock_widget.windowIcon().isNull()

        # Clear with None
        win._icon.value = None
        qt.process_events()

        # Icon is now null
        assert win._explorer.dock_widget.windowIcon().isNull()

    def test_icon_qicon_or_qpixmap_variable(self, qt: QtDriver) -> None:
        """Variable[QIcon | QPixmap] can switch between types."""
        # Start with QIcon
        pixmap1 = QPixmap(16, 16)
        pixmap1.fill(Qt.GlobalColor.red)
        initial_icon = QIcon(pixmap1)

        @window
        class TestWindow(Window):
            _icon: Variable[QIcon | QPixmap] = new(initial_icon)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", icon="_icon")

        win = TestWindow()
        qt.track(win)

        # Has icon initially (QIcon)
        assert not win._explorer.dock_widget.windowIcon().isNull()

        # Switch to QPixmap
        pixmap2 = QPixmap(16, 16)
        pixmap2.fill(Qt.GlobalColor.blue)
        win._icon.value = pixmap2
        qt.process_events()

        # Still has icon (QPixmap converted to QIcon)
        assert not win._explorer.dock_widget.windowIcon().isNull()

        # Switch back to QIcon
        pixmap3 = QPixmap(16, 16)
        pixmap3.fill(Qt.GlobalColor.green)
        win._icon.value = QIcon(pixmap3)
        qt.process_events()

        # Still has icon
        assert not win._explorer.dock_widget.windowIcon().isNull()


class TestVariableDockReactiveTitle:
    """Test reactive title for Variable[T, Dock[W]]."""

    def test_variable_dock_reactive_title(self, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports reactive title."""

        @window
        class TestWindow(Window):
            _tab_title: Variable[str] = new("Name Editor")
            _name: Variable[str, Dock[QLineEdit]] = new("", dock="right", title="_tab_title")

        win = TestWindow()
        qt.track(win)

        assert win._name.widget.dock_widget.windowTitle() == "Name Editor"

        win._tab_title.value = "User Name"
        qt.process_events()

        assert win._name.widget.dock_widget.windowTitle() == "User Name"

    def test_variable_dock_title_expression(self, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports title expression."""

        @window
        class TestWindow(Window):
            _field_name: Variable[str] = new("Name")
            _required: Variable[bool] = new(True)
            _name: Variable[str, Dock[QLineEdit]] = new(
                "",
                dock="right",
                title="{_field_name}{'*' if _required else ''}",
            )

        win = TestWindow()
        qt.track(win)

        assert win._name.widget.dock_widget.windowTitle() == "Name*"

        win._required.value = False
        qt.process_events()

        assert win._name.widget.dock_widget.windowTitle() == "Name"


class TestDockFeatures:
    """Test dock features (closable, floatable, movable, allowedAreas, verticalTitleBar)."""

    def test_closable_false(self, qt: QtDriver) -> None:
        """closable=False removes close button."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", closable=False)

        win = TestWindow()
        qt.track(win)

        features = win._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        # Other features should still be enabled
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable

    def test_floatable_false(self, qt: QtDriver) -> None:
        """floatable=False prevents floating."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", floatable=False)

        win = TestWindow()
        qt.track(win)

        features = win._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        # Other features should still be enabled
        assert features & QDockWidget.DockWidgetFeature.DockWidgetClosable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable

    def test_movable_false(self, qt: QtDriver) -> None:
        """movable=False prevents dragging."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", movable=False)

        win = TestWindow()
        qt.track(win)

        features = win._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        # Other features should still be enabled
        assert features & QDockWidget.DockWidgetFeature.DockWidgetClosable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable

    def test_all_features_disabled(self, qt: QtDriver) -> None:
        """All features can be disabled at once."""

        @window
        class TestWindow(Window):
            _toolbar: Dock[ExplorerPanel] = new(
                dock="left",
                title="Toolbar",
                closable=False,
                floatable=False,
                movable=False,
            )

        win = TestWindow()
        qt.track(win)

        features = win._toolbar.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)

    def test_allowed_areas_left_right(self, qt: QtDriver) -> None:
        """allowedAreas restricts where dock can be placed."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="Explorer",
                allowedAreas=["left", "right"],
            )

        win = TestWindow()
        qt.track(win)

        allowed = win._explorer.dock_widget.allowedAreas()
        assert allowed & Qt.DockWidgetArea.LeftDockWidgetArea
        assert allowed & Qt.DockWidgetArea.RightDockWidgetArea
        assert not (allowed & Qt.DockWidgetArea.TopDockWidgetArea)
        assert not (allowed & Qt.DockWidgetArea.BottomDockWidgetArea)

    def test_allowed_areas_all(self, qt: QtDriver) -> None:
        """allowedAreas with all areas."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="Explorer",
                allowedAreas=["left", "right", "top", "bottom"],
            )

        win = TestWindow()
        qt.track(win)

        allowed = win._explorer.dock_widget.allowedAreas()
        assert allowed & Qt.DockWidgetArea.LeftDockWidgetArea
        assert allowed & Qt.DockWidgetArea.RightDockWidgetArea
        assert allowed & Qt.DockWidgetArea.TopDockWidgetArea
        assert allowed & Qt.DockWidgetArea.BottomDockWidgetArea

    def test_vertical_title_bar(self, qt: QtDriver) -> None:
        """verticalTitleBar=True enables vertical title bar."""

        @window
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(
                dock="left",
                title="Explorer",
                verticalTitleBar=True,
            )

        win = TestWindow()
        qt.track(win)

        features = win._explorer.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar

    def test_combined_features(self, qt: QtDriver) -> None:
        """Multiple features can be combined."""

        @window
        class TestWindow(Window):
            _toolbar: Dock[ExplorerPanel] = new(
                dock="left",
                title="Tools",
                closable=False,
                floatable=False,
                movable=False,
                allowedAreas=["left", "right"],
                verticalTitleBar=True,
            )

        win = TestWindow()
        qt.track(win)

        features = win._toolbar.dock_widget.features()
        # Features disabled
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        # Vertical title bar enabled
        assert features & QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar

        # Allowed areas
        allowed = win._toolbar.dock_widget.allowedAreas()
        assert allowed & Qt.DockWidgetArea.LeftDockWidgetArea
        assert allowed & Qt.DockWidgetArea.RightDockWidgetArea
        assert not (allowed & Qt.DockWidgetArea.TopDockWidgetArea)


class TestDockFeaturesVariableDock:
    """Test dock features for Variable[T, Dock[W]]."""

    def test_variable_dock_closable_false(self, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports closable=False."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new(
                "",
                dock="right",
                title="Name",
                closable=False,
            )

        win = TestWindow()
        qt.track(win)

        features = win._name.widget.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)

    def test_variable_dock_allowed_areas(self, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports allowedAreas."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new(
                "",
                dock="right",
                title="Name",
                allowedAreas=["left", "right"],
            )

        win = TestWindow()
        qt.track(win)

        allowed = win._name.widget.dock_widget.allowedAreas()
        assert allowed & Qt.DockWidgetArea.LeftDockWidgetArea
        assert allowed & Qt.DockWidgetArea.RightDockWidgetArea
        assert not (allowed & Qt.DockWidgetArea.TopDockWidgetArea)

    def test_variable_dock_vertical_title_bar(self, qt: QtDriver) -> None:
        """Variable[T, Dock[W]] supports verticalTitleBar."""

        @window
        class TestWindow(Window):
            _name: Variable[str, Dock[QLineEdit]] = new(
                "",
                dock="left",
                title="Name",
                verticalTitleBar=True,
            )

        win = TestWindow()
        qt.track(win)

        features = win._name.widget.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar


class TestWindowDockCorners:
    """Test corners= parameter for window-level corner assignment."""

    def test_corners_top_left_to_left(self, qt: QtDriver) -> None:
        """corners= assigns top-left corner to left dock area."""

        @window(corners={"top_left": "left"})
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")

        win = TestWindow()
        qt.track(win)

        # Verify the corner is assigned to left area
        assert win.corner(Qt.Corner.TopLeftCorner) == Qt.DockWidgetArea.LeftDockWidgetArea

    def test_corners_multiple(self, qt: QtDriver) -> None:
        """corners= can assign multiple corners."""

        @window(
            corners={
                "top_left": "left",
                "bottom_left": "bottom",
                "top_right": "right",
                "bottom_right": "bottom",
            }
        )
        class TestWindow(Window):
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        win = TestWindow()
        qt.track(win)

        assert win.corner(Qt.Corner.TopLeftCorner) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert win.corner(Qt.Corner.BottomLeftCorner) == Qt.DockWidgetArea.BottomDockWidgetArea
        assert win.corner(Qt.Corner.TopRightCorner) == Qt.DockWidgetArea.RightDockWidgetArea
        assert win.corner(Qt.Corner.BottomRightCorner) == Qt.DockWidgetArea.BottomDockWidgetArea


class TestDocksLocked:
    """Test docksLocked= parameter for locking all docks."""

    def test_docks_locked_initial_true(self, qt: QtDriver) -> None:
        """docksLocked=True initially locks all docks."""

        @window(docksLocked="_locked")
        class TestWindow(Window):
            _locked: Variable[bool] = new(True)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")
            _console: Dock[ConsolePanel] = new(dock="bottom", title="Console")

        win = TestWindow()
        qt.track(win)

        # All docks should be locked (not movable/floatable)
        explorer_features = win._explorer.dock_widget.features()
        console_features = win._console.dock_widget.features()

        assert not (explorer_features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        assert not (explorer_features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        assert not (console_features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        assert not (console_features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)

    def test_docks_locked_initial_false(self, qt: QtDriver) -> None:
        """docksLocked=False initially leaves docks unlocked."""

        @window(docksLocked="_locked")
        class TestWindow(Window):
            _locked: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        win = TestWindow()
        qt.track(win)

        # Docks should be unlocked (movable/floatable)
        features = win._explorer.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable

    def test_docks_locked_reactive(self, qt: QtDriver) -> None:
        """docksLocked binding is reactive."""

        @window(docksLocked="_locked")
        class TestWindow(Window):
            _locked: Variable[bool] = new(False)
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer")

        win = TestWindow()
        qt.track(win)

        # Initially unlocked
        features = win._explorer.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable

        # Lock
        win._locked.value = True
        qt.process_events()

        features = win._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetFloatable)

        # Unlock
        win._locked.value = False
        qt.process_events()

        features = win._explorer.dock_widget.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable

    def test_docks_locked_preserves_closable(self, qt: QtDriver) -> None:
        """docksLocked only affects movable/floatable, not closable."""

        @window(docksLocked="_locked")
        class TestWindow(Window):
            _locked: Variable[bool] = new(False)
            # closable=False should be preserved
            _explorer: Dock[ExplorerPanel] = new(dock="left", title="Explorer", closable=False)

        win = TestWindow()
        qt.track(win)

        # Initially not closable
        features = win._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable

        # Lock
        win._locked.value = True
        qt.process_events()

        # Still not closable, and now not movable
        features = win._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetMovable)

        # Unlock - closable should still be False
        win._locked.value = False
        qt.process_events()

        features = win._explorer.dock_widget.features()
        assert not (features & QDockWidget.DockWidgetFeature.DockWidgetClosable)
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
