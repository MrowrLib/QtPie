"""Tests for the @slot decorator."""

from assertpy import assert_that
from qtpy.QtWidgets import QWidget

from qtpie import slot, widget
from qtpie.testing import QtDriver


class TestSlotBasics:
    """Basic @slot functionality."""

    def test_slot_detects_async_function(self, qt: QtDriver) -> None:
        """@slot should detect async functions."""
        _ = qt

        @slot
        async def my_async_func() -> None:
            pass

        # asyncSlot wraps the function, so it's no longer a coroutine function
        # but it should be callable
        assert_that(my_async_func).is_not_none()
        assert_that(callable(my_async_func)).is_true()

    def test_slot_passes_through_sync_function(self, qt: QtDriver) -> None:
        """@slot should pass through sync functions unchanged."""
        _ = qt

        @slot
        def my_sync_func() -> str:
            return "hello"

        result = my_sync_func()
        assert_that(result).is_equal_to("hello")

    def test_slot_without_parens(self, qt: QtDriver) -> None:
        """@slot without parentheses should work."""
        _ = qt

        @slot
        async def handler() -> None:
            pass

        assert_that(handler).is_not_none()

    def test_slot_with_empty_parens(self, qt: QtDriver) -> None:
        """@slot() with empty parentheses should work."""
        _ = qt

        @slot()
        async def handler() -> None:
            pass

        assert_that(handler).is_not_none()

    def test_slot_with_type_args(self, qt: QtDriver) -> None:
        """@slot(str) with type arguments should work."""
        _ = qt

        @slot(str)
        async def handler(text: str) -> None:
            pass

        assert_that(handler).is_not_none()

    def test_slot_with_multiple_type_args(self, qt: QtDriver) -> None:
        """@slot(str, int) with multiple type arguments should work."""
        _ = qt

        @slot(str, int)
        async def handler(text: str, count: int) -> None:
            pass

        assert_that(handler).is_not_none()


class TestSlotOnWidget:
    """@slot used within @widget classes."""

    def test_slot_on_widget_method(self, qt: QtDriver) -> None:
        """@slot should work on widget methods."""

        @widget
        class MyWidget(QWidget):
            called: bool = False

            @slot
            async def on_click(self) -> None:
                self.called = True

        w = MyWidget()
        qt.track(w)

        assert_that(w.on_click).is_not_none()
        assert_that(callable(w.on_click)).is_true()

    def test_sync_slot_on_widget_method(self, qt: QtDriver) -> None:
        """@slot should work on sync widget methods."""

        @widget
        class MyWidget(QWidget):
            value: int = 0

            @slot
            def increment(self) -> None:
                self.value += 1

        w = MyWidget()
        qt.track(w)

        w.increment()
        assert_that(w.value).is_equal_to(1)


class TestSlotSyncBehavior:
    """Test sync function behavior with @slot."""

    def test_sync_slot_without_parens_returns_same_function(self, qt: QtDriver) -> None:
        """@slot on sync function without parens returns the function."""
        _ = qt

        def original() -> int:
            return 42

        decorated = slot(original)

        assert_that(decorated()).is_equal_to(42)

    def test_sync_slot_with_parens_returns_same_function(self, qt: QtDriver) -> None:
        """@slot() on sync function with parens returns the function."""
        _ = qt

        @slot()
        def handler() -> int:
            return 42

        assert_that(handler()).is_equal_to(42)
