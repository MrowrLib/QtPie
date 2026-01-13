# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportUnknownMemberType=false
"""Tests for Widget with auto-layout."""

from pathlib import Path

from assertpy import assert_that
from qtpy.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

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

    def test_exclude_variable_widget_from_layout(self, qt: QtDriver) -> None:
        """Variable[T, W] with layout=False excludes widget from layout."""
        from qtpy.QtWidgets import QLineEdit

        @widget
        class MyWidget(Widget):
            _visible: QLabel = new("Visible")
            _name: Variable[str, QLineEdit] = new("test")(layout=False)
            _also_visible: QLabel = new("Also Visible")

        w = qt.track(MyWidget())
        layout = w.layout()

        # Only 2 widgets in layout (labels, not the Variable's QLineEdit)
        assert_that(layout.count()).is_equal_to(2)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w._visible)
        assert_that(layout.itemAt(1).widget()).is_equal_to(w._also_visible)

        # But the Variable widget exists and works
        assert_that(w._name.widget).is_not_none()
        assert_that(w._name.widget.text()).is_equal_to("test")


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

    def test_bind_kwarg_passed_to_non_qwidget(self, qt: QtDriver) -> None:
        """bind= is passed through to non-QWidget constructors."""

        class Config:
            def __init__(self, **kwargs: object) -> None:
                self.kwargs = kwargs

        @widget
        class MyWidget(Widget):
            # bind= is NOT a QtPie kwarg for non-QWidgets, so it passes through
            _config: Config = new(bind="some_value")
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        # bind SHOULD be in kwargs - only consumed for QWidget types
        assert_that(w._config.kwargs).contains_key("bind")
        assert_that(w._config.kwargs["bind"]).is_equal_to("some_value")


class TestWidgetDecoratorRequired:
    """Test that @widget decorator is required."""

    def test_missing_decorator_raises_error(self) -> None:
        """Widget without @widget raises TypeError on instantiation."""
        import pytest

        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        with pytest.raises(TypeError) as exc_info:
            MyWidget()

        assert "must be decorated with @widget" in str(exc_info.value)
        assert "MyWidget" in str(exc_info.value)


class TestSignalConnections:
    """Test declarative signal connections."""

    def test_signal_with_lambda(self, qt: QtDriver) -> None:
        """Signal connected to lambda."""
        clicked = False

        def on_click() -> None:
            nonlocal clicked
            clicked = True

        @widget
        class MyWidget(Widget):
            _btn: QPushButton = new("Click", clicked=on_click)

        w = qt.track(MyWidget())
        w._btn.click()
        assert_that(clicked).is_true()

    def test_signal_with_method_name(self, qt: QtDriver) -> None:
        """Signal connected to method by name."""

        @widget
        class MyWidget(Widget):
            _btn: QPushButton = new("Click", clicked="on_clicked")
            was_clicked: bool = False

            def on_clicked(self) -> None:
                self.was_clicked = True

        w = qt.track(MyWidget())
        w._btn.click()
        assert_that(w.was_clicked).is_true()

    def test_signal_missing_method_raises(self) -> None:
        """Missing method name raises AttributeError."""
        import pytest

        @widget
        class MyWidget(Widget):
            _btn: QPushButton = new("Click", clicked="nonexistent_method")

        with pytest.raises(AttributeError) as exc_info:
            MyWidget()

        assert "nonexistent_method" in str(exc_info.value)

    def test_multiple_signals(self, qt: QtDriver) -> None:
        """Multiple signals can be connected."""
        pressed_count = 0
        released_count = 0

        @widget
        class MyWidget(Widget):
            _btn: QPushButton = new(
                "Click",
                pressed=lambda: inc_pressed(),
                released=lambda: inc_released(),
            )

        def inc_pressed() -> None:
            nonlocal pressed_count
            pressed_count += 1

        def inc_released() -> None:
            nonlocal released_count
            released_count += 1

        w = qt.track(MyWidget())
        w._btn.pressed.emit()
        w._btn.released.emit()

        assert_that(pressed_count).is_equal_to(1)
        assert_that(released_count).is_equal_to(1)


