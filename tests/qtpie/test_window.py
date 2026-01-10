# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportUnknownMemberType=false
# pyright: reportUnknownLambdaType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportGeneralTypeIssues=false
"""Tests for Window with auto-layout and menu bar integration."""

from dataclasses import dataclass
from pathlib import Path
from typing import override

from assertpy import assert_that
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from qtpie import Menu, Variable, Widget, Window, menu, new, widget, window
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

        @menu(text="&File")
        class FileMenu(Menu):
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

        @menu(text="&File")
        class FileMenu(Menu):
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

        @menu(text="&File")
        class FileMenu(Menu):
            pass

        @menu(text="&Edit")
        class EditMenu(Menu):
            pass

        @menu(text="&Help")
        class HelpMenu(Menu):
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

        @menu(text="&File")
        class FileMenu(Menu):
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

    def test_underscore_central_widget(self, qt: QtDriver) -> None:
        """_central_widget field (with underscore) becomes the central widget directly."""

        @window
        class MainWindow(Window):
            _central_widget: QLabel = new("UNDERSCORE CENTRAL")

        w = qt.track(MainWindow())
        central = w.centralWidget()
        assert_that(central).is_same_as(w._central_widget)
        assert_that(central.text()).is_equal_to("UNDERSCORE CENTRAL")

    def test_underscore_central_widget_no_container(self, qt: QtDriver) -> None:
        """With _central_widget, other widgets are NOT added to layout."""

        @window
        class MainWindow(Window):
            _central_widget: QLabel = new("Central")
            other_label: QLabel = new("Other")  # Not added to layout

        w = qt.track(MainWindow())
        central = w.centralWidget()
        # _central_widget is the central widget directly
        assert_that(central).is_same_as(w._central_widget)
        # other_label exists but not in any layout
        assert_that(w.other_label).is_not_none()
        assert_that(w.other_label.text()).is_equal_to("Other")

    def test_underscore_variable_central_widget(self, qt: QtDriver) -> None:
        """_central_widget: Variable[str, QLabel] works."""

        @window
        class MainWindow(Window):
            _central_widget: Variable[str, QLabel] = new("Initial")(bind="{#self.upper()}")

        w = qt.track(MainWindow())
        central = w.centralWidget()
        # The central widget should be the Variable's widget
        assert_that(central).is_same_as(w._central_widget.widget)
        assert_that(central.text()).is_equal_to("INITIAL")

        # Reactive update
        w._central_widget.value = "updated"
        assert_that(central.text()).is_equal_to("UPDATED")


class TestWindowIcon:
    """Tests for icon= parameter on @window decorator."""

    def test_icon_accepts_qicon(self, qt: QtDriver) -> None:
        """icon= accepts QIcon."""
        from qtpy.QtGui import QIcon, QPixmap

        pixmap = QPixmap(16, 16)
        pixmap.fill()
        test_icon = QIcon(pixmap)

        @window(icon=test_icon)
        class MainWindow(Window):
            _label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.windowIcon().isNull()).is_false()

    def test_icon_accepts_qpixmap(self, qt: QtDriver) -> None:
        """icon= accepts QPixmap."""
        from qtpy.QtGui import QPixmap

        pixmap = QPixmap(16, 16)
        pixmap.fill()

        @window(icon=pixmap)
        class MainWindow(Window):
            _label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.windowIcon().isNull()).is_false()

    def test_icon_accepts_string_path(self, qt: QtDriver, tmp_path: Path) -> None:
        """icon= accepts string file path."""
        from qtpy.QtGui import QImage

        icon_file = tmp_path / "window_icon.png"
        img = QImage(16, 16, QImage.Format.Format_ARGB32)
        img.fill(0xFF0000FF)  # Blue
        img.save(str(icon_file))

        @window(icon=str(icon_file))
        class MainWindow(Window):
            _label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.windowIcon().isNull()).is_false()

    def test_icon_accepts_standard_pixmap(self, qt: QtDriver) -> None:
        """icon= accepts QStyle.StandardPixmap."""
        from qtpy.QtWidgets import QStyle

        @window(icon=QStyle.StandardPixmap.SP_ComputerIcon)
        class MainWindow(Window):
            _label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.windowIcon().isNull()).is_false()

    def test_icon_with_title(self, qt: QtDriver) -> None:
        """icon= works together with title=."""
        from qtpy.QtGui import QIcon, QPixmap

        pixmap = QPixmap(16, 16)
        pixmap.fill()
        test_icon = QIcon(pixmap)

        @window(title="My Window", icon=test_icon)
        class MainWindow(Window):
            _label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.windowTitle()).is_equal_to("My Window")
        assert_that(w.windowIcon().isNull()).is_false()


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

        @menu(text="&File")
        class FileMenu(Menu):
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


