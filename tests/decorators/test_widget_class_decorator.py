# IMPORTANT: If you add or change a test here, you MUST add or change a corresponding test
# in test_widget_decorator.py! These two files are meant to have parallel coverage
# for @widget_class and @widget. Do NOT add a test to only one file unless it is
# absolutely unique to that decorator. Keep them in sync!

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


def test_widget_class_labelwidget_no_init_sets_text(qtbot: QtBot) -> None:
    """Test @widget_class with QLabel and no __init__, should set text via constructor."""

    from qtpy.QtWidgets import QLabel

    @widget_class
    class LabelWidgetNoInit(QLabel):
        pass

    widget = LabelWidgetNoInit("Hello")
    qtbot.addWidget(widget)
    assert_that(widget.text()).is_equal_to("Hello")


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


def test_widget_class_labelwidget_custom_init_sets_text(qtbot: QtBot) -> None:
    """Test @widget_class with QLabel and custom __init__."""

    from qtpy.QtWidgets import QLabel

    @widget_class
    class LabelWidgetCustomInit(QLabel):
        def __init__(self, number: int) -> None:
            super().__init__(f"The number is: {number}")

    widget = LabelWidgetCustomInit(42)
    qtbot.addWidget(widget)
    assert_that(widget.text()).is_equal_to("The number is: 42")
