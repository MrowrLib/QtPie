from typing import Callable

from assertpy import assert_that
from qtpy.QtWidgets import QWidget

Decorator = Callable[..., type]


def make_decorated(decorator: Decorator, **kwargs: object) -> type[QWidget]:
    @decorator(**kwargs)
    class TestWidget(QWidget):
        value: int = 42

    return TestWidget


def assert_layout(widget: QWidget, expected_layout: type) -> None:
    assert_that(widget.layout()).is_instance_of(expected_layout)
