# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportUnknownMemberType=false
# pyright: reportUnknownLambdaType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportGeneralTypeIssues=false
"""Tests for Window with auto-layout and menu bar integration."""

from dataclasses import dataclass

from assertpy import assert_that
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton, QVBoxLayout

from qtpie import Variable, Window, menu, new, window
from qtpie.testing import QtDriver


class TestWindowBasicLayout:
    """Test Window central widget layout functionality."""

    def test_vertical_layout_default(self, qt: QtDriver) -> None:
        """Window central widget uses vertical layout by default."""

        @window
        class MainWindow(Window):
            label: QLabel = new("Hello")
            button: QPushButton = new("Click")

        w = qt.track(MainWindow())
        central = w.centralWidget()
        assert_that(central).is_not_none()
        assert_that(central.layout()).is_instance_of(QVBoxLayout)

    def test_horizontal_layout(self, qt: QtDriver) -> None:
        """Window can use horizontal layout for central widget."""

        @window(layout="horizontal")
        class MainWindow(Window):
            label: QLabel = new("Hello")
            button: QPushButton = new("Click")

        w = qt.track(MainWindow())
        central = w.centralWidget()
        assert_that(central.layout()).is_instance_of(QHBoxLayout)

    def test_no_layout(self, qt: QtDriver) -> None:
        """Window with layout=None creates no central widget layout."""

        @window(layout=None)
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        # With layout=None and non-menu widgets, no central widget is created
        # (since we can't add widgets to a layout that doesn't exist)
        # Actually the implementation creates a central widget but without layout
        central = w.centralWidget()
        # When layout is None but there are widgets, no container is created
        assert_that(central).is_none()

    def test_widgets_added_in_order(self, qt: QtDriver) -> None:
        """Child widgets are added to central widget layout in field definition order."""

        @window
        class MainWindow(Window):
            first: QLabel = new("First")
            second: QLabel = new("Second")
            third: QLabel = new("Third")

        w = qt.track(MainWindow())
        layout = w.centralWidget().layout()
        assert_that(layout.count()).is_equal_to(3)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w.first)
        assert_that(layout.itemAt(1).widget()).is_equal_to(w.second)
        assert_that(layout.itemAt(2).widget()).is_equal_to(w.third)

    def test_no_widgets_no_central(self, qt: QtDriver) -> None:
        """Window with only menus has no central widget."""

        @menu("&File")
        class FileMenu(QMenu):
            pass

        @window
        class MainWindow(Window):
            file_menu: FileMenu = new()

        w = qt.track(MainWindow())
        # No QWidget fields, so no central widget created
        assert_that(w.centralWidget()).is_none()


class TestWindowMargins:
    """Test Window central widget layout margins."""

    def test_int_margins(self, qt: QtDriver) -> None:
        """Integer margins apply to all sides."""

        @window(margins=10)
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        margins = w.centralWidget().layout().contentsMargins()
        assert_that(margins.left()).is_equal_to(10)
        assert_that(margins.top()).is_equal_to(10)
        assert_that(margins.right()).is_equal_to(10)
        assert_that(margins.bottom()).is_equal_to(10)

    def test_tuple_margins(self, qt: QtDriver) -> None:
        """Tuple margins apply to (left, top, right, bottom)."""

        @window(margins=(1, 2, 3, 4))
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        margins = w.centralWidget().layout().contentsMargins()
        assert_that(margins.left()).is_equal_to(1)
        assert_that(margins.top()).is_equal_to(2)
        assert_that(margins.right()).is_equal_to(3)
        assert_that(margins.bottom()).is_equal_to(4)


class TestWindowMenuBar:
    """Test Window menu bar integration."""

    def test_qmenu_added_to_menubar(self, qt: QtDriver) -> None:
        """QMenu fields are automatically added to menu bar."""

        @menu("&File")
        class FileMenu(QMenu):
            pass

        @window
        class MainWindow(Window):
            file_menu: FileMenu = new()

        w = qt.track(MainWindow())
        menubar = w.menuBar()
        actions = menubar.actions()
        assert_that(len(actions)).is_equal_to(1)
        assert_that(actions[0].text()).is_equal_to("&File")

    def test_multiple_menus_in_order(self, qt: QtDriver) -> None:
        """Multiple QMenu fields added in declaration order."""

        @menu("&File")
        class FileMenu(QMenu):
            pass

        @menu("&Edit")
        class EditMenu(QMenu):
            pass

        @menu("&Help")
        class HelpMenu(QMenu):
            pass

        @window
        class MainWindow(Window):
            file_menu: FileMenu = new()
            edit_menu: EditMenu = new()
            help_menu: HelpMenu = new()

        w = qt.track(MainWindow())
        menubar = w.menuBar()
        actions = menubar.actions()
        assert_that(len(actions)).is_equal_to(3)
        assert_that(actions[0].text()).is_equal_to("&File")
        assert_that(actions[1].text()).is_equal_to("&Edit")
        assert_that(actions[2].text()).is_equal_to("&Help")

    def test_menus_and_widgets_together(self, qt: QtDriver) -> None:
        """Menus go to menubar, widgets go to central widget."""

        @menu("&File")
        class FileMenu(QMenu):
            pass

        @window
        class MainWindow(Window):
            file_menu: FileMenu = new()
            label: QLabel = new("Hello")
            button: QPushButton = new("Click")

        w = qt.track(MainWindow())

        # Menu in menubar
        menubar = w.menuBar()
        assert_that(len(menubar.actions())).is_equal_to(1)
        assert_that(menubar.actions()[0].text()).is_equal_to("&File")

        # Widgets in central widget
        layout = w.centralWidget().layout()
        assert_that(layout.count()).is_equal_to(2)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w.label)
        assert_that(layout.itemAt(1).widget()).is_equal_to(w.button)