class TestWindowRecordDecorator:
    """Test @window(record=...) decorator parameter."""

    def test_record_via_decorator(self, qt: QtDriver) -> None:
        """@window(record=...) sets initial record value."""

        @dataclass
        class Dog:
            name: str
            breed: str

        @window(record=Dog("Fido", "Lab"))
        class DogWindow(Window[Dog]):
            pass

        w = qt.track(DogWindow())
        assert_that(w.record.name).is_equal_to("Fido")
        assert_that(w.record.breed).is_equal_to("Lab")

    def test_record_via_decorator_accessible_in_setup(self, qt: QtDriver) -> None:
        """Record from decorator is available in __setup__."""
        captured_name: list[str] = []

        @dataclass
        class Dog:
            name: str
            age: int

        @window(record=Dog("Buddy", 5))
        class DogWindow(Window[Dog]):
            def __setup__(self) -> None:
                captured_name.append(self.record.name)

        qt.track(DogWindow())
        assert_that(captured_name[0]).is_equal_to("Buddy")

    def test_record_via_decorator_modifiable(self, qt: QtDriver) -> None:
        """Record from decorator can be modified."""

        @dataclass
        class Person:
            name: str
            age: int

        @window(record=Person("Alice", 30))
        class PersonWindow(Window[Person]):
            pass

        w = qt.track(PersonWindow())
        w.record.name = "Bob"
        w.record.age = 25

        assert_that(w.record.name).is_equal_to("Bob")
        assert_that(w.record.age).is_equal_to(25)

    def test_record_via_decorator_dirty_tracking(self, qt: QtDriver) -> None:
        """Record from decorator participates in dirty tracking."""

        @dataclass
        class Person:
            name: str
            age: int

        @window(record=Person("Initial", 0))
        class PersonWindow(Window[Person]):
            pass

        w = qt.track(PersonWindow())
        assert_that(w._qtpie.record_state.is_dirty.get()).is_false()

        w.record.name = "Changed"
        assert_that(w._qtpie.record_state.is_dirty.get()).is_true()

    def test_record_via_decorator_with_no_defaults(self, qt: QtDriver) -> None:
        """@window(record=...) works with types that have no default values."""

        @dataclass
        class Cat:
            name: str
            lives: int

        @window(record=Cat("Whiskers", 9))
        class CatWindow(Window[Cat]):
            pass

        w = qt.track(CatWindow())
        assert_that(w.record.name).is_equal_to("Whiskers")
        assert_that(w.record.lives).is_equal_to(9)


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
        state = w._qtpie.record_state
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
        vm = w._qtpie.view_model
        assert_that(vm._count.value).is_equal_to(42)
        assert_that(vm._name.value).is_equal_to("updated")


class TestMenuSignalConnections:
    """Test menu action signal connections in Window."""

    def test_menu_action_triggered(self, qt: QtDriver) -> None:
        """Menu actions with triggered= connect properly."""
        exit_called = False

        @menu(text="&File")
        class FileMenu(Menu):
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


# =============================================================================
# Dirty tracking in Window
# =============================================================================


