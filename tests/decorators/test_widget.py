from dataclasses import is_dataclass

from assertpy import assert_that

from qtpie.decorators.widget import widget


@widget
class DummyWidget:
    x: int
    y: int


class TestWidget:
    def test_widget_makes_dataclass(self) -> None:
        """Test that @widget decorator makes the class a dataclass."""
        # Arrange & Act
        dummy = DummyWidget(1, 2)

        # Assert
        assert_that(dummy).is_instance_of(DummyWidget)
        assert_that(dummy.x).is_equal_to(1)
        assert_that(dummy.y).is_equal_to(2)
        assert_that(is_dataclass(DummyWidget)).is_true()
        assert_that(is_dataclass(dummy)).is_true()
