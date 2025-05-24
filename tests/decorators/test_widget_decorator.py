from dataclasses import is_dataclass

from qtpy.QtWidgets import QWidget

from qtpie.decorators.widget import widget


@widget
class DataclassWidget(QWidget):
    value: int = 42


def test_is_dataclass() -> None:
    assert is_dataclass(DataclassWidget)
    assert is_dataclass(DataclassWidget())


def test_field_defaults() -> None:
    widget_instance = DataclassWidget()
    assert widget_instance.value == 42


def test_accepts_kwarg() -> None:
    widget_instance = DataclassWidget(value=99)
    assert widget_instance.value == 99
