from dataclasses import is_dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QWidget

from qtpie.decorators.widget import widget


def test_is_dataclass() -> None:
    @widget
    class SimpleWidget(QWidget):
        value: int = 42

    assert_that(is_dataclass(SimpleWidget)).is_true()
    assert_that(is_dataclass(SimpleWidget())).is_true()


def test_field_defaults() -> None:
    @widget
    class SimpleWidget(QWidget):
        value: int = 42

    widget_instance = SimpleWidget()
    assert_that(widget_instance.value).is_equal_to(42)


def test_accepts_kwarg() -> None:
    @widget
    class SimpleWidget(QWidget):
        value: int = 42

    widget_instance = SimpleWidget(value=99)
    assert_that(widget_instance.value).is_equal_to(99)


def test_multi_field_defaults() -> None:
    @widget
    class MultiFieldWidget(QWidget):
        name: str = "default"
        count: int = 0

    widget_instance = MultiFieldWidget()
    assert_that(widget_instance.name).is_equal_to("default")
    assert_that(widget_instance.count).is_equal_to(0)


def test_layout_mode_vertical() -> None:
    from qtpy.QtWidgets import QVBoxLayout

    @widget(layout="vertical")
    class VerticalWidget(QWidget):
        pass

    widget_instance = VerticalWidget()
    assert_that(widget_instance.layout()).is_instance_of(QVBoxLayout)


def test_layout_mode_horizontal() -> None:
    from qtpy.QtWidgets import QHBoxLayout

    @widget(layout="horizontal")
    class HorizontalWidget(QWidget):
        pass

    widget_instance = HorizontalWidget()
    assert_that(widget_instance.layout()).is_instance_of(QHBoxLayout)


def test_layout_mode_grid() -> None:
    from qtpy.QtWidgets import QGridLayout

    @widget(layout="grid")
    class GridWidget(QWidget):
        pass

    widget_instance = GridWidget()
    assert_that(widget_instance.layout()).is_instance_of(QGridLayout)


def test_layout_mode_form() -> None:
    from qtpy.QtWidgets import QFormLayout

    @widget(layout="form")
    class FormWidget(QWidget):
        pass

    widget_instance = FormWidget()
    assert_that(widget_instance.layout()).is_instance_of(QFormLayout)


def test_named_widget_name() -> None:
    @widget
    class NamedWidget(QWidget):
        name: str = "CustomWidgetName"

    widget_instance = NamedWidget()
    assert_that(widget_instance.name).is_equal_to("CustomWidgetName")


def test_classes_default_empty() -> None:
    from qtpie.styles.classes import get_classes

    @widget
    class NoClassWidget(QWidget):
        pass

    widget_instance = NoClassWidget()
    assert_that(get_classes(widget_instance)).is_empty()


def test_classes_explicit() -> None:
    from qtpie.styles.classes import get_classes

    @widget(classes=["foo", "bar"])
    class WithClassWidget(QWidget):
        pass

    widget_instance = WithClassWidget()
    assert_that(get_classes(widget_instance)).is_equal_to(["foo", "bar"])
