from dataclasses import is_dataclass

from qtpy.QtWidgets import QWidget

from qtpie.decorators.widget import widget_class


@widget_class
class PlainWidget(QWidget):
    def __init__(self, value: int = 42) -> None:
        self.value = value


def test_is_not_dataclass() -> None:
    assert not is_dataclass(PlainWidget)
    assert not is_dataclass(PlainWidget())


def test_manual_init_preserved() -> None:
    widget_instance = PlainWidget(123)
    assert widget_instance.value == 123


def test_accepts_kwarg() -> None:
    widget_instance = PlainWidget(value=99)
    assert widget_instance.value == 99