class TestWindowDirtyTracking:
    """Test dirty tracking in Window matches Widget behavior."""

    def test_initially_not_dirty(self, qt: QtDriver) -> None:
        """New window's view_model is not dirty."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

        w = qt.track(MainWindow())
        assert_that(w.is_dirty).is_false()

    def test_dirty_after_change(self, qt: QtDriver) -> None:
        """view_model becomes dirty after Variable change."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

        w = qt.track(MainWindow())
        w._name.value = "changed"
        assert_that(w.is_dirty).is_true()

    def test_dirty_fields_tracks_which_changed(self, qt: QtDriver) -> None:
        """dirty_fields() returns only the changed fields."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

        w = qt.track(MainWindow())
        w._name.value = "changed"

        assert_that(w.dirty_fields).is_equal_to({"_name"})

    def test_dirty_fields_multiple(self, qt: QtDriver) -> None:
        """dirty_fields() returns all changed fields."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

        w = qt.track(MainWindow())
        w._name.value = "changed"
        w._count.value = 42

        assert_that(w.dirty_fields).is_equal_to({"_name", "_count"})

    def test_reset_dirty_clears_all(self, qt: QtDriver) -> None:
        """reset_dirty() marks all Variables as clean."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

        w = qt.track(MainWindow())
        w._name.value = "changed"
        w._count.value = 42
        assert_that(w.is_dirty).is_true()

        w.reset_dirty()
        assert_that(w.is_dirty).is_false()
        assert_that(w.dirty_fields).is_equal_to(set())

    def test_dirty_after_reset_and_change(self, qt: QtDriver) -> None:
        """After reset, changing a value makes it dirty again."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

        w = qt.track(MainWindow())
        w._name.value = "first"
        w.reset_dirty()

        w._name.value = "second"
        assert_that(w.is_dirty).is_true()