class TestWindowCentralWidget:
    """Test explicit central_widget field."""

    def test_explicit_central_widget(self, qt: QtDriver) -> None:
        """central_widget field becomes the central widget directly."""

        @window
        class MainWindow(Window):
            central_widget: QLabel = new("I AM THE CENTRAL WIDGET")

        w = qt.track(MainWindow())
        central = w.centralWidget()
        assert_that(central).is_same_as(w.central_widget)
        assert_that(central.text()).is_equal_to("I AM THE CENTRAL WIDGET")

    def test_explicit_central_widget_no_container(self, qt: QtDriver) -> None:
        """With explicit central_widget, other widgets are NOT added."""

        @window
        class MainWindow(Window):
            central_widget: QLabel = new("Central")
            other_label: QLabel = new("Other")  # Not added to layout

        w = qt.track(MainWindow())
        central = w.centralWidget()
        # central_widget is the central widget directly
        assert_that(central).is_same_as(w.central_widget)
        # other_label exists but not in any layout
        assert_that(w.other_label).is_not_none()
        assert_that(w.other_label.text()).is_equal_to("Other")

    def test_variable_central_widget(self, qt: QtDriver) -> None:
        """central_widget: Variable[str, QLabel] works."""

        @window
        class MainWindow(Window):
            central_widget: Variable[str, QLabel] = new("Initial")(bind="{#self.upper()}")

        w = qt.track(MainWindow())
        central = w.centralWidget()
        # The central widget should be the Variable's widget
        assert_that(central).is_same_as(w.central_widget.widget)
        assert_that(central.text()).is_equal_to("INITIAL")

        # Reactive update
        w.central_widget.value = "updated"
        assert_that(central.text()).is_equal_to("UPDATED")

    def test_variable_central_widget_with_binding(self, qt: QtDriver) -> None:
        """central_widget: Variable[str, QLineEdit] with two-way binding works."""

        @window
        class MainWindow(Window):
            central_widget: Variable[str, QLineEdit] = new("")

        w = qt.track(MainWindow())
        central = w.centralWidget()
        assert isinstance(central, QLineEdit)

        # Two-way binding works
        w.central_widget.value = "test"
        assert_that(central.text()).is_equal_to("test")

        central.setText("typed")
        assert_that(w.central_widget.value).is_equal_to("typed")


class TestWindowLayoutExclusion:
    """Test excluding widgets from layout."""

    def test_exclude_from_layout(self, qt: QtDriver) -> None:
        """Widgets with layout=False are not added to central widget layout."""

        @window
        class MainWindow(Window):
            visible: QLabel = new("Visible")
            hidden: QLabel = new("Hidden", layout=False)
            also_visible: QLabel = new("Also Visible")

        w = qt.track(MainWindow())
        layout = w.centralWidget().layout()

        # Only 2 widgets in layout
        assert_that(layout.count()).is_equal_to(2)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w.visible)
        assert_that(layout.itemAt(1).widget()).is_equal_to(w.also_visible)

        # But all widgets exist as attributes
        assert_that(w.hidden).is_not_none()
        assert_that(w.hidden.text()).is_equal_to("Hidden")


class TestWindowWithVariables:
    """Test Window with Variable fields."""

    def test_variable_fields_work(self, qt: QtDriver) -> None:
        """Variable fields work in Window."""

        @window
        class MainWindow(Window):
            _count: Variable[int] = new(0)
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        w._count = 42
        assert_that(w._count.value).is_equal_to(42)

    def test_variables_not_added_to_layout(self, qt: QtDriver) -> None:
        """Variable fields (without widgets) are not added to layout."""

        @window
        class MainWindow(Window):
            _count: Variable[int] = new(0)
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        layout = w.centralWidget().layout()
        # Only the QLabel should be in the layout
        assert_that(layout.count()).is_equal_to(1)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w.label)


