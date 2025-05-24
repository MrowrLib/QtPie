from dataclasses import is_dataclass

from tests.decorators.widget_decorator_examples import (
    MultiFieldWidget,
    NamedWidget,
    SimpleWidget,
)


def test_is_dataclass() -> None:
    assert is_dataclass(SimpleWidget)
    assert is_dataclass(SimpleWidget())


def test_field_defaults() -> None:
    widget_instance = SimpleWidget()
    assert widget_instance.value == 42


def test_accepts_kwarg() -> None:
    widget_instance = SimpleWidget(value=99)
    assert widget_instance.value == 99


def test_multi_field_defaults() -> None:
    widget_instance = MultiFieldWidget()
    assert widget_instance.name == "default"
    assert widget_instance.count == 0


def test_layout_mode_default() -> None:
    widget_instance = SimpleWidget()
    assert isinstance(widget_instance, SimpleWidget)


def test_named_widget_name() -> None:
    widget_instance = NamedWidget()
    assert widget_instance.name == "CustomWidgetName"