class TestWindowOnDirtyChangedHook:
    """Test on_dirty_changed lifecycle hook in Window."""

    def test_hook_fires_on_dirty(self, qt: QtDriver) -> None:
        """on_dirty_changed fires when window becomes dirty."""
        dirty_states: list[bool] = []

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        w = qt.track(MainWindow())
        w._name.value = "changed"

        assert_that(dirty_states).is_equal_to([True])

    def test_hook_fires_on_clean(self, qt: QtDriver) -> None:
        """on_dirty_changed fires when window becomes clean."""
        dirty_states: list[bool] = []

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        w = qt.track(MainWindow())
        w._name.value = "changed"
        w.reset_dirty()

        assert_that(dirty_states).is_equal_to([True, False])

    def test_hook_fires_on_transition_only(self, qt: QtDriver) -> None:
        """on_dirty_changed only fires on state transitions, not every change."""
        dirty_states: list[bool] = []

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        w = qt.track(MainWindow())
        w._name.value = "first"  # clean -> dirty
        w._name.value = "second"  # dirty -> dirty (no fire)
        w._count.value = 42  # dirty -> dirty (no fire)

        assert_that(dirty_states).is_equal_to([True])

    def test_hook_not_required(self, qt: QtDriver) -> None:
        """Window without on_dirty_changed still works."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

        w = qt.track(MainWindow())
        w._name.value = "changed"
        # Should not raise
        assert_that(w.is_dirty).is_true()


# =============================================================================
# Validation in Window
# =============================================================================


class TestWindowValidation:
    """Test validation in Window matches Widget behavior."""

    def test_window_add_validator(self, qt: QtDriver) -> None:
        """Window.add_validator adds validator to field."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        w = qt.track(MainWindow())
        assert_that(w._name.is_valid.get()).is_false()

    def test_window_is_valid_aggregates(self, qt: QtDriver) -> None:
        """Window.is_valid aggregates from all fields."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")
            _age: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

        w = qt.track(MainWindow())
        assert_that(w.is_valid).is_false()

        w._name.value = "Alice"
        assert_that(w.is_valid).is_false()  # still invalid (age)

        w._age.value = 25
        assert_that(w.is_valid).is_true()

    def test_window_validation_errors_nested_dict(self, qt: QtDriver) -> None:
        """Window.validation_errors returns {field: {validator: [errors]}}."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")
            _age: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

        w = qt.track(MainWindow())
        errors = w.validation_errors

        assert_that(errors).contains_key("_name", "_age")
        assert_that(errors["_name"]["required"]).is_equal_to(["Required"])
        assert_that(errors["_age"]["positive"]).is_equal_to(["Must be positive"])

    def test_window_validation_error_messages_flat(self, qt: QtDriver) -> None:
        """Window.validation_error_messages returns flat list."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_name", "min_len", lambda v: None if len(v) >= 3 else "Too short")

        w = qt.track(MainWindow())
        msgs = w.validation_error_messages.get()

        assert_that(msgs).contains("Required", "Too short")

    def test_window_valid_without_validators(self, qt: QtDriver) -> None:
        """Window without validators is always valid."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")
            label: QLabel = new("Hello")

        w = qt.track(MainWindow())
        assert_that(w.is_valid).is_true()

    def test_record_field_validation(self, qt: QtDriver) -> None:
        """Can add validators to record fields in Window[T]."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @window(title="Test")
        class PersonWindow(Window[Person]):
            def __setup__(self) -> None:
                self.add_validator("name", "required", lambda v: None if v else "Name required")

        w = qt.track(PersonWindow())
        assert_that(w.is_valid).is_false()

        w.record.name = "Alice"
        assert_that(w.is_valid).is_true()


class TestWindowOnValidChangedHook:
    """Test on_valid_changed lifecycle hook in Window."""

    def test_hook_fires_on_valid(self, qt: QtDriver) -> None:
        """on_valid_changed fires when validity changes."""
        valid_states: list[bool] = []

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                valid_states.append(is_valid)

        w = qt.track(MainWindow())
        # Initially invalid, but hook fires on transition only

        w._name.value = "hello"
        assert_that(valid_states).contains(True)

        w._name.value = ""
        assert_that(valid_states).contains(False)


class TestWindowIsDirty:
    """Test Window.is_dirty property (aggregates Variables AND record)."""

    def test_window_is_dirty_returns_observable(self, qt: QtDriver) -> None:
        """Window.is_dirty should return Observable[bool]."""
        from observant import Observable

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

        w = qt.track(MainWindow())
        assert_that(w.is_dirty).is_instance_of(Observable)
        assert_that(w.is_dirty.get()).is_false()

    def test_window_is_dirty_from_variables(self, qt: QtDriver) -> None:
        """Window.is_dirty becomes True when Variables change."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

        w = qt.track(MainWindow())
        assert_that(w.is_dirty.get()).is_false()

        w._name.value = "changed"
        assert_that(w.is_dirty.get()).is_true()

    def test_window_is_dirty_from_record(self, qt: QtDriver) -> None:
        """Window.is_dirty becomes True when record changes."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @window(title="Test", record=Person())
        class PersonWindow(Window[Person]):
            pass

        w = qt.track(PersonWindow())
        assert_that(w.is_dirty.get()).is_false()

        w.record.name = "Alice"
        assert_that(w.is_dirty.get()).is_true()

    def test_window_is_dirty_aggregates_both(self, qt: QtDriver) -> None:
        """Window.is_dirty aggregates Variables AND record."""

        @dataclass
        class Person:
            name: str = ""

        @window(title="Test", record=Person())
        class PersonWindow(Window[Person]):
            _extra: Variable[str] = new("")

        w = qt.track(PersonWindow())
        assert_that(w.is_dirty.get()).is_false()

        # Modify Variable
        w._extra.value = "extra"
        assert_that(w.is_dirty.get()).is_true()

        # Reset Variables
        w.reset_dirty()
        assert_that(w.is_dirty.get()).is_false()

        # Modify record
        w.record.name = "Bob"
        assert_that(w.is_dirty.get()).is_true()

    def test_window_is_dirty_reactive_binding(self, qt: QtDriver) -> None:
        """Window.is_dirty can be used in enabled= bindings."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")
            _save_btn: QPushButton = new("Save", enabled="is_dirty")

        w = qt.track(MainWindow())

        # Initially clean - button should be disabled
        assert_that(w._save_btn.isEnabled()).is_false()

        # Become dirty - button should enable
        w._name.value = "changed"
        assert_that(w._save_btn.isEnabled()).is_true()

    def test_window_is_dirty_subscribable(self, qt: QtDriver) -> None:
        """Window.is_dirty Observable can be subscribed to."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

        w = qt.track(MainWindow())
        dirty_changes: list[bool] = []
        w.is_dirty.on_change(lambda v: dirty_changes.append(v))

        w._name.value = "changed"
        assert_that(dirty_changes).contains(True)

        w.reset_dirty()
        assert_that(dirty_changes).contains(False)


class TestWindowResetDirty:
    """Test Window.reset_dirty() method."""

    def test_reset_dirty_clears_variables(self, qt: QtDriver) -> None:
        """Window.reset_dirty() clears Variable dirty state."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("")

        w = qt.track(MainWindow())
        w._name.value = "changed"
        assert_that(w.is_dirty.get()).is_true()

        w.reset_dirty()
        assert_that(w.is_dirty.get()).is_false()

    def test_reset_dirty_clears_record(self, qt: QtDriver) -> None:
        """Window.reset_dirty() clears record dirty state."""

        @dataclass
        class Person:
            name: str = ""

        @window(title="Test", record=Person())
        class PersonWindow(Window[Person]):
            pass

        w = qt.track(PersonWindow())
        w.record.name = "Alice"
        assert_that(w.is_dirty.get()).is_true()

        w.reset_dirty()
        assert_that(w.is_dirty.get()).is_false()

    def test_reset_dirty_clears_both(self, qt: QtDriver) -> None:
        """Window.reset_dirty() clears both Variables and record."""

        @dataclass
        class Person:
            name: str = ""

        @window(title="Test", record=Person())
        class PersonWindow(Window[Person]):
            _extra: Variable[str] = new("")

        w = qt.track(PersonWindow())
        w._extra.value = "extra"
        w.record.name = "Alice"
        assert_that(w.is_dirty.get()).is_true()

        w.reset_dirty()
        assert_that(w.is_dirty.get()).is_false()