class TestWindowSetup:
    """Test Window __setup__ hook."""

    def test_setup_called(self, qt: QtDriver) -> None:
        """__setup__ is called after initialization."""
        setup_called = False

        @window
        class MainWindow(Window):
            label: QLabel = new("Hello")

            def __setup__(self) -> None:
                nonlocal setup_called
                setup_called = True
                # Widgets should be ready
                assert self.label.text() == "Hello"

        qt.track(MainWindow())
        assert_that(setup_called).is_true()

    def test_setup_called_after_menus(self, qt: QtDriver) -> None:
        """__setup__ is called after menus are added to menubar."""

        @menu("&File")
        class FileMenu(QMenu):
            pass

        setup_menu_count = 0

        @window
        class MainWindow(Window):
            file_menu: FileMenu = new()

            def __setup__(self) -> None:
                nonlocal setup_menu_count
                setup_menu_count = len(self.menuBar().actions())

        qt.track(MainWindow())
        assert_that(setup_menu_count).is_equal_to(1)


class TestWindowDecoratorRequired:
    """Test that @window decorator is required."""

    def test_missing_decorator_raises_error(self) -> None:
        """Window without @window raises TypeError on instantiation."""
        import pytest

        class MainWindow(Window):
            label: QLabel = new("Hello")

        with pytest.raises(TypeError) as exc_info:
            MainWindow()

        assert "must be decorated with @window" in str(exc_info.value)
        assert "MainWindow" in str(exc_info.value)


class TestWindowSignalConnections:
    """Test declarative signal connections in Window."""

    def test_signal_with_method_name(self, qt: QtDriver) -> None:
        """Signal connected to method by name."""

        @window
        class MainWindow(Window):
            btn: QPushButton = new("Click", clicked="on_clicked")
            was_clicked: bool = False

            def on_clicked(self) -> None:
                self.was_clicked = True

        w = qt.track(MainWindow())
        w.btn.click()
        assert_that(w.was_clicked).is_true()

    def test_signal_with_lambda(self, qt: QtDriver) -> None:
        """Signal connected to lambda."""
        clicked = False

        def on_click() -> None:
            nonlocal clicked
            clicked = True

        @window
        class MainWindow(Window):
            btn: QPushButton = new("Click", clicked=on_click)

        w = qt.track(MainWindow())
        w.btn.click()
        assert_that(clicked).is_true()


class TestWindowProps:
    """Test @window decorator kwargs become setXXX() calls."""

    def test_window_title(self, qt: QtDriver) -> None:
        """windowTitle kwarg calls setWindowTitle()."""

        @window(windowTitle="My Window")
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.windowTitle()).is_equal_to("My Window")

    def test_title_alias(self, qt: QtDriver) -> None:
        """title kwarg is alias for windowTitle."""

        @window(title="My Window")
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.windowTitle()).is_equal_to("My Window")

    def test_stylesheet_alias(self, qt: QtDriver) -> None:
        """stylesheet kwarg is alias for styleSheet."""

        @window(stylesheet="background: yellow;")
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.styleSheet()).is_equal_to("background: yellow;")

    def test_minimum_size(self, qt: QtDriver) -> None:
        """minimumWidth/minimumHeight kwargs work."""

        @window(minimumWidth=800, minimumHeight=600)
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.minimumWidth()).is_equal_to(800)
        assert_that(w.minimumHeight()).is_equal_to(600)


class TestWindowObjectName:
    """Test Window objectName configuration."""

    def test_default_object_name(self, qt: QtDriver) -> None:
        """Window gets class name as default objectName."""

        @window
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.objectName()).is_equal_to("MainWindow")

    def test_explicit_object_name(self, qt: QtDriver) -> None:
        """Window can have explicit objectName via name= param."""

        @window(name="my-main-window")
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.objectName()).is_equal_to("my-main-window")


class TestWindowCssClasses:
    """Test Window CSS class configuration."""

    def test_css_classes(self, qt: QtDriver) -> None:
        """Window can have CSS classes via classes= param."""

        @window(classes=["dark-theme", "main-window"])
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        # CSS classes are stored in the "class" dynamic property
        class_prop = w.property("class")
        assert_that(class_prop).contains("dark-theme")
        assert_that(class_prop).contains("main-window")


class TestWindowRecord:
    """Test Window[T] record support."""

    def test_window_with_record_type(self, qt: QtDriver) -> None:
        """Window[T] creates record accessor."""

        @dataclass
        class Dog:
            name: str
            age: int

        @window
        class DogWindow(Window[Dog]):
            label: QLabel = new("Dog Editor")

        w = qt.track(DogWindow())
        # Can set record
        w.record = Dog("Fido", 3)
        assert_that(w.record.name).is_equal_to("Fido")
        assert_that(w.record.age).is_equal_to(3)

    def test_window_record_state(self, qt: QtDriver) -> None:
        """Window[T] has record_state accessor."""

        @dataclass
        class Dog:
            name: str
            age: int

        @window
        class DogWindow(Window[Dog]):
            label: QLabel = new("Dog Editor")

        w = qt.track(DogWindow())
        w.record = Dog("Buddy", 5)

        # record_state gives access to the Variable wrapper
        state = w.record_state
        assert_that(state.value.name).is_equal_to("Buddy")
        assert_that(state.value.age).is_equal_to(5)

    def test_window_without_record_raises(self, qt: QtDriver) -> None:
        """Accessing record on Window without T raises TypeError."""
        import pytest

        @window
        class MainWindow(Window):
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())

        with pytest.raises(TypeError) as exc_info:
            _ = w.record

        assert "has no record type" in str(exc_info.value)


