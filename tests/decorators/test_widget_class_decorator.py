from dataclasses import is_dataclass

from tests.decorators.widget_class_decorator_examples import (
    MultiArgWidgetClass,
    NamedWidgetClass,
    SimpleWidgetClass,
)


def test_is_not_dataclass() -> None:
    assert not is_dataclass(SimpleWidgetClass)
    assert not is_dataclass(SimpleWidgetClass())


def test_manual_init_preserved() -> None:
    widget_instance = SimpleWidgetClass(123)
    assert widget_instance.value == 123


def test_accepts_kwarg() -> None:
    widget_instance = SimpleWidgetClass(value=99)
    assert widget_instance.value == 99


def test_multi_arg_widget_class() -> None:
    widget_instance = MultiArgWidgetClass("foo", 7)
    assert widget_instance.name == "foo"
    assert widget_instance.count == 7


def test_layout_mode_default_class() -> None:
    widget_instance = SimpleWidgetClass()
    assert isinstance(widget_instance, SimpleWidgetClass)


def test_named_widget_class_name() -> None:
    widget_instance = NamedWidgetClass()
    assert widget_instance.name == "CustomWidgetName"