# =============================================================================
# Variable Bindings in Window (Phase B) - Same as Widget
# =============================================================================


class TestWindowVariableBindingsDetection:
    """Test bare Variable[T] detection as required bindings in Window."""

    def test_bare_variable_detected_as_required(self, qt: QtDriver) -> None:
        """Bare Variable[T] (no = new()) is a required binding."""
        from qtpie import Widget, widget

        @widget
        class ChildWidget(Widget):
            count: Variable[int]  # Required

        assert "count" in ChildWidget._qtpie_config.required_bindings

        @window(title="Test")
        class MainWindow(Window):
            count: Variable[int]  # Required

        assert "count" in MainWindow._qtpie_config.required_bindings

    def test_variable_with_default_is_optional(self, qt: QtDriver) -> None:
        """Variable[T] = new(default) is optional (has a default)."""

        @window(title="Test")
        class MainWindow(Window):
            count: Variable[int] = new(0)

        assert "count" not in MainWindow._qtpie_config.required_bindings

    def test_multiple_required_bindings(self, qt: QtDriver) -> None:
        """Multiple bare Variables are all detected."""

        @window(title="Test")
        class MainWindow(Window):
            count: Variable[int]
            name: Variable[str]
            enabled: Variable[bool]

        assert MainWindow._qtpie_config.required_bindings == {"count", "name", "enabled"}

    def test_mixed_required_and_optional(self, qt: QtDriver) -> None:
        """Mix of required (bare) and optional (with default) Variables."""

        @window(title="Test")
        class MainWindow(Window):
            required_var: Variable[int]
            optional_var: Variable[str] = new("default")
            another_required: Variable[bool]

        assert MainWindow._qtpie_config.required_bindings == {"required_var", "another_required"}