class TestWindowViewModel:
    """Test Window view_model accessor."""

    def test_view_model_access(self, qt: QtDriver) -> None:
        """Window has view_model accessor for Variable fields."""

        @window
        class MainWindow(Window):
            _count: Variable[int] = new(0)
            _name: Variable[str] = new("test")
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        w._count = 42
        w._name = "updated"

        # view_model provides access to Variables
        vm = w.view_model
        assert_that(vm._count.value).is_equal_to(42)
        assert_that(vm._name.value).is_equal_to("updated")


class TestMenuSignalConnections:
    """Test menu action signal connections in Window."""

    def test_menu_action_triggered(self, qt: QtDriver) -> None:
        """Menu actions with triggered= connect properly."""
        exit_called = False

        @menu("&File")
        class FileMenu(QMenu):
            action_exit: QAction = new("E&xit", triggered="on_exit")

            def on_exit(self) -> None:
                nonlocal exit_called
                exit_called = True

        @window
        class MainWindow(Window):
            file_menu: FileMenu = new()

        w = qt.track(MainWindow())
        w.file_menu.action_exit.trigger()
        assert_that(exit_called).is_true()


class TestWindowBindingPlaceholder:
    """Test #window binding placeholder in Window."""

    def test_window_placeholder_in_binding(self, qt: QtDriver) -> None:
        """#window placeholder works in binding expressions."""

        @window(title="Test Window")
        class MainWindow(Window):
            label: QLabel = new(bind="Title: {#window.windowTitle()}")

        w = qt.track(MainWindow())
        assert_that(w.label.text()).is_equal_to("Title: Test Window")

    def test_window_placeholder_alias_for_widget(self, qt: QtDriver) -> None:
        """#window is an alias for #widget."""

        @window(title="My App")
        class MainWindow(Window):
            label1: QLabel = new(bind="Widget: {#widget.windowTitle()}")
            label2: QLabel = new(bind="Window: {#window.windowTitle()}")

        w = qt.track(MainWindow())
        # Both should give the same result
        assert_that(w.label1.text()).is_equal_to("Widget: My App")
        assert_that(w.label2.text()).is_equal_to("Window: My App")


# =============================================================================
# Format binding expressions in Window - matching Widget behavior
# =============================================================================