class TestWidgetProps:
    """Test @widget decorator kwargs become setXXX() calls."""

    def test_window_title(self, qt: QtDriver) -> None:
        """windowTitle kwarg calls setWindowTitle()."""

        @widget(windowTitle="My Window")
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.windowTitle()).is_equal_to("My Window")

    def test_title_alias(self, qt: QtDriver) -> None:
        """title kwarg is alias for windowTitle."""

        @widget(title="My Window")
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.windowTitle()).is_equal_to("My Window")

    def test_minimum_size(self, qt: QtDriver) -> None:
        """minimumWidth/minimumHeight kwargs work."""

        @widget(minimumWidth=400, minimumHeight=300)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.minimumWidth()).is_equal_to(400)
        assert_that(w.minimumHeight()).is_equal_to(300)

    def test_multiple_props(self, qt: QtDriver) -> None:
        """Multiple props all applied."""

        @widget(windowTitle="Test", toolTip="A tooltip")
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.windowTitle()).is_equal_to("Test")
        assert_that(w.toolTip()).is_equal_to("A tooltip")

    def test_invalid_prop_raises(self) -> None:
        """Invalid prop name raises AttributeError."""
        import pytest

        @widget(notARealProperty="value")
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        with pytest.raises(AttributeError) as exc_info:
            MyWidget()

        assert "setNotARealProperty" in str(exc_info.value)
        assert "notARealProperty" in str(exc_info.value)


class TestNewFieldWidgetProps:
    """Test new() kwargs become setXXX() calls on child QWidgets."""

    def test_new_with_tooltip(self, qt: QtDriver) -> None:
        """new(toolTip=...) calls setToolTip() on the widget."""

        @widget
        class MyWidget(Widget):
            label: QLabel = new("Hello", toolTip="This is a label")

        w = qt.track(MyWidget())
        assert_that(w.label.toolTip()).is_equal_to("This is a label")

    def test_new_with_style_sheet(self, qt: QtDriver) -> None:
        """new(styleSheet=...) calls setStyleSheet() on the widget."""

        @widget
        class MyWidget(Widget):
            label: QLabel = new("Hello", styleSheet="color: red;")

        w = qt.track(MyWidget())
        assert_that(w.label.styleSheet()).is_equal_to("color: red;")

    def test_new_with_multiple_props(self, qt: QtDriver) -> None:
        """Multiple props all applied to child widget."""

        @widget
        class MyWidget(Widget):
            label: QLabel = new("Hello", toolTip="Tip", styleSheet="color: blue;")

        w = qt.track(MyWidget())
        assert_that(w.label.toolTip()).is_equal_to("Tip")
        assert_that(w.label.styleSheet()).is_equal_to("color: blue;")

    def test_new_with_enabled_false(self, qt: QtDriver) -> None:
        """new(enabled=False) calls setEnabled(False)."""

        @widget
        class MyWidget(Widget):
            label: QLabel = new("Disabled", enabled=False)

        w = qt.track(MyWidget())
        assert_that(w.label.isEnabled()).is_false()

    def test_new_with_visible_false(self, qt: QtDriver) -> None:
        """new(visible=False) calls setVisible(False)."""

        @widget
        class MyWidget(Widget):
            label: QLabel = new("Hidden", visible=False)

        w = qt.track(MyWidget())
        assert_that(w.label.isVisible()).is_false()

    def test_new_with_title_alias(self, qt: QtDriver) -> None:
        """new(title=...) is alias for windowTitle."""

        @widget
        class MyWidget(Widget):
            label: QLabel = new("Hello", title="My Label")

        w = qt.track(MyWidget())
        assert_that(w.label.windowTitle()).is_equal_to("My Label")

    def test_new_with_stylesheet_alias(self, qt: QtDriver) -> None:
        """new(stylesheet=...) is alias for styleSheet (lowercase convenience)."""

        @widget
        class MyWidget(Widget):
            label: QLabel = new("Hello", stylesheet="color: green;")

        w = qt.track(MyWidget())
        assert_that(w.label.styleSheet()).is_equal_to("color: green;")


