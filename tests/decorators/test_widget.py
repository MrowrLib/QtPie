from dataclasses import is_dataclass

from assertpy import assert_that

from qtpie.decorators.widget import widget


@widget
class WidgetWithoutParentheses:
    x: int


@widget()
class WidgetWithParentheses:
    x: int
    y: int


class TestWidgetWithoutParentheses:
    def test_widget_makes_dataclass(self) -> None:
        """Test that @widget decorator makes the class a dataclass."""
        # Arrange & Act
        widget_instance = WidgetWithoutParentheses(1)

        # Assert
        assert_that(widget_instance).is_instance_of(WidgetWithoutParentheses)
        assert_that(widget_instance.x).is_equal_to(1)
        assert_that(is_dataclass(WidgetWithoutParentheses)).is_true()
        assert_that(is_dataclass(widget_instance)).is_true()


class TestWidgetWithParentheses:
    def test_widget_makes_dataclass(self) -> None:
        """Test that @widget() decorator makes the class a dataclass."""
        # Arrange & Act
        widget_instance = WidgetWithParentheses(1, 2)

        # Assert
        assert_that(widget_instance).is_instance_of(WidgetWithParentheses)
        assert_that(widget_instance.x).is_equal_to(1)
        assert_that(widget_instance.y).is_equal_to(2)
        assert_that(is_dataclass(WidgetWithParentheses)).is_true()
        assert_that(is_dataclass(widget_instance)).is_true()