class TestWindowVariableBindingsWithChildWidgets:
    """Test passing Variable bindings to child widgets from Window."""

    def test_window_to_widget_binding(self, qt: QtDriver) -> None:
        """Window can pass Variable bindings to child widgets."""
        from qtpie import Widget, widget

        @widget
        class CounterDisplay(Widget):
            count: Variable[int]  # Required
            label: QLabel = new(bind="Count: {count}")

        @window(title="Counter App")
        class App(Window):
            _my_count: Variable[int] = new(0)
            display: CounterDisplay = new(count="_my_count")
            btn: QPushButton = new("+1", clicked="on_inc")

            def on_inc(self) -> None:
                self._my_count += 1

        app = qt.track(App())

        # Initially synced
        assert app.display.count.value == 0
        assert app.display.label.text() == "Count: 0"

        # Window changes -> widget updates
        app._my_count.value = 42
        assert app.display.count.value == 42
        assert app.display.label.text() == "Count: 42"

    def test_window_to_widget_two_way_binding(self, qt: QtDriver) -> None:
        """Changes in child widget propagate back to window."""
        from qtpie import Widget, widget

        @widget
        class Editor(Widget):
            value: Variable[str]  # Required

        @window(title="Editor App")
        class App(Window):
            _text: Variable[str] = new("initial")
            editor: Editor = new(value="_text")

        app = qt.track(App())

        # Child changes -> window updates
        app.editor.value.value = "changed"
        assert app._text.value == "changed"

    def test_window_to_widget_expression_binding(self, qt: QtDriver) -> None:
        """Expression binding works from Window to child widget."""
        from qtpie import Widget, widget

        @widget
        class ConditionalWidget(Widget):
            is_enabled: Variable[bool]

        @window(title="Test")
        class App(Window):
            _items: Variable[list[str]] = new([])
            child: ConditionalWidget = new(is_enabled="{len(_items) > 0}")

        app = qt.track(App())
        assert app.child.is_enabled.value is False

        app._items.value = ["a", "b"]
        assert app.child.is_enabled.value is True

    def test_window_to_widget_literal_binding(self, qt: QtDriver) -> None:
        """Literal value binding works from Window to child widget."""
        from qtpie import Widget, widget

        @widget
        class TextWidget(Widget):
            text: Variable[str]

        @window(title="Test")
        class App(Window):
            # "Hello World" is a literal (no _ prefix, no {})
            child: TextWidget = new(text="Hello World")

        app = qt.track(App())
        assert app.child.text.value == "Hello World"

    def test_missing_required_binding_raises_error(self, qt: QtDriver) -> None:
        """Missing required binding on child widget raises error."""
        import pytest

        from qtpie import Widget, widget

        @widget
        class RequiresBinding(Widget):
            count: Variable[int]  # Required

        @window(title="Test")
        class App(Window):
            child: RequiresBinding = new()  # Missing count binding!

        with pytest.raises(TypeError, match="requires binding for 'count'"):
            App()

    def test_nested_binding_through_widgets(self, qt: QtDriver) -> None:
        """Bindings pass through nested widget hierarchy."""
        from qtpie import Widget, widget

        @widget
        class GrandChild(Widget):
            theme: Variable[str]

        @widget
        class Child(Widget):
            theme: Variable[str]  # Required
            grandchild: GrandChild = new(theme="theme")

        @window(title="Test")
        class App(Window):
            _theme: Variable[str] = new("dark")
            child: Child = new(theme="_theme")

        app = qt.track(App())
        assert app.child.grandchild.theme.value == "dark"

        # Changes propagate through the chain
        app._theme.value = "light"
        assert app.child.grandchild.theme.value == "light"


class TestWindowVariableWidgetSignalConnections:
    """Test signal connections on Variable[T, W] widgets in Window."""

    def test_signal_connection_string_handler(self, qt: QtDriver) -> None:
        """Signal connection with string handler resolves to parent window method."""
        call_count = 0

        @window(title="Test")
        class App(Window):
            _input: Variable[str, QLineEdit] = new("")(returnPressed="on_submit")  # type: ignore[type-arg]

            def on_submit(self) -> None:
                nonlocal call_count
                call_count += 1

        app = qt.track(App())
        app._input.widget.returnPressed.emit()

        assert_that(call_count).is_equal_to(1)

    def test_signal_kwargs_not_passed_to_widget(self, qt: QtDriver) -> None:
        """Signal kwargs are extracted, not passed to widget constructor."""

        @window(title="Test")
        class App(Window):
            _input: Variable[str, QLineEdit] = new("")(  # type: ignore[type-arg]
                placeholderText="Type here",
                returnPressed="on_submit",
            )

            def on_submit(self) -> None:
                pass

        # Should not raise any Qt warnings about invalid method signatures
        app = qt.track(App())
        assert_that(app._input.widget.placeholderText()).is_equal_to("Type here")

    def test_nonexistent_handler_raises_runtime_error(self, qt: QtDriver) -> None:
        """Connecting to nonexistent handler raises RuntimeError."""
        import pytest

        @window(title="Test")
        class App(Window):
            _input: Variable[str, QLineEdit] = new("")(returnPressed="nonexistent")  # type: ignore[type-arg]

        with pytest.raises(RuntimeError, match="nonexistent"):
            qt.track(App())


# =============================================================================
# Validate= parameter on Variables in Window
# =============================================================================