class TestWindowFormatBindingExpressions:
    """Test complex Python expressions in format bindings work in Window."""

    def test_len_function(self, qt: QtDriver) -> None:
        """len() works on string variables in Window."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("Hello")
            label: QLabel = new(bind="{len(_name)}")

        w = qt.track(MainWindow())
        assert_that(w.label.text()).is_equal_to("5")

    def test_len_reactivity(self, qt: QtDriver) -> None:
        """len() updates when variable changes in Window."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("Hi")
            label: QLabel = new(bind="{len(_name)}")

        w = qt.track(MainWindow())
        assert_that(w.label.text()).is_equal_to("2")

        w._name.value = "Hello World"
        assert_that(w.label.text()).is_equal_to("11")

    def test_string_methods(self, qt: QtDriver) -> None:
        """String methods work in Window bindings."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("hello")
            upper_label: QLabel = new(bind="{_name.upper()}")
            title_label: QLabel = new(bind="{_name.title()}")

        w = qt.track(MainWindow())
        assert_that(w.upper_label.text()).is_equal_to("HELLO")
        assert_that(w.title_label.text()).is_equal_to("Hello")

    def test_math_expressions(self, qt: QtDriver) -> None:
        """Math expressions work in Window bindings."""

        @window(title="Test")
        class MainWindow(Window):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(20)
            sum_label: QLabel = new(bind="{_x + _y}")
            product_label: QLabel = new(bind="{_x * _y}")

        w = qt.track(MainWindow())
        assert_that(w.sum_label.text()).is_equal_to("30")
        assert_that(w.product_label.text()).is_equal_to("200")

    def test_complex_math(self, qt: QtDriver) -> None:
        """Complex math with parentheses works in Window."""

        @window(title="Test")
        class MainWindow(Window):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(20)
            _z: Variable[int] = new(5)
            result_label: QLabel = new(bind="{(_x + _y) * _z}")

        w = qt.track(MainWindow())
        assert_that(w.result_label.text()).is_equal_to("150")

    def test_math_reactivity(self, qt: QtDriver) -> None:
        """Math expressions update when variables change."""

        @window(title="Test")
        class MainWindow(Window):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(20)
            sum_label: QLabel = new(bind="{_x + _y}")

        w = qt.track(MainWindow())
        assert_that(w.sum_label.text()).is_equal_to("30")

        w._x.value = 100
        assert_that(w.sum_label.text()).is_equal_to("120")

    def test_format_specs(self, qt: QtDriver) -> None:
        """Format specifications work in Window bindings."""

        @window(title="Test")
        class MainWindow(Window):
            _price: Variable[float] = new(19.99)
            label: QLabel = new(bind="${_price:.2f}")

        w = qt.track(MainWindow())
        assert_that(w.label.text()).is_equal_to("$19.99")

    def test_instance_methods(self, qt: QtDriver) -> None:
        """Instance methods can be called in bindings."""

        @window(title="Test")
        class MainWindow(Window):
            label: QLabel = new(bind="{compute_value()}")

            def compute_value(self) -> str:
                return "Computed!"

        w = qt.track(MainWindow())
        assert_that(w.label.text()).is_equal_to("Computed!")

    def test_methods_with_args(self, qt: QtDriver) -> None:
        """Methods with arguments work in bindings."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("Hi")
            label: QLabel = new(bind="{repeat_text(_name, 3)}")

            def repeat_text(self, text: str, times: int) -> str:
                return text * times

        w = qt.track(MainWindow())
        assert_that(w.label.text()).is_equal_to("HiHiHi")

    def test_self_placeholder(self, qt: QtDriver) -> None:
        """#self placeholder works in Variable[T, W] bindings."""

        @window(title="Test")
        class MainWindow(Window):
            var: Variable[str, QLabel] = new("hello")(bind="{#self.upper()}")

        w = qt.track(MainWindow())
        assert_that(w.var.widget.text()).is_equal_to("HELLO")

    def test_mixed_text_and_expressions(self, qt: QtDriver) -> None:
        """Multiple expressions in one binding work."""

        @window(title="Test")
        class MainWindow(Window):
            _x: Variable[int] = new(5)
            _y: Variable[int] = new(10)
            label: QLabel = new(bind="x={_x}, y={_y}, sum={_x + _y}")

        w = qt.track(MainWindow())
        assert_that(w.label.text()).is_equal_to("x=5, y=10, sum=15")


# =============================================================================
# Property bindings in Window (visible=, enabled=)
# =============================================================================


class TestWindowPropertyBindings:
    """Test property bindings work in Window."""

    def test_visible_binding_simple(self, qt: QtDriver) -> None:
        """visible= binding works in Window."""

        @window(title="Test")
        class MainWindow(Window):
            _show_label: Variable[bool] = new(True)
            label: QLabel = new("Hello", visible="_show_label")

        w = qt.track(MainWindow())
        assert not w.label.isHidden()

        w._show_label.value = False
        assert w.label.isHidden()

        w._show_label.value = True
        assert not w.label.isHidden()

    def test_visible_starts_hidden(self, qt: QtDriver) -> None:
        """visible= with initial False hides widget."""

        @window(title="Test")
        class MainWindow(Window):
            _show: Variable[bool] = new(False)
            label: QLabel = new("Hidden", visible="_show")

        w = qt.track(MainWindow())
        assert w.label.isHidden()

    def test_enabled_binding(self, qt: QtDriver) -> None:
        """enabled= binding works in Window."""

        @window(title="Test")
        class MainWindow(Window):
            _can_click: Variable[bool] = new(True)
            button: QPushButton = new("Click", enabled="_can_click")

        w = qt.track(MainWindow())
        assert w.button.isEnabled()

        w._can_click.value = False
        assert not w.button.isEnabled()

    def test_visible_expression_binding(self, qt: QtDriver) -> None:
        """visible= with expression works in Window."""

        @window(title="Test")
        class MainWindow(Window):
            _count: Variable[int] = new(5)
            label: QLabel = new("Visible when > 3", visible="{_count > 3}")

        w = qt.track(MainWindow())
        assert not w.label.isHidden()

        w._count.value = 2
        assert w.label.isHidden()


# =============================================================================
# Auto-bindings in Window
# =============================================================================


