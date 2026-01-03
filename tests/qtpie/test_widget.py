# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportUnknownMemberType=false
"""Tests for Widget with auto-layout."""

from assertpy import assert_that
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


class TestWidgetBasicLayout:
    """Test Widget auto-layout functionality."""

    def test_vertical_layout_default(self, qt: QtDriver) -> None:
        """Widget uses vertical layout by default."""

        @widget
        class MyWidget(Widget):
            _label: QLabel = new("Hello")
            _button: QPushButton = new("Click")

        w = qt.track(MyWidget())
        assert_that(w.layout()).is_instance_of(QVBoxLayout)

    def test_horizontal_layout(self, qt: QtDriver) -> None:
        """Widget can use horizontal layout."""

        @widget(layout="horizontal")
        class MyWidget(Widget):
            _label: QLabel = new("Hello")
            _button: QPushButton = new("Click")

        w = qt.track(MyWidget())
        assert_that(w.layout()).is_instance_of(QHBoxLayout)

    def test_no_layout(self, qt: QtDriver) -> None:
        """Widget with layout=None has no layout."""

        @widget(layout=None)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.layout()).is_none()

    def test_widgets_added_in_order(self, qt: QtDriver) -> None:
        """Child widgets are added to layout in field definition order."""

        @widget
        class MyWidget(Widget):
            _first: QLabel = new("First")
            _second: QLabel = new("Second")
            _third: QLabel = new("Third")

        w = qt.track(MyWidget())
        layout = w.layout()
        assert_that(layout.count()).is_equal_to(3)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w._first)
        assert_that(layout.itemAt(1).widget()).is_equal_to(w._second)
        assert_that(layout.itemAt(2).widget()).is_equal_to(w._third)


class TestWidgetMargins:
    """Test Widget layout margins."""

    def test_int_margins(self, qt: QtDriver) -> None:
        """Integer margins apply to all sides."""

        @widget(margins=10)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        margins = w.layout().contentsMargins()
        assert_that(margins.left()).is_equal_to(10)
        assert_that(margins.top()).is_equal_to(10)
        assert_that(margins.right()).is_equal_to(10)
        assert_that(margins.bottom()).is_equal_to(10)

    def test_tuple_margins(self, qt: QtDriver) -> None:
        """Tuple margins apply to (left, top, right, bottom)."""

        @widget(margins=(1, 2, 3, 4))
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        margins = w.layout().contentsMargins()
        assert_that(margins.left()).is_equal_to(1)
        assert_that(margins.top()).is_equal_to(2)
        assert_that(margins.right()).is_equal_to(3)
        assert_that(margins.bottom()).is_equal_to(4)


class TestWidgetLayoutExclusion:
    """Test excluding widgets from layout."""

    def test_exclude_from_layout(self, qt: QtDriver) -> None:
        """Widgets with layout=False are not added to layout."""

        @widget
        class MyWidget(Widget):
            _visible: QLabel = new("Visible")
            _hidden: QLabel = new("Hidden", layout=False)
            _also_visible: QLabel = new("Also Visible")

        w = qt.track(MyWidget())
        layout = w.layout()

        # Only 2 widgets in layout
        assert_that(layout.count()).is_equal_to(2)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w._visible)
        assert_that(layout.itemAt(1).widget()).is_equal_to(w._also_visible)

        # But all widgets exist as attributes
        assert_that(w._hidden).is_not_none()
        assert_that(w._hidden.text()).is_equal_to("Hidden")


class TestWidgetWithVariables:
    """Test Widget with Variable fields."""

    def test_variable_fields_work(self, qt: QtDriver) -> None:
        """Variable fields work in Widget."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(0)
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        w._count = 42  # Direct assignment works
        assert_that(w._count.value).is_equal_to(42)

    def test_variables_not_added_to_layout(self, qt: QtDriver) -> None:
        """Variable fields are not added to layout (not QWidgets)."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(0)
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        layout = w.layout()
        # Only the QLabel should be in the layout
        assert_that(layout.count()).is_equal_to(1)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w._label)


class TestWidgetSetup:
    """Test Widget __setup__ hook."""

    def test_setup_called(self, qt: QtDriver) -> None:
        """__setup__ is called after layout is ready."""
        setup_called = False

        @widget
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

            def __setup__(self) -> None:
                nonlocal setup_called
                setup_called = True
                # Layout should be ready
                assert self.layout() is not None
                assert self._label.text() == "Hello"

        qt.track(MyWidget())
        assert_that(setup_called).is_true()


class TestNonQWidgetFields:
    """Test non-QWidget field instantiation."""

    def test_non_qwidget_instantiated(self, qt: QtDriver) -> None:
        """Non-QWidget types are instantiated with args/kwargs."""

        class Config:
            def __init__(self, name: str = "default") -> None:
                self.name = name

        @widget
        class MyWidget(Widget):
            _config: Config = new(name="custom")
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w._config.name).is_equal_to("custom")

    def test_layout_kwarg_passed_to_non_qwidget(self, qt: QtDriver) -> None:
        """layout= is passed through to non-QWidget constructors."""

        class Config:
            def __init__(self, **kwargs: object) -> None:
                self.kwargs = kwargs

        @widget
        class MyWidget(Widget):
            # layout= is NOT a QtPie kwarg for non-QWidgets, so it passes through
            _config: Config = new(layout=123)
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        # layout SHOULD be in kwargs - only consumed for QWidget types
        assert_that(w._config.kwargs).contains_key("layout")
        assert_that(w._config.kwargs["layout"]).is_equal_to(123)
