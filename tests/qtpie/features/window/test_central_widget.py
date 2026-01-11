# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportOptionalMemberAccess=false
"""Tests for Window central widget setup.

Window wraps QMainWindow and creates a central widget to hold declared fields.
"""

from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton

from qtpie import Variable, Window, new, window
from qtpie.testing import QtDriver


class TestCentralWidgetBasic:
    """Basic central widget functionality."""

    def test_window_has_central_widget(self, qt: QtDriver) -> None:
        """Window creates a central widget to hold fields."""

        @window(title="Test")
        class TestWindow(Window):
            label: QLabel = new("Hello")

        w = TestWindow()
        qt.track(w)

        central = w.centralWidget()
        assert_that(central).is_not_none()

    def test_widgets_in_central_widget(self, qt: QtDriver) -> None:
        """Declared QWidget fields are added to central widget layout."""

        @window(title="Test")
        class TestWindow(Window):
            label1: QLabel = new("First")
            label2: QLabel = new("Second")

        w = TestWindow()
        qt.track(w)

        # Both labels accessible as fields
        assert_that(w.label1.text()).is_equal_to("First")
        assert_that(w.label2.text()).is_equal_to("Second")

        # Central widget has a layout
        central = w.centralWidget()
        assert_that(central.layout()).is_not_none()


class TestCentralWidgetLayouts:
    """Central widget layout types."""

    def test_vertical_layout_default(self, qt: QtDriver) -> None:
        """Default layout is vertical."""

        @window(title="Test")
        class TestWindow(Window):
            label: QLabel = new("Content")

        w = TestWindow()
        qt.track(w)

        central = w.centralWidget()
        layout = central.layout()
        assert_that(layout.objectName()).is_equal_to("")  # VBoxLayout has no name
        # Verify it's vertical by checking class name
        assert_that(type(layout).__name__).contains("VBox")

    def test_horizontal_layout(self, qt: QtDriver) -> None:
        """layout="horizontal" uses HBoxLayout."""

        @window(title="Test", layout="horizontal")
        class TestWindow(Window):
            btn1: QPushButton = new("A")
            btn2: QPushButton = new("B")

        w = TestWindow()
        qt.track(w)

        layout = w.centralWidget().layout()
        assert_that(type(layout).__name__).contains("HBox")

    def test_form_layout(self, qt: QtDriver) -> None:
        """layout="form" with label= creates form rows."""

        @window(title="Test", layout="form")
        class TestWindow(Window):
            name: QLineEdit = new(label="Name:")
            email: QLineEdit = new(label="Email:")

        w = TestWindow()
        qt.track(w)

        layout = w.centralWidget().layout()
        assert_that(type(layout).__name__).contains("Form")

    def test_grid_layout(self, qt: QtDriver) -> None:
        """layout="grid" with grid= positions widgets."""

        @window(title="Test", layout="grid")
        class TestWindow(Window):
            a: QLabel = new("A", grid=(0, 0))
            b: QLabel = new("B", grid=(0, 1))
            c: QLabel = new("C", grid=(1, 0, 1, 2))  # Span 2 columns

        w = TestWindow()
        qt.track(w)

        layout = w.centralWidget().layout()
        assert_that(type(layout).__name__).contains("Grid")


class TestVariableWidgetsInWindow:
    """Variable[T, W] fields in Window."""

    def test_variable_with_widget(self, qt: QtDriver) -> None:
        """Variable[T, W] creates widget in central widget."""

        @window(title="Test")
        class TestWindow(Window):
            _name: Variable[str, QLineEdit] = new("")

        w = TestWindow()
        qt.track(w)

        # Variable accessible
        assert_that(w._name.value).is_equal_to("")

        # Widget exists
        widget = w._name.widget
        assert_that(widget).is_instance_of(QLineEdit)

    def test_variable_widget_with_label(self, qt: QtDriver) -> None:
        """Variable[T, W] with label= in form layout."""

        @window(title="Test", layout="form")
        class TestWindow(Window):
            _name: Variable[str, QLineEdit] = new("")(label="Name:")

        w = TestWindow()
        qt.track(w)

        # Variable and widget exist
        assert_that(w._name.widget).is_instance_of(QLineEdit)


class TestWindowProperties:
    """Window decorator properties."""

    def test_window_title(self, qt: QtDriver) -> None:
        """title= sets window title."""

        @window(title="My Application")
        class TestWindow(Window):
            label: QLabel = new("Content")

        w = TestWindow()
        qt.track(w)

        assert_that(w.windowTitle()).is_equal_to("My Application")

    def test_window_name_sets_object_name(self, qt: QtDriver) -> None:
        """name= sets window objectName."""

        @window(title="Test", name="main-window")
        class TestWindow(Window):
            label: QLabel = new("Content")

        w = TestWindow()
        qt.track(w)

        assert_that(w.objectName()).is_equal_to("main-window")

    def test_window_default_object_name(self, qt: QtDriver) -> None:
        """Without name=, objectName is class name."""

        @window(title="Test")
        class MyCustomWindow(Window):
            label: QLabel = new("Content")

        w = MyCustomWindow()
        qt.track(w)

        assert_that(w.objectName()).is_equal_to("MyCustomWindow")

    def test_window_css_classes(self, qt: QtDriver) -> None:
        """classes= sets CSS classes on window."""

        @window(title="Test", classes=["dark-theme", "compact"])
        class TestWindow(Window):
            label: QLabel = new("Content")

        w = TestWindow()
        qt.track(w)

        from qtpie.styles import get_classes

        classes = get_classes(w)
        assert_that(classes).contains("dark-theme", "compact")


class TestWindowMargins:
    """Central widget layout margins."""

    def test_int_margins(self, qt: QtDriver) -> None:
        """margins=int sets uniform margins."""

        @window(title="Test", margins=20)
        class TestWindow(Window):
            label: QLabel = new("Content")

        w = TestWindow()
        qt.track(w)

        layout = w.centralWidget().layout()
        margins = layout.contentsMargins()
        assert_that(margins.left()).is_equal_to(20)
        assert_that(margins.right()).is_equal_to(20)
        assert_that(margins.top()).is_equal_to(20)
        assert_that(margins.bottom()).is_equal_to(20)

    def test_tuple_margins(self, qt: QtDriver) -> None:
        """margins=tuple sets individual margins."""

        @window(title="Test", margins=(5, 10, 15, 20))
        class TestWindow(Window):
            label: QLabel = new("Content")

        w = TestWindow()
        qt.track(w)

        layout = w.centralWidget().layout()
        margins = layout.contentsMargins()
        assert_that(margins.left()).is_equal_to(5)
        assert_that(margins.top()).is_equal_to(10)
        assert_that(margins.right()).is_equal_to(15)
        assert_that(margins.bottom()).is_equal_to(20)
