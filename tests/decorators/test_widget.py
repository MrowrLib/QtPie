from dataclasses import is_dataclass

import pytest
from assertpy import assert_that
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QWidget

from qtpie.decorators.widget import widget, widget_class

# --- Decorated Widget Classes ---


@widget
class WidgetWithoutParentheses(QWidget):
    value: int


@widget()
class WidgetWithParentheses(QWidget):
    value: int


@widget_class
class PlainWidgetWithoutParentheses(QWidget):
    def __init__(self, value: int):
        self.value = value


@widget_class()
class PlainWidgetWithParentheses(QWidget):
    def __init__(self, value: int):
        self.value = value


# --- Shared Tests ---


@pytest.mark.parametrize(
    "widget_class,args,expected_name",
    [
        (WidgetWithoutParentheses, (1,), "WidgetWithoutParentheses"),
        (WidgetWithParentheses, (2,), "WidgetWithParentheses"),
        (PlainWidgetWithoutParentheses, (42,), "PlainWidgetWithoutParentheses"),
        (PlainWidgetWithParentheses, (99,), "PlainWidgetWithParentheses"),
    ],
)
class TestSharedWidgetBehavior:
    def test_constructor_and_object_name(
        self,
        qtbot: QtBot,
        widget_class: type[QWidget],
        args: tuple[int, ...],
        expected_name: str,
    ) -> None:
        """Test that all widgets set object name and constructor args correctly."""
        widget_instance = widget_class(*args)
        assert_that(widget_instance.objectName()).is_equal_to(expected_name)
        assert_that(widget_instance.value).is_equal_to(args[0])


# --- Decorator-Specific Tests ---


@pytest.mark.parametrize(
    "widget_class,args",
    [
        (WidgetWithoutParentheses, (1,)),
        (WidgetWithParentheses, (2,)),
    ],
)
class TestDataclassWidgets:
    def test_makes_dataclass(
        self,
        qtbot: QtBot,
        widget_class: type[QWidget],
        args: tuple[int, ...],
    ) -> None:
        widget_instance = widget_class(*args)
        assert_that(is_dataclass(widget_class)).is_true()
        assert_that(is_dataclass(widget_instance)).is_true()


@pytest.mark.parametrize(
    "widget_class,args",
    [
        (PlainWidgetWithoutParentheses, (42,)),
        (PlainWidgetWithParentheses, (99,)),
    ],
)
class TestPlainWidgets:
    def test_not_dataclass(
        self,
        qtbot: QtBot,
        widget_class: type[QWidget],
        args: tuple[int, ...],
    ) -> None:
        widget_instance = widget_class(*args)
        assert_that(is_dataclass(widget_class)).is_false()
        assert_that(is_dataclass(widget_instance)).is_false()


# --- Validation Tests ---


class TestWidgetValidation:
    def test_widget_rejects_non_qwidget(self) -> None:
        """Test that @widget decorator rejects classes that don't inherit from QWidget."""
        with pytest.raises(TypeError, match="@widget can only be applied to QWidget subclasses"):

            @widget
            class NotAWidget:  # type: ignore
                pass