class TestWidgetDecoratorAliases:
    """Test @widget decorator convenience aliases."""

    def test_widget_stylesheet_alias(self, qt: QtDriver) -> None:
        """@widget(stylesheet=...) is alias for styleSheet."""

        @widget(stylesheet="background: yellow;")
        class MyWidget(Widget):
            label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.styleSheet()).is_equal_to("background: yellow;")


class TestWidgetRefWithRequiredBinding:
    """Test ref() with required bindings in nested Widget composition."""

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

        @widget(record=Dog("Rover", 5))
        class ParentWidget(Widget[Dog]):
            dog_display: DogDisplay = new(dog="record")

        parent = qt.track(ParentWidget())
        # The ref should resolve with literal text preserved
        assert_that(parent.dog_display.name_label.text()).is_equal_to("Dog name: Rover")


class TestWidgetIcon:
    """Tests for icon= parameter on @widget decorator."""

    def test_icon_accepts_qicon(self, qt: QtDriver) -> None:
        """icon= accepts QIcon."""
        from qtpy.QtGui import QIcon, QPixmap

        pixmap = QPixmap(16, 16)
        pixmap.fill()
        test_icon = QIcon(pixmap)

        @widget(icon=test_icon)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.windowIcon().isNull()).is_false()

    def test_icon_accepts_qpixmap(self, qt: QtDriver) -> None:
        """icon= accepts QPixmap."""
        from qtpy.QtGui import QPixmap

        pixmap = QPixmap(16, 16)
        pixmap.fill()

        @widget(icon=pixmap)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.windowIcon().isNull()).is_false()

    def test_icon_accepts_string_path(self, qt: QtDriver, tmp_path: Path) -> None:
        """icon= accepts string file path."""
        from qtpy.QtGui import QImage

        icon_file = tmp_path / "widget_icon.png"
        img = QImage(16, 16, QImage.Format.Format_ARGB32)
        img.fill(0xFF00FF00)  # Green
        img.save(str(icon_file))

        @widget(icon=str(icon_file))
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.windowIcon().isNull()).is_false()

    def test_icon_accepts_standard_pixmap(self, qt: QtDriver) -> None:
        """icon= accepts QStyle.StandardPixmap."""
        from qtpy.QtWidgets import QStyle

        @widget(icon=QStyle.StandardPixmap.SP_FileIcon)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.windowIcon().isNull()).is_false()

    def test_icon_with_title(self, qt: QtDriver) -> None:
        """icon= works together with title=."""
        from qtpy.QtGui import QIcon, QPixmap

        pixmap = QPixmap(16, 16)
        pixmap.fill()
        test_icon = QIcon(pixmap)

        @widget(title="My Widget", icon=test_icon)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(MyWidget())
        assert_that(w.windowTitle()).is_equal_to("My Widget")
        assert_that(w.windowIcon().isNull()).is_false()

    def test_icon_string_resolved_at_runtime(self, qt: QtDriver, tmp_path: Path) -> None:
        """icon= string path is resolved at instance creation, not at class definition.

        This ensures Qt resource paths like ':/icon.png' work even when the
        resource is registered after the class is defined.
        """
        from qtpy.QtGui import QImage

        # Create icon file AFTER class definition
        icon_file = tmp_path / "deferred_widget_icon.png"

        # Define class with path to file that doesn't exist yet
        @widget(icon=str(icon_file))
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

        # Now create the icon file
        img = QImage(16, 16, QImage.Format.Format_ARGB32)
        img.fill(0xFF00FF00)  # Green
        img.save(str(icon_file))

        # Icon should be resolved now at instantiation time
        w = qt.track(MyWidget())
        assert_that(w.windowIcon().isNull()).is_false()
