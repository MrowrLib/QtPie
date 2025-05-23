from dataclasses import is_dataclass

import pytest
from assertpy import assert_that
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QWidget

from qtpie.decorators.widget import widget, widget_class

# --- Decorated Widget Classes ---


# @widget-decorated widgets


@widget
class WidgetWithoutParentheses(QWidget):
    value: int


@widget()
class WidgetWithParentheses(QWidget):
    value_x: int
    value_y: int


# @widget_class-decorated widgets


@widget_class
class PlainWidgetWithoutParentheses(QWidget):
    def __init__(self, value: int):
        self.value = value


@widget_class()
class PlainWidgetWithParentheses(QWidget):
    def __init__(self, value_x: int, value_y: int):
        self.value_x = value_x
        self.value_y = value_y


# --- Tests ---


class TestWidgetWithoutParentheses:
    def test_widget_makes_dataclass(self, qtbot: QtBot) -> None:
        """Test that @widget decorator makes the class a dataclass."""
        # Arrange & Act
        widget_instance = WidgetWithoutParentheses(1)

        # Assert
        assert_that(widget_instance).is_instance_of(WidgetWithoutParentheses)
        assert_that(widget_instance.value).is_equal_to(1)
        assert_that(is_dataclass(WidgetWithoutParentheses)).is_true()
        assert_that(is_dataclass(widget_instance)).is_true()

    def test_widget_sets_object_name(self, qtbot: QtBot) -> None:
        """Test that @widget decorator sets the object name to the class name."""
        # Arrange & Act
        widget_instance = WidgetWithoutParentheses(1)

        # Assert
        assert_that(widget_instance.objectName()).is_equal_to("WidgetWithoutParentheses")


class TestWidgetWithParentheses:
    def test_widget_makes_dataclass(self, qtbot: QtBot) -> None:
        """Test that @widget() decorator makes the class a dataclass."""
        # Arrange & Act
        widget_instance = WidgetWithParentheses(1, 2)

        # Assert
        assert_that(widget_instance).is_instance_of(WidgetWithParentheses)
        assert_that(widget_instance.value_x).is_equal_to(1)
        assert_that(widget_instance.value_y).is_equal_to(2)
        assert_that(is_dataclass(WidgetWithParentheses)).is_true()
        assert_that(is_dataclass(widget_instance)).is_true()

    def test_widget_sets_object_name(self, qtbot: QtBot) -> None:
        """Test that @widget() decorator sets the object name to the class name."""
        # Arrange & Act
        widget_instance = WidgetWithParentheses(1, 2)

        # Assert
        assert_that(widget_instance.objectName()).is_equal_to("WidgetWithParentheses")


@pytest.mark.parametrize(
    "widget_class,args,expected_name",
    [
        (WidgetWithoutParentheses, (1,), "WidgetWithoutParentheses"),
        (WidgetWithParentheses, (1, 2), "WidgetWithParentheses"),
        (PlainWidgetWithoutParentheses, (42,), "PlainWidgetWithoutParentheses"),
        (PlainWidgetWithParentheses, (1, 2), "PlainWidgetWithParentheses"),
    ],
)
class TestSharedWidgetBehavior:
    def test_sets_object_name(self, qtbot: QtBot, widget_class, args, expected_name):
        widget_instance = widget_class(*args)
        assert_that(widget_instance.objectName()).is_equal_to(expected_name)


@pytest.mark.parametrize(
    "widget_class,args",
    [
        (WidgetWithoutParentheses, (1,)),
        (WidgetWithParentheses, (1, 2)),
    ],
)
class TestDataclassWidgets:
    def test_makes_dataclass(self, qtbot: QtBot, widget_class, args):
        widget_instance = widget_class(*args)
        assert_that(is_dataclass(widget_class)).is_true()
        assert_that(is_dataclass(widget_instance)).is_true()


@pytest.mark.parametrize(
    "widget_class,args",
    [
        (PlainWidgetWithoutParentheses, (42,)),
        (PlainWidgetWithParentheses, (1, 2)),
    ],
)
class TestPlainWidgets:
    def test_not_dataclass(self, qtbot: QtBot, widget_class, args):
        widget_instance = widget_class(*args)
        assert_that(is_dataclass(widget_class)).is_false()
        assert_that(is_dataclass(widget_instance)).is_false()


class TestWidgetValidation:
    def test_widget_rejects_non_qwidget(self) -> None:
        """Test that @widget decorator rejects classes that don't inherit from QWidget."""
        # Arrange & Act & Assert
        with pytest.raises(TypeError, match="@widget can only be applied to QWidget subclasses"):

            @widget
            class NotAWidget:  # type: ignore
                pass