class TestWindowAutoBindings:
    """Test auto-binding feature in Window."""

    def test_auto_bind_on_lineedit(self, qt: QtDriver) -> None:
        """QLineEdit auto-binds to same-named Variable."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("Initial")
            name: QLineEdit = new()

        w = qt.track(MainWindow())
        assert_that(w.name.text()).is_equal_to("Initial")

        # Two-way: widget → variable
        w.name.setText("Updated")
        assert_that(w._name.value).is_equal_to("Updated")

    def test_explicit_bind(self, qt: QtDriver) -> None:
        """Explicit bind= overrides auto-bind."""

        @window(title="Test")
        class MainWindow(Window):
            _source: Variable[str] = new("From source")
            label: QLabel = new(bind="_source")

        w = qt.track(MainWindow())
        assert_that(w.label.text()).is_equal_to("From source")


# =============================================================================
# bind() function in Window
# =============================================================================


class TestWindowBindFunction:
    """Test bind() function works in Window."""

    def test_bind_sets_initial_value(self, qt: QtDriver) -> None:
        """bind() sets the widget's initial value."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("Hello")
            label: QLabel = new("")

            def __setup__(self) -> None:
                from qtpie import bind

                bind(self._name).to(self.label)

        w = qt.track(MainWindow())
        assert_that(w.label.text()).is_equal_to("Hello")

    def test_bind_reactive(self, qt: QtDriver) -> None:
        """bind() creates reactive connection."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("Initial")
            label: QLabel = new("")

            def __setup__(self) -> None:
                from qtpie import bind

                bind(self._name).to(self.label)

        w = qt.track(MainWindow())
        w._name.value = "Updated"
        assert_that(w.label.text()).is_equal_to("Updated")

    def test_two_way_binding(self, qt: QtDriver) -> None:
        """bind() creates two-way binding with QLineEdit."""

        @window(title="Test")
        class MainWindow(Window):
            _text: Variable[str] = new("")
            input: QLineEdit = new("")

            def __setup__(self) -> None:
                from qtpie import bind

                bind(self._text).to(self.input)

        w = qt.track(MainWindow())
        w.input.setText("User typed")
        assert_that(w._text.value).is_equal_to("User typed")


# =============================================================================
# Variable[T, W] in Window
# =============================================================================


class TestWindowVariableWidget:
    """Test Variable[T, W] feature in Window."""

    def test_variable_widget_created(self, qt: QtDriver) -> None:
        """Variable[T, W] creates the widget."""

        @window(title="Test")
        class MainWindow(Window):
            name: Variable[str, QLineEdit] = new("")

        w = qt.track(MainWindow())
        assert isinstance(w.name.widget, QLineEdit)

    def test_variable_widget_bound(self, qt: QtDriver) -> None:
        """Variable[T, W] widget is two-way bound."""

        @window(title="Test")
        class MainWindow(Window):
            name: Variable[str, QLineEdit] = new("Initial")

        w = qt.track(MainWindow())
        assert_that(w.name.widget.text()).is_equal_to("Initial")

        # Variable → widget
        w.name.value = "Updated"
        assert_that(w.name.widget.text()).is_equal_to("Updated")

        # Widget → variable
        w.name.widget.setText("Typed")
        assert_that(w.name.value).is_equal_to("Typed")

    def test_variable_widget_kwargs(self, qt: QtDriver) -> None:
        """Variable[T, W] passes kwargs to widget."""

        @window(title="Test")
        class MainWindow(Window):
            name: Variable[str, QLineEdit] = new("")(placeholderText="Enter name")

        w = qt.track(MainWindow())
        assert_that(w.name.widget.placeholderText()).is_equal_to("Enter name")

    def test_variable_widget_in_layout(self, qt: QtDriver) -> None:
        """Variable[T, W] widget is added to layout."""

        @window(title="Test")
        class MainWindow(Window):
            label: QLabel = new("Some label")  # Regular widget to ensure central widget is created
            var: Variable[str, QLineEdit] = new("")

        w = qt.track(MainWindow())
        central = w.centralWidget()
        assert central is not None
        layout = central.layout()
        assert layout is not None
        # Should find the Variable widget in the layout
        found = False
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() == w.var.widget:
                found = True
                break
        assert found, "Variable widget should be in the layout"


# =============================================================================
# Reactive window properties
# =============================================================================


class TestWindowReactiveProperties:
    """Test reactive properties in @window decorator."""

    def test_reactive_window_title(self, qt: QtDriver) -> None:
        """windowTitle='{var}' is reactive."""

        @window(windowTitle="{_title}")
        class MainWindow(Window):
            _title: Variable[str] = new("Initial Title")

        w = qt.track(MainWindow())
        assert_that(w.windowTitle()).is_equal_to("Initial Title")

        w._title.value = "Updated Title"
        assert_that(w.windowTitle()).is_equal_to("Updated Title")

    def test_reactive_title_alias(self, qt: QtDriver) -> None:
        """title='{var}' is reactive (alias for windowTitle)."""

        @window(title="{_title}")
        class MainWindow(Window):
            _title: Variable[str] = new("My App")

        w = qt.track(MainWindow())
        assert_that(w.windowTitle()).is_equal_to("My App")

        w._title.value = "New Title"
        assert_that(w.windowTitle()).is_equal_to("New Title")

    def test_reactive_title_with_expression(self, qt: QtDriver) -> None:
        """title= with expression is reactive."""

        @window(title="{_name.upper()}")
        class MainWindow(Window):
            _name: Variable[str] = new("hello")

        w = qt.track(MainWindow())
        assert_that(w.windowTitle()).is_equal_to("HELLO")

        w._name.value = "world"
        assert_that(w.windowTitle()).is_equal_to("WORLD")


# =============================================================================
# Window[T] with record bindings
# =============================================================================


class TestWindowRecordBindings:
    """Test Window[T] record binding features."""

    def test_record_fields_accessible(self, qt: QtDriver) -> None:
        """Record fields are accessible via auto-bind."""

        @dataclass
        class Config:
            name: str = ""
            value: int = 0

        @window(title="Test")
        class MainWindow(Window[Config]):
            # Auto-bind by field name
            name: QLineEdit = new()

        w = qt.track(MainWindow())
        # Set record field via observable
        w.record.name = "Test"
        assert_that(w.name.text()).is_equal_to("Test")

    def test_record_auto_bind(self, qt: QtDriver) -> None:
        """Fields auto-bind to record properties."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @window(title="Test")
        class MainWindow(Window[Person]):
            name: QLineEdit = new()
            age: QLineEdit = new()

        w = qt.track(MainWindow())
        w.record.name = "John"
        w.record.age = 30
        assert_that(w.name.text()).is_equal_to("John")
        assert_that(w.age.text()).is_equal_to("30")

    def test_record_reactive(self, qt: QtDriver) -> None:
        """Record changes update bindings."""

        @dataclass
        class User:
            username: str = ""

        @window(title="Test")
        class MainWindow(Window[User]):
            label: QLabel = new(bind="{username}")

        w = qt.track(MainWindow())
        w.record.username = "alice"
        assert_that(w.label.text()).is_equal_to("alice")

        w.record.username = "bob"
        assert_that(w.label.text()).is_equal_to("bob")


