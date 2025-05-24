from dataclasses import is_dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QWidget

from qtpie.decorators.widget import widget_class


def test_is_not_dataclass() -> None:
    @widget_class
    class SimpleWidgetClass(QWidget):
        def __init__(self, value: int = 42) -> None:
            self.value = value

    assert_that(is_dataclass(SimpleWidgetClass)).is_false()
    assert_that(is_dataclass(SimpleWidgetClass())).is_false()


def test_manual_init_preserved() -> None:
    @widget_class
    class SimpleWidgetClass(QWidget):
        def __init__(self, value: int = 42) -> None:
            self.value = value

    widget_instance = SimpleWidgetClass(123)
    assert_that(widget_instance.value).is_equal_to(123)


def test_accepts_kwarg() -> None:
    @widget_class
    class SimpleWidgetClass(QWidget):
        def __init__(self, value: int = 42) -> None:
            self.value = value

    widget_instance = SimpleWidgetClass(value=99)
    assert_that(widget_instance.value).is_equal_to(99)


def test_multi_arg_widget_class() -> None:
    @widget_class
    class MultiArgWidgetClass(QWidget):
        def __init__(self, name: str, count: int) -> None:
            self.name = name
            self.count = count

    widget_instance = MultiArgWidgetClass("foo", 7)
    assert_that(widget_instance.name).is_equal_to("foo")
    assert_that(widget_instance.count).is_equal_to(7)


def test_layout_mode_vertical_class() -> None:
    from qtpy.QtWidgets import QVBoxLayout

    @widget_class(layout="vertical")
    class VerticalWidgetClass(QWidget):
        pass

    widget_instance = VerticalWidgetClass()
    assert_that(widget_instance.layout()).is_instance_of(QVBoxLayout)


def test_layout_mode_horizontal_class() -> None:
    from qtpy.QtWidgets import QHBoxLayout

    @widget_class(layout="horizontal")
    class HorizontalWidgetClass(QWidget):
        pass

    widget_instance = HorizontalWidgetClass()
    assert_that(widget_instance.layout()).is_instance_of(QHBoxLayout)


def test_layout_mode_grid_class() -> None:
    from qtpy.QtWidgets import QGridLayout

    @widget_class(layout="grid")
    class GridWidgetClass(QWidget):
        pass

    widget_instance = GridWidgetClass()
    assert_that(widget_instance.layout()).is_instance_of(QGridLayout)


def test_layout_mode_form_class() -> None:
    from qtpy.QtWidgets import QFormLayout

    @widget_class(layout="form")
    class FormWidgetClass(QWidget):
        pass

    widget_instance = FormWidgetClass()
    assert_that(widget_instance.layout()).is_instance_of(QFormLayout)


def test_named_widget_class_name() -> None:
    @widget_class
    class NamedWidgetClass(QWidget):
        def __init__(self, name: str = "CustomWidgetName") -> None:
            self.name = name

    widget_instance = NamedWidgetClass()
    assert widget_instance.name == "CustomWidgetName"
