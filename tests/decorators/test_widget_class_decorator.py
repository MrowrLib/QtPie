from assertpy import assert_that
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QVBoxLayout, QWidget

from qtpie.decorators.widget import widget_class


def test_widget_class_no_init_sets_up_qwidget(qtbot: QtBot) -> None:
    """Test @widget_class with no __init__ (should auto-call QWidget.__init__)."""

    @widget_class
    class NoInitWidget(QWidget):
        pass

    widget = NoInitWidget()
    qtbot.addWidget(widget)
    assert_that(widget.objectName()).is_equal_to("NoInitWidget")
    assert_that(widget.layout()).is_instance_of(QVBoxLayout)


def test_widget_class_custom_init_calls_super(qtbot: QtBot) -> None:
    """Test @widget_class with custom __init__ that calls super().__init__()."""

    @widget_class
    class CustomInitWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()

    widget = CustomInitWidget()
    qtbot.addWidget(widget)
    assert_that(widget.objectName()).is_equal_to("CustomInitWidget")
    assert_that(widget.layout()).is_instance_of(QVBoxLayout)