# =============================================================================
# Grid and Form layouts in Window
# =============================================================================


class TestWindowFormLayout:
    """Test form layout in Window."""

    def test_form_layout_with_labels(self, qt: QtDriver) -> None:
        """Form layout uses label= parameter."""

        @window(title="Test", layout="form")
        class MainWindow(Window):
            name: QLineEdit = new(label="Name:")
            email: QLineEdit = new(label="Email:")

        w = qt.track(MainWindow())
        central = w.centralWidget()
        assert central is not None
        layout = central.layout()
        assert isinstance(layout, QFormLayout)
        # Check row count
        assert layout.rowCount() == 2


class TestWindowGridLayout:
    """Test grid layout in Window."""

    def test_grid_layout_positions(self, qt: QtDriver) -> None:
        """Grid layout uses grid= parameter."""

        @window(title="Test", layout="grid")
        class MainWindow(Window):
            a: QLabel = new("A", grid=(0, 0))
            b: QLabel = new("B", grid=(0, 1))
            c: QLabel = new("C", grid=(1, 0))
            d: QLabel = new("D", grid=(1, 1))

        w = qt.track(MainWindow())
        central = w.centralWidget()
        assert central is not None
        layout = central.layout()
        assert isinstance(layout, QGridLayout)
        # Should have 4 items
        assert layout.count() == 4


# =============================================================================
# Signal connections in Window
# =============================================================================


class TestWindowSignals:
    """Test signal connections in Window work like Widget."""

    def test_button_clicked_lambda(self, qt: QtDriver) -> None:
        """clicked= with lambda works."""
        clicked_count = [0]

        @window(title="Test")
        class MainWindow(Window):
            button: QPushButton = new("Click", clicked=lambda: clicked_count.__setitem__(0, clicked_count[0] + 1))

        w = qt.track(MainWindow())
        w.button.click()
        assert clicked_count[0] == 1

    def test_lineedit_text_changed(self, qt: QtDriver) -> None:
        """textChanged= signal works."""
        changes: list[str] = []

        @window(title="Test")
        class MainWindow(Window):
            input: QLineEdit = new(textChanged=lambda t: changes.append(t))

        w = qt.track(MainWindow())
        w.input.setText("hello")
        assert "hello" in changes


# =============================================================================
# List and Dict repeaters in Window
# =============================================================================