class TestWindowValidateParameter:
    """Test validate= parameter on Variable fields in Window (matching Widget behavior)."""

    def test_validate_single_method_name(self, qt: QtDriver) -> None:
        """validate='method_name' registers a validator."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Name required"

        w = qt.track(MainWindow())
        assert_that(w._name.is_valid.get()).is_false()

        w._name.value = "Alice"
        assert_that(w._name.is_valid.get()).is_true()

    def test_validate_list_of_method_names(self, qt: QtDriver) -> None:
        """validate=['method1', 'method2'] registers multiple validators."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("", validate=["not_empty", "min_length"])

            def not_empty(self, value: str) -> str | None:
                return None if value else "Required"

            def min_length(self, value: str) -> str | None:
                return None if len(value) >= 3 else "Min 3 chars"

        w = qt.track(MainWindow())
        assert_that(w._name.is_valid.get()).is_false()

        w._name.value = "ab"
        assert_that(w._name.is_valid.get()).is_false()  # Still too short

        w._name.value = "abc"
        assert_that(w._name.is_valid.get()).is_true()

    def test_validate_with_callable(self, qt: QtDriver) -> None:
        """validate=callable registers a callable validator."""

        @window(title="Test")
        class MainWindow(Window):
            _age: Variable[int] = new(0, validate=lambda v: None if v >= 0 else "Must be positive")

        w = qt.track(MainWindow())
        # Initial value 0 is valid (>= 0)
        assert_that(w._age.is_valid.get()).is_true()

        w._age.value = -1
        assert_that(w._age.is_valid.get()).is_false()

    def test_validate_with_tuple_explicit_name(self, qt: QtDriver) -> None:
        """validate=('name', 'method') uses explicit validator name."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("", validate=[("custom_name", "check_name")])

            def check_name(self, value: str) -> str | None:
                return None if value else "Empty"

        w = qt.track(MainWindow())
        errors = w._name.validation_errors.get()
        assert "custom_name" in errors

    def test_validate_with_tuple_callable(self, qt: QtDriver) -> None:
        """validate=('name', callable) works."""

        @window(title="Test")
        class MainWindow(Window):
            _count: Variable[int] = new(0, validate=[("positive_check", lambda v: None if v >= 0 else "Negative")])

        w = qt.track(MainWindow())
        w._count.value = -5
        errors = w._count.validation_errors.get()
        assert "positive_check" in errors

    def test_validate_mixed_formats(self, qt: QtDriver) -> None:
        """validate= supports mixed formats in list."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new(
                "",
                validate=[
                    "not_empty",  # Method name
                    lambda v: None if len(v) <= 50 else "Too long",  # Lambda
                    ("custom", "custom_check"),  # Tuple with method
                ],
            )

            def not_empty(self, v: str) -> str | None:
                return None if v else "Empty"

            def custom_check(self, v: str) -> str | None:
                return None if v.isalpha() else "Letters only"

        w = qt.track(MainWindow())
        w._name.value = "abc123"  # Has non-letters
        assert_that(w._name.is_valid.get()).is_false()

        w._name.value = "abc"
        assert_that(w._name.is_valid.get()).is_true()

    def test_validate_runs_before_setup(self, qt: QtDriver) -> None:
        """validate= validators are registered before __setup__."""
        setup_valid: list[bool] = []

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str] = new("valid", validate=lambda v: None if v else "Empty")

            def __setup__(self) -> None:
                setup_valid.append(self._name.is_valid.get())

        qt.track(MainWindow())
        assert_that(setup_valid[0]).is_true()

    def test_validate_with_widget_type(self, qt: QtDriver) -> None:
        """validate= works with Variable[T, W] (inline widget)."""

        @window(title="Test")
        class MainWindow(Window):
            _name: Variable[str, QLineEdit] = new("", validate=lambda v: None if v else "Required")

        w = qt.track(MainWindow())
        assert_that(w._name.is_valid.get()).is_false()

        w._name.value = "test"
        assert_that(w._name.is_valid.get()).is_true()


class TestWindowRefWithRequiredBinding:
    """Test ref() with required bindings in nested Window/Widget composition."""

    def test_ref_with_literal_text_and_required_binding(self, qt: QtDriver) -> None:
        """ref() with literal text + expression works with required bindings."""
        from dataclasses import dataclass

        from qtpie import ref

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @widget
        class DogDisplay(Widget):
            dog: Variable[Dog]
            name_label: QLabel = new(text=ref("Dog name: {dog.name}"))

        @window(title="Test", record=Dog("Max", 7))
        class MainWindow(Window[Dog]):
            dog_display: DogDisplay = new(dog="record")

        w = qt.track(MainWindow())
        # The ref should resolve with literal text preserved
        assert_that(w.dog_display.name_label.text()).is_equal_to("Dog name: Max")