class TestWindowListRepeater:
    """Test Variable[list[T], W] list repeater in Window."""

    def test_list_repeater_creates_widgets(self, qt: QtDriver) -> None:
        """Variable[list[int], QLabel] creates a label per item."""

        @window(title="Test")
        class MainWindow(Window):
            numbers: Variable[list[int], QLabel] = new([1, 2, 3])(bind="{#self}")

        w = qt.track(MainWindow())
        # Should have 3 labels - access via .widget (WidgetRepeater)
        repeater = w.numbers.widget
        assert repeater.widget_count() == 3
        assert_that(repeater.widget_at(0).text()).is_equal_to("1")
        assert_that(repeater.widget_at(1).text()).is_equal_to("2")
        assert_that(repeater.widget_at(2).text()).is_equal_to("3")

    def test_list_repeater_reactive(self, qt: QtDriver) -> None:
        """Adding items to list creates new widgets."""

        @window(title="Test")
        class MainWindow(Window):
            items: Variable[list[str], QLabel] = new(["a"])(bind="{#self}")

        w = qt.track(MainWindow())
        repeater = w.items.widget
        assert repeater.widget_count() == 1

        w.items.append("b")
        assert repeater.widget_count() == 2
        assert_that(repeater.widget_at(1).text()).is_equal_to("b")

    def test_list_repeater_with_index(self, qt: QtDriver) -> None:
        """#index placeholder works in list repeater."""

        @window(title="Test")
        class MainWindow(Window):
            items: Variable[list[str], QLabel] = new(["x", "y"])(bind="Item {#index}: {#self}")

        w = qt.track(MainWindow())
        repeater = w.items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("Item 0: x")
        assert_that(repeater.widget_at(1).text()).is_equal_to("Item 1: y")

    def test_list_repeater_with_objects(self, qt: QtDriver) -> None:
        """List of objects with property access works."""

        @dataclass
        class Item:
            name: str
            count: int

        @window(title="Test")
        class MainWindow(Window):
            items: Variable[list[Item], QLabel] = new([Item("Apple", 5), Item("Banana", 3)])(bind="{name}: {count}")

        w = qt.track(MainWindow())
        repeater = w.items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("Apple: 5")
        assert_that(repeater.widget_at(1).text()).is_equal_to("Banana: 3")


class TestWindowDictRepeater:
    """Test Variable[dict[K, V], W] dict repeater in Window."""

    def test_dict_repeater_creates_widgets(self, qt: QtDriver) -> None:
        """Variable[dict[str, int], QLabel] creates a label per entry."""

        @window(title="Test")
        class MainWindow(Window):
            scores: Variable[dict[str, int], QLabel] = new({"Alice": 100, "Bob": 85})(bind="{#key}: {#value}")

        w = qt.track(MainWindow())
        # Should have 2 labels - access via .widget (DictWidgetRepeater)
        repeater = w.scores.widget
        assert repeater.widget_count() == 2
        texts = [repeater.widget_for_key(k).text() for k in repeater.keys()]
        assert "Alice: 100" in texts
        assert "Bob: 85" in texts

    def test_dict_repeater_reactive(self, qt: QtDriver) -> None:
        """Adding entries to dict creates new widgets."""

        @window(title="Test")
        class MainWindow(Window):
            data: Variable[dict[str, int], QLabel] = new({"a": 1})(bind="{#key}={#value}")

        w = qt.track(MainWindow())
        repeater = w.data.widget
        assert repeater.widget_count() == 1

        w.data["b"] = 2
        assert repeater.widget_count() == 2

    def test_dict_repeater_with_objects(self, qt: QtDriver) -> None:
        """Dict with object values and property access works."""

        @dataclass
        class Person:
            name: str
            age: int

        @window(title="Test")
        class MainWindow(Window):
            people: Variable[dict[str, Person], QLabel] = new({"user1": Person("Alice", 30), "user2": Person("Bob", 25)})(bind="{#key} is {name}, age {age}")

        w = qt.track(MainWindow())
        repeater = w.people.widget
        texts = [repeater.widget_for_key(k).text() for k in repeater.keys()]
        assert "user1 is Alice, age 30" in texts
        assert "user2 is Bob, age 25" in texts


# =============================================================================
# list[QWidget] binding in Window
# =============================================================================


class TestWindowListWidgetBinding:
    """Test list[QWidget] = new(bind="...") in Window."""

    def test_list_widget_binding(self, qt: QtDriver) -> None:
        """list[QLabel] bound to Variable creates widgets per item."""

        @window(title="Test")
        class MainWindow(Window):
            _items: Variable[list[str]] = new(["one", "two", "three"])
            labels: list[QLabel] = new(bind="_items")

        w = qt.track(MainWindow())
        assert len(w.labels) == 3
        assert_that(w.labels[0].text()).is_equal_to("one")

    def test_list_widget_binding_reactive(self, qt: QtDriver) -> None:
        """List widget binding updates when source changes."""

        @window(title="Test")
        class MainWindow(Window):
            _items: Variable[list[str]] = new(["a"])
            labels: list[QLabel] = new(bind="_items")

        w = qt.track(MainWindow())
        assert len(w.labels) == 1

        w._items.append("b")
        assert len(w.labels) == 2

    def test_list_widget_format_binding(self, qt: QtDriver) -> None:
        """list[QLabel] with format= creates formatted labels."""

        @window(title="Test")
        class MainWindow(Window):
            _numbers: Variable[list[int]] = new([10, 20])
            labels: list[QLabel] = new(bind="_numbers", format="Value: {#self}")

        w = qt.track(MainWindow())
        assert_that(w.labels[0].text()).is_equal_to("Value: 10")
        assert_that(w.labels[1].text()).is_equal_to("Value: 20")
